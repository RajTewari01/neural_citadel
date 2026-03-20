import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:shared_preferences/shared_preferences.dart';

class PhoneSettingsScreen extends StatefulWidget {
  const PhoneSettingsScreen({super.key});

  @override
  State<PhoneSettingsScreen> createState() => _PhoneSettingsScreenState();
}

class _PhoneSettingsScreenState extends State<PhoneSettingsScreen> {
  // State for toggles
  bool _displayNumber = true;
  bool _vibrateOnAnswer = true;
  bool _autoAnswer = false;
  bool _spamBlock = false;
  bool _unknownId = true;
  bool _smsReject = false;

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    final prefs = await SharedPreferences.getInstance();
    if (mounted) {
      setState(() {
        _displayNumber = prefs.getBool('phone_display_number') ?? true;
        _vibrateOnAnswer = prefs.getBool('phone_vibrate_answer') ?? true;
        _autoAnswer = prefs.getBool('phone_auto_answer') ?? false;
        _spamBlock = prefs.getBool('phone_spam_block') ?? false;
        _unknownId = prefs.getBool('phone_unknown_id') ?? true;
        _smsReject = prefs.getBool('phone_sms_reject') ?? false;
      });
    }
  }

  Future<void> _saveSetting(String key, bool value) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(key, value);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black, // Dark Theme
      appBar: AppBar(
        title: Text("Phone Settings", style: GoogleFonts.outfit(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.black,
        elevation: 0,
        leading: IconButton(icon: Icon(Icons.arrow_back, color: Colors.white), onPressed: () => Navigator.pop(context)),
      ),
      body: ListView(
        children: [
          _buildToggle("Display number when calling", _displayNumber, (v) {
             setState(() => _displayNumber = v);
             _saveSetting('phone_display_number', v);
          }),
          
          _buildMenuLink("Speed dial", onTap: () {
             ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Speed Dial Configuration")));
          }),
          
          _buildMenuLink("Display incoming calls when unlocked", subtitle: "Banner"),
          
          _buildToggle("Unknown number identification", _unknownId, (v) {
             setState(() => _unknownId = v);
             _saveSetting('phone_unknown_id', v);
          }),
          
          _buildToggle("Block spam calls", _spamBlock, (v) {
             setState(() => _spamBlock = v);
             _saveSetting('phone_spam_block', v);
          }, activeColor: Colors.redAccent),
          
          _buildToggle("Reject incoming calls with SMS", _smsReject, (v) {
             setState(() => _smsReject = v);
             _saveSetting('phone_sms_reject', v);
          }),
          
          _buildMenuLink("Call recordings", onTap: () {
             ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("No recordings found")));
          }),
          
          _buildToggle("Auto answer", _autoAnswer, (v) {
             setState(() => _autoAnswer = v);
             _saveSetting('phone_auto_answer', v);
          }, subtitle: _autoAnswer ? "On (2s delay)" : "Off"),
          
          _buildToggle("Vibrate when answering/hanging up", _vibrateOnAnswer, (v) {
             setState(() => _vibrateOnAnswer = v);
             _saveSetting('phone_vibrate_answer', v);
          }, activeColor: Colors.cyanAccent),
          
        ],
      ),
    );
  }

  Widget _buildToggle(String title, bool value, Function(bool) onChanged, {Color activeColor = Colors.cyanAccent, String? subtitle}) {
    return SwitchListTile(
      value: value, 
      onChanged: onChanged,
      activeColor: activeColor,
      title: Text(title, style: GoogleFonts.outfit(color: Colors.white, fontSize: 18)),
      subtitle: subtitle != null ? Text(subtitle, style: GoogleFonts.sourceCodePro(color: Colors.white54, fontSize: 12)) : null,
      contentPadding: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
      inactiveTrackColor: Colors.white10,
    );
  }

  Widget _buildMenuLink(String title, {String? subtitle, VoidCallback? onTap}) {
    return ListTile(
      title: Text(title, style: GoogleFonts.outfit(color: Colors.white, fontSize: 18)),
      subtitle: subtitle != null ? Text(subtitle, style: GoogleFonts.sourceCodePro(color: Colors.cyanAccent)) : null,
      contentPadding: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
      onTap: onTap,
      trailing: Icon(Icons.arrow_forward_ios, color: Colors.white24, size: 14),
    );
  }
}
