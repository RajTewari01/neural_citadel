import 'package:flutter/material.dart';
import 'package:flutter/scheduler.dart';
import 'dart:math' as math;
import '../../services/physics_manager.dart';
import 'modes/gravity_orbs_painter.dart';
import 'modes/matrix_rain_painter.dart';
import 'modes/cyber_grid_painter.dart';
import 'modes/nebula_pulse_painter.dart';
import 'modes/liquid_metal_painter.dart';
// New V21 Physics
import 'modes/black_hole_painter.dart';
import 'modes/digital_dna_painter.dart';
import 'modes/hexagon_hive_painter.dart';
import 'modes/starfield_warp_painter.dart';
import 'modes/audio_wave_painter.dart';
import 'modes/chinese_scroll_painter.dart';
import 'dart:io';

class PhysicsBackground extends StatefulWidget {
  final PhysicsMode mode;
  final Widget? child;

  const PhysicsBackground({
    super.key, 
    required this.mode,
    this.child,
  });

  @override
  State<PhysicsBackground> createState() => _PhysicsBackgroundState();
}

class _PhysicsBackgroundState extends State<PhysicsBackground> with SingleTickerProviderStateMixin {
  late Ticker _ticker;
  double _time = 0.0;

  @override
  void initState() {
    super.initState();
    _ticker = createTicker(_onTick)..start();
  }

  @override
  void dispose() {
    _ticker.dispose();
    super.dispose();
  }

  void _onTick(Duration elapsed) {
    setState(() {
      _time = elapsed.inMilliseconds / 1000.0;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        Positioned.fill(
          child: Container(color: Colors.black), // Base layer
        ),
        Positioned.fill(
          child: ColorFiltered(
            colorFilter: ColorFilter.matrix([
               1, 0, 0, 0, 0,
               0, 1, 0, 0, 0,
               0, 0, 1, 0, 0,
               0, 0, 0, PhysicsManager().physicsOpacity, 0,
            ]),
            child: _buildPhysicsLayer(),
          ),
        ),
        Positioned.fill(
          child: CustomPaint(
            painter: _ScanlinePainter(_time),
          ),
        ),
        if (widget.child != null)
          Positioned.fill(child: widget.child!),
      ],
    );
  }

  Widget _buildPhysicsLayer() {
    switch (widget.mode) {
      case PhysicsMode.gravityOrbs:
        return CustomPaint(painter: GravityOrbsPainter(time: _time));
      case PhysicsMode.matrixRain:
        return CustomPaint(painter: MatrixRainPainter(time: _time));
      case PhysicsMode.cyberGrid:
        return CustomPaint(painter: CyberGridPainter(time: _time));
      case PhysicsMode.nebulaPulse:
        return CustomPaint(painter: NebulaPulsePainter(time: _time));
      case PhysicsMode.liquidMetal:
        return CustomPaint(painter: LiquidMetalPainter(time: _time));
      case PhysicsMode.blackHole:
        return CustomPaint(painter: BlackHolePainter(time: _time));
      case PhysicsMode.digitalDna:
        return CustomPaint(painter: NetworkDNA(time: _time));
      case PhysicsMode.hexagonHive:
        return CustomPaint(painter: HexagonHivePainter(time: _time));
      case PhysicsMode.starfieldWarp:
        return CustomPaint(painter: StarfieldWarpPainter(time: _time));
      case PhysicsMode.audioWave:
        return CustomPaint(painter: AudioWavePainter(time: _time));
      case PhysicsMode.chineseScroll:
        return CustomPaint(painter: ChineseScrollPainter(time: _time));
      case PhysicsMode.customPhoto:
         final path = PhysicsManager().customPhotoPath;
         if (path != null && path.isNotEmpty) { // Need dart:io 
            return Stack(
               fit: StackFit.expand,
               children: [
                   // Base Image (Low Opacity for Hologram feel)
                   Opacity(
                       opacity: 0.6,
                       child: Image.file(
                           File(path), 
                           fit: BoxFit.cover,
                           color: Colors.cyanAccent.withOpacity(0.3),
                           colorBlendMode: BlendMode.screen,
                       )
                   ),
                   // Holographic Noise/Scan Overlay
                   CustomPaint(painter: _ScanlinePainter(_time, isHologram: true)),
               ]
            );
         }
         return Container(color: Colors.black);
      default:
        return Container();
    }
  }
}

class _ScanlinePainter extends CustomPainter {
  final double time;
  final bool isHologram;
  _ScanlinePainter(this.time, {this.isHologram = false});

  @override
  void paint(Canvas canvas, Size size) {
    if (isHologram) {
       // Hologram Mode: Thicker, animated VHS scrolling bars
       final paint = Paint()
         ..color = Colors.cyanAccent.withOpacity(0.05)
         ..style = PaintingStyle.fill;
         
       double barHeight = 20.0;
       double offset = (time * 100) % (size.height + barHeight);
       
       canvas.drawRect(Rect.fromLTWH(0, offset - barHeight, size.width, barHeight), paint);
       
       // Slower secondary bar
       double offset2 = (time * 40) % (size.height + barHeight);
       canvas.drawRect(Rect.fromLTWH(0, size.height - offset2, size.width, barHeight * 2), paint..color = Colors.purpleAccent.withOpacity(0.03));
       
    } else {
       // Standard Mode: Static fine pixel grid lines
       final paint = Paint()
         ..color = Colors.white.withOpacity(0.02)
         ..strokeWidth = 1.0;

       for (double i = 0; i < size.height; i += 4) {
         canvas.drawLine(Offset(0, i), Offset(size.width, i), paint);
       }
    }
  }

  @override
  bool shouldRepaint(covariant _ScanlinePainter oldDelegate) => isHologram ? true : false; 
}
