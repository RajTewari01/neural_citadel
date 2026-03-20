import 'package:flutter/material.dart';
import 'dart:math';

class MatrixRainPainter extends CustomPainter {
  final double time;
  static final List<_codeStream> _streams = [];
  
  MatrixRainPainter({required this.time});

  @override
  void paint(Canvas canvas, Size size) {
    final rnd = Random();
    
    // Init Streams
    if (_streams.isEmpty || _streams.length * 15 < size.width) { // 15px spacing approx
       _streams.clear();
       int cols = (size.width / 15).floor();
       for(int i=0; i<cols; i++) {
          _streams.add(_codeStream(
             x: i * 15.0,
             y: rnd.nextDouble() * -size.height,
             speed: 5 + rnd.nextDouble() * 10,
             length: 5 + rnd.nextInt(15),
          ));
       }
    }
    
    // Check resizing
    if (_streams.isNotEmpty && _streams.last.x > size.width) _streams.clear();

    final textPainter = TextPainter(textDirection: TextDirection.ltr);
    
    for (var s in _streams) {
       // Move
       s.y += s.speed;
       if (s.y - s.length * 15 > size.height) {
          s.y = -100;
          s.length = 5 + rnd.nextInt(15);
          s.speed = 5 + rnd.nextDouble() * 10;
       }
       
       // Draw Stream
       for (int i=0; i<s.length; i++) {
          double charY = s.y - i * 15;
          if (charY < 0 || charY > size.height) continue;
          
          bool isHead = i == 0;
          Color c = isHead ? Colors.white : const Color(0xFF00FF41).withOpacity((1.0 - (i / s.length) * 0.7).clamp(0.2, 1.0));
          
          // Random Character Switch
          if (rnd.nextDouble() > 0.95) s.chars[i] = String.fromCharCode(0x30A0 + rnd.nextInt(96));
          // Ensure char map exists
          if (i >= s.chars.length) s.chars.add(String.fromCharCode(0x30A0 + rnd.nextInt(96)));
          
          textPainter.text = TextSpan(
             text: s.chars[i],
             style: TextStyle(color: c, fontSize: 14, height: 1.0, shadows: [Shadow(color: c, blurRadius: isHead ? 10 : 0)])
          );
          textPainter.layout();
          textPainter.paint(canvas, Offset(s.x, charY));
       }
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}

class _codeStream {
   double x;
   double y;
   double speed;
   int length;
   List<String> chars = [];
   
   _codeStream({required this.x, required this.y, required this.speed, required this.length});
}
