import 'package:flutter/material.dart';
import 'dart:async';

class TypewriterText extends StatefulWidget {
  final String text;
  final TextStyle? style;
  final Duration duration;
  final VoidCallback? onComplete;

  const TypewriterText({
    Key? key,
    required this.text,
    this.style,
    this.duration = const Duration(milliseconds: 30),
    this.onComplete,
  }) : super(key: key);

  @override
  _TypewriterTextState createState() => _TypewriterTextState();
}

class _TypewriterTextState extends State<TypewriterText> {
  String _displayedText = "";
  int _currentIndex = 0;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _startAnimation();
  }

  @override
  void didUpdateWidget(TypewriterText oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.text != widget.text) {
      if (widget.text.startsWith(oldWidget.text)) {
        // Simple append optimization
        _startAnimation();
      } else {
        // Reset
        _displayedText = "";
        _currentIndex = 0;
        _startAnimation();
      }
    }
  }

  void _startAnimation() {
    _timer?.cancel();
    
    // Instant display if duration is zero
    if (widget.duration == Duration.zero) {
      setState(() {
        _displayedText = widget.text;
        _currentIndex = widget.text.runes.length;
      });
      widget.onComplete?.call();
      return;
    }

    // Use Runes to handle Surrogate Pairs safely (Emojis)
    final runes = widget.text.runes.toList();
    
    // Optimization: If text is already displayed, don't restart
    if (_currentIndex >= runes.length && _displayedText == widget.text) {
        return;
    }
    
    _timer = Timer.periodic(widget.duration, (timer) {
      if (_currentIndex < runes.length) {
        setState(() {
          _currentIndex++;
          _displayedText = String.fromCharCodes(runes.take(_currentIndex));
        });
      } else {
        _timer?.cancel();
        widget.onComplete?.call();
      }
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Text(
      _displayedText,
      style: widget.style,
    );
  }
}
