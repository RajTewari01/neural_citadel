import 'package:flutter/material.dart';
import 'chat_screen.dart';
import 'voice_screen.dart';
import 'phone/dialer_screen.dart';
import '../widgets/newspaper_view.dart';
import '../widgets/surgeon_view.dart';
import '../widgets/movie_view.dart';
import '../widgets/qr_view.dart';
import '../services/theme_provider.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: themeProvider,
      builder: (context, child) {
        final isDark = themeProvider.isDarkMode;
        final bg = isDark ? const Color(0xFF0D0D0D) : const Color(0xFFF5F5F5);
        final textColor = isDark ? Colors.white : Colors.black87;
        final subTextColor = isDark ? Colors.white54 : Colors.black54;
        final accentColor = const Color(0xFF00FF9D);
        final cardColor = isDark ? const Color(0xFF1A1A1A) : Colors.white;
        final borderColor = isDark ? Colors.white10 : Colors.black12;

        return Scaffold(
          backgroundColor: bg,
          body: SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(24.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                   Row(
                     mainAxisAlignment: MainAxisAlignment.spaceBetween,
                     children: [
                       Text(
                        "Neural\nCitadel",
                        style: TextStyle(
                          color: textColor,
                          fontSize: 40,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 1.2,
                          height: 1.1,
                        ),
                      ),
                       IconButton(
                        icon: Icon(Icons.call, color: Colors.cyanAccent),
                        onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const DialerScreen())),
                      ),
                      IconButton(
                        icon: Icon(isDark ? Icons.light_mode : Icons.dark_mode, color: textColor),
                        onPressed: () => themeProvider.toggleTheme(),
                      )
                     ],
                   ),
              const SizedBox(height: 8),
              Row(
                children: [
                   Container(
                     width: 8, height: 8,
                     decoration: BoxDecoration(color: accentColor, shape: BoxShape.circle),
                   ),
                   const SizedBox(width: 8),
                   Text("SYSTEM ONLINE", style: TextStyle(color: subTextColor, fontSize: 12, letterSpacing: 2)),
                ],
              ),
              const SizedBox(height: 48),
              
              Text("SELECT MODULE", style: TextStyle(color: isDark ? Colors.white30 : Colors.black38, fontSize: 12, fontWeight: FontWeight.bold)),
              const SizedBox(height: 16),
              
              Expanded(
                child: GridView.count(
                  crossAxisCount: 2,
                  mainAxisSpacing: 16,
                  crossAxisSpacing: 16,
                  childAspectRatio: 0.85,
                  children: [
                  children: [
                    _buildModuleCard(
                      context, title: "Neural Phone", icon: "📞", color: Colors.cyanAccent,
                      cardColor: cardColor, borderColor: borderColor, textColor: textColor,
                      onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const DialerScreen())),
                    ),
                    _buildModuleCard(
                      context, title: "Talking System", icon: "🎙️", color: Colors.blueAccent,
                      cardColor: cardColor, borderColor: borderColor, textColor: textColor,
                      onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const VoiceScreen())),
                    ),
                    _buildModuleCard(
                      context, title: "Reasoning", icon: "🧠", color: Colors.purpleAccent,
                      cardColor: cardColor, borderColor: borderColor, textColor: textColor,
                      onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ChatScreen(mode: "reasoning"))),
                    ),
                    _buildModuleCard(
                      context, title: "Coding", icon: "💻", color: Colors.greenAccent,
                      cardColor: cardColor, borderColor: borderColor, textColor: textColor,
                      onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ChatScreen(mode: "coding"))),
                    ),
                    _buildModuleCard(
                      context, title: "Hacking", icon: "💀", color: Colors.redAccent,
                      cardColor: cardColor, borderColor: borderColor, textColor: textColor,
                      onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ChatScreen(mode: "hacking"))),
                    ),
                    _buildModuleCard(
                      context, title: "Writing", icon: "✍️", color: Colors.orangeAccent,
                      cardColor: cardColor, borderColor: borderColor, textColor: textColor,
                      onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ChatScreen(mode: "writing"))),
                    ),
                    _buildModuleCard(
                      context, title: "Newspaper", icon: "📰", color: Colors.tealAccent,
                      cardColor: cardColor, borderColor: borderColor, textColor: textColor,
                      onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const NewspaperView())),
                    ),
                     _buildModuleCard(
                      context, title: "Surgeon", icon: "⚕️", color: Colors.redAccent,
                      cardColor: cardColor, borderColor: borderColor, textColor: textColor,
                      onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const SurgeonView())),
                    ),
                     _buildModuleCard(
                      context, title: "Movie DL", icon: "🎬", color: Colors.indigoAccent,
                      cardColor: cardColor, borderColor: borderColor, textColor: textColor,
                      onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const MovieView())),
                    ),
                     _buildModuleCard(
                      context, title: "QR Scanner", icon: "📷", color: Colors.yellowAccent,
                      cardColor: cardColor, borderColor: borderColor, textColor: textColor,
                      onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const QRView())),
                    ),
                    _buildModuleCard(
                      context, title: "Image Gen", icon: "🎨", color: Colors.pinkAccent,
                      cardColor: cardColor, borderColor: borderColor, textColor: textColor,
                      onTap: () => ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Coming Soon"))),
                    ),
                  ].map((w) => w).toList(),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
  );
  }

  Widget _buildModuleCard(BuildContext context, {
    required String title, 
    required String icon, 
    required Color color, 
    required Color cardColor,
    required Color borderColor,
    required Color textColor,
    required VoidCallback onTap
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        decoration: BoxDecoration(
          color: cardColor,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: borderColor),
          boxShadow: [
             BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10, offset: const Offset(0,5))
          ]
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: color.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: Text(icon, style: const TextStyle(fontSize: 32)),
            ),
            const SizedBox(height: 16),
            Text(title, style: TextStyle(color: textColor, fontSize: 16, fontWeight: FontWeight.w600)),
            const SizedBox(height: 4),
            Container(
              width: 30, height: 2,
              color: color.withOpacity(0.5),
            )
          ],
        ),
      ),
    );
  }
}
