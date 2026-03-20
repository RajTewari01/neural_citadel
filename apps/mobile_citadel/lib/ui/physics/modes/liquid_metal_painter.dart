import 'package:flutter/material.dart';
import 'dart:math';

// Simulating Liquid Metal with Metaballs approach (Canvas based for performance without heavy shaders for now)
class LiquidMetalPainter extends CustomPainter {
  final double time;
  static final List<Blob> _blobs = [];
  
  LiquidMetalPainter({required this.time});

  @override
  void paint(Canvas canvas, Size size) {
    if (_blobs.isEmpty) _initBlobs(size);
    _updateBlobs(size);
    
    // In a real shader, we'd threshold a gradient field.
    // For Canvas, we draw overlapping blurred circles and hope the visual "merging" works enough for V1.
    // Or we stick to a simpler "Ripples" effect if metaballs are too heavy.
    // Let's go with "Ripples" simulating mercury surface tension.
    
    final paint = Paint()
      ..color = Colors.grey[300]! // Mercury Silver
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 15);
      
    for (var blob in _blobs) {
       canvas.drawCircle(blob.position, blob.radius, paint);
       // Highlight
       canvas.drawCircle(blob.position + const Offset(-5,-5), blob.radius * 0.3, Paint()..color = Colors.white.withOpacity(0.8)..maskFilter = const MaskFilter.blur(BlurStyle.normal, 5));
    }
  }
  
  void _initBlobs(Size size) {
    final rnd = Random();
    for(int i=0; i<8; i++) {
      _blobs.add(Blob(
        position: Offset(rnd.nextDouble() * size.width, rnd.nextDouble() * size.height),
        velocity: Offset((rnd.nextDouble()-0.5)*3, (rnd.nextDouble()-0.5)*3),
        radius: 40 + rnd.nextDouble() * 40,
      ));
    }
  }
  
  void _updateBlobs(Size size) {
     for (var blob in _blobs) {
        blob.position += blob.velocity;
        if (blob.position.dx < 0 || blob.position.dx > size.width) blob.velocity = Offset(-blob.velocity.dx, blob.velocity.dy);
        if (blob.position.dy < 0 || blob.position.dy > size.height) blob.velocity = Offset(blob.velocity.dx, -blob.velocity.dy);
        
        // Simple attraction to center to simulate cohesion?
        // blob.velocity += (Offset(size.width/2, size.height/2) - blob.position) * 0.001;
     }
  }

  @override
  bool shouldRepaint(covariant LiquidMetalPainter oldDelegate) => true;
}

class Blob {
  Offset position;
  Offset velocity;
  double radius;
  Blob({required this.position, required this.velocity, required this.radius});
}
