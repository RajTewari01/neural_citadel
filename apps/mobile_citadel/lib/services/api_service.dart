import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/app_schemas.dart';
import 'reports_db.dart'; // Offline DB


class ApiService {
  static const String _defaultUrl = "http://10.36.207.134:8000"; 
  String baseUrl = _defaultUrl;
 
  ApiService() {
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    final prefs = await SharedPreferences.getInstance();
    baseUrl = prefs.getString('server_ip') ?? _defaultUrl;
  }

  Future<String> getBaseUrl() async {
    if (baseUrl == _defaultUrl) {
       await _loadSettings();
    }
    return baseUrl;
  }
  
  Future<bool> checkHealth() async {
    try {
      final baseUrl = await getBaseUrl();
      final response = await http.get(Uri.parse(baseUrl)).timeout(const Duration(seconds: 2));
      if (response.statusCode == 200) {
         _syncPendingReports(); // Auto-sync
         return true;
      }
      return false;
    } catch (e) {
      return false;
    }
  }

  Future<void> updateBaseUrl(String newUrl) async {
    final prefs = await SharedPreferences.getInstance();
    if (!newUrl.startsWith("http")) { // Loose check, user might type https
       newUrl = "http://$newUrl";
    }
    // Remove trailing slash
    if (newUrl.endsWith('/')) {
      newUrl = newUrl.substring(0, newUrl.length - 1);
    }
    await prefs.setString('server_ip', newUrl);
    baseUrl = newUrl;
  }

  // --- CHAT API ---
  
  Stream<String> chatStream(String prompt, {String model = "reasoning", List<Map<String, String>>? history, String? persona, String? style, bool nsfw = false}) async* {
    final baseUrl = await getBaseUrl();
    final uri = Uri.parse('$baseUrl/chat/reasoning');
    
    // For specific models (Coding, Hacking) we might route differently or pass param
    // If model is "coding", use /chat/code? Or payload param?
    // Based on server implementation:
    // Hacking -> /chat/hacking
    // Code -> /chat/code
    // Reasoning -> /chat/reasoning
    // Writing -> /chat/writing
    
    Uri targetUri = uri;
    if (model == "coding") targetUri = Uri.parse('$baseUrl/chat/code');
    if (model == "hacking") targetUri = Uri.parse('$baseUrl/chat/hacking');
    if (model == "writing") targetUri = Uri.parse('$baseUrl/chat/writing');
    
    final client = http.Client();
    try {
      final request = http.Request('POST', targetUri);
      request.headers['Content-Type'] = 'application/json';
      
      final prefs = await SharedPreferences.getInstance();
      final userEmail = prefs.getString('user_email');
      
      Map<String, dynamic> body = {
        "prompt": prompt,
        "history": history ?? [],
        "model": model,
        "user_email": userEmail // Added for God Mode tracking
      };
      
      // Writing engine parameters
      if (model == "writing") {
         body["persona"] = persona ?? "therapist";
         body["style"] = style ?? "supportive";
         body["nsfw"] = nsfw;
      }
      
      request.body = jsonEncode(body);

      final response = await client.send(request);
      
      if (response.statusCode != 200) {
        throw Exception('Failed to connect: ${response.statusCode}');
      }

      await for (final chunk in response.stream.transform(utf8.decoder)) {
        final lines = chunk.split('\n');
        for (final line in lines) {
          if (line.isNotEmpty) {
             if (line.startsWith("TOKEN:")) {
               var content = line.substring(6);
               if (content.startsWith('"')) {
                 try {
                   content = jsonDecode(content);
                 } catch (e) {
                   // ignore
                 }
               }
               yield content;
             } else if (line == "THINK_START") {
               yield "<think>"; 
             } else if (line == "THINK_END") {
               yield "</think>";
             }
          }
        }
      }
    } finally {
      client.close();
    }
  }

  // --- VOICE API ---
  
  Future<String> transcribeAudio(File audioFile) async {
    final baseUrl = await getBaseUrl();
    final uri = Uri.parse('$baseUrl/voice/transcribe');
    
    var request = http.MultipartRequest('POST', uri);
    request.files.add(await http.MultipartFile.fromPath('file', audioFile.path));
    
    final response = await request.send();
    if (response.statusCode == 200) {
      final respStr = await response.stream.bytesToString();
      final json = jsonDecode(respStr);
      return json['text'];
    } else {
      throw Exception('Transcription failed');
    }
  }

  // --- IMAGE API ---
  
