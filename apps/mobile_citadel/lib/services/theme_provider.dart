import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class ThemeProvider extends ChangeNotifier {
  ThemeMode _themeMode = ThemeMode.dark;

  ThemeMode get themeMode => _themeMode;
  bool get isDarkMode => _themeMode == ThemeMode.dark;

  ThemeData get currentTheme => isDarkMode ? AppTheme.cyberpunkRed : AppTheme.lightRedTheme;

  void toggleTheme() {
    _themeMode = _themeMode == ThemeMode.dark ? ThemeMode.light : ThemeMode.dark;
    AppTheme.isDark = isDarkMode; // Sync static helper
    notifyListeners();
  }
}

// Global instance for simplicity in this demo
final themeProvider = ThemeProvider();
