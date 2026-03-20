import 'dart:math';
import 'package:flutter/material.dart';
import 'package:flutter/scheduler.dart';
import 'package:google_fonts/google_fonts.dart';

enum RainType {
  matrixGreen,
  cyanCyber,
  redAlert,
  purpleHaze,
  goldenData,
  blueDrops,
  whiteSnow,
  fireEmbers,
  binaryStorm,
  asciiArt,
  starfield, // Now with Rocket Dog!
  neonRain,
  crimsonCode,
  violetStream,
  orangeFlux,
  emeraldCity,
  midnightRain,
  glitchStatic,
  pinkRetro,
  toxicSludge,
  none
}

class RainConfig {
  final Color color;
  final double speed;
  final double fontSize;
  final List<String> chars;
  final bool isParticles; 
  final bool isMatrixStream;

  const RainConfig({
    required this.color,
    required this.speed,
    this.fontSize = 14,
    this.chars = const [],
    this.isParticles = false,
    this.isMatrixStream = false,
  });
}


enum EntityType { standard, rocket, meteorite, star, nebula, planet, dust }

class RainDrop {
  double x;
  double y;
  double speed;
  String text;
  List<String> streamChars;
  double size;
  double opacity;
  Color color;
  
  // Physics Extensions
  EntityType type;
  double vx; // Velocity X
  double vy; // Velocity Y
  double angle; // Rotation

  RainDrop({
    required this.x, 
    required this.y, 
    required this.speed, 
    required this.text, 
    this.streamChars = const [],
    required this.size, 
    required this.opacity,
    required this.color,
    this.type = EntityType.standard,
    this.vx = 0.0,
    this.vy = 0.0,
    this.angle = 0.0,
  });
}

class RainOverlay extends StatefulWidget {
  final RainType type;
  final Widget? child;

  const RainOverlay({super.key, required this.type, this.child});

  @override
  State<RainOverlay> createState() => _RainOverlayState();
}

class _RainOverlayState extends State<RainOverlay> with SingleTickerProviderStateMixin {
  late Ticker _ticker;
  final Random _random = Random();
  final List<RainDrop> _drops = [];
  RainDrop? _rocket; // The Hero Rocket
  Size? _size;
  
  static const Map<RainType, RainConfig> _configs = {
    RainType.matrixGreen: RainConfig(
      color: Color(0xFF00FF41), 
      speed: 12.0, 
      chars: ['0', '1', 'ﾊ', 'ﾐ', 'ﾋ', 'ｰ', 'ｳ', 'ｼ', 'ﾅ', 'ﾓ', 'ﾆ', 'ｻ', 'ﾚ', 'ｹ', 'ﾒ'], 
      isMatrixStream: true
    ),
    RainType.cyanCyber: RainConfig(
      color: Color(0xFF00E5FF), 
      speed: 10.0, 
      chars: ['<', '>', '/', '{', '}', ';', '*', '?', '!', '0', '1', 'A', 'X', 'Z', '9', 'ﾊ', 'ﾐ', 'ﾋ', 'ｰ'], 
      isMatrixStream: true
    ),
    RainType.redAlert: RainConfig(color: Colors.redAccent, speed: 7.0, isParticles: true),
    RainType.purpleHaze: RainConfig(color: Colors.purpleAccent, speed: 3.0, isParticles: true),
    RainType.goldenData: RainConfig(color: Colors.amber, speed: 4.0, chars: ['\$', '€', '£', '₿', '%']),
    RainType.blueDrops: RainConfig(color: Colors.blue, speed: 9.0, isParticles: true),
    RainType.whiteSnow: RainConfig(color: Colors.white, speed: 2.0, isParticles: true),
    RainType.fireEmbers: RainConfig(color: Colors.deepOrange, speed: -3.0, isParticles: true),
    RainType.binaryStorm: RainConfig(color: Colors.green, speed: 10.0, chars: ['0', '1']),
    RainType.asciiArt: RainConfig(color: Colors.white70, speed: 5.0, chars: ['@', '#', '&', '%', '=', '+', '-', ':']),
    RainType.starfield: RainConfig(color: Colors.white, speed: 4.0, isParticles: true), // Base speed for stars
    RainType.neonRain: RainConfig(color: Colors.white, speed: 5.0, isParticles: true),
    RainType.crimsonCode: RainConfig(color: Color(0xFFDC143C), speed: 6.0, chars: ['E', 'R', 'R', 'O', 'R', '!', 'X']),
    RainType.violetStream: RainConfig(color: Color(0xFF8A2BE2), speed: 4.5, isParticles: false, chars: ['⚛', '⚡', '☊', '✈']),
    RainType.orangeFlux: RainConfig(color: Colors.orangeAccent, speed: 5.5, isParticles: true),
    RainType.emeraldCity: RainConfig(color: Color(0xFF50C878), speed: 3.0, isParticles: true),
    RainType.midnightRain: RainConfig(color: Color(0xFF191970), speed: 12.0, isParticles: true),
    RainType.glitchStatic: RainConfig(color: Colors.grey, speed: 15.0, chars: ['░', '▒', '▓', '█']),
    RainType.pinkRetro: RainConfig(color: Color(0xFFFF007F), speed: 4.0, chars: ['♥', '★', '♫', '✿']),
    RainType.toxicSludge: RainConfig(color: Color(0xFFADFF2F), speed: 2.0, isParticles: false, chars: ['☣', '☠', '☢'])
  };

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

