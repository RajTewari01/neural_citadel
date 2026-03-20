import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppTheme {
  static bool isDark = true;

  // --- Cyberpunk Dark Palette ---
  // --- Cyberpunk Red Palette ---
  static const Color neonRed = Color(0xFFFF003C); // Cyberpunk Red
  static const Color neonCyan = Color(0xFF00F0FF); // Cyberpunk Cyan (Secondary)
  static const Color neonBlue = Color(0xFF2979FF); // Neon Blue
  static const Color neonPurple = Color(0xFFD500F9); // Neon Purple
  static const Color neonGreen = Color(0xFF00E676); // Neon Green
  static const Color darkBg = Color(0xFF000000); // Pure Black
  static const Color darkSurface = Color(0xFF050505); // Almost Black
  static const Color darkBorder = Color(0xFF1A1A1A);

  // --- Light Red Palette ---
  static const Color lightRed = Color(0xFFD32F2F);
  static const Color lightAccent = Color(0xFFEF5350);
  static const Color lightBg = Color(0xFFFAFAFA); 
  static const Color lightSurface = Color(0xFFFFFFFF);
  static const Color lightBorder = Color(0xFFEEEEEE);

  static ThemeData get currentTheme => isDark ? cyberpunkRed : lightRedTheme;

  static ThemeData get cyberpunkRed {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: darkBg,
      primaryColor: neonRed,
      colorScheme: const ColorScheme.dark(
        primary: neonRed,
        secondary: neonCyan,
        surface: darkSurface,
        background: darkBg,
        onSurface: Colors.white,
      ),
      textTheme: ThemeData.dark().textTheme.apply(
        fontFamily: GoogleFonts.getFont('JetBrains Mono').fontFamily,
        bodyColor: Colors.white,
        displayColor: neonRed,
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: const Color(0xFF151515),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: darkBorder),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: darkBorder),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: neonRed),
        ),
      ),
    );
  }

  static ThemeData get lightRedTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      scaffoldBackgroundColor: lightBg,
      primaryColor: lightRed,
      colorScheme: const ColorScheme.light(
        primary: lightRed,
        secondary: lightAccent,
        surface: lightSurface,
        background: lightBg,
        onSurface: Color(0xFF202020),
      ),
      textTheme: ThemeData.light().textTheme.apply(
        fontFamily: GoogleFonts.getFont('Outfit').fontFamily,
        bodyColor: const Color(0xFF202020),
        displayColor: lightRed,
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.white,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: lightBorder),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: lightBorder),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: lightRed),
        ),
      ),
    );
  }

  // Gradients
  static LinearGradient get primaryGradient => isDark
      ? const LinearGradient(
          colors: [neonRed, Color(0xFFFF4B2B)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        )
      : const LinearGradient(
          colors: [lightRed, lightAccent],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        );
}
