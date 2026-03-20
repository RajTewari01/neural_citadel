import 'dart:async';
import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'dart:math' as math;

class HelpCenterScreen extends StatefulWidget {
  const HelpCenterScreen({super.key});

  @override
  State<HelpCenterScreen> createState() => _HelpCenterScreenState();
}

class _HelpCenterScreenState extends State<HelpCenterScreen> with SingleTickerProviderStateMixin {
  final ScrollController _scrollController = ScrollController();
  final TextEditingController _searchController = TextEditingController();
  String _searchQuery = "";
  final FocusNode _searchFocus = FocusNode();
  
  // V15: Exclusive Expansion Logic
  int? _expandedIndex; 
  
  // Animation for "Living" Orbs
  late AnimationController _orbController;
  late Animation<Color?> _topOrbColor;
  late Animation<Color?> _bottomOrbColor;
  bool _isVisible = true; // Optimization Check

  // V15: MASSIVE KNOWLEDGE BASE (30+ Items, No God Mode)
  final List<Map<String, dynamic>> _faqs = [
    // --- ESSENTIALS ---
    {
      "q": "What is Neural Citadel?",
      "a": "Neural Citadel is a secure, local-first multimodal AI client. It connects to your personal server to run advanced LLMs, ensuring total data privacy.",
      "icon": Icons.security
    },
    {
      "q": "Is my data sent to the cloud?",
      "a": "No. All text processing happens on your local server. Images may use external APIs depending on your configuration, but chat logs remain encrypted on your device.",
      "icon": Icons.cloud_off
    },
    {
      "q": "Do I need an internet connection?",
      "a": "Yes, a local Wi-Fi connection to your host server is required. The app enables offline history viewing, but generation requires a live link.",
      "icon": Icons.wifi
    },
    {
      "q": "How do I create an account?",
      "a": "Accounts are created by the server administrator. Contact your admin for an invite code or credentials.",
      "icon": Icons.person_add
    },
    {
      "q": "Is Neural Citadel free?",
      "a": "The client software is open-source. Server costs depend on your hardware hosting the models.",
      "icon": Icons.attach_money
    },

    // --- CHAT & MODELS ---
    {
      "q": "How do I switch AI Models?",
      "a": "Tap the model name indicator (e.g., 'Llama 3') in the bottom-left of the chat screen. Select from the available list configured on your server.",
      "icon": Icons.swap_horiz
    },
    {
      "q": "What is 'Reasoning Mode'?",
      "a": "Reasoning Mode activates chain-of-thought processing. The AI will 'think' out loud before answering, improving accuracy for complex logic puzzles.",
      "icon": Icons.psychology
    },
    {
      "q": "Can the AI write code?",
      "a": "Yes. Switch to the 'Coding' persona for optimized output. Resulting code blocks function with syntax highlighting and a copy button.",
      "icon": Icons.terminal
    },
    {
      "q": "How do I clear chat history?",
      "a": "Go to the History tab, press and hold a session, and tap 'Delete'. Or use the 'Clear Context' button in the chat menu.",
      "icon": Icons.delete_sweep
    },
    {
      "q": "Why is the AI responding slowly?",
      "a": "Response speed depends on your server's GPU. Heavy models (70B+) will key slower than lighter ones (8B).",
      "icon": Icons.speed
    },

    // --- VOICE COMMANDER ---
    {
      "q": "How do I use Voice Mode?",
      "a": "Tap and hold the microphone icon. Release to send. For hands-free, drag the icon UP to lock it.",
      "icon": Icons.mic
    },
    {
      "q": "What is 'Auto-Listen'?",
      "a": "Enabled in Settings, this allows the app to listen for the wake word 'Hey Citadel' even when you aren't touching the screen.",
      "icon": Icons.hearing
    },
    {
      "q": "Can I change the voice?",
      "a": "Yes. Go to Settings > Voice Output to select between different TTS engines and accents.",
      "icon": Icons.record_voice_over
    },
    {
      "q": "Voice isn't working.",
      "a": "Ensure microphone permissions are granted in Android Settings. Restart the app if the audio engine hangs.",
      "icon": Icons.mic_off
    },
    {
      "q": "Does it support other languages?",
      "a": "Yes. The Whisper engine supports 99+ languages. You can speak in Hindi, Bengali, or French, and it will translate automatically.",
      "icon": Icons.translate
    },

    // --- TOOLS & UTILITIES ---
    {
      "q": "How to use Image Surgeon?",
      "a": "Type '/surgeon' in chat or access via the Tools menu. Upload a photo, then prompt to 'remove background' or 'replace X with Y'.",
      "icon": Icons.content_cut
    },
    {
      "q": "Movie Downloader Usage",
      "a": "Paste a magnet link into the chat. The server handles the download. Check progress in the Tools > Downloads section.",
      "icon": Icons.movie
    },
    {
      "q": "What is the QR Generator?",
      "a": "A privacy-focused QR tool. Enter text or URLs to generate codes instantly on-device.",
      "icon": Icons.qr_code
    },
    {
      "q": "Can I generate images?",
      "a": "Yes. Start your prompt with 'Generate an image of...' or use the '/imagine' command.",
      "icon": Icons.image
    },
    {
      "q": "Newspaper Feature",
      "a": "Ask for 'Daily News' to receive a summarization of top RSS feeds formatted as a digital newspaper.",
      "icon": Icons.newspaper
    },

    // --- PRIVACY & SECURITY ---
    {
      "q": "Where are chats stored?",
      "a": "Chats are stored in a local SQLite database on your phone (`citadel_secure.db`) and synced to your private server.",
      "icon": Icons.storage
    },
    {
      "q": "Is encryption used?",
      "a": "Yes. All network traffic is encrypted via HTTPS (if configured) or secure WebSocket tunnels.",
      "icon": Icons.lock
    },
    {
      "q": "Can I export my data?",
      "a": "Currently, you can copy individual chats. Full JSON export is coming in v2.0.",
      "icon": Icons.download
    },
    {
      "q": "How do I logout?",
      "a": "Go to Settings > Profile (Top Card) > Tap the Logout icon. This wipes local session keys.",
      "icon": Icons.logout
    },
    {
      "q": "What permissions are needed?",
      "a": "Microphone (Voice), Storage (Images), and Notification (Alerts). Location is NOT required.",
      "icon": Icons.verified_user
    },

    // --- TROUBLESHOOTING ---
    {
      "q": "Error 503: Service Unavailable",
      "a": "Your server is offline or unreachable. Check if the Python backend is running.",
      "icon": Icons.error_outline
    },
    {
      "q": "App crashes on startup",
      "a": "Clear App Data in Android Settings. Only local cache will be reset; server data is safe.",
      "icon": Icons.restart_alt
    },
    {
      "q": "Images aren't loading",
      "a": "Ensure port 8181 (Static File Server) is open on your host machine firewall.",
      "icon": Icons.image_not_supported
    },
    {
      "q": "Battery drain issues",
      "a": "Disable 'Auto-Listen' and 'High-Fidelity Animations' in Settings to save power.",
      "icon": Icons.battery_alert
    },
    {
      "q": "How to report a bug?",
      "a": "Shake your phone vigorously for 3 seconds. An automated diagnostic report will be generated.",
      "icon": Icons.bug_report
    },
    {
      "q": "Contact Support",
      "a": "Use the 'Live Neural Uplink' below to contact the development team directly.",
      "icon": Icons.support_agent
    },
  ];

