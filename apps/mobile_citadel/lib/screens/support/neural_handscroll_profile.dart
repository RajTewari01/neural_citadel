import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'dart:ui' as ui;
import 'dart:math' as math;
import 'package:url_launcher/url_launcher.dart';
import '../../theme/app_theme.dart';

class NeuralHandscrollProfile extends StatefulWidget {
  const NeuralHandscrollProfile({super.key});

  @override
  State<NeuralHandscrollProfile> createState() => _NeuralHandscrollProfileState();
}

class _NeuralHandscrollProfileState extends State<NeuralHandscrollProfile> {
  final PageController _pageController = PageController();
  double _scrollPercent = 0.0;

  @override
  void initState() {
    super.initState();
    _pageController.addListener(() {
      setState(() {
        _scrollPercent = _pageController.page ?? 0.0;
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF050505), // Deep Ink Black
      body: Stack(
        children: [
          // 1. Global Background Effects
          const Positioned.fill(child: InkParticleField()),
          Positioned.fill(child: CustomPaint(painter: InkLandscapePainter())),
          
          // 2. Parallax Watermarks (Chinese Characters)
          _buildParallaxWatermark(0, "创造者", Alignment.topCenter), // Creator - Centered for impact
          
          // Vertical Couplets (Poetic aesthetic)
          const VerticalCouplet(text: "天地玄黄", alignLeft: true), // Heaven/Earth Dark/Yellow
          const VerticalCouplet(text: "宇宙洪荒", alignLeft: false), // Universe Flood/Wild

          _buildParallaxWatermark(1, "堡垒", Alignment.centerLeft),   // Fortress
          _buildParallaxWatermark(2, "核心", Alignment.bottomRight), // Core
          _buildParallaxWatermark(3, "链接", Alignment.center),      // Link

          // 3. Main Content Scroll
          PageView(
            controller: _pageController,
            scrollDirection: Axis.vertical,
            children: [
              _buildArchitectPage(),
              _buildCitadelPage(),
              _buildEnginePage(),
              _buildUplinkPage(),
            ],
          ),

          // 4. Floating Navigation / Back Button
          Positioned(
            top: 50,
            left: 20,
            child: IconButton(
              icon: const Icon(Icons.arrow_back_ios_new, color: Colors.white54),
              onPressed: () => Navigator.pop(context),
            ).animate().fadeIn(delay: 500.ms),
          ),
        ],
      ),
    );
  }

  Widget _buildParallaxWatermark(int index, String char, Alignment alignment) {
    // Parallax Logic: Move character based on scroll percent relative to its page index
    double parallaxOffset = (_scrollPercent - index) * 50; 
    
    return Positioned.fill(
      child: IgnorePointer(
        child: AnimatedOpacity(
          duration: 400.ms,
          opacity: (_scrollPercent - index).abs() < 1.0 ? 0.15 : 0.0, // Only visible when near page
          child: Container(
            alignment: alignment,
            padding: const EdgeInsets.all(30),
            transform: Matrix4.translationValues(0, parallaxOffset, 0),
            child: Text(
              char,
              style: GoogleFonts.maShanZheng( // Fallback to a standard if not avail, but let's try
                fontSize: 200,
                color: Colors.white,
                fontWeight: FontWeight.bold,
              ),
            ).animate(target: (_scrollPercent - index).abs() < 0.5 ? 1 : 0)
             .blur(begin: const Offset(10, 10), end: const Offset(0, 0), duration: 800.ms),
          ),
        ),
      ),
    );
  }

  Widget _buildScrollIndicator() {
    return Container(
      width: 4,
      decoration: BoxDecoration(
        color: Colors.white10,
        borderRadius: BorderRadius.circular(2),
      ),
      child: Stack(
        children: [
          Positioned(
            top: (_scrollPercent / 3) * (MediaQuery.of(context).size.height - 200), // Map 0-3 to height
            child: Container(
              width: 4,
              height: 40,
              decoration: BoxDecoration(
                color: AppTheme.neonCyan,
                borderRadius: BorderRadius.circular(2),
                boxShadow: [BoxShadow(color: AppTheme.neonCyan, blurRadius: 10)],
              ),
            ),
          ),
        ],
      ),
    );
  }

  // --- PAGES ---

  Widget _buildArchitectPage() {
    return Container(
      padding: const EdgeInsets.all(32),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          // Halo Avatar with Fallback
          Container(
            width: 180,
            height: 180,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              border: Border.all(color: Colors.white24, width: 1),
              boxShadow: [
                BoxShadow(color: AppTheme.neonCyan.withOpacity(0.2), blurRadius: 50, spreadRadius: 10),
              ],
            ),
            child: CircleAvatar(
              backgroundColor: Colors.black,
              backgroundImage: const AssetImage('assets/images/creator_raj.jpg'),
              onBackgroundImageError: (_, __) {}, // Handle error silently, fallback to child
              child: const Icon(Icons.person, size: 60, color: Colors.white24),
            ),
          ).animate().scale(duration: 800.ms, begin: const Offset(0, 0), end: const Offset(1, 1), curve: Curves.easeOutBack)
           .shimmer(duration: 2000.ms, color: AppTheme.neonCyan.withOpacity(0.3)),

          const SizedBox(height: 40),
          
          Text("Raj Tewari\n(Biswadeep)", 
            style: GoogleFonts.orbitron(fontSize: 32, fontWeight: FontWeight.bold, color: Colors.white, letterSpacing: 4),
          ).animate().fadeIn(delay: 300.ms).slideY(begin: 0.2, end: 0),
          
          Text("Lead Architect // Neural Citadel",
            style: GoogleFonts.shareTechMono(color: AppTheme.neonCyan, fontSize: 16),
          ).animate().fadeIn(delay: 500.ms),
          
          const SizedBox(height: 60),
          
          _buildQuoteCard(
            "Building the bridge between human intent and machine intelligence.\nNeural Citadel is not just an app, it's an extension of the mind.The offline ai-hub."
          ).animate().fadeIn(delay: 800.ms).slideY(begin: 0.1, end: 0),
        ],
      ),
    );
  }

  Widget _buildCitadelPage() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text("THE CITADEL", style: GoogleFonts.orbitron(fontSize: 40, color: Colors.white12)),
          const SizedBox(height: 20),
          Text("System Capabilities", style: GoogleFonts.shareTechMono(color: AppTheme.neonCyan, fontSize: 18)),
          const SizedBox(height: 30),
          
          _buildCapabilityCard("4K Generation", "Consumer-grade GPU optimization for ultra-high fidelity output.", Icons.blur_on),
          _buildCapabilityCard("Multi-Model Orchestration", "Intelligent switching between specialized AI agents.", Icons.hub),
          _buildCapabilityCard("Offline-First Core", "Full functionality without external cloud dependencies.", Icons.wifi_off),
          _buildCapabilityCard("Automated Publishing", "Multi-language newspaper generation engine.", Icons.newspaper),
          _buildCapabilityCard("Diffusion Qr Code", "Different style of QR code from diffusion style to gradient to SVG.", Icons.qr_code),
        ],
      ),
    );
  }

  Widget _buildEnginePage() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text("THE ENGINE", style: GoogleFonts.orbitron(fontSize: 40, color: Colors.white12)),
          const SizedBox(height: 30),
          
          _buildTechNode("Backend Architecture", "Python-first modular system with FastAPI integration.", 0),
          _buildTechNode("Memory Management", "Dynamic model unloading & quantized GGUF workflows.", 1),
          _buildTechNode("Interface Engineering", "Flutter (Mobile) + PyQt (Desktop) unified ecosystem.", 2),
          _buildTechNode("Security Protocols", "Fernet-based encryption & offensive security tooling.", 3),
          
          const SizedBox(height: 40),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              border: Border.all(color: AppTheme.neonCyan.withOpacity(0.3)),
              color: const Color(0xFF0A0A0A),
              borderRadius: BorderRadius.circular(16), // Rounded corners
            ),
            child: Text(
              "> SYSTEM_STATUS: OPTIMAL\n> NEURAL_APP: ONLINE",
              style: GoogleFonts.firaCode(color: AppTheme.neonCyan, fontSize: 12),
            ),
          ).animate().fadeIn(delay: 1000.ms),
        ],
      ),
    );
  }

  Widget _buildUplinkPage() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const SizedBox(height: 60), // Push down as requested
          Text("CREATOR NETWORK", style: GoogleFonts.orbitron(fontSize: 28, color: Colors.white, letterSpacing: 7)),
          Text("THE PLACE TO CONNECT WITH THE CREATOR", style: GoogleFonts.shareTechMono(fontSize: 12, color: AppTheme.neonCyan)),
          const SizedBox(height: 50),
          
          // Cards - Static Column to prevent Scroll conflict
          Column(
            children: [
              _buildSocialCard(
                title: "GITHUB REPO",
                subtitle: "SOURCE CODE :: ACCESS GRANTED",
                icon: Icons.code,
                color: Colors.greenAccent,
                url: "https://github.com/RajTewari01",
                background: CustomPaint(painter: _GitGraphPainter()),
              ),
              const SizedBox(height: 24),
              _buildSocialCard(
                title: "INSTAGRAM",
                subtitle: "VISUAL FEED :: LIVE",
                icon: Icons.camera_alt,
                color: const Color(0xFFE1306C),
                url: "https://instagram.com/light_up_my_world01",
                background: _buildInstaGradient(),
              ),
              const SizedBox(height: 24),
              _buildSocialCard(
                title: "Facebook",
                subtitle: "SOCIAL FEED :: LIVE",
                icon: Icons.facebook,
                color: const Color(0xFFE1306C),
                url: "https://m.facebook.com/raj.tewari.585",
                background: _buildInstaGradient(),
              ),
              const SizedBox(height: 24),
              _buildSocialCard(
                title: "SECTOR TARGET",
                subtitle: "WEST BENGAL, INDIA",
                icon: Icons.map,
                color: const Color(0xFF00E5FF), // Neon Blue
                onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const _SciFiMapScreen())),
                background: CustomPaint(painter: _AsphaltMapPainter()),
              ),
            ],
          ),
          
          const Spacer(),
          
          // Scroll Up Indicator / Hint
          Icon(Icons.keyboard_arrow_up, color: Colors.white24, size: 24)
              .animate(onPlay: (c) => c.repeat(reverse: true)).moveY(begin: 0, end: -5),
          const SizedBox(height: 8),
          Text("NEURAL CITADEL v1.0", style: GoogleFonts.shareTechMono(color: Colors.white24)),
          const SizedBox(height: 30),
        ],
      ),
    );
  }

  // --- SOCIAL CARDS ---

  Widget _buildSocialCard({
    required String title, 
    required String subtitle, 
    required IconData icon, 
    required Color color, 
    String? url,
    VoidCallback? onTap,
    required Widget background,
  }) {
    return InkWell(
      onTap: onTap ?? (url != null ? () => launchUrl(Uri.parse(url)) : null),
      child: Container(
        height: 100,
        decoration: BoxDecoration(
          color: const Color(0xFF050505),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: color.withOpacity(0.5), width: 1),
          boxShadow: [
            BoxShadow(color: color.withOpacity(0.1), blurRadius: 15, offset: const Offset(0, 4)),
          ],
        ),
        clipBehavior: Clip.antiAlias,
        child: Stack(
          children: [ //... existing stack content
            // Background Animation/Graphic
            Positioned.fill(child: Opacity(opacity: 0.3, child: background)),
            
            // Content
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
              child: Row(
                children: [
                   Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: color.withOpacity(0.2),
                      shape: BoxShape.circle,
                      border: Border.all(color: color.withOpacity(0.5)),
                    ),
                    child: Icon(icon, color: color, size: 24),
                  ),
                  const SizedBox(width: 20),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(title, style: GoogleFonts.orbitron(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
                        const SizedBox(height: 4),
                        Text(subtitle, style: GoogleFonts.shareTechMono(color: Colors.white70, fontSize: 10)),
                      ],
                    ),
                  ),
                  Icon(Icons.arrow_forward_ios, color: color.withOpacity(0.5), size: 16),
                ],
              ),
            ),
            
            // Racing Stripe (Asphalt Style)
            Positioned(
              top: 0, bottom: 0, left: 0,
              child: Container(width: 4, color: color),
            ),
          ],
        ),
      ),
    ).animate().fadeIn().slideX(begin: 0.1, end: 0, duration: 500.ms);
  }

  Widget _buildInstaGradient() {
    return Container(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          colors: [Color(0xFF833AB4), Color(0xFFFD1D1D), Color(0xFFF77737)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
      ),
    );
  }

  // --- COMPONENTS ---

  Widget _buildQuoteCard(String text) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [Colors.white.withOpacity(0.05), Colors.transparent],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: Colors.white10),
      ),
      child: Text(
        text,
        style: GoogleFonts.outfit(color: Colors.white70, fontSize: 16, height: 1.6, fontStyle: FontStyle.italic),
        textAlign: TextAlign.center,
      ),
    );
  }

  // REMOVED _buildGithubNode, _buildInstagramNode, _buildLocationNode specific widgets
  // KEEP _buildCapabilityCard and _buildTechNode as they are called by other pages
  // REMOVE NetworkConnectorPainter usage


  Widget _buildCapabilityCard(String title, String desc, IconData icon) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFF101010), // Darker solid for contrast
        borderRadius: BorderRadius.circular(24), // Extremely rounded "Modern" look
        border: Border.all(color: Colors.white10),
        boxShadow: [
          BoxShadow(color: Colors.black.withOpacity(0.5), blurRadius: 10, offset: const Offset(0, 5)),
        ],
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: AppTheme.neonCyan.withOpacity(0.1),
              shape: BoxShape.circle,
            ),
            child: Icon(icon, color: AppTheme.neonCyan, size: 24),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: GoogleFonts.orbitron(color: Colors.white, fontSize: 15, fontWeight: FontWeight.bold)),
                const SizedBox(height: 4),
                Text(desc, style: GoogleFonts.outfit(color: Colors.white54, fontSize: 13)),
              ],
            ),
          ),
        ],
      ),
    ).animate().slideX(begin: 0.2, end: 0, duration: 600.ms).fadeIn();
  }

  Widget _buildTechNode(String label, String value, int index) {
    return Container(
      margin: const EdgeInsets.only(bottom: 24),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Node Dot
          Container(
            margin: const EdgeInsets.only(top: 4, right: 16),
            width: 12, height: 12,
            decoration: BoxDecoration(
              color: AppTheme.neonCyan,
              shape: BoxShape.circle,
              boxShadow: [BoxShadow(color: AppTheme.neonCyan, blurRadius: 8)],
            ),
          ).animate(onPlay: (c) => c.repeat(reverse: true)).scale(begin: const Offset(0.8, 0.8), end: const Offset(1.2, 1.2)),
          
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: GoogleFonts.shareTechMono(color: AppTheme.neonCyan, fontSize: 16)),
                const SizedBox(height: 4),
                Text(value, style: GoogleFonts.outfit(color: Colors.white70, fontSize: 14)),
              ],
            ),
          ),
        ],
      ),
    ).animate().fadeIn(delay: (200 * index).ms).slideX(begin: 0.1, end: 0);
  }
}

