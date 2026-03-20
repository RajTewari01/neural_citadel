import 'package:flutter/material.dart';
import 'dart:math';

class NetworkDNA extends CustomPainter {
  final double time;
  NetworkDNA({required this.time});

  @override
  void paint(Canvas canvas, Size size) {
     double centerY = size.height / 2;
     double centerX = size.width / 2;
     
     // 3D parameters
     double amplitude = size.width * 0.35; // How wide the helix is
     double frequency = 0.05; // How tight the spirals are
     double speed = time * 2.0; // Vertical scrolling speed
     double rotation = time * 0.8; // 3D spin speed
     
     // Draw from top to bottom
     int steps = 40; // Number of base pairs
     double spacing = size.height / steps;
     
     for (int i = 0; i <= steps; i++) {
        double y = i * spacing;
        
        // Add vertical scrolling
        double movingY = (y + speed * 50) % size.height;
        
        // Phase for the current Y position
        double phase = movingY * frequency;
        
        // Strand 1 (X and Z coordinates in 3D space)
        double x1 = centerX + sin(phase + rotation) * amplitude;
        double z1 = cos(phase + rotation); // -1 (back) to 1 (front)
        
        // Strand 2 (opposite side of the helix)
        double x2 = centerX + sin(phase + rotation + pi) * amplitude;
        double z2 = cos(phase + rotation + pi);
        
        // --- Render Logic (Z-Sorting for 3D illusion) ---
        // Back Elements first, then Front Elements
        
        // Depth scaling and opacity
        double scale1 = (z1 + 2.0) / 3.0; // Map [-1, 1] to [0.33, 1.0]
        double scale2 = (z2 + 2.0) / 3.0;
        
        double opacity1 = (z1 + 1.5) / 2.5; // Back is dimmer
        double opacity2 = (z2 + 1.5) / 2.5;
        
        // Base pair connections (Draw behind everything)
        canvas.drawLine(
           Offset(x1, movingY), 
           Offset(x2, movingY), 
           Paint()
             ..color = Colors.white.withOpacity(0.15)
             ..strokeWidth = 1.0
        );

        // Nodes (Determine draw order based on Z)
        if (z1 < z2) {
           _drawNode(canvas, x1, movingY, scale1, opacity1, Colors.cyanAccent);
           _drawNode(canvas, x2, movingY, scale2, opacity2, Colors.purpleAccent);
        } else {
           _drawNode(canvas, x2, movingY, scale2, opacity2, Colors.purpleAccent);
           _drawNode(canvas, x1, movingY, scale1, opacity1, Colors.cyanAccent);
        }
     }
  }

  void _drawNode(Canvas canvas, double x, double y, double scale, double opacity, Color color) {
     final paint = Paint()
       ..color = color.withOpacity(opacity.clamp(0.0, 1.0))
       ..style = PaintingStyle.fill;
       
     // Core
     canvas.drawCircle(Offset(x, y), 4.0 * scale, paint);
     // Glow
     canvas.drawCircle(Offset(x, y), 12.0 * scale, Paint()
       ..color = color.withOpacity((opacity * 0.4).clamp(0.0, 1.0))
       ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 5.0)
     );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}
