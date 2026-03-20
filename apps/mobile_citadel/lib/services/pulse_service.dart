import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_overlay_window/flutter_overlay_window.dart';
import 'package:provider/provider.dart';
import 'package:phone_state/phone_state.dart';


enum PulseState {
  idle,       // Small Pill
  listening,  // Waveform
  processing, // Spinner
  success,    // Wide notification
  error       // Shake red
}

class PulseService extends ChangeNotifier with WidgetsBindingObserver {
  static final PulseService _instance = PulseService._internal();
  factory PulseService() => _instance;
  
  PulseService._internal() {
    WidgetsBinding.instance.addObserver(this);
    _checkOverlayPermission();
  }
  PhoneStateStatus _callStatus = PhoneStateStatus.NOTHING;
  
  void initPhoneListener() {
    // Legacy phone_state listener as fallback
    PhoneState.stream.listen((event) {
      if (event.status != null) {
        _handlePhoneStateChange(event.status!);
      }
    });

    // NATIVE HIGH-FIDELITY CALL EVENT STREAM
    const EventChannel('com.neuralcitadel/callStateStream')
        .receiveBroadcastStream()
        .listen((dynamic event) {
      if (event is Map) {
         _handleNativeCallState(event);
      }
    });

    // OVERLAY ACTIONS LISTENER
    FlutterOverlayWindow.overlayListener.listen((data) {
      if (data is Map && data.containsKey('action')) {
         final action = data['action'];
         if (action == 'answer_call') {
            const MethodChannel("com.neuralcitadel/native").invokeMethod("answerCall");
         } else if (action == 'end_call') {
            const MethodChannel("com.neuralcitadel/native").invokeMethod("endCall");
         } else if (action == 'toggle_speaker') {
            _isSpeakerOn = !_isSpeakerOn;
            const MethodChannel("com.neuralcitadel/native").invokeMethod("toggleSpeaker", {"active": _isSpeakerOn});
         }
      }
    });
  }

  void _handleNativeCallState(Map dynamicEvent) {
      if (dynamicEvent['event'] == 'state_sync') {
          final data = dynamicEvent['data'];
          if (data is Map && data['activeCall'] != null) {
              var activeCall = data['activeCall'];
              if (activeCall is Map) {
                  int state = activeCall['state'] ?? 0;
                  String number = (activeCall['number']?.toString().trim().isNotEmpty == true) ? activeCall['number'].toString().trim() : "Unknown";
                  String name = activeCall['name']?.toString().trim() ?? "";
                  String display = name.isNotEmpty ? name : number;
                  
                  // Map Android Call states: 1=DIALING, 2=RINGING, 3=HOLDING, 4=ACTIVE, 7=DISCONNECTED, 8=SELECT, 9=CONNECTING
                  if (state == 2) { 
                      bool wasNotCall = _activeMode != "call";
                      _activeMode = "call"; // Mode 'call' for full Call UI in Island
                      _message = display;
                      _activeCallNumber = number;
                      _isActiveCall = false;
                      _isIncomingCall = true;
                      forceShowOverlay();
                      if (wasNotCall) {
                          FlutterOverlayWindow.resizeOverlay(WindowSize.matchParent, 160, false);
                          _sendStateToOverlay(forceExpand: true);
                      } else {
                          _sendStateToOverlay();
                      }
                  } else if (state == 1 || state == 4 || state == 3 || state == 8 || state == 9) { 
                      bool wasNotCall = _activeMode != "call";
                      _activeMode = "call";
                      _message = display;
                      _activeCallNumber = number;
                      _isActiveCall = (state == 4 || state == 3);
                      _isIncomingCall = false;
                      forceShowOverlay();
                      if (wasNotCall) {
                          FlutterOverlayWindow.resizeOverlay(WindowSize.matchParent, 160, false); 
                          _sendStateToOverlay(forceExpand: true);
                      } else {
                          _sendStateToOverlay();
                      }
                  } else if (state == 7) { 
                      _activeMode = "idle";
                      setSuccess("Call Ended");
                      Future.delayed(const Duration(seconds: 2), () {
                          resizeOverlay(60);
                          setIdle();
                      });
                  }
              }
          } else if (data is Map && data['activeCall'] == null) {
               _activeMode = "idle";
               setSuccess("Call Ended");
               Future.delayed(const Duration(seconds: 2), () {
                   resizeOverlay(60);
                   setIdle();
               });
          }
      } else if (dynamicEvent['event'] == 'incoming_call') {
          final data = dynamicEvent['data'];
          if (data is Map) {
              String number = (data['number']?.toString().trim().isNotEmpty == true) ? data['number'].toString().trim() : "Unknown";
              String name = data['name']?.toString().trim() ?? "";
              String display = name.isNotEmpty ? name : number;
              
              bool wasNotCall = _activeMode != "call";
              _activeMode = "call";
              _message = display;
              _activeCallNumber = number;
              _isActiveCall = false;
              _isIncomingCall = true;
              forceShowOverlay();
              if (wasNotCall) {
                  FlutterOverlayWindow.resizeOverlay(WindowSize.matchParent, 160, false);
                  _sendStateToOverlay(forceExpand: true);
              } else {
                  _sendStateToOverlay();
              }
          }
      }
  }

