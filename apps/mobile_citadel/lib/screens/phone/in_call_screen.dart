import 'package:flutter/material.dart';
import 'package:flutter/cupertino.dart';
import 'package:google_fonts/google_fonts.dart';
import 'dart:ui' as ui;
import 'package:url_launcher/url_launcher.dart';
import 'dart:async';
import 'package:flutter/services.dart';
import 'package:permission_handler/permission_handler.dart'; // REQUIRED
import 'package:flutter_callkit_incoming/flutter_callkit_incoming.dart';
import 'package:wakelock_plus/wakelock_plus.dart';
import '../../ui/physics/physics_background.dart';

// ... (Rest of imports)

// Imports cleaned up
import '../../services/physics_manager.dart';
import '../../ui/physics/modes/gravity_orbs_painter.dart'; 
import '../../services/contact_service.dart';
import '../../services/database_service.dart';
import 'note_sheet.dart';
import 'dart:io';
import '../../utils/call_lock.dart';
import '../../services/call_overlay_service.dart';
import 'edit_contact_screen.dart'; // Added Import

class InCallScreen extends StatefulWidget {
  final String callerName;
  final String callerNumber;
  final bool isIncoming;
  final String? debugInfo; // Diagnostics
  
  // Debug Helpers
  static int debugContactCount = 0;

  const InCallScreen({
    super.key, 
    required this.callerName, 
    required this.callerNumber,
    this.isIncoming = false,
    this.debugInfo,
  });

  @override
  State<InCallScreen> createState() => _InCallScreenState();
}



class _InCallScreenState extends State<InCallScreen> with SingleTickerProviderStateMixin {
  late AnimationController _pulseController;
  bool _showSuggestionPill = true;
  bool _isMoreExpanded = false; // Phase 8: Dynamic Expansion
  Duration _callDuration = Duration.zero;
  Timer? _timer;
  Timer? _nativePollTimer; // Self-healing timer
  static const _platform = MethodChannel('com.neuralcitadel/native');

  // Audio Route Constants (Matches Android CallAudioState)
  static const int ROUTE_EARPIECE = 1;
  static const int ROUTE_BLUETOOTH = 2;
  static const int ROUTE_WIRED_HEADSET = 4;
  static const int ROUTE_SPEAKER = 8;
  
  // State
  int _audioRoute = ROUTE_EARPIECE;
  int _supportedAudioRoutes = ROUTE_EARPIECE;
  List<Map<String, dynamic>> _supportedBluetoothDevices = [];
  Map<String, dynamic>? _activeBluetoothDevice;
  
  bool _isMuted = false;
  bool _isRecording = false;
  bool _isOnHold = false;
  bool _isEndingCall = false;
  bool _isResolving = false;
  bool _isVideoMode = false; // Video State
  bool _isCameraPaused = false; // NEW: Local Privacy Mode
  bool _isPipMode = false; // NEW: PiP State
  bool _isRequestDialogOpen = false; // Safe Dialog State
  
  // CONFERENCE & MULTI-CALL STATE
  bool _isConference = false;
  Map<String, dynamic>? _backgroundCall;
  List<Map<String, dynamic>> _participants = [];

  int? _videoViewId; // Dynamic Video View ID
  String _debugStatus = "Checking DB...";
  int _nullCheckCounter = 0; // Debounce for disconnect
  
  // Dynamic Contact Data
  late String _effectiveNumber; // Mutable number (starts with widget.callerNumber)
  String _currentTheme = "default";
  ImageProvider? _avatarImage;
  RichContact? _resolvedContact;
  final ContactService _contactService = ContactService();

  @override
  void initState() {
    super.initState();
    CallLock.isActive = true; 
    _effectiveNumber = widget.callerNumber;
    _videoViewId = null; // Reset
    _setupNativeListener(); // Call the new listener setup

    _pulseController = AnimationController(vsync: this, duration: const Duration(milliseconds: 2000))..repeat();
    
    // START RESOLUTION
    _resolveContact();

    // Setup Overlay Restore
    CallOverlayService.instance.setRestoreCallback((ctx) {
         Navigator.of(ctx).push(MaterialPageRoute(
             builder: (_) => InCallScreen(
                 callerName: widget.callerName,
                 callerNumber: widget.callerNumber,
                 isIncoming: false,
             )
         ));
    });

    // Check if Overlay is already active (e.g. returning from PiP)
    print("🔄 InitState: Checking Overlay Logic. Active=${CallOverlayService.instance.isActive}");
    if (CallOverlayService.instance.isActive) {
        // Synchronous Restore attempt
        _isVideoMode = true; 
        
        WidgetsBinding.instance.addPostFrameCallback((_) {
             print("🔄 Maximizing Overlay from InitState");
             CallOverlayService.instance.maximize(context);
             if (mounted) setState(() {}); // Refresh to be sure
        });
    }

    // ALWAYS poll to sync state (Disconnects, Number Updates)
    _startContinuousNativeCheck();

    if (!widget.isIncoming) {
      _startTimer();
    }
    
    // NATIVE INTEGRATION: Activate Proximity Sensor (Screen Off)
    _invokeNative("enableProximity", {"enable": true});
    WakelockPlus.enable(); // Keep Screen On for Video/Call
    
    // Register Native Listeners (Incoming Video, PiP)
    _setupNativeListener();

  }

  void _startContinuousNativeCheck() {
      _nativePollTimer = Timer.periodic(const Duration(milliseconds: 800), (timer) async {
          if (!mounted) { timer.cancel(); return; }
          try {
             final dynamic result = await _platform.invokeMethod('checkActiveCall');
             
             // Auto-Close if call ended externally (with Debounce)
             if (result == null) {
                  print("DEBUG: Active Call Check returned NULL. Counter: $_nullCheckCounter");
                  _nullCheckCounter++;
                  if (_nullCheckCounter > 2) { // Wait for 3 consecutive nulls (~2.4s)
                      // ENABLED AUTO-CLOSE
                      if (_debugStatus != "Call Ended") {
                         setState(() => _debugStatus = "Call Ended");
                      }
                      if (mounted && !_isEndingCall) {
                          Navigator.of(context).popUntil((route) => route.isFirst);
                      }
                      timer.cancel();
                  }
                  return;
             }
             _nullCheckCounter = 0; // Reset on success

             if (result != null && result is Map) {
                 // 1. SYNC MULTI-CALL STATE (Async / Background)
                 if (result.containsKey("background")) {
                     final bgMap = Map<String, dynamic>.from(result["background"]);
                     if (_backgroundCall == null || _backgroundCall!['number'] != bgMap['number']) {
                        setState(() => _backgroundCall = bgMap);
                     }
                 } else {
                     if (_backgroundCall != null) setState(() => _backgroundCall = null);
                 }
                 
                 bool conf = result["conference"] == true;
                 if (_isConference != conf) setState(() => _isConference = conf);
                 
                 // 1.1 Sync Participants (New)
                 if (conf && result.containsKey("participants")) {
                     final List<dynamic> rawParts = result["participants"];
                     final List<Map<String, dynamic>> newParts = rawParts.map((e) => Map<String, dynamic>.from(e)).toList();
                     if (newParts.length != _participants.length) { 
                         setState(() => _participants = newParts);
                     }
                 }

                 // 2. Sync Number (Self-Healing)
                 String newNumber = result["number"] as String? ?? "Unknown";
                 if (newNumber != "Unknown" && newNumber != _effectiveNumber && !_isConference) {
                     print("✨ SELF-HEALING: Found real number $newNumber");
                     setState(() {
                        _effectiveNumber = newNumber;
                     });
                     _resolveContact(); // Re-trigger resolution
                 }

                 // 3. Sync Mute State (Native -> Flutter)
                 bool nativeMute = result["isMuted"] as bool? ?? false;
                 if (nativeMute != _isMuted) {
                     setState(() {
                        _isMuted = nativeMute;
                     });
                 }
                 
                 // 4. Sync Audio Route (New Phase 9)
                 if (result.containsKey("audioRoute")) {
                     int route = result["audioRoute"] as int;
                     if (route != _audioRoute) setState(() => _audioRoute = route);
                 }
                 if (result.containsKey("supportedAudioRoutes")) {
                     int mask = result["supportedAudioRoutes"] as int;
                     if (mask != _supportedAudioRoutes) setState(() => _supportedAudioRoutes = mask);
                 }
                 if (result.containsKey("supportedBluetoothDevices")) {
                     final List<dynamic> raw = result["supportedBluetoothDevices"];
                     final List<Map<String, dynamic>> devices = raw.map((e) => Map<String, dynamic>.from(e)).toList();
                     if (_supportedBluetoothDevices.length != devices.length) {
                         setState(() => _supportedBluetoothDevices = devices);
                     }
                 }
                 if (result.containsKey("activeBluetoothDevice")) {
                     final activeBt = result["activeBluetoothDevice"] != null ? Map<String, dynamic>.from(result["activeBluetoothDevice"]) : null;
                     if (_activeBluetoothDevice?["address"] != activeBt?["address"]) {
                         setState(() => _activeBluetoothDevice = activeBt);
                     }
                 } else {
                     if (_activeBluetoothDevice != null) setState(() => _activeBluetoothDevice = null);
                 }
             }
          } catch (_) {}
      });
  }