  @override
  void initState() {
    super.initState();
    _orbController = AnimationController(vsync: this, duration: const Duration(seconds: 10))..repeat(reverse: true);
    
    _topOrbColor = TweenSequence<Color?>([
      TweenSequenceItem(weight: 1.0, tween: ColorTween(begin: const Color(0xFFFF003C), end: const Color(0xFF7C4DFF))),
      TweenSequenceItem(weight: 1.0, tween: ColorTween(begin: const Color(0xFF7C4DFF), end: const Color(0xFF00F0FF))),
      TweenSequenceItem(weight: 1.0, tween: ColorTween(begin: const Color(0xFF00F0FF), end: const Color(0xFFFF003C))),
    ]).animate(_orbController);

     _bottomOrbColor = TweenSequence<Color?>([
      TweenSequenceItem(weight: 1.0, tween: ColorTween(begin: const Color(0xFF00F0FF), end: const Color(0xFF00E5FF))),
      TweenSequenceItem(weight: 1.0, tween: ColorTween(begin: const Color(0xFF00E5FF), end: const Color(0xFFFF003C))),
      TweenSequenceItem(weight: 1.0, tween: ColorTween(begin: const Color(0xFFFF003C), end: const Color(0xFF00F0FF))),
    ]).animate(_orbController);
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    // V15.2: Deep Sleep - Pause animation if not top route
    final route = ModalRoute.of(context);
    if (route != null && !route.isCurrent) {
      if (_orbController.isAnimating) _orbController.stop();
    }
  }

  @override
  void deactivate() {
    // V15.2: Deep Sleep - Stop immediately on pop/push
    _orbController.stop(); 
    super.deactivate();
  }