  Stream<String> generateImageStream(String prompt, {String style = "Cinematic", String? subtype, String ratio = "1152:896", int? seed}) async* {
    final baseUrl = await getBaseUrl();
    final uri = Uri.parse('$baseUrl/image/generate');
    
    final client = http.Client();
    try {
      final request = http.Request('POST', uri);
      request.headers['Content-Type'] = 'application/json';
      
      Map<String, dynamic> body = {
        "prompt": prompt,
        "style": style,
        "ratio": ratio
      };
      if (subtype != null) body["subtype"] = subtype;
      if (seed != null) body["seed"] = seed;
      
      request.body = jsonEncode(body);
      
      final response = await client.send(request);
      
      await for (final chunk in response.stream.transform(utf8.decoder)) {
         final lines = chunk.split('\n');
         for (final line in lines) {
           if (line.isNotEmpty) yield line;
         }
      }
    } finally {
      client.close();
    }
  }

  Future<void> cancelImageGeneration() async {
    final baseUrl = await getBaseUrl();
    final uri = Uri.parse('$baseUrl/image/cancel');
    try {
      await http.post(uri);
    } catch (e) {
      print("Error cancelling image: $e");
    }
  }

  // --- QR API ---

  Future<String> generateQR(String data, {
    String handler = "url",
    String mode = "gradient",
    List<String>? colors,
    String? prompt,
    String mask = "radial",
    String? gradientType,
    String? moduleDrawer,
    String? logoPath,
  }) async {
    final baseUrl = await getBaseUrl();
    final uri = Uri.parse('$baseUrl/qr/generate');
    
    Map<String, dynamic> body = {
      "data": data,
      "handler": handler,
      "mode": mode,
      "mask": mask
    };
    
    if (colors != null) body["colors"] = colors;
    if (prompt != null) body["prompt"] = prompt;
    if (gradientType != null) body["gradient_type"] = gradientType;
    if (moduleDrawer != null) body["module_drawer"] = moduleDrawer;
    if (logoPath != null) body["logo_path"] = logoPath;
    
    final response = await http.post(
      uri,
      headers: {"Content-Type": "application/json"},
      body: jsonEncode(body)
    );
    
    if (response.statusCode == 200) {
      final json = jsonDecode(response.body);
      if (json['status'] == 'success') {
        final path = json['path'];
        if (path.startsWith('/')) {
          return '$baseUrl$path';
        }
        return path;
      }
      throw Exception('QR Generation failed');
    } else {
      throw Exception('Server Error: ${response.statusCode}');
    }
  }

  /// Generate QR with SSE streaming (for diffusion mode)
  Stream<String> generateQRStream(String data, {
    required String handler,
    required String prompt,
    required String sessionId,
  }) async* {
    final baseUrl = await getBaseUrl();
    final uri = Uri.parse('$baseUrl/qr/generate-stream');
    
    final client = http.Client();
    try {
      final request = http.Request('POST', uri);
      request.headers['Content-Type'] = 'application/json';
      request.body = jsonEncode({
        "data": data,
        "handler": handler,
        "mode": "diffusion",
        "prompt": prompt,
        "session_id": sessionId,
      });
      
      final response = await client.send(request);
      
      await for (final chunk in response.stream.transform(utf8.decoder)) {
        final lines = chunk.split('\n');
        for (final line in lines) {
          if (line.startsWith('data: ')) {
            yield line.substring(6);
          }
        }
      }
    } finally {
      client.close();
    }
  }