  @override
  void didUpdateWidget(RainOverlay oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.type != widget.type) {
       _drops.clear(); 
       _rocket = null;
    }
  }

  void _onTick(Duration elapsed) {
    if (_size == null || widget.type == RainType.none) return;

    final config = _configs[widget.type] ?? _configs[RainType.matrixGreen]!;
    
    // -------------------------------------------------------------------------
    // ROCKET LOGIC (Professional "Game Feel" Sim)
    // -------------------------------------------------------------------------
    if (widget.type == RainType.starfield) {
        if (_rocket == null) {
            _rocket = RainDrop(
                x: _size!.width / 2, y: _size!.height - 150, 
                speed: 0, text: '', size: 30, opacity: 1.0,  // Bigger for detail
                color: Colors.white, type: EntityType.rocket,
                vx: 0, vy: 0 
            );
            _drops.add(_rocket!);
        }

        // PREDICTIVE STEERING AI (Not "Flee")
        // The rocket looks ahead and steers gently to find open space.
        double steerX = 0;
        double steerY = 0;
        
        // 1. Center Tether (The "Home Base")
        // Gentle pull to center-screen so it defaults to a good composition
        double centerX = _size!.width / 2;
        double dx = centerX - _rocket!.x;
        steerX += dx * 0.005; // Very gentle drift back

        // 2. Obstacle Avoidance (Raycast)
        for (var drop in _drops) {
           if (drop == _rocket || drop.type == EntityType.star) continue; // Ignore faint stars
           
           double dist = sqrt(pow(_rocket!.x - drop.x, 2) + pow(_rocket!.y - drop.y, 2));
           
           // Look Further Ahead (350px) for smooth early turns
           if (dist < 350) { 
              // Calculate "Threat Factor"
              // If obstacles is directly below us (blocking path), steer hard.
              // If it's to the side, ignore.
              double riskFactor = (350 - dist) / 350; // 0.0 to 1.0 (Close = 1.0)
              
              double dxObs = _rocket!.x - drop.x;
              // Push AWAY from obstacle, weighted by risk
              steerX += (dxObs / dist) * 4.0 * riskFactor;
           }
        }

        // 3. Smooth Bounds (Never touch edges)
        double margin = 120;
        if (_rocket!.x < margin) steerX += 2.0;
        if (_rocket!.x > _size!.width - margin) steerX -= 2.0;
        // Keep altitude steady
        double targetY = _size!.height - 150;
        steerY += (targetY - _rocket!.y) * 0.05;

        // 4. Apply Physics (Heavy Mass Feel)
        _rocket!.vx += steerX * 0.8; // Acceleration
        _rocket!.vy += steerY * 0.1;
        
        // Friction / Drag (Crucial for stability)
        _rocket!.vx *= 0.94; // 6% drag per frame
        _rocket!.vy *= 0.90;

        _rocket!.x += _rocket!.vx;
        _rocket!.y += _rocket!.vy;
        
        // Clamp
        _rocket!.x = _rocket!.x.clamp(margin, _size!.width - margin);

        // 6. Calculate facing angle (BANKING ONLY)
        // FORCE LOCK: The ship always faces UP (-pi/2)
        // We do NOT rotate the canvas for heading, we only roll in 3D.
        _rocket!.angle = -pi / 2; 
    }

    // -------------------------------------------------------------------------
    // SPAWN LOGIC (Stars & Meteors)
    // -------------------------------------------------------------------------
    if (_drops.length < (widget.type == RainType.starfield ? 70 : 100)) { 
       if (_random.nextDouble() < 0.1) {
         _spawnDrop(config);
       }
    }

    setState(() {
      for (var drop in _drops) {
        if (drop.type == EntityType.rocket) continue; 

        drop.y += drop.speed;
        drop.x += drop.vx;

        // Rotate Asteroids
        if (drop.type == EntityType.meteorite) {
           drop.angle += 0.05; // Spin
        }

        // Standard Rain Logic (Matrix Stream mutation)
         if (config.isMatrixStream && drop.streamChars.isNotEmpty && _random.nextDouble() < 0.05) {
            int idx = _random.nextInt(drop.streamChars.length);
            drop.streamChars[idx] = config.chars[_random.nextInt(config.chars.length)];
         }

        // Wrap Logic
        if (drop.y > _size!.height + 50) { 
           drop.y = -50;
           drop.x = _random.nextDouble() * _size!.width;
           
           if (widget.type == RainType.starfield) {
              if (drop.type == EntityType.meteorite) {
                 if (_random.nextDouble() > 0.3) _resetAsStar(drop); // Recycle to star
                 else _resetAsMeteor(drop);
              } else {
                 if (_random.nextDouble() < 0.05) _resetAsMeteor(drop); // Star becomes meteor
                 else _resetAsStar(drop);
              }
           }
        } 
      }
    });
  }

  void _resetAsStar(RainDrop drop) {
      drop.type = EntityType.star;
      // 3 Layers of Depth
      double depth = _random.nextDouble();
      if (depth < 0.6) {
         // Background (Slow, Small)
         drop.speed = 1.0 + _random.nextDouble();
         drop.size = 1.5 + _random.nextDouble();
         drop.opacity = 0.3;
      } else if (depth < 0.9) {
         // Midground
         drop.speed = 3.0 + _random.nextDouble() * 2.0;
         drop.size = 2.5 + _random.nextDouble();
         drop.opacity = 0.6;
      } else {
         // Foreground (Fast)
         drop.speed = 6.0 + _random.nextDouble() * 3.0;
         drop.size = 3.5;
         drop.opacity = 0.9;
      }
      drop.vx = 0; // Stars fall straight rel to motion
      drop.color = Colors.white;
  }

  void _resetAsMeteor(RainDrop drop) {
      drop.type = EntityType.meteorite;
      drop.speed = 8.0 + _random.nextDouble() * 4.0; // Slower, heavier feel
      drop.vx = (_random.nextDouble() - 0.5) * 2.0;  // Slight drift
      drop.size = 15.0 + _random.nextDouble() * 10.0; // BIG rocks
      drop.color = const Color(0xFF5D4037); // Brown asteroid color
      drop.opacity = 1.0;
  }

  void _spawnDrop(RainConfig config) {
     if (_size == null) return;
     
     double x = _random.nextDouble() * _size!.width;
     double y = config.speed > 0 ? -20 : _size!.height + 20;
     
     Color color = config.color;
     EntityType type = EntityType.standard;
     double vx = 0;
     double speed = config.speed * (0.8 + _random.nextDouble() * 0.4);
     double size = config.isParticles ? 2.0 + _random.nextDouble() * 4.0 : 14.0;

     // Starfield Special Spawning
     if (widget.type == RainType.starfield) {
         double roll = _random.nextDouble();
         
         // 1. DUST (Common - Speed Effect)
         if (roll < 0.4) {
             type = EntityType.dust;
             speed = 20.0 + _random.nextDouble() * 20.0; // Very fast
             size = 0.5 + _random.nextDouble(); // Tiny
             config = RainConfig(
               color: Colors.white.withOpacity(0.1 + _random.nextDouble() * 0.2),
               speed: speed,
             ); // Override config for color
         }
         // 2. METEORITE (Uncommon - Hazard)
         else if (roll < 0.45) {
             // Will be handled by _resetAsMeteor later or we set type here
             type = EntityType.meteorite;
         }
         // 3. NEBULA (Rare - Atmosphere)
         else if (roll < 0.46) {
             type = EntityType.nebula;
             speed = 0.5 + _random.nextDouble(); // Slow drift
             size = 200.0 + _random.nextDouble() * 300.0; // Massive
             List<Color> nebulaColors = [Colors.purple, Colors.blue, Colors.pink, Colors.teal];
             color = nebulaColors[_random.nextInt(nebulaColors.length)].withOpacity(0.1 + _random.nextDouble() * 0.15);
             vx = (_random.nextDouble() - 0.5) * 0.2; // Slight lateral drift
         }
         // 4. PLANET (Very Rare - Background)
         else if (roll < 0.4605) { // 0.05% chance
             type = EntityType.planet;
             speed = 0.2; // Very slow
             size = 80.0 + _random.nextDouble() * 100.0;
             color = Colors.transparent; 
             vx = _random.nextInt(3).toDouble(); // Type 0,1,2
         }
         // 5. STAR (Default)
         else {
             type = EntityType.star;
             // We'll let the standard init happen, then _resetAsStar fixes it
         }
     } else if (widget.type == RainType.neonRain) {
         color = Color.fromARGB(255, _random.nextInt(255), _random.nextInt(255), _random.nextInt(255));
     }

     List<String> stream = [];
     if (config.isMatrixStream) {
         int len = 10 + _random.nextInt(15);
         for(int i=0; i<len; i++) stream.add(config.chars[_random.nextInt(config.chars.length)]);
     }

     var d = RainDrop(
       x: x, y: y, speed: speed, 
       text: config.isParticles ? "" : stream.isNotEmpty ? stream.first : config.chars.isNotEmpty ? config.chars[_random.nextInt(config.chars.length)] : "", 
       streamChars: stream,
       size: size, opacity: 0.3 + _random.nextDouble() * 0.7,
       color: color, type: type, vx: vx
     );
     
     if (widget.type == RainType.starfield && type == EntityType.star) {
         _resetAsStar(d); // Apply depth logic immediately
     }
     
     _drops.add(d);
  }

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (ctx, constraints) {
        _size = Size(constraints.maxWidth, constraints.maxHeight);
        return Stack(
          children: [
            if (widget.child != null) widget.child!,
            if (widget.type != RainType.none)
              IgnorePointer(
                child: CustomPaint(
                  painter: RainPainter(_drops, widget.type),
                  size: Size.infinite,
                ),
              ),
          ],
        );
      },
    );
  }
}

