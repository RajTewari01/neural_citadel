import 'dart:async';
import 'dart:ui';
import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:speech_to_text/speech_to_text.dart';
import 'package:flutter_tts/flutter_tts.dart';

class SmartCameraScreen extends StatefulWidget {
  static bool isCameraActive = false; // Track strict state
  final bool autoCapture;
  const SmartCameraScreen({super.key, this.autoCapture = false});

  @override
  State<SmartCameraScreen> createState() => _SmartCameraScreenState();
}

class _SmartCameraScreenState extends State<SmartCameraScreen> with SingleTickerProviderStateMixin {
  CameraController? _controller;
  List<CameraDescription> _cameras = [];
  bool _isInitialized = false;
  final FlutterTts _tts = FlutterTts();
  final SpeechToText _stt = SpeechToText();
  
  // UI State
  bool _isNeuralFilterActive = false;
  late AnimationController _shutterController;
  late Animation<double> _shutterAnimation;

  @override
  void initState() {
    super.initState();
    SmartCameraScreen.isCameraActive = true;
    _initCamera();
    
    _shutterController = AnimationController(vsync: this, duration: const Duration(milliseconds: 200));
    _shutterAnimation = Tween<double>(begin: 1.0, end: 0.8).animate(
      CurvedAnimation(parent: _shutterController, curve: Curves.easeInOut)
    );
  }

  Future<void> _initCamera() async {
    try {
      _cameras = await availableCameras();
      final frontCam = _cameras.firstWhere(
        (c) => c.lensDirection == CameraLensDirection.front,
        orElse: () => _cameras.first,
      );

      _controller = CameraController(
        frontCam,
        ResolutionPreset.high,
        enableAudio: false,
      );

      await _controller!.initialize();
      await _stt.initialize();
      
      if (!mounted) return;
      setState(() => _isInitialized = true);

      // Start voice loop
      _startVoiceControlLoop();
      
      if (widget.autoCapture) {
         await _tts.speak("Camera ready.");
      }

    } catch (e) {
      debugPrint("Camera error: $e");
    }
  }

  Future<void> _startVoiceControlLoop() async {
    if (!mounted || _stt.isListening) return;
    
    try {
      await _stt.listen(
        onResult: (result) async {
          final words = result.recognizedWords.toLowerCase();
          
          if (words.contains('cheese') || words.contains('photo') || words.contains('capture')) {
             if (!_controller!.value.isTakingPicture) {
                await _takePicture();
             }
          }
           // Exit Word
          else if (words.contains('done') || words.contains('close')) {
            await _tts.speak("Closing.");
            if (mounted) Navigator.pop(context);
          }
        },
        listenFor: const Duration(seconds: 30),
        pauseFor: const Duration(milliseconds: 500),
        partialResults: true,
        cancelOnError: false,
        listenMode: ListenMode.dictation, 
      );
    } catch (_) {}
    
    // Infinite Loop
    if (mounted) {
       Future.delayed(const Duration(milliseconds: 1000), () {
         if (mounted && !_stt.isListening) _startVoiceControlLoop();
       });
    }
  }

  Future<void> _takePicture() async {
    if (_controller == null || !_controller!.value.isInitialized) return;
    
    try {
      // Animate Shutter
      await _shutterController.forward();
      await _shutterController.reverse();
      
      final image = await _controller!.takePicture();
      
      // Flash Effect
      if (mounted) {
          showGeneralDialog(
            context: context,
            pageBuilder: (_,__,___) => Container(color: Colors.white),
            transitionDuration: const Duration(milliseconds: 100),
            transitionBuilder: (ctx, anim, _, child) => Opacity(opacity: 1.0 - anim.value, child: child),
          );
      }
      
      await _tts.speak("Nice shot!");
    } catch (e) {
      debugPrint("Capture error: $e");
    }
  }

  @override
  void dispose() {
    SmartCameraScreen.isCameraActive = false;
    _stt.cancel();
    _controller?.dispose();
    _shutterController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!_isInitialized) return const Scaffold(backgroundColor: Colors.black);

    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        fit: StackFit.expand,
        children: [
          // 1. Camera Feed
          CameraPreview(_controller!),
          
          // 2. Neural Filter Overlay
          if (_isNeuralFilterActive)
            ColorFiltered(
              colorFilter: const ColorFilter.mode(Colors.cyanAccent, BlendMode.overlay),
              child: CameraPreview(_controller!),
            ),

          // 3. UI Controls
          Column(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              // TOP BAR (Glass)
              Container(
                padding: const EdgeInsets.symmetric(vertical: 40, horizontal: 20),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: [Colors.black.withOpacity(0.6), Colors.transparent],
                  )
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    IconButton(
                      icon: const Icon(Icons.close, color: Colors.white), 
                      onPressed: () => Navigator.pop(context)
                    ),
                    Text("NEURAL LENS", style: GoogleFonts.orbitron(color: Colors.white, letterSpacing: 2, fontWeight: FontWeight.bold)),
                    IconButton(
                      icon: Icon(Icons.auto_fix_high, color: _isNeuralFilterActive ? Colors.cyanAccent : Colors.white),
                      onPressed: () => setState(() => _isNeuralFilterActive = !_isNeuralFilterActive),
                    ),
                  ],
                ),
              ),

              // BOTTOM CONTROL BAR (Glass)
              ClipRRect(
                child: BackdropFilter(
                  filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
                  child: Container(
                    height: 180,
                    padding: const EdgeInsets.only(bottom: 20),
                    decoration: BoxDecoration(
                      color: Colors.black.withOpacity(0.3),
                      border: const Border(top: BorderSide(color: Colors.white10)),
                    ),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                         Text(
                           'Say "Cheese" to Capture', 
                           style: GoogleFonts.shareTechMono(color: Colors.white54, fontSize: 12)
                         ),
                         const SizedBox(height: 20),
                         Row(
                           mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                           children: [
                             // Gallery Preview
                             Container(
                               width: 50, height: 50,
                               decoration: BoxDecoration(
                                 color: Colors.white10,
                                 borderRadius: BorderRadius.circular(8),
                                 border: Border.all(color: Colors.white24)
                               ),
                             ),
                             
                             // Shutter Button
                             ScaleTransition(
                               scale: _shutterAnimation,
                               child: GestureDetector(
                                 onTap: _takePicture,
                                 child: Container(
                                   width: 80, height: 80,
                                   decoration: BoxDecoration(
                                     shape: BoxShape.circle,
                                     border: Border.all(color: Colors.white, width: 4),
                                     color: Colors.white24,
                                   ),
                                   child: Container(
                                     margin: const EdgeInsets.all(4),
                                     decoration: const BoxDecoration(
                                       color: Colors.white,
                                       shape: BoxShape.circle,
                                     ),
                                   ),
                                 ),
                               ),
                             ),
                             
                             // Flip Camera
                             IconButton(
                               icon: const Icon(Icons.flip_camera_ios, color: Colors.white, size: 30),
                               onPressed: () {}, 
                             ),
                           ],
                         ),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
