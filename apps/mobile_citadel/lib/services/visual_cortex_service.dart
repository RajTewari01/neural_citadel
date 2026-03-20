import 'dart:async';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class VisualCortexService extends ChangeNotifier {
  // Persistence Keys
  static const String _keyRainbow = 'dialpad_rainbow';
  static const String _keyBreathing = 'dialpad_breathing';
  static const String _keyColorIndex = 'dialpad_color_index';

  // State
  bool _rainbowMode = false;
  bool _breathingMode = false;
  int _colorIndex = 0;
  
  // Rainbow Timer
  Timer? _rainbowTimer;

  // Colors (Neon Palette)
  final List<Color> _neonColors = [
    Colors.cyanAccent, 
    Colors.purpleAccent, 
    const Color(0xFF00FF41), // Matrix Green
    Colors.deepOrangeAccent,
    Colors.pinkAccent,
    Colors.amberAccent,
    Colors.white,
  ];

  // Getters
  bool get isRainbowMode => _rainbowMode;
  bool get isBreathingMode => _breathingMode;
  int get colorIndex => _colorIndex;
  
  Color get activeColor {
    if (_rainbowMode) {
      // In Rainbow Mode, we cycle automatically. 
      // ACTUALLY: The user asked for "Every time pressing, the colour should change" OR "Cycle automatically"?
      // User said: "THE RAINBOW CYCCLE IF ON... THEN BY PRESSING, EVERY TIME THE COLOUR OF THE DIALPAD SHOULD CHANGE"
      // Wait, usually "Rainbow Mode" means auto-cycle. But user said "BY PRESSING".
      // Let's re-read: "THE RAINBOW CYCCLE IF ON IN THE VISUAL CORTEX THEN BY PRESSING,EVERY TIME THE COLOUR OF THE DIALPAD SHOULD CHANGE"
      // Okay, so Rainbow Mode = Cycle on Tap.
      // "IF NOT IT SHOULD STAY AS THE COLOUR CHOOSEN"
      return _neonColors[_colorIndex % _neonColors.length];
    } else {
      return _neonColors[_colorIndex % _neonColors.length];
    }
  }

  // Init
  Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    _rainbowMode = prefs.getBool(_keyRainbow) ?? false;
    _breathingMode = prefs.getBool(_keyBreathing) ?? false;
    _colorIndex = prefs.getInt(_keyColorIndex) ?? 0;
    notifyListeners();
  }

  // Actions
  Future<void> setRainbowMode(bool enabled) async {
    _rainbowMode = enabled;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_keyRainbow, enabled);
    notifyListeners();
  }

  Future<void> setBreathingMode(bool enabled) async {
    _breathingMode = enabled;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_keyBreathing, enabled);
    notifyListeners();
  }

  Future<void> setColorIndex(int index) async {
    _colorIndex = index;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt(_keyColorIndex, index);
    notifyListeners();
  }

  // Triggered by Keypad Tap
  void cycleRainbowColor() {
    if (_rainbowMode) {
      _colorIndex = (_colorIndex + 1) % _neonColors.length;
      // We don't save this rapidly changing index to disk to avoid IO lag
      notifyListeners();
    }
  }
}
