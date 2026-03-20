import 'dart:async';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:io';
import 'dart:ui' as ui;
import 'package:path_provider/path_provider.dart';
import 'package:path/path.dart' as p;
import 'package:flutter/services.dart'; // For MethodChannel


import '../services/auth_service.dart';
import '../services/api_service.dart';
import '../services/voice_commander.dart';
import '../services/pulse_service.dart';
import '../theme/app_theme.dart';
import '../widgets/rain_overlay.dart';
import 'auth/admin_login_dialog.dart';
import 'auth/login_screen.dart';
import 'history_screen.dart';
import 'support/help_center_screen.dart'; 
import 'support/neural_handscroll_profile.dart';
import '../widgets/liquid_physics_background.dart';
import '../services/database_helper.dart';
import 'settings/neural_settings_screen.dart';
import 'gallery_screen.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  // Local Avatar State
  File? _localAvatar;
  bool _isProfileExpanded = false;
  
  // Server Status
  bool _isConnected = false;
  Timer? _statusTimer;

  // Neural Interface State
  bool _autoListen = false;
  String _selectedLang = 'English (US)';
  double _islandScale = 1.0;
  double _verticalOffset = 0.0;
  double _horizontalOffset = 0.0;
  
  // Dummy languages
  final List<String> _languages = ['English (US)', 'Hindi (IN)', 'Bengali (IN)'];

  @override
  void initState() {
    super.initState();
    _checkServerStatus();
    _statusTimer = Timer.periodic(const Duration(seconds: 3), (_) => _checkServerStatus());
    
    // Init state from service
    WidgetsBinding.instance.addPostFrameCallback((_) {
       final pulse = Provider.of<PulseService>(context, listen: false);
       setState(() {
         _verticalOffset = pulse.topOffset;
         _horizontalOffset = pulse.leftOffset;
       });
    });
  }

  @override
  void dispose() {
    _statusTimer?.cancel();
    super.dispose();
  }

  Future<void> _checkServerStatus() async {
    final api = Provider.of<ApiService>(context, listen: false);
    final status = await api.checkHealth();
    if (mounted && status != _isConnected) {
      setState(() => _isConnected = status);
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthService>(context);
    final user = auth.currentUser;
    final isGoogle = user?['password_hash'] == 'GOOGLE_AUTH';
    final photoUrl = user?['photo_url'];

    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        title: Text("COMMAND CENTER", style: GoogleFonts.orbitron(fontWeight: FontWeight.bold, letterSpacing: 2)),
        backgroundColor: Colors.transparent,
        centerTitle: true,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, color: Colors.white70),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: Stack(
        children: [
          // Background Liquid Physics
          const Positioned.fill(child: LiquidPhysicsBackground()),
          
          // Main Content
          SafeArea(
            child: Column(
              children: [
                // Scrollable Content (Profile + Options)
                Expanded(
                  child: SingleChildScrollView(
                    physics: const BouncingScrollPhysics(),
                    child: Column(
                      children: [
                         const SizedBox(height: 10),

                         // Profile Section (Android Style - Top)
                         _buildProfileSection(user, isGoogle, photoUrl),

                         const SizedBox(height: 12),
                         
                         // Options Grid
                         // Options List (Fixed Height to match Profile)
                         Column(
                           children: [
                              SizedBox(
                                height: 100,
                                child: _buildActionCard(
                                  icon: Icons.history, 
                                  label: "HISTORY & MEMORY", 
                                  onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const HistoryScreen())),
                                ),
                              ),
                              const SizedBox(height: 12),
                              SizedBox(
                                height: 100,
                                child: _buildActionCard(
                                  icon: Icons.hub, 
                                  label: "SERVER UPLINK", 
                                  onTap: _showServerDialog,
                                  trailing: Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                    decoration: BoxDecoration(
                                      color: _isConnected ? Colors.green.withOpacity(0.2) : Colors.red.withOpacity(0.2),
                                      borderRadius: BorderRadius.circular(20),
                                      border: Border.all(color: _isConnected ? Colors.green : Colors.red, width: 1)
                                    ),
                                    child: Row(
                                      mainAxisSize: MainAxisSize.min,
                                      children: [
                                        Icon(_isConnected ? Icons.wifi : Icons.wifi_off, size: 12, color: _isConnected ? Colors.green : Colors.red),
                                        const SizedBox(width: 6),
                                        Text(_isConnected ? "ONLINE" : "OFFLINE", style: GoogleFonts.shareTechMono(color: _isConnected ? Colors.green : Colors.red, fontSize: 10))
                                      ],
                                    ),
                                  )
                                ),
                              ),
                              const SizedBox(height: 12),
                              SizedBox(
                                height: 100,
                                child: _buildActionCard(
                                  icon: Icons.help_outline, 
                                  label: "SUPPORT FREQUENCY", 
                                  onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const HelpCenterScreen())),
                                ),
                              ),
                              const SizedBox(height: 12),
                              SizedBox(
                                height: 100,
                                child: _buildActionCard(
                                  icon: Icons.person_pin_circle_outlined, 
                                  label: "ABOUT CREATOR", 
                                  onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const NeuralHandscrollProfile())),
                                ),
                              ),
                            ],
                          ),
                          
                          const SizedBox(height: 24),
                          _buildSectionTitle("NEURAL INTERFACE"),
                          const SizedBox(height: 12),
                          
                          // Neural Config Card
                          _buildGlassContainer(
                            padding: const EdgeInsets.all(20),
                            child: Column(
                              children: [
                                // Auto-Listener
                                SwitchListTile(
                                  title: Text("Auto-Listener AI", style: GoogleFonts.orbitron(color: Colors.white, fontSize: 14)),
                                  subtitle: Text("Wake word detection in background", style: GoogleFonts.outfit(color: Colors.white54, fontSize: 12)),
                                  value: _autoListen,
                                  activeColor: AppTheme.neonBlue,
                                  onChanged: (val) {
                                    setState(() => _autoListen = val);
                                    VoiceCommander().setAutoWake(val, context);
                                  },
                                ),
                                const Divider(color: Colors.white10),
                                
                                // Language
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Text("Voice Language", style: GoogleFonts.shareTechMono(color: Colors.white70)),
                                    DropdownButton<String>(
                                      value: _selectedLang,
                                      dropdownColor: const Color(0xFF1E1E1E),
                                      style: GoogleFonts.outfit(color: Colors.white),
                                      underline: Container(),
                                      icon: const Icon(Icons.arrow_drop_down, color: AppTheme.neonBlue),
                                      items: _languages.map((l) => DropdownMenuItem(value: l, child: Text(l))).toList(),
                                      onChanged: (val) {
                                        if (val != null) {
                                           setState(() => _selectedLang = val);
                                           VoiceCommander().updateLocale(val);
                                        }
                                      },
                                    )
                                  ],
                                ),
                                const Divider(color: Colors.white10),
                                
                                // Calibration Slider (Vertical Offset)
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Text("Pulse Vertical Offset", style: GoogleFonts.shareTechMono(color: Colors.white70)),
                                    Text("${_verticalOffset.toInt()}px", style: GoogleFonts.outfit(color: AppTheme.neonBlue)),
                                  ],
                                ),
                                Slider(
                                  value: _verticalOffset,
                                  min: -20,
                                  max: 50,
                                    activeColor: AppTheme.neonBlue,
                                    inactiveColor: Colors.white10,
                                    onChangeStart: (_) => Provider.of<PulseService>(context, listen: false).setCalibrationMode(true),
                                    onChangeEnd: (_) => Provider.of<PulseService>(context, listen: false).setCalibrationMode(false),
                                    onChanged: (val) {
                                      setState(() => _verticalOffset = val);
                                      Provider.of<PulseService>(context, listen: false).setOffsets(_verticalOffset, _horizontalOffset);
                                    },
                                  ),
                                  
                                  // Horizontal Offset
                                  const SizedBox(height: 10),
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                    children: [
                                      Text("Pulse Horizontal Offset", style: GoogleFonts.shareTechMono(color: Colors.white70)),
                                      Text("${_horizontalOffset.toInt()}px", style: GoogleFonts.outfit(color: AppTheme.neonBlue)),
                                    ],
                                  ),
                                  Slider(
                                    value: _horizontalOffset,
                                    min: -150,
                                    max: 150,
                                    activeColor: AppTheme.neonBlue,
                                    inactiveColor: Colors.white10,
                                    onChangeStart: (_) => Provider.of<PulseService>(context, listen: false).setCalibrationMode(true),
                                    onChangeEnd: (_) => Provider.of<PulseService>(context, listen: false).setCalibrationMode(false),
                                    onChanged: (val) {
                                        setState(() => _horizontalOffset = val);
                                        Provider.of<PulseService>(context, listen: false).setOffsets(_verticalOffset, _horizontalOffset);
                                    },
                                  ),

                                  const Divider(color: Colors.white10),
                                  
                                  // Visual Cortex (Physics Engine)
                                   ListTile(
                                    contentPadding: const EdgeInsets.symmetric(horizontal: 0),
                                    title: Text("Visual Cortex", style: GoogleFonts.orbitron(color: Colors.white, fontSize: 14)),
                                    subtitle: Text("Configure Physics Engine & Holograms", style: GoogleFonts.outfit(color: Colors.white54, fontSize: 12)),
                                    leading: const Icon(Icons.hub, color: Colors.purpleAccent),
                                    trailing: const Icon(Icons.arrow_forward_ios, size: 14, color: Colors.white30),
                                    onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => NeuralSettingsScreen())),
                                  ),
                                  
                                  const Divider(color: Colors.white10),
                                  
                                  // Image Generator (Moved from Home)
                                   ListTile(
                                    contentPadding: const EdgeInsets.symmetric(horizontal: 0),
                                    title: Text("Server Gallery", style: GoogleFonts.orbitron(color: Colors.white, fontSize: 14)),
                                    subtitle: Text("Access System Files & Logs", style: GoogleFonts.outfit(color: Colors.white54, fontSize: 12)),
                                    leading: const Icon(Icons.palette, color: Colors.pinkAccent),
                                    trailing: const Icon(Icons.arrow_forward_ios, size: 14, color: Colors.white30),
                                    onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const GalleryScreen())),
                                  ),
                                  

                              ],
                            ),
                          ),
                         const SizedBox(height: 20),
                      ],
                    ),
                  ),
                ),
                
                // Fixed Footer (Pinned to Bottom)
                Container(
                  padding: const EdgeInsets.only(bottom: 20, top: 10),
                  child: Center(
                     child: GestureDetector(
                       onLongPress: _showAdminLogin, // SECRET TRIGGER
                       child: Column(
                         children: [
                           Text(
                             "NEURAL CITADEL",
                             style: GoogleFonts.orbitron(
                               color: Colors.white38, 
                               fontSize: 12, 
                               letterSpacing: 2,
                               fontWeight: FontWeight.w600
                             ),
                           ),
                           const SizedBox(height: 4),
                           Text(
                             "by Raj Tewari", 
                             style: GoogleFonts.sacramento(
                               color: AppTheme.neonBlue.withOpacity(0.5), 
                               fontSize: 18, 
                               letterSpacing: 1
                             ),
                           ),
                         ],
                       ),
                     ),
                   ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // Premium Monochrome Style
  Widget _buildActionCard({required IconData icon, required String label, required VoidCallback onTap, Widget? trailing}) {
    return GestureDetector(
      onTap: onTap,
      child: _buildGlassContainer(
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 0), // Adjust padding as needed
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Row(
              children: [
                Icon(icon, size: 24, color: AppTheme.neonBlue), // Neon accent
                const SizedBox(width: 16),
                Text(label, style: GoogleFonts.orbitron(color: Colors.white, fontSize: 14, fontWeight: FontWeight.bold, letterSpacing: 1)),
              ],
            ),
             // Dynamic Trailing or Default Arrow
             trailing ?? const Icon(Icons.arrow_forward_ios, size: 14, color: Colors.white30),
          ],
        ),
      ),
    );
  }

  Widget _buildGlassContainer({required Widget child, EdgeInsetsGeometry? padding}) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 24, vertical: 0), // Consistent Margin
      child: ClipRRect(
        borderRadius: BorderRadius.circular(24),
        child: BackdropFilter(
          filter: ui.ImageFilter.blur(sigmaX: 15, sigmaY: 15),
          child: Container(
            padding: padding ?? const EdgeInsets.all(16),
            decoration: BoxDecoration(
              // Frost Glass (White Tint) for Visibility
              color: Colors.white.withOpacity(0.05),
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [
                  Colors.white.withOpacity(0.12),
                  Colors.white.withOpacity(0.02),
                ],
              ),
              borderRadius: BorderRadius.circular(24),
              border: Border.all(color: Colors.white.withOpacity(0.15)),
              boxShadow: [
                 BoxShadow(color: Colors.black.withOpacity(0.2), blurRadius: 20),
                 BoxShadow(color: AppTheme.neonBlue.withOpacity(0.05), blurRadius: 30, spreadRadius: -5), 
              ],
            ),
            child: child,
          ),
        ),
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 32),
      child: Row(
        children: [
          Container(width: 4, height: 16, color: AppTheme.neonBlue),
          const SizedBox(width: 12),
          Text(title, style: GoogleFonts.shareTechMono(color: Colors.white54, letterSpacing: 2)),
        ],
      ),
    );
  }

  Widget _buildProfileSection(Map<String, dynamic>? user, bool isGoogle, String? photoUrl) {
    final authType = isGoogle ? "Google Uplink" : "Secure Email";

    return GestureDetector(
      onTap: () => setState(() => _isProfileExpanded = !_isProfileExpanded),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOutBack,
        height: _isProfileExpanded ? 280 : 100, // Compacted from 400 to 280 (No useless space)
        margin: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(24),
          child: BackdropFilter(
            filter: ui.ImageFilter.blur(sigmaX: 15, sigmaY: 15),
            child: Container(
              padding: const EdgeInsets.all(16), // Reduced padding for sleek look
              decoration: BoxDecoration(
                // Frost Glass (White Tint) for Visibility
                color: Colors.white.withOpacity(0.05),
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [
                    Colors.white.withOpacity(0.12),
                    Colors.white.withOpacity(0.02),
                  ],
                ),
                borderRadius: BorderRadius.circular(24),
                border: Border.all(color: Colors.white.withOpacity(0.15)),
                boxShadow: [
                   BoxShadow(color: Colors.black.withOpacity(0.2), blurRadius: 20),
                   BoxShadow(color: AppTheme.neonBlue.withOpacity(0.05), blurRadius: 30, spreadRadius: -5), 
                ],
              ),
              child: SingleChildScrollView( // PREVENTS OVERFLOW ERROR during animation
                physics: const NeverScrollableScrollPhysics(),
                child: Column(
                  children: [
                    Row(
                      children: [
                        // Avatar Logic
                        GestureDetector(
                          onTap: (_isProfileExpanded) ? _pickImage : null,
                          child: Stack(
                            children: [
                              Container(
                                decoration: BoxDecoration(
                                  shape: BoxShape.circle,
                                  border: Border.all(color: AppTheme.neonBlue.withOpacity(0.5), width: 1),
                                  boxShadow: [BoxShadow(color: AppTheme.neonBlue.withOpacity(0.2), blurRadius: 10)],
                                ),
                                child: CircleAvatar(
                                  radius: 28, // Slightly smaller avatar to fit sleek height
                                  backgroundColor: Colors.black38,
                                  backgroundImage: _localAvatar != null 
                                      ? FileImage(_localAvatar!) as ImageProvider
                                      : (photoUrl != null 
                                         ? NetworkImage(photoUrl) 
                                         : null),
                                  child: (_localAvatar == null && photoUrl == null) 
                                      ? const Icon(Icons.person, color: Colors.white54)
                                      : null,
                                ),
                              ),
                            if (_isProfileExpanded)
                              Positioned(
                                right: 0, bottom: 0,
                                child: Container(
                                  padding: const EdgeInsets.all(4),
                                  decoration: const BoxDecoration(color: AppTheme.neonBlue, shape: BoxShape.circle),
                                  child: const Icon(Icons.edit, size: 12, color: Colors.black),
                                ),
                              )
                          ],
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Text(user?['username'] ?? "Unknown User", style: GoogleFonts.outfit(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
                            const SizedBox(height: 4),
                             Row(
                               children: [
                                 Icon(isGoogle ? Icons.cloud : Icons.email, color: Colors.white30, size: 12),
                                 const SizedBox(width: 6),
                                 Text(authType, style: GoogleFonts.shareTechMono(color: Colors.white30, fontSize: 11)),
                               ],
                             ),
                          ],
                        ),
                      ),
                      Icon(_isProfileExpanded ? Icons.keyboard_arrow_up : Icons.keyboard_arrow_down, color: Colors.white30),
                    ],
                  ),
                  
                  // Expanded Details
                  if (_isProfileExpanded) ...[
                    const Divider(color: Colors.white10, height: 32),
                    
                    _buildDetailRow("IDENTITY", user?['email'] ?? "N/A"),
                    const SizedBox(height: 8),
                    _buildDetailRow("ROLE", (user?['role'] ?? "user").toUpperCase()),
                    
                    const SizedBox(height: 30), // Fixed spacing instead of Spacer() (which crashes ScrollView)
                    
                    // Logout Button inside Profile
                    SizedBox(
                      width: double.infinity,
                      child: TextButton.icon(
                        onPressed: () {
                           final auth = Provider.of<AuthService>(context, listen: false);
                           auth.signOut();
                           Navigator.of(context).pushAndRemoveUntil(
                             MaterialPageRoute(builder: (_) => const LoginScreen()),
                             (route) => false,
                           );
                        },
                        icon: const Icon(Icons.logout, color: Colors.redAccent),
                        label: Text("LOG OUT", style: GoogleFonts.shareTechMono(color: Colors.redAccent)),
                        style: TextButton.styleFrom(
                          backgroundColor: Colors.redAccent.withOpacity(0.1),
                          padding: const EdgeInsets.symmetric(vertical: 12),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))
                        ),
                      ),
                    )
                  ]
                ],
              ),
            ),
          ),
        ),
      ),
    ),
  );
}

  Widget _buildDetailRow(String label, String value) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: GoogleFonts.shareTechMono(color: Colors.white38)),
        Text(value, style: GoogleFonts.outfit(color: Colors.white, fontWeight: FontWeight.w500)),
      ],
    );
  }

  Future<void> _setAsDefaultDialer() async {
    try {
      if (Theme.of(context).platform == TargetPlatform.android) {
        // Native Implementation to bypass broken package
        const platform = MethodChannel('com.neuralcitadel/native');
        await platform.invokeMethod('setDefaultDialer');
      }
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Error: $e")));
    }
  }

  void _showServerDialog() {
     final api = Provider.of<ApiService>(context, listen: false);
     final controller = TextEditingController();
     api.getBaseUrl().then((url) => controller.text = url);
    
     showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF1E1E1E),
        title: Text("Server Uplink", style: GoogleFonts.orbitron(color: Colors.white)),
        content: TextField(
          controller: controller,
          style: const TextStyle(color: Colors.white),
          decoration: const InputDecoration(
            labelText: "Endpoint URL",
            labelStyle: TextStyle(color: Colors.white54),
            enabledBorder: UnderlineInputBorder(borderSide: BorderSide(color: Colors.white24)),
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Cancel")),
          TextButton(
            onPressed: () {
              api.updateBaseUrl(controller.text);
              Navigator.pop(ctx);
              ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Uplink Reconfigured")));
            },
            child: const Text("Engage", style: TextStyle(color: AppTheme.neonBlue)),
          ),
        ],
      ),
    );
  }

  void _showAdminLogin() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => const AdminLoginDialog(),
    );
  }

  Future<void> _pickImage() async {
    final picker = ImagePicker();
    final picked = await picker.pickImage(source: ImageSource.gallery);
    if (picked != null) {
      try {
        // 1. Save Locally (Persistent)
        final directory = await getApplicationDocumentsDirectory();
        final fileName = 'avatar_${DateTime.now().millisecondsSinceEpoch}.jpg';
        final savedImage = await File(picked.path).copy('${directory.path}/$fileName');
        
        // 2. Update Database
        final auth = Provider.of<AuthService>(context, listen: false);
        final api = Provider.of<ApiService>(context, listen: false);
        final email = auth.currentUser?['email'];
        final username = auth.currentUser?['username'] ?? 'User';

        if (email != null) {
          await DatabaseHelper.instance.updateUserPhoto(email, savedImage.path);
          
          // Refresh UI
          setState(() {
             _localAvatar = savedImage;
          });
          
          // Reload Auth so other screens see it
          await auth.init(); 

          // 3. Sync to Server (If connected)
          try {
            ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Uploading Profile Link...")));
            await api.uploadAvatar(savedImage, username);
            ScaffoldMessenger.of(context).showSnackBar(const SnackBar(backgroundColor: Colors.green, content: Text("Profile Sync Active.")));
          } catch (e) {
            print("Avatar Sync Failed: $e");
             // Silent fail is okay, local persists
          }
        }
      } catch (e) {
        print("Profile Pic Error: $e");
      }
    }
  }
}
