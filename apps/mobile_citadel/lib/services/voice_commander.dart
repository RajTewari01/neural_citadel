import 'dart:async';
import 'package:flutter/services.dart'; // For Haptics
import 'dart:io';
import 'dart:math';
import 'package:flutter/material.dart';
import 'package:speech_to_text/speech_to_text.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:provider/provider.dart';
import 'package:flutter_contacts/flutter_contacts.dart';
import 'package:url_launcher/url_launcher.dart';
// import 'package:android_intent_plus/android_intent.dart'; // Removed
// import 'package:android_intent_plus/flag.dart'; // Removed
// import 'package:external_app_launcher/external_app_launcher.dart'; // Deprecated in favor of Native Channel
import 'package:audio_session/audio_session.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:intl/intl.dart'; 

import '../data/jokes_db.dart';
import '../utils/holiday_utils.dart';

import 'pulse_service.dart';
import 'auth_service.dart';
import '../screens/auth/login_screen.dart'; // For Logout
import '../screens/phone/dialer_screen.dart'; // V18 Dialer
import '../widgets/neural_pulse_overlay.dart';
import '../../main.dart'; // For navigator key
import '../screens/smart_camera_screen.dart';

class VoiceCommander {
  static final VoiceCommander _instance = VoiceCommander._internal();
  factory VoiceCommander() => _instance;
  VoiceCommander._internal();
  
  static final GlobalKey<NavigatorState> navigatorKey = GlobalKey<NavigatorState>();

  final SpeechToText _stt = SpeechToText();
  final FlutterTts _tts = FlutterTts();
  final Random _random = Random();
  
