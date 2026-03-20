import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

enum PhysicsMode {
  liquidMetal,
  gravityOrbs,
  cyberGrid,
  nebulaPulse,
  matrixRain,
  blackHole,
  digitalDna,
  hexagonHive,
  starfieldWarp,
  audioWave,
  neuralNetwork,
  chineseScroll,
  customPhoto,
  static // Fallback
}

class PhysicsManager {
  static final PhysicsManager _instance = PhysicsManager._internal();
  factory PhysicsManager() => _instance;
  PhysicsManager._internal();

  PhysicsMode _currentMode = PhysicsMode.gravityOrbs; // Default
  String? _customPhotoPath;
  double _physicsOpacity = 0.6; // Default opacity
  double _panelOpacity = 0.8; // Default opacity for UI elements hiding physics

  PhysicsMode get currentMode => _currentMode;
  String? get customPhotoPath => _customPhotoPath;
  double get physicsOpacity => _physicsOpacity;
  double get panelOpacity => _panelOpacity;

  Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    final modeIndex = prefs.getInt('physics_mode_index') ?? PhysicsMode.gravityOrbs.index;
    _currentMode = PhysicsMode.values[modeIndex];
    _customPhotoPath = prefs.getString('custom_photo_path');
    _physicsOpacity = prefs.getDouble('physics_opacity') ?? 0.6;
    _panelOpacity = prefs.getDouble('panel_opacity') ?? 0.8;
  }

  Future<void> setMode(PhysicsMode mode) async {
    _currentMode = mode;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt('physics_mode_index', mode.index);
  }

  Future<void> setCustomPhoto(String path) async {
    _customPhotoPath = path;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('custom_photo_path', path);
    await setMode(PhysicsMode.customPhoto);
  }
  
  Future<void> setPhysicsOpacity(double opacity) async {
    _physicsOpacity = opacity.clamp(0.0, 1.0);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setDouble('physics_opacity', _physicsOpacity);
  }

  Future<void> setPanelOpacity(double opacity) async {
    _panelOpacity = opacity.clamp(0.0, 1.0);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setDouble('panel_opacity', _panelOpacity);
  }
}
