import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:flutter_overlay_window/flutter_overlay_window.dart';
import 'package:flutter_background_service/flutter_background_service.dart';
import 'theme/app_theme.dart';
import 'screens/launch_screen.dart'; 
import 'screens/auth/login_screen.dart';
import 'services/theme_provider.dart';
import 'services/api_service.dart';
import 'services/auth_service.dart';
import 'utils/shake_detector.dart';
import 'package:screenshot/screenshot.dart';
import 'screens/support/bug_report_dialog.dart';
import 'dart:io';
import 'package:path_provider/path_provider.dart';
import 'services/pulse_service.dart';
import 'services/voice_commander.dart';
import 'services/visual_cortex_service.dart';
import 'utils/call_lock.dart';
import 'widgets/neural_pulse_overlay.dart';
import 'screens/phone/in_call_screen.dart';
import 'package:permission_handler/permission_handler.dart';
import 'services/contact_service.dart';

// Proxy global key to VoiceCommander to ensure single context source
final GlobalKey<NavigatorState> navigatorKey = VoiceCommander.navigatorKey;
bool isCallScreenVisible = false;

Future<void> startOutgoingCall(String number, String name) async {
  if (isCallScreenVisible) return;
  isCallScreenVisible = true;

  // Optimistic UI Push
  VoiceCommander.navigatorKey.currentState?.push(
    MaterialPageRoute(builder: (_) => InCallScreen(
       isIncoming: false, 
       callerName: name, 
       callerNumber: number
    ))
  ).then((_) => isCallScreenVisible = false);

  // Native Trigger
  const platform = MethodChannel('com.neuralcitadel/native');
  try {
     await platform.invokeMethod('placeCall', {"number": number});
  } catch (e) {
     print("Call Failed: $e");
  }
}

Future<void> initializeService() async {
  final service = FlutterBackgroundService();
  await service.configure(
    androidConfiguration: AndroidConfiguration(
      onStart: onStart,
      autoStart: true,
      isForegroundMode: false,
    ),
    iosConfiguration: IosConfiguration(
        autoStart: false,
        onForeground: onStart,
        onBackground: onIosBackground
    ),
  );
}

@pragma('vm:entry-point')
void onStart(ServiceInstance service) {
}

@pragma('vm:entry-point')
Future<bool> onIosBackground(ServiceInstance service) async {
  return true;
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp();
  await initializeService();
  runApp(const NeuralCitadelApp());
}

// ... 

// Overlay Entry Point (runs in separate isolate when app is backgrounded)
@pragma("vm:entry-point")
void overlayMain() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const MaterialApp(
    debugShowCheckedModeBanner: false,
    home: NeuralPulseOverlay(),
  ));
}

class NeuralCitadelApp extends StatefulWidget {
  const NeuralCitadelApp({super.key});

  // Navigation Observer
  static final RouteObserver<ModalRoute<void>> routeObserver = RouteObserver<ModalRoute<void>>();

  @override
  State<NeuralCitadelApp> createState() => _NeuralCitadelAppState();
}

class _NeuralCitadelAppState extends State<NeuralCitadelApp> with WidgetsBindingObserver {
  final ScreenshotController _screenshotController = ScreenshotController();
  ShakeDetector? _detector;
  
  // Call State Lock (Prevents Ghost Screens)
  static String? _lastCallNumber;
  static DateTime? _lastCallTime;
  
  // Call Check Lock
  static bool _isCheckingCall = false;
  
  // Persistence Cache (Prevents "Unknown" flash on Resume)
  static Map<String, dynamic>? _cachedCallData;



  @override
  void initState() {
    super.initState();
    CallLock.isActive = false; // Reset on Launch
    _isCheckingCall = false;
    WidgetsBinding.instance.addObserver(this); // Add Observer
    _detector = ShakeDetector.autoStart(onPhoneShake: _handleShake);
    _requestCriticalPermissions();
    _checkDefaultDialer();
    PulseService().initPhoneListener();
    _checkNativeCall(); // FAST CHECK ON LAUNCH
  }
  
  Future<void> _checkDefaultDialer() async {
     try {
       const platform = MethodChannel('com.neuralcitadel/native');
       await platform.invokeMethod('setDefaultDialer');
     } catch (e) {
       print("Failed to request default dialer: $e");
     }
  }

  Future<void> _requestCriticalPermissions() async {
     // Requesting broad permissions to ensure compatibility across Android versions
     final statuses = await [
       Permission.phone,
       Permission.contacts,
       Permission.microphone,
       Permission.bluetoothConnect, // Android 12+
       Permission.storage, // Android < 13
       Permission.audio,   // Android 13+ (Music/Audio)
     ].request();
     
     print("⚠️ Permissions Result: $statuses");
     
     if (statuses[Permission.storage]!.isDenied && statuses[Permission.audio]!.isDenied) {
        print("CRITICAL: Storage permission denied. Recording will not save.");
     }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this); // Remove Observer
    _detector?.stopListening();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
       // Trigger Sync Check when coming to foreground
       ApiService().checkHealth();
       