  /// Cancel QR generation (for diffusion mode)
  Future<void> cancelQR(String sessionId) async {
    final baseUrl = await getBaseUrl();
    final uri = Uri.parse('$baseUrl/qr/cancel');
    try {
      await http.post(
        uri,
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"session_id": sessionId})
      );
    } catch (e) {
      print("Error cancelling QR: $e");
    }
  }
  
  Future<String> resolveUrl(String relativeUrl) async {
    final baseUrl = await getBaseUrl();
    if (relativeUrl.startsWith("http")) return relativeUrl;
    return "$baseUrl$relativeUrl";
  }

  // --- SCHEMA API ---

  Future<QRSchema> getQRSchema() async {
    final baseUrl = await getBaseUrl();
    final response = await http.get(Uri.parse('$baseUrl/qr/schema'));
    
    if (response.statusCode == 200) {
      return QRSchema.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Failed to load QR schema');
    }
  }

  Future<ImageGenSchema> getImageGenSchema() async {
    final baseUrl = await getBaseUrl();
    final response = await http.get(Uri.parse('$baseUrl/image/schema'));
    
    if (response.statusCode == 200) {
      return ImageGenSchema.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Failed to load Image Gen schema');
    }
  }

  Future<SurgeonSchema> getSurgeonSchema() async {
    final baseUrl = await getBaseUrl();
    final response = await http.get(Uri.parse('$baseUrl/surgeon/schema'));
    
    if (response.statusCode == 200) {
      return SurgeonSchema.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Failed to load Surgeon schema');
    }
  }

  Future<NewspaperSchema> getNewspaperSchema() async {
    final baseUrl = await getBaseUrl();
    final response = await http.get(Uri.parse('$baseUrl/newspaper/schema'));
    
    if (response.statusCode == 200) {
      return NewspaperSchema.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Failed to load Newspaper schema');
    }
  }

  Future<List<Map<String, dynamic>>> getTrendingMovies() async {
    final baseUrl = await getBaseUrl();
    final response = await http.get(Uri.parse('$baseUrl/movie/trending'));
    
    if (response.statusCode == 200) {
      final json = jsonDecode(response.body);
      if (json['results'] != null) {
        return List<Map<String, dynamic>>.from(json['results']);
      }
      return [];
    } else {
      throw Exception('Failed to load Trending Movies');
    }
  }

  Future<List<dynamic>> searchMovies(String query) async {
    final baseUrl = await getBaseUrl();
    final response = await http.post(
      Uri.parse('$baseUrl/movie/search'),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({"query": query, "limit": 20})
    );
    
    if (response.statusCode == 200) {
      final json = jsonDecode(response.body);
      // Determine format, usually a list or {results: []}
      // movie.py returns whatever the runner returns.
      // runner usually returns a list of results in JSON.
      // Let's assume list or check 'results' key
      if (json is List) return json;
      if (json['results'] != null) return json['results'];
      return [];
    } else {
      throw Exception('Failed to search movies');
    }
  }

  Future<List<Map<String, dynamic>>> getGalleryItems() async {
    final baseUrl = await getBaseUrl();
    final uri = Uri.parse('$baseUrl/gallery/items');
    
    final response = await http.get(uri);
    
    if (response.statusCode == 200) {
      final json = jsonDecode(response.body);
      if (json is List) {
        return List<Map<String, dynamic>>.from(json);
      } else if (json['items'] != null) {
        return List<Map<String, dynamic>>.from(json['items']);
      }
      return [];
    } else {
      throw Exception('Failed to load Gallery items');
    }
  }

  /// Generate newspaper PDF - streams progress lines
  Stream<String> generateNewspaperStream({
    required String style,
    required String region,
    required String language,
    String? substyle,
    String translationMode = "online", // Added
  }) async* {
    final baseUrl = await getBaseUrl();
    final request = http.Request('POST', Uri.parse('$baseUrl/newspaper/generate'));
    request.headers['Content-Type'] = 'application/json';
    
    Map<String, dynamic> body = {
      'category': region,
      'style': style,
      'language': language,
      'translation_mode': translationMode, // Added
    };
    if (substyle != null) body['substyle'] = substyle;

    request.body = jsonEncode(body);

    try {
      final streamedResponse = await request.send();
      await for (final chunk in streamedResponse.stream.transform(utf8.decoder)) {
        for (final line in chunk.split('\n')) {
          if (line.trim().isNotEmpty) {
            yield line;
          }
        }
      }
    } catch (e) {
      yield 'ERROR: $e';
    }
  }

  Future<void> cancelNewspaperGeneration() async {
    final baseUrl = await getBaseUrl();
    try {
      await http.post(Uri.parse('$baseUrl/newspaper/cancel'));
    } catch (e) {
      print("Error canceling newspaper: $e");
    }
  }

  /// Process image with Image Surgeon (multipart upload)
  Future<Map<String, dynamic>> processSurgeon({
    required String mode,
    required String imagePath, // Local file path or base64
    String? prompt,
    String? solidColor,
    String? garmentPath,
    String? bgImagePath,
  }) async {
    final baseUrl = await getBaseUrl();
    final uri = Uri.parse('$baseUrl/surgeon/process');
    
    var request = http.MultipartRequest('POST', uri);
    request.fields['mode'] = mode;
    
    if (prompt != null) request.fields['prompt'] = prompt;
    if (solidColor != null) request.fields['solid_color'] = solidColor;
    
    // Add main image
    request.files.add(await http.MultipartFile.fromPath('image', imagePath));
    
    // Optional garment
    if (garmentPath != null) {
      request.files.add(await http.MultipartFile.fromPath('garment', garmentPath));
    }
    
    // Optional background image
    if (bgImagePath != null) {
      request.files.add(await http.MultipartFile.fromPath('bg_image', bgImagePath));
    }
    
    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Surgeon processing failed: ${response.body}');
    }
  }

  /// Download movie via magnet link - streams progress logs
  Stream<String> downloadMovieStream(String magnetLink) async* {
    final baseUrl = await getBaseUrl();
    final request = http.Request('POST', Uri.parse('$baseUrl/movie/download'));
    request.headers['Content-Type'] = 'application/json';
    request.body = jsonEncode({'magnet': magnetLink});

    try {
      final streamedResponse = await request.send();
      await for (final chunk in streamedResponse.stream.transform(utf8.decoder)) {
        for (final line in chunk.split('\n')) {
          if (line.trim().isNotEmpty) {
            yield line;
          }
        }
      }
    } catch (e) {
      yield 'ERROR: $e';
    }
  }

  Future<void> backupDatabase(File dbFile, String username) async {
    final baseUrl = await getBaseUrl();
    final uri = Uri.parse('$baseUrl/admin/upload_history');

    var request = http.MultipartRequest('POST', uri);
    request.fields['username'] = username;
    request.files.add(await http.MultipartFile.fromPath('file', dbFile.path));
    
    final response = await request.send();
    if (response.statusCode != 200) {
      final respStr = await response.stream.bytesToString();
      throw Exception('Backup failed: $respStr');
    }
  }

  Future<void> uploadAvatar(File imageFile, String username) async {
    final baseUrl = await getBaseUrl();
    final uri = Uri.parse('$baseUrl/admin/upload_avatar');

    var request = http.MultipartRequest('POST', uri);
    request.fields['username'] = username;
    request.files.add(await http.MultipartFile.fromPath('file', imageFile.path));
    
    final response = await request.send();
    if (response.statusCode != 200) {
      final respStr = await response.stream.bytesToString();
      throw Exception('Avatar upload failed: $respStr');
    }
  }

  // --- SYSTEM STATS API ---

  Future<Map<String, dynamic>> getSystemStats() async {
    final baseUrl = await getBaseUrl();
    final response = await http.get(Uri.parse('$baseUrl/system/stats'));
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to load system stats');
    }
  }

  // --- SUPPORT API ---

  Future<void> reportBug({
    required String description,
    required String steps,
    required String userId,
    required String screenshotPath,
  }) async {
    // 1. OPTIMISTIC / OFFLINE-FIRST: Save locally immediately.
    print("Optimistic Save: Storing report locally first...");
    await ReportsDB().insertReport(
        description: description, 
        steps: steps, 
        userId: userId, 
        screenshotPath: screenshotPath
    );
    
    // 2. Trigger Sync in Background (Do not await!)
    // This ensures UI returns immediately.
    _syncPendingReports(); 
    
    // 3. Return success immediately
    print("Report queued. UI should close.");
  }
  
  Future<void> _submitReportToServer(String description, String steps, String userId, String screenshotPath) async {
    // Added shorter timeout for sync attempts
    final baseUrl = await getBaseUrl();
    final uri = Uri.parse('$baseUrl/support/report_bug');
    
    var request = http.MultipartRequest('POST', uri);
    request.fields['description'] = description;
    request.fields['steps'] = steps;
    request.fields['user_id'] = userId;
    
    request.files.add(await http.MultipartFile.fromPath('screenshot', screenshotPath));
    
    // Timeout is important here so background sync doesn't hang forever on each item
    final response = await request.send().timeout(const Duration(seconds: 10));
    
    if (response.statusCode != 200) {
      final respStr = await response.stream.bytesToString();
      throw Exception('Server rejected: $respStr');
    }
  }

  Future<void> _syncPendingReports() async {
    final db = ReportsDB();
    final pending = await db.getPendingReports();
    if (pending.isEmpty) return;
    
    print("Syncing ${pending.length} pending reports...");
    
    for (var report in pending) {
        try {
            await _submitReportToServer(
               report['description'], 
               report['steps'], 
               report['userId'], 
               report['screenshotPath']
            );
            await db.deleteReport(report['id']);
            print("Report ${report['id']} synced.");
        } catch (e) {
            print("Failed to sync report ${report['id']}: $e");
        }
    }
  }

  // --- ADMIN REPORTS ---

  Future<List<Map<String, dynamic>>> getAdminReports() async {
    final baseUrl = await getBaseUrl();
    final response = await http.get(Uri.parse('$baseUrl/support/admin/reports'));
    
    if (response.statusCode == 200) {
      return List<Map<String, dynamic>>.from(jsonDecode(response.body));
    } else {
      throw Exception('Failed to fetch reports');
    }
  }

  Future<void> deleteAdminReport(int id) async {
    final baseUrl = await getBaseUrl();
    final response = await http.delete(Uri.parse('$baseUrl/support/admin/reports/$id'));
    
    if (response.statusCode != 200) {
      throw Exception('Failed to delete report');
    }
  }

  void unloadResources() {
    // Clean up resources if needed
  }
}