  Future<void> _resolveContact() async {
    // 1. Try Local DB Lookup (Most Reliable)
    if (_effectiveNumber != "Unknown") {
       try {
         final contact = await _contactService.getContactByNumber(_effectiveNumber);
         if (contact != null && mounted) {
           setState(() {
              _resolvedContact = contact;
              _currentTheme = contact.theme ?? "default";
              _isResolving = false;
              
               // Resolve Image
               if (contact.customImage != null && File(contact.customImage!).existsSync()) {
                  _avatarImage = FileImage(File(contact.customImage!));
               } else if (contact.nativeContact.photo != null) { 
                  _avatarImage = MemoryImage(contact.nativeContact.photo!);
               } else if (contact.nativeContact.thumbnail != null) {
                  _avatarImage = MemoryImage(contact.nativeContact.thumbnail!);
               }
           });
           return;
         }
       } catch (e) {
         print("Resolution Error: $e");
       }
    }

    if (mounted) {
       setState(() {
          _isResolving = false; 
       });
    }
  }

  void _startTimer() {
    _timer = Timer.periodic(const Duration(seconds: 1), (t) {
      if (mounted) setState(() => _callDuration += const Duration(seconds: 1));
    });
  }

  void _setupNativeListener() {
      const MethodChannel("com.neuralcitadel/native").setMethodCallHandler((call) async {
          // 1. PIP SYNC
          if (call.method == "PIP_MODE_CHANGED") {
             bool pip = call.arguments as bool;
             setState(() => _isPipMode = pip);
             
             // SYSTEM PIP -> Force Overlay Maximize (Background Mode) so Native Window is filled
             if (pip) {
                 if (CallOverlayService.instance.isActive) {
                     CallOverlayService.instance.maximize(context);
                 }
             }

             // Propagate to Native Video View to Hide/Show Local Camera (Tiny Mode)
             int? vid = CallOverlayService.instance.videoId;
             if (vid != null) {
                  MethodChannel("neural_video_view_$vid").invokeMethod("setPipMode", {"active": pip});
             }
          }
          // 2. INCOMING VIDEO REQUEST
           else if (call.method == "incomingVideoRequest") {
              if (!mounted) return;
              
              // 1. SAFETY: Prevent Stacked Dialogs
              if (_isRequestDialogOpen) {
                  print("⚠️ Dialog already open. Ignoring duplicate request.");
                  return;
              }

              // 2. Set Active Flag
              _isRequestDialogOpen = true;
              print("✅ INCOMING VIDEO REQUEST: Showing Dialog");
              
              showDialog(
                  context: context,
                  barrierDismissible: false,
                  builder: (ctx) => AlertDialog(
                      title: const Text("Incoming Video Request"),
                      content: const Text("The other person wants to switch to video."),
                      actions: [
                          TextButton(
                              onPressed: () {
                                  _isRequestDialogOpen = false; // Reset
                                  Navigator.pop(ctx);
                              }, 
                              child: const Text("Decline")
                          ),
                          TextButton(
                              onPressed: () async {
                                 _isRequestDialogOpen = false; // Reset
                                 Navigator.pop(ctx);
                                 await const MethodChannel('com.neuralcitadel/native').invokeMethod("acceptVideoUpgrade");
                                 // Check Perms & Enable
                                 if (await Permission.camera.request().isGranted) {
                                     setState(() => _isVideoMode = true);
                                     
                                     // 1. Start Video Service
                                     WidgetsBinding.instance.addPostFrameCallback((_) {
                                          CallOverlayService.instance.startCall(context);
                                     });
                                     
                                     // 2. Disable Proximity
                                     _invokeNative("enableProximity", {"enable": false});
                                 }
                              },
                              child: const Text("Accept")
                          )
                      ]
                  )
              ).then((_) {
                  // Fallback reset if dialog closed by other means
                  if (mounted) _isRequestDialogOpen = false; 
              });
           }
           
           // 3. REMOTE DOWNGRADE (Other person switched to audio)
           else if (call.method == "downgradeToAudio") {
               print("📉 NATIVE EVENT: Downgrade to Audio");
               if (_isVideoMode) {
                   setState(() => _isVideoMode = false);
                   CallOverlayService.instance.endCall();
                   _invokeNative("enableProximity", {"enable": true});
               }
           }
       });
  }

  @override
  void dispose() {
    CallLock.isActive = false;
    
    // NATIVE INTEGRATION: Release Proximity Sensor
    _invokeNative("enableProximity", {"enable": false});
    
    // CRITICAL: Force Video/Overlay Cleanup on Hangup
    CallOverlayService.instance.endCall();
    if (_isVideoMode) {
      _isVideoMode = false;
    }
    
    _pulseController.dispose();
    _nativePollTimer?.cancel();
    _timer?.cancel();
    super.dispose();
  }

  String _formatDuration(Duration d) {
    String twoDigits(int n) => n.toString().padLeft(2, "0");
    return "${twoDigits(d.inMinutes)}:${twoDigits(d.inSeconds.remainder(60))}";
  }

  PhysicsMode _getPhysicsMode(String theme) {
     try {
       return PhysicsMode.values.firstWhere(
          (e) => e.toString().split('.').last.toLowerCase() == theme.toLowerCase()
       );
     } catch (_) {
       return PhysicsMode.gravityOrbs; 
     }
  }