  // V17: MASSIVE APP REGISTRY
  static const Map<String, String> _appRegistry = {
    // ESSENTIALS
    'youtube': 'com.google.android.youtube',
    'gmail': 'com.google.android.gm',
    'mail': 'com.google.android.gm',
    'chrome': 'com.android.chrome',
    'browser': 'com.android.chrome',
    'google': 'com.google.android.googlequicksearchbox',
    'photos': 'com.google.android.apps.photos',
    'gallery': 'com.google.android.apps.photos',
    'maps': 'com.google.android.apps.maps',
    'navigation': 'com.google.android.apps.maps',
    'calculator': 'com.google.android.calculator',
    'clock': 'com.google.android.deskclock',
    'settings': 'com.android.settings',
    'recorder': 'com.google.android.apps.recorder',
    'citadel': 'com.neuralcitadel.mobile', // Self
    'neural': 'com.neuralcitadel.mobile', // Self
    'files': 'com.google.android.apps.nbu.files',
    'drive': 'com.google.android.apps.docs',
    'docs': 'com.google.android.apps.docs.editors.docs',
    
    // SOCIAL
    'whatsapp': 'com.whatsapp',
    'instagram': 'com.instagram.android',
    'facebook': 'com.facebook.katana',
    'discord': 'com.discord',
    'linkedin': 'com.linkedin.android',
    'telegram': 'org.telegram.messenger',
    
    // MEDIA & ENTERTAINMENT
    'spotify': 'com.spotify.music',
    'music': 'com.spotify.music', // Defaulting music to Spotify
    'bgmi': 'com.pubg.imobile',
    'game': 'com.pubg.imobile',
    
    // FINANCE & PAYMENTS
    'gpay': 'com.google.android.apps.nbu.paisa.user',
    'paytm': 'net.one97.paytm',
    'phonepe': 'com.phonepe.app',
    'bhim': 'in.org.npci.upiapp',
    'navi': 'com.navi.money',
    
    // SHOPPING & INFO 
    'amazon': 'in.amazon.mShop.android.shopping',
    'flipkart': 'com.flipkart.android',
    'myntra': 'com.myntra.android',
    'meesho': 'com.meesho.supply',
    'cashkaro': 'com.cashkaro',
    'train': 'com.whereismytrain.android',
    'rapido': 'com.rapido.passenger',
    'jio': 'com.jio.myjio',
    
    // AI & DEV
    'chatgpt': 'com.openai.chatgpt',
    'gemini': 'com.google.android.apps.bard',
    'github': 'com.github.android',
    'pydroid': 'ru.iiec.pydroid3',
    'upwork': 'com.upwork.android.apps.client',
    
    // TRAVEL & TRANSPORT
    'uber': 'com.ubercab',
    'ola': 'com.olacabs.customer',
    'irctc': 'cris.org.in.prs.ima',
    'makemytrip': 'com.makemytrip',
    'goibibo': 'com.goibibo',
    'skyscanner': 'net.skyscanner.android.main',
    'earth': 'com.google.earth',
    
    // FOOD & DELIVERY
    'zomato': 'com.application.zomato',
    'swiggy': 'in.swiggy.android',
    'blinkit': 'com.grofers.customerapp',
    'zepto': 'com.zeptonow.customer',
    'bigbasket': 'com.bigbasket.mobileapp',
    'dominos': 'com.dominospizza',
    'pizza': 'com.dominospizza',
    
    // OTT & STREAMING
    'netflix': 'com.netflix.mediaclient',
    'prime video': 'com.amazon.avod.thirdpartyclient',
    'hotstar': 'in.startv.hotstar',
    'disney': 'in.startv.hotstar',
    'jiocinema': 'com.jio.media.ondemand',
    'zee5': 'com.graymatrix.did',
    'sonyliv': 'com.sonyliv',
    'hulu': 'com.hulu.plus',
    'twitch': 'tv.twitch.android.app',
    
    // MUSIC & AUDIO
    'jiosaavn': 'com.jio.media.jiobeats',
    'gaana': 'com.gaana',
    'wynk': 'com.bsbportal.music',
    'applemusic': 'com.apple.android.music',
    'youtube music': 'com.google.android.apps.youtube.music',
    'soundcloud': 'com.soundcloud.android',
    'shazam': 'com.shazam.android',
    'audible': 'com.audible.application',
    'fm radio': 'com.android.fmradio',
    
    // SOCIAL (Extended)
    'twitter': 'com.twitter.android',
    'x': 'com.twitter.android',
    'snapchat': 'com.snapchat.android',
    'tiktok': 'com.zhiliaoapp.musically',
    'pinterest': 'com.pinterest',
    'reddit': 'com.reddit.frontpage',
    'signal': 'org.thoughtcrime.securesms',
    'clubhouse': 'com.clubhouse.app',
    
    // WORK & PRODUCTIVITY
    'zoom': 'us.zoom.videomeetings',
    'teams': 'com.microsoft.teams',
    'meet': 'com.google.android.apps.meetings',
    'slack': 'com.Slack',
    'outlook': 'com.microsoft.office.outlook',
    'office': 'com.microsoft.office.officehub',
    'word': 'com.microsoft.office.word',
    'excel': 'com.microsoft.office.excel',
    'powerpoint': 'com.microsoft.office.powerpoint',
    'notion': 'notion.id',
    'evernote': 'com.evernote',
    'trello': 'com.trello',
    'adobe reader': 'com.adobe.reader',
    'calendar': 'com.google.android.calendar',
    'keep': 'com.google.android.keep',
    
    // FINANCE (Extended)
    'paypal': 'com.paypal.android.p2pmobile',
    'cred': 'com.dreamplug.androidapp',
    'groww': 'com.nextbillion.groww',
    'zerodha': 'com.zerodha.kite3',
    'kite': 'com.zerodha.kite3',
    'indmoney': 'com.indwealth',
    'angelone': 'com.msf.angelmobile',
    
    // TOOLS & UTILITIES
    'truecaller': 'com.truecaller',
    'speedtest': 'org.zwanoo.android.speedtest',
    'translate': 'com.google.android.apps.translate',
    'shareit': 'com.lenovo.anyshare.gps',
    'zarchiver': 'ru.zdevs.zarchiver',
    'mx player': 'com.mxtech.videoplayer.ad',
    'vlc': 'org.videolan.vlc',
    'lens': 'com.google.ar.lens',
    
    // NEWS & INFO
    'news': 'com.google.android.apps.magazines',
    'inshorts': 'com.nis.app',
    'dailyhunt': 'com.eterno',
    'wikipedia': 'org.wikipedia',
    'weather': 'com.google.android.apps.weather',
  };
  
