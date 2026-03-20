import 'package:flutter/material.dart';
import 'dart:math';

class BlackHolePainter extends CustomPainter {
  final double time;
  static final List<_Debris> _debris = [];
  
  BlackHolePainter({required this.time});

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    // Base size for the event horizon
    final holeRadius = size.width * 0.18;
    
    // Perspective Ratio (simulates the tilted accretion disk of Gargantua)
    const double ratio = 0.35;

    // --- LAYER 1: GRAVITY LENSING HALO ---
    // A massive soft glow behind everything representing bent starlight
    canvas.drawCircle(
       center, 
       holeRadius * 2.5, 
       Paint()
         ..shader = RadialGradient(
            colors: [
               Colors.orangeAccent.withOpacity(0.15),
               Colors.deepOrange.withOpacity(0.05),
               Colors.transparent
            ],
            stops: const [0.3, 0.6, 1.0]
         ).createShader(Rect.fromCircle(center: center, radius: holeRadius * 2.5))
    );

    // --- LAYER 2: BACK ACCRETION DISK (Behind the Black Hole) ---
    // We draw the top half of the disk first so the black hole eclipses it
    _drawDiskHalf(canvas, center, holeRadius, ratio, true);

    // --- LAYER 3: PHOTON SPHERE & EVENT HORIZON ---
    // The photon sphere (a perfectly round, incredibly bright thin ring hugging the black hole)
    canvas.drawCircle(
       center, 
       holeRadius + 2, 
       Paint()
         ..color = Colors.white.withOpacity(0.8)
         ..style = PaintingStyle.stroke
         ..strokeWidth = 3.0
         ..maskFilter = const MaskFilter.blur(BlurStyle.solid, 4)
    );
    
    // Outer photon glow
    canvas.drawCircle(
       center, 
       holeRadius + 4, 
       Paint()
         ..color = Colors.orangeAccent.withOpacity(0.6)
         ..style = PaintingStyle.stroke
         ..strokeWidth = 6.0
         ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 12)
    );

    // The Event Horizon (Pure Black void)
    canvas.drawCircle(
       center, 
       holeRadius,
       Paint()..color = Colors.black..style=PaintingStyle.fill
    );

    // --- LAYER 4: FRONT ACCRETION DISK ---
    // The bottom half of the disk that sweeps in front of the black hole
    _drawDiskHalf(canvas, center, holeRadius, ratio, false);

    // --- LAYER 5: RELATIVISTIC HOT MATTER (Particles) ---
    if (_debris.isEmpty) {
      for(int i=0; i<400; i++) _spawnDebris(size);
    }
    
    for (var p in _debris) {
       _updateDebris(p, size, center, holeRadius, ratio);
       
       // Heat map: White/Blue (Hotter/Close), Orange/Red (Cooler/Far)
       final distNorm = (p.dist - holeRadius) / (size.width * 0.6);
       Color color = Colors.orangeAccent;
       if (distNorm < 0.1) color = Colors.white;
       else if (distNorm < 0.25) color = Colors.yellowAccent;
       else color = Colors.deepOrange;

       final paint = Paint()
         ..color = color.withOpacity(p.opacity)
         ..style = PaintingStyle.fill;
         
       // Render particle with perspective compression
       canvas.drawOval(
           Rect.fromCenter(center: p.pos, width: p.size, height: p.size * (p.isFront ? ratio : ratio * 0.8)), 
           paint
       );
    }
  }

  void _drawDiskHalf(Canvas canvas, Offset center, double holeRadius, double ratio, bool isBackEdge) {
     // A cinematic black hole has a highly luminous, swirling fluidic disk
     int layers = 6;
     
     // The disk stretches from the photon ring out to roughly 2.5x the radius
     double diskWidth = holeRadius * 2.8;
     
     canvas.save();
     canvas.translate(center.dx, center.dy);
     
     // Rotate the entire disk array slowly over time
     canvas.rotate(time * 0.1); 

     for (int i = 0; i < layers; i++) {
         double currentDiskSpan = holeRadius + (diskWidth - holeRadius) * (i / layers);
         
         // Inner rings spin much faster than outer rings (Keplerian dynamics)
         double ringSpin = time * (0.8 - (i * 0.1));
         
         canvas.save();
         canvas.rotate(ringSpin);

         final rect = Rect.fromCenter(
            center: Offset.zero, 
            width: currentDiskSpan * 2, 
            height: currentDiskSpan * 2 * ratio
         );
         
         Color ringColor = (i < 2) ? Colors.white : Colors.orangeAccent;
         double opacity = (i < 2) ? 0.6 : 0.3 - (i * 0.04);
         
         final glowPaint = Paint()
           ..color = ringColor.withOpacity(opacity)
           ..style = PaintingStyle.stroke
           ..strokeWidth = 8.0 + (i * 4) // Outer rings are thicker and fuzzier
           ..maskFilter = MaskFilter.blur(BlurStyle.normal, 10.0 + (i * 5));

         // Draw either the top arch (pi to 2pi) or bottom arch (0 to pi)
         if (isBackEdge) {
            canvas.drawArc(rect, pi, pi, false, glowPaint);
         } else {
            canvas.drawArc(rect, 0, pi, false, glowPaint);
         }
         
         canvas.restore();
     }
     
     canvas.restore();
  }
  
  void _spawnDebris(Size size) {
     final rnd = Random();
     double angle = rnd.nextDouble() * 2 * pi;
     double dist = size.width * 0.18 + rnd.nextDouble() * size.width * 0.8;
     _debris.add(_Debris(
        angle: angle,
        dist: dist,
        size: 1 + rnd.nextDouble() * 3,
        opacity: rnd.nextDouble() * 0.8,
        speedFactor: 0.8 + rnd.nextDouble() * 1.5
     ));
  }
  
  void _updateDebris(_Debris p, Size size, Offset center, double holeRadius, double ratio) {
      // Speed scales inverse to distance (faster near horizon)
      double speed = (150 / p.dist) * 0.008 * p.speedFactor; 
      p.angle = (p.angle + speed) % (2 * pi);
      
      // Slowly spiral entirely into the hole
      p.dist -= 0.15; 
      
      if (p.dist < holeRadius) {
         final rnd = Random();
         p.dist = size.width * 0.8 + rnd.nextDouble() * 200;
         p.opacity = 0; // Respawn vanished
      }
      
      // Fade in as it approaches from outside
      if (p.dist > size.width * 0.6) p.opacity += 0.005;
      if (p.opacity > 1.0) p.opacity = 1.0;
      
      // Calculate 3D to 2D perspective projection
      double x = center.dx + cos(p.angle) * p.dist;
      double y = center.dy + sin(p.angle) * (p.dist * ratio);
      
      // Determine if particle is in front of or behind the central mass
      p.isFront = sin(p.angle) > 0;
      
      // If the particle is behind the black hole, and its 2D projected distance is *less* than 
      // the raw sphere radius, it is being eclipsed by the void.
      if (!p.isFront) {
         double distanceFromCenter2D = sqrt(pow(x - center.dx, 2) + pow(y - center.dy, 2));
         if (distanceFromCenter2D < holeRadius - 2) {
             p.opacity = 0; // Hidden by Event Horizon
         }
      }
      
      p.pos = Offset(x, y);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}

class _Debris {
  double angle;
  double dist;
  double size;
  double opacity;
  double speedFactor;
  bool isFront = true;
  Offset pos = Offset.zero;
  
  _Debris({required this.angle, required this.dist, required this.size, required this.opacity, this.speedFactor = 1.0});
}
