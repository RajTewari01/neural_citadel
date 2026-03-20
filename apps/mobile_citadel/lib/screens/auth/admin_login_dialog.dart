
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../../services/auth_service.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import '../../theme/app_theme.dart';
import '../admin/admin_dashboard.dart';

class AdminLoginDialog extends StatefulWidget {
  const AdminLoginDialog({super.key});

  @override
  State<AdminLoginDialog> createState() => _AdminLoginDialogState();
}

class _AdminLoginDialogState extends State<AdminLoginDialog> {
  int _stage = 1; // 1: Creds, 2: OTP
  bool _isLoading = false;
  String? _error;
  String? _sessionToken;

  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  final _otpController = TextEditingController();

  Future<void> _submitStage1() async {
    setState(() { _isLoading = true; _error = null; });
    
    try {
      final auth = Provider.of<AuthService>(context, listen: false);
      final result = await auth.adminLoginStage1(_usernameController.text, _passwordController.text);
      
      setState(() {
        _isLoading = false;
        _sessionToken = result['session_token'];
        _stage = 2; // Move to OTP
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
        _error = "ACCESS DENIED: Invalid Credentials";
      });
    }
  }

  Future<void> _submitStage2() async {
    setState(() { _isLoading = true; _error = null; });
    
    try {
      final auth = Provider.of<AuthService>(context, listen: false);
      final success = await auth.adminLoginStage2(_otpController.text, _sessionToken!);
      
      setState(() => _isLoading = false);
      
      if (success) {
        if (mounted) {
           Navigator.pop(context); // Close dialog
           Navigator.of(context).push(
             MaterialPageRoute(builder: (_) => const AdminDashboard())
           );
        }
      } else {
        setState(() => _error = "SECURITY BREACH: Invalid OTP");
      }
    } catch (e) {
      setState(() {
        _isLoading = false;
        _error = "CONNECTION FAILURE";
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      backgroundColor: Colors.transparent, // Glass Dialog
      child: Container(
        width: 350,
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          color: const Color(0xFF101010).withOpacity(0.95),
          borderRadius: BorderRadius.circular(24),
          border: Border.all(color: Colors.white12),
          boxShadow: [
             BoxShadow(color: AppTheme.neonBlue.withOpacity(0.1), blurRadius: 20, spreadRadius: 5),
          ],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Header
            Center(
              child: Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppTheme.neonBlue.withOpacity(0.1),
                  shape: BoxShape.circle,
                ),
                child: Icon(Icons.security, color: AppTheme.neonBlue, size: 28),
              ),
            ),
            const SizedBox(height: 16),
            Text(
              "CITADEL OVERWATCH",
              style: GoogleFonts.orbitron(
                color: Colors.white,
                fontSize: 18,
                fontWeight: FontWeight.bold,
                letterSpacing: 2,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),

            // Content
            if (_stage == 1) _buildStage1(),
            if (_stage == 2) _buildStage2(),

            if (_error != null)
              Padding(
                padding: const EdgeInsets.only(top: 16),
                child: Text(
                  _error!,
                  style: GoogleFonts.shareTechMono(color: Colors.redAccent, fontSize: 12),
                  textAlign: TextAlign.center,
                ),
              ),
              
             if (_isLoading)
               Padding(
                 padding: const EdgeInsets.only(top: 16),
                 child: Center(
                   child: SizedBox(
                     height: 20, width: 20, 
                     child: CircularProgressIndicator(strokeWidth: 2, color: AppTheme.neonBlue)
                   )
                 ),
               ),
          ],
        ),
      ),
    );
  }

  Widget _buildStage1() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildGlassField("IDENTITY", _usernameController, false),
        const SizedBox(height: 12),
        _buildGlassField("ACCESS KEY", _passwordController, true),
        const SizedBox(height: 24),
        _buildGlassButton("INITIATE UPLINK", _submitStage1),
      ],
    );
  }

  Widget _buildStage2() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          "SECURE CHANNEL ESTABLISHED.\nENTER 2FA TOKEN.",
          style: GoogleFonts.shareTechMono(color: Colors.white54, fontSize: 11),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 16),
        _buildGlassField("OTP TOKEN", _otpController, false),
        const SizedBox(height: 24),
        _buildGlassButton("AUTHORIZE SESSIONS", _submitStage2),
      ],
    );
  }

  Widget _buildGlassField(String label, TextEditingController controller, bool obscure) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(12),
      ),
      child: TextField(
        controller: controller,
        obscureText: obscure,
        style: GoogleFonts.outfit(color: Colors.white),
        cursorColor: AppTheme.neonBlue,
        decoration: InputDecoration(
          labelText: label,
          labelStyle: GoogleFonts.shareTechMono(color: Colors.white38, fontSize: 11),
          border: InputBorder.none,
          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        ),
      ),
    );
  }

  Widget _buildGlassButton(String text, VoidCallback onTap) {
    return GestureDetector(
      onTap: _isLoading ? null : onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 14),
        decoration: BoxDecoration(
          color: AppTheme.neonBlue,
          borderRadius: BorderRadius.circular(12),
          boxShadow: [
             BoxShadow(color: AppTheme.neonBlue.withOpacity(0.3), blurRadius: 10, offset: const Offset(0, 4)),
          ],
        ),
        child: Center(
          child: Text(
            text,
            style: GoogleFonts.orbitron(
              color: Colors.black,
              fontSize: 12,
              fontWeight: FontWeight.bold,
              letterSpacing: 1,
            ),
          ),
        ),
      ),
    );
  }
}
