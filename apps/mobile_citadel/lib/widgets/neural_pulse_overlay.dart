import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_overlay_window/flutter_overlay_window.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:google_fonts/google_fonts.dart';
import 'dart:math' as math;
import 'dart:ui' as ui; // For ImageFilter

// Premium Siri-Style Colors
const Color _cyan = Color(0xFF5AC8FA);
const Color _blue = Color(0xFF007AFF);
const Color _purple = Color(0xFFAF52DE);

/// The overlay widget displayed when the app is in background.
/// Designed to wrap around the punch-hole camera (centered top).
class NeuralPulseOverlay extends StatefulWidget {
  const NeuralPulseOverlay({super.key});

  @override
  State<NeuralPulseOverlay> createState() => _NeuralPulseOverlayState();
}

class _NeuralPulseOverlayState extends State<NeuralPulseOverlay>
    with SingleTickerProviderStateMixin {
  String _status = "Neural";
  bool _isListening = false;
  String _mode = "idle"; // idle, call, media, listening
  String _phoneNumber = "Unknown";
  bool _isCallActive = false;
  bool _isIncomingCall = false;
  bool _isSpeakerOn = false;
  late AnimationController _pulseController;
  
  // Interaction State
  bool _isExpanded = false;
  double _topOffset = 0.0;
  double _leftOffset = 0.0;

  @override
  void initState() {
    super.initState();
    
    _pulseController = AnimationController(
      duration: const Duration(seconds: 2),
      vsync: this,
    );
    _pulseController.repeat();
    
    // Listen for messages from main app
    FlutterOverlayWindow.overlayListener.listen((data) {
      if (data is Map) {
        // IGNORE incoming action broadcasts (sent by ourselves)
        if (data.containsKey('action')) return;
        
        setState(() {
          _status = data['status']?.toString() ?? "Neural";
          _isListening = data['listening'] == true;
          if (data.containsKey('mode')) _mode = data['mode'];
          if (data.containsKey('number')) _phoneNumber = data['number'];
          if (data.containsKey('isCallActive')) _isCallActive = data['isCallActive'] == true;
          if (data.containsKey('isIncomingCall')) _isIncomingCall = data['isIncomingCall'] == true;
          
          if (_mode == "calibration") _isExpanded = true;
          if (_mode == "idle") _isExpanded = false;
          // Only expand forcefully if explicitly told to
          if (data['forceExpand'] == true) _isExpanded = true; 
          
          if (data.containsKey('topOffset')) _topOffset = (data['topOffset'] as num?)?.toDouble() ?? 0.0;
          if (data.containsKey('leftOffset')) _leftOffset = (data['leftOffset'] as num?)?.toDouble() ?? 0.0;
        });
      }
    });
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  Future<void> _toggleExpanded(bool expand) async {
    // 1. RESIZE OVERLAY WINDOW
    try {
      if (expand) {
         await FlutterOverlayWindow.resizeOverlay(WindowSize.matchParent, 600, false);
      } else {
         await FlutterOverlayWindow.resizeOverlay(WindowSize.matchParent, 100, false); 
      }
    } catch (e) {
      debugPrint("Resize Failed: $e");
    }

    // 2. UPDATE UI STATE
    setState(() => _isExpanded = expand);
    
    if (expand) FlutterOverlayWindow.shareData({'action': 'tap'});
  }

  @override
  Widget build(BuildContext context) {
    // Dynamic width based on content/state
    double width = 120;
    if (_isExpanded) {
        width = 340;
    } else if (_mode == "call") {
        width = 120.0; // Comfortably fit phone icon and dynamic waveform
    } else if (_isListening) {
        width = 180;
    }
    double height = _isExpanded ? 180 : 36; 

    // CRITICAL: TopCenter Alignment to fix "Huge" offset issue
    return Align(
      alignment: Alignment.topCenter,
      child: Material(
        type: MaterialType.transparency, // ROBUST TOUCH HANDLING: Fixes "Hard to click"
        child: Transform.translate(
          offset: Offset(_leftOffset, _topOffset),
          child: GestureDetector(
            behavior: HitTestBehavior.opaque, // FORCE CATCH ALL: Fixes "Ghost" touches
            onTap: () => _toggleExpanded(!_isExpanded),
            onDoubleTap: () => FlutterOverlayWindow.shareData({'action': 'double_tap'}), 
            child: Container(
              // INVISIBLE HITBOX (Tight wrap to prevent blocking OS touches)
              height: _isExpanded ? 180 : 80, // DYNAMIC HEIGHT
              width: _isExpanded ? 360 : 150, // DYNAMIC WIDTH
              color: Colors.white.withOpacity(0.02), // Debugging hit box (set to 0 for production)
              alignment: Alignment.topCenter, 
              padding: const EdgeInsets.symmetric(horizontal: 0, vertical: 5),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 350),
                curve: Curves.easeOutBack,
                width: width,
                height: _isExpanded ? 140 : 40,
                decoration: BoxDecoration(
                  // GLASSMORPHISM: Frosted Black
                  color: Colors.black.withOpacity(0.7), 
                  borderRadius: BorderRadius.circular(height / 2),
                  backgroundBlendMode: BlendMode.srcOver,
                  boxShadow: [
                     // GLOW with Cyan/Green Hue
                     BoxShadow(
                       color: (_isListening ? _cyan : Colors.blueAccent).withOpacity(0.4), 
                       blurRadius: 20, 
                       spreadRadius: 2
                     ),
                  ],
                ),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(height / 2),
                  child: Stack(
                    alignment: Alignment.center,
                    children: [
                      // LAYER 0: INFINITY WAVE BACKGROUND (Persistent)
                      // A slow breathing wave that runs ALWAYS
                      if (_mode != "call")
                        Positioned.fill(
                        child: Opacity(
                          opacity: _isListening ? 0.8 : 0.3, // Brighter when listening
                          child: CustomPaint(
                            painter: SiriWaveformPainter(
                              animation: _pulseController,
                              barCount: 5, // More complex wave
                              color: _isListening ? _cyan : Colors.purpleAccent,
                            ),
                          ),
                        ),
                      ),
                      
                      // LAYER 1: GLASS BLUR
                      // Adds the premium frosted effect over the wave
                      BackdropFilter(
                         filter: ui.ImageFilter.blur(sigmaX: 10.0, sigmaY: 10.0),
                         child: Container(color: Colors.transparent),
                      ),

                      // LAYER 2: CONTENT
                      AnimatedSwitcher(
                        duration: const Duration(milliseconds: 300),
                        child: _isExpanded 
                          ? _buildExpandedContent() 
                          : _buildCollapsedContent(),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildCollapsedContent() {
    return Stack(
      alignment: Alignment.center,
      children: [
        // 1. Microphone/Phone Icon (Left Aligned)
        Align(
          alignment: const Alignment(-0.85, 0.0), // Precise left positioning
          child: Icon(
            _mode == "call" ? Icons.phone_in_talk : (_isListening ? Icons.mic : Icons.circle), 
            color: _mode == "call" ? Colors.greenAccent : (_isListening ? _cyan : Colors.white30),
            size: 14, // Slightly smaller for premium look
          ),
        ),

        // 2. Status / Waveform
        if (_mode == "call")
          Positioned(
            right: 12, // Pin precisely to the right side with slight padding
            child: _buildDynamicWaveform(color: Colors.greenAccent),
          )
        else 
          Align(
            alignment: Alignment.center,
            child: _isListening 
                ? _buildDynamicWaveform()  
                : FittedBox(
                    fit: BoxFit.scaleDown,
                    child: _safeText(
                      _status == "Positioning..." ? "Adjusting..." : (_status == "Neural" ? "" : _status),
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
          ),
      ],
    );
  }

  // Make waveform constantly alive
  Widget _buildDynamicWaveform({Color? color}) {
    return SizedBox(
      height: 24, // Compact height for collapsed mode
      width: 45, // Comfortably fits inside the 120 width island
      child: ShaderMask(
        blendMode: BlendMode.dstIn,
        shaderCallback: (bounds) {
          // Gracefully fade out the harsh left/right edges of the waveform
          return const LinearGradient(
            colors: [Colors.transparent, Colors.white, Colors.white, Colors.transparent],
            stops: [0.0, 0.25, 0.75, 1.0],
            begin: Alignment.centerLeft,
            end: Alignment.centerRight,
          ).createShader(bounds);
        },
        child: CustomPaint(
          painter: SiriWaveformPainter(
            animation: _pulseController, 
            barCount: 3,
            color: color ?? (_isListening ? _cyan : Colors.purpleAccent),
          ),
        ),
      ),
    );
  }

  Widget _buildExpandedContent() {
    // NUCLEAR: Dynamic Content based on MODE (Call, Media, or Voice)
    if (_mode == 'call') return _buildCallUI();
    if (_mode == 'media') return _buildMediaUI();

    return Container(
      padding: const EdgeInsets.all(16),
      child: SingleChildScrollView( // CRITICAL FIX: SCROLL SAFETY
        physics: const BouncingScrollPhysics(),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
          // Header: Waveform + Status
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
               SizedBox(
                 height: 40, width: 60,
                 child: CustomPaint(painter: SiriWaveformPainter(animation: _pulseController, barCount: 3))
               ),
               const SizedBox(width: 10),
                Flexible(
                 child: _safeText(
                   _status.contains("Error") ? "Listening..." : _status, 
                   fontSize: 14, 
                   fontWeight: FontWeight.w600,
                 ),
               ),
            ],
          ),
          
          const SizedBox(height: 20),
          
          // Quick Actions Grid
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildModernAction(Icons.camera_alt, "Camera", () => FlutterOverlayWindow.shareData({'action': 'camera'})),
              _buildModernAction(Icons.mic_off, "Mute", () => FlutterOverlayWindow.shareData({'action': 'mute'})),
              _buildModernAction(Icons.close, "Close", () => _toggleExpanded(false)),
            ],
          ),
          
          const SizedBox(height: 10),
          Text(
            "Listening for 'Hey Neural'...",
            style: TextStyle(color: Colors.white38, fontSize: 10, letterSpacing: 1),
          )
        ],
      ),
      ),
    );
  }

  // --- NUCLEAR UI MODES ---

  Widget _buildShimmerText(String text, double fontSize, {TextOverflow? overflow}) {
    return AnimatedBuilder(
      animation: _pulseController,
      builder: (context, child) {
        return ShaderMask(
          blendMode: BlendMode.srcIn,
          shaderCallback: (bounds) {
            return LinearGradient(
              colors: const [Colors.white70, Colors.cyanAccent, Colors.white70],
              stops: [
                _pulseController.value - 0.2,
                _pulseController.value,
                _pulseController.value + 0.2
              ],
              begin: const Alignment(-1.0, 0),
              end: const Alignment(1.0, 0),
              tileMode: TileMode.clamp,
            ).createShader(bounds);
          },
          child: Text(
            text,
            textAlign: TextAlign.center,
            overflow: overflow,
            style: TextStyle(fontSize: fontSize, fontWeight: FontWeight.bold, color: Colors.white, letterSpacing: 0.5),
          ),
        );
      },
    );
  }

  Widget _buildCallUI() {
    // Premium Glassmorphism Button Builder
    Widget buildPremiumButton(IconData icon, Color baseColor, VoidCallback onTap, {bool isActive = false, bool isDanger = false}) {
       Color finalColor = isActive ? Colors.white : baseColor;
       Color iconColor = isActive ? Colors.black : (isDanger ? Colors.white : baseColor);
       return GestureDetector(
         behavior: HitTestBehavior.opaque,
         onTap: onTap,
         child: Container(
           width: 55,
           height: 55,
           decoration: BoxDecoration(
             shape: BoxShape.circle,
             color: isActive ? Colors.white : (isDanger ? Colors.redAccent : baseColor.withOpacity(0.1)),
             border: Border.all(color: isActive ? Colors.white : (isDanger ? Colors.redAccent.withOpacity(0.8) : baseColor.withOpacity(0.4)), width: 1.5),
             boxShadow: [
               BoxShadow(color: finalColor.withOpacity(isDanger ? 0.4 : 0.2), blurRadius: 15, spreadRadius: 2)
             ]
           ),
           child: Icon(icon, color: iconColor, size: 28),
         )
       );
    }

    return SingleChildScrollView(
      physics: const NeverScrollableScrollPhysics(),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 20),
        width: double.infinity,
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: [
             // DECLINE / END
             buildPremiumButton(Icons.call_end, Colors.redAccent, () async {
                 try {
                     final prefs = await SharedPreferences.getInstance();
                     await prefs.setInt('actionEvent_end_call', DateTime.now().millisecondsSinceEpoch);
                 } catch (e) {}
             }, isDanger: true),

              Expanded(
               child: Column(
                 mainAxisSize: MainAxisSize.min,
                 crossAxisAlignment: CrossAxisAlignment.center,
                 children: [
                   _safeText(
                     _isIncomingCall ? "INCOMING CALL" : (_isCallActive ? "ONGOING CALL" : "DIALING..."), 
                     color: _isIncomingCall ? Colors.cyanAccent : Colors.grey, 
                     fontSize: 10, 
                     letterSpacing: 1.2,
                     fontWeight: FontWeight.w800
                   ),
                   const SizedBox(height: 6),
                   Container(
                     height: 24,
                     width: double.infinity,
                     alignment: Alignment.center,
                     child: FittedBox(
                       fit: BoxFit.scaleDown,
                       child: _buildShimmerText(_status, 20)
                     )
                   ),

                   // DNA WAVE IN THE UNCOLLAPSED ISLAND
                   if (_mode == "call")
                      Container(
                        margin: const EdgeInsets.symmetric(vertical: 8),
                        height: 25,
                        width: 100,
                        child: CustomPaint(
                          painter: SiriWaveformPainter(
                            animation: _pulseController, 
                            barCount: 4,
                            color: Colors.greenAccent
                          ),
                        ),
                      ),

                   // DEBUG: Unconditionally print the phone number variable to see what Kotlin is passing
                   Padding(
                     padding: const EdgeInsets.only(top: 2),
                     child: _safeText("Num: $_phoneNumber", color: Colors.white54, fontSize: 13, letterSpacing: 0.5, textAlign: TextAlign.center)
                   ),
                 ],
               ),
             ),

             // ACCEPT / SPEAKER
             if (_isIncomingCall && !_isCallActive)
               buildPremiumButton(Icons.call, Colors.greenAccent, () async {
                   try {
                       final prefs = await SharedPreferences.getInstance();
                       await prefs.setInt('actionEvent_answer_call', DateTime.now().millisecondsSinceEpoch);
                   } catch (e) {}
               }, isActive: true)
             else if (_isCallActive || (!_isIncomingCall && !_isCallActive))
               buildPremiumButton(Icons.volume_up, Colors.white, () async {
                   setState(() { _isSpeakerOn = !_isSpeakerOn; });
                   try {
                       final prefs = await SharedPreferences.getInstance();
                       await prefs.setInt(_isSpeakerOn ? 'actionEvent_speaker_on' : 'actionEvent_speaker_off', DateTime.now().millisecondsSinceEpoch);
                   } catch (e) {}
               }, isActive: _isSpeakerOn),
          ],
        ),
      ),
    );
  }

  Widget _buildMediaUI() {
    return Container(
      padding: const EdgeInsets.all(16),
      child: Row(
        children: [
          Container(width: 50, height: 50, decoration: BoxDecoration(color: Colors.grey[800], borderRadius: BorderRadius.circular(10)), child: const Icon(Icons.music_note, color: Colors.grey)),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                _safeText("Music Playing", fontWeight: FontWeight.bold),
                _safeText("Tap for controls", color: Colors.white54, fontSize: 12),
              ],
            ),
          ),
          const Icon(Icons.skip_previous, color: Colors.white),
          const SizedBox(width: 10),
          const Icon(Icons.play_circle_fill, color: Colors.white, size: 30),
          const SizedBox(width: 10),
          const Icon(Icons.skip_next, color: Colors.white),
        ],
      ),
    );
  }

  Widget _buildModernAction(IconData icon, String label, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Column(
        children: [
          Container(
            width: 50, height: 50,
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.1),
              shape: BoxShape.circle,
              border: Border.all(color: Colors.white10)
            ),
            child: Icon(icon, color: Colors.white, size: 22),
          ),
          const SizedBox(height: 8),
          _safeText(label, color: Colors.white70, fontSize: 11)
        ],
      ),
    );
  }

  Widget _buildActionBtn(IconData icon, String label, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(color: Colors.white10, shape: BoxShape.circle),
            child: Icon(icon, color: Colors.white, size: 24),
          ),
          const SizedBox(height: 4),
          _safeText(label, color: Colors.white54, fontSize: 10)
        ],
      ),
    );
  }
  // SAFE TEXT HELPER (Prevents Red Screen)
  Widget _safeText(String text, {
    Color color = Colors.white, 
    double fontSize = 12, 
    FontWeight fontWeight = FontWeight.normal,
    TextAlign? textAlign,
    double? letterSpacing,
    TextOverflow? overflow,
  }) {
    return Text(
      text,
      textAlign: textAlign,
      overflow: overflow,
      style: TextStyle( // NO GOOGLE FONTS. NO SHADOWS.
        color: color,
        fontSize: fontSize,
        fontWeight: fontWeight,
        fontFamily: 'Roboto', // FORCE SYSTEM FONT
        letterSpacing: letterSpacing,
        shadows: [], // NUCLEAR OPTION: Empty list prevents crash
        decoration: TextDecoration.none,
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// PREMIUM SIRI WAVEFORM PAINTER
// ---------------------------------------------------------------------------
class SiriWaveformPainter extends CustomPainter {
  final Animation<double> animation;
  final int barCount;
  final Color? color; // Custom color support

  SiriWaveformPainter({
    required this.animation, 
    this.barCount = 3,
    this.color,
  }) : super(repaint: animation);

  @override
  void paint(Canvas canvas, Size size) {
    if (size.isEmpty || size.width <= 0 || size.height <= 0) return; 

    final paint = Paint()..style = PaintingStyle.fill;
    
    // If Custom Color is provided (Infinity Mode), verify it works
    if (color != null) {
       for(int i=0; i<barCount; i++) {
          double speed = 0.5 + (i * 0.2);
          double offset = i * 2.0;
          _drawWave(canvas, size, paint, color!.withOpacity(0.3), speed, offset);
       }
       return;
    }
    
    // Default Multi-Color
    _drawWave(canvas, size, paint, _cyan.withOpacity(0.4), 1.0, 0.0);
    _drawWave(canvas, size, paint, _purple.withOpacity(0.4), 0.8, 2.0);
    _drawWave(canvas, size, paint, _blue.withOpacity(0.5), 0.6, 4.0);
  }

  void _drawWave(Canvas canvas, Size size, Paint paint, Color color, double speed, double offset) {
    paint.color = color;
    final path = Path();
    
    double t = (animation.value * 2 * math.pi) * speed + offset;
    double midY = size.height / 2;
    double amp = size.height * 0.4; 

    path.moveTo(0, midY);
    for (double x = 0; x <= size.width; x++) {
      double y = midY + amp * math.sin((x / size.width * 2 * math.pi) - t);
      path.lineTo(x, y);
    }
    path.lineTo(size.width, size.height);
    path.lineTo(0, size.height);
    path.close();

    paint.blendMode = BlendMode.srcOver; 
    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(covariant SiriWaveformPainter oldDelegate) => true;
}
