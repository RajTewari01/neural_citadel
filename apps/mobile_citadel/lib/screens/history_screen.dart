import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../services/database_helper.dart';
import '../services/auth_service.dart';
import '../theme/app_theme.dart';
import 'chat_screen.dart';

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  final DatabaseHelper _db = DatabaseHelper.instance;
  List<Map<String, dynamic>> _sessions = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadSessions();
  }

  Future<void> _loadSessions() async {
    final auth = Provider.of<AuthService>(context, listen: false);
    if (!auth.isLoggedIn) return;

    final sessions = await _db.getUserSessions(auth.currentUser!['id'] as int);
    setState(() {
      _sessions = sessions;
      _isLoading = false;
    });
  }

  String _formatDate(String isoString) {
    try {
      final date = DateTime.parse(isoString);
      final now = DateTime.now();
      if (date.year == now.year && date.month == now.month && date.day == now.day) {
        return DateFormat.jm().format(date); // 2:30 PM
      } else if (date.year == now.year) {
        return DateFormat.MMMd().format(date); // Jan 22
      } else {
        return DateFormat.yMMMd().format(date); // Jan 22, 2025
      }
    } catch (e) {
      return '';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black, // Deep black background
      appBar: AppBar(
        title: Text("Neural Memory", style: GoogleFonts.orbitron(letterSpacing: 1)),
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: AppTheme.neonBlue))
          : _sessions.isEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.memory, size: 48, color: Colors.white24),
                      const SizedBox(height: 16),
                      Text("No recorded memories.", style: GoogleFonts.outfit(color: Colors.white54)),
                    ],
                  ),
                )
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: _sessions.length,
                  itemBuilder: (context, index) {
                    final session = _sessions[index];
                    return Dismissible(
                      key: Key(session['id'].toString()),
                      direction: DismissDirection.endToStart,
                      background: Container(
                        margin: const EdgeInsets.only(bottom: 12),
                        decoration: BoxDecoration(
                          color: Colors.red.withOpacity(0.8),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        alignment: Alignment.centerRight,
                        padding: const EdgeInsets.only(right: 20),
                        child: const Icon(Icons.delete, color: Colors.white),
                      ),
                      onDismissed: (direction) async {
                        await _db.deleteSession(session['id']);
                        // Remove from local list instantly
                        setState(() {
                          _sessions.removeAt(index);
                        });
                        ScaffoldMessenger.of(context).showSnackBar(
                           SnackBar(content: Text("Memory erased.", style: GoogleFonts.shareTechMono()))
                        );
                      },
                      child: Container(
                        margin: const EdgeInsets.only(bottom: 12),
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.05),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: Colors.white12),
                        ),
                        child: ListTile(
                          onTap: () {
                             // Navigate to chat with this session
                             Navigator.pushReplacement(
                               context, 
                               MaterialPageRoute(builder: (_) => ChatScreen(mode: session['mode'] ?? 'reasoning', sessionId: session['id']))
                             );
                          },
                          title: Text(
                            session['title'] ?? "Untitled Session",
                            style: GoogleFonts.outfit(color: Colors.white, fontWeight: FontWeight.w500),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                          trailing: Text(
                            _formatDate(session['last_updated']),
                            style: GoogleFonts.jetBrainsMono(color: Colors.white38, fontSize: 12),
                          ),
                          leading: Container(
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              color: AppTheme.neonPurple.withOpacity(0.1),
                              shape: BoxShape.circle,
                            ),
                            child: const Icon(Icons.chat_bubble_outline, color: AppTheme.neonPurple, size: 18),
                          ),
                        ),
                      ),
                    );
                  },
                ),
    );
  }
}
