import 'dart:async';
import 'dart:math';
import 'package:sensors_plus/sensors_plus.dart';

/// A simple class to detect phone shakes using Accelerometer.
class ShakeDetector {
  final Function() onPhoneShake;
  final double shakeThresholdGravity;
  final int minTimeBetweenShakesMs;
  final int shakeCountResetTimeMs;
  final int minShakeCount;

  StreamSubscription? _streamSubscription;
  int _lastShakeTimestamp = 0;
  int _shakeCount = 0;

  ShakeDetector({
    required this.onPhoneShake,
    this.shakeThresholdGravity = 2.7,
    this.minTimeBetweenShakesMs = 250, // fast shakes
    this.shakeCountResetTimeMs = 2000, 
    this.minShakeCount = 6, // Reduced from 10 (~3-4 seconds)
  });

  /// Factory constructor to auto-start listening
  factory ShakeDetector.autoStart({
    required Function() onPhoneShake,
  }) {
    final detector = ShakeDetector(onPhoneShake: onPhoneShake);
    detector.startListening();
    return detector;
  }

  void startListening() {
    _streamSubscription = accelerometerEvents.listen((AccelerometerEvent event) {
      double gX = event.x / 9.80665;
      double gY = event.y / 9.80665;
      double gZ = event.z / 9.80665;

      // gForce will be close to 1 when there is no movement.
      double gForce = sqrt(gX * gX + gY * gY + gZ * gZ);

      if (gForce > shakeThresholdGravity) {
        final now = DateTime.now().millisecondsSinceEpoch;
        
        // Ignore shakes too close together
        if (_lastShakeTimestamp + minTimeBetweenShakesMs > now) {
          return;
        }

        // Reset shake count if too much time passed
        if (_lastShakeTimestamp + shakeCountResetTimeMs < now) {
          _shakeCount = 0;
        }

        _lastShakeTimestamp = now;
        _shakeCount++;

        if (_shakeCount >= minShakeCount) {
          onPhoneShake();
          _shakeCount = 0; // Reset after trigger
        }
      }
    });
  }

  void stopListening() {
    _streamSubscription?.cancel();
  }
}