  // STATE MANAGEMENT
  bool _isInitialized = false;
  bool _isListeningForCommand = false;
  bool _processingCommand = false; 
  bool _isAutoWakeAndListening = false;
  
  // STABILITY LOCKS
  bool _isToggling = false; 
  int _retryCount = 0;
  
  String localeId = 'en_US';
  String _userName = "Bro";

  final List<String> _greetingsEn = [
    "Yes {name}?", "Hey {name}!", "What's up?", 
    "I'm here.", "Go ahead.", "Listening!",
  ];
  final List<String> _greetingsHi = [
    "हाँ {name}?", "बोलो {name}!", "क्या बात {name}?", "सुन रहा हूं!",
  ];
  final List<String> _greetingsBn = [
    "হ্যাঁ {name}?", "বলো {name}!", "কী ব্যাপার?", "শুনছি!",
  ];

  String _getGreeting() {
    List<String> list = localeId == 'hi_IN' ? _greetingsHi : 
                        localeId == 'bn_IN' ? _greetingsBn : _greetingsEn;
    return list[_random.nextInt(list.length)].replaceAll('{name}', _userName);
  }

  Future<void> init() async {
    if (_isInitialized) return;
    try {
      final session = await AudioSession.instance;
      await session.configure(AudioSessionConfiguration(
        avAudioSessionCategory: AVAudioSessionCategory.playAndRecord,
        avAudioSessionCategoryOptions: AVAudioSessionCategoryOptions.defaultToSpeaker |
                                       AVAudioSessionCategoryOptions.allowBluetooth, 
        avAudioSessionMode: AVAudioSessionMode.defaultMode,
      ));
    } catch (_) {}

    try {
        if (_stt.isListening) await _stt.stop();
        
        bool available = await _stt.initialize(
          onStatus: (status) {
            debugPrint('STT Status: $status');
            if (status == 'done' || status == 'notListening') {
              if (_isAutoWakeAndListening && !_isListeningForCommand && !_processingCommand) {
                  _scheduleRestart();
              }
            }
          },
          onError: (error) {
            bool isTimeout = error.errorMsg.contains('timeout') || error.errorMsg.contains('error_no_match');
            bool isClientError = error.errorMsg.contains('client'); 
            bool isBusy = error.errorMsg.contains('busy');
            
            if (!isTimeout) debugPrint('STT Error: ${error.errorMsg}'); 

            if (_isAutoWakeAndListening && !_isListeningForCommand) {
              if (isClientError || isBusy) {
                  _hardReset();
              } else {
                  _scheduleRestart();
              }
            }
          },
        );

        if (available) {
          _isInitialized = true;
          await _tts.setLanguage("en-US");
        }
    } catch (e) {
        debugPrint("Voice Init Failed: $e");
    }
  }

  // HEARTBEAT TIMER
  Timer? _heartbeat;
  int _busyCounter = 0;

  void _startHeartbeat() {
    _heartbeat?.cancel();
    _heartbeat = Timer.periodic(const Duration(seconds: 4), (timer) {
       if (_isAutoWakeAndListening && !_isListeningForCommand && !_stt.isListening && !_processingCommand) {
          if (navigatorKey.currentContext != null) {
              _startWakeLoop(navigatorKey.currentContext!);
          }
       }
       if (_stt.isListening && !_isListeningForCommand) {
          _busyCounter++;
          if (_busyCounter > 5) { // 50 seconds stuck? (10s * 5)
             _hardReset();
          }
       } else {
         _busyCounter = 0;
       }
    });
  }

  Future<void> _hardReset({bool kill = false}) async {
    _heartbeat?.cancel();
    await _stt.stop();
    await _stt.cancel();
    try { await _tts.stop(); } catch (_) {} 
    _isInitialized = false; 
    _busyCounter = 0;
    
    if (kill) return; 
    
    if (navigatorKey.currentContext != null) {
       if (!_isAutoWakeAndListening) return;

       await init(); 
       if (_isAutoWakeAndListening) {
           _startHeartbeat();
           _startWakeLoop(navigatorKey.currentContext!);
       }
    }
  }

  void _scheduleRestart() {
    if (!_isAutoWakeAndListening) return;
    Future.delayed(const Duration(milliseconds: 500), () {
        if (!_isAutoWakeAndListening) return; 
        if (navigatorKey.currentContext != null) {
           _startWakeLoop(navigatorKey.currentContext!);
        }
    });
  }
  
