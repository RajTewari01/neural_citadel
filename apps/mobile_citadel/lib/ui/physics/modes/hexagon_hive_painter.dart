import 'package:flutter/material.dart';
import 'dart:math';

class HexagonHivePainter extends CustomPainter {
  final double time;
  HexagonHivePainter({required this.time});

  @override
  void paint(Canvas canvas, Size size) {
    final hexSize = 40.0;
    final w = sqrt(3) * hexSize;
    final h = 2 * hexSize;
    
    final Paint outline = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.0
      ..color = Colors.amber.withOpacity(0.2);
    
    // Grid
    for (double y = -h; y < size.height + h; y += h * 0.75) {
       bool offsetRow = ((y / (h*0.75)).round() % 2) == 1;
       double xOffset = offsetRow ? w / 2 : 0;
       
       for (double x = -w + xOffset; x < size.width + w; x += w) {
          // Pulse Calculation
          double dist = sqrt(pow(x - size.width/2, 2) + pow(y - size.height/2, 2));
          double ripple = sin(dist * 0.05 - time * 3);
          
          Color activeColor = Colors.amber;
          if (ripple > 0.5) {
             canvas.drawPath(_hexPath(x, y, hexSize * 0.9), Paint()..color = activeColor.withOpacity((ripple-0.5)*0.5));
          }
          
          canvas.drawPath(_hexPath(x, y, hexSize), outline);
       }
    }
  }
  
  Path _hexPath(double x, double y, double r) {
     final path = Path();
     for (int i=0; i<6; i++) {
        double angle = (60 * i + 30) * pi / 180;
        double px = x + r * cos(angle);
        double py = y + r * sin(angle);
        if (i==0) path.moveTo(px, py);
        else path.lineTo(px, py);
     }
     path.close();
     return path;
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}
