import 'package:flutter/material.dart';
import 'dart:math';
import 'dart:ui' as ui;

class StarfieldWarpPainter extends CustomPainter {
  final double time;

  // Persist between frames
  static final List<_Asteroid> _asteroids = [];
  static final List<_Crack> _cracks = [];
  static final List<Offset> _stars = [];
  static final List<_Streak> _streaks = [];
  static double _lastTime = 0.0;
  static double _shakeForce = 0.0;
  
  static const double FOV = 400.0;
  static const double HIT_Z = 50.0;

  StarfieldWarpPainter({required this.time});

  @override
  void paint(Canvas canvas, Size size) {
     double dt = time - _lastTime;
     if (dt < 0) dt = 0.016; // Handle wrap
     if (dt > 0.1) dt = 0.016; // Cap delta
     _lastTime = time;

     final center = Offset(size.width / 2, size.height / 2);
     Random rnd = Random();

     // 1. Initialize Once
     if (_asteroids.isEmpty) {
        for(int i=0; i<8; i++) _asteroids.add(_Asteroid(size.width, size.height, rnd, true));
        for(int i=0; i<100; i++) _stars.add(Offset(rnd.nextDouble() * size.width, rnd.nextDouble() * size.height));
        for(int i=0; i<40; i++) _streaks.add(_Streak(size.width, size.height, rnd, true));
     }

     // 2. Handle Screen Shake
     if (_shakeForce > 0) {
        _shakeForce -= dt * 3.0; // Fade out shake
        if (_shakeForce < 0) _shakeForce = 0;
     }

     canvas.save();
     if (_shakeForce > 0) {
        canvas.translate((rnd.nextDouble() - 0.5) * _shakeForce * 20, (rnd.nextDouble() - 0.5) * _shakeForce * 20);
     }

     // 3. Cinematic Deep Space Background
     canvas.drawRect(
        Rect.fromLTWH(0, 0, size.width, size.height),
        Paint()..shader = ui.Gradient.radial(
           center,
           size.width * 0.8,
           [const Color(0xFF0F172A), const Color(0xFF000000)],
           [0.0, 1.0]
        )
     );

     // 4. Distant Twinkling Stars (Static positions, cheap to draw)
     Paint starPaint = Paint()..color = Colors.white;
     for (int i = 0; i < _stars.length; i++) {
        double opacity = 0.2 + 0.3 * sin(time * 3.0 + i);
        starPaint.color = Colors.white.withOpacity(opacity.clamp(0.0, 1.0));
        canvas.drawCircle(_stars[i], i % 4 == 0 ? 1.5 : 0.8, starPaint);
     }

     // 5. Light Streaks (Hyperspace sense of speed)
     Paint streakPaint = Paint()..strokeWidth = 1.0..strokeCap = StrokeCap.round;
     for (var s in _streaks) {
        s.z -= s.vz * dt;
        if (s.z <= HIT_Z) s.reset(size.width, size.height, false);

        double k = FOV / s.z;
        double px = s.x * k + center.dx;
        double py = s.y * k + center.dy;

        double tailZ = s.z + s.vz * 0.1; // Length of streak
        double tailK = FOV / tailZ;
        double tailPx = s.x * tailK + center.dx;
        double tailPy = s.y * tailK + center.dy;

        double opacity = (1.0 - (s.z / 2000.0)).clamp(0.0, 1.0) * 0.5;
        streakPaint.color = s.color.withOpacity(opacity);
        canvas.drawLine(Offset(tailPx, tailPy), Offset(px, py), streakPaint);
     }

     // 6. 3D Asteroids
     for (var a in _asteroids) {
        a.x += a.vx * dt;
        a.y += a.vy * dt;
        a.z -= a.vz * dt;
        a.rotation += a.rotSpeed * dt;

        // Check for Impact
        if (a.z <= HIT_Z) {
           double k = FOV / HIT_Z;
           double px = a.x * k + center.dx;
           double py = a.y * k + center.dy;

           // Hit Glass
           if (px > -50 && px < size.width + 50 && py > -50 && py < size.height + 50) {
              _cracks.add(_Crack(x: px, y: py, size: 40.0 + a.radius * 2.5));
              _shakeForce = 1.0; 
           }
           a.reset(size.width, size.height, false);
           continue; // Skip rendering frame
        }

        // Draw Asteroid
        double k = FOV / a.z;
        double px = a.x * k + center.dx;
        double py = a.y * k + center.dy;
        double scale = a.radius * k;

        // Cull offscreen
        if (px < -scale*2 || px > size.width + scale*2 || py < -scale*2 || py > size.height + scale*2) {
           continue;
        }

        double depthFade = (1.0 - (a.z / 2500.0)).clamp(0.0, 1.0);

        // Transform the pre-baked Path instead of doing trig 8 times per frame per rock
        canvas.save();
        canvas.translate(px, py);
        canvas.scale(scale, scale);
        canvas.rotate(a.rotation);

        // Atmospheric shading for 3D feel
        Rect rockBounds = Rect.fromCircle(center: Offset.zero, radius: 1.0);
        Paint rockPaint = Paint()
           ..shader = ui.Gradient.linear(
              rockBounds.topLeft,
              rockBounds.bottomRight,
              [Colors.grey.shade400.withOpacity(depthFade), Colors.black.withOpacity(depthFade)],
              [0.0, 1.0]
           );
        canvas.drawPath(a.cachedPath, rockPaint);

        // Edge rim light
        Paint rockHighlight = Paint()
           ..style = PaintingStyle.stroke
           ..strokeWidth = max(0.05, 0.05) // Scale is applied to canvas
           ..color = Colors.white.withOpacity((depthFade * 0.3).clamp(0.0, 1.0));
        canvas.drawPath(a.cachedPath, rockHighlight);
        
        canvas.restore();
     }

     // 7. Render Glass Cracks (Energy Shield Shatter)
     double flashAlpha = 0.0;
     for (int i = _cracks.length - 1; i >= 0; i--) {
        var c = _cracks[i];
        c.age += dt;

        if (c.age < 0.15) {
           flashAlpha = max(flashAlpha, 1.0 - (c.age / 0.15));
        }

        double maxAge = 4.0;
        double fade = (1.0 - (c.age / maxAge)).clamp(0.0, 1.0);

        if (fade <= 0.0) {
           _cracks.removeAt(i);
        } else {
           // Cyan Hologram glow behind crack
           Paint crackGlow = Paint()
              ..style = PaintingStyle.stroke
              ..strokeWidth = 3.0
              ..strokeCap = StrokeCap.round
              ..color = Colors.cyanAccent.withOpacity((fade * 0.8).clamp(0.0, 1.0));
           canvas.drawPath(c.path, crackGlow);

           // White searing hot core
           Paint crackCore = Paint()
              ..style = PaintingStyle.stroke
              ..strokeWidth = 1.0
              ..strokeCap = StrokeCap.round
              ..color = Colors.white.withOpacity(fade.clamp(0.0, 1.0));
           canvas.drawPath(c.path, crackCore);
        }
     }

     // Impact Flash Overlay
     if (flashAlpha > 0) {
        canvas.drawRect(
           Rect.fromLTWH(0, 0, size.width, size.height),
           Paint()..color = Colors.cyanAccent.withOpacity((flashAlpha * 0.3).clamp(0.0, 1.0))
        );
     }

     canvas.restore(); // Undo screen shake translation
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}

class _Asteroid {
   double x=0, y=0, z=0;
   double vx=0, vy=0, vz=0;
   double radius=10;
   double rotation=0;
   double rotSpeed=0;
   List<Offset> vertices = [];
   Path cachedPath = Path();
   final Random rnd;