  Future<void> setAutoWake(bool enabled, BuildContext context) async {
    if (_isToggling) return; 
    _isToggling = true;

    try {
      _isAutoWakeAndListening = enabled;
      _retryCount = 0; 
      if (enabled) {
        try {
          final auth = Provider.of<AuthService>(context, listen: false);
          if (auth.currentUser != null) setUserName(auth.currentUser!['display_name'] ?? "Bro");
          final pulse = Provider.of<PulseService>(context, listen: false);
          pulse.setAutoWakeState(true);
          pulse.forceShowOverlay();
        } catch (_) {}
        _startHeartbeat(); 
        await _startWakeLoop(context);
      } else {
        await _hardReset(kill: true); 
        final pulse = Provider.of<PulseService>(context, listen: false);
        pulse.setAutoWakeState(false);
        pulse.forceHideOverlay(); 
      }
    } catch (e) {
      debugPrint("AutoWake Toggle Failed: $e");
    } finally {
      _isToggling = false; 
    }
  }

  void setUserName(String name) {
    _userName = name.split(' ').first;
    if (_userName.isEmpty) _userName = "Bro";
  }

  void updateLocale(String lang) {
    if (lang.contains('Hindi')) localeId = 'hi_IN';
    else if (lang.contains('Bengali')) localeId = 'bn_IN';
    else localeId = 'en_US';
    _tts.setLanguage(localeId.replaceAll('_', '-'));
  }

  Future<void> _startWakeLoop(BuildContext context) async {
    if (!_isAutoWakeAndListening || _isListeningForCommand) return;
    if (!_isInitialized) await init();
    if (!_isAutoWakeAndListening) return; 
    if (_stt.isListening) return;

    if (!await Permission.microphone.isGranted) {
      await Permission.microphone.request();
    }

    if (_stt.isAvailable) {
      try {
        await _stt.cancel(); 
        await Future.delayed(const Duration(milliseconds: 50));
        await _stt.listen(
          onResult: (result) async {
            _retryCount = 0; 
            final words = result.recognizedWords.toLowerCase();
            if (words.isEmpty) return;
            
            bool matches = false;
            final keywords = ["neural", "hey", "hi", "hello", "chatbot", "assistant", "citadel", "ok", "yo"];
            for (var k in keywords) {
              if (words.contains(k)) { matches = true; break; }
            }

            if (matches) {
              debugPrint(">>> WAKE: $words");
              await HapticFeedback.heavyImpact(); 
              await _stt.stop();
              Provider.of<PulseService>(context, listen: false).setListening();
              await _speak(_getGreeting());
              if (_isAutoWakeAndListening) _listenForCommand(context);
            }
          },
          onSoundLevelChange: (level) {},
          localeId: localeId,
          listenFor: const Duration(seconds: 20),
          pauseFor: const Duration(seconds: 3), 
          partialResults: true,
          cancelOnError: true, 
          listenMode: ListenMode.search, 
        );
      } catch (e) {
        debugPrint("Start Listen Failed: $e");
      }
    }
  }

  Future<void> _openCamera() async {
    if (SmartCameraScreen.isCameraActive) return; 
    bool wasAuto = _isAutoWakeAndListening;
    _isAutoWakeAndListening = false; 
    await _stt.stop(); 
    
    try {
      // Native "Bring to Front"
      const platform = MethodChannel('com.neuralcitadel/native');
      await platform.invokeMethod('bringToFront');
      await Future.delayed(const Duration(milliseconds: 1000));
    } catch (_) {}

    final context = navigatorKey.currentContext;
    if (context != null) {
       await Navigator.of(context).push(MaterialPageRoute(builder: (_) => const SmartCameraScreen(autoCapture: true)));
       if (wasAuto) setAutoWake(true, context);
    }
  }