class RainPainter extends CustomPainter {
  final List<RainDrop> drops;
  final RainType type;

  RainPainter(this.drops, this.type);

  @override
  void paint(Canvas canvas, Size size) {
    try {
      final textPainter = TextPainter(textDirection: TextDirection.ltr);
      final baseStyle = GoogleFonts.jetBrainsMono(height: 1.0);
      
      for (var drop in drops) {
        final paint = Paint()..color = drop.color.withOpacity(drop.opacity);

        // -----------------------
        // ROCKET PAINTING (4D TESSERACT DRIVE - ULTIMATE EDITION)
        // -----------------------
        if (drop.type == EntityType.rocket) {
           canvas.save();
           
           // 1. POSITIONING: "Stay at the Middle" logic
           double centerX = size.width / 2;
           double centerY = size.height * 0.75;
           
           // Apply slight sway based on 'real' physics x to feel responsive
           double sway = (drop.x - centerX) * 0.15;
           canvas.translate(centerX + sway, centerY);
           
           // 2. 4D ANIMATION PHASE
           double t = DateTime.now().millisecondsSinceEpoch / 1000.0;
           
           // 3. ROTATION
           double bank = -(drop.vx / 15.0).clamp(-1.0, 1.0) * (pi / 3);
           double pitch = (drop.vy / 10.0) * (pi / 6); 
           double cR = cos(bank); double sR = sin(bank);
           double cP = cos(pitch); double sP = sin(pitch);

           // ========== PART 0: SHIELD BUBBLE (Behind Everything) ==========
           // Hexagonal force field
           double shieldPulse = 0.8 + sin(t * 4) * 0.2;
           double shieldRadius = 70 * shieldPulse;
           Path shield = Path();
           for(int i=0; i<6; i++) {
               double angle = (pi / 3) * i - pi/2;
               double x = cos(angle) * shieldRadius;
               double y = sin(angle) * shieldRadius * 0.6; // Squash vertically
               if(i==0) shield.moveTo(x, y);
               else shield.lineTo(x, y);
           }
           shield.close();
           
           // Shield glow layers
           canvas.drawPath(shield, Paint()
             ..color=Colors.cyanAccent.withOpacity(0.05 * shieldPulse)
             ..style=PaintingStyle.fill
             ..maskFilter=MaskFilter.blur(BlurStyle.normal, 20));
           canvas.drawPath(shield, Paint()
             ..color=Colors.cyan.withOpacity(0.3 * shieldPulse)
             ..style=PaintingStyle.stroke
             ..strokeWidth=1.5
             ..maskFilter=MaskFilter.blur(BlurStyle.normal, 3));

           // ========== PART A: THE TESSERACT CORE (Color-Shifting Hypercube) ==========
           // Rainbow color based on time
           Color coreColor = HSVColor.fromAHSV(1.0, (t * 60) % 360, 0.8, 1.0).toColor();
           
           // Outer Cube (Large)
           List<List<double>> outerCube = [
              [-12,-12,-12], [12,-12,-12], [12,12,-12], [-12,12,-12],
              [-12,-12,12], [12,-12,12], [12,12,12], [-12,12,12]
           ];
           
           // Inner Cube (Small, spins opposite)
           List<List<double>> innerCube = [
              [-6,-6,-6], [6,-6,-6], [6,6,-6], [-6,6,-6],
              [-6,-6,6], [6,-6,6], [6,6,6], [-6,6,6]
           ];
           
           Paint outerCorePaint = Paint()..color=coreColor..style=PaintingStyle.stroke..strokeWidth=2;
           Paint innerCorePaint = Paint()..color=Colors.white..style=PaintingStyle.stroke..strokeWidth=1;
           Paint coreGlow = Paint()..color=coreColor.withOpacity(0.4)..maskFilter=MaskFilter.blur(BlurStyle.normal, 10);

           double spinOuter = t * 2.0;
           double spinInner = -t * 3.0; // Opposite direction, faster
           
           // Project Outer Cube
           List<Offset> outer2d = [];
           for(var v in outerCube) {
               double x = v[0], y = v[1], z = v[2];
               double x1 = x * cos(spinOuter) - z * sin(spinOuter);
               double z1 = x * sin(spinOuter) + z * cos(spinOuter);
               double y2 = y * cos(spinOuter*0.7) - z1 * sin(spinOuter*0.7);
               double z2 = y * sin(spinOuter*0.7) + z1 * cos(spinOuter*0.7);
               double scale = 1.0 + z2 * 0.015;
               outer2d.add(Offset(x1 * scale, y2 * scale));
           }
           
           // Project Inner Cube
           List<Offset> inner2d = [];
           for(var v in innerCube) {
               double x = v[0], y = v[1], z = v[2];
               double x1 = x * cos(spinInner) - z * sin(spinInner);
               double z1 = x * sin(spinInner) + z * cos(spinInner);
               double y2 = y * cos(spinInner*0.5) - z1 * sin(spinInner*0.5);
               double z2 = y * sin(spinInner*0.5) + z1 * cos(spinInner*0.5);
               double scale = 1.0 + z2 * 0.02;
               inner2d.add(Offset(x1 * scale, y2 * scale));
           }
           
           // Draw Core Glow (Behind)
           canvas.drawCircle(Offset.zero, 20, coreGlow);
           
           // Draw Outer Wireframe
           for(int i=0; i<4; i++) canvas.drawLine(outer2d[i], outer2d[(i+1)%4], outerCorePaint);
           for(int i=4; i<8; i++) canvas.drawLine(outer2d[i], outer2d[4 + (i+1)%4], outerCorePaint);
           for(int i=0; i<4; i++) canvas.drawLine(outer2d[i], outer2d[i+4], outerCorePaint);
           
           // Draw Inner Wireframe
           for(int i=0; i<4; i++) canvas.drawLine(inner2d[i], inner2d[(i+1)%4], innerCorePaint);
           for(int i=4; i<8; i++) canvas.drawLine(inner2d[i], inner2d[4 + (i+1)%4], innerCorePaint);
           for(int i=0; i<4; i++) canvas.drawLine(inner2d[i], inner2d[i+4], innerCorePaint);
           
           // Draw 4D Connections (Lines between inner and outer cubes)
           Paint conduitPaint = Paint()..color=coreColor.withOpacity(0.3)..strokeWidth=0.5;
           for(int i=0; i<8; i++) canvas.drawLine(inner2d[i], outer2d[i], conduitPaint);

           // ========== PART B: FLOATING HULL PLATES ==========
           List<List<double>> hull = [
               // Left Prow (Triangle)
               [-18, -50, 0], [-30, 15, 0], [-12, 5, 8],
               // Right Prow (Triangle)
               [18, -50, 0], [30, 15, 0], [12, 5, 8],
               // Left Stabilizer
               [-35, 25, -3], [-40, 40, -3], [-25, 35, 2],
               // Right Stabilizer
               [35, 25, -3], [40, 40, -3], [25, 35, 2],
               // Rear Engine Block Points
               [-20, 40, 0], [20, 40, 0], [0, 50, 0]
           ];
           
           List<Offset> hull2d = [];
           double breath = 1.0 + sin(t * 2) * 0.03;
           
           for(var v in hull) {
              double x = v[0] * breath, y = v[1] * breath, z = v[2];
              double x1 = x * cR - z * sR;
              double z1 = x * sR + z * cR;
              double y2 = y * cP - z1 * sP;
              hull2d.add(Offset(x1, y2));
           }
           
           Paint hullPaint = Paint()
             ..shader = LinearGradient(
                colors: [Color(0xFF1A1A2E), Color(0xFF0F0F1A)],
                begin: Alignment.topCenter, end: Alignment.bottomCenter
             ).createShader(Rect.fromLTWH(-50, -60, 100, 120))
             ..style = PaintingStyle.fill;
             
           Paint hullStroke = Paint()..color=coreColor.withOpacity(0.6)..style=PaintingStyle.stroke..strokeWidth=1;
           Paint hullGlow = Paint()..color=coreColor.withOpacity(0.2)..style=PaintingStyle.stroke..strokeWidth=4..maskFilter=MaskFilter.blur(BlurStyle.normal, 5);

           // Draw Hull Plates
           // Left Prow
           Path lProw = Path()..moveTo(hull2d[0].dx, hull2d[0].dy)..lineTo(hull2d[1].dx, hull2d[1].dy)..lineTo(hull2d[2].dx, hull2d[2].dy)..close();
           canvas.drawPath(lProw, hullGlow);
           canvas.drawPath(lProw, hullPaint);
           canvas.drawPath(lProw, hullStroke);

           // Right Prow
           Path rProw = Path()..moveTo(hull2d[3].dx, hull2d[3].dy)..lineTo(hull2d[4].dx, hull2d[4].dy)..lineTo(hull2d[5].dx, hull2d[5].dy)..close();
           canvas.drawPath(rProw, hullGlow);
           canvas.drawPath(rProw, hullPaint);
           canvas.drawPath(rProw, hullStroke);
           
           // Left Stabilizer
           Path lStab = Path()..moveTo(hull2d[6].dx, hull2d[6].dy)..lineTo(hull2d[7].dx, hull2d[7].dy)..lineTo(hull2d[8].dx, hull2d[8].dy)..close();
           canvas.drawPath(lStab, hullPaint);
           canvas.drawPath(lStab, hullStroke);
           
           // Right Stabilizer
           Path rStab = Path()..moveTo(hull2d[9].dx, hull2d[9].dy)..lineTo(hull2d[10].dx, hull2d[10].dy)..lineTo(hull2d[11].dx, hull2d[11].dy)..close();
           canvas.drawPath(rStab, hullPaint);
           canvas.drawPath(rStab, hullStroke);

           // ========== PART C: ENERGY CONDUITS (Core to Hull) ==========
           Paint conduit = Paint()..color=coreColor.withOpacity(0.5)..strokeWidth=1..maskFilter=MaskFilter.blur(BlurStyle.normal, 2);
           // Connect core to prow tips
           canvas.drawLine(Offset.zero, hull2d[0], conduit);
           canvas.drawLine(Offset.zero, hull2d[3], conduit);
           // Connect core to stabilizers
           canvas.drawLine(Offset.zero, hull2d[7], conduit);
           canvas.drawLine(Offset.zero, hull2d[10], conduit);

           // ========== PART D: ENGINE EXHAUST ==========
           // Engine Arc
           Path arc = Path()..moveTo(hull2d[12].dx, hull2d[12].dy);
           arc.quadraticBezierTo(hull2d[14].dx, hull2d[14].dy + 10, hull2d[13].dx, hull2d[13].dy);
           
           // Main Engine Glow
           canvas.drawPath(arc, Paint()..color=Colors.white..strokeWidth=4..style=PaintingStyle.stroke..maskFilter=MaskFilter.blur(BlurStyle.normal, 6));
           canvas.drawPath(arc, Paint()..color=coreColor..strokeWidth=2..style=PaintingStyle.stroke);
           
           // Warp Trail (Multiple fading echoes)
           for(int i=1; i<=6; i++) {
               canvas.save();
               canvas.translate(0, i * 5.0);
               canvas.scale(1.0 - (i*0.08));
               double opacity = (0.6 - i*0.1).clamp(0.0, 1.0);
               canvas.drawPath(arc, Paint()
                 ..color=coreColor.withOpacity(opacity)
                 ..style=PaintingStyle.stroke
                 ..strokeWidth=3
                 ..maskFilter=MaskFilter.blur(BlurStyle.normal, i*2.0));
               canvas.restore();
           }
           
           // Engine Particle Spray
           Random rand = Random((t * 10).toInt());
           for(int i=0; i<8; i++) {
               double px = hull2d[14].dx + (rand.nextDouble() - 0.5) * 30;
               double py = hull2d[14].dy + 20 + rand.nextDouble() * 40;
               double ps = 1.0 + rand.nextDouble() * 2;
               canvas.drawCircle(Offset(px, py), ps, Paint()..color=Colors.white.withOpacity(0.3 + rand.nextDouble()*0.4));
           }

           canvas.restore();
           continue;
        }

        // -----------------------
        // METEORITE PAINTING (HYPER-REAL)
        // -----------------------
        if (drop.type == EntityType.meteorite) {
           canvas.save();
           canvas.translate(drop.x, drop.y);
           canvas.rotate(drop.angle); 

           double r = drop.size;
           
           // 1. Base Shadow (Ambient Occlusion)
           canvas.drawCircle(Offset(r*0.2, r*0.2), r, Paint()..color=Colors.black.withOpacity(0.5)..maskFilter=MaskFilter.blur(BlurStyle.normal, r/2));

           // 2. Procedural Rock Shape (Voronoi-ish jaggedness)
           Path rock = Path();
           rock.moveTo(r, 0);
           for (int i=1; i<12; i++) {
              double angle = (2 * pi * i) / 12;
              double variance = 1.0 - (i%2==0 ? 0.0 : 0.2) + (Random().nextDouble()*0.1); 
              rock.lineTo(cos(angle)*r*variance, sin(angle)*r*variance);
           }
           rock.close();

           // 3. Material Shader (PBR Style)
           final shader = RadialGradient(
               center: const Alignment(-0.5, -0.5), // Sun Top-Left
               radius: 1.2,
               colors: [
                   const Color(0xFFD7CCC8), // Highlight (Regolith)
                   const Color(0xFF795548), // Midtone
                   const Color(0xFF3E2723), // Shadow
                   const Color(0xFF1B0000), // Core
               ],
               stops: const [0.0, 0.3, 0.7, 1.0]
           ).createShader(Rect.fromCircle(center: Offset.zero, radius: r));
           
           canvas.drawPath(rock, Paint()..shader=shader);

           // 4. Crater Details (Sub-geometry)
           // Draw a few overlapping circles with inverted gradients to look like craters
           for(int i=0; i<3; i++) {
               double cx = (Random().nextDouble() - 0.5) * r;
               double cy = (Random().nextDouble() - 0.5) * r;
               double cr = r * 0.3 * Random().nextDouble();
               canvas.drawCircle(Offset(cx, cy), cr, Paint()..color=Colors.black.withOpacity(0.3));
               canvas.drawArc(Rect.fromCircle(center: Offset(cx, cy), radius: cr), pi/4, pi, false, Paint()..style=PaintingStyle.stroke..color=Colors.white.withOpacity(0.1)..strokeWidth=1);
           }

           canvas.restore();
           continue; 
        }

        // -----------------------
        // PLANET PAINTING (Background Giants)
        // -----------------------
        if (drop.type == EntityType.planet) {
           canvas.save();
           canvas.translate(drop.x, drop.y);
           
           double r = drop.size;
           int planetType = drop.vx.toInt(); // 0:Gas, 1:Ice, 2:Molten
           
           // Planet Gradient
           List<Color> colors;
           if (planetType == 0) colors = [Colors.purple.shade900, Colors.deepPurple, Colors.orangeAccent]; // Gas Giant
           else if (planetType == 1) colors = [Colors.white, Colors.cyan.shade100, Colors.blue.shade900]; // Ice World
           else colors = [Colors.red.shade900, Colors.orange, Colors.yellow]; // Molten
           
           final planetPaint = Paint()..shader = LinearGradient(
               begin: Alignment.topLeft, end: Alignment.bottomRight,
               colors: colors
           ).createShader(Rect.fromCircle(center: Offset.zero, radius: r));
           
           canvas.drawCircle(Offset.zero, r, planetPaint);
           
           // Atmosphere Glow
           canvas.drawCircle(Offset.zero, r * 1.1, Paint()..color=colors[1].withOpacity(0.3)..maskFilter=const MaskFilter.blur(BlurStyle.normal, 20));
           
           // Shadow (Crescent)
           canvas.drawCircle(Offset(r*0.3, r*0.3), r, Paint()..color=Colors.black.withOpacity(0.7)..maskFilter=MaskFilter.blur(BlurStyle.normal, r/2));
           
           canvas.restore();
           continue;
        }

        // -----------------------
        // NEBULA PAINTING (Volumetric Clouds)
        // -----------------------
        if (drop.type == EntityType.nebula) {
           // Draw large fuzzy blob
           paint.maskFilter = const MaskFilter.blur(BlurStyle.normal, 60);
           canvas.drawCircle(Offset(drop.x, drop.y), drop.size, paint);
           paint.maskFilter = null; // Reset
           continue;
        }

        // -----------------------
        // DUST PAINTING (Warp Speed)
        // -----------------------
        if (drop.type == EntityType.dust) {
           // Stretch based on speed (blur effect)
           paint.color = Colors.white.withOpacity(drop.opacity);
           canvas.drawRect(Rect.fromLTWH(drop.x, drop.y, 1, drop.speed * 0.8), paint);
           continue;
        }

        // -----------------------
        // STAR PAINTING (Crisp 5-Point)
        // -----------------------
        if (drop.type == EntityType.star) {
           paint.color = Colors.white.withOpacity(drop.opacity);
           // Only draw full star shape for foreground stars (size > 2.5) to save perf
           if (drop.size > 2.5) {
               _drawStar(canvas, paint, drop.x, drop.y, drop.size * 0.8);
               // Glint center
               canvas.drawCircle(Offset(drop.x, drop.y), 1.0, Paint()..color=Colors.white);
           } else {
               canvas.drawCircle(Offset(drop.x, drop.y), drop.size * 0.5, paint);
           }
           continue;
        }

        // -----------------------
        // STANDARD RAIN
        if (drop.text.isEmpty) {
          if (type == RainType.whiteSnow) {
             canvas.drawCircle(Offset(drop.x, drop.y), drop.size, paint);
          } else if (type == RainType.fireEmbers) {
             canvas.drawRect(Rect.fromLTWH(drop.x, drop.y, drop.size, drop.size), paint);
          } else {
             paint.strokeWidth = 2;
             canvas.drawLine(Offset(drop.x, drop.y), Offset(drop.x, drop.y + 10), paint);
          }
        } else {
           // Text/Matrix Rendering...
           if (drop.streamChars.isNotEmpty) {
               for (int i = 0; i < drop.streamChars.length; i++) {
                   double charY = drop.y - (i * drop.size);
                   if (charY < -20) continue;
                   Color charColor = (i == 0) ? Colors.white : drop.color;
                   double fade = (i == 0) ? 1.0 : (1.0 - (i / drop.streamChars.length)).clamp(0.1, 1.0);
                   
                   textPainter.text = TextSpan(
                      text: drop.streamChars[i],
                      style: baseStyle.copyWith(
                        color: charColor.withOpacity(drop.opacity * fade),
                        fontSize: drop.size,
                        fontWeight: i==0 ? FontWeight.bold : FontWeight.normal,
                        shadows: i==0 ? [Shadow(color: drop.color, blurRadius: 8)] : null
                      ),
                   );
                   textPainter.layout();
                   textPainter.paint(canvas, Offset(drop.x, charY));
               }
           } else {
                 textPainter.text = TextSpan(
                   text: drop.text,
                   style: baseStyle.copyWith(
                     color: drop.color.withOpacity(drop.opacity),
                     fontSize: drop.size,
                     shadows: [Shadow(color: drop.color, blurRadius: 4)]
                   ),
                 );
                 textPainter.layout();
                 textPainter.paint(canvas, Offset(drop.x, drop.y));
           }
        }
      }
    } catch (e) {}
  }

  void _drawStar(Canvas canvas, Paint paint, double x, double y, double size) {
     final path = Path();
     double angle = -pi / 2;
     double step = pi / 5;
     
     // 5 Points
     for (int i = 0; i < 5; i++) {
        double px = x + cos(angle) * size;
        double py = y + sin(angle) * size;
        if (i == 0) {
           path.moveTo(px, py); // Move to first point to avoid line from (0,0)
        } else {
           path.lineTo(px, py);
        }
        angle += step;
        path.lineTo(x + cos(angle) * (size / 2.5), y + sin(angle) * (size / 2.5));
        angle += step; 
     }
     path.close();
     canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(CustomPainter oldDelegate) => true;
}
