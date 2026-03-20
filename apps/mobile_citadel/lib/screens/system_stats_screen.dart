import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'package:battery_plus/battery_plus.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:disk_space_plus/disk_space_plus.dart';
import 'package:device_info_plus/device_info_plus.dart';
import 'dart:async';
import 'dart:ui';
import '../services/api_service.dart';

class SystemStatsScreen extends StatefulWidget {
  const SystemStatsScreen({super.key});

  @override
  State<SystemStatsScreen> createState() => _SystemStatsScreenState();
}

class _SystemStatsScreenState extends State<SystemStatsScreen> {
  // Mobile (Local)
  final Battery _battery = Battery();
  int _batteryLevel = 0;
  BatteryState _batteryState = BatteryState.unknown;
  double _localDiskUsed = 0;
  double _localDiskTotal = 0;
  String _deviceModel = "Unknown Device";
  String _osVersion = "Android";

  // Server (Remote)
  bool _serverOnline = false;
  Map<String, dynamic> _serverStats = {};
  
  // Graph Data (History)
  final List<FlSpot> _cpuHistory = [];
  final List<FlSpot> _ramHistory = [];
  double _timeCounter = 0;
  final int _maxHistory = 20;

  Timer? _timer;

  // Instagram Gradient
  final LinearGradient _neonGradient = const LinearGradient(
    colors: [Color(0xFF833AB4), Color(0xFFFD1D1D), Color(0xFFFCB045)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );
  
  final LinearGradient _blueGradient = const LinearGradient(
    colors: [Color(0xFF00C6FF), Color(0xFF0072FF)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  @override
  void initState() {
    super.initState();
    _initLocalInfo();
    _initGraph(); // Pre-fill to prevent "sliding in" effect
    _timer = Timer.periodic(const Duration(seconds: 1), (_) => _refreshStats());
  }

  void _initGraph() {
    // Fill with empty data so the graph starts "Full" (width-wise)
    // and doesn't scroll from right to left.
    for (int i = 0; i < _maxHistory; i++) {
        _cpuHistory.add(FlSpot(i.toDouble(), 0));
        _ramHistory.add(FlSpot(i.toDouble(), 0));
    }
    _timeCounter = _maxHistory.toDouble();
  }

  // ... (existing code)



  Future<void> _initLocalInfo() async {
    // Battery
    try {
      final level = await _battery.batteryLevel;
      final state = await _battery.batteryState;
      setState(() {
        _batteryLevel = level;
        _batteryState = state;
      });
    } catch (_) {}

    // Disk
    try {
      final disk = DiskSpacePlus();
      final total = await disk.getTotalDiskSpace;
      final free = await disk.getFreeDiskSpace;
      if (total != null && free != null) {
        setState(() {
          _localDiskTotal = total / 1024; // MB to GB
          _localDiskUsed = (total - free) / 1024;
        });
      }
    } catch (_) {}

    // Device Info
    final deviceInfo = DeviceInfoPlugin();
    try {
       final androidInfo = await deviceInfo.androidInfo;
       setState(() {
         _deviceModel = "${androidInfo.manufacturer} ${androidInfo.model}";
         _osVersion = "Android ${androidInfo.version.release}";
       });
    } catch (_) {} // Add iOS support if needed
  }

  Future<void> _refreshStats() async {
    if (!mounted) return;
    
    // Update Local Battery
    try {
       final level = await _battery.batteryLevel;
       setState(() => _batteryLevel = level);
    } catch(_) {}

    // Update Server
    try {
      final api = Provider.of<ApiService>(context, listen: false);
      final stats = await api.getSystemStats();
      
      _serverOnline = true;
      _serverStats = stats;
      
      // Update Graph History
      double cpu = (stats['cpu_percent'] as num?)?.toDouble() ?? 0;
      double ram = (stats['memory_percent'] as num?)?.toDouble() ?? 0;
      
      _timeCounter++;
      _cpuHistory.add(FlSpot(_timeCounter, cpu));
      _ramHistory.add(FlSpot(_timeCounter, ram));
      
      if (_cpuHistory.length > _maxHistory) _cpuHistory.removeAt(0);
      if (_ramHistory.length > _maxHistory) _ramHistory.removeAt(0);

      setState(() {});
    } catch (e) {
      if (mounted) setState(() => _serverOnline = false);
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          // Background Glow
          Positioned(
             top: -100, left: -100,
             child: Container(
               width: 300, height: 300,
               decoration: BoxDecoration(color: Colors.purple.withOpacity(0.3), shape: BoxShape.circle),
             )
          ),
          Positioned(
             bottom: -100, right: -100,
             child: Container(
               width: 300, height: 300, 
               decoration: BoxDecoration(color: Colors.orange.withOpacity(0.2), shape: BoxShape.circle),
             )
          ),

          SafeArea(
            child: Column(
              children: [
                // AppBar
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  child: Row(
                    children: [
                      IconButton(
                        icon: const Icon(Icons.arrow_back_ios_new, color: Colors.white),
                        onPressed: () => Navigator.pop(context),
                      ),
                      Expanded(
                        child: Center(
                          child: Text("NEURAL METRICS", 
                            style: GoogleFonts.outfit(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold, letterSpacing: 2)
                          ),
                        ),
                      ),
                      const SizedBox(width: 40), // Balance
                    ],
                  ),
                ),

                Expanded(
                  child: ListView(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    children: [
                      // --- MOBILE GRID ---
                      _buildHeader("MOBILE UNIT", Icons.phone_android),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          Expanded(child: _buildGradientCard(
                            title: "BATTERY",
                            value: "$_batteryLevel%",
                            subtitle: _batteryState.toString().split('.').last.toUpperCase(),
                            icon: _batteryState == BatteryState.charging ? Icons.bolt : Icons.battery_std,
                            gradient: _batteryLevel < 20 ? const LinearGradient(colors: [Colors.red, Colors.orange]) : _neonGradient,
                          )),
                          const SizedBox(width: 12),
                          Expanded(child: _buildGradientCard(
                            title: "STORAGE",
                            value: "${_localDiskUsed.toStringAsFixed(1)} GB",
                            subtitle: "of ${_localDiskTotal.toStringAsFixed(1)} GB",
                            icon: Icons.storage,
                            gradient: _blueGradient,
                          )),
                        ],
                      ),
                      const SizedBox(height: 12),
                      _buildInfoTile("Device Model", _deviceModel),
                      _buildInfoTile("OS Version", _osVersion),

                      const SizedBox(height: 32),
                      
                      // --- SERVER GRID ---
                      _buildHeader("NEURAL SERVER", Icons.dns),
                      const SizedBox(height: 12),
                      
                      if (!_serverOnline)
                        _buildOfflineCard()
                      else ...[
                        // REAL-TIME GRAPHS
                        Container(
                          height: 180,
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: Colors.white.withOpacity(0.05),
                            borderRadius: BorderRadius.circular(16),
                            border: Border.all(color: Colors.white10),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text("LIVE LOAD (CPU vs RAM)", style: GoogleFonts.jetBrainsMono(color: Colors.white54, fontSize: 10)),
                              const SizedBox(height: 12),
                              Expanded(child: _buildLineChart()),
                            ],
                          ),
                        ),
                        const SizedBox(height: 12),

                        // STATS ROW 1
                        Row(
                          children: [
                            Expanded(child: _buildStatBox("CPU", "${(_serverStats['cpu_percent'] ?? 0).toInt()}%", "${_serverStats['cpu_cores']} Cores", Colors.cyanAccent)),
                            const SizedBox(width: 12),
                            Expanded(child: _buildStatBox("RAM", "${(_serverStats['memory_percent'] ?? 0).toInt()}%", "${(_serverStats['memory_used'] ?? 0).toStringAsFixed(1)} GB Used", Colors.purpleAccent)),
                          ],
                        ),
                        const SizedBox(height: 12),
                        
                        // DISK ROW
                        _buildStatBox("SERVER DISK", "${(_serverStats['disk_percent'] ?? 0).toInt()}%", "${(_serverStats['disk_used'] ?? 0).toStringAsFixed(1)} GB / ${(_serverStats['disk_total'] ?? 0).toStringAsFixed(1)} GB", Colors.greenAccent),
                        
                        const SizedBox(height: 12),
                        
                        // GPU ROW (Dynamic)
                        if (_serverStats['gpus'] != null && (_serverStats['gpus'] as List).isNotEmpty)
                          ...(_serverStats['gpus'] as List).map((gpu) => Padding(
                            padding: const EdgeInsets.only(bottom: 12),
                            child: _buildThinkingGlassCard(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                    children: [
                                      Text("GPU unit: ${gpu['name']}", style: GoogleFonts.outfit(color: Colors.white, fontWeight: FontWeight.bold)),
                                      Icon(Icons.layers, color: Colors.orangeAccent, size: 16),
                                    ],
                                  ),
                                  const SizedBox(height: 8),
                                  _buildGpuBar("Load", gpu['load'], Colors.orangeAccent),
                                  const SizedBox(height: 4),
                                  _buildGpuBar("Memory", (gpu['memory_used'] / gpu['memory_total']) * 100, Colors.pinkAccent),
                                  const SizedBox(height: 8),
                                  Text("TEMP: ${gpu['temperature']}°C  |  VRAM: ${gpu['memory_used']}MB / ${gpu['memory_total']}MB", style: GoogleFonts.firaCode(color: Colors.white54, fontSize: 10))
                                ],
                              )
                            ),
                          )),
                      ]
                    ], 
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader(String title, IconData icon) {
    return Row(
      children: [
        Icon(icon, color: Colors.white54, size: 16),
        const SizedBox(width: 8),
        Text(title, style: GoogleFonts.jetBrainsMono(color: Colors.white54, fontSize: 12, letterSpacing: 1.5)),
        const SizedBox(width: 8),
        Expanded(child: Container(height: 1, color: Colors.white10)),
      ],
    );
  }

  Widget _buildGradientCard({required String title, required String value, required String subtitle, required IconData icon, required Gradient gradient}) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: gradient,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [BoxShadow(color: gradient.colors.first.withOpacity(0.4), blurRadius: 10, offset: const Offset(0, 4))]
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: Colors.white, size: 24),
          const SizedBox(height: 12),
          Text(value, style: GoogleFonts.outfit(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold)),
          Text(subtitle, style: GoogleFonts.outfit(color: Colors.white70, fontSize: 12)),
          const SizedBox(height: 4),
          Text(title, style: GoogleFonts.jetBrainsMono(color: Colors.white38, fontSize: 10)),
        ],
      ),
    );
  }

  Widget _buildStatBox(String title, String mainValue, String subValue, Color accent) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white10),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: GoogleFonts.jetBrainsMono(color: Colors.white38, fontSize: 10)),
          const SizedBox(height: 4),
          Text(mainValue, style: GoogleFonts.outfit(color: accent, fontSize: 22, fontWeight: FontWeight.bold)),
          Text(subValue, style: GoogleFonts.outfit(color: Colors.white70, fontSize: 12)),
        ],
      ),
    );
  }

  Widget _buildInfoTile(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: GoogleFonts.outfit(color: Colors.white54)),
          Text(value, style: GoogleFonts.outfit(color: Colors.white)),
        ],
      ),
    );
  }

  Widget _buildThinkingGlassCard({required Widget child}) {
     return Container(
       padding: const EdgeInsets.all(16),
       decoration: BoxDecoration(
         color: Colors.white.withOpacity(0.05),
         borderRadius: BorderRadius.circular(16),
         border: Border.all(color: Colors.white10),
       ),
       child: child
     );
  }

  Widget _buildGpuBar(String label, double percent, Color color) {
    return Row(
      children: [
        SizedBox(width: 50, child: Text(label, style: GoogleFonts.jetBrainsMono(color: Colors.white54, fontSize: 10))),
        Expanded(
          child: Container(
            height: 6,
            decoration: BoxDecoration(color: Colors.white10, borderRadius: BorderRadius.circular(3)),
            child: FractionallySizedBox(
              alignment: Alignment.centerLeft,
              widthFactor: (percent / 100).clamp(0.0, 1.0),
              child: Container(decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(3))),
            ),
          )
        ),
        const SizedBox(width: 8),
        Text("${percent.toInt()}%", style: GoogleFonts.jetBrainsMono(color: color, fontSize: 10)),
      ],
    );
  }

  Widget _buildOfflineCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Colors.red.withOpacity(0.1),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.red.withOpacity(0.3)),
      ),
      child: Column(
        children: [
          const Icon(Icons.wifi_off, color: Colors.red, size: 32),
          const SizedBox(height: 8),
          Text("SERVER DISCONNECTED", style: GoogleFonts.jetBrainsMono(color: Colors.red, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  Widget _buildLineChart() {
    return LineChart(
      LineChartData(
        minX: _timeCounter - _maxHistory,
        maxX: _timeCounter,
        minY: 0,
        maxY: 100,
        gridData: FlGridData(show: false),
        titlesData: FlTitlesData(show: false),
        borderData: FlBorderData(show: false),
        lineTouchData: LineTouchData(enabled: false),
        lineBarsData: [
           // CPU Line (Cyan)
           LineChartBarData(
             spots: _cpuHistory,
             isCurved: true,
             color: Colors.cyanAccent,
             barWidth: 2,
             dotData: FlDotData(show: false),
             belowBarData: BarAreaData(show: true, color: Colors.cyanAccent.withOpacity(0.2)),
           ),
           // RAM Line (Purple)
           LineChartBarData(
             spots: _ramHistory,
             isCurved: true,
             color: Colors.purpleAccent,
             barWidth: 2,
             dotData: FlDotData(show: false),
             belowBarData: BarAreaData(show: true, color: Colors.purpleAccent.withOpacity(0.2)),
           )
        ]
      )
    );
  }
}
