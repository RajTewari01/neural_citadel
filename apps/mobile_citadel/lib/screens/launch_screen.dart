import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../services/auth_service.dart';
import 'auth/login_screen.dart';
import 'chat_screen.dart'; // Navigating to Unified Chat

class LaunchScreen extends StatefulWidget {
  const LaunchScreen({super.key});

  @override
  State<LaunchScreen> createState() => _LaunchScreenState();
}

class _LaunchScreenState extends State<LaunchScreen> {
  final String _textToType = "NEURAL CITADEL";
  String _displayedText = "";
  int _charIndex = 0;
  bool _isTyping = true;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _startAnimation();
  }

  void _startAnimation() {
    // Stage 1: Type faster (50ms)
    _timer = Timer.periodic(const Duration(milliseconds: 50), (timer) {
      if (_charIndex < _textToType.length) {
        setState(() {
          _charIndex++;
          _displayedText = _textToType.substring(0, _charIndex);
        });
      } else {
        // Finished typing, pause then stage 2
        _timer?.cancel();
        _isTyping = false;
        
        Future.delayed(const Duration(milliseconds: 800), () {
          _startErase();
        });
      }
    });
  }

  void _startErase() {
    // Stage 2: Erase fast ("fast close")
    _timer = Timer.periodic(const Duration(milliseconds: 50), (timer) {
      if (_charIndex > 0) {
        setState(() {
          _charIndex--;
          _displayedText = _textToType.substring(0, _charIndex);
        });
      } else {
        // Finished erasing, check Dialer Role then navigate
        _timer?.cancel();
        _checkDefaultDialerAndNavigate();
      }
    });
  }

  Future<void> _checkDefaultDialerAndNavigate() async {
     try {
       const platform = MethodChannel('com.neuralcitadel/native');
       // This will trigger the native system dialog if not already default
       await platform.invokeMethod('setDefaultDialer');
     } catch (e) {
       debugPrint("Failed to request Dialer Role: $e");
     }
     
     // Proceed regardless of result (user might deny)
     _navigateToHome();
  }

  void _navigateToHome() async {
    final auth = Provider.of<AuthService>(context, listen: false);
    
    // Wait for initialization if needed (polling)
    // Since we are not listening, we check manually or attach a listener 
    // But polling is safer here for the imperative flow
    int retries = 0;
    while (!auth.isInitialized && retries < 20) {
      await Future.delayed(const Duration(milliseconds: 100));
      retries++;
    }

    if (mounted) {
       final nextScreen = auth.isLoggedIn ? const ChatScreen(mode: "reasoning") : const LoginScreen();
       Navigator.of(context).pushReplacement(
        PageRouteBuilder(
          pageBuilder: (context, animation, secondaryAnimation) => nextScreen,
          transitionsBuilder: (context, animation, secondaryAnimation, child) {
            return FadeTransition(opacity: animation, child: child);
          },
          transitionDuration: const Duration(milliseconds: 500),
        ),
      );
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    
    // Determine color based on theme (Neon Green or Rose Primary)
    final textColor = isDark ? const Color(0xFF00FF9D) : const Color(0xFFE1306C);

    return Scaffold(
      backgroundColor: theme.scaffoldBackgroundColor,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Blinking cursor effect included in logic implicitly by display update? 
            // Better: Render text + cursor
            Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  _displayedText,
                  style: GoogleFonts.getFont('JetBrains Mono',
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    color: textColor,
                    letterSpacing: 2.0,
                  ),
                ),
                // Cursor
                if (_isTyping || _charIndex > 0)
                  _BlinkingCursor(color: textColor),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _BlinkingCursor extends StatefulWidget {
  final Color color;
  const _BlinkingCursor({required this.color});

  @override
  State<_BlinkingCursor> createState() => _BlinkingCursorState();
}

class _BlinkingCursorState extends State<_BlinkingCursor> with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 500),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return FadeTransition(
      opacity: _controller,
      child: Container(
        width: 10,
        height: 24,
        color: widget.color,
        margin: const EdgeInsets.only(left: 4),
      ),
    );
  }
}
