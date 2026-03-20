import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter/services.dart';
import 'dart:ui' as ui;
import 'dart:async';
import '../../services/database_service.dart';

class NoteSheet extends StatefulWidget {
  final String number;
  final Function(String, Map<String, dynamic>?) onNativeInvoke;

  const NoteSheet({super.key, required this.number, required this.onNativeInvoke});

  @override
  State<NoteSheet> createState() => _NoteSheetState();
}

class _NoteSheetState extends State<NoteSheet> {
  final TextEditingController _controller = TextEditingController();
  final FocusNode _focusNode = FocusNode();
  bool _isSaving = false;
  bool _hasStartedTyping = false;

  @override
  void initState() {
    super.initState();
    _controller.addListener(_onTextChanged);
    // OPTIMIZATION: Delay focus slightly for animation smoothness
    Future.delayed(const Duration(milliseconds: 400), () {
      if (mounted) FocusScope.of(context).requestFocus(_focusNode);
    });
  }

  void _onTextChanged() {
    final hasText = _controller.text.isNotEmpty;
    if (_hasStartedTyping != hasText) {
      setState(() => _hasStartedTyping = hasText);
    }
  }

  @override
  void dispose() {
    _controller.removeListener(_onTextChanged);
    _controller.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // REQUIREMENTS:
    // 1. FROSTED PREMIUM MODERN BUTTONS (+COPY)
    // 2. COMPLETE BLUR BLACK (NO GREY)
    // 3. NO BORDER
    // 4. SMALLER SIZE
    // 5. TYPEWRITER HINT / WHATSAPP STYLE ...
    // 6. 65% TRANSPARENT BLUR SHOWING PHYSICS

    return Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
      child: SizedBox(
        height: MediaQuery.of(context).size.height * 0.55, // Requirement: SMALLER
        child: Stack(
          alignment: Alignment.bottomCenter,
          children: [
            // 1. THE GLASS LAYER
            ClipRRect(
              borderRadius: const BorderRadius.vertical(top: Radius.circular(40)), // Apple-style large radius
              child: BackdropFilter(
                filter: ui.ImageFilter.blur(sigmaX: 40, sigmaY: 40), // Heavy Premium Blur
                child: Container(
                  decoration: BoxDecoration(
                    color: const Color(0xFF000000).withOpacity(0.65), // Requirement: 65% Black
                    borderRadius: const BorderRadius.vertical(top: Radius.circular(40)),
                     // NO BORDERS as requested
                  ),
                  child: Column(
                    children: [
                      // HANDLE
                      const SizedBox(height: 16),
                      Center(
                        child: Container(
                          width: 36, height: 4,
                          decoration: BoxDecoration(
                            color: Colors.white.withOpacity(0.15), 
                            borderRadius: BorderRadius.circular(2)
                          ),
                        ),
                      ),
                      
                      // HEADER
                      Padding(
                        padding: const EdgeInsets.fromLTRB(32, 24, 32, 10),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                             Text("Quick Note", 
                               style: GoogleFonts.outfit(color: Colors.white, fontSize: 24, fontWeight: FontWeight.w600, letterSpacing: -0.5)
                             ),
                             
                             // CLOSE (Minimal)
                             GestureDetector(
                               onTap: () => Navigator.pop(context),
                               child: CircleAvatar(
                                 radius: 16,
                                 backgroundColor: Colors.white.withOpacity(0.1),
                                 child: const Icon(Icons.close, size: 18, color: Colors.white),
                               ),
                             )
                          ],
                        ),
                      ),
                      
                      // TEXT FIELD AREA (MESSAGE BUBBLE)
                      Expanded(
                        child: Align(
                          alignment: Alignment.topRight, // User note = Outgoing message align
                          child: Container(
                             margin: const EdgeInsets.symmetric(horizontal: 24, vertical: 10),
                             constraints: BoxConstraints(
                                maxWidth: MediaQuery.of(context).size.width * 0.85, // Max width like a bubble
                             ),
                             decoration: BoxDecoration(
                               color: const Color(0xFF2C2C2E), // iMessage/WhatsApp Dark Bubble Color
                               borderRadius: const BorderRadius.only(
                                  topLeft: Radius.circular(20),
                                  topRight: Radius.circular(4), // Pointy corner for "outgoing" feel
                                  bottomLeft: Radius.circular(20),
                                  bottomRight: Radius.circular(20)
                               ),
                               border: Border.all(color: Colors.white.withOpacity(0.05))
                             ),
                             child: Stack(
                               children: [
                                  // 1. SCROLLABLE TEXT FIELD
                                  SingleChildScrollView( // Allows expansion then scroll
                                     child: Padding(
                                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                                        child: TextField(
                                           controller: _controller,
                                           focusNode: _focusNode,
                                           maxLines: null, // Dynamic expansion
                                           style: GoogleFonts.outfit(
                                              color: Colors.white, 
                                              fontSize: 17, 
                                              height: 1.3,
                                              shadows: [
                                                 Shadow(color: Colors.white.withOpacity(0.4), blurRadius: 12),
                                                 Shadow(color: Colors.white.withOpacity(0.1), blurRadius: 4),
                                              ]
                                           ),
                                           cursorColor: Colors.blueAccent,
                                           decoration: const InputDecoration(
                                              isDense: true,
                                              contentPadding: EdgeInsets.zero,
                                              hintText: "",
                                              filled: false, // FIX: Transparent background
                                              fillColor: Colors.transparent, 
                                              border: InputBorder.none,
                                              focusedBorder: InputBorder.none,
                                              enabledBorder: InputBorder.none,
                                              errorBorder: InputBorder.none,
                                              disabledBorder: InputBorder.none,
                                           ),
                                        ),
                                     ),
                                  ),
                                  
                                  // 2. WHATSAPP DOTS (Inside Bubble)
                                  if (!_hasStartedTyping)
                                    Positioned(
                                      left: 16, top: 14,
                                      child: IgnorePointer(
                                        child: _WhatsAppDots(),
                                      ),
                                    ),
                               ],
                             ),
                          ),
                        ),
                      ),
                      
                      // ACTION BUTTONS
                      _buildActionRow(context),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ).animate().moveY(begin: 100, end: 0, duration: 350.ms, curve: Curves.easeOutQuart),
    );
  }

  Widget _buildActionRow(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(24, 0, 24, 32),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          _buildGlassButton(
            icon: Icons.copy_rounded,
            label: "Copy",
            onTap: () {
               if (_controller.text.isNotEmpty) {
                  HapticFeedback.selectionClick();
                  Clipboard.setData(ClipboardData(text: _controller.text));
                  // Subtle feedback
               }
            }
          ),
          
          const SizedBox(width: 12),
          
          _buildGlassButton(
            icon: Icons.ios_share_rounded,
            label: "Share",
            onTap: () {
               if (_controller.text.isNotEmpty) {
                  HapticFeedback.mediumImpact();
                  // VERIFIED LOGIC
                  widget.onNativeInvoke("shareText", {"text": "Note for ${widget.number}:\n\n${_controller.text}"});
               }
            }
          ),
          
          const SizedBox(width: 12),
          
          _buildGlassButton(
            icon: Icons.save_rounded,
            label: "Save",
            isPrimary: true,
            isLoading: _isSaving,
            onTap: () async {
               if (_controller.text.isNotEmpty) {
                  setState(() => _isSaving = true);
                  HapticFeedback.heavyImpact();
                  // VERIFIED LOGIC
                  await DatabaseService().addCallNote(widget.number, _controller.text);
                  if (mounted) {
                      setState(() => _isSaving = false);
                      Navigator.pop(context);
                  }
               }
            }
          ),
        ],
      ),
    );
  }

  Widget _buildGlassButton({
    required IconData icon, 
    required String label, 
    bool isPrimary = false, 
    bool isLoading = false,
    required VoidCallback onTap
  }) {
    return Expanded(
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          height: 60, // Taller touch target
          decoration: BoxDecoration(
            color: isPrimary ? Colors.white : Colors.white.withOpacity(0.08),
            borderRadius: BorderRadius.circular(20), // Soft Apple-like radius
            // No Borders
          ),
           child: Center(
              child: isLoading
                 ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.black))
                 : Column( // Icon + Text Stack for modern look
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                       Icon(icon, color: isPrimary ? Colors.black : Colors.white, size: 22),
                       const SizedBox(height: 2),
                       Text(label, 
                          style: GoogleFonts.outfit(
                             color: isPrimary ? Colors.black : Colors.white.withOpacity(0.6), 
                             fontSize: 11, 
                             fontWeight: FontWeight.w600
                          )
                       ),
                    ],
                 ),
           ),
        ),
      ),
    );
  }
}

// PREMIUM WHATSAPP-STYLE DOTS (GLOWING)
class _WhatsAppDots extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        _buildDot(0),
        const SizedBox(width: 6),
        _buildDot(300),
        const SizedBox(width: 6),
        _buildDot(600),
      ],
    );
  }

  Widget _buildDot(int delayMs) {
     return Container(
       width: 10, height: 10,
       decoration: BoxDecoration(
         color: Colors.white.withOpacity(0.8), // Standard Grey/White
         shape: BoxShape.circle,
         boxShadow: [
            BoxShadow(color: Colors.white.withOpacity(0.4), blurRadius: 10, spreadRadius: 2), // GLOW for dots
            BoxShadow(color: Colors.white.withOpacity(0.1), blurRadius: 4, spreadRadius: 1),
         ]
       ),
     ).animate(onPlay: (c) => c.repeat(reverse: true))
      .scale(begin: const Offset(0.7, 0.7), end: const Offset(1.1, 1.1), duration: 600.ms, delay: delayMs.ms)
      .fade(begin: 0.3, end: 1.0, duration: 600.ms, delay: delayMs.ms);
  }
}
