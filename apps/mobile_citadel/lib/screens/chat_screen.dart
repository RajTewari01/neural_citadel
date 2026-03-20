import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../widgets/typewriter_text.dart';
import '../widgets/message_bubble.dart';
import '../services/database_helper.dart';
import '../services/auth_service.dart';
import '../screens/history_screen.dart';
import '../screens/admin/admin_dashboard.dart';
import '../widgets/rain_overlay.dart'; 
import '../widgets/qr_view.dart';
import '../widgets/movie_view.dart';
import '../widgets/chat_input.dart';
import '../widgets/mode_selector.dart';
import '../widgets/writing_controls.dart';
import '../widgets/coding_controls.dart';
import '../widgets/image_controls.dart';
import '../widgets/mode_selector_pill.dart';
import '../widgets/newspaper_view.dart'; 
import '../widgets/surgeon_view.dart';
import '../widgets/image_viewer.dart';
import '../widgets/code_block.dart';
import 'gallery_screen.dart'; // Added
import '../theme/app_theme.dart';
import '../widgets/system_stats_pill.dart'; // Added
import '../screens/settings_screen.dart';
import '../services/pulse_service.dart'; // Added
import 'phone/dialer_screen.dart';

class ChatScreen extends StatefulWidget {
  final String mode; 
  final int? sessionId;

  const ChatScreen({Key? key, required this.mode, this.sessionId}) : super(key: key);

  @override
  _ChatScreenState createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final TextEditingController _controller = TextEditingController();
  late ApiService _api;
  final List<Map<String, dynamic>> _messages = []; 
  final ScrollController _scrollController = ScrollController();
  
  late String _currentMode;
  String _modeLabel = "Neural Citadel";
  bool _isLoading = false;
  
  // Writing Mode State
  bool _isNSFW = false;
  String _writingPersona = "therapist";
  String _writingStyle = "supportive";

  // Image Gen State
  String _imagePipeline = "anime";
  String? _imageSubtype;
  String _imageRatio = "1152:896";
  int? _imageSeed;

  // Speech State
  late stt.SpeechToText _speech;
  bool _isListening = false;
  String _baseText = "";
  bool _isSpeechUpdate = false;
  
  // Persistence
  final DatabaseHelper _db = DatabaseHelper.instance;
  int? _sessionId;
  bool _isSessionLoaded = false;