  @override
  Widget build(BuildContext context) {
    // -----------------------------------------------------
    // PERSISTENT UI STACK (Single Scaffold)
    // -----------------------------------------------------
    return PopScope(
      canPop: false, 
      onPopInvoked: (didPop) async {
         if (didPop) return;
         if (_isVideoMode) {
             // In-App PiP (Floating Mode)
             CallOverlayService.instance.minimize(context);
             Navigator.pop(context); 
         } else {
              // AUDIO MODE: Just Return to Previous App Screen (Contact/Chat)
              Navigator.pop(context);
         }
      },
      child: Scaffold(
      backgroundColor: (_isVideoMode || _isPipMode) ? Colors.transparent : Colors.black, // TRANSPARENT for Pure Video
      body: Stack(
        children: [
            // LAYER 1: Physics Background (Audio Mode ONLY)
            if (!_isVideoMode && !_isPipMode)
               Positioned.fill(child: PhysicsBackground(mode: _getPhysicsMode(_currentTheme))),

            // LAYER 2: VIDEO SURFACE (Hybrid Mode)
            // Rendered directly in-app unless minimized
            if (_isVideoMode && CallOverlayService.instance.videoWidget != null)
                Positioned.fill(child: CallOverlayService.instance.videoWidget!),
            
            // LAYER 3: TOP INFO (Hidden in Video Mode)
            // This contains Avatar, Name, Timer, etc.
            if (!_isVideoMode && !_isPipMode)
               Positioned(
                 top: 0, left: 0, right: 0,
                 child: SafeArea( // Use SafeArea to avoid notch
                   child: SingleChildScrollView( // Allow scrolling only if needed
                     physics: const BouncingScrollPhysics(),
                     child: Padding(
                       padding: const EdgeInsets.only(top: 20, bottom: 100), // Bottom padding to avoid controls overlap
                       child: Column(
                         children: [
                            // RECORDING INDICATOR
                            if (_isRecording)
                                FadeTransition(
                                   opacity: _pulseController,
                                   child: Container(
                                     margin: const EdgeInsets.only(bottom: 24),
                                     padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
                                     decoration: BoxDecoration(
                                       color: Colors.redAccent.withOpacity(0.2),
                                       borderRadius: BorderRadius.circular(30),
                                       border: Border.all(color: Colors.redAccent, width: 1)
                                     ),
                                     child: Row(
                                       mainAxisSize: MainAxisSize.min,
                                       children: [
                                          const Icon(Icons.fiber_manual_record, color: Colors.red, size: 14),
                                          const SizedBox(width: 8),
                                          Text("SYSTEM RECORDING", style: GoogleFonts.orbitron(color: Colors.white, fontSize: 12, letterSpacing: 2))
                                       ],
                                     ),
                                   ),
                                ),

                             // HOLD INDICATOR
                             if (_isOnHold)
                                Container(
                                   margin: const EdgeInsets.only(bottom: 24),
                                   padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
                                   decoration: BoxDecoration(
                                     color: Colors.amber.withOpacity(0.2),
                                     borderRadius: BorderRadius.circular(30),
                                     border: Border.all(color: Colors.amber, width: 1)
                                   ),
                                   child: Row(
                                     mainAxisSize: MainAxisSize.min,
                                     children: [
                                        const Icon(Icons.pause, color: Colors.amber, size: 14),
                                        const SizedBox(width: 8),
                                        Text("CALL ON HOLD", style: GoogleFonts.orbitron(color: Colors.white, fontSize: 12, letterSpacing: 2))
                                     ],
                                   ),
                                 ),

                            _isConference 
                                ? _buildConferenceList() 
                                : _buildAvatarPulse(),
                            const SizedBox(height: 24),
                            
                            // Name / Status Transition
                            AnimatedSwitcher(
                              duration: const Duration(milliseconds: 500),
                              child: _isResolving 
                                  ? Column(
                                      key: const ValueKey('scanning'),
                                      children: [
                                        Text(
                                          _effectiveNumber,
                                          style: GoogleFonts.orbitron(fontSize: 28, color: Colors.white, fontWeight: FontWeight.bold),
                                        ),
                                        const SizedBox(height: 8),
                                        Row(
                                          mainAxisSize: MainAxisSize.min,
                                          children: [
                                            const SizedBox(width: 12, height: 12, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.cyanAccent)),
                                            const SizedBox(width: 8),
                                            Text("IDENTIFYING...", style: GoogleFonts.sourceCodePro(color: Colors.cyanAccent, letterSpacing: 2)),
                                          ],
                                        )
                                      ],
                                    )
                                  : Column(
                                      key: const ValueKey('resolved'),
                                      children: [
                                        Builder(
                                          builder: (context) {
                                             final bool hasLocal = _resolvedContact != null;
                                             final bool hasSystemName = widget.callerName.isNotEmpty && widget.callerName != "Unknown" && widget.callerName != _effectiveNumber;
                                             
                                             final String mainTitle = hasLocal 
                                                  ? _resolvedContact!.displayName 
                                                  : (hasSystemName ? widget.callerName : _effectiveNumber);
                                                  
                                             final String subTitle = hasLocal
                                                  ? _effectiveNumber
                                                  : (hasSystemName 
                                                      ? "Carrier Verified ID" 
                                                      : (_effectiveNumber == "Unknown" ? "Private Number" : "Unsaved Contact")
                                                    );

                                             return Column(
                                               children: [
                                                 Text(
                                                    mainTitle,
                                                    style: GoogleFonts.orbitron(fontSize: 32, color: Colors.white, fontWeight: FontWeight.bold),
                                                    textAlign: TextAlign.center,
                                                 ),
                                                 const SizedBox(height: 8),
                                                 Text(
                                                    subTitle,
                                                    style: GoogleFonts.sourceCodePro(fontSize: 18, color: Colors.white70),
                                                 )
                                               ]
                                             );
                                          }
                                        ),
                                      ],
                                    ),
                            ),

                            const SizedBox(height: 16),
                            Text(
                              widget.isIncoming 
                                  ? "INCOMING SIGNAL..." 
                                  : (_isOnHold ? "SIGNAL PAUSED" : _formatDuration(_callDuration)),
                              style: GoogleFonts.shareTechMono(
                                fontSize: 16, 
                                color: widget.isIncoming 
                                    ? Colors.cyanAccent 
                                    : (_isOnHold ? Colors.amber : Colors.greenAccent)
                              ),
                            ),
                          ],
                        ),
                      )
                   )
                 )
               ),

            // LAYER 4: CONTROLS (Always Visible on Top, Bottom Aligned)
            if (!_isPipMode)
              Positioned(
                  left: 0, right: 0, bottom: 0,
                  child: Container(
                    padding: EdgeInsets.only(
                       bottom: MediaQuery.of(context).padding.bottom + 20, 
                       left: 20, 
                       right: 20,
                       top: 40
                    ),
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: [
                           Colors.black.withOpacity(0.9), // Stronger scrim for visibility
                           Colors.transparent
                        ],
                        begin: Alignment.bottomCenter,
                        end: Alignment.topCenter,
                      )
                    ),
                    child: widget.isIncoming ? _buildIncomingControls() : _buildActiveControls(),
                  )
              ),
            
            // LAYER 5: BACK BUTTON (Always Visible, Top Left)
            if (!_isPipMode)
              Positioned(
                 top: MediaQuery.of(context).padding.top + 10, 
                 left: 10,
                 child: IconButton(
                   icon: const Icon(Icons.keyboard_arrow_down, color: Colors.white, size: 36), // White + Larger
                    onPressed: () {
                        if (_isVideoMode) {
                            CallOverlayService.instance.minimize(context);
                        }
                        Navigator.pop(context);
                    },
                 ),
              ),
    ],
      ),
    ));
  }

  Widget _buildConferenceList() {
      return Container(
          height: 300, 
          margin: const EdgeInsets.symmetric(horizontal: 20),
          decoration: BoxDecoration(
             color: Colors.white.withOpacity(0.05),
             borderRadius: BorderRadius.circular(24),
             border: Border.all(color: Colors.white.withOpacity(0.1))
          ),
          child: Column(
             children: [
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: Text(
                     "Conference Call (${_participants.length})",
                     style: GoogleFonts.outfit(color: Colors.cyanAccent, fontSize: 16, fontWeight: FontWeight.bold, letterSpacing: 1),
                  ),
                ),
                Expanded(
                   child: ListView.builder(
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      itemCount: _participants.length,
                      itemBuilder: (context, index) {
                          final p = _participants[index];
                          String name = p["name"] ?? "Unknown";
                          String number = p["number"] ?? "";
                          bool isActive = p["state"] == 4; // Active
                          
                          return Container(
                             margin: const EdgeInsets.only(bottom: 8),
                             padding: const EdgeInsets.all(12),
                             decoration: BoxDecoration(
                                color: Colors.white.withOpacity(0.05),
                                borderRadius: BorderRadius.circular(12)
                             ),
                             child: Row(
                                children: [
                                   CircleAvatar(
                                      backgroundColor: Colors.white.withOpacity(0.1),
                                      child: Icon(Icons.person, color: Colors.white70, size: 20),
                                   ),
                                   const SizedBox(width: 12),
                                   Expanded(
                                      child: Column(
                                         crossAxisAlignment: CrossAxisAlignment.start,
                                         children: [
                                            Text(name.isNotEmpty ? name : number, style: GoogleFonts.outfit(color: Colors.white, fontSize: 16)),
                                            if (name.isNotEmpty && number.isNotEmpty)
                                               Text(number, style: GoogleFonts.sourceCodePro(color: Colors.white54, fontSize: 12)),
                                         ],
                                      ),
                                   ),
                                   // Status Indicator
                                   Icon(
                                      isActive ? Icons.mic : Icons.pause,
                                      color: isActive ? Colors.greenAccent : Colors.amber,
                                      size: 16
                                   )
                                ],
                             ),
                          );
                      }
                   ),
                )
             ],
          ),
      );
  }

  Widget _buildAvatarPulse() {
    return AnimatedBuilder(
      animation: _pulseController,
      builder: (context, child) {
        return Stack(
          alignment: Alignment.center,
          children: [
             // 1. The Avatar
             Container(
               width: 150, height: 150,
               decoration: BoxDecoration(
                 shape: BoxShape.circle,
                 color: Colors.cyanAccent.withOpacity(0.1),
                 image: _avatarImage != null ? DecorationImage(image: _avatarImage!, fit: BoxFit.cover) : null,
                 boxShadow: [
                   BoxShadow(
                     color: (_isRecording 
                        ? Colors.redAccent 
                        : (_isOnHold 
                            ? Colors.amber 
                            : (widget.isIncoming ? Colors.greenAccent : Colors.cyanAccent)))
                         .withOpacity(0.2 * _pulseController.value),
                     blurRadius: 50 * _pulseController.value,
                     spreadRadius: 20 * _pulseController.value,
                   )
                 ]
               ),
               child: _avatarImage == null ? Center(
                 child: Icon(Icons.person, size: 64, color: Colors.white.withOpacity(0.8)),
               ) : null,
             ),
             
             // HOLD OVERLAY
             if (_isOnHold)
               Container(
                 width: 150, height: 150,
                 decoration: BoxDecoration(
                    color: Colors.black.withOpacity(0.6),
                    shape: BoxShape.circle,
                    border: Border.all(color: Colors.amber, width: 2)
                 ),
                 child: Center(
                    child: Icon(Icons.pause, color: Colors.amber, size: 64)
                 ),
               ),

             // 2. Recording Overlay (Microphone Animation)
             if (_isRecording)
               Container(
                  width: 150, height: 150,
                  decoration: BoxDecoration(
                    color: Colors.black.withOpacity(0.6),
                    shape: BoxShape.circle,
                  ),
                  child: Center(
                     child: Column(
                       mainAxisSize: MainAxisSize.min,
                       children: [
                          Icon(Icons.mic, color: Colors.redAccent.withOpacity(0.8 + (0.2 * _pulseController.value)), size: 48),
                          Text("REC", style: GoogleFonts.sourceCodePro(fontSize: 14, color: Colors.redAccent, fontWeight: FontWeight.bold)),
                       ]
                     )
                  ),
               )
          ],
        );
      },
    );
  }

  Widget _buildIncomingControls() {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        // PREMIUM MESSAGE BUTTON
        Padding(
          padding: const EdgeInsets.only(bottom: 50),
          child: PremiumMessageButton(onTap: () => _showMessageOptions(context)),
        ),

        // BI-DIRECTIONAL SLIDER
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 40),
          child: BiDirectionalCallSlider(
            onAnswer: () async {
                 try {
                    const platform = MethodChannel('com.neuralcitadel/native');
                    await platform.invokeMethod('answerCall');
                 } catch (_) {}
                 // Switch UI to Active
                 Navigator.pushReplacement(context, MaterialPageRoute(
                   builder: (_) => InCallScreen(
                     callerName: widget.callerName,
                     callerNumber: widget.callerNumber,
                     isIncoming: false, // Active
                   )
                 ));
            },
            onDecline: () async {
                 try {
                    const platform = MethodChannel('com.neuralcitadel/native');
                    await platform.invokeMethod('endCall');
                 } catch (_) {}
                 Navigator.pop(context);
            },
          ),
        )
      ],
    );
  }

  void _showMessageOptions(BuildContext context) {
      showModalBottomSheet(
         context: context,
         backgroundColor: Colors.transparent,
         isScrollControlled: true,
         builder: (ctx) => BackdropFilter(
           filter: ui.ImageFilter.blur(sigmaX: 20, sigmaY: 20),
           child: Container(
              decoration: BoxDecoration(
                 color: Colors.grey.shade900.withOpacity(0.8),
                 borderRadius: const BorderRadius.vertical(top: Radius.circular(32)),
                 border: Border.all(color: Colors.white.withOpacity(0.1))
              ),
              padding: const EdgeInsets.fromLTRB(24, 16, 24, 40),
              child: Column(
                 mainAxisSize: MainAxisSize.min,
                 crossAxisAlignment: CrossAxisAlignment.start,
                 children: [
                    Center(
                      child: Container(
                        width: 40, height: 4, 
                        decoration: BoxDecoration(color: Colors.white24, borderRadius: BorderRadius.circular(2))
                      )
                    ),
                    const SizedBox(height: 24),
                    Text("Reply with Message", style: GoogleFonts.outfit(color: Colors.white, fontSize: 20, fontWeight: FontWeight.w600)),
                    const SizedBox(height: 24),
                    
                    _buildGlassOption("Can't talk now. Call you later?"),
                    const SizedBox(height: 12),
                    _buildGlassOption("I'll be there in 10 mins."),
                    const SizedBox(height: 12),
                    _buildGlassOption("What's up?"),
                    const SizedBox(height: 12),
                    
                    GestureDetector( // CUSTOM MESSAGE
                      onTap: () {
                         Navigator.pop(ctx);
                         _launchSMS(""); 
                      },
                      child: Container(
                         padding: const EdgeInsets.all(20),
                         decoration: BoxDecoration(
                            color: Colors.white.withOpacity(0.08),
                            borderRadius: BorderRadius.circular(16),
                            border: Border.all(color: Colors.white.withOpacity(0.05))
                         ),
                         child: Row(
                            children: [
                               Icon(Icons.edit, color: Colors.blueAccent.shade100, size: 20),
                               const SizedBox(width: 16),
                               Text("Type a custom message...", style: GoogleFonts.outfit(color: Colors.white70, fontSize: 16)),
                            ],
                         ),
                      ),
                    )
                 ],
              ),
           ),
         )
      );
  }
  
  Widget _buildGlassOption(String text) {
     return GestureDetector(
        onTap: () {
            Navigator.pop(context);
            _launchSMS(text);
        },
        child: Container(
           width: double.infinity,
           padding: const EdgeInsets.all(20),
           decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.05),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: Colors.white.withOpacity(0.05))
           ),
           child: Text(text, style: GoogleFonts.outfit(color: Colors.white, fontSize: 16)),
        ),
     );
  }

  Future<void> _launchSMS(String body) async {
      // 1. Terminate Call (Reject with Message)
      try {
         const MethodChannel('com.neuralcitadel/native').invokeMethod('endCall');
      } catch (_) {};
      
      Navigator.pop(context); // Close Screen

      // 2. Launch SMS App
      final Uri smsLaunchUri = Uri(
        scheme: 'sms',
        path: widget.callerNumber,
        queryParameters: <String, String>{
          'body': body,
        },
      );
      
      if (await canLaunchUrl(smsLaunchUri)) {
          await launchUrl(smsLaunchUri);
      } else {
          if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Could not launch SMS app")));
      }
  }




  Widget _buildActiveControls() {
    return Column(
      mainAxisAlignment: MainAxisAlignment.end,
      children: [
        // 0. DYNAMIC SUGGESTION PILL (Restored)
        if (_showSuggestionPill) ...[
           SuggestionPill(
              isOnHold: _isOnHold, 
              onToggleHold: () {
                  setState(() => _isOnHold = !_isOnHold);
                  _invokeNative("toggleHold", {"active": _isOnHold});
              },
              onDismiss: () => setState(() => _showSuggestionPill = false),
           ),
           const SizedBox(height: 20),
        ],

        // 1. DYNAMIC CONTROL PANEL (Expands on "More")
        AnimatedContainer(
          duration: const Duration(milliseconds: 350),
          curve: Curves.easeOutBack,
          padding: const EdgeInsets.all(24),
          margin: const EdgeInsets.symmetric(horizontal: 20),
          decoration: BoxDecoration(
             color: Colors.black.withOpacity(0.5), // Darker for panel
             borderRadius: BorderRadius.circular(40),
             border: Border.all(color: Colors.white.withOpacity(0.15))
          ),
          child: _isMoreExpanded 
            ? _buildExpandedGrid()
            : Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                   // MUTE
                   _buildActiveActionBtn(
                      _isMuted ? CupertinoIcons.mic_off : CupertinoIcons.mic_fill, 
                      _isMuted ? "Unmute" : "Mute", 
                      () {
                        setState(() => _isMuted = !_isMuted);
                        _invokeNative("toggleMute", {"active": _isMuted});
                      }, 
                      isActive: _isMuted
                   ),

                   // KEYPAD
                   _buildActiveActionBtn(
                      CupertinoIcons.padlock, 
                      "Keypad", 
                      _showKeypad,
                      iconOverride: Icons.dialpad
                   ),

                   // SPEAKER (Smart Toggle)
                   _buildActiveActionBtn(
                      _getSpeakerIcon(), 
                      _getSpeakerLabel(), 
                      _handleSpeakerToggle, 
                      isActive: _audioRoute == ROUTE_SPEAKER || _audioRoute == ROUTE_BLUETOOTH,
                      activeColor: _audioRoute == ROUTE_BLUETOOTH ? Colors.white : Colors.white
                   ),

                   // FACETIME (VIDEO)
                   if (_isVideoMode)
                       _buildActiveActionBtn(
                          Icons.videocam_off, 
                          "FaceTime Off", 
                          () {
                              _invokeNative("downgradeToAudio");
                              setState(() => _isVideoMode = false);
                              CallOverlayService.instance.endCall();
                          }, 
                          isActive: true,
                          activeColor: Colors.white, 
                          activeIconColor: Colors.black 
                       )
                   else
                       _buildActiveActionBtn(
                          CupertinoIcons.video_camera, 
                          "FaceTime", 
                          () async {
                              if (await Permission.camera.request().isGranted) {
                                 setState(() => _isVideoMode = true);
                                 _invokeNative("upgradeToVideo");
                                 // Initialize Video Service
                                 CallOverlayService.instance.startCall(context);
                                 _invokeNative("enableProximity", {"enable": false});
                              }
                          }, 
                          isActive: false
                       ),
                ],
              ),
        ),
        
        const SizedBox(height: 30),

        // 2. BOTTOM CONTROLS (Stack for Perfect Centering)
        SizedBox(
           height: 80,
           width: double.infinity,
           child: Stack(
              alignment: Alignment.center,
              children: [
                 // LEFT: MORE BUTTON (Closer to End Call)
                 Positioned(
                    // Calculated: Center(0) - 36(half EndBtns) - 24(Gap) - 60(MoreBtn) = -120 from center
                    // Or simpler: Align in a Row with maintainSize
                    right: (MediaQuery.of(context).size.width / 2) + 50, // 36 + 14 gap
                    child: _buildLargeMoreButton(),
                 ),

                 // CENTER: END CALL (Red Circle)
                 GestureDetector(
                    onTap: () async {
                         if (_isEndingCall) return; 
                         if (mounted) setState(() => _isEndingCall = true);
                         HapticFeedback.heavyImpact();
                         try {
                            const platform = MethodChannel('com.neuralcitadel/native');
                            await platform.invokeMethod('endCall', {'force': true}); 
                         } catch (e) {}
                         if (mounted) Navigator.of(context).popUntil((route) => route.isFirst); 
                    },
                    child: Container(
                       width: 72, height: 72,
                       decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: Colors.redAccent.shade400,
                          boxShadow: [
                             BoxShadow(color: Colors.redAccent.withOpacity(0.4), blurRadius: 20, spreadRadius: 4)
                          ]
                       ),
                       child: _isEndingCall 
                          ? const Center(child: CircularProgressIndicator(color: Colors.white))
                          : const Icon(CupertinoIcons.phone_down_fill, color: Colors.white, size: 36),
                    ),
                 ),
              ],
           ),
        ),
        const SizedBox(height: 50),
      ],
    );
  }

  // Expanded Grid for Control Panel
  Widget _buildExpandedGrid() {
      // 4 Columns Grid (Including Primary Actions)
      return Column(
         mainAxisSize: MainAxisSize.min,
         children: [
            // ROW 1: PRIMARY ACTIONS (Mute, Keypad, Speaker, Video)
            // ROW 1: PRIMARY ACTIONS (Standard - Always Visible)
            Row(
               mainAxisAlignment: MainAxisAlignment.spaceAround,
               children: [
                   _buildActiveActionBtn(
                      _isMuted ? CupertinoIcons.mic_off : CupertinoIcons.mic_fill, 
                      _isMuted ? "Unmute" : "Mute", 
                      () {
                        setState(() => _isMuted = !_isMuted);
                        _invokeNative("toggleMute", {"active": _isMuted});
                      }, 
                      isActive: _isMuted
                   ),
                   _buildActiveActionBtn(
                      CupertinoIcons.padlock, 
                      "Keypad", 
                      _showKeypad,
                      iconOverride: Icons.dialpad
                   ),
                   _buildActiveActionBtn(
                      _getSpeakerIcon(), 
                      _getSpeakerLabel(), 
                      _handleSpeakerToggle, 
                      isActive: _audioRoute == ROUTE_SPEAKER || _audioRoute == ROUTE_BLUETOOTH,
                      activeColor: _audioRoute == ROUTE_BLUETOOTH ? Colors.white : Colors.white
                   ),
                   if (_isVideoMode)
                       _buildActiveActionBtn(
                          Icons.videocam_off, 
                          "FaceTime Off", 
                          () {
                              _invokeNative("downgradeToAudio");
                              setState(() {
                                  _isVideoMode = false;
                                  _isCameraPaused = false; // Reset state
                              });
                              CallOverlayService.instance.endCall();
                          }, 
                          isActive: true,
                          activeColor: Colors.redAccent, 
                          activeIconColor: Colors.white 
                       )
                   else
                       _buildActiveActionBtn(
                          CupertinoIcons.video_camera, 
                          "FaceTime", 
                          () async {
                              if (await Permission.camera.request().isGranted) {
                                 setState(() => _isVideoMode = true);
                                 _invokeNative("upgradeToVideo");
                                 CallOverlayService.instance.startCall(context);
                                 _invokeNative("enableProximity", {"enable": false});
                              }
                          }, 
                          isActive: false
                       ),
               ],
            ),
            const SizedBox(height: 20),
            
            // ROW 2: SECONDARY ACTIONS (Hold, Add, Merge, Rec)
            Row(
               mainAxisAlignment: MainAxisAlignment.spaceAround,
               children: [
                   _buildActiveActionBtn(
                      _isOnHold ? Icons.play_arrow : Icons.pause, 
                      _isOnHold ? "Resume" : "Hold", 
                      () {
                         setState(() => _isOnHold = !_isOnHold);
                         _invokeNative("toggleHold", {"active": _isOnHold});
                      }, 
                      isActive: _isOnHold,
                      activeColor: Colors.amber
                   ),
                   // SWAP / ADD CALL
                   if (_backgroundCall != null)
                       _buildActiveActionBtn(
                           Icons.swap_calls, 
                           "Swap", 
                           () => _invokeNative("swapCalls"), 
                           isActive: false
                       )
                   else
                       _buildActiveActionBtn(Icons.person_add, "Add Call", () => _invokeNative("addCall"), isActive: false, iconOverride: Icons.person_add),

                   _buildActiveActionBtn(Icons.merge_type, "Merge", () => _invokeNative("mergeCalls"), isActive: false),
                   _buildActiveActionBtn(
                      Icons.fiber_manual_record, 
                      _isRecording ? "Stop Rec" : "Record", 
                      () {
                         setState(() => _isRecording = !_isRecording);
                         _invokeNative("toggleRecording", {"active": _isRecording});
                      }, 
                      isActive: _isRecording, 
                      activeColor: Colors.redAccent
                   ),
               ],
            ),
            
            const SizedBox(height: 20),

            // ROW 3: VIDEO CONTROLS + NOTES (Unified Row)
            Row(
               mainAxisAlignment: MainAxisAlignment.spaceAround,
               children: [
                   if (_isVideoMode) ...[
                       // 1. SWITCH CAMERA
                       _buildActiveActionBtn(
                          Icons.flip_camera_ios_rounded, 
                          "Switch Cam", 
                          () => _invokeNative("switchCamera"),
                          isActive: false 
                       ),

                       // 2. PAUSE CAMERA (Local Privacy)
                       _buildActiveActionBtn(
                          _isCameraPaused ? Icons.videocam_off : Icons.videocam, 
                          _isCameraPaused ? "Resume Cam" : "Pause Cam", 
                          () {
                              setState(() => _isCameraPaused = !_isCameraPaused);
                              if (_isCameraPaused) {
                                  _invokeNative("pauseCamera");
                                  _invokeNative("setPipMode", {"active": true}); // Force PIP update
                              } else {
                                  _invokeNative("resumeCamera");
                                  _invokeNative("setPipMode", {"active": false}); // Force PIP update
                              }
                          }, 
                          isActive: _isCameraPaused,
                          activeColor: Colors.white,
                          activeIconColor: Colors.black
                       ),
                   ],
                   
                   // NOTES (Always Visible)
                   _buildActiveActionBtn(Icons.edit_note, "Notes", () => _showNotePad(), isActive: false),
                   
                   // FILLER if needed for alignment (e.g. if not video mode, centered)
                   if (!_isVideoMode) 
                      const SizedBox(width: 40), // Balance the Notes 
               ],
            ),
         ],
      );
  }

  // Large Squircle More Button
  Widget _buildLargeMoreButton() {
     return GestureDetector(
        onTap: () {
           HapticFeedback.mediumImpact();
           setState(() => _isMoreExpanded = !_isMoreExpanded);
        },
        child: AnimatedContainer(
           duration: const Duration(milliseconds: 200),
           width: 60, height: 60, // Matches visual weight of End Call
           decoration: BoxDecoration(
              color: _isMoreExpanded ? Colors.white : Colors.white.withOpacity(0.1),
              borderRadius: BorderRadius.circular(20), // Squircle
              border: Border.all(color: Colors.white.withOpacity(0.1))
           ),
           child: Icon(
              _isMoreExpanded ? Icons.close : Icons.grid_view_rounded, // Grid icon for "More"
              color: _isMoreExpanded ? Colors.black : Colors.white, 
              size: 28
           ),
        ),
     );
  }

  // Renamed helper to avoid conflict with incoming action btn
  Widget _buildActiveActionBtn(IconData icon, String label, VoidCallback onTap, {bool isActive = false, Color? activeColor, Color? activeIconColor, IconData? iconOverride}) {
    return GestureDetector(
      onTap: () {
         HapticFeedback.lightImpact();
         onTap();
      },
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            padding: const EdgeInsets.all(14), // Compact padding
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: isActive ? (activeColor ?? Colors.white) : Colors.white.withOpacity(0.1), 
              border: Border.all(color: isActive ? Colors.transparent : Colors.white.withOpacity(0.1)) // Subtle border
            ),
            child: Icon(
               iconOverride ?? icon, 
               color: isActive ? Colors.black : Colors.white, 
               size: 24 // Smaller icon
            ),
          ),
          const SizedBox(height: 6),
          Text(label, style: GoogleFonts.outfit(color: Colors.white70, fontSize: 11, fontWeight: FontWeight.w500)),
        ],
      ),
    );
  }

  void _showMoreOptions() async {
    final result = await showModalBottomSheet<String>(
       context: context,
       backgroundColor: Colors.transparent,
       builder: (ctx) => BackdropFilter(
         filter: ui.ImageFilter.blur(sigmaX: 20, sigmaY: 20),
         child: Container(
            decoration: BoxDecoration(
               color: const Color(0xFF1C1C1E).withOpacity(0.9), // iOS Dark Grey
               borderRadius: const BorderRadius.vertical(top: Radius.circular(32)),
               border: Border.all(color: Colors.white.withOpacity(0.1))
            ),
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
            child: Column(
               mainAxisSize: MainAxisSize.min,
               children: [
                  Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.white24, borderRadius: BorderRadius.circular(2))),
                  const SizedBox(height: 32),
                  
                  // GRID OF SECONDARY ACTIONS
                  Wrap(
                    spacing: 32, runSpacing: 32,
                    alignment: WrapAlignment.center,
                    children: [
                       _buildSecondaryAction(Icons.person_add, "Add Call", () { 
                           Navigator.pop(ctx, "addCall"); 
                       }),
                       _buildSecondaryAction(Icons.fiber_manual_record, _isRecording ? "Stop Rec" : "Record", () {
                          Navigator.pop(ctx);
                          setState(() => _isRecording = !_isRecording);
                          _invokeNative("toggleRecording", {"active": _isRecording});
                       }, color: _isRecording ? Colors.redAccent : null),
                       _buildSecondaryAction(Icons.merge_type, "Merge", () { 
                          Navigator.pop(ctx); 
                          _invokeNative("mergeCalls"); 
                       }),
                       _buildSecondaryAction(Icons.edit_note, "Notes", () { 
                          Navigator.pop(ctx); 
                          _showNotePad(); 
                       }),
                       if (_isVideoMode)
                           _buildSecondaryAction(Icons.cameraswitch, "Flip Cam", () {
                               Navigator.pop(ctx);
                               int targetId = CallOverlayService.instance.videoId ?? 0;
                               MethodChannel("neural_video_view_$targetId").invokeMethod("switchCamera");
                           }),
                    ],
                  ),
                  const SizedBox(height: 40),
               ],
            ),
         ),
       )
    );

    if (result == "addCall") {
        if (_isVideoMode) {
            CallOverlayService.instance.minimize(context);
        }
        
        // Force the root Navigator to drop the InCallScreen Overlay.
        // We do NOT use 'canPop' here because in_call_screen is pushed via main.dart's 
        // global navigatorKey, which sometimes misreports canPop as false.
        Navigator.of(context, rootNavigator: true).pop();
    }
  }

  Widget _buildSecondaryAction(IconData icon, String label, VoidCallback onTap, {Color? color}) {
     return GestureDetector(
        onTap: () {
           HapticFeedback.mediumImpact();
           onTap();
        },
        child: Column(
           mainAxisSize: MainAxisSize.min,
           children: [
              Container(
                 width: 60, height: 60,
                 decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.08),
                    shape: BoxShape.circle,
                 ),
                 child: Icon(icon, color: color ?? Colors.white, size: 26),
              ),
              const SizedBox(height: 8),
              Text(label, style: GoogleFonts.outfit(color: Colors.white, fontSize: 13))
           ],
        ),
     );
  }

  void _showKeypad() {
    showModalBottomSheet(
      context: context, 
      isScrollControlled: true,
      backgroundColor: Colors.transparent, 
      builder: (_) => StatefulBuilder(
        builder: (context, setSheetState) {
          return BackdropFilter(
            filter: ui.ImageFilter.blur(sigmaX: 16, sigmaY: 16),
            child: Container(
              height: MediaQuery.of(context).size.height * 0.5, // 50% Height Constraint
              padding: const EdgeInsets.only(bottom: 20),
              decoration: BoxDecoration(
                  color: Colors.black.withOpacity(0.85), 
                  borderRadius: const BorderRadius.vertical(top: Radius.circular(32)),
                  border: Border.all(color: Colors.white.withOpacity(0.08))
              ),
              child: Column(
                children: [
                   const SizedBox(height: 12),
                   Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.white24, borderRadius: BorderRadius.circular(2))),
                   
                   // DTMF Display (Compact)
                   Expanded(
                     flex: 1,
                     child: Center(
                        child: Text(
                          _dtmfString.isEmpty ? "..." : _dtmfString,
                          style: GoogleFonts.outfit(fontSize: 40, color: Colors.white, fontWeight: FontWeight.w300),
                          textAlign: TextAlign.center,
                        ),
                     ),
                   ),

                   // Keypad Grid
                   Expanded(
                     flex: 4,
                     child: Column(
                       mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                       children: [
                          ["1", "2", "3"],
                          ["4", "5", "6"],
                          ["7", "8", "9"],
                          ["*", "0", "#"]
                       ].map((row) => Row(
                           mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                           children: row.map((key) => GestureDetector(
                              onTap: () {
                                 setSheetState(() => _dtmfString += key);
                                 // IMPORTANT: Do NOT call setState() on parent to avoid "saved on outside screen" confusion
                                 // unless you want the display elsewhere updated. 
                                 // The user complained about it being "saved on outside", so let's keep it local to sheet if possible,
                                 // BUT _dtmfString is a class member. Let's just update the sheet state primarily.
                                 HapticFeedback.lightImpact();
                                 _invokeNative("sendDtmf", {"key": key});
                              },
                              child: Container(
                                width: 64, height: 64, // Smaller keys for 50% height
                                alignment: Alignment.center,
                                decoration: BoxDecoration(
                                   color: Colors.white.withOpacity(0.06), 
                                   shape: BoxShape.circle,
                                   border: Border.all(color: Colors.white.withOpacity(0.05))
                                ),
                                child: Text(key, style: GoogleFonts.outfit(fontSize: 24, color: Colors.white, fontWeight: FontWeight.w400)),
                              ),
                           )).toList(),
                       )).toList(),
                     ),
                   ),

                   // Action Buttons
                   if (_dtmfString.isNotEmpty)
                      Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                            children: [
                                // NATIVE CONTACT
                                IconButton(
                                   icon: const Icon(Icons.person_add_alt_1, color: Colors.greenAccent),
                                   onPressed: () {
                                      Navigator.push(
                                        context, 
                                        MaterialPageRoute(
                                          builder: (_) => EditContactScreen(
                                            contact: null, 
                                            contactService: _contactService, // Use class member
                                            initialNumber: _dtmfString
                                          )
                                        )
                                      );
                                      // Navigator.pop(context); // Optional: Keep keypad open or close? User might want to return.
                                      // Usually, we close the keypad.
                                   },
                                   tooltip: "Create Contact",
                                ),

                                // SHORTCUT (Existing)
                                IconButton(
                                   icon: const Icon(Icons.add_to_home_screen, color: Colors.blueAccent),
                                   onPressed: () {
                                      _invokeNative("createDirectCallShortcut", {"number": _dtmfString, "name": "New Contact"});
                                      Navigator.pop(context);
                                      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Shortcut Created!")));
                                   },
                                   tooltip: "Pin Shortcut",
                                ),
                                
                                // BACKSPACE
                                IconButton(
                                   icon: const Icon(Icons.backspace_outlined, color: Colors.white70),
                                   onPressed: () {
                                      setSheetState(() {
                                         if (_dtmfString.isNotEmpty) {
                                             _dtmfString = _dtmfString.substring(0, _dtmfString.length - 1);
                                         }
                                      });
                                   },
                                )
                            ],
                          )
                      ),
                ],
              ),
            ),
          );
        }
      )
    ).whenComplete(() {
        // Clear DTMF on close if that's what "saved on outside screen" meant?
        // Or maybe just leave it. The user said "number is getting saved on the outside screen".
        // This implies they see the number persisted on the main screen (which isn't implemented here, 
        // so maybe they meant the *keypad* state persists?). 
        // I will clear it on close to be safe.
        setState(() => _dtmfString = ""); 
    });
  }
  
  String _dtmfString = "";
  
  // --- Audio Route Logic ---

  IconData _getSpeakerIcon() {
      if (_audioRoute == ROUTE_BLUETOOTH) return Icons.bluetooth_audio;
      if (_audioRoute == ROUTE_WIRED_HEADSET) return Icons.headset;
      if (_audioRoute == ROUTE_SPEAKER) return CupertinoIcons.speaker_3_fill;
      return CupertinoIcons.speaker_2; // Earpiece
  }

  String _getSpeakerLabel() {
      if (_audioRoute == ROUTE_BLUETOOTH) {
          if (_activeBluetoothDevice != null && _activeBluetoothDevice!["name"] != null) {
              String name = _activeBluetoothDevice!["name"];
              if (name.length > 10) return "${name.substring(0, 8)}...";
              return name;
          }
          return "Bluetooth";
      }
      if (_audioRoute == ROUTE_WIRED_HEADSET) return "Headset";
      if (_audioRoute == ROUTE_SPEAKER) return "Speaker";
      return "Receiver";
  }

  void _handleSpeakerToggle() {
      bool hasBluetooth = (_supportedAudioRoutes & ROUTE_BLUETOOTH) != 0;
      bool hasWired = (_supportedAudioRoutes & ROUTE_WIRED_HEADSET) != 0;

      if (hasBluetooth || hasWired) {
          _showAudioRoutePicker();
      } else {
          // Simple Toggle (Speaker <-> Earpiece)
          int newRoute = (_audioRoute == ROUTE_SPEAKER) ? ROUTE_EARPIECE : ROUTE_SPEAKER;
          _invokeNative("setAudioRoute", {"route": newRoute});
      }
  }

  void _showAudioRoutePicker() {
      showModalBottomSheet(
          context: context,
          backgroundColor: Colors.transparent,
          builder: (context) => Container(
              decoration: BoxDecoration(
                  color: const Color(0xFF1E1E1E).withOpacity(0.95),
                  borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
                  border: Border.all(color: Colors.white10)
              ),
              child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                      const SizedBox(height: 10),
                      Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.white24, borderRadius: BorderRadius.circular(2))),
                      const SizedBox(height: 20),
                      Text("Audio Output", style: GoogleFonts.outfit(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w600)),
                      const SizedBox(height: 20),
                      
                      if ((_supportedAudioRoutes & ROUTE_EARPIECE) != 0)
                          _buildRouteOption("Receiver", CupertinoIcons.phone, ROUTE_EARPIECE),
                      if ((_supportedAudioRoutes & ROUTE_SPEAKER) != 0)
                          _buildRouteOption("Speaker", CupertinoIcons.speaker_3_fill, ROUTE_SPEAKER),
                      if ((_supportedAudioRoutes & ROUTE_WIRED_HEADSET) != 0)
                          _buildRouteOption("Headset", Icons.headset, ROUTE_WIRED_HEADSET),
                      
                      // DYNAMIC BLUETOOTH LIST
                      for (var d in _supportedBluetoothDevices)
                          _buildBtOption(d["name"] ?? "Bluetooth Device", d["address"]),

                      // Fallback if BT supported but list empty
                      if ((_supportedAudioRoutes & ROUTE_BLUETOOTH) != 0 && _supportedBluetoothDevices.isEmpty)
                          _buildRouteOption("Bluetooth", Icons.bluetooth_audio, ROUTE_BLUETOOTH),

                      const SizedBox(height: 30),
                  ],
              ),
          )
      );
  }

  Widget _buildRouteOption(String label, IconData icon, int route) {
      bool isSelected = _audioRoute == route && (_audioRoute != ROUTE_BLUETOOTH || _activeBluetoothDevice == null); 
      return ListTile(
          leading: Icon(icon, color: isSelected ? Colors.white : Colors.white70),
          title: Text(label, style: GoogleFonts.outfit(color: Colors.white, fontWeight: isSelected ? FontWeight.w600 : FontWeight.w400)),
          trailing: isSelected ? const Icon(Icons.check, color: Colors.white) : null,
          onTap: () {
              Navigator.pop(context);
              _invokeNative("setAudioRoute", {"route": route});
          },
      );
  }

  Widget _buildBtOption(String label, String address) {
      bool isSelected = _audioRoute == ROUTE_BLUETOOTH && _activeBluetoothDevice?["address"] == address;
      return ListTile(
          leading: Icon(Icons.bluetooth_audio, color: isSelected ? Colors.white : Colors.blueAccent),
          title: Text(label, style: GoogleFonts.outfit(color: Colors.white, fontWeight: isSelected ? FontWeight.w600 : FontWeight.w400)),
          trailing: isSelected ? const Icon(Icons.check, color: Colors.blueAccent) : null,
          onTap: () {
              Navigator.pop(context);
              _invokeNative("setBluetoothAudioRoute", {"address": address});
          },
      );
  }



  Future<void> _invokeNative(String method, [Map<String, dynamic>? args]) async {
      try {
        const platform = MethodChannel('com.neuralcitadel/native');
        await platform.invokeMethod(method, args);
      } catch (e) {}
  }

  void _showNotePad() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      barrierColor: Colors.black.withOpacity(0.8),
      builder: (context) => NoteSheet(
        number: _effectiveNumber, 
        onNativeInvoke: (method, args) => _invokeNative(method, args)
      )
    );
  }

  Widget _buildCircleBtn(IconData icon, Color color, VoidCallback onTap, {double size = 64, bool isLoading = false}) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: size, height: size,
        decoration: BoxDecoration(shape: BoxShape.circle, color: color),
        child: isLoading 
            ? const Padding(padding: EdgeInsets.all(16), child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
            : Icon(icon, color: Colors.white, size: 32),
      ),
    );
  }
}



