import 'dart:math';
import 'package:flutter/material.dart';

enum ParticleType {
  fire,
  snow,
  heart,
}

class ParticleRain extends StatefulWidget {
  final ParticleType type;
  final Color color;
  final int particleCount;

  const ParticleRain({
    super.key,
    required this.type,
    this.color = Colors.red,
    this.particleCount = 50,
  });

  @override
  State<ParticleRain> createState() => _ParticleRainState();
}

class _ParticleRainState extends State<ParticleRain> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late List<Particle> _particles;
  final Random _random = Random();

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 1),
    )..repeat();
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _initializeParticles();
  }

  void _initializeParticles() {
    final size = MediaQuery.of(context).size;
    _particles = List.generate(widget.particleCount, (index) {
      return Particle(
        screenSize: size,
        type: widget.type,
        random: _random,
      );
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        for (var particle in _particles) {
          particle.update();
        }
        
        return CustomPaint(
          painter: ParticlePainter(
            particles: _particles,
            defaultColor: widget.color,
            type: widget.type,
          ),
          size: Size.infinite,
        );
      },
    );
  }
}

// ... (imports remain matching original file)

class Particle {
  final Size screenSize;
  final ParticleType type;
  final Random random;
  
  late double x;
  late double y;
  late double speed;
  late double size;
  late double opacity;
  late double driftOffset; // For sine wave calculation
  late double driftSpeed;  // How fast it sways
  late double depth;      // 0.0 (far) to 1.0 (near)

  Particle({
    required this.screenSize,
    required this.type,
    required this.random,
  }) {
    _reset(randomY: true);
  }

  void _reset({bool randomY = false}) {
    x = random.nextDouble() * screenSize.width;
    
    // Depth Calculation: 
    // Small particles are "far away" -> slower, more transparent
    // Large particles are "close" -> faster, more opaque
    depth = random.nextDouble(); 
    
    if (type == ParticleType.fire) {
      // Fire logic (Keep existing)
      y = randomY ? random.nextDouble() * screenSize.height : screenSize.height + 10;
      speed = 1.0 + random.nextDouble() * 3.0;
      size = 2.0 + random.nextDouble() * 4.0;
      opacity = 0.5 + random.nextDouble() * 0.5;
       driftOffset = 0;
       driftSpeed = 0;
    } else if (type == ParticleType.snow) {
      // REALISTIC SNOW PHYSICS
      y = randomY ? random.nextDouble() * screenSize.height : -20;
      
      // Physics based on Depth
      speed = 1.0 + (depth * 3.5); // Range: 1.0 to 4.5
      size = 1.5 + (depth * 4.5);  // Range: 1.5 to 6.0
      opacity = 0.3 + (depth * 0.6); // Range: 0.3 to 0.9

      // Sway Physics
      driftOffset = random.nextDouble() * 100; // Random starting phase
      driftSpeed = 0.02 + (random.nextDouble() * 0.03); // Random sway frequency
    } else {
      // Heart/Default
      y = randomY ? random.nextDouble() * screenSize.height : -20;
      speed = 1.0 + random.nextDouble() * 2.0;
      size = 10.0 + random.nextDouble() * 10.0;
      opacity = 0.5 + random.nextDouble() * 0.5;
      driftOffset = 0;
      driftSpeed = 0;
    }
  }

  void update() {
    if (type == ParticleType.snow) {
      // Snow Physics Update
      y += speed;
      
      // Calculate horizontal sway using Sine wave
      driftOffset += driftSpeed;
      x += sin(driftOffset) * (0.5 + (depth * 1.5)); // Closer flakes sway more
      
      // Wind Effect (Always slight drift to right)
      x += 0.2; 

    } else if (type == ParticleType.fire) {
      y -= speed;
      if (y < screenSize.height * 0.6) opacity -= 0.01;
      x += (random.nextDouble() - 0.5) * 0.5;
    } else {
      y += speed;
      x += (random.nextDouble() - 0.5) * 0.5;
    }

    // Boundary Checks
    if (type == ParticleType.fire) {
       if (y < -10 || opacity <= 0) _reset();
    } else {
       if (y > screenSize.height + 20) _reset();
       if (x > screenSize.width + 10) x = -10; // Wrap horizontal
       if (x < -10) x = screenSize.width + 10;
    }
  }
}

class ParticlePainter extends CustomPainter {
  final List<Particle> particles;
  final Color defaultColor;
  final ParticleType type;

  ParticlePainter({
    required this.particles,
    required this.defaultColor,
    required this.type,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()..color = defaultColor;

    for (var particle in particles) {
      // Dynamic Opacity per particle
      paint.color = defaultColor.withOpacity(particle.opacity.clamp(0.0, 1.0));
      
      if (type == ParticleType.heart) {
        _drawHeart(canvas, paint, particle.x, particle.y, particle.size);
      } else if (type == ParticleType.snow) {
         // Soft Snowball (Radial Gradient for fluffiness)
         final gradient = RadialGradient(
           colors: [
             Colors.white.withOpacity(particle.opacity), 
             Colors.white.withOpacity(0.0)
           ],
           stops: const [0.4, 1.0],
         );
         
         final snowPaint = Paint()
           ..shader = gradient.createShader(Rect.fromCircle(center: Offset(particle.x, particle.y), radius: particle.size));
           
         canvas.drawCircle(Offset(particle.x, particle.y), particle.size, snowPaint);
      } else {
        // Standard Circle (Fire/Other)
        canvas.drawCircle(Offset(particle.x, particle.y), particle.size, paint);
      }
    }
  }

  void _drawHeart(Canvas canvas, Paint paint, double x, double y, double size) {
    Path path = Path();
    path.moveTo(x, y + size / 4);
    path.cubicTo(
        x - size / 2, y - size / 2, 
        x - size, y + size / 3, 
        x, y + size);
    path.cubicTo(
        x + size, y + size / 3, 
        x + size / 2, y - size / 2, 
        x, y + size / 4);
    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}