   _Asteroid(double w, double h, this.rnd, bool firstRun) {
      reset(w, h, firstRun);
   }

   void reset(double w, double h, bool firstRun) {
      z = firstRun ? (rnd.nextDouble() * 2500.0) : 2500.0 + rnd.nextDouble() * 500.0;
      
      // Target hit coordinates on the screen
      double targetPx, targetPy;
      if (rnd.nextDouble() < 0.85) {
         // Bias highly toward hitting the visible glass shield
         targetPx = (rnd.nextDouble() - 0.5) * w * 0.9;
         targetPy = (rnd.nextDouble() - 0.5) * h * 0.9;
      } else {
         // Fly past
         targetPx = (rnd.nextDouble() - 0.5) * w * 3;
         targetPy = (rnd.nextDouble() - 0.5) * h * 3;
      }

      // Convert target pixel to world coordinate at HIT_Z
      double targetX = targetPx * StarfieldWarpPainter.HIT_Z / StarfieldWarpPainter.FOV;
      double targetY = targetPy * StarfieldWarpPainter.HIT_Z / StarfieldWarpPainter.FOV;

      // Spawn world coordinate at spawn Z
      double spawnX = (rnd.nextDouble() - 0.5) * w * 8;
      double spawnY = (rnd.nextDouble() - 0.5) * h * 8;
      
      x = spawnX;
      y = spawnY;

      // Trajectory Math: must travel from Spawn to Target in exactly timeToHit
      vz = 800.0 + rnd.nextDouble() * 1200.0; 
      double timeToHit = (z - StarfieldWarpPainter.HIT_Z) / vz;
      vx = (targetX - spawnX) / timeToHit;
      vy = (targetY - spawnY) / timeToHit;

      radius = 10.0 + rnd.nextDouble() * 30.0;
      rotation = rnd.nextDouble() * pi * 2;
      rotSpeed = (rnd.nextDouble() - 0.5) * 3.0;

      // Procedural rock geometry cached ONCE per lifecycle
      vertices.clear();
      cachedPath.reset();
      int sides = 5 + rnd.nextInt(5);
      for (int i=0; i<sides; i++) {
         double angle = (i * 2 * pi) / sides;
         double r = 0.6 + rnd.nextDouble() * 0.4;
         vertices.add(Offset(cos(angle)*r, sin(angle)*r));
         
         double vx = cos(angle)*r;
         double vy = sin(angle)*r;
         if (i == 0) cachedPath.moveTo(vx, vy);
         else cachedPath.lineTo(vx, vy);
      }
      cachedPath.close();
   }
}

class _Crack {
   double age = 0.0;
   final Path path;

