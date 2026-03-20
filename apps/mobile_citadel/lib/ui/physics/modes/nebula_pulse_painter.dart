import 'package:flutter/material.dart';
import 'dart:math';

class NebulaPulsePainter extends CustomPainter {
  final double time;
  
  NebulaPulsePainter({required this.time});
  
  @override
  void paint(Canvas canvas, Size size) {
     final center = Offset(size.width/2, size.height/2);
     
     // Deep space base
     canvas.drawRect(Rect.fromLTWH(0,0,size.width, size.height), Paint()..color = Colors.black);
     
     // --- Layer 1: Massive Background Nebula Glow (Slow Rotation) ---
     canvas.save();
     canvas.translate(center.dx, center.dy);
     canvas.rotate(time * 0.05); // Very slow spin
     _drawGasCloud(canvas, size, Offset.zero, Colors.deepPurple, 1.5, 80, time * 0.1);
     canvas.restore();

     // --- Layer 2: Mid-ground Vivid Colors (Counter Rotation) ---
     canvas.save();
     canvas.translate(center.dx, center.dy);
     canvas.rotate(-time * 0.08); // Counter spin
     _drawGasCloud(canvas, size, Offset.zero, Colors.purpleAccent, 1.0, 60, time * 0.3);
     canvas.restore();
     
     // --- Layer 3: High-Energy Core (Fastest, Brightest) ---
     canvas.save();
     canvas.translate(center.dx, center.dy);
     canvas.rotate(time * 0.12);
     _drawGasCloud(canvas, size, Offset.zero, Colors.cyanAccent.withOpacity(0.8), 0.6, 40, time * 0.5);
     canvas.restore();
     
     // --- Layer 4: Cinematic Stardust (Depth Parallax) ---
     // We use a fixed seed overlaid with time to make stars twinkle smoothly without recreating objects
     final rnd = Random(1337); 
     for(int i=0; i<150; i++) {
        // Space distribution
        double angle = rnd.nextDouble() * 2 * pi;
        double dist = rnd.nextDouble() * size.width;
        
        // Parallax rotation around center
        double currentAngle = angle + (time * 0.02 * (1.0 + rnd.nextDouble())); 
        
        double x = center.dx + cos(currentAngle) * dist;
        double y = center.dy + sin(currentAngle) * dist;
        
        // Twinkle effect (Smooth Sinc curve)
        double phase = rnd.nextDouble() * pi * 2;
        double speed = 2.0 + rnd.nextDouble() * 3.0;
        double pulse = (sin(time * speed + phase) + 1.0) / 2.0; // 0 to 1
        
        // Base star
        double starSize = 0.5 + rnd.nextDouble() * 1.5;
        canvas.drawCircle(Offset(x,y), starSize, Paint()..color = Colors.white.withOpacity(0.3 + (pulse * 0.7)));
        
        // Rare super bright stars get a bloom ring
        if (rnd.nextDouble() > 0.95) {
           canvas.drawCircle(Offset(x,y), starSize * 4, Paint()
             ..color = Colors.cyanAccent.withOpacity(pulse * 0.4)
             ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 3.0)
           );
        }
     }
  }
  
  void _drawGasCloud(Canvas canvas, Size size, Offset center, Color color, double scale, double blur, double t) {
      final paint = Paint()
        ..color = color.withOpacity(0.4) // Richer opacity
        ..maskFilter = MaskFilter.blur(BlurStyle.normal, blur);
        
      final path = Path();
      int points = 12; // More points for smoother organic shape
      double baseRadius = size.width * 0.4 * scale;
      
      for(int i=0; i<=points; i++) {
         double angle = (i / points) * 2 * pi;
         // Complex overlapping sine waves for highly organic flow
         double noise = sin(angle * 3 + t) * cos(angle * 2 - t) + sin(angle * 5 + t*1.5)*0.5;
         double r = baseRadius + noise * (60 * scale);
         double x = center.dx + cos(angle) * r;
         double y = center.dy + sin(angle) * r;
         
         if (i==0) path.moveTo(x,y);
         else path.lineTo(x,y);
      }
      path.close();
      canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}
