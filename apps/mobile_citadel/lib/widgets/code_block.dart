import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';

/// Code block widget with syntax highlighting and copy button
/// Code block widget with syntax highlighting and copy button
class CodeBlock extends StatefulWidget {
  final String code;
  final String? language;
  final bool showLineNumbers;

  const CodeBlock({
    super.key,
    required this.code,
    this.language,
    this.showLineNumbers = true,
  });

  @override
  State<CodeBlock> createState() => _CodeBlockState();
}

class _CodeBlockState extends State<CodeBlock> {
  late List<TextSpan> _highlightedSpans;

  @override
  void initState() {
    super.initState();
    _computeSpans();
  }

  @override
  void didUpdateWidget(CodeBlock oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.code != oldWidget.code || widget.language != oldWidget.language) {
      _computeSpans();
    }
  }

  void _computeSpans() {
    // Determine brightness from context is tricky in initState, 
    // but simplified logic assumes pure colors or we can update in build if needed.
    // For perf, we'll do the heavy regex here.
    // NOTE: TextSpan styles need context for Theme usually, 
    // but here we used hardcoded colors based on isDark flag passed to helper.
    // We'll defer actual Color object creation to build or pass a flag? 
    // Actually, passing 'isDark' to _highlightCode requires context.
    // Optimization: We'll calculate the abstract ranges here, or just keep it simple:
    // We'll invoke _highlightCode in build ONLY if it changed, using Memoization?
    // No, standard State approach:
    // We will compute spans in 'build' but only if code changed? 
    // Actually, simply wrapping in RepaintBoundary is often enough for scrolling.
    // But let's cache the list of spans to be safe.
  }
  
  // Revised approach:
  // Since we need 'context' to know if it's dark mode, we can't do it easily in initState 
  // without 'didChangeDependencies'. 
  // BETTER: Just wrap the expensive part in a RepaintBoundary and KeepAlive.
  // The regex itself is fast enough for 144hz IF it's not repainted every pixel of scroll.
  // Let's rely on RepaintBoundary first.

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final lines = widget.code.split('\n');

    return RepaintBoundary(
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 8),
        decoration: BoxDecoration(
          color: isDark ? const Color(0xFF1E1E1E) : const Color(0xFFF5F5F5),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: isDark ? Colors.white12 : Colors.black12,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header with language and copy button
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              decoration: BoxDecoration(
                color: isDark ? const Color(0xFF2D2D2D) : const Color(0xFFE8E8E8),
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(8),
                  topRight: Radius.circular(8),
                ),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    widget.language?.toUpperCase() ?? 'CODE',
                    style: GoogleFonts.jetBrainsMono(
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      color: isDark ? Colors.white70 : Colors.black54,
                    ),
                  ),
                  GestureDetector(
                    onTap: () {
                      Clipboard.setData(ClipboardData(text: widget.code));
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text('Code copied to clipboard!'),
                          duration: Duration(seconds: 1),
                        ),
                      );
                    },
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: isDark ? Colors.white10 : Colors.black.withValues(alpha: 0.05),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            Icons.copy,
                            size: 14,
                            color: isDark ? Colors.white70 : Colors.black54,
                          ),
                          const SizedBox(width: 4),
                          Text(
                            'Copy',
                            style: GoogleFonts.jetBrainsMono(
                              fontSize: 11,
                              color: isDark ? Colors.white70 : Colors.black54,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
            // Code content
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              physics: const ClampingScrollPhysics(), // Better for nested scrolls
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Line numbers
                    if (widget.showLineNumbers)
                      Padding(
                        padding: const EdgeInsets.only(right: 12),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.end,
                          children: List.generate(lines.length, (i) {
                            return Text(
                              '${i + 1}',
                              style: GoogleFonts.jetBrainsMono(
                                fontSize: 13,
                                color: isDark ? Colors.white24 : Colors.black26,
                                height: 1.5,
                              ),
                            );
                          }),
                        ),
                      ),
                    // Code text with basic syntax highlighting
                    SelectableText.rich(
                      TextSpan(
                        children: _highlightCode(widget.code, isDark),
                        style: GoogleFonts.jetBrainsMono(
                          fontSize: 13,
                          height: 1.5,
                          color: isDark ? Colors.white : Colors.black87,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// Basic syntax highlighting
  List<TextSpan> _highlightCode(String code, bool isDark) {
    final spans = <TextSpan>[];
    
    // Define color scheme
    final keywordColor = isDark ? const Color(0xFF569CD6) : const Color(0xFF0000FF);
    final stringColor = isDark ? const Color(0xFFCE9178) : const Color(0xFFA31515);
    final commentColor = isDark ? const Color(0xFF6A9955) : const Color(0xFF008000);
    final numberColor = isDark ? const Color(0xFFB5CEA8) : const Color(0xFF098658);
    final functionColor = isDark ? const Color(0xFFDCDCAA) : const Color(0xFF795E26);
    final defaultColor = isDark ? Colors.white : Colors.black87;

    // Common keywords
    final keywords = {
      'function', 'const', 'let', 'var', 'if', 'else', 'for', 'while', 'return',
      'class', 'extends', 'import', 'export', 'from', 'async', 'await', 'try',
      'catch', 'throw', 'new', 'this', 'super', 'null', 'undefined', 'true', 'false',
      'def', 'print', 'self', 'None', 'True', 'False', 'and', 'or', 'not', 'in',
      'final', 'void', 'int', 'String', 'bool', 'double', 'List', 'Map', 'Future',
    };

    // Simple regex patterns
    final patterns = [
      (RegExp(r'//.*$', multiLine: true), commentColor),
      (RegExp(r'#.*$', multiLine: true), commentColor),
      (RegExp(r'/\*[\s\S]*?\*/'), commentColor),
      (RegExp(r"'[^']*'"), stringColor),
      (RegExp(r'"[^"]*"'), stringColor),
      (RegExp(r'`[^`]*`'), stringColor),
      (RegExp(r'\b\d+\.?\d*\b'), numberColor),
      (RegExp(r'\b(' + keywords.join('|') + r')\b'), keywordColor),
      (RegExp(r'\b[A-Za-z_]\w*(?=\s*\()'), functionColor),
    ];

    // Find all matches
    final matches = <(int, int, Color)>[];
    for (final (pattern, color) in patterns) {
      for (final match in pattern.allMatches(code)) {
        matches.add((match.start, match.end, color));
      }
    }

    // Sort by start position
    matches.sort((a, b) => a.$1.compareTo(b.$1));

    // Build spans, avoiding overlaps
    int currentIndex = 0;
    final usedRanges = <(int, int)>[];

    for (final (start, end, color) in matches) {
      // Skip if overlapping with a used range
      if (usedRanges.any((r) => start < r.$2 && end > r.$1)) continue;

      // Add plain text before this match
      if (start > currentIndex) {
        spans.add(TextSpan(
          text: code.substring(currentIndex, start),
          style: TextStyle(color: defaultColor),
        ));
      }

      // Add highlighted text
      spans.add(TextSpan(
        text: code.substring(start, end),
        style: TextStyle(color: color),
      ));

      usedRanges.add((start, end));
      currentIndex = end;
    }

    // Add remaining text
    if (currentIndex < code.length) {
      spans.add(TextSpan(
        text: code.substring(currentIndex),
        style: TextStyle(color: defaultColor),
      ));
    }

    return spans.isEmpty ? [TextSpan(text: code, style: TextStyle(color: defaultColor))] : spans;
  }
}

/// Parse markdown-style code blocks and return widgets
List<Widget> parseCodeBlocks(String text) {
  final widgets = <Widget>[];
  final codeBlockPattern = RegExp(r'```(\w*)\n([\s\S]*?)```');
  
  int lastEnd = 0;
  for (final match in codeBlockPattern.allMatches(text)) {
    // Add text before code block
    if (match.start > lastEnd) {
      final before = text.substring(lastEnd, match.start).trim();
      if (before.isNotEmpty) {
        widgets.add(SelectableText(before));
      }
    }
    
    // Add code block
    final language = match.group(1);
    final code = match.group(2)?.trim() ?? '';
    widgets.add(CodeBlock(code: code, language: language));
    
    lastEnd = match.end;
  }
  
  // Add remaining text
  if (lastEnd < text.length) {
    final after = text.substring(lastEnd).trim();
    if (after.isNotEmpty) {
      widgets.add(SelectableText(after));
    }
  }
  
  return widgets;
}
