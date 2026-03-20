
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'package:animate_do/animate_do.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import '../../services/auth_service.dart';
import '../chat_screen.dart';
import 'admin_login_dialog.dart';
import '../../widgets/rain_overlay.dart'; 
import '../../theme/app_theme.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _phoneController = TextEditingController();
  final _otpController = TextEditingController();
  
  bool _isLogin = true;
  bool _isLoading = false;
  String _authMethod = 'email'; // email, sms
  bool _otpSent = false;

  void _submit() async {
    setState(() => _isLoading = true);
    final auth = Provider.of<AuthService>(context, listen: false);
    bool success = false;

    if (_authMethod == 'email') {
      if (_isLogin) {
        success = await auth.signInWithPassword(_emailController.text, _passwordController.text);
      } else {
        success = await auth.register(_emailController.text.split('@')[0], _emailController.text, _passwordController.text);
      }
    } else {
      if (!_otpSent) {
        success = await auth.signInWithSMS(_phoneController.text);
        if (success) setState(() => _otpSent = true);
        setState(() => _isLoading = false);
        return;
      } else {
        success = await auth.verifyOTP(_phoneController.text, _otpController.text);
      }
    }

    setState(() => _isLoading = false);

    if (success) {
      if (mounted) {
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(builder: (_) => const ChatScreen(mode: "reasoning")),
        );
      }
    } else {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(_otpSent ? "Invalid OTP" : "Authentication Failed"), backgroundColor: Colors.redAccent),
        );
      }
    }
  }

  void _googleSignIn() async {
    setState(() => _isLoading = true);
    final auth = Provider.of<AuthService>(context, listen: false);
    final success = await auth.signInWithGoogle();
    setState(() => _isLoading = false);
    if (success) {
       if (mounted) {
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(builder: (_) => const ChatScreen(mode: "reasoning")),
        );
      }
    } else {
       if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Google Sign In Failed"), backgroundColor: Colors.redAccent),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          // Background Rain
          const Positioned.fill(child: RainOverlay(type: RainType.matrixGreen)),
          
          Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: FadeInUp(
                duration: const Duration(milliseconds: 800),
                child: Container(
                  constraints: const BoxConstraints(maxWidth: 400),
                  padding: const EdgeInsets.all(32),
                  decoration: BoxDecoration(
                    color: Colors.black.withOpacity(0.7),
                    borderRadius: BorderRadius.circular(24),
                    border: Border.all(color: Colors.white12),
                    boxShadow: [
                      BoxShadow(color: AppTheme.neonBlue.withOpacity(0.1), blurRadius: 20, spreadRadius: 0),
                    ]
                  ),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      // Logo / Header
                      GestureDetector(
                        onLongPress: () {
                          showDialog(
                            context: context,
                            barrierDismissible: false,
                            builder: (context) => const AdminLoginDialog(),
                          );
                        },
                        child: ShaderMask(
                          shaderCallback: (bounds) => const LinearGradient(
                            colors: [AppTheme.neonBlue, AppTheme.neonPurple],
                          ).createShader(bounds),
                          child: Text(
                            "NEURAL CITADEL",
                            style: GoogleFonts.orbitron(
                              fontSize: 28,
                              fontWeight: FontWeight.bold,
                              color: Colors.white,
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: 8),

                      const SizedBox(height: 32),

                      // Auth Method Tabs
                      Container(
                        padding: const EdgeInsets.all(4),
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.05),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Row(
                          children: [
                            _buildTab("Email/Pass", 'email'),
                            _buildTab("SMS Link", 'sms'),
                          ],
                        ),
                      ),
                      const SizedBox(height: 24),

                      if (_authMethod == 'email') ...[
                        _buildTextField("Email Identity", _emailController, Icons.email_outlined),
                        const SizedBox(height: 16),
                        _buildTextField("Access Code", _passwordController, Icons.lock_outline,  isPass: true),
                      ] else ...[
                        _buildTextField("Comm Link (Phone)", _phoneController, Icons.phone_android),
                        if (_otpSent) ...[
                          const SizedBox(height: 16),
                          _buildTextField("Encryption Key (OTP)", _otpController, Icons.key),
                        ]
                      ],

                      const SizedBox(height: 24),

                      // Main Action Button
                      SizedBox(
                        width: double.infinity,
                        height: 50,
                        child: ElevatedButton(
                          onPressed: _isLoading ? null : _submit,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppTheme.neonBlue.withOpacity(0.8),
                            foregroundColor: Colors.white,
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                            shadowColor: AppTheme.neonBlue.withOpacity(0.5),
                            elevation: 8,
                          ),
                          child: _isLoading 
                            ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                            : Text(
                                _authMethod == 'sms' && !_otpSent ? "SEND UPLINK" : (_isLogin ? "JACK IN" : "INITIALIZE"),
                                style: GoogleFonts.orbitron(fontWeight: FontWeight.bold, letterSpacing: 1),
                              ),
                        ),
                      ),

                      const SizedBox(height: 24),
                      
                      // Divider
                      Row(children: [
                        const Expanded(child: Divider(color: Colors.white10)),
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 16),
                          child: Text("OR", style: GoogleFonts.jetBrainsMono(color: Colors.white24, fontSize: 10)),
                        ),
                        const Expanded(child: Divider(color: Colors.white10)),
                      ]),
                      
                      const SizedBox(height: 24),

                      // Google Button
                      OutlinedButton.icon(
                        onPressed: _isLoading ? null : _googleSignIn,
                        icon: const FaIcon(FontAwesomeIcons.google, color: Colors.white, size: 18),
                        label: Text("Sign in with Google", style: GoogleFonts.outfit(color: Colors.white)),
                        style: OutlinedButton.styleFrom(
                          minimumSize: const Size(double.infinity, 50),
                          side: const BorderSide(color: Colors.white24),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        ),
                      ),

                      const SizedBox(height: 24),
                      
                      // Toggle Login/Register
                      if (_authMethod == 'email')
                        TextButton(
                          onPressed: () => setState(() => _isLogin = !_isLogin),
                          child: Text(
                            _isLogin ? "New user? Initialize Profile" : "Existing user? Jack In",
                            style: GoogleFonts.outfit(color: AppTheme.neonPurple),
                          ),
                        ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTextField(String label, TextEditingController ctrl, IconData icon, {bool isPass = false}) {
    return TextField(
      controller: ctrl,
      obscureText: isPass,
      style: const TextStyle(color: Colors.white),
      decoration: InputDecoration(
        labelText: label,
        labelStyle: const TextStyle(color: Colors.white38),
        prefixIcon: Icon(icon, color: Colors.white54, size: 18),
        filled: true,
        fillColor: Colors.white.withOpacity(0.05),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
        enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
        focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: AppTheme.neonBlue, width: 1)),
      ),
    );
  }

  Widget _buildTab(String label, String method) {
    final isSelected = _authMethod == method;
    return Expanded(
      child: GestureDetector(
        onTap: () => setState(() {
          _authMethod = method;
          _otpSent = false;
        }),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 10),
          decoration: BoxDecoration(
            color: isSelected ? Colors.white10 : Colors.transparent,
            borderRadius: BorderRadius.circular(10),
          ),
          child: Center(
            child: Text(
              label,
              style: GoogleFonts.outfit(
                color: isSelected ? Colors.white : Colors.white38,
                fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
              ),
            ),
          ),
        ),
      ),
    );
  }
}
