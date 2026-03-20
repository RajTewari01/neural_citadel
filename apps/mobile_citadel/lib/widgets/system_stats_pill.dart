import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'package:battery_plus/battery_plus.dart';
import 'dart:async';
import '../services/api_service.dart';
import '../screens/system_stats_screen.dart';

class SystemStatsPill extends StatefulWidget {
  const SystemStatsPill({super.key});

  @override
  State<SystemStatsPill> createState() => _SystemStatsPillState();
}

class _SystemStatsPillState extends State<SystemStatsPill> {
  final Battery _battery = Battery();
  
  // Local Stats
  int _batteryLevel = 100;
  BatteryState _batteryState = BatteryState.full;
  
  // Server Stats
  double _serverCpu = 0.0;
  double _serverRam = 0.0;
  bool _serverOnline = false;

  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _initStats();
    // User requested to STOP constant polling to reduce log spam
    // Updates will happen only on Init or when returning from the Stats Screen
  }
  
  void _initStats() async {
    try {
      final level = await _battery.batteryLevel;
      if (mounted) setState(() => _batteryLevel = level);
    } catch(e) {}
    
    _battery.onBatteryStateChanged.listen((state) {
      if (mounted) setState(() => _batteryState = state);
    });

    _refreshStats();
  }

  Future<void> _refreshStats() async {
    try {
      // Local
      final level = await _battery.batteryLevel;
      if (mounted) setState(() => _batteryLevel = level);

      // Server
      final api = Provider.of<ApiService>(context, listen: false);
      final stats = await api.getSystemStats(); 
      
      if (mounted) {
        setState(() {
          _serverCpu = stats['cpu_percent'] ?? 0.0;
          _serverRam = stats['memory_percent'] ?? 0.0;
          _serverOnline = true;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _serverOnline = false);
    }
  }

  @override
  void dispose() {
    // Timer removed
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // Hide if offline or mostly idle to save space (User Request)
    // Only show if connected OR user explicitly wants to see battery?
    // User said "system should only be shown when open other will take up space"
    // He likely means if he taps it, it opens? Or if the server is active?
    // "when open" might refer to the screen itself (The pill opens the screen).
    
    // Interpretation: The pill itself takes up space. Make it smaller or invisible?
    // "only be shown when open" -> maybe the pill should be an Icon that expands?
    // Let's make it a small dot/icon that expands on tap, or just hide the text if idle.
    
    // Better: If offline/idle, show a tiny dot. If processing, show stats.
    
    bool isProcessing = _serverOnline && _serverCpu > 5.0; // Arbitrary threshold
    
    return GestureDetector(
      onTap: () async {
        await Navigator.push(context, MaterialPageRoute(builder: (_) => const SystemStatsScreen()));
        // Refresh when returning
        _refreshStats();
      },
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 300),
        padding: EdgeInsets.symmetric(horizontal: isProcessing ? 8 : 6, vertical: 4),
        decoration: BoxDecoration(
          color: Colors.black.withOpacity(0.4),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: Colors.white12),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
             // Always show Battery (Tiny)
             Icon(
                _batteryState == BatteryState.charging ? Icons.bolt : Icons.battery_std,
                size: 14,
                color: _batteryLevel < 20 ? Colors.redAccent : Colors.greenAccent,
             ),
             if (isProcessing) ...[
                const SizedBox(width: 4),
                // Constrain text width to prevent overflow
                Flexible(child: Text("$_batteryLevel%", overflow: TextOverflow.ellipsis, style: GoogleFonts.firaCode(fontSize: 10, color: Colors.white70))),
             ],
             
             if (_serverOnline) ...[
                 const SizedBox(width: 6),
                 Container(width: 1, height: 10, color: Colors.white24),
                 const SizedBox(width: 6),
                 
                 if (isProcessing) ...[
                   Icon(Icons.dns, size: 14, color: Colors.blueAccent),
                   const SizedBox(width: 4),
                   Flexible(child: Text("CPU:${_serverCpu.toInt()}%", overflow: TextOverflow.ellipsis, style: GoogleFonts.firaCode(fontSize: 10, color: Colors.blueAccent))),
                 ] else ...[
                   // Idle State: Just a Blue Dot
                   Container(width: 6, height: 6, decoration: const BoxDecoration(color: Colors.blueAccent, shape: BoxShape.circle))
                 ]
             ] else ...[
                 // Show OFFLINE text (User requested to keep this)
                 const SizedBox(width: 8),
                 Text("OFFLINE", style: GoogleFonts.firaCode(fontSize: 10, color: Colors.red))
             ]
          ],
        ),
      ),
    );
  }
}