// ============================================================================
// BI-DIRECTIONAL CALL SLIDER (PREMIUM SHIMMER)
// ============================================================================
class BiDirectionalCallSlider extends StatefulWidget {
  final VoidCallback onAnswer;
  final VoidCallback onDecline;

  const BiDirectionalCallSlider({
    super.key, 
    required this.onAnswer,
    required this.onDecline,
  });

  @override
  State<BiDirectionalCallSlider> createState() => _BiDirectionalCallSliderState();
}

class _BiDirectionalCallSliderState extends State<BiDirectionalCallSlider> with TickerProviderStateMixin {
  double _dragValue = 0.0; // -1.0 (Left) to 1.0 (Right)
  double _dragPixels = 0.0; 
  double _maxWidth = 0.0;
  
  late AnimationController _shimmerController;
  late AnimationController _pulseController;

  bool get _isAnswering => _dragValue > 0.1;
  bool get _isDeclining => _dragValue < -0.1;


  @override
  void initState() {
    super.initState();
    _shimmerController = AnimationController(vsync: this, duration: const Duration(milliseconds: 3500))..repeat(); // Slower Typewriter Scan
    _pulseController = AnimationController(vsync: this, duration: const Duration(milliseconds: 1500))..repeat(reverse: true);
  }
  
  @override
  void dispose() {
    _shimmerController.dispose();
    _pulseController.dispose();
    super.dispose();
  }

