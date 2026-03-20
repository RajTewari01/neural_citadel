import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class ModeSelectorPill extends StatelessWidget {
  final String currentModeLabel;
  final VoidCallback onTap;

  const ModeSelectorPill({
    Key? key,
    required this.currentModeLabel,
    required this.onTap,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    // Gradient for the pill to give it a premium look (Cyberpunk-ish)
    final Gradient pillGradient = isDark 
        ? const LinearGradient(
            colors: [Color(0xFF2C1A4D), Color(0xFF4A1448)], // Deep purple/red
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          )
        : LinearGradient(
            colors: [Colors.grey[200]!, Colors.grey[300]!],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          );

    return Align(
      alignment: Alignment.centerLeft,
      child: Padding(
        padding: const EdgeInsets.only(left: 16, bottom: 8),
        child: GestureDetector(
          onTap: onTap,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            decoration: BoxDecoration(
              gradient: pillGradient,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(
                color: Theme.of(context).dividerColor.withOpacity(0.1),
                width: 1,
              ),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.2),
                  blurRadius: 4,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                _getIconForMode(currentModeLabel),
                const SizedBox(width: 8),
                Text(
                  currentModeLabel,
                  style: GoogleFonts.getFont('Outfit', 
                    fontSize: 14, 
                    fontWeight: FontWeight.w600,
                    color: isDark ? Colors.white : Colors.black87,
                  ),
                ),
                const SizedBox(width: 4),
                Icon(
                  Icons.arrow_drop_down_rounded, 
                  color: isDark ? Colors.white70 : Colors.black54,
                  size: 20,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
  
  Widget _getIconForMode(String label) {
    IconData icon;
    Color color = Colors.white;
    
    // Simple parsing since we pass the label, or passed id would be better but label works for display
    if (label.contains("Image")) { icon = Icons.image; color = Colors.purpleAccent; }
    else if (label.contains("Reasoning")) { icon = Icons.psychology; color = Colors.blueAccent; }
    else if (label.contains("Dev") || label.contains("Coding")) { icon = Icons.code; color = const Color(0xFF00FF9D); }
    else if (label.contains("Hacking")) { icon = Icons.terminal; color = Colors.redAccent; }
    else if (label.contains("Writer")) { icon = Icons.edit_note; color = Colors.amberAccent; }
    else if (label.contains("Movie")) { icon = Icons.movie; color = Colors.orangeAccent; }
    else if (label.contains("QR")) { icon = Icons.qr_code; color = Colors.white; }
    else if (label.contains("Newspaper")) { icon = Icons.newspaper; color = Colors.pinkAccent; }
    else { icon = Icons.chat_bubble_outline; color = Colors.white; }
    
    return Icon(icon, size: 16, color: color);
  }
}