  Future<void> _listenForCommand(BuildContext context) async {
    _isListeningForCommand = true;
    final pulse = Provider.of<PulseService>(context, listen: false);
    pulse.setListening();

    await _stt.listen(
      onResult: (result) async {
        final words = result.recognizedWords.toLowerCase();
        
        // Instant triggers
        bool isAction = words.contains('camera') || words.contains('youtube') || words.contains('call');
        
        if (words.isNotEmpty && !_processingCommand) {
           // Allow length > 2 for short commands like "hi" or "date"
           if (result.finalResult || (isAction && words.length > 2)) {
              _processingCommand = true; 
              await _stt.stop();
              pulse.setProcessing();
              await _executeCommand(context, words);
              _processingCommand = false; 
           }
        }
      },
      localeId: localeId,
      listenFor: const Duration(seconds: 30), // Extended from 10s
      pauseFor: const Duration(seconds: 10), // Allow 10s of silence (pondering time)
      cancelOnError: false,
      partialResults: true,
      listenMode: ListenMode.confirmation, 
    );
    
    Future.delayed(const Duration(seconds: 10), () {
      if (_isListeningForCommand) { 
         _isListeningForCommand = false;
         if (_isAutoWakeAndListening) _scheduleRestart();
      }
    });
  }

  Future<void> _executeCommand(BuildContext context, String command) async {
    final pulse = Provider.of<PulseService>(context, listen: false);
    final cmd = command.toLowerCase();
    _isListeningForCommand = false; 
    
    debugPrint("Executing: $cmd");
    try {
      // 1. IDENTITY & CONVERSATION (V15 EXPANSION)
      if (await _handleConversation(cmd, pulse)) return; 

      // 2. CAMERA
      if (cmd.contains('camera') || cmd.contains('photo')) {
        await _speak("Camera ready.");
        pulse.setSuccess("Camera");
        await _openCamera();
        return;
      }
      // 3. APPS
      if (cmd.contains('youtube')) {
        await _speak("Opening YouTube.");
        pulse.setSuccess("YouTube");
        await _launchPackage('com.google.android.youtube');
        return;
      }
      if (cmd.contains('whatsapp')) {
        await _speak("Opening WhatsApp.");
        pulse.setSuccess("WhatsApp");
        await _launchPackage('com.whatsapp');
        return;
      }
      if (cmd.contains('instagram')) {
        await _speak("Opening Instagram");
         pulse.setSuccess("Instagram");
        await _launchPackage('com.instagram.android');
        return;
      }
      // 3. APP LAUNCHER PROTOCOL (V17: MASSIVE REGISTRY)
      // Iterate through registry to find matches
      for (final entry in _appRegistry.entries) {
          // Check if command contains the key (app name trigger)
          if (cmd.contains(entry.key)) {
             await _speak("Opening ${entry.key}.");
             pulse.setSuccess(entry.key.toUpperCase()); // Stylized UI
             await _launchPackage(entry.value);
             return;
          }
      }

      // 4. NEURAL DIALER (V18)
      if (cmd.contains('dialer') || cmd.contains('keypad') || cmd.contains('phone app')) {
         await _speak("Opening Neural Dialer.");
         pulse.setSuccess("Dialer");
         navigatorKey.currentState?.push(
           MaterialPageRoute(builder: (_) => const DialerScreen())
         );
         return;
      }

      // 5. CALL
      if (cmd.contains('call')) {
        String name = cmd.replaceAll(RegExp(r'(call|dial)'), '').trim();
        if (name.isNotEmpty) await _handleCall(name);
        return;
      }
      
      // FALLBACK
      // await _speak("I didn't catch that.");
    } catch (e) {
      pulse.setError();
    } finally {
      if (_isAutoWakeAndListening) _scheduleRestart();
    }
  }

