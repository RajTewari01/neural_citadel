import 'dart:math';
import 'package:flutter/material.dart';

class MatrixRain extends StatefulWidget {
  final Color color;
  final double speed;

  const MatrixRain({
    super.key,
    this.color = const Color(0xFF00FF9D),
    this.speed = 1.0,
  });

  @override
  State<MatrixRain> createState() => _MatrixRainState();
}

class _MatrixRainState extends State<MatrixRain> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late List<Stream> _streams;
  final Random _random = Random();

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 1), // Loop duration doesn't matter much (infinite)
    )..repeat();
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _initializeStreams();
  }

  void _initializeStreams() {
    final size = MediaQuery.of(context).size;
    final int columnCount = (size.width / 16).ceil(); // ~16px font width
    
    _streams = List.generate(columnCount, (index) {
      return Stream(
        column: index,
        screenHeight: size.height,
        speed: (2.0 + _random.nextDouble() * 4.0) * widget.speed,
        length: 5 + _random.nextInt(20),
        startDelay: _random.nextDouble() * 2000,
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
        // Update stream positions
        for (var stream in _streams) {
          stream.update();
        }
        
        return CustomPaint(
          painter: MatrixRainPainter(
            streams: _streams,
            color: widget.color,
          ),
          size: Size.infinite,
        );
      },
    );
  }
}

class Stream {
  final int column;
  final double screenHeight;
  final double speed;
  final int length;
  final double startDelay; // Simulated delay
  
  double y = -100;
  List<String> chars = [];
  
  Stream({
    required this.column,
    required this.screenHeight,
    required this.speed,
    required this.length,
    required this.startDelay,
  }) {
    y = -100 - startDelay;
    _generateChars();
  }
  
  void _generateChars() {
    chars = List.generate(length, (index) => _getRandomChar());
  }
  
  String _getRandomChar() {
    const chars = 'abcdefghijklmnopqrstuvwxyz0123456789ﾊﾐﾋｰｳｼﾅﾓﾆｻﾜﾂｵﾘｱﾎﾃﾏｹﾒｴｶｷﾑﾕﾗｾﾈｽﾀﾇﾍ';
    return chars[Random().nextInt(chars.length)];
  }
  
  void update() {
    y += speed;
    if (y - (length * 16) > screenHeight) {
      y = -100;
      _generateChars(); // Regenerate chars for next fall
    }
    
    // Randomly flip characters occasionally
    if (Random().nextDouble() < 0.05) {
      chars[Random().nextInt(length)] = _getRandomChar();
    }
  }
}

class MatrixRainPainter extends CustomPainter {
  final List<Stream> streams;
  final Color color;

  MatrixRainPainter({required this.streams, required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()..color = color;
    final textStyle = TextStyle(
      color: color,
      fontSize: 14,
      fontFamily: 'Consolas', // Fallback monospaced
      fontWeight: FontWeight.bold,
    );

    for (var stream in streams) {
      if (stream.y < 0) continue; // Offscreen top
      
      for (int i = 0; i < stream.length; i++) {
        final charY = stream.y - (i * 16);
        
        if (charY < -20 || charY > size.height + 20) continue;

        // Calculate opacity based on position in stream (head is bright, tail is dim)
        double opacity = 1.0 - (i / stream.length);
        opacity = opacity.clamp(0.0, 1.0);
        
        // Head character is white
        final charColor = (i == 0) ? Colors.white : color.withOpacity(opacity);
        
        final span = TextSpan(
          text: stream.chars[i],
          style: textStyle.copyWith(color: charColor, fontSize: 14),
        );
        
        final textPainter = TextPainter(
          text: span,
          textDirection: TextDirection.ltr,
        );
        
        textPainter.layout();
        textPainter.paint(canvas, Offset(stream.column * 16.0, charY));
      }
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}