// NetworkConnectorPainter removed.

// --- PARTICLES ---

// --- SCROLL PAINTERS ---

class InkLandscapePainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.white.withOpacity(0.05)
      ..style = PaintingStyle.fill;

    final path = Path();
    path.moveTo(0, size.height);
    
    // Procedural Mountains
    path.lineTo(0, size.height * 0.7);
    path.quadraticBezierTo(size.width * 0.2, size.height * 0.5, size.width * 0.4, size.height * 0.8);
    path.quadraticBezierTo(size.width * 0.6, size.height * 0.9, size.width * 0.8, size.height * 0.6);
    path.quadraticBezierTo(size.width * 0.9, size.height * 0.5, size.width, size.height * 0.8);
    path.lineTo(size.width, size.height);
    path.close();

    canvas.drawPath(path, paint);

    // Mist
    final mistPaint = Paint()
      ..shader = ui.Gradient.linear(
        Offset(0, size.height * 0.8),
        Offset(0, size.height),
        [Colors.transparent, const Color(0xFF050505)],
      );
    canvas.drawRect(Rect.fromLTWH(0, size.height * 0.6, size.width, size.height * 0.4), mistPaint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class VerticalCouplet extends StatelessWidget {
  final String text;
  final bool alignLeft;

  const VerticalCouplet({super.key, required this.text, this.alignLeft = true});

  @override
  Widget build(BuildContext context) {
    return Positioned(
      top: 100,
      bottom: 100,
      left: alignLeft ? 20 : null,
      right: alignLeft ? null : 20,
      child: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: text.split('').map((char) => Padding(
            padding: const EdgeInsets.symmetric(vertical: 4),
            child: Text(
              char,
              style: GoogleFonts.maShanZheng(
                color: Colors.white12,
                fontSize: 24,
                shadows: [BoxShadow(color: AppTheme.neonCyan.withOpacity(0.2), blurRadius: 10)],
              ),
            ),
          )).toList(),
        ),
      ),
    );
  }
}

