import 'dart:async';
import 'dart:math';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:sensors_plus/sensors_plus.dart';

class LiquidPhysicsBackground extends StatefulWidget {
  final String themeName;
  const LiquidPhysicsBackground({super.key, this.themeName = 'water'});

  @override
  State<LiquidPhysicsBackground> createState() => _LiquidPhysicsBackgroundState();
}

class _LiquidPhysicsBackgroundState extends State<LiquidPhysicsBackground> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  StreamSubscription? _accelerometerSub;
  
  List<_GlassOrb> orbs = [];
  double gx = 0, gy = 0;
  final Random _rnd = Random();
  Size? _canvasSize;

  @override
  void initState() {
    super.initState();
    // Defer init until layout knows size
    
    _controller = AnimationController(vsync: this, duration: const Duration(hours: 1))
      ..addListener(_updatePhysics)
      ..repeat();

    _accelerometerSub = accelerometerEvents.listen((event) {
      if (mounted) {
        // Smooth gravity
        const double alpha = 0.1; 
        gx = (gx * (1 - alpha)) + ((-event.x) * alpha);
        gy = (gy * (1 - alpha)) + ((event.y) * alpha);
      }
    });
  }
  
  @override
  void didUpdateWidget(covariant LiquidPhysicsBackground oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.themeName != widget.themeName && _canvasSize != null) {
      _initOrbs(_canvasSize!);
    }
  }

  void _initOrbs(Size size) {
    orbs.clear();
    
    // Determine Colors based on Theme
    List<Color> palette;
    switch (widget.themeName.toLowerCase()) {
      case 'fire':
        palette = [Colors.redAccent, Colors.deepOrangeAccent, Colors.orange];
        break;
      case 'toxic':
        palette = [Colors.greenAccent, Colors.lightGreenAccent, Colors.purpleAccent];
        break;
      case 'void':
        palette = [Colors.white24, Colors.grey, Colors.blueGrey];
        break;
      case 'neon':
        palette = [Colors.cyanAccent, Colors.pinkAccent, Colors.purpleAccent];
        break;
      case 'water':
      default:
        palette = [Colors.cyanAccent, Colors.blueAccent, Colors.lightBlueAccent];
    }
    
    // Premium "Water/Glass" bubbles
    for (int i = 0; i < 12; i++) { 
        orbs.add(_GlassOrb(
          x: _rnd.nextDouble() * size.width,
          y: _rnd.nextDouble() * size.height,
          radius: 30 + _rnd.nextDouble() * 50, 
          color: palette[i % palette.length], 
          mass: 1.0 + _rnd.nextDouble(),
        ));
    }
  }

  List<_SplashParticle> particles = [];

  void _updatePhysics() {
    if (_canvasSize == null) return;
    final size = _canvasSize!;
    
    // Update Particles
    particles.removeWhere((p) => p.life <= 0);
    for (var p in particles) {
      p.x += p.vx;
      p.y += p.vy;
      p.life -= 0.05;
    }

    for (var orb in orbs) {
      // Physics (Reduced Gravity for "Floating" feel)
      orb.vx += gx * 0.01 * orb.mass; // Significant reduction
      orb.vy += gy * 0.01 * orb.mass;

      // No Friction - "Infinity Store of Energy"
      // Occasionally boost speed if it gets too slow to ensure "Infinity" feel
      double currentSpeed = sqrt(orb.vx*orb.vx + orb.vy*orb.vy);
      if (currentSpeed < 2.0 && currentSpeed > 0.1) {
         orb.vx *= 1.05;
         orb.vy *= 1.05;
      }
      
      // Limit Max Speed to prevent chaos
      if (currentSpeed > 15) {
        orb.vx = (orb.vx / currentSpeed) * 15;
        orb.vy = (orb.vy / currentSpeed) * 15;
      }

      // Movement
      orb.x += orb.vx;
      orb.y += orb.vy;

      // Strict Boundary Bouncing + Splash
      bool collided = false;
      if (orb.x - orb.radius < 0) {
        orb.x = orb.radius;
        orb.vx = orb.vx.abs(); // Force positive direction
        collided = true;
      }
      if (orb.x + orb.radius > size.width) {
        orb.x = size.width - orb.radius;
        orb.vx = -orb.vx.abs(); // Force negative
        collided = true;
      }
      if (orb.y - orb.radius < 0) {
        orb.y = orb.radius;
        orb.vy = orb.vy.abs();
        collided = true;
      }
      if (orb.y + orb.radius > size.height) {
        orb.y = size.height - orb.radius;
        orb.vy = -orb.vy.abs();
        collided = true;
      }

      if (collided && _rnd.nextDouble() > 0.5) { // More frequent splashes
        _spawnSplash(orb.x, orb.y, orb.color);
      }
    }
    if (mounted) setState(() {}); 
  }

  void _spawnSplash(double x, double y, Color color) {
    if (particles.length > 60) return; // Limit
    for (int i=0; i<8; i++) { // More particles
      particles.add(_SplashParticle(
        x: x, y: y,
        vx: (_rnd.nextDouble() - 0.5) * 8, // Faster splash
        vy: (_rnd.nextDouble() - 0.5) * 8,
        color: color.withOpacity(0.6),
      ));
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    _accelerometerSub?.cancel();
    super.dispose();
  }

  void _onTapDown(TapDownDetails details) {
    // "Pop" / Repel effect
    final touch = details.localPosition;
    _spawnSplash(touch.dx, touch.dy, Colors.white);

    for (var orb in orbs) {
      double dx = orb.x - touch.dx;
      double dy = orb.y - touch.dy;
      double dist = sqrt(dx*dx + dy*dy);
      
      if (dist < 200) { // Larger Interaction Radius
        // Prevent Division by Zero
        if (dist < 1) dist = 1;
        
        // Massive repulsion
        double force = (200 - dist) * 0.2; 
        orb.vx += (dx / dist) * force;
        orb.vy += (dy / dist) * force;
      }
    }
    // No setState here needed as loop handles it, but good for instant feedback
  }

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        if (_canvasSize == null || _canvasSize!.width != constraints.maxWidth || _canvasSize!.height != constraints.maxHeight) {
           _canvasSize = Size(constraints.maxWidth, constraints.maxHeight);
           _initOrbs(_canvasSize!); 
        }

        return GestureDetector(
          onTapDown: _onTapDown,
          child: Container(
            decoration: const BoxDecoration(
              gradient: RadialGradient(
                 center: Alignment.center,
                 radius: 1.5,
                 colors: [Color(0xFF0A0A0A), Color(0xFF000000)],
              )
            ),
            child: CustomPaint(
              painter: _GlassLiquidPainter(orbs, particles),
              size: Size(constraints.maxWidth, constraints.maxHeight),
            ),
          ),
        );
      }
    );
  }
}