  void _handleDragUpdate(DragUpdateDetails details, double limit) {
    setState(() {
      _dragPixels += details.delta.dx;
      _dragPixels = _dragPixels.clamp(-limit, limit);
      _dragValue = _dragPixels / limit;
    });
    
    // Light haptics for "texture"
    if (_dragPixels.abs() % 10 < 1) {
       HapticFeedback.selectionClick();
    }
  }

  void _handleDragEnd(double limit) {
    if (_dragValue > 0.5) { 
       // ANSWER SNAP
       setState(() => _dragPixels = limit);
       HapticFeedback.heavyImpact();
       widget.onAnswer();
    } else if (_dragValue < -0.5) {
       // DECLINE SNAP
       setState(() => _dragPixels = -limit);
       HapticFeedback.heavyImpact();
       widget.onDecline();
    } else {
       // RESET SNAP
       setState(() {
          _dragPixels = 0.0;
          _dragValue = 0.0;
       });
    }
  }

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        // RESPONSIVE SIZING
        final totalWidth = constraints.maxWidth; 
        final double sliderHeight = 88.0; // Reverted Height
        final double knobSize = 78.0; // Smaller Knob
        final double trackPadding = 5.0; // Balanced Padding
        final double limit = (totalWidth / 2) - (knobSize / 2) - trackPadding;
        