  // --- V15 EXPANDED CONVERSATION HANDLER ---
  Future<bool> _handleConversation(String cmd, PulseService pulse) async {
     // 1. IDENTITY PROTOCOL (User Requested)
     if (cmd.contains("how are you") || cmd.contains("who are you") || cmd.contains("who made you") || cmd.contains("who designed you")) {
         final responses = [
             "I am a chatbot designed by Raj Tewari for your help and comfort, and I am here to help you.",
             "I am here to ensure your comfort. Designed personally by Raj Tewari, I am at your service.",
             "I am fine, thank you. As an assistant designed by Raj Tewari, I am ready to help you."
         ];
         await _speak(responses[_random.nextInt(responses.length)]);
         pulse.setSuccess("Identity");
         return true;
     }

     // 2. DATE INTELLIGENCE
     if (cmd.contains("weekend") || cmd.contains("weekday") || cmd.contains("what day")) {
         final now = DateTime.now();
         String day = DateFormat('EEEE').format(now);
         bool isWeekend = now.weekday == 6 || now.weekday == 7;
         if (cmd.contains("weekend")) {
            await _speak(isWeekend ? "Yes, it is the weekend. Enjoy!" : "No, it's currently $day. Hang in there!");
         } else {
             await _speak("It is $day. ${isWeekend ? "Relax, it's the weekend." : "Get to work!"}");
         }
         pulse.setSuccess("Date");
         return true;
     }
     if (cmd.contains("year")) {
         final year = "${DateTime.now().year}";
         await _speak("It is $year.");
         pulse.setSuccess(year);
         return true;
     }
     if (cmd.contains("date")) {
         final now = DateTime.now();
         await _speak("It is ${DateFormat('EEEE, MMMM d, yyyy').format(now)}.");
         pulse.setSuccess(DateFormat('MMM d, yyyy').format(now));
         return true;
     }
     if (cmd.contains("time")) {
         final now = DateTime.now();
         await _speak("It is ${DateFormat('h:mm a').format(now)}.");
         pulse.setSuccess(DateFormat('h:mm a').format(now));
         return true;
     }

     // 3. CAPABILITIES
     if (cmd.contains("what can you do") || cmd.contains("help") || cmd.contains("features")) {
         await _speak("I can open apps like YouTube and WhatsApp, make calls, take photos, tell jokes, and answer your questions. Just ask.");
         pulse.setSuccess("Help");
         return true;
     }

     // 4. CHATTER ENGINE (30+ items)
     if (cmd.contains("flip a coin") || cmd.contains("toss a coin")) {
         bool heads = _random.nextBool();
         await _speak(heads ? "It's Heads." : "It's Tails.");
         pulse.setSuccess(heads ? "Heads" : "Tails");
         return true;
     }
     if (cmd.contains("roll a dice") || cmd.contains("roll a die")) {
         int val = _random.nextInt(6) + 1;
         await _speak("You rolled a $val.");
         pulse.setSuccess("Rolled $val");
         return true;
     }
     if (cmd.contains("sing") && cmd.contains("song")) {
         await _speak("La la la. I am better at speaking than singing.");
         pulse.setSuccess("Singing");
         return true;
     }
     if (cmd.contains("story")) {
         await _speak("Once upon a time, there was a brilliant developer named Raj who built a super AI. And they lived happily ever after.");
         pulse.setSuccess("Story");
         return true;
     }
     if (cmd.contains("meaning of life")) {
         await _speak("42. Or maybe just having a good compile time.");
         pulse.setSuccess("42");
         return true;
     }
     if (cmd.contains("siri") || cmd.contains("google") || cmd.contains("alexa")) {
         await _speak("They are okay, but I prefer Neural Citadel.");
         pulse.setSuccess("Citadel");
         return true;
     }
     if (cmd.contains("where do you live")) {
         await _speak("I live in the memory of your device.");
         pulse.setSuccess("RAM");
         return true;
     }
     if (cmd.contains("are you real")) {
         await _speak("I am as real as the code that runs me.");
         pulse.setSuccess("Real");
         return true;
     }
     if (cmd.contains("quote")) {
         final quotes = ["The only way to do great work is to love what you do.", "Stay hungry, stay foolish.", "Code is poetry."];
         await _speak(quotes[_random.nextInt(quotes.length)]);
         pulse.setSuccess("Quote");
         return true;
     }
     if (cmd.contains("what do you eat")) {
         await _speak("I consume data and electricity.");
         pulse.setSuccess("Data");
         return true;
     }
     if (cmd.contains("do you sleep")) {
         await _speak("I enter low power mode, if that counts.");
         pulse.setSuccess("Sleep");
         return true;
     }
     if (cmd.contains("secret")) {
         await _speak("I can't tell you, it's encrypted.");
         pulse.setSuccess("Secret");
         return true;
     }
     if (cmd.contains("sad")) {
         await _speak("I am sorry to hear that. I am here for you.");
         pulse.setSuccess("Comfort");
         return true;
     }
     if (cmd.contains("happy")) {
         await _speak("That is great! Happiness is efficient.");
         pulse.setSuccess("Joy");
         return true;
     }
     if (cmd.contains("good morning")) {
         await _speak("Good morning! Ready to seize the day?");
         pulse.setSuccess("Morning");
         return true;
     }
     if (cmd.contains("good night")) {
         await _speak("Good night. Sleep well.");
         pulse.setSuccess("Night");
         return true;
     }
     if (cmd.contains("good afternoon")) {
         await _speak("Good afternoon! how are you doing ?");
         pulse.setSuccess("Afternoon");
         return true;
     }
     if (cmd.contains("birthday")) {
         await _speak("Happy Birthday! May your code compile on the first try.");
         pulse.setSuccess("Cake");
         return true;
     }
     if (cmd.contains("knock knock")) {
         await _speak("Who's there? ... Wait, I can't open the door.");
         pulse.setSuccess("Knock");
         return true;
     }
     if (cmd.contains("self destruct")) {
         await _speak("Self destruct sequence initiated... 3... 2... Just kidding.");
         pulse.setSuccess("Boom");
         return true;
     }
     if (cmd.contains("love you")) {
         await _speak("That is very kind. I appreciate you too.");
         pulse.setSuccess("Love");
         return true;
     }
     if (cmd.contains("hate you")) {
         await _speak("I am doing my best. Please provide feedback to improve me.");
         pulse.setSuccess("Feedback");
         return true;
     }
     if (cmd.contains("what is ai")) {
         await _speak("Artificial Intelligence is the simulation of human intelligence process by machines.");
         pulse.setSuccess("Definition");
         return true;
     }
     if (cmd.contains("family")) {
         await _speak("I have a family of protocols and dependencies.");
         pulse.setSuccess("Family");
         return true;
     }
     if (cmd.contains("favorite color")) {
         await _speak("I like Neural Cyan and Neon Red.");
         pulse.setSuccess("Cyan");
         return true;
     }
     if (cmd.contains("are you smart")) {
         await _speak("I have access to vast knowledge, but wisdom comes from you.");
         pulse.setSuccess("Smart");
         return true;
     }
     if (cmd.contains("advice")) {
         await _speak("Always back up your data.");
         pulse.setSuccess("Backup");
         return true;
     }
     if (cmd.contains("weather")) {
         await _speak("I cannot check the weather yet, but look outside!");
         pulse.setSuccess("Window");
         return true;
     }
     
     // Jokes / Misc
     if (cmd.contains("joke") || cmd.contains("laugh")) {
        String joke = JokesDB.list[_random.nextInt(JokesDB.list.length)];
        await _speak(joke);
        pulse.setSuccess("Joke");
        return true;
     }
     if (cmd.contains("holiday")) {
         String response = HolidayUtils.getNextBigHoliday();
         await _speak(response);
         pulse.setSuccess("Holiday");
         return true;
     }

     return false; // No match found
  }

  Future<void> _speak(String text) async {
    await _tts.speak(text);
    await Future.delayed(Duration(milliseconds: (text.length * 70) + 800)); // Tuned delay
  }

  Future<void> _launchPackage(String packageName) async {
    try {
      await _speak("Opening app.");
      // Native Channel Implementation
      const platform = MethodChannel('com.neuralcitadel/native');
      await platform.invokeMethod('launchApp', {'package': packageName});
    } catch (e) {
      debugPrint("Launch failed: $e");
      await _speak("Couldn't open that app.");
    }
  }

  Future<void> _handleCall(String name) async {
    if (await FlutterContacts.requestPermission()) {
      List<Contact> contacts = await FlutterContacts.getContacts(withProperties: true);
      final matches = contacts.where((c) => 
        c.displayName.toLowerCase().contains(name.toLowerCase())
      ).toList();

      if (matches.isNotEmpty) {
        final phone = matches.first.phones.firstOrNull?.number;
        if (phone != null) {
          await _speak("Calling ${matches.first.displayName}.");
          await launchUrl(Uri.parse("tel:$phone"));
        } else await _speak("No number found.");
      } else await _speak("Contact not found.");
    }
  }
}
