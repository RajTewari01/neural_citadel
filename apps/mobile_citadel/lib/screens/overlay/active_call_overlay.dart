import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:neural_citadel/services/phone_control_service.dart';
import 'package:neural_citadel/ui/physics/physics_background.dart';
import 'package:neural_citadel/services/physics_manager.dart';
import 'package:neural_citadel/services/contact_service.dart'; // For RichContact if needed

// Simple Call State Enum
enum CallStatus { incoming, active, ended }

class ActiveCallOverlay extends StatefulWidget {
  final String callerName;
  final String? callerNumber;
  final String? profession; // Rich data
  final String? location;   // Rich data
  final String? imagePath;
  final CallStatus initialState;

  const ActiveCallOverlay({
    super.key,
    required this.callerName,
    this.callerNumber,
    this.profession,
    this.location,
    this.imagePath,
    this.initialState = CallStatus.active,
  });

  @override
  State<ActiveCallOverlay> createState() => _ActiveCallOverlayState();
}

class _ActiveCallOverlayState extends State<ActiveCallOverlay> {
  final PhoneControlService _phoneService = PhoneControlService();
  bool _isSpeakerOn = false;
  bool _isMuted = false;
  
  @override
  Widget build(BuildContext context) {
    // Determine Physics Mode from Manager
    // In a real expanded app, we might pass this as arg or look it up.
    final mode = PhysicsManager().currentMode;

    return PhysicsBackground(
      mode: mode, 
      child: Scaffold(
        backgroundColor: Colors.transparent,
        body: SafeArea(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              // Top Bar (Minimize)
              Padding(
                padding: const EdgeInsets.only(top: 16),
                child: IconButton(
                  icon: const Icon(Icons.keyboard_arrow_down, color: Colors.white, size: 32),
                  onPressed: () {
                     // Logic to minimize back to Island would go here
                     // For now, standard back (which might close overlay window activity)
                     // If using flutter_overlay_window, we might need specific API to close.
                  },
                ),
              ),

              // Caller Info (Cyberpunk Center)
              Column(
                children: [
                  Container(
                    width: 120,
                    height: 120,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(color: Colors.cyanAccent, width: 2),
                      boxShadow: [
                         BoxShadow(color: Colors.cyanAccent.withOpacity(0.5), blurRadius: 20),
                      ],
                      image: widget.imagePath != null
                          ? DecorationImage(image: NetworkImage(widget.imagePath!), fit: BoxFit.cover)
                          : null,
                    ),
                     child: widget.imagePath == null
                          ? Center(child: Text(widget.callerName[0], style: GoogleFonts.orbitron(fontSize: 48, color: Colors.white)))
                          : null,
                  ),
                  const SizedBox(height: 24),
                  Text(
                    widget.callerName,
                    style: GoogleFonts.orbitron(
                      fontSize: 32,
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                      shadows: [Shadow(color: Colors.cyanAccent, blurRadius: 10)],
                    ),
                  ),
                  const SizedBox(height: 8),
                  if (widget.profession != null)
                    Text(
                      '${widget.profession} // ${widget.location ?? 'N/A'}',
                      style: GoogleFonts.sourceCodePro(
                        color: Colors.cyanAccent,
                        fontSize: 16,
                        letterSpacing: 2,
                      ),
                    ),
                   const SizedBox(height: 8),
                   Text(
                    widget.initialState == CallStatus.incoming ? 'INCOMING SIGNAL...' : 'LINK ESTABLISHED',
                    style: GoogleFonts.sourceCodePro(color: Colors.white54),
                   ),
                ],
              ),

              // Controls
              Container(
                margin: const EdgeInsets.all(32),
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                  color: Colors.black.withOpacity(0.4),
                  borderRadius: BorderRadius.circular(32),
                  border: Border.all(color: Colors.white10),
                ),
                child: widget.initialState == CallStatus.incoming
                    ? _buildIncomingControls()
                    : _buildActiveControls(),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildIncomingControls() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children: [
         _buildCircleBtn(Icons.call_end, Colors.red, () async {
            await _phoneService.endCall();
         }),
         _buildCircleBtn(Icons.call, Colors.greenAccent, () async {
            await _phoneService.answerCall();
            // TODO: Update local state to active 
         }),
      ],
    );
  }

  Widget _buildActiveControls() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children: [
        _buildIconBtn(Icons.mic_off, _isMuted ? Colors.red : Colors.white, () {
           setState(() => _isMuted = !_isMuted);
           // Native Mute Logic
        }),
        _buildCircleBtn(Icons.call_end, Colors.red, () async {
           await _phoneService.endCall();
        }),
        _buildIconBtn(Icons.volume_up, _isSpeakerOn ? Colors.greenAccent : Colors.white, () async {
           setState(() => _isSpeakerOn = !_isSpeakerOn);
           await _phoneService.setSpeakerphone(_isSpeakerOn);
        }),
      ],
    );
  }

  Widget _buildCircleBtn(IconData icon, Color color, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 72,
        height: 72,
        decoration: BoxDecoration(
          color: color.withOpacity(0.2),
          shape: BoxShape.circle,
          border: Border.all(color: color),
        ),
         child: Icon(icon, color: color, size: 32),
      ),
    );
  }
  
  Widget _buildIconBtn(IconData icon, Color color, VoidCallback onTap) {
     return IconButton(
       icon: Icon(icon, color: color, size: 32),
       onPressed: onTap,
     );
  }
}
