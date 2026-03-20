import 'dart:math';
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:google_fonts/google_fonts.dart';

class ChatInput extends StatefulWidget {
  final TextEditingController controller;
  final Function(String) onSubmitted;
  final VoidCallback? onMicPressed; // Tap (legacy)
  final Function(bool isRecording)? onMicLongPressChanged; // Hold for Transcribe
  final VoidCallback? onMicLocked; // Slide up for Wave
  final VoidCallback? onStopRecording;
  final bool isLoading;

  const ChatInput({
    Key? key,
    required this.controller,
    required this.onSubmitted,
    this.onMicPressed,
    this.onMicLongPressChanged,
    this.onMicLocked,
    this.onStopRecording,
    this.isLoading = false,
  }) : super(key: key);

  @override
  _ChatInputState createState() => _ChatInputState();
}

class _ChatInputState extends State<ChatInput> with SingleTickerProviderStateMixin {
  bool _isComposing = false;
  bool _isLocked = false; // Wave/Voice Mode Locked
  bool _isHolding = false; // Transient Hold state
  late AnimationController _waveController;

  @override
  void initState() {
    super.initState();
    widget.controller.addListener(_onTextChanged);
    _waveController = AnimationController(vsync: this, duration: const Duration(milliseconds: 1000))..repeat(reverse: true);
  }

  void _onTextChanged() {
    setState(() {
      _isComposing = widget.controller.text.trim().isNotEmpty;
    });
  }

  @override
  void dispose() {
    widget.controller.removeListener(_onTextChanged);
    _waveController.dispose();
    super.dispose();
  }

