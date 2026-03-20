
import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import '../../services/auth_service.dart';
import '../../theme/app_theme.dart';
import '../../services/api_service.dart'; // Required for Provider.of<ApiService>


class AdminDashboard extends StatefulWidget {
  const AdminDashboard({super.key});

  @override
  State<AdminDashboard> createState() => _AdminDashboardState();
}

class _AdminDashboardState extends State<AdminDashboard> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  Map<String, dynamic>? _stats;
  List<dynamic>? _users;
  List<dynamic>? _reports; // Added
  String? _baseUrl; // Added for dynamic image loading
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _loading = true);
    try {
       final auth = Provider.of<AuthService>(context, listen: false);
       final api = Provider.of<ApiService>(context, listen: false); // ApiService
       
       final stats = await auth.getAdminStats();
       final users = await auth.getUsers();
       final reports = await api.getAdminReports(); // Fetch Reports
       final baseUrl = await api.getBaseUrl();

       
       if (mounted) {
         setState(() {
           _stats = stats;
           _users = users;
           _reports = reports;
           _baseUrl = baseUrl;
           _loading = false;
         });
       }
    } catch (e) {
      print("Dashboard Load Error: $e");
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        title: Text("CITADEL OVERWATCH", style: GoogleFonts.orbitron(letterSpacing: 2, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.transparent,
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: const Color(0xFF00FFFF), // Cyan
          labelColor: const Color(0xFF00FFFF),
          unselectedLabelColor: Colors.white38,
          dividerColor: Colors.transparent,
          isScrollable: true, // Allow scrolling if needed
          tabs: const [
            Tab(icon: Icon(Icons.analytics), text: "OVERVIEW"),
            Tab(icon: Icon(Icons.people), text: "USERS"),
            Tab(icon: Icon(Icons.security), text: "GOD MODE"),
            Tab(icon: Icon(Icons.bug_report), text: "REPORTS"), // New Tab
          ],
        ),
        actions: [
           IconButton(icon: const Icon(Icons.refresh, color: Colors.white), onPressed: _loadData),
           const SizedBox(width: 8),
        ],
      ),
      body: _loading 
         ? const Center(child: CircularProgressIndicator(color: Color(0xFF00FF00)))
         : TabBarView(
            controller: _tabController,
            children: [
              _buildOverviewTab(),
              _buildUsersTab(),
              _buildGodModeTab(),
              _buildReportsTab(), // New View
            ],
          ),
    );
  }

  // ... (Other Tabs) ...

  // --- TAB 4: REPORTS ---
  Widget _buildReportsTab() {
    if (_reports == null || _reports!.isEmpty) {
        return Center(
            child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                    const Icon(Icons.check_circle_outline, color: Colors.green, size: 64),
                    const SizedBox(height: 16),
                    Text("SYSTEM OPTIMAL", style: GoogleFonts.orbitron(color: Colors.white54, fontSize: 18)),
                    Text("No anomalies reported.", style: GoogleFonts.shareTechMono(color: Colors.white38)),
                ],
            )
        );
    }

    return ListView.builder(
      itemCount: _reports!.length,
      itemBuilder: (context, index) {
        final report = _reports![index];
        final id = report['id'];
        final severity = report['severity'] ?? 'Medium';
        
        return Dismissible(
            key: Key('report_$id'),
            direction: DismissDirection.endToStart,
            background: Container(color: Colors.red, alignment: Alignment.centerRight, padding: const EdgeInsets.only(right: 20), child: const Icon(Icons.delete, color: Colors.white)),
            onDismissed: (_) => _deleteReport(id),
            child: Container(
                margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                decoration: _cardDecoration(borderColor: severity == 'Critical' ? Colors.red : (severity == 'High' ? Colors.orange : Colors.blue)),
                child: ExpansionTile(
                    tilePadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    collapsedIconColor: Colors.white54,
                    iconColor: AppTheme.neonBlue,
                    leading: CircleAvatar(
                        backgroundColor: severity == 'Critical' ? Colors.red.withOpacity(0.2) : Colors.blue.withOpacity(0.2),
                        child: Icon(Icons.bug_report, color: severity == 'Critical' ? Colors.red : Colors.blueAccent),
                    ),
                    title: Text("ANOMALY #${id}", style: GoogleFonts.orbitron(color: Colors.white, fontWeight: FontWeight.bold)),
                    subtitle: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                            Text(report['description'] ?? 'No Description', maxLines: 2, overflow: TextOverflow.ellipsis, style: GoogleFonts.shareTechMono(color: Colors.white70)),
                            const SizedBox(height: 4),
                            Text("User: ${report['user_id']} • ${report['timestamp'].toString().substring(0,10)}", style: GoogleFonts.shareTechMono(color: Colors.grey, fontSize: 10)),
                        ],
                    ),
                    children: [
                        Padding(
                            padding: const EdgeInsets.all(16),
                            child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                    if (report['screenshot_path'] != null)
                                        Padding(
                                            padding: const EdgeInsets.only(bottom: 12),
                                            child: ClipRRect(
                                                borderRadius: BorderRadius.circular(8),
                                                child: GestureDetector(
                                                  onTap: () => _showFullImage("${_baseUrl ?? 'http://10.0.2.2:8000'}${report['screenshot_path']}"),
                                                  child: Image.network(
                                                      "${_baseUrl ?? 'http://10.0.2.2:8000'}${report['screenshot_path']}", // Dynamic URL
                                                      height: 200, width: double.infinity, fit: BoxFit.cover,
                                                      errorBuilder: (c,e,s) => Container(height: 100, color: Colors.white10, child: const Center(child: Text("Image Load Failed", style: TextStyle(color: Colors.white)))),
                                                  ),
                                                ),
                                            ),
                                        ),
                                    const Text("DESCRIPTION:", style: TextStyle(color: AppTheme.neonBlue, fontWeight: FontWeight.bold)),
                                    Text(report['description'] ?? "", style: const TextStyle(color: Colors.white)),
                                    const SizedBox(height: 12),
                                    const Text("STEPS:", style: TextStyle(color: AppTheme.neonBlue, fontWeight: FontWeight.bold)),
                                    Text(report['steps'] ?? "N/A", style: const TextStyle(color: Colors.white)),
                                    const SizedBox(height: 16),
                                    SizedBox(
                                        width: double.infinity,
                                        child: ElevatedButton.icon(
                                            style: ElevatedButton.styleFrom(backgroundColor: Colors.red.withOpacity(0.2), foregroundColor: Colors.red, side: const BorderSide(color: Colors.red)),
                                            icon: const Icon(Icons.delete_forever),
                                            label: const Text("PURGE REPORT"),
                                            onPressed: () => _deleteReport(id),
                                        ),
                                    )
                                ],
                            ),
                        )
                    ],
                ),
            ),
        );
      },
    );
  }

  Future<void> _deleteReport(int id) async {
      try {
          final api = Provider.of<ApiService>(context, listen: false);
          await api.deleteAdminReport(id);
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Report Purged.")));
          // Refresh
          _loadData();
      } catch (e) {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Purge Failed: $e")));
      }
  }

  // --- HELPERS ---


  // --- TAB 1: OVERVIEW (CHARTS) ---
  Widget _buildOverviewTab() {
    if (_stats == null) return const Center(child: Text("No Data"));
    
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: SingleChildScrollView(
        child: Column(
          children: [
            // KPI Cards
            Row(
              children: [
                _buildKpiCard("TOTAL USERS", "${_stats!['total_users']}", Icons.people),
                const SizedBox(width: 16),
                _buildKpiCard("TOTAL EVENTS", "${_stats!['total_events']}", Icons.bolt),
              ],
            ),
            const SizedBox(height: 24),
            
            // Feature Usage (Neon Line Chart)
            Container(
              height: 320,
              padding: const EdgeInsets.all(16),
              decoration: _cardDecoration(),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                   Text("SYSTEM ACTIVITY", style: GoogleFonts.shareTechMono(color: Colors.white, fontSize: 16)),
                   const SizedBox(height: 20),
                   Expanded(
                     child: LineChart(
                       LineChartData(
                         gridData: FlGridData(show: true, drawVerticalLine: true, getDrawingHorizontalLine: (val) => FlLine(color: Colors.white10, strokeWidth: 1)),
                         titlesData: _getCategoryTitles(_stats!['by_type']),
                         borderData: FlBorderData(show: false),
                         lineBarsData: [
                            LineChartBarData(
                              spots: _getPoints(_stats!['by_type']),
                              isCurved: true,
                              color: AppTheme.neonBlue,
                              barWidth: 3,
                              isStrokeCapRound: true,
                              dotData: FlDotData(show: true),
                              belowBarData: BarAreaData(show: true, color: AppTheme.neonBlue.withOpacity(0.2)),
                            )
                         ],
                         minY: 0,
                       )
                     ),
                   ),
                ],
              ),
            ),
            const SizedBox(height: 24),
            
            // Model Usage (Neon Bar Chart)
            if (_stats!['by_model'] != null)
            // Model Usage (Neon Line Chart)
            if (_stats!['by_model'] != null)
            Container(
              height: 320,
              padding: const EdgeInsets.all(16),
              decoration: _cardDecoration(),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                   Text("NEURAL ENGINE LOAD", style: GoogleFonts.shareTechMono(color: Colors.white, fontSize: 16)),
                   const SizedBox(height: 20),
                   Expanded(
                     child: LineChart(
                       LineChartData(
                         gridData: FlGridData(show: true, drawVerticalLine: true, getDrawingHorizontalLine: (val) => FlLine(color: Colors.white10, strokeWidth: 1)),
                         titlesData: _getCategoryTitles(_stats!['by_model']),
                         borderData: FlBorderData(show: false),
                         lineBarsData: [
                            LineChartBarData(
                              spots: _getPoints(_stats!['by_model']),
                              isCurved: true,
                              color: Colors.purpleAccent,
                              barWidth: 3,
                              isStrokeCapRound: true,
                              dotData: FlDotData(show: true),
                              belowBarData: BarAreaData(show: true, color: Colors.purpleAccent.withOpacity(0.2)),
                            )
                         ],
                         minY: 0,
                       )
                     ),
                   ),
                ],
              ),
            ),
             const SizedBox(height: 24),
             
             // Simple Activity Graph (Mocked curve based on provided hourly data or simpler representation)
             Container(
              height: 300,
              padding: const EdgeInsets.all(16),
              decoration: _cardDecoration(),
              child: Column(
                children: [
                   Text("ACTIVITY (24H)", style: GoogleFonts.shareTechMono(color: Colors.white)),
                   const SizedBox(height: 20),
                   Expanded(
                     child: LineChart(
                       LineChartData(
                         gridData: FlGridData(show: false),
                         titlesData: FlTitlesData(show: false),
                         borderData: FlBorderData(show: false),
                         lineBarsData: [
                           LineChartBarData(
                             spots: _getLineSpots(),
                             isCurved: true,
                             color: const Color(0xFF00FFFF),
                             barWidth: 3,
                             dotData: FlDotData(show: false),
                             belowBarData: BarAreaData(show: true, color: const Color(0xFF00FFFF).withOpacity(0.1)),
                           ),
                         ],
                       )
                     ),
                   ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
  
  // --- TAB 2: USERS ---
  Widget _buildUsersTab() {
    if (_users == null) return const Center(child: Text("No Data"));
    
    return ListView.builder(
      itemCount: _users!.length,
      itemBuilder: (context, index) {
        final user = _users![index];
        final isBlocked = user['is_blocked'] == 1;
        final isAdmin = user['role'] == 'admin';
        
        return Container(
          margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          decoration: isAdmin 
             ? BoxDecoration(
                 gradient: LinearGradient(colors: [Colors.amber.withOpacity(0.2), Colors.transparent]),
                 border: Border.all(color: Colors.amberAccent),
                 borderRadius: BorderRadius.circular(16)
               )
             : _cardDecoration(borderColor: isBlocked ? Colors.red : null),
          child: ListTile(
            onTap: () => _showUserAudit(user), // AUDIT TAP
            leading: CircleAvatar(
              backgroundColor: isAdmin ? Colors.amber : (isBlocked ? Colors.red : const Color(0xFF00FF00)),
              child: FaIcon(
                 isAdmin ? FontAwesomeIcons.crown : (isBlocked ? Icons.block : FontAwesomeIcons.userSecret), 
                 color: Colors.black,
                 size: isAdmin ? 18 : 20,
              ),
            ),
            title: Text(
               user['username'] ?? "Unknown", 
               style: GoogleFonts.orbitron(
                 color: isAdmin ? Colors.amberAccent : Colors.white, 
                 fontWeight: FontWeight.bold,
                 letterSpacing: isAdmin ? 1.5 : 0
               )
            ),
            subtitle: Text(user['email'] ?? "No Email", style: GoogleFonts.shareTechMono(color: Colors.grey)),
            trailing: isAdmin 
               ? Container(
                   padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                   decoration: BoxDecoration(color: Colors.amber.withOpacity(0.2), borderRadius: BorderRadius.circular(20), border: Border.all(color: Colors.amber)),
                   child: const Text("ARCHITECT", style: TextStyle(fontSize: 10, color: Colors.amber, fontWeight: FontWeight.bold)),
                 ) 
               : IconButton(
                  icon: Icon(isBlocked ? Icons.lock_open : Icons.block, color: isBlocked ? Colors.green : Colors.red),
                  onPressed: () => _toggleBlock(user['id'], !isBlocked),
               ),
          ),
        );
      },
    );
  }
  
  // --- TAB 3: GOD MODE ---
  Widget _buildGodModeTab() {
     final events = _stats?['recent_events'] as List?;
     if (events == null || events.isEmpty) return const Center(child: Text("No Signal..."));
     
    return ListView.builder(
      itemCount: events.length,
      itemBuilder: (ctx, i) {
        final e = events[i];
        
        // Parse Metadata safely
        Map<String, dynamic> meta = {};
        if (e['metadata'] != null) {
          try {
             meta = e['metadata'] is Map ? e['metadata'] : {}; 
             // Try parse string if it looks like json string
             if (e['metadata'] is String && e['metadata'].toString().startsWith('{')) {
                // If it's a string from SQLite, backend might return it as String even with dict(r). Why?
                // Because SQLite stores it as TEXT.
                // We should parse it here if needed, but display raw is safer if parsing fails.
             }
          } catch (_) {}
        }

        String metaString = e['metadata'].toString();
        String username = e['username'] ?? "Unknown Agent";
        String email = e['email'] ?? "No Signal";
        
        return GestureDetector(
          onTap: () => _showEventDetails(e),
          child: Container(
            margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            decoration: _cardDecoration(borderColor: AppTheme.neonBlue.withOpacity(0.3)),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // User Header
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.05),
                    borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
                  ),
                  child: Row(
                    children: [
                       const FaIcon(FontAwesomeIcons.userAstronaut, size: 12, color: Colors.grey),
                       const SizedBox(width: 8),
                       Text("$username ($email)", style: GoogleFonts.shareTechMono(color: AppTheme.neonBlue, fontSize: 11)),
                       const Spacer(),
                       Text(e['timestamp'].toString().substring(5, 16).replaceAll("T", " "), style: GoogleFonts.shareTechMono(color: Colors.grey, fontSize: 10)),
                    ],
                  ),
                ),
                
                Padding(
                  padding: const EdgeInsets.all(12),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(
                        children: [
                          Icon(_getIconForType(e['type']), color: Colors.white, size: 16),
                          const SizedBox(width: 8),
                          Text(e['type'].toString().toUpperCase(), style: GoogleFonts.orbitron(color: Colors.white, fontSize: 13, fontWeight: FontWeight.bold)),
                        ],
                      ),
                      const Icon(Icons.chevron_right, color: Colors.grey, size: 16),
                    ],
                  ),
                ),
              ],
            ),
          ),
        );
      }
    );
  }
  
  void _showEventDetails(Map<String, dynamic> event) {
     final meta = event['metadata'].toString();
     
     showDialog(
       context: context, 
       builder: (ctx) => AlertDialog(
         backgroundColor: Colors.black,
         shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16), side: const BorderSide(color: AppTheme.neonBlue)),
         title: Text("EVENT LOG", style: GoogleFonts.orbitron(color: AppTheme.neonBlue)),
         content: SingleChildScrollView(
           child: Column(
             mainAxisSize: MainAxisSize.min,
             crossAxisAlignment: CrossAxisAlignment.start,
             children: [
               Text("USER: ${event['username'] ?? 'Unknown'}", style: GoogleFonts.shareTechMono(color: Colors.white)),
               const SizedBox(height: 16),
               Text("TRACE DATA:", style: GoogleFonts.shareTechMono(color: Colors.grey)),
               const SizedBox(height: 8),
               SelectableText(meta.replaceAll("{", "").replaceAll("}", "").replaceAll('"', ''), style: GoogleFonts.firaCode(color: Colors.white70, fontSize: 12)),
             ],
           ),
         ),
         actions: [
           TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("CLOSE", style: TextStyle(color: Colors.white)))
         ],
       )
     );
  }

  void _showFullImage(String url) {
    showDialog(
      context: context,
      builder: (ctx) => Dialog(
        backgroundColor: Colors.black, // Dark background
        insetPadding: EdgeInsets.zero,
        child: Stack(
          alignment: Alignment.center,
          children: [
            InteractiveViewer(
               child: Image.network(
                 url,
                 loadingBuilder: (ctx, child, prog) => prog == null ? child : const CircularProgressIndicator(color: AppTheme.neonBlue),
                 errorBuilder: (c,e,s) => const Icon(Icons.broken_image, color: Colors.white, size: 50),
               ),
            ),
            Positioned(
              top: 40,
              right: 20,
              child: IconButton(
                icon: const Icon(Icons.close, color: Colors.white, size: 30),
                onPressed: () => Navigator.pop(ctx),
              ),
            )
          ],
        ),
      )
    );
  }
  
  IconData _getIconForType(String type) {
    if (type == 'chat') return Icons.chat;
    if (type == 'image_gen') return Icons.image;
    if (type == 'login') return Icons.vpn_key;
    return Icons.bolt;
  }

  // --- HELPERS ---

  Future<void> _toggleBlock(int userId, bool block) async {
    final auth = Provider.of<AuthService>(context, listen: false);
    await auth.blockUser(userId, block);
    _loadData(); // Refresh
  }

  Future<void> _showUserAudit(Map<String, dynamic> user) async {
      // Fetch Audit Logic
      final auth = Provider.of<AuthService>(context, listen: false);
      // We need a direct API call. AuthService helper? Or direct via auth.api
      // Let's assume auth exposes api or we add a method.
      // Easiest is to add getAudit(userId) to AuthService or use the one exposed public getter if exists (it doesn't).
      // I'll make a quick raw call here or add to auth.
      // Let's add simple method to AuthService is cleaner but requires edit.
      // For now, I'll use auth.getAdminStats style.
      
      List<dynamic> logs = [];
      try {
         // Using the auth instance to make authenticated call
         // Wait, AuthService doesn't expose generic GET. 
         // I'll assume I can just use a helper if I edit AuthService, OR copy logic. 
         // Let's edit AuthService to add getUserAudit.
         logs = await auth.getUserAudit(user['id']);
      } catch (e) {
         print("Audit Fail: $e");
         ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Audit Failed: $e")));
         return;
      }

      showDialog(
        context: context, 
        builder: (ctx) => AlertDialog(
          backgroundColor: Colors.black,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16), side: const BorderSide(color: AppTheme.neonBlue)),
          title: Text("AUDIT: ${user['username']}", style: GoogleFonts.orbitron(color: AppTheme.neonBlue)),
          content: SizedBox(
            width: double.maxFinite,
            height: 400,
            child: ListView.builder(
              itemCount: logs.length,
              itemBuilder: (c, i) {
                 final log = logs[i];
                 final meta = log['metadata'].toString();
                 
                 return Container(
                   margin: const EdgeInsets.only(bottom: 12),
                   padding: const EdgeInsets.all(12),
                   decoration: BoxDecoration(
                     color: Colors.white10,
                     borderRadius: BorderRadius.circular(8),
                     border: Border.all(color: Colors.white24)
                   ),
                   child: Column(
                     crossAxisAlignment: CrossAxisAlignment.start,
                     children: [
                       Row(
                         mainAxisAlignment: MainAxisAlignment.spaceBetween,
                         children: [
                           Text(log['type'].toString().toUpperCase(), style: GoogleFonts.orbitron(color: AppTheme.neonBlue, fontSize: 10)),
                           Text(log['timestamp'].toString().substring(5, 16).replaceAll("T", " "), style: GoogleFonts.firaCode(color: Colors.grey, fontSize: 10)),
                         ],
                       ),
                       const SizedBox(height: 8),
                       Text(meta.replaceAll("{", "").replaceAll("}", "").replaceAll('"', '').trim(), style: GoogleFonts.shareTechMono(color: Colors.white70, fontSize: 11)),
                     ],
                   ),
                 );
              }
            ),
          ),
          actions: [TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("CLOSE"))],
        )
      );
  }

  Decoration _cardDecoration({Color? borderColor}) {
    return BoxDecoration(
      color: const Color(0xFF1A1A1A).withOpacity(0.8), // Glassy Dark
      border: Border.all(color: borderColor ?? Colors.white10),
      borderRadius: BorderRadius.circular(16),
      boxShadow: [
        BoxShadow(color: Colors.black.withOpacity(0.5), blurRadius: 10, offset: const Offset(0, 4))
      ]
    );
  }
  
  Widget _buildKpiCard(String title, String value, IconData icon) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(20),
        decoration: _cardDecoration(),
        child: Column(
          children: [
            Icon(icon, color: const Color(0xFF00FFFF), size: 32),
            const SizedBox(height: 12),
            Text(value, style: GoogleFonts.outfit(color: Colors.white, fontSize: 28, fontWeight: FontWeight.bold)),
            Text(title, style: GoogleFonts.shareTechMono(color: Colors.white54, fontSize: 11)),
          ],
        ),
      ),
    );
  }
  
  List<PieChartSectionData> _getPieSections(Map<String, dynamic>? data) {
    if (data == null) return [];
    final colors = [Colors.blue, Colors.purple, Colors.orange, Colors.red, Colors.green, Colors.cyan];
    int i = 0;
    
    return data.entries.map((e) {
      final color = colors[i % colors.length];
      i++;
      return PieChartSectionData(
        color: color,
        value: (e.value as int).toDouble(),
        title: "${e.key}\n${e.value}",
        radius: 60,
        titleStyle: GoogleFonts.shareTechMono(fontSize: 10, color: Colors.white, fontWeight: FontWeight.bold),
      );
    }).toList();
  }
  
  List<FlSpot> _getPoints(Map<String, dynamic>? data) {
    if (data == null) return [];
    int x = 0;
    return data.entries.map((e) {
      final y = (e.value as int).toDouble();
      return FlSpot((x++).toDouble(), y);
    }).toList();
  }
  
  FlTitlesData _getCategoryTitles(Map<String, dynamic>? data) {
    return FlTitlesData(
      leftTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
      topTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
      rightTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
      bottomTitles: AxisTitles(
        sideTitles: SideTitles(
          showTitles: true,
          reservedSize: 40,
          interval: 1, // FORCE INTERVAL TO 1
          getTitlesWidget: (val, meta) {
             if (data == null) return const Text("");
             final index = val.toInt();
             if (index < 0 || index >= data.length) return const Text("");
             final text = data.keys.elementAt(index);
             // Shorten text
             final label = text.length > 5 ? text.substring(0,5) : text;
             return Padding(
               padding: const EdgeInsets.only(top: 8),
               child: Transform.rotate(
                 angle: -0.5,
                 child: Text(label.toUpperCase(), style: const TextStyle(color: Colors.white54, fontSize: 9))
               ),
             );
          },
        )
      )
    );
  }

  List<FlSpot> _getLineSpots() {
    final List<dynamic> byHour = _stats!['by_hour'] ?? [];
    List<FlSpot> spots = [];
    
    // Reverse because server sends limit 24 order by hour desc (newest first)
    // We want graph left-to-right (old -> new)
    final reversed = byHour.reversed.toList();
    
    for (int i=0; i<reversed.length; i++) {
        spots.add(FlSpot(i.toDouble(), (reversed[i]['count'] as int).toDouble()));
    }
    if (spots.isEmpty) spots.add(const FlSpot(0,0));
    return spots;
  }
}
