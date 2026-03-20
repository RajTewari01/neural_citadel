import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../widgets/draggable_video_overlay.dart';

class CallOverlayService {
  static final CallOverlayService instance = CallOverlayService._();
  CallOverlayService._();

  OverlayEntry? _overlayEntry;
  VideoOverlayMode _mode = VideoOverlayMode.hidden;
  int? _activeVideoId;
  
  // The Persistent Widget (We keep valid reference to avoid recreation)
  Widget? _videoWidget;

  // Callback to restore UI
  Function(BuildContext)? _restoreCallback;

  void setRestoreCallback(Function(BuildContext) callback) {
    _restoreCallback = callback;
  }

  void startCall(BuildContext context) {
    if (_overlayEntry != null) return; // Already Active

    // 1. Create the persistent video widget
    _videoWidget = const AndroidView(
        viewType: 'neural_video_view',
        onPlatformViewCreated: _onPlatformViewCreated,
    );

    // 2. Create Overlay Entry
    _overlayEntry = OverlayEntry(builder: (context) {
       return DraggableVideoOverlay(
           videoView: _videoWidget!,
           mode: _mode,
           onMaximize: () => maximize(context),
       );
    });

    // 3. Do NOT insert Overlay yet. 
    // In "Internal Mode", the InCallScreen will render the _videoWidget directly.
    // We only use Overlay for "Floating Mode" (PiP).
    
    // 4. Default to Hidden (Managed by InCallScreen)
    _mode = VideoOverlayMode.hidden;
  }

  static void _onPlatformViewCreated(int id) {
     print("📹 Global Video Overlay Created: $id");
     instance._activeVideoId = id;
     MethodChannel("neural_video_view_$id").invokeMethod("initialize");
  }

  void minimize(BuildContext context) {
     print("📉 Minimizing to Floating PiP");
     _mode = VideoOverlayMode.floating;
     
     // Create Entry if needed (We are leaving InCallScreen)
     if (_overlayEntry == null) {
         _overlayEntry = OverlayEntry(builder: (context) {
             return DraggableVideoOverlay(
                 videoView: _videoWidget!,
                 mode: _mode,
                 onMaximize: () => maximize(context),
             );
         });
         Overlay.of(context).insert(_overlayEntry!);
     } else {
         _overlayEntry!.markNeedsBuild();
     }
    
    // Notify Native to Hide Local View (Tiny Mode)
    if (_activeVideoId != null) {
         MethodChannel("neural_video_view_$_activeVideoId").invokeMethod("setPipMode", {"active": true});
    }
  }

  void maximize(BuildContext context) {
    if (_overlayEntry == null) return;
    print("📈 Maximizing to Full Screen");
    _mode = VideoOverlayMode.hidden; // Hidden in Overlay, shown in Screen
    
    // Remove Overlay (Transfer back to Screen)
    _overlayEntry?.remove();
    _overlayEntry = null;

    // Notify Native to Show Full Local View
    if (_activeVideoId != null) {
         MethodChannel("neural_video_view_$_activeVideoId").invokeMethod("setPipMode", {"active": false});
    }

    // Restore the Controller UI (InCallScreen) using the callback or Navigator
    if (_restoreCallback != null) {
        _restoreCallback!(context);
    }
  }

  void endCall() {
    print("❌ Ending Call Overlay");
    _overlayEntry?.remove();
    _overlayEntry = null;
    _videoWidget = null;
    _mode = VideoOverlayMode.hidden;
    _activeVideoId = null;
  }

  bool get isActive => _videoWidget != null; // Active if widget exists
  Widget? get videoWidget => _videoWidget;
  
  // Expose Native ID for other controllers
  int? get videoId => _activeVideoId;
}