        _maxWidth = limit;

        // Opacity & Color Logic
        final double rightDrag = _dragValue.clamp(0.0, 1.0);
        final double leftDrag = _dragValue.clamp(-1.0, 0.0).abs();
        
        // Dynamic Track Color
        Color trackColor = Colors.grey.shade900.withOpacity(0.4); // Darker base for contrast
        if (_isAnswering) trackColor = Colors.green.withOpacity((0.2 + rightDrag * 0.6).clamp(0.0, 0.9));
        if (_isDeclining) trackColor = Colors.red.withOpacity((0.2 + leftDrag * 0.6).clamp(0.0, 0.9));

        return Center(
          child: SizedBox(
            width: totalWidth,
            height: sliderHeight,
            child: Stack(
              alignment: Alignment.center,
              children: [
                 // 1. GLASS TRACK
                 ClipRRect(
                    borderRadius: BorderRadius.circular(sliderHeight / 2),
                    child: BackdropFilter(
                      filter: ui.ImageFilter.blur(sigmaX: 15, sigmaY: 15),
                      child: AnimatedContainer(
                        duration: const Duration(milliseconds: 100),
                        decoration: BoxDecoration(
                           color: trackColor,
                           borderRadius: BorderRadius.circular(sliderHeight / 2),
                           border: Border.all(color: Colors.white.withOpacity(0.12), width: 1),
                        ),
                      ),
                    ),
                 ),
                 
                 // 2. TEXT & ICONS (Below Knob)
                 Padding(
                   padding: const EdgeInsets.symmetric(horizontal: 24),
                   child: Row(
                     mainAxisAlignment: MainAxisAlignment.spaceBetween,
                     children: [
                        // LEFT SIDE (Decline)
                        GestureDetector(
                          onTap: () {
                             HapticFeedback.mediumImpact();
                             widget.onDecline(); // TAP ACTION
                          },
                          child: AnimatedOpacity(
                             duration: const Duration(milliseconds: 200),
                             opacity: _isAnswering ? 0.0 : 1.0, // Hide if answering
                             child: Row(
                               children: [
                                  Icon(Icons.call_end, color: Colors.redAccent.shade100, size: 28),
                                  const SizedBox(width: 8),
                                  // Hide text if knob matches
                                  if (leftDrag < 0.2)
                                    TypewriterText(
                                      text: "Decline",
                                      controller: _shimmerController,
                                      baseColor: Colors.white38, // Faded Base
                                      highlightColor: Colors.white,
                                      style: GoogleFonts.outfit(fontSize: 16, fontWeight: FontWeight.w500, letterSpacing: 2.0),
                                    )
                               ],
                             ),
                          ),
                        ),

                        // RIGHT SIDE (Answer)
                        GestureDetector(
                          onTap: () {
                             HapticFeedback.mediumImpact();
                             widget.onAnswer(); // TAP ACTION
                          },
                          child: AnimatedOpacity(
                             duration: const Duration(milliseconds: 200),
                             opacity: _isDeclining ? 0.0 : 1.0, // Hide if declining
                             child: Row(
                               children: [
                                  // Hide text if knob matches
                                  if (rightDrag < 0.2)
                                    TypewriterText(
                                      text: "Answer",
                                      controller: _shimmerController,
                                      baseColor: Colors.white38, // Faded Base
                                      highlightColor: Colors.white,
                                      style: GoogleFonts.outfit(fontSize: 16, fontWeight: FontWeight.w500, letterSpacing: 2.0),
                                    ),
                                  const SizedBox(width: 8),
                                  Icon(Icons.call, color: Colors.greenAccent.shade100, size: 28),
                               ],
                             ),
                          ),
                        ),
                     ],
                   ),
                 ),

                 // 3. KNOB (White Circle)
                 Transform.translate(
                   offset: Offset(_dragPixels, 0),
                   child: GestureDetector(
                      onHorizontalDragUpdate: (d) => _handleDragUpdate(d, limit),
                      onHorizontalDragEnd: (d) => _handleDragEnd(limit),
                      child: Container(
                         width: knobSize, height: knobSize,
                         decoration: BoxDecoration(
                           shape: BoxShape.circle,
                           color: Colors.white,
                           boxShadow: [
                             BoxShadow(
                               color: Colors.black.withOpacity(0.3),
                               blurRadius: 15, spreadRadius: 2, offset: const Offset(0, 4)
                             )
                           ]
                         ),
                         child: Icon(
                            _isDeclining ? Icons.call_end : Icons.call, 
                            color: _isDeclining ? Colors.red : (_isAnswering ? Colors.green : Colors.black),
                            size: 38,
                         ),
                      ),
                   ),
                 )
              ],
            ),
          ),
        );
      }
    );
  }
}

