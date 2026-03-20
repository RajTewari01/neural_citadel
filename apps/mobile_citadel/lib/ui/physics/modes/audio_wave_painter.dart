import 'package:flutter/material.dart';
import 'dart:math';

class AudioWavePainter extends CustomPainter {
  final double time;
  AudioWavePainter({required this.time});

  @override
  void paint(Canvas canvas, Size size) {
    final Paint paint = Paint()
      ..strokeWidth = 2.0
      ..style = PaintingStyle.stroke;
      
      // Simulate multiple frequency bands
      _drawWave(canvas, size, 1.0, Colors.redAccent, time);
      _drawWave(canvas, size, 1.5, Colors.greenAccent, time + 1);
      _drawWave(canvas, size, 2.0, Colors.blueAccent, time + 2);
  }
  
  void _drawWave(Canvas canvas, Size size, double freqMult, Color color, double t) {
      final path = Path();
      final midY = size.height / 2;
      path.moveTo(0, midY);
      
      for (double x = 0; x <= size.width; x+=5) {
         // Simulated Audio Data (Simplex noise-ish)
         double noise = sin(x * 0.02 * freqMult + t * 5) * sin(x * 0.01 + t) * sin(t*2);
         double amp = size.height * 0.2 * noise; 
         
         path.lineTo(x, midY + amp);
      }
      
      canvas.drawPath(path, Paint()..color = color..style = PaintingStyle.stroke..strokeWidth = 2);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}