  @override
  void initState() {
    super.initState();
    _currentMode = widget.mode;
    _sessionId = widget.sessionId;
    _modeLabel = _getModeLabel(widget.mode);
    _speech = stt.SpeechToText();
    
    // Defer DB loading to post-build/init
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _initSession();
      // No in-app overlay - background only per user request
    });
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _api = Provider.of<ApiService>(context, listen: false);
  }

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  String _getModeLabel(String mode) {
    switch (mode) {
      case 'writing': return "✍️ Writing";
      case 'coding': return "💻 Coding";
      case 'hacking': return "🔓 Hacking";
      case 'image': return "🎨 Image Gen";
      case 'qr': return "📱 QR Studio";
      case 'movie': return "🎬 Movies";
      case 'newspaper': return "📰 Newspaper";
      case 'surgeon': return "🔪 Surgeon";
      case 'voice': return "🎙️ Voice";
      case 'gallery': return "🖼️ Gallery";
      default: return "🧠 Reasoning";
    }
  }

  void _addSystemMessageForMode(String mode) {
    String msg = "Mode: ${_getModeLabel(mode)}";
    if (mode == 'writing' && _isNSFW) msg += " (NSFW Enabled)";
    setState(() {
      _messages.add({"role": "system", "content": msg, "type": "text"});
    });
  }

  RainType _getRainForMode(String mode) {
    switch (mode) {
      case 'coding': return RainType.matrixGreen;
      case 'hacking': return RainType.cyanCyber;
      case 'writing': 
        if (_writingPersona == 'teacher') return RainType.violetStream;
        if (_writingPersona == 'poet') return RainType.pinkRetro;
        return RainType.purpleHaze;
      case 'image': return RainType.goldenData;
      case 'qr': return RainType.blueDrops;
      case 'movie': return RainType.orangeFlux;
      case 'newspaper': return RainType.neonRain;
      case 'surgeon': return RainType.emeraldCity;
      case 'reasoning': return RainType.starfield;
      default: return RainType.starfield; // Fallback to starfield
    }
  }

  void _openModeSelector() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (ctx) => ModeSelector(
        currentModeId: _currentMode,
        onModeSelected: (modeId, modeLabel) {
          Navigator.pop(ctx);
          setState(() {
            _currentMode = modeId;
            _modeLabel = modeLabel;
            _messages.clear();
            _addSystemMessageForMode(modeId);
          });
        },
      ),
    );
  }

  void _handleSubmitted(String text) {
    if (text.trim().isEmpty) return;
    setState(() {
      _messages.add({"role": "user", "content": text, "type": "text"});
      _isLoading = true;
    });
    _controller.clear();
    _scrollToBottom();
    _sendMessage(text);
  }

  bool _isSpeechInitialized = false;

  Future<void> _startRecording() async {
    if (!mounted) return;
    try {
      if (!_isSpeechInitialized) {
        bool available = await _speech.initialize(
          onError: (val) {
             // Force restart on error (e.g. timeout) if listening is intended
             if (_isListening) {
               Future.delayed(const Duration(milliseconds: 50), () => _startRecording());
             }
          },
          onStatus: (status) {
             if (status == 'done' || status == 'notListening') {
                if (_isListening) {
                   Future.delayed(const Duration(milliseconds: 50), () => _startRecording());
                }
             }
          }
        );
        if (!available) return;
        _isSpeechInitialized = true;
      }

      // Capture current text reference immediately before starting new session
      setState(() {
        _baseText = _controller.text;
        _isListening = true; 
      });
      
      await _speech.listen(
        onDevice: false, // Cloud-based for better accents (Hindi/Indian)
        listenFor: const Duration(minutes: 30), // Long duration
        pauseFor: const Duration(minutes: 5),  // Long pause check
        onResult: (val) {
          if (!mounted) return;
          setState(() {
            _isSpeechUpdate = true;
            String spacer = (_baseText.isNotEmpty && !_baseText.endsWith(' ')) ? " " : "";
            _controller.text = "$_baseText$spacer${val.recognizedWords}";
            _controller.selection = TextSelection.fromPosition(TextPosition(offset: _controller.text.length));
            _isSpeechUpdate = false;
          });
        },
        listenMode: stt.ListenMode.dictation,
        cancelOnError: false, // Don't stop on temporary errors
        partialResults: true,
      );
    } catch (e) {
       // Retry if startup failed but we want to listen
       if (_isListening) {
          Future.delayed(const Duration(milliseconds: 50), () => _startRecording());
       }
    }
  }

  void _stopRecording() {
    _speech.stop();
    setState(() => _isListening = false);
  }

  void _toggleRecording() {
    if (_isListening) {
      _stopRecording();
    } else {
      _startRecording();
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _initSession() async {
    final auth = Provider.of<AuthService>(context, listen: false);
    
    if (_sessionId != null) {
      // Load existing
      final msgs = await _db.getSessionMessages(_sessionId!);
      setState(() {
        _messages.clear();
        _messages.addAll(msgs);
        _isSessionLoaded = true;
      });
      // Delay scroll until build
      Future.delayed(const Duration(milliseconds: 100), _scrollToBottom);
    } else {
      // New Session
      _addSystemMessageForMode(_currentMode);
      setState(() => _isSessionLoaded = true);
    }
  }

  void _sendMessage(String text) async {
    // 0. Ensure Session Exists
    final auth = Provider.of<AuthService>(context, listen: false);
    if (_sessionId == null && auth.isLoggedIn) {
      _sessionId = await _db.createSession(auth.currentUser!['id'] as int, text, _currentMode); // Use first msg as title, save mode
    }

    // 1. Save User Msg
    if (_sessionId != null) {
      await _db.addMessage(_sessionId!, {"role": "user", "content": text, "type": "text"});
    }

    try {
      if (_currentMode == 'image') {
        // Add Placeholder
        final placeholder = {
          "role": "assistant", 
          "content": "Generating...", 
          "type": "image_placeholder",
          "ratio": _imageRatio,
          "percent": 0
        };
        setState(() => _messages.add(placeholder));
        _scrollToBottom();
        
        // Save placeholder to DB? Maybe wait for result.
        // Actually, we should probably save the RESULT only to avoid cluttering DB with loading states.

        // Image Gen Stream
        String finalUrl = "";
        await for (final chunk in _api.generateImageStream(text, style: _imagePipeline, subtype: _imageSubtype, ratio: _imageRatio, seed: _imageSeed)) {
          if (chunk.startsWith("RESULT:")) {
            finalUrl = chunk.substring(7).trim();
            setState(() {
              if (_messages.isNotEmpty && _messages.last['type'] == 'image_placeholder') {
                _messages.last['content'] = finalUrl;
                _messages.last['type'] = 'image';
              }
            });
          } else if (chunk.startsWith("PROGRESS:")) {
             // ... handling progress ...
             try {
               int prog = int.parse(chunk.substring(9).trim());
               setState(() {
                  if (_messages.isNotEmpty && _messages.last['type'] == 'image_placeholder') {
                    _messages.last['percent'] = prog;
                  }
               });
             } catch(e) {}
          } else {
             final log = chunk.trim();
             if (log.isNotEmpty) {
                setState(() {
                   if (_messages.isNotEmpty && _messages.last['type'] == 'image_placeholder') {
                      _messages.last['statusText'] = log;
                   }
                });
             }
          }
        }
        
        // Save Result to DB
        if (_sessionId != null && finalUrl.isNotEmpty) {
           await _db.addMessage(_sessionId!, {"role": "assistant", "content": finalUrl, "type": "image"});
        }

      } else {
        // Chat Stream
        String fullResponse = "";
        final history = _messages.toList(); // copy
        
        // Add streaming placeholder
        setState(() {
           _messages.add({"role": "assistant", "content": "", "type": "text"});
        });
        
        await for (final chunk in _api.chatStream(
          text, 
          model: _currentMode, 
          history: history.map((m) => {"role": m["role"] as String, "content": m["content"] as String}).toList(),
          persona: _currentMode == 'writing' ? _writingPersona : null,
          style: _currentMode == 'writing' ? _writingStyle : null,
          nsfw: _isNSFW
        )) {
          fullResponse += chunk;
          setState(() {
            _messages.last['content'] = fullResponse;
          });
          _scrollToBottom();
        }
        
        // Save Assistant Msg
        if (_sessionId != null) {
           await _db.addMessage(_sessionId!, {"role": "assistant", "content": fullResponse, "type": "text"});
        }
      }
    } catch (e) {
      setState(() { _messages.add({"role": "system", "content": "Error: $e", "type": "text"}); });
      if (_sessionId != null) await _db.addMessage(_sessionId!, {"role": "system", "content": "Error: $e", "type": "text"});
    } finally {
      setState(() { _isLoading = false; });
      _scrollToBottom();
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final topPadding = MediaQuery.of(context).padding.top;
    
    return Scaffold(
      backgroundColor: theme.scaffoldBackgroundColor,
      appBar: PreferredSize(
        preferredSize: Size.fromHeight(_isListening ? 0 : kToolbarHeight),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 300),
          height: _isListening ? 0 : kToolbarHeight + topPadding,
child: Container(
            color: Colors.transparent, // AppBar background was transparent
            child: SafeArea(
              bottom: false,
              child: Stack(
                children: [
                   // 1. LEFT: System Stats Pill
                   Align(
                     alignment: Alignment.centerLeft,
                     child: Padding(
                       padding: const EdgeInsets.symmetric(horizontal: 16),
                       child: const SystemStatsPill(),
                     ),
                   ),

                   // 2. CENTER: Dynamic Title
                   Align(
                     alignment: Alignment.center,
                     child: TypewriterText(
                        text: _modeLabel,
                        style: GoogleFonts.getFont('JetBrains Mono', fontSize: 16, fontWeight: FontWeight.bold),
                        duration: const Duration(milliseconds: 50),
                     ),
                   ),

                   // 3. RIGHT: Action Buttons
                   Align(
                     alignment: Alignment.centerRight,
                     child: Row(
                       mainAxisSize: MainAxisSize.min,
                       children: [
                          IconButton(
                            icon: const Icon(Icons.call, color: Colors.cyanAccent),
                            onPressed: _navigateToDialer,
                          ),
                          if (Provider.of<AuthService>(context).isAdmin)
                            IconButton(
                              icon: const Icon(Icons.security, color: Colors.redAccent),
                              onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const AdminDashboard())),
                            ),
                          IconButton(
                            icon: const Icon(Icons.settings_outlined),
                            onPressed: _showSettingsDialog,
                          ),
                          const SizedBox(width: 8), // Right Padding
                       ],
                     ),
                   ),
                ],
              ),
            ),
          ),
        ),
      ),
      body: Stack(
        children: [
          RepaintBoundary(
             child: RainOverlay(type: _getRainForMode(_currentMode)),
          ),
          SafeArea(
            child: Column(
              children: [
                Expanded(child: _buildBodyContent()),
                
                // Wrap bottom controls to avoid overflow (RenderFlex)
                SingleChildScrollView(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      if (_currentMode == 'writing') 
                        WritingControls(
                          isNSFW: _isNSFW, 
                          onNSFWToggle: (v) => setState(() {
                            _isNSFW = v;
                            _addSystemMessageForMode('writing');
                          }),
                          onUpdate: (persona, style) => setState(() {
                            _writingPersona = persona;
                            _writingStyle = style;
                          }),
                        ),
                      if (_currentMode == 'coding' || _currentMode == 'hacking')
                        CodingControls(onModelChanged: (m) {}, mode: _currentMode), 
                      if (_currentMode == 'image')
                        ImageControls(
                          onUpdate: (pipeline, subtype, ratio, seed) {
                            setState(() {
                              _imagePipeline = pipeline;
                              _imageSubtype = subtype;
                              _imageRatio = ratio;
                              _imageSeed = seed;
                            });
                          },
                        ),
      
                      // Mode Selector (Bottom Left)
                      Align(
                        alignment: Alignment.centerLeft,
                        child: Padding(
                          padding: const EdgeInsets.only(left: 16, bottom: 8),
                          child: ModeSelectorPill(
                            currentModeLabel: _modeLabel, 
                            onTap: _openModeSelector
                          ),
                        ),
                      ),
      
                      // Input (Hide for some modes)
                      if (!['qr', 'newspaper', 'surgeon', 'movie'].contains(_currentMode))
                        ChatInput(
                          controller: _controller,
                          isLoading: _isLoading,
                          onSubmitted: _handleSubmitted,
                          onMicPressed: _toggleRecording,
                          onMicLongPressChanged: (isRecording) {
                            if (isRecording) {
                              _startRecording();
                            } else {
                              _stopRecording();
                            }
                          },
                          onMicLocked: () {
                             // Just update state, listening continues from LongPress logic
                             setState(() => _isListening = true);
                          },
                          onStopRecording: () {
                            _speech.stop();
                            setState(() => _isListening = false);
                          },
                        )
                    ],
                  ),
                )
              ],
            ),
          ),
        ],
      ),
    );
  }

  void _showSettingsDialog() {
    Navigator.push(context, MaterialPageRoute(builder: (_) => const SettingsScreen()));
  }

  Widget _buildBodyContent() {
    // Special Views
    if (_currentMode == 'qr') return const QRView();
    if (_currentMode == 'movie') return const MovieView();
    if (_currentMode == 'newspaper') return const NewspaperView();
    if (_currentMode == 'surgeon') return const SurgeonView();
    if (_currentMode == 'voice') return _buildVoiceView();

    // Default Chat List
    return ListView.builder(
      controller: _scrollController,
      padding: const EdgeInsets.all(16),
      itemCount: _messages.length,
      itemBuilder: (ctx, i) {
        final msg = _messages[i];
        final isUser = msg['role'] == 'user';
        final isSystem = msg['role'] == 'system';
        
        // Only animate the very last message, and only if it's not from the user
        final shouldAnimate = (i == _messages.length - 1) && !isUser;

        if (isSystem) return Center(child: Padding(padding: const EdgeInsets.all(8), child: Text(msg['content'], style: const TextStyle(color: Colors.grey, fontSize: 12))));
        
        return Align(
          alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
          child: Container(
            margin: const EdgeInsets.symmetric(vertical: 4),
            padding: const EdgeInsets.all(12),
            constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.75),
            decoration: BoxDecoration(
              color: isUser ? const Color(0xFF1E1E1E).withValues(alpha: 0.8) : const Color(0xFF000000).withValues(alpha: 0.6), // Pure black glass
              border: Border.all(color: Colors.white12), // Mirror frame style
              borderRadius: BorderRadius.circular(12),
            ),
            // Use the new optimized widget
            child: MessageBubble(
              message: msg,
              mode: _currentMode,
              animate: shouldAnimate,
            ),
          ),
        );
      },
    );
  }
  Widget _buildVoiceView() => const Center(child: Text("Voice Mode Active"));

  void _navigateToDialer() {
    Navigator.of(context).push(
      PageRouteBuilder(
        pageBuilder: (context, animation, secondaryAnimation) => const DialerScreen(),
        transitionsBuilder: (context, animation, secondaryAnimation, child) {
          const begin = Offset(-1.0, 0.0); // Start from Left
          const end = Offset.zero;
          const curve = Curves.fastOutSlowIn;

          var tween = Tween(begin: begin, end: end).chain(CurveTween(curve: curve));

          return SlideTransition(
            position: animation.drive(tween),
            child: child,
          );
        },
        transitionDuration: const Duration(milliseconds: 200), // Fast
      ),
    );
  }
}
