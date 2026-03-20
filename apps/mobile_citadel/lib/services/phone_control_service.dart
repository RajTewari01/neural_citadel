import 'package:flutter/services.dart';
import 'package:permission_handler/permission_handler.dart';

class PhoneControlService {
  static const MethodChannel _channel = MethodChannel('com.neuralcitadel.mobile/phone');

  // Request permissions required for answering calls (Android 8.0+)
  Future<bool> requestPhonePermissions() async {
    // We need ANSWER_PHONE_CALLS usually. 
    // Since permission_handler might not have specific enum for it or it might be 'phone' group.
    // 'Permission.phone' covers READ_PHONE_STATE, CALL_PHONE, etc. 
    // ANSWER_PHONE_CALLS is separate in recent Android versions.
    
    // Let's request general phone first.
    final status = await Permission.phone.request();
    return status.isGranted;
  }

  Future<void> answerCall() async {
    try {
      await _channel.invokeMethod('answerCall');
    } on PlatformException catch (e) {
      print("Failed to answer call: '${e.message}'.");
    }
  }

  Future<void> endCall() async {
    try {
      await _channel.invokeMethod('endCall');
    } on PlatformException catch (e) {
      print("Failed to end call: '${e.message}'.");
    }
  }

  Future<void> setSpeakerphone(bool enabled) async {
    try {
      await _channel.invokeMethod('setSpeakerphone', {'enabled': enabled});
    } on PlatformException catch (e) {
      print("Failed to set speakerphone: '${e.message}'.");
    }
  }
}