  void _handleSubmitted() {
    if (_isComposing && !widget.isLoading) {
      widget.onSubmitted(widget.controller.text.trim());
      // Reset Recording States if any
      if (_isLocked) { 
         setState(() => _isLocked = false); 
         widget.onStopRecording?.call();
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final accentColor = const Color(0xFF00F0FF); 

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      color: Colors.transparent, // Parent handles BG (Black)
      child: SafeArea(
        child: Stack(
            clipBehavior: Clip.none,
            alignment: Alignment.bottomRight,
            children: [
                Row(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
            // Expanded Input Box
            Expanded(
              child: Container(
                constraints: const BoxConstraints(maxHeight: 120),
                decoration: BoxDecoration(
                  color: const Color(0xFF101010),
                  borderRadius: BorderRadius.circular(24),
                ),
                child: Stack(
                  alignment: Alignment.centerLeft,
                  children: [
                    TextField(
                      controller: widget.controller,
                      maxLines: null,
                      style: GoogleFonts.getFont('Outfit', fontSize: 16, color: Colors.white),
                      cursorColor: accentColor,
                      decoration: InputDecoration(
                        hintText: _isLocked ? "  " : (_isHolding ? "  " : "Message..."), // Hide hint when recording for Waveform
                        hintStyle: GoogleFonts.getFont('Outfit', fontSize: 16, color: Colors.grey[600]),
                        border: InputBorder.none,
                        contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
                        isDense: false,
                      ),
                      onSubmitted: (text) => _handleSubmitted(),
                    ),

                  ],
                ),
              ),
            ),
            const SizedBox(width: 8),

            // Locked Cancel Button (Visible only when locked)
            if (_isLocked)
               Padding(
                  padding: const EdgeInsets.only(bottom: 0, right: 8),
                  child: IconButton(
                    icon: const Icon(Icons.delete_outline, color: Colors.redAccent),
                    onPressed: () {
                        setState(() { _isLocked = false; });
                        widget.onStopRecording?.call();
                        widget.controller.clear();
                    },
                  ),
               ),
            
            // Mic Button (Always Visible)
            Padding(
               padding: const EdgeInsets.only(bottom: 0), // Base alignment
               child: _buildMicGestureButton(accentColor),
            ),

            const SizedBox(width: 8),

            // Send Button (Always Visible & Separated)
            Padding(
               padding: const EdgeInsets.only(bottom: 0),
               child: widget.isLoading
                ? const SizedBox(width: 44, height: 44, child: Center(child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)))
                : _buildIconButton(
                    icon: Icons.arrow_upward,
                    onPressed: _handleSubmitted,
                    backgroundColor: _isComposing ? theme.primaryColor : Colors.grey[800],
                    color: _isComposing ? Colors.white : Colors.grey[500],
                  ),
            ),
          ],
        ),

        // Waveform Overlay ABOVE the input box (when recording)
        // Waveform Overlay (Modern & Sleek)
        if (_isLocked || _isHolding)
            Positioned(
                bottom: 85, // Just above the mic button
                right: 20,  // Aligned with the mic button on the right
                child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    decoration: BoxDecoration(
                      color: const Color(0xFF101010).withOpacity(0.9), // Darker, sleeker background
                      borderRadius: BorderRadius.circular(24),
                      border: Border.all(color: Colors.cyanAccent.withOpacity(0.3)),
                      boxShadow: [
                         BoxShadow(color: Colors.cyanAccent.withOpacity(0.1), blurRadius: 10, spreadRadius: 2)
                      ]
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        // Recording Indicator
                        Container(
                          width: 8, height: 8,
                          decoration: const BoxDecoration(color: Colors.cyanAccent, shape: BoxShape.circle),
                        ).animate(onPlay: (c) => c.repeat(reverse: true)).fade(duration: 600.ms),
                        const SizedBox(width: 8),
                        
                        Text(
                          _isLocked ? "Recording" : "Listening...", 
                          style: GoogleFonts.getFont('Outfit', color: Colors.cyanAccent, fontSize: 12, fontWeight: FontWeight.w600)
                        ),
                        const SizedBox(width: 12),
                        
                        // Sleek Waveform
                        RepaintBoundary(
                            child: SizedBox(
                              width: 100, 
                              height: 24,
                              child: CustomPaint(
                                 painter: SleekWaveformPainter(
                                   animation: _waveController, 
                                   color: Colors.cyanAccent
                                 ),
                              ),
                            ),
                        ),
                      ],
                    ),
                ),
            ),
        
        // Slide to Lock Indicator (Overlay)
        if (_isHolding && !_isLocked)
            Positioned(
                bottom: 130, 
                right: 60, 
                child: Animate(
                    effects: [MoveEffect(begin: Offset(0, 10), end: Offset(0, 0), duration: 500.ms, curve: Curves.easeOutBack), FadeEffect()],
                    child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                            const Icon(Icons.keyboard_arrow_up, color: Colors.white54),
                            Text("Slide to Lock", style: GoogleFonts.getFont('Outfit', color: Colors.white54, fontSize: 12)),
                        ],
                    ),
                ),
            )
      ]),
      ),
    );
  }
  
  // Removed _buildLockedUI to keep Input Field visible

  Widget _buildMicGestureButton(Color accentColor) {
     return GestureDetector(
       onLongPressStart: (_) {
         if (_isLocked) return; // Don't trigger long press when locked
         setState(() => _isHolding = true);
         widget.onMicLongPressChanged?.call(true);
       },
       onLongPressEnd: (_) {
         if (!_isLocked) {
            setState(() => _isHolding = false);
            widget.onMicLongPressChanged?.call(false);
         }
       },
       onLongPressMoveUpdate: (details) {
         // Slide Up Logic
         if (details.offsetFromOrigin.dy < -50 && !_isLocked) { // Threshold
             setState(() {
               _isLocked = true; 
               _isHolding = false;
             });
             widget.onMicLocked?.call();
         }
       },
       onTap: () {
         // If locked, tap to unlock
         if (_isLocked) {
           setState(() => _isLocked = false);
           widget.onStopRecording?.call();
         } else {
           // Normal tap behavior
           widget.onMicPressed?.call();
         }
       },
       child: Animate(
         target: (_isHolding && !_isLocked) ? 1 : 0, // Only scale when holding in UNLOCKED mode
         effects: [
            ScaleEffect(begin: const Offset(1, 1), end: const Offset(1.8, 1.8), duration: 200.ms, curve: Curves.easeOutBack), // Big Scaling
         ],
         child: Container(
           width: 50, height: 50, // Slightly bigger base
           decoration: BoxDecoration(
             // Use Cyan (accentColor) for Locked state too, maybe darker or same?
             // User said "button needs to be cyan and not red"
             color: _isLocked ? Colors.cyan : (_isHolding ? accentColor : const Color(0xFF1E1E1E)), 
             shape: BoxShape.circle,
              boxShadow: _isHolding || _isLocked ? [BoxShadow(color: accentColor.withOpacity(0.6), blurRadius: 20, spreadRadius: 5)] : [],
            ),
            child: Icon(
              _isLocked ? Icons.lock : (_isHolding ? Icons.mic : Icons.mic_none), 
              color: _isLocked ? Colors.white : (_isHolding ? Colors.black : Colors.white), // Cyan icon when active
              size: 26
            ),
         ),
       ),
     );
  }

  Widget _buildIconButton({
    required IconData icon,
    VoidCallback? onPressed,
    Color? color,
    Color? backgroundColor,
    double size = 44,
  }) {
    return InkWell(
      onTap: onPressed,
      borderRadius: BorderRadius.circular(size / 2),
      child: Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
          color: backgroundColor ?? Colors.transparent,
          shape: BoxShape.circle,
        ),
        child: Icon(icon, color: color, size: 24),
      ),
    );
  }


  Widget _buildWaveform(Color color) {
     return Container(); // Deprecated, replaced by CustomPainter
  }
}

class SleekWaveformPainter extends CustomPainter {
  final Animation<double> animation;
  final Color color;

  SleekWaveformPainter({required this.animation, required this.color}) : super(repaint: animation);

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..strokeWidth = 2.0
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;

    final path = Path();
    final centerY = size.height / 2;
    // Dynamic sine wave
    for (double x = 0; x <= size.width; x++) {
      // 2 overlapping waves
      double y1 = sin((x / size.width * 4 * pi) + (animation.value * 2 * pi)) * 8;
      double y2 = sin((x / size.width * 6 * pi) - (animation.value * 2 * pi)) * 4;
      
      // Amplitude modulation (taper ends)
      double amplitude = 1.0 - (2 * (x / size.width - 0.5).abs()); // 0 at ends, 1 in center
      
      if (x == 0) {
        path.moveTo(x, centerY + (y1 + y2) * amplitude);
      } else {
        path.lineTo(x, centerY + (y1 + y2) * amplitude);
      }
    }
    
    // Glow effect
    canvas.drawPath(path, paint..strokeWidth=3..color=color.withOpacity(0.3));
    canvas.drawPath(path, paint..strokeWidth=1.5..color=color);
  }

  @override
  bool shouldRepaint(covariant SleekWaveformPainter oldDelegate) => true;
}
