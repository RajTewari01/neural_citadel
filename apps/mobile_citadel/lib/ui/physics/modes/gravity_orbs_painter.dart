import 'package:flutter/material.dart';
import 'dart:math';

class Orb {
  Offset position;
  Offset velocity;
  double radius;
  Color color;

  Orb({
    required this.position,
    required this.velocity,
    required this.radius,
    required this.color,
  });
}

class GravityOrbsPainter extends CustomPainter {
  final double time;
  static final List<Orb> _orbs = [];
  static bool _initialized = false;
  static Size? _lastSize;

  GravityOrbsPainter({required this.time});

  @override
  void paint(Canvas canvas, Size size) {
    if (!_initialized || _lastSize != size) {
      _initOrbs(size);
    }

    _updatePhysics(size);

    for (var orb in _orbs) {
      final paint = Paint()
        ..color = orb.color
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 10);
        
      // Draw glow
      canvas.drawCircle(orb.position, orb.radius * 1.5, Paint()..color = orb.color.withOpacity(0.3)..maskFilter = const MaskFilter.blur(BlurStyle.normal, 20));
      
      // Draw core
      canvas.drawCircle(orb.position, orb.radius, paint);
    }
  }

  void _initOrbs(Size size) {
    final rnd = Random();
    _orbs.clear();
    for (int i = 0; i < 15; i++) {
      _orbs.add(Orb(
        position: Offset(rnd.nextDouble() * size.width, rnd.nextDouble() * size.height),
        velocity: Offset((rnd.nextDouble() - 0.5) * 2, (rnd.nextDouble() - 0.5) * 2),
        radius: 10 + rnd.nextDouble() * 30,
        color: Colors.cyanAccent.withOpacity(0.6 + rnd.nextDouble() * 0.4),
      ));
    }
    _initialized = true;
    _lastSize = size;
  }

  void _updatePhysics(Size size) {
    for (var orb in _orbs) {
      // Movement
      orb.position += orb.velocity;

      // Gravity (Subtle pull to center or down?)
      // distinct "Space" feel, so low gravity, mostly bounce
      
      // Floor/Wall Bounce
      if (orb.position.dx < 0 || orb.position.dx > size.width) {
        orb.velocity = Offset(-orb.velocity.dx, orb.velocity.dy);
      }
      if (orb.position.dy < 0 || orb.position.dy > size.height) {
        orb.velocity = Offset(orb.velocity.dx, -orb.velocity.dy);
      }
    }
  }

  @override
  bool shouldRepaint(covariant GravityOrbsPainter oldDelegate) {
    return oldDelegate.time != time;
  }
}