// PREMIUM TYPEWRITER WIDGET (Character-by-Character Glow)
class TypewriterText extends StatelessWidget {
  final String text;
  final TextStyle? style;
  final AnimationController? controller;
  final Color baseColor;
  final Color highlightColor;

  const TypewriterText({
    super.key, 
    required this.text, 
    this.controller, 
    this.style,
    this.baseColor = Colors.white38, // Visible Base
    this.highlightColor = Colors.white,
  });

  @override
  Widget build(BuildContext context) {
    if (controller == null) return Text(text, style: style?.copyWith(color: baseColor));

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: List.generate(text.length, (index) {
        return AnimatedBuilder(
          animation: controller!,
          builder: (context, child) {
             // 0.0 -> 1.0 (Controller)
             // We want the wave to traverse the full length.
             // Spread factor controls how many chars are lit.
             
             final double total = text.length.toDouble();
             final double percent = index / total;
             
             // Travel from -0.2 to 1.2 to ensure full entry/exit
             final double travel = -0.2 + (1.4 * controller!.value);
             
             final double dist = (travel - percent).abs();
             
             // Gaussian-ish falloff
             // If dist is 0 (exact match), opacity is 1.0
             // If dist is large, opacity is baseOpacity (0.0 added to base)
             
             final double glow = (1.0 - (dist * 5.0)).clamp(0.0, 1.0); // 5.0 makes it tight
             
             // Final Color Interpolation
             final Color color = Color.lerp(baseColor, highlightColor, glow)!;
             
             // Slightly scale up the active character
             final double scale = 1.0 + (0.1 * glow);

             return Transform.scale(
               scale: scale,
               child: Text(text[index], style: style?.copyWith(color: color)),
             );
          },
        );
      }),
    );
  }
}

