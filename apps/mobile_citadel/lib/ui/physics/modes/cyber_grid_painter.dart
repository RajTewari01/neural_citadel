import 'package:flutter/material.dart';
import 'dart:math';

class CyberGridPainter extends CustomPainter {
  final double time;
  CyberGridPainter({required this.time});

  @override
  void paint(Canvas canvas, Size size) {
     // Grid Floor (Perspective)
     double horizonY = size.height * 0.45;
     double centerX = size.width / 2;

     final Paint linePaint = Paint()
       ..color = Colors.purpleAccent.withOpacity(0.8)
       ..style = PaintingStyle.stroke
       ..strokeWidth = 2.0;

     // --- 1. VAPORWAVE SUN ---
     canvas.save();
     // Clip strictly above the horizon so the sun sets perfectly into the grid
     canvas.clipRect(Rect.fromLTRB(0, 0, size.width, horizonY)); 
     
     Offset sunPos = Offset(centerX, horizonY - 10); // Sit right on the horizon line
     double sunRadius = size.width * 0.25;
     
     canvas.drawCircle(sunPos, sunRadius, Paint()..shader = const LinearGradient(
        colors: [Colors.yellowAccent, Colors.pinkAccent], 
        begin: Alignment.topCenter, 
        end: Alignment.bottomCenter
     ).createShader(Rect.fromCircle(center: sunPos, radius: sunRadius)));
     
     // Retro Stripes on Sun (Sliced out)
     final stripePaint = Paint()..color = Colors.black..style = PaintingStyle.fill; // Pure black cuts
     for(int i=0; i<8; i++) {
        double yPos = horizonY - (i * 12) * (1 + i * 0.15); // Exponential gap spacing
        double height = 2.0 + (i * 0.8); // Top stripes are thicker
        if (yPos < horizonY - sunRadius) break;
        canvas.drawRect(Rect.fromLTRB(centerX - sunRadius, yPos - height, centerX + sunRadius, yPos), stripePaint);
     }
     canvas.restore();
     
     // --- 2. RETROWAVE MOUNTAINS ---
     // Draw a jagged wireframe mountain range just at the horizon
     final mountPaint = Paint()
       ..color = Colors.pinkAccent.withOpacity(0.5)
       ..style = PaintingStyle.stroke
       ..strokeWidth = 1.5;

     Path mountPath = Path();
     mountPath.moveTo(0, horizonY);
     final rnd = Random(42); // Fixed seed so mountains don't jump every frame
     double curX = 0;
     while(curX < size.width) {
        curX += 20 + rnd.nextDouble() * 30;
        double y = horizonY - (30 + rnd.nextDouble() * 50);
        mountPath.lineTo(curX, y);
        curX += 20 + rnd.nextDouble() * 30;
        mountPath.lineTo(curX, horizonY);
     }
     
     // Fill mountains with black to obscure the sun behind them, then stroke
     canvas.drawPath(mountPath, Paint()..color=Colors.black..style=PaintingStyle.fill);
     canvas.drawPath(mountPath, mountPaint);


     // --- 3. PERSPECTIVE GRID FLOOR ---
     
     // Background glow floor to separate from pitch black
     canvas.drawRect(
         Rect.fromLTRB(0, horizonY, size.width, size.height), 
         Paint()..shader = LinearGradient(
              colors: [Colors.purpleAccent.withOpacity(0.2), Colors.transparent],
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter
         ).createShader(Rect.fromLTRB(0, horizonY, size.width, size.height))
     );

     // Verticals (Fan out from a vanishing point)
     int numVerts = 40;
     for (int i = -numVerts; i <= numVerts; i++) {
        double topX = centerX + (i * 15); // Tightly clustered at horizon
        double bottomX = centerX + (i * 100); // Widely fanned out at screen bottom
        
        // Add a gradient so lines fade out into the dark horizon
        final vertPaint = Paint()
           ..shader = LinearGradient(
                colors: [Colors.transparent, Colors.cyanAccent.withOpacity(0.8)],
                begin: Alignment.topCenter, end: Alignment.bottomCenter
           ).createShader(Rect.fromLTRB(topX, horizonY, bottomX, size.height))
           ..style = PaintingStyle.stroke
           ..strokeWidth = 1.5;
           
        canvas.drawLine(Offset(topX, horizonY), Offset(bottomX, size.height), vertPaint);
     }
     
     // Horizontals (Simulate Z-depth forward motion)
     double speed = 2.0;
     double near = 0.5; // Closest Z
     double far = 15.0; // Farthest Z at horizon
     
     for (double z = far; z >= near; z -= 0.5) { 
        // Move Z toward the camera (decreasing Z over time)
        double movingZ = z - (time * speed) % 0.5;
        
        // Perspective projection: closer Z = lower Y on screen
        double projection = 1.0 / movingZ; 
        double y = horizonY + (projection * (size.height - horizonY) * 0.8);
        
        if (y < size.height && y >= horizonY) {
           // Color intensity scales with projection (closer = brighter)
           double intensity = (projection * 0.8).clamp(0.0, 1.0);
           
           final horizPaint = Paint()
              ..color = Colors.cyanAccent.withOpacity(intensity)
              ..style = PaintingStyle.stroke
              ..strokeWidth = 1.0 + (projection * 2); // Thicker line closer to camera
              
           canvas.drawLine(Offset(0, y), Offset(size.width, y), horizPaint);
        }
     }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}