       // Check for Active Call (Field Authority Loop)
       _checkNativeCall();
    }
  }

  Future<void> _checkNativeCall() async {
    print("CORE: Native Check Start. Lock: ${CallLock.isActive} | Checking: $_isCheckingCall");
    if (_isCheckingCall) return; 
    _isCheckingCall = true;

    try {
      const platform = MethodChannel('com.neuralcitadel/native');
      
      // ZERO LATENCY - NO POLLING
      // Indian Telecom CNAP data comes with the call signal. We read it instantly.
      
      // 1. Safety Check
      if (CallLock.isActive) {
           print("CORE: Aborted - Screen became active.");
           return;
      }

      final dynamic result = await platform.invokeMethod('checkActiveCall');
      
      // 1. Native Guard
      if (result == null) return;
      
      // 2. Debug Log
      print("RAW NATIVE RESULT: $result");

      bool isIncoming = result["isIncoming"] == true;
      String rawNumber = result["number"] as String? ?? "Unknown";
      String rawName = result["name"] as String? ?? ""; 
      String? debugInfo = result["debug"] as String?;

      // 3. Strict Dart Guard
      if ((rawNumber.trim() == "Unknown" || rawNumber.trim().isEmpty || rawNumber == "null") && rawName.trim().isEmpty) {
           print("⛔ CORE: Ghost Call Blocked by Dart Filter.");
           return;
      }

      String number = rawNumber;
      String name = rawName;

      if (result != null && result is Map) {
          // CACHE LOGIC
          if (number != "Unknown") {
             // We have good data. Update Cache.
             _cachedCallData = {
                "name": name,
                "number": number,
                "isIncoming": isIncoming,
                "timestamp": DateTime.now()
             };
          } else {
             // We have bad data. Can we recover?
             // Only recover if we are actively in a session (time check)
             if (_cachedCallData != null) {
                 final lastTime = _cachedCallData!["timestamp"] as DateTime;
                 if (DateTime.now().difference(lastTime) < const Duration(minutes: 10)) {
                     print("✨ RESTORED FROM CACHE: ${_cachedCallData!['name']}");
                     number = _cachedCallData!["number"];
                     name = _cachedCallData!["name"];
                     // Use cached details to prevent "Unknown" flash
                 } else {
                     number = rawNumber; 
                 }
             } else {
                number = rawNumber;
             }
          }
      }

      // Check Ghost/Duplicate (Only if we have a valid number to compare)
      if (number != "Unknown" && _lastCallNumber == number && 
          DateTime.now().difference(_lastCallTime ?? DateTime.now()) < const Duration(seconds: 5)) {
             print("CORE: Ignored duplicate call $number");
             return;
      }
      
      print("🚀 INSTANT LAUNCH: $name | $number");
      _pushCallScreen(name, number, isIncoming, debugInfo);

    } catch (e) {
      print("Native Call Check Error: $e");
    } finally {
       _isCheckingCall = false; // Release Lock
    }
  }
  
  void _pushCallScreen(String name, String number, bool isIncoming, String? debugInfo) {
     if (isCallScreenVisible) {
        print("CORE: Screen already visible. Skipping push.");
        return;
     }
     
     print("✅ Pushing Call Screen");
     isCallScreenVisible = true;

     navigatorKey.currentState?.push(
       PageRouteBuilder(
         pageBuilder: (context, animation, secondaryAnimation) => InCallScreen(
           isIncoming: isIncoming, 
           callerName: name, 
           callerNumber: number,
           debugInfo: debugInfo,
         ),
         transitionsBuilder: (context, animation, secondaryAnimation, child) {
           return FadeTransition(opacity: animation, child: child);
         },
         transitionDuration: const Duration(milliseconds: 300),
       )
     ).then((_) {
        print("CORE: Call Screen Popped");
        isCallScreenVisible = false;
        _checkNativeCall(); // Re-check on pop
     });
  }

  void _handleShake() async {
    // Capture Screenshot
    try {
      final directory = (await getApplicationDocumentsDirectory()).path;
      final imagePath = await _screenshotController.captureAndSave(
          directory, 
          fileName: "bug_report_${DateTime.now().millisecondsSinceEpoch}.png"
      );

      if (imagePath != null && mounted) {
        // Show Dialog
        VoiceCommander.navigatorKey.currentState?.push(
          MaterialPageRoute(builder: (_) => BugReportDialog(screenshot: File(imagePath))),
        );
      }
    } catch (e) {
      print("Shake Error: $e");
    }
  }

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        Provider<ApiService>(create: (_) => ApiService()),
        ChangeNotifierProvider<AuthService>(create: (_) => AuthService()..init()),
        ChangeNotifierProvider<PulseService>(create: (_) => PulseService()),
        ChangeNotifierProvider<VisualCortexService>(create: (_) => VisualCortexService()..init()),
        ChangeNotifierProvider<ContactService>(create: (_) => ContactService()..init()),
      ],
      child: AnimatedBuilder(
        animation: themeProvider,
        builder: (context, _) {
          return Screenshot(
            controller: _screenshotController,
            child: MaterialApp(
              navigatorKey: VoiceCommander.navigatorKey,
              navigatorObservers: [NeuralCitadelApp.routeObserver],
              title: 'Neural Citadel',
              theme: AppTheme.lightRedTheme,
              darkTheme: AppTheme.cyberpunkRed,
              themeMode: themeProvider.themeMode,
              home: const LaunchScreen(), 
              debugShowCheckedModeBanner: false,
            ),
          );
        }
      ),
    );
  }
}