// --- PARTICLES (Keep Existing) ---
class InkParticleField extends StatefulWidget {
  const InkParticleField({super.key});

  @override
  State<InkParticleField> createState() => _InkParticleFieldState();
}

class _InkParticleFieldState extends State<InkParticleField> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  final List<_InkParticle> _particles = [];
  final math.Random _random = math.Random();

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(vsync: this, duration: const Duration(seconds: 10))..repeat();
    for (int i = 0; i < 30; i++) {
      _particles.add(_InkParticle(_random));
    }
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
        return CustomPaint(
          painter: _InkPainter(_particles, _controller.value),
        );
      },
    );
  }
}

class _InkParticle {
  double x;
  double y;
  double size;
  double speed;
  double opacity;

  _InkParticle(math.Random r)
      : x = r.nextDouble(),
        y = r.nextDouble(),
        size = r.nextDouble() * 3 + 1,
        speed = r.nextDouble() * 0.002 + 0.001,
        opacity = r.nextDouble() * 0.3 + 0.1;
  
  void update() {
    y -= speed;
    if (y < 0) y = 1.0;
  }
}

class _InkPainter extends CustomPainter {
  final List<_InkParticle> particles;
  final double animationValue;

  _InkPainter(this.particles, this.animationValue);

  @override
  void paint(Canvas canvas, Size size) {
    var paint = Paint()..color = Colors.white;
    for (var p in particles) {
      p.update(); // Side effect in paint method is generally bad practice but acceptable for simple particle animation here
      paint.color = Colors.white.withOpacity(p.opacity);
      canvas.drawCircle(Offset(p.x * size.width, p.y * size.height), p.size, paint);
    }
  }