  @override
  void dispose() {
    // Aggressive Disposal
    _orbController.dispose();
    _scrollController.dispose();
    _searchController.dispose();
    _searchFocus.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    const Color bgBlack = Color(0xFF05050A);

    return Scaffold(
      backgroundColor: bgBlack,
      body: Stack(
        children: [
          // 1. Orbs (Lower opacity)
          RepaintBoundary(
            child: AnimatedBuilder(
              animation: _orbController,
              builder: (context, child) {
                return Stack(
                  children: [
                    Positioned(
                      top: -150, left: -100,
                      child: Container(
                        width: 500, height: 500,
                        decoration: BoxDecoration(shape: BoxShape.circle, gradient: RadialGradient(colors: [_topOrbColor.value!.withOpacity(0.15), Colors.transparent])),
                      ),
                    ),
                    Positioned(
                      bottom: -150, right: -100,
                      child: Container(
                        width: 500, height: 500,
                        decoration: BoxDecoration(shape: BoxShape.circle, gradient: RadialGradient(colors: [_bottomOrbColor.value!.withOpacity(0.15), Colors.transparent])),
                      ),
                    ),
                  ],
                );
              },
            ),
          ),

          // 2. Content
          CustomScrollView(
            controller: _scrollController,
            physics: const BouncingScrollPhysics(),
            slivers: [
              SliverAppBar(
                backgroundColor: Colors.transparent,
                expandedHeight: 80,
                floating: true, pinned: false,
                leading: const BackButton(color: Colors.white),
                flexibleSpace: FlexibleSpaceBar(
                  centerTitle: true,
                  title: Text(
                    "KNOWLEDGE BASE",
                    style: GoogleFonts.orbitron(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold, letterSpacing: 2),
                  ),
                ),
              ),

              SliverPersistentHeader(
                pinned: true,
                delegate: _StickySearchDelegate(
                  maxHeight: 110, minHeight: 110,
                  child: _buildStickySearchArea(context),
                ),
              ),

              SliverPadding(
                padding: const EdgeInsets.only(top: 20, bottom: 40),
                sliver: SliverList(
                  delegate: SliverChildBuilderDelegate(
                    (context, index) {
                      if (index >= _faqs.length) return _buildContactSection();
                      final faq = _faqs[index];
                      // Filter
                      if (_searchQuery.isNotEmpty && !faq['q'].toString().toLowerCase().contains(_searchQuery.toLowerCase())) {
                        return const SizedBox.shrink();
                      }
                      return _buildCyberpunkTile(faq, index);
                    },
                    childCount: _faqs.length + 1,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStickySearchArea(BuildContext context) {
    // V16: STABILITY FIX - Removed BackdropFilter (Crash Prone)
    const Color appBackground = Color(0xFF05050A); 
    
    return Container(
        color: appBackground.withOpacity(0.95), // High opacity instead of blur
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 20),
        alignment: Alignment.center,
        child: Container(
            height: 55,
            decoration: BoxDecoration(
              // THE BORDER GRADIENT
              gradient: const LinearGradient(colors: [Color(0xFFFF003C), Color(0xFF00F0FF)]),
              borderRadius: BorderRadius.circular(30),
            ),
            padding: const EdgeInsets.all(2), // 2px Border Width
            child: Container(
              // THE INNER FILL: MUST MATCH APP BACKGROUND EXACTLY
              decoration: BoxDecoration(
                color: appBackground, // V16: Exact Match
                borderRadius: BorderRadius.circular(28),
              ),
              child: Row(
                children: [
                  const SizedBox(width: 16),
                  const Icon(Icons.search, color: Colors.white70, size: 24),
                  const SizedBox(width: 12),
                  Expanded(
                    child: TextField(
                      controller: _searchController,
                      focusNode: _searchFocus,
                      style: GoogleFonts.outfit(color: Colors.white, fontSize: 16),
                      onChanged: (val) => setState(() => _searchQuery = val),
                      cursorColor: const Color(0xFF00F0FF),
                      decoration: const InputDecoration(
                        hintText: "Search Knowledge Base...", 
                        hintStyle: TextStyle(color: Colors.white30),
                        filled: true, // V16: Explicit fill
                        fillColor: Colors.transparent, // V16: Explicit transparent
                        border: InputBorder.none,
                        focusedBorder: InputBorder.none,
                        enabledBorder: InputBorder.none,
                        errorBorder: InputBorder.none,
                        disabledBorder: InputBorder.none,
                        contentPadding: EdgeInsets.zero,
                        isCollapsed: true,
                      ),
                    ),
                  ),
                  const SizedBox(width: 16), // V16: Right padding to prevent stretch look
                ],
              ),
            ),
          ),
        );
  }

  Widget _buildCyberpunkTile(Map<String, dynamic> faq, int index) {
    // V15: EXCLUSIVE EXPANSION (Open one, close others)
    bool isExpanded = _expandedIndex == index;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 300),
        decoration: BoxDecoration(
          color: const Color(0xFF111111),
          borderRadius: BorderRadius.circular(12),
          // V15: Unified Gradient Border Style
          border: isExpanded ? Border.all(color: Colors.transparent) : Border.all(color: Colors.white.withOpacity(0.05)),
          gradient: isExpanded ? const LinearGradient(colors: [Color(0xFFFF003C), Color(0xFF00F0FF)]) : null,
          boxShadow: isExpanded ? [
             const BoxShadow(color: Color(0xFFFF003C), blurRadius: 8, spreadRadius: -4),
             const BoxShadow(color: Color(0xFF00F0FF), blurRadius: 8, spreadRadius: -4, offset: Offset(4,4)),
          ] : [],
        ),
        padding: isExpanded ? const EdgeInsets.all(1.5) : EdgeInsets.zero,
        child: Container(
          decoration: BoxDecoration(
            color: Colors.black, // Pure Black inside expanded too for consistency
            borderRadius: BorderRadius.circular(isExpanded ? 11 : 12),
          ),
          child: Column(
             children: [
               ListTile(
                 leading: Icon(faq['icon'], color: isExpanded ? const Color(0xFF00F0FF) : Colors.white54, size: 20),
                 title: Text(faq['q'], style: GoogleFonts.outfit(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 15)),
                 trailing: Icon(
                   isExpanded ? Icons.keyboard_arrow_up : Icons.keyboard_arrow_down, 
                   color: isExpanded ? const Color(0xFFFF003C) : Colors.white30
                 ),
                 onTap: () {
                   setState(() {
                     if (_expandedIndex == index) {
                       _expandedIndex = null; // Close
                     } else {
                       _expandedIndex = index; // Open & Close others
                     }
                   });
                 },
               ),
               // Custom Content Expansion (Avoiding ExpansionTile for exclusive control)
               AnimatedCrossFade(
                 firstChild: Container(),
                 secondChild: Padding(
                   padding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
                   child: Text(
                      faq['a'],
                      style: GoogleFonts.outfit(color: Colors.white70, fontSize: 14, height: 1.5),
                   ),
                 ),
                 crossFadeState: isExpanded ? CrossFadeState.showSecond : CrossFadeState.showFirst,
                 duration: const Duration(milliseconds: 200),
               )
             ],
          ),
        ),
      ),
    );
  }

  Widget _buildContactSection() {
    // V15: "Live Neural Uplink" Redesign
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 40, 20, 40),
      child: Container(
        height: 80,
        decoration: BoxDecoration(
           gradient: const LinearGradient(colors: [Color(0xFFFF003C), Color(0xFF00F0FF)]),
           borderRadius: BorderRadius.circular(16),
           boxShadow: [
              BoxShadow(color: const Color(0xFFFF003C).withOpacity(0.3), blurRadius: 20, offset: const Offset(-5,5)),
              BoxShadow(color: const Color(0xFF00F0FF).withOpacity(0.3), blurRadius: 20, offset: const Offset(5,5)),
           ]
        ),
        padding: const EdgeInsets.all(2),
        child: Container(
          decoration: BoxDecoration(
            color: Colors.black, // Pure Black
            borderRadius: BorderRadius.circular(14),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              Text("LIVE SUPPORT UPLINK", style: GoogleFonts.orbitron(color: Colors.white, fontWeight: FontWeight.bold, letterSpacing: 1)),
              Container(width: 1, height: 40, color: Colors.white10),
              IconButton(onPressed: _launchEmail, icon: const Icon(Icons.mail, color: Color(0xFF00F0FF))),
              IconButton(onPressed: () {}, icon: const Icon(FontAwesomeIcons.discord, color: Color(0xFF7C4DFF))),
            ],
          ),
        ),
      ),
    );
  }

   void _launchEmail() async {
    final Uri emailLaunchUri = Uri(scheme: 'mailto', path: 'support@neuralcitadel.com');
    try { await launchUrl(emailLaunchUri); } catch (_) {}
  }
}

class _StickySearchDelegate extends SliverPersistentHeaderDelegate {
  final Widget child;
  final double maxHeight;
  final double minHeight;
  _StickySearchDelegate({required this.child, required this.maxHeight, required this.minHeight});
  @override
  Widget build(BuildContext context, double shrinkOffset, bool overlapsContent) => SizedBox.expand(child: child);
  @override
  double get maxExtent => maxHeight;
  @override
  double get minExtent => minHeight;
  @override
  bool shouldRebuild(_StickySearchDelegate oldDelegate) => true;
}