   _Crack({required double x, required double y, required double size}) : path = Path() {
      Random rnd = Random();
      int numVeins = 4 + rnd.nextInt(4);
      for (int i = 0; i < numVeins; i++) {
         double angle = (i * 2 * pi / numVeins) + (rnd.nextDouble() - 0.5) * 0.5;
         double dist = 0.0;
         double currentX = x;
         double currentY = y;
         path.moveTo(x, y);

         while(dist < size) {
            double step = 8 + rnd.nextDouble() * 20;
            dist += step;
            angle += (rnd.nextDouble() - 0.5) * 0.6; // Jagged shift
            currentX += cos(angle) * step;
            currentY += sin(angle) * step;
            path.lineTo(currentX, currentY);

            // Bifurcation fork
            if (rnd.nextDouble() > 0.6) {
               double bAngle = angle + (rnd.nextBool() ? 1.0 : -1.0) * 0.8;
               double bx = currentX + cos(bAngle) * step * 0.8;
               double by = currentY + sin(bAngle) * step * 0.8;
               path.moveTo(currentX, currentY);
               path.lineTo(bx, by);
               path.moveTo(currentX, currentY); // Return to main vein
            }
         }
      }
   }
}

class _Streak {
   double x=0, y=0, z=0, vz=0;
   Color color = Colors.cyanAccent;
   final Random rnd;

   _Streak(double w, double h, this.rnd, bool firstRun) {
      reset(w, h, firstRun);
   }

   void reset(double w, double h, bool firstRun) {
      z = firstRun ? (rnd.nextDouble() * 2500.0) : 2500.0;
      x = (rnd.nextDouble() - 0.5) * w * 10;
      y = (rnd.nextDouble() - 0.5) * h * 10;
      vz = 1500.0 + rnd.nextDouble() * 2000.0;
      color = rnd.nextBool() ? Colors.cyanAccent : Colors.lightBlueAccent;
   }
}