  @override
  bool shouldRepaint(covariant _InkPainter oldDelegate) => true;
}

class _GitGraphPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.greenAccent.withOpacity(0.2)
      ..strokeWidth = 2.0
      ..style = PaintingStyle.stroke;

    final path = Path();
    var random = math.Random(42); // Consistent seed
    
    path.moveTo(0, size.height * 0.5);
    for (double i = 0; i < size.width; i += 20) {
      double deviation = (random.nextDouble() - 0.5) * 30;
      path.lineTo(i, size.height * 0.5 + deviation);
    }
    canvas.drawPath(path, paint);

    // Commit Dots
    final dotPaint = Paint()..color = Colors.greenAccent.withOpacity(0.5);
    for (double i = 20; i < size.width; i += 60) {
      canvas.drawCircle(Offset(i, size.height * 0.5 + (random.nextDouble() - 0.5) * 30), 3, dotPaint);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _AsphaltMapPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    // 1. Grid Background (Holographic Floor)
    final gridPaint = Paint()
      ..color = AppTheme.neonCyan.withOpacity(0.1)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 0.5;

    double gridSize = 25;
    for (double i = 0; i < size.width; i += gridSize) {
      canvas.drawLine(Offset(i, 0), Offset(i, size.height), gridPaint);
    }
    for (double i = 0; i < size.height; i += gridSize) {
      canvas.drawLine(Offset(0, i), Offset(size.width, i), gridPaint);
    }

    // 2. The "Route" / Track (Neon Blue Line)
    final trackPaint = Paint()
      ..color = const Color(0xFF00E5FF)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3.0
      ..strokeCap = StrokeCap.round
      ..maskFilter = const MaskFilter.blur(BlurStyle.solid, 2);

    final path = Path();
    // Use relative coordinates for scalability
    path.moveTo(size.width * 0.1, size.height * 0.8);
    path.lineTo(size.width * 0.3, size.height * 0.4); 
    path.lineTo(size.width * 0.5, size.height * 0.6); 
    path.lineTo(size.width * 0.7, size.height * 0.3); 
    path.lineTo(size.width * 0.9, size.height * 0.5);

    canvas.drawPath(path, trackPaint);
    
    // Glow effect for track
    final glowPaint = Paint()
      ..color = const Color(0xFF00E5FF).withOpacity(0.3)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 8.0
      ..strokeCap = StrokeCap.round
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 10);
      
    canvas.drawPath(path, glowPaint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

// --- SCIFI MAP SCREEN ---

class _SciFiMapScreen extends StatefulWidget {
  const _SciFiMapScreen();

  @override
  State<_SciFiMapScreen> createState() => _SciFiMapScreenState();
}

class _SciFiMapScreenState extends State<_SciFiMapScreen> with TickerProviderStateMixin {
  late AnimationController _scanController;
  
  @override
  void initState() {
    super.initState();
    _scanController = AnimationController(vsync: this, duration: const Duration(seconds: 4))..repeat();
  }

  @override
  void dispose() {
    _scanController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          // 1. Grid Background
          Positioned.fill(
            child: CustomPaint(
              painter: _HoloGridPainter(),
            ),
          ),

          // 2. The Map
          Center(
            child: SizedBox(
              width: 300,
              height: 500,
              child: AnimatedBuilder(
                animation: _scanController,
                builder: (context, child) {
                  return CustomPaint(
                    painter: _WestBengalSciFiPainter(_scanController.value),
                  );
                },
              ),
            ),
          ),

          // 3. UI Overlays (HUD)
          Positioned(
            top: 60, left: 24,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text("SECTOR SCAN", style: GoogleFonts.orbitron(color: AppTheme.neonCyan, fontSize: 24, fontWeight: FontWeight.bold)),
                Text("TARGET: WEST BENGAL", style: GoogleFonts.shareTechMono(color: Colors.white, fontSize: 14)),
                const SizedBox(height: 8),
                Container(width: 100, height: 2, color: AppTheme.neonCyan),
              ],
            ),
          ),

          Positioned(
            bottom: 40, right: 24,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text("COORDINATES LOCKED", style: GoogleFonts.shareTechMono(color: Colors.redAccent, fontSize: 12)),
                Text("22.9868° N, 87.8550° E", style: GoogleFonts.orbitron(color: Colors.white, fontSize: 16)),
              ],
            ),
          ),
          
          // Back Button
          Positioned(
            top: 50, right: 20,
            child: IconButton(
              icon: Icon(Icons.close, color: Colors.white),
              onPressed: () => Navigator.pop(context),
            ),
          ),
        ],
      ),
    );
  }
}

