import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../widgets/typewriter_text.dart';
import 'image_viewer.dart';
import '../widgets/code_block.dart';

class MessageBubble extends StatefulWidget {
  final Map<String, dynamic> message;
  final bool animate;
  final String mode;

  const MessageBubble({
    super.key,
    required this.message,
    required this.animate,
    required this.mode,
  });

  @override
  State<MessageBubble> createState() => _MessageBubbleState();
}

class _MessageBubbleState extends State<MessageBubble> with AutomaticKeepAliveClientMixin {
  @override
  bool get wantKeepAlive => true; // Keeps widget alive off-screen

  @override
  Widget build(BuildContext context) {
    super.build(context); // Must call super
    final msg = widget.message;
    final content = msg['content'] ?? '';

    // --- IMAGE TYPE ---
    if (msg['type'] == 'image') {
      final url = content as String;
      final api = Provider.of<ApiService>(context, listen: false);
      
      // Resolve relative URLs
      if (url.startsWith('/')) {
        return FutureBuilder<String>(
          future: api.resolveUrl(url),
          builder: (ctx, snap) {
            if (snap.hasData) {
              return GestureDetector(
                onTap: () => ImageViewer.show(context, snap.data!),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(8),
                  child: Image.network(snap.data!, fit: BoxFit.cover),
                ),
              );
            }
            return const SizedBox(height: 200, child: Center(child: CircularProgressIndicator()));
          },
        );
      }
      return GestureDetector(
        onTap: () => ImageViewer.show(context, url),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(8),
          child: Image.network(url, fit: BoxFit.cover),
        ),
      );
    }
    
    // --- IMAGE PLACEHOLDER ---
    if (msg['type'] == 'image_placeholder') {
      double aspectRatio = 1.0;
      try {
        final parts = (msg['ratio'] as String).split(':');
        if (parts.length == 2) aspectRatio = double.parse(parts[0]) / double.parse(parts[1]);
      } catch(e) {}
      
      int percent = msg['percent'] ?? 0;
      
      return AspectRatio(
        aspectRatio: aspectRatio,
        child: Container(
          decoration: BoxDecoration(
            color: Colors.white10,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Colors.white24)
          ),
          child: Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                CircularProgressIndicator(value: percent > 0 ? percent / 100.0 : null, color: Colors.white),
                if (percent > 0) ...[
                  const SizedBox(height: 8),
                  Text("$percent%", style: const TextStyle(color: Colors.white, fontSize: 12))
                ],
                const SizedBox(height: 8),
                Text(
                  msg['statusText'] ?? "Initializing...", 
                  style: const TextStyle(color: Colors.white70, fontSize: 10),
                  textAlign: TextAlign.center,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 12),
                TextButton.icon(
                  onPressed: () {
                     final api = Provider.of<ApiService>(context, listen: false);
                     api.cancelImageGeneration();
                     setState(() {
                        msg['content'] = 'Generation Cancelled';
                        msg['type'] = 'text'; // Convert to text message
                     });
                  },
                  icon: const Icon(Icons.cancel, size: 14, color: Colors.redAccent),
                  label: const Text("Cancel", style: TextStyle(color: Colors.redAccent, fontSize: 12)),
                  style: TextButton.styleFrom(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                    backgroundColor: Colors.black26,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20))
                  )
                )
              ]
            ),
          ),
        ),
      );
    }
    
    // --- REASONING MODE ---
    if (widget.mode == 'reasoning' && msg['role'] != 'user') {
      final parts = content.split('</think>');
      String thinkContent = "";
      String answerContent = "";
      
      if (parts.length > 1) {
        thinkContent = parts[0].replaceAll('<think>', '').trim();
        answerContent = parts.sublist(1).join('</think>').trim();
      } else {
        if (content.contains('<think>')) { 
           thinkContent = content.replaceAll('<think>', '').trim();
        } else {
           answerContent = content;
        }
      }
      
      if (thinkContent.isNotEmpty) {
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              margin: const EdgeInsets.only(bottom: 8),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.05),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.white10)
              ),
              child: Theme(
                data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
                child: ExpansionTile(
                  initiallyExpanded: true, 
                  title: Row(
                    children: [
                      const Icon(Icons.psychology, size: 16, color: Colors.white54),
                      const SizedBox(width: 8),
                      Text("Reasoning Process", style: GoogleFonts.outfit(fontSize: 12, color: Colors.white54)),
                    ],
                  ),
                  children: [
                    Padding(
                      padding: const EdgeInsets.all(12),
                      child: TypewriterText(
                        text: thinkContent,
                        style: GoogleFonts.jetBrainsMono(fontSize: 12, color: Colors.white60),
                        duration: widget.animate ? const Duration(milliseconds: 1) : Duration.zero, 
                      ),
                    )
                  ],
                ),
              ),
            ),
            if (answerContent.isNotEmpty)
              TypewriterText(
                text: answerContent,
                style: GoogleFonts.outfit(color: Colors.white),
                duration: widget.animate ? const Duration(milliseconds: 5) : Duration.zero,
              )
          ],
        );
      }
    }
    
    // --- TEXT TYPE ---
    // Check if content has code blocks (```...```)
    if (content.contains('```') && ['coding', 'hacking'].contains(widget.mode)) {
      final widgets = parseCodeBlocks(content);
      if (widgets.length == 1) {
        return widgets.first;
      }
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: widgets,
      );
    }
    
    return TypewriterText(
      text: content, 
      style: GoogleFonts.outfit(color: Colors.white),
      duration: widget.animate ? const Duration(milliseconds: 5) : Duration.zero,
    );
  }
}