class _SplashParticle {
  double x, y, vx, vy;
  double life = 1.0;
  Color color;
  _SplashParticle({required this.x, required this.y, required this.vx, required this.vy, required this.color});
}

class _GlassOrb {
  double x, y;
  double vx = 0, vy = 0;
  double radius;
  double mass;
  Color color;

  _GlassOrb({required this.x, required this.y, required this.radius, required this.color, this.mass = 1.0});
}

class _GlassLiquidPainter extends CustomPainter {
  final List<_GlassOrb> orbs;
  final List<_SplashParticle> particles;
  
  _GlassLiquidPainter(this.orbs, this.particles);

  @override
  void paint(Canvas canvas, Size size) {
    // Particles
    for (var p in particles) {
      final paint = Paint()..color = p.color.withOpacity(p.life * 0.8)..style = PaintingStyle.fill;
      canvas.drawCircle(Offset(p.x, p.y), 2 * p.life, paint);
    }

    // Orbs logic (Same as before but using orbs list)
    for (var orb in orbs) {
      // 1. Base Body (Semi-transparent)
      final bodyPaint = Paint()
        ..color = orb.color.withOpacity(0.3) // Increased from 0.15 for visibility
        ..style = PaintingStyle.fill;
      canvas.drawCircle(Offset(orb.x, orb.y), orb.radius, bodyPaint);

      // 2. Rim/Border (Glossy)
      final borderPaint = Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2.0 // Slightly thicker
        ..color = orb.color.withOpacity(0.6); // Increased from 0.4
      canvas.drawCircle(Offset(orb.x, orb.y), orb.radius, borderPaint);

      // 3. Specular Highlight (The "Glass" reflection) - Top Left
      final highlightPaint = Paint()
        ..shader = RadialGradient(
          colors: [Colors.white.withOpacity(0.7), Colors.white.withOpacity(0.0)],
          stops: const [0.0, 1.0],
          center: Alignment.topLeft,
          radius: 0.8,
        ).createShader(Rect.fromCircle(center: Offset(orb.x - orb.radius*0.3, orb.y - orb.radius*0.3), radius: orb.radius * 0.5));
      
      // Draw oval for reflection
      canvas.drawOval(
        Rect.fromCenter(
          center: Offset(orb.x - orb.radius*0.35, orb.y - orb.radius*0.35), 
          width: orb.radius * 0.6, 
          height: orb.radius * 0.4
        ), 
        Paint()..color = Colors.white.withOpacity(0.4)..maskFilter = const MaskFilter.blur(BlurStyle.normal, 3)
      );

      // 4. Inner Glow (Bottom Right)
      final glowPaint = Paint()
         ..color = orb.color.withOpacity(0.2)
         ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 10);
      canvas.drawCircle(Offset(orb.x + orb.radius*0.3, orb.y + orb.radius*0.3), orb.radius * 0.6, glowPaint);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}