  void _handlePhoneStateChange(PhoneStateStatus status) {
    _callStatus = status;
    debugPrint("Phone State Changed: \$status");

    switch (status) {
      case PhoneStateStatus.CALL_INCOMING:
        _activeMode = "call";
        forceShowOverlay();
        FlutterOverlayWindow.resizeOverlay(WindowSize.matchParent, 160, false);
        break;
        
      case PhoneStateStatus.CALL_STARTED:
        _activeMode = "call";
        forceShowOverlay(); 
        FlutterOverlayWindow.resizeOverlay(WindowSize.matchParent, 160, false); 
        break;
        
      case PhoneStateStatus.CALL_ENDED:
        _activeMode = "idle";
        setSuccess("Call Ended");
        Future.delayed(const Duration(seconds: 2), () {
            resizeOverlay(60); // Reset to pill size
            setIdle();
        });
        break;
        
      case PhoneStateStatus.CALL_OUTGOING:
      default:
        if (_activeMode.startsWith("call")) {
           setIdle();
        }
        break;
    }
  }

  // Exposed for UI layer to trigger expansion
  Future<void> expandToFullScreenCall() async {
     await FlutterOverlayWindow.resizeOverlay(WindowSize.matchParent, WindowSize.matchParent, true); 
     _sendStateToOverlay();
  }

  // ... existing methods ...


  OverlayEntry? _overlayEntry;
  PulseState _state = PulseState.idle;
  String _message = "";
  bool _isSpeakerOn = false;
  String _activeCallNumber = "";
  bool _isActiveCall = false;
  bool _isIncomingCall = false;
  
  // Calibration
  double _topOffset = 0; 
  double _leftOffset = 0;
  
  PulseState get state => _state;
  String get message => _message;
  double get topOffset => _topOffset;
  double get leftOffset => _leftOffset;

  void setOffsets(double top, double left) {
    _topOffset = top;
    _leftOffset = left;
    notifyListeners();
    _sendStateToOverlay(); // Re-send instantly to update UI
  }

  void setTopOffset(double offset) => setOffsets(offset, _leftOffset); // Legacy wrapper

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  Future<void> _checkOverlayPermission() async {
    bool granted = await FlutterOverlayWindow.isPermissionGranted();
    if (!granted) {
      await FlutterOverlayWindow.requestPermission();
    }
  }

  bool _isForeground = true; 
  bool _isAutoWakeEnabled = false; // LOGIC FIX: Track user preference

