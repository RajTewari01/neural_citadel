import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'dart:async';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import '../../services/auth_service.dart';

class TerminationScreen extends StatefulWidget {
  const TerminationScreen({super.key});

  @override
  State<TerminationScreen> createState() => _TerminationScreenState();
}

class _TerminationScreenState extends State<TerminationScreen> {
  int _counter = 5;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _startSelfDestruct();
  }

  void _startSelfDestruct() {
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) async {
      if (_counter > 0) {
        if (mounted) setState(() => _counter--);
      } else {
        timer.cancel();
        // EXECUTE TERMINATION
        if (mounted) await AuthService().performTermination();
      }
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          // Glitchy Background (Reuse Liquid or simple animated container)
          Container(
            color: Colors.red.withOpacity(0.1),
            child: Center(
              child: Opacity(
                opacity: 0.2,
                child: Icon(Icons.gpp_bad, size: 300, color: Colors.red),
              ),
            ),
          ),
          
          Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const FaIcon(FontAwesomeIcons.triangleExclamation, color: Colors.red, size: 80),
                const SizedBox(height: 40),
                
                Text(
                  "CRITICAL FAILURE",
                  style: GoogleFonts.orbitron(
                    color: Colors.red,
                    fontSize: 32,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 4
                  ),
                ),
                const SizedBox(height: 20),
                
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                  decoration: BoxDecoration(
                    color: Colors.red.withOpacity(0.1),
                    border: Border.all(color: Colors.red),
                    borderRadius: BorderRadius.circular(8)
                  ),
                  child: Text(
                    "ADMIN HAS TERMINATED YOUR CONNECTION",
                    textAlign: TextAlign.center,
                    style: GoogleFonts.shareTechMono(color: Colors.red, fontSize: 16),
                  ),
                ),
                
                const SizedBox(height: 60),
                
                Text(
                  "SYSTEM WIPE IN",
                  style: GoogleFonts.shareTechMono(color: Colors.grey),
                ),
                Text(
                  "00:0$_counter",
                  style: GoogleFonts.rubikGlitch(
                    color: Colors.red, 
                    fontSize: 80
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
