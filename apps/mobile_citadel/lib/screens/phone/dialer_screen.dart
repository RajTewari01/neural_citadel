import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'dart:async';
import 'dart:ui' as ui;
import 'package:flutter/services.dart';
import '../../ui/physics/physics_background.dart';
import '../../services/physics_manager.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../services/contact_service.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:flutter_phone_direct_caller/flutter_phone_direct_caller.dart';
import 'package:permission_handler/permission_handler.dart';
import 'tabs/keypad_tab.dart';
import 'tabs/favorites_tab.dart'; 
import 'tabs/recents_tab.dart';
import 'tabs/contacts_tab.dart';
import 'in_call_screen.dart';
import '../../main.dart'; // For isCallScreenVisible global
import '../settings_screen.dart';

class DialerScreen extends StatefulWidget {
  const DialerScreen({super.key});

  @override
  State<DialerScreen> createState() => _DialerScreenState();
}

class _DialerScreenState extends State<DialerScreen> with WidgetsBindingObserver {
  late ContactService _contactService;
  final MethodChannel _platform = const MethodChannel('com.neuralcitadel/native');
  final PhysicsManager _physicsManager = PhysicsManager();
  PhysicsMode _currentMode = PhysicsMode.gravityOrbs;
  bool _hasActiveCall = false;
  Timer? _statusTimer;
  final PageController _pageController = PageController();
  int _currentIndex = 0;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    // _contactService.init() moved to main.dart provider
    _loadTheme();
    _startStatusPoll();
    _setupNativeListener(); // Prioritize Event Listener
  }

  void _setupNativeListener() {
      _platform.setMethodCallHandler((call) async {
         if (call.method == "incomingCall") {
             final args = call.arguments as Map?;
             final bool isIncoming = args?['isIncoming'] == true;
             if (mounted && !isCallScreenVisible) {
                 isCallScreenVisible = true;
                 // INSTANT LAUNCH for ALL call types
                 Navigator.push(context, MaterialPageRoute(builder: (_) => InCallScreen(
                    callerName: args?['name'] ?? "Unknown", 
                    callerNumber: args?['number'] ?? "Unknown",
                    isIncoming: isIncoming,
                 ))).then((_) {
                    isCallScreenVisible = false;
                    _setupNativeListener(); // Restore handler on return
                 });
             }
         }
      });
  }
  
  void _startStatusPoll() {
     _checkActiveCall();
     _statusTimer = Timer.periodic(const Duration(seconds: 1), (_) => _checkActiveCall());
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _contactService = Provider.of<ContactService>(context);
  }

  Future<void> _loadTheme() async {
    await _physicsManager.init();
    if (mounted) {
      setState(() {
        _currentMode = _physicsManager.currentMode;
      });
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _statusTimer?.cancel();
    _pageController.dispose();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      _checkActiveCall();
    }
  }

  Future<void> _checkActiveCall() async {
    try {
      final dynamic result = await _platform.invokeMethod('checkActiveCall');
      final bool isActive = result != null && result is Map && result.isNotEmpty;
      final bool isIncoming = isActive && (result['isIncoming'] == true);
      
      if (mounted) {
         if (_hasActiveCall != isActive) setState(() => _hasActiveCall = isActive);
      }

      if (isIncoming && mounted && !isCallScreenVisible) {
        // Only force push if RINGING and NOT already visible
        isCallScreenVisible = true;
        Navigator.push(context, MaterialPageRoute(builder: (_) => InCallScreen(
          callerName: result['name'] ?? "Unknown", 
          callerNumber: result['number'] ?? "Unknown",
          isIncoming: true,
        ))).then((_) {
            isCallScreenVisible = false;
            _setupNativeListener();
        });
      }
    } catch (e) {
      debugPrint("Error checking call: $e");
    }
  }

  void _showKeypadOverlay() {
    Navigator.of(context).push(PageRouteBuilder(
      pageBuilder: (context, animation, secondaryAnimation) {
        return Scaffold(
          backgroundColor: Colors.transparent,
          body: Stack(
            children: [
               // Premium Glass Blur
               Positioned.fill(
                 child: BackdropFilter(
                   filter: ui.ImageFilter.blur(sigmaX: 25, sigmaY: 25),
                   child: Container(color: Colors.black.withOpacity(0.5)),
                 ),
               ),
               SafeArea(
                 child: Stack(
                   children: [
                      KeypadTab(
                         contactService: _contactService,
                         onCallInitiated: (number) {
                            Navigator.pop(context); 
                            _launchCall(number);
                         },
                      ),
                      Positioned(
                        top: 16,
                        left: 16,
                        child: IconButton(
                          icon: const Icon(Icons.arrow_back, color: Colors.white54),
                          onPressed: () => Navigator.pop(context),
                        ),
                      )
                   ],
                 ),
               ),
            ],
          ),
        );
      },
      transitionsBuilder: (context, animation, secondaryAnimation, child) {
        const curve = Curves.fastOutSlowIn;
        return SlideTransition(
           position: Tween<Offset>(begin: const Offset(0, 0.05), end: Offset.zero).animate(CurvedAnimation(parent: animation, curve: curve)),
           child: FadeTransition(
             opacity: animation,
             child: child
           ),
        );
      },
      barrierDismissible: true,
      opaque: false,
      transitionDuration: const Duration(milliseconds: 250),
    ));
  }



  @override
  Widget build(BuildContext context) {
    // Provenance: ContactService initialized in didChangeDependencies

    return Scaffold(
      backgroundColor: Colors.black, // Fallback
      body: Stack(
        children: [
          // Background
           // PREMIUM BACKGROUND: Physics + Blur + Gradient
           Positioned.fill(
             child: Stack(
               children: [
                  PhysicsBackground(mode: _currentMode),
                  
                  // Mirror Blur & Tint scaled by panelOpacity (0.0 = completely clear, 1.0 = heavy blur/dark)
                  if (PhysicsManager().panelOpacity > 0.0) ...[
                     BackdropFilter(
                       filter: ui.ImageFilter.blur(
                          sigmaX: 15.0 * PhysicsManager().panelOpacity, 
                          sigmaY: 15.0 * PhysicsManager().panelOpacity
                       ),
                       child: Container(color: Colors.black.withOpacity(0.2 * PhysicsManager().panelOpacity)), 
                     ),
                     
                     // Vignette scales with panelOpacity
                     Container(
                       decoration: BoxDecoration(
                         gradient: RadialGradient(
                           center: Alignment.center,
                           radius: 1.4,
                           colors: [Colors.transparent, Colors.black.withOpacity(PhysicsManager().panelOpacity)],
                           stops: const [0.7, 1.0],
                         )
                       ),
                     )
                  ]
               ],
             )
           ),
           
           SafeArea(
             child: PageView(
               controller: _pageController,
               onPageChanged: (index) {
                 setState(() => _currentIndex = index);
               },
               physics: const BouncingScrollPhysics(), // Elastic swipe
               children: [
                 // Tab 0: Dial (Recents)
                 const RecentsTab(),
                 // Tab 1: Contacts
                 ContactsTab(
                   contactService: _contactService,
                   onContactSelected: (number) => _launchCall(number),
                 ),
                 // Tab 2: Favorites
                 FavoritesTab(
                   contactService: _contactService,
                   onContactSelected: (number) => _launchCall(number),
                 ),
               ],
             ),
           ),
           
           // ACTIVE CALL BANNER
           if (_hasActiveCall)
             Positioned(
               top: 0, left: 0, right: 0,
               child: SafeArea(
                 child: GestureDetector(
                   onTap: () async {
                       // Resume Call UI
                       final dynamic result = await _platform.invokeMethod('checkActiveCall');
                       if (result != null && mounted) {
                          Navigator.push(context, MaterialPageRoute(builder: (_) => InCallScreen(
                              callerName: result['name'] ?? "Unknown", 
                              callerNumber: result['number'] ?? "Unknown",
                              isIncoming: result['isIncoming'] == true,
                          )));
                       }
                   },
                   child: Container(
                     width: double.infinity,
                     padding: const EdgeInsets.symmetric(vertical: 12),
                     color: Colors.greenAccent,
                     child: Center(
                       child: Row(
                         mainAxisAlignment: MainAxisAlignment.center,
                         children: [
                            const Icon(Icons.phone_in_talk, color: Colors.black, size: 20),
                            const SizedBox(width: 8),
                            Text("RETURN TO CALL", style: GoogleFonts.orbitron(color: Colors.black, fontWeight: FontWeight.bold, letterSpacing: 1.5)),
                         ],
                       ),
                     ),
                   ),
                 ),
               )
             ),
        ],
      ),
      
      // FLOATING ACTION BUTTON (Keypad) - Only on Dial Tab (Index 0)
      floatingActionButton: _currentIndex == 0 ? FloatingActionButton(
        backgroundColor: Colors.cyanAccent,
        child: const Icon(Icons.dialpad, color: Colors.black),
        onPressed: _showKeypadOverlay,
      ) : null,
      
      // BOTTOM NAVIGATION BAR
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (index) {
           setState(() => _currentIndex = index);
           _pageController.jumpToPage(index);
        },
        backgroundColor: Colors.black,
        selectedItemColor: Colors.cyanAccent,
        unselectedItemColor: Colors.white38,
        showUnselectedLabels: true,
        type: BottomNavigationBarType.fixed,
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.phone), label: "Dial"),
          BottomNavigationBarItem(icon: Icon(Icons.people), label: "Contacts"),
          BottomNavigationBarItem(icon: Icon(Icons.star), label: "Favorites"),
        ],
      ),
    );
  }

  Future<void> _launchCall(String number) async {
    if (number.isEmpty) return;
    
    // 1. Request Runtime Permission
    var status = await Permission.phone.status;
    if (!status.isGranted) {
      status = await Permission.phone.request();
      if (!status.isGranted) {
        if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Phone permission required to call")));
        return;
      }
    }

    // 2. Native System Call
    try {
      await _platform.invokeMethod('placeCall', {'number': number});
      // We don't force push here anymore; poll will handle banner or incoming check
      // Future.delayed(const Duration(milliseconds: 500), () => _checkActiveCall());
    } catch (e) {
       debugPrint("Native call failed: $e");
       final Uri launchUri = Uri(scheme: 'tel', path: number);
       if (await canLaunchUrl(launchUri)) await launchUrl(launchUri);
    }
  }
}