  // SYNC WITH VOICE COMMANDER
  void setAutoWakeState(bool enabled) {
    _isAutoWakeEnabled = enabled;
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.detached) {
      _isForeground = false;
      FlutterOverlayWindow.closeOverlay();
    } else if (state == AppLifecycleState.paused || state == AppLifecycleState.inactive || state.name == 'hidden') {
      _isForeground = false;
      // LOGIC FIX: Show if Voice is enabled OR if we are in an ACTIVE CALL
      if (_isAutoWakeEnabled || _activeMode == "call") {
         _showBackgroundOverlay().then((_) {
             if (_activeMode == "call") {
                 FlutterOverlayWindow.resizeOverlay(WindowSize.matchParent, 160, false);
                 _sendStateToOverlay(); // Resync just in case
             }
         });
      }
    } else if (state == AppLifecycleState.resumed) {
      _isForeground = true;
      FlutterOverlayWindow.closeOverlay(); // NUCLEAR: Force close when app is open
      _sendStateToOverlay(); 
    }
  }

  // Force close overlay - Robust
  Future<void> forceHideOverlay() async {
    debugPrint("Force Hiding Overlay...");
    await FlutterOverlayWindow.closeOverlay();
    _state = PulseState.idle;
    notifyListeners();
  }

  /// Force show overlay - useful when voice is activated
  Future<void> forceShowOverlay() async {
    bool granted = await FlutterOverlayWindow.isPermissionGranted();
    if (!granted) {
      granted = await FlutterOverlayWindow.requestPermission() ?? false;
    }
    if (granted) {
      await _showBackgroundOverlay();
    }
  }

  Future<void> _showBackgroundOverlay() async {
    // STRICT GUARD: If foreground, don't double show (unless debugging)
    if (_isForeground) return;

    bool granted = await FlutterOverlayWindow.isPermissionGranted();
    if (!granted) return;

    // Check if overlay is already showing
    bool isActive = await FlutterOverlayWindow.isActive();
    if (isActive) {
      _sendStateToOverlay();
      return;
    }

    await FlutterOverlayWindow.showOverlay(
      height: 250, // CRITICAL FIX: Only cover top area so background apps work!
      width: WindowSize.matchParent,
      alignment: OverlayAlignment.topCenter,
      flag: OverlayFlag.defaultFlag, // Touchable
      visibility: NotificationVisibility.visibilityPublic, 
      overlayTitle: "Neural Citadel",
      overlayContent: "Voice Assistant Active",
      enableDrag: false,
      startPosition: const OverlayPosition(0, 0), 
    );
    
    // Update overlay with current state
    _sendStateToOverlay();
  }

  // CALIBRATION & UX
  bool _isCalibrating = false;

  void setCalibrationMode(bool active) {
    if (_activeMode == "calibration" && !active) {
       _activeMode = "idle";
       setIdle();
    }
    
    _isCalibrating = active;
    if (active) {
       // Force show overlay GREEN
       _activeMode = "calibration";
       _state = PulseState.idle; 
       _isForeground = false; // Bypass foreground check
       forceShowOverlay();
    } else {
       if (!_isAutoWakeEnabled) forceHideOverlay(); // Only hide if auto-wake is OFF
    }
    _sendStateToOverlay();
  }

  String _stateToString() {
    if (_isCalibrating) return "Positioning...";
    
    switch (_state) {
      case PulseState.idle: return "Neural"; 
      case PulseState.listening: return "Listening...";
      case PulseState.processing: return "Processing...";
      case PulseState.success: return _message;
      case PulseState.error: return "Error";
    }
  }

  // --- State Setters ---
  String _activeMode = "idle"; // idle, calibration, call, media

  void setIdle() {
    _state = PulseState.idle;
    _message = "";
    notifyListeners();
    _sendStateToOverlay();
    // AUTO HIDE if Voice Auto-Wake is OFF and we are not in the app
    if (!_isForeground && !_isAutoWakeEnabled && _activeMode != "call") {
        forceHideOverlay();
    }
  }

  void setListening() {
    _state = PulseState.listening;
    notifyListeners();
    forceShowOverlay(); // Show overlay when voice is active
  }

  void setProcessing() {
    _state = PulseState.processing;
    notifyListeners();
    _sendStateToOverlay();
  }

  void setSuccess(String msg) {
    _state = PulseState.success;
    _message = msg;
    notifyListeners();
    // Default mode is idle/success unless specified
    _sendStateToOverlay(mode: "success");
    
    Future.delayed(const Duration(seconds: 4), () {
      if (_state == PulseState.success) setIdle();
    });
  }

  void _sendStateToOverlay({String? mode, bool? forceExpand}) {
    FlutterOverlayWindow.shareData({
      'status': _message.isEmpty ? _stateToString() : _message,
      'number': _activeCallNumber,
      'isCallActive': _isActiveCall,
      'isIncomingCall': _isIncomingCall,
      'listening': _state == PulseState.listening,
      'mode': mode ?? _activeMode,
      'topOffset': _topOffset,
      'leftOffset': _leftOffset,
      if (forceExpand != null) 'forceExpand': forceExpand,
    });
  }

  // DYNAMIC RESIZING (The Holy Grail)
  Future<void> resizeOverlay(int height) async {
    try {
      if (await FlutterOverlayWindow.isActive()) {
        await FlutterOverlayWindow.resizeOverlay(WindowSize.matchParent, height, false);
      }
    } catch (_) {}
  }

  void setError() {
    _state = PulseState.error;
    notifyListeners();
    _sendStateToOverlay();
    
    Future.delayed(const Duration(seconds: 2), () {
      if (_state == PulseState.error) setIdle();
    });
  }
}
