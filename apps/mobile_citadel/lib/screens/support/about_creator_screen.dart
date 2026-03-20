import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../theme/app_theme.dart';
import '../../widgets/liquid_physics_background.dart';
import 'dart:ui' as ui;

class AboutCreatorScreen extends StatelessWidget {
  const AboutCreatorScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        title: Text("ARCHITECT", style: GoogleFonts.orbitron(letterSpacing: 2, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: Stack(
        children: [
          // Background
          const Positioned.fill(child: LiquidPhysicsBackground()),
          
          // Content
          Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  // Profile Halo
                  Container(
                    width: 150,
                    height: 150,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      boxShadow: [
                        BoxShadow(color: AppTheme.neonBlue.withOpacity(0.4), blurRadius: 40, spreadRadius: 10),
                        BoxShadow(color: AppTheme.neonPurple.withOpacity(0.2), blurRadius: 60, spreadRadius: 20),
                      ],
                      border: Border.all(color: Colors.white.withOpacity(0.2), width: 2),
                    ),
                    child: const CircleAvatar(
                      backgroundColor: Colors.black,
                      backgroundImage: AssetImage('assets/images/creator_raj.jpg'), // Placeholder or omit if not available
                      child: Icon(Icons.person_outline, size: 60, color: Colors.white54),
                    ),
                  ),
                  const SizedBox(height: 32),
                  
                  // Name & Title
                  Text("BISWADEEP TEWARI (RAJ)", 
                    style: GoogleFonts.orbitron(
                      fontSize: 24, 
                      fontWeight: FontWeight.bold, 
                      color: Colors.white,
                      shadows: [Shadow(color: AppTheme.neonBlue, blurRadius: 20)]
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 8),
                  Text("LEAD ARCHITECT // NEURAL CITADEL", 
                    style: GoogleFonts.shareTechMono(color: AppTheme.neonCyan, fontSize: 14, letterSpacing: 1.5),
                  ),
                  
                  const SizedBox(height: 48),
                  
                  // Vision / Bio Card
                  ClipRRect(
                    borderRadius: BorderRadius.circular(20),
                    child: BackdropFilter(
                      filter: ui.ImageFilter.blur(sigmaX: 10, sigmaY: 10),
                      child: Container(
                        padding: const EdgeInsets.all(24),
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.05),
                          border: Border.all(color: Colors.white.withOpacity(0.1)),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Column(
                          children: [
                            const Icon(Icons.format_quote, color: Colors.white24, size: 30),
                            const SizedBox(height: 16),
                            Text(
                              "Building the bridge between human intent and machine intelligence. Neural Citadel is not just an app, it's an extension of the mind.",
                              style: GoogleFonts.outfit(color: Colors.white70, fontSize: 16, height: 1.5),
                              textAlign: TextAlign.center,
                            ),
                            const SizedBox(height: 16),
                            Text("- Raj", style: GoogleFonts.sacramento(color: AppTheme.neonBlue, fontSize: 24)),
                          ],
                        ),
                      ),
                    ),
                  ),
                  
                  const SizedBox(height: 40),
                  
                  // Socials / Links (Static for now)
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      _buildSocialIcon(Icons.code, "GitHub"),
                      const SizedBox(width: 24),
                      _buildSocialIcon(Icons.alternate_email, "Contact"),
                      const SizedBox(width: 24),
                      _buildSocialIcon(Icons.language, "Web"),
                    ],
                  ),

                  const SizedBox(height: 40),
                  Text("v1.0.0-alpha.21", style: GoogleFonts.shareTechMono(color: Colors.white24)),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSocialIcon(IconData icon, String label) {
    return Column(
      children: [
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: Colors.white.withOpacity(0.05),
            shape: BoxShape.circle,
            border: Border.all(color: Colors.white12),
          ),
          child: Icon(icon, color: Colors.white70, size: 20),
        ),
        const SizedBox(height: 8),
        Text(label, style: GoogleFonts.outfit(color: Colors.white30, fontSize: 10)),
      ],
    );
  }
}