// PREMIUM MESSAGE BUTTON (GLASS + SHIMMER)
// ============================================================================
class PremiumMessageButton extends StatefulWidget {
  final VoidCallback onTap;
  const PremiumMessageButton({super.key, required this.onTap});

  @override
  State<PremiumMessageButton> createState() => _PremiumMessageButtonState();
}

class _PremiumMessageButtonState extends State<PremiumMessageButton> with SingleTickerProviderStateMixin {
  late AnimationController _shimmerCtrl;

  @override
  void initState() {
    super.initState();
    _shimmerCtrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 3000))..repeat(); 
  }

  @override
  void dispose() {
    _shimmerCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () {
         HapticFeedback.mediumImpact();
         widget.onTap();
      },
      child: ClipRRect(
        borderRadius: BorderRadius.circular(30),
        child: BackdropFilter(
          filter: ui.ImageFilter.blur(sigmaX: 20, sigmaY: 20), // Heavy Blur
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
            decoration: BoxDecoration(
               gradient: LinearGradient( 
                 colors: [Colors.white.withOpacity(0.12), Colors.white.withOpacity(0.05)],
                 begin: Alignment.topLeft,
                 end: Alignment.bottomRight,
               ),
               borderRadius: BorderRadius.circular(30),
               border: Border.all(color: Colors.white.withOpacity(0.2))
            ),
            child: Row(
               mainAxisSize: MainAxisSize.min,
               children: [
                  Icon(Icons.message_outlined, color: Colors.white.withOpacity(0.9), size: 20),
                  const SizedBox(width: 12),
                  TypewriterText( // Swapped Widget
                     text: "Reply with Message", 
                     controller: _shimmerCtrl,
                     baseColor: Colors.white38, // Visible but dimmed
                     highlightColor: Colors.white,
                     style: GoogleFonts.outfit(fontSize: 15, fontWeight: FontWeight.w500, letterSpacing: 1.0), // Spaced out
                  )
               ],
            ),
          ),
        ),
      ),
    );
  }
} // Closes _PremiumMessageButtonState

// DYNAMIC SUGGESTION PILL (HOLD/RESUME)
// ============================================================================
class SuggestionPill extends StatefulWidget {
  final bool isOnHold;
  final VoidCallback onToggleHold;
  final VoidCallback onDismiss;

  const SuggestionPill({
    super.key,
    required this.isOnHold,
    required this.onToggleHold,
    required this.onDismiss,
  });

  @override
  State<SuggestionPill> createState() => _SuggestionPillState();
}

class _SuggestionPillState extends State<SuggestionPill> with SingleTickerProviderStateMixin {
  late AnimationController _glowController;

  @override
  void initState() {
    super.initState();
    _glowController = AnimationController(vsync: this, duration: const Duration(seconds: 4))..repeat();
  }

  @override
  void dispose() {
    _glowController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () {
         HapticFeedback.mediumImpact();
         widget.onToggleHold();
      },
      child: ClipRRect(
        borderRadius: BorderRadius.circular(40),
        child: BackdropFilter(
          filter: ui.ImageFilter.blur(sigmaX: 15, sigmaY: 15),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
            decoration: BoxDecoration(
               color: widget.isOnHold ? Colors.amber.withOpacity(0.2) : Colors.white.withOpacity(0.1),
               borderRadius: BorderRadius.circular(40),
               border: Border.all(color: Colors.white.withOpacity(0.15))
            ),
            child: Row(
               mainAxisSize: MainAxisSize.min,
               children: [
                  Icon(
                    widget.isOnHold ? Icons.play_arrow : Icons.pause, 
                    color: widget.isOnHold ? Colors.amber : Colors.white70, 
                    size: 20
                  ),
                  const SizedBox(width: 12),
                  TypewriterText(
                     text: widget.isOnHold ? "Call on Hold (Tap to Resume)" : "Hold This Call?", 
                     controller: _glowController,
                     baseColor: Colors.white60,
                     highlightColor: Colors.white,
                     style: GoogleFonts.outfit(fontSize: 14, fontWeight: FontWeight.w500),
                  ),
                  const SizedBox(width: 12),
                  
                  // CLOSE BUTTON
                  GestureDetector(
                    onTap: () {
                       HapticFeedback.lightImpact();
                       widget.onDismiss();
                    },
                    child: Container(
                       padding: const EdgeInsets.all(4),
                       decoration: BoxDecoration(color: Colors.white10, shape: BoxShape.circle),
                       child: const Icon(Icons.close, size: 14, color: Colors.white54),
                    ),
                  )
               ],
            ),
          ),
        ),
      ),
    );
  }
}