class _HoloGridPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = const Color(0xFF001133)
      ..strokeWidth = 1
      ..style = PaintingStyle.stroke;

    double step = 40;
    for (double i = 0; i < size.width; i += step) {
      canvas.drawLine(Offset(i, 0), Offset(i, size.height), paint);
    }
    for (double i = 0; i < size.height; i += step) {
      canvas.drawLine(Offset(0, i), Offset(size.width, i), paint);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _WestBengalSciFiPainter extends CustomPainter {
  final double scanValue;
  _WestBengalSciFiPainter(this.scanValue);

  @override
  void paint(Canvas canvas, Size size) {
    double w = size.width;
    double h = size.height;

    // --- 1. Map Base (Geographically Projected) ---
    final mapPath = Path();

    // 1. NORTH (Darjeeling / Himalayas)
    mapPath.moveTo(w * 0.55, h * 0.05); // Darjeeling Top
    mapPath.lineTo(w * 0.60, h * 0.08); 
    
    // 2. DOOARS (Jalpaiguri / Alipurduar / Cooch Behar)
    mapPath.lineTo(w * 0.75, h * 0.10); 
    mapPath.lineTo(w * 0.92, h * 0.14); // Cooch Behar Tip (Rightmost)
    mapPath.lineTo(w * 0.85, h * 0.18); 
    
    // 3. CHICKEN'S NECK (Islampur / North Dinajpur)
    mapPath.lineTo(w * 0.65, h * 0.18); 
    mapPath.lineTo(w * 0.60, h * 0.19); // The Neck (Narrowest)
    
    // 4. MALDA / SOUTH DINAJPUR (Widening)
    mapPath.lineTo(w * 0.62, h * 0.25); // Balurghat
    mapPath.lineTo(w * 0.60, h * 0.35); // Malda East
    
    // 5. MURSHIDABAD / NADIA (Eastern Border with Bangladesh)
    // Convex curve out
    mapPath.lineTo(w * 0.68, h * 0.45); // Murshidabad
    mapPath.lineTo(w * 0.75, h * 0.55); // Nadia North
    mapPath.lineTo(w * 0.78, h * 0.65); // Krishnanagar Area
    mapPath.lineTo(w * 0.80, h * 0.75); // North 24 Pgs border
    
    // 6. SUNDARBANS (Southern Delta)
    mapPath.lineTo(w * 0.82, h * 0.85); // Hasnabad
    mapPath.lineTo(w * 0.67, h * 0.96); // Deep Sundarbans/Bay
    mapPath.lineTo(w * 0.55, h * 0.92); // Sagar Island Inlet
    
    // 7. COASTAL WEST (East Midnapore)
    mapPath.lineTo(w * 0.42, h * 0.98); // Digha/Haldia Coast
    mapPath.lineTo(w * 0.38, h * 0.85); // Kharagpur Side
    
    // 8. WESTERN PLATEAU (Midnapore -> Purulia)
    mapPath.lineTo(w * 0.25, h * 0.78); // Jhargram
    mapPath.lineTo(w * 0.15, h * 0.72); // South Purulia
    mapPath.lineTo(w * 0.02, h * 0.69); // Purulia Tip (Extreme West)
    
    // 9. DAMODAR VALLEY (Asansol -> Birbhum)
    mapPath.lineTo(w * 0.15, h * 0.62); // Purulia Top
    mapPath.lineTo(w * 0.27, h * 0.60); // Asansol/Burnpur
    mapPath.lineTo(w * 0.35, h * 0.52); // Bolpur/Birbhum
    mapPath.lineTo(w * 0.40, h * 0.45); // Rampurhat
    
    // 10. BIHAR/JHARKHAND BORDER (Up to Neck)
    mapPath.lineTo(w * 0.48, h * 0.35); // Farakka West
    mapPath.lineTo(w * 0.52, h * 0.25); // Malda West
    mapPath.lineTo(w * 0.48, h * 0.20); // Islampur West
    mapPath.lineTo(w * 0.50, h * 0.10); // Darjeeling West
    
    mapPath.close();

    final mapPaint = Paint()
      ..color = const Color(0xFF001220).withOpacity(0.9)
      ..style = PaintingStyle.fill;
    
    final borderPaint = Paint()
      ..color = AppTheme.neonCyan.withOpacity(0.8)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.6
      ..strokeJoin = StrokeJoin.round
      ..maskFilter = const MaskFilter.blur(BlurStyle.solid, 2);

    canvas.drawPath(mapPath, mapPaint);
    canvas.drawPath(mapPath, borderPaint);

    // --- 2. Key Locations (Projected Coordinates) ---
    // Calculated based on Lat/Lon alignment
    final siliguri = Offset(w * 0.65, h * 0.10);
    final kolkata = Offset(w * 0.64, h * 0.81);
    final nadia = Offset(w * 0.72, h * 0.67); // Krishnanagar
    final burdwan = Offset(w * 0.54, h * 0.70); // Adjusted relative to Kol
    final durgapur = Offset(w * 0.40, h * 0.65);
    final haldia = Offset(w * 0.57, h * 0.90);
    final purulia = Offset(w * 0.14, h * 0.68);

    // --- 3. Neural Connections ---
    final roadPaint = Paint()
      ..color = const Color(0xFF00E5FF).withOpacity(0.5)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.0;

    final roadPath = Path();
    
    // NH-12 (Spine)
    roadPath.moveTo(siliguri.dx, siliguri.dy);
    roadPath.quadraticBezierTo(w * 0.60, h * 0.35, nadia.dx, nadia.dy); // Via Malda
    roadPath.lineTo(kolkata.dx, kolkata.dy); // Nadia -> Kol
    
    // NH-19 (West Link)
    roadPath.moveTo(kolkata.dx, kolkata.dy);
    roadPath.lineTo(burdwan.dx, burdwan.dy);
    roadPath.lineTo(durgapur.dx, durgapur.dy);
    roadPath.lineTo(purulia.dx, purulia.dy); // Extension

    // Port Link
    roadPath.moveTo(kolkata.dx, kolkata.dy);
    roadPath.lineTo(haldia.dx, haldia.dy);

    canvas.drawPath(roadPath, roadPaint);
    
    // --- 4. Nodes & Labels ---
    _drawCityNode(canvas, kolkata, "KOLKATA", true, w);
    _drawCityNode(canvas, nadia, "NADIA", true, w);
    _drawCityNode(canvas, burdwan, "BURDWAN", true, w);
    _drawCityNode(canvas, durgapur, "DURGAPUR", true, w);
    _drawCityNode(canvas, siliguri, "SILIGURI", false, w);
    _drawCityNode(canvas, haldia, "HALDIA", false, w);
    _drawCityNode(canvas, purulia, "PURULIA", false, w);

    // --- 5. Scan Line ---
    double scanY = h * scanValue;
    final scanPaint = Paint()
      ..shader = ui.Gradient.linear(
        Offset(0, scanY), 
        Offset(0, scanY + 30),
        [
          AppTheme.neonCyan.withOpacity(0),
          AppTheme.neonCyan.withOpacity(0.6),
          AppTheme.neonCyan.withOpacity(0)
        ],
        [0.0, 0.5, 1.0]
      );
    
    canvas.drawRect(Rect.fromLTWH(0, scanY, w, 30), scanPaint);
  }

  void _drawCityNode(Canvas canvas, Offset pos, String label, bool isMajor, double w) {
    // Pulse Effect
    final paint = Paint()..color = isMajor ? AppTheme.neonCyan : Colors.white70;
    final glow = Paint()..color = AppTheme.neonCyan.withOpacity(0.3);

    canvas.drawCircle(pos, 5, glow);
    canvas.drawCircle(pos, 2, paint);

    // Label Offset
    double dx = 8; 
    double dy = -5;
    
    // Avoid overlap
    if (pos.dx > w * 0.6) dx = -55; // Right side labels go Left
    if (label == "DURGAPUR") dy = -12;
    if (label == "BURDWAN") dy = 10;

    final textSpan = TextSpan(
      text: label,
      style: GoogleFonts.shareTechMono(
        color: Colors.white,
        fontSize: 9, 
        letterSpacing: 0.8
      ),
    );
    final textPainter = TextPainter(
      text: textSpan,
      textDirection: TextDirection.ltr,
    );
    textPainter.layout();
    textPainter.paint(canvas, Offset(pos.dx + dx, pos.dy + dy));
  }

  @override
  bool shouldRepaint(covariant _WestBengalSciFiPainter oldDelegate) => oldDelegate.scanValue != scanValue;
}
