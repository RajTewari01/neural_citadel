import 'package:flutter/material.dart';
import 'dart:math';

class ChineseScrollPainter extends CustomPainter {
  final double time;
  static final List<_InkParticle> _particles = [];
  static final List<_Watermark> _watermarks = [];
  static final Random _rnd = Random();
  
  ChineseScrollPainter({required this.time});

  @override
  void paint(Canvas canvas, Size size) {
    // 1. Mist Background
    final mistPaint = Paint()
      ..shader = LinearGradient(
        begin: Alignment.topCenter,
        end: Alignment.bottomCenter,
        colors: [Colors.transparent, Colors.white.withOpacity(0.05), Colors.white.withOpacity(0.1)],
      ).createShader(Rect.fromLTWH(0, size.height * 0.4, size.width, size.height * 0.6));
    canvas.drawRect(Rect.fromLTWH(0, size.height * 0.4, size.width, size.height * 0.6), mistPaint);

    // 2. Procedural Ink Mountains
    final path = Path();
    path.moveTo(0, size.height);
    path.lineTo(0, size.height * 0.75);
    path.quadraticBezierTo(size.width * 0.25, size.height * 0.65, size.width * 0.5, size.height * 0.8);
    path.quadraticBezierTo(size.width * 0.75, size.height * 0.95, size.width, size.height * 0.7);
    path.lineTo(size.width, size.height);
    path.close();
    canvas.drawPath(path, Paint()..color = Colors.white.withOpacity(0.03)..style = PaintingStyle.fill);

    // 3. Ink Particles (Drifting up)
    if (_particles.isEmpty) {
        for (int i = 0; i < 40; i++) _particles.add(_InkParticle(size.width, size.height));
    }
    for (var p in _particles) {
        p.y -= p.speed;
        p.x += sin(time + p.phase) * 0.5; // Drift sideways
        if (p.y < 0) p.reset(size.width, size.height, bottomAlign: true);
        
        canvas.drawCircle(Offset(p.x, p.y), p.radius, Paint()..color = Colors.white.withOpacity(p.opacity.clamp(0.0, 1.0)));
    }

    // 4. Epic Blurring Watermarks (Chinese Characters)
    if (_watermarks.isEmpty) {
        _watermarks.add(_Watermark("创造", size.width * 0.2, size.height * 0.3, 0));
        _watermarks.add(_Watermark("堡垒", size.width * 0.8, size.height * 0.6, 2));
        _watermarks.add(_Watermark("核心", size.width * 0.3, size.height * 0.8, 4));
        _watermarks.add(_Watermark("链接", size.width * 0.7, size.height * 0.2, 6));
    }

    final textPainter = TextPainter(textDirection: TextDirection.ltr);
    
    for (var w in _watermarks) {
        // Slow cycle based on time
        double cycle = (time * 0.2 + w.phaseOffset) % (pi * 2);
        double progress = (sin(cycle) + 1) / 2; // 0.0 to 1.0
        
        // Scale and blur based on progress
        double scale = 1.0 + progress * 0.5;
        double blurRadius = (1.0 - progress) * 20.0; // High blur when fading out
        double opacity = progress * 0.15; // Max opacity 0.15 for watermark
        
        if (opacity > 0.01) {
            textPainter.text = TextSpan(
               text: w.text,
               style: TextStyle(
                  color: Colors.white.withOpacity(opacity.clamp(0.0, 1.0)), 
                  fontSize: 100 * scale, 
                  fontWeight: FontWeight.bold,
                  shadows: [
                     Shadow(color: Colors.cyanAccent.withOpacity((opacity * 0.5).clamp(0.0, 1.0)), blurRadius: blurRadius),
                  ]
               )
            );
            textPainter.layout();
            canvas.save();
            canvas.translate(w.x - textPainter.width / 2, w.y - textPainter.height / 2);
            textPainter.paint(canvas, Offset.zero);
            canvas.restore();
        }
    }
    
    // 5. Vertical Poetry (Couplets)
    _drawVerticalCouplet(canvas, "天地玄黄", size.width * 0.1, size.height * 0.15, time);
    _drawVerticalCouplet(canvas, "宇宙洪荒", size.width * 0.9, size.height * 0.45, time + pi);
  }

  void _drawVerticalCouplet(Canvas canvas, String text, double x, double startY, double t) {
     final textPainter = TextPainter(textDirection: TextDirection.ltr);
     double y = startY;
     
     // Gentle floating effect
     y += sin(t * 0.5) * 20.0;
     
     for (int i = 0; i < text.length; i++) {
        textPainter.text = TextSpan(
           text: text[i],
           style: TextStyle(
              color: Colors.white.withOpacity(0.3), 
              fontSize: 24,
              shadows: [Shadow(color: Colors.cyanAccent.withOpacity(0.2), blurRadius: 10)]
           )
        );
        textPainter.layout();
        textPainter.paint(canvas, Offset(x - textPainter.width / 2, y));
        y += textPainter.height + 16; // Spacing between characters
     }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}

class _Watermark {
   String text;
   double x, y;
   double phaseOffset;
   _Watermark(this.text, this.x, this.y, this.phaseOffset);
}

class _InkParticle {
   double x = 0, y = 0, speed = 0, opacity = 0, radius = 0, phase = 0;
   
   _InkParticle(double w, double h) {
       reset(w, h, bottomAlign: false);
   }
   
   void reset(double w, double h, {bool bottomAlign = false}) {
       final rnd = ChineseScrollPainter._rnd;
       x = rnd.nextDouble() * w;
       y = bottomAlign ? h + rnd.nextDouble() * 100 : rnd.nextDouble() * h;
       speed = 0.5 + rnd.nextDouble() * 1.5;
       opacity = 0.1 + rnd.nextDouble() * 0.3;
       radius = 1.0 + rnd.nextDouble() * 3.0;
       phase = rnd.nextDouble() * pi * 2;
   }
}
