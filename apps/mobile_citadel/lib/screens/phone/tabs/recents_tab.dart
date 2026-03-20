import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../contact_details_screen.dart';
import 'package:flutter_contacts/flutter_contacts.dart';
import '../../../services/contact_service.dart';
import 'package:call_log/call_log.dart';
import '../../../services/history_service.dart';
import 'package:google_fonts/google_fonts.dart';
import '../phone_settings_screen.dart';

class RecentsTab extends StatefulWidget {
  const RecentsTab({super.key});

  @override
  State<RecentsTab> createState() => _RecentsTabState();
}

class _RecentsTabState extends State<RecentsTab> with AutomaticKeepAliveClientMixin, WidgetsBindingObserver {
  final HistoryService _historyService = HistoryService();
  final List<CallLogEntry> _recents = [];
  bool _isLoading = true;
  bool _isSelectionMode = false;
  final Set<String> _selectedIds = {}; 
  String _filter = "All"; // "All" or "Missed"

  @override
  bool get wantKeepAlive => true;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _loadRecents();
    // Safety check for cold start permissions race condition
    Future.delayed(const Duration(milliseconds: 1000), _loadRecents);
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      _loadRecents();
    }
  }

  void _toggleSelection(CallLogEntry entry) {
     final key = "${entry.number}_${entry.timestamp}";
     setState(() {
       if (_selectedIds.contains(key)) {
         _selectedIds.remove(key);
         if (_selectedIds.isEmpty) _isSelectionMode = false;
       } else {
         _selectedIds.add(key);
         _isSelectionMode = true;
       }
     });
  }

  void _selectAll() {
    setState(() {
      final targetList = _filter == "Missed" 
          ? _recents.where((e) => e.callType == CallType.missed) 
          : _recents;
      _selectedIds.addAll(targetList.map((e) => "${e.number}_${e.timestamp}"));
      _isSelectionMode = true;
    });
  }

  void _deleteSelected() async {
      // In real app: delete from logs via generic native call or call_log plugin
      // For now, just remove from UI list
      setState(() {
        _recents.removeWhere((e) => _selectedIds.contains("${e.number}_${e.timestamp}"));
        _selectedIds.clear();
        _isSelectionMode = false;
      });
  }

  @override
  Widget build(BuildContext context) {
    super.build(context); // Ensure KeepAlive works
    List<CallLogEntry> visibleRecents = _recents;
    if (_filter == "Missed") {
       visibleRecents = _recents.where((e) => e.callType == CallType.missed).toList();
    }

    return Column(
      children: [
        // HEADER
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
               Row(
                 mainAxisAlignment: MainAxisAlignment.spaceBetween,
                 children: [
                   Text("Dial", style: GoogleFonts.outfit(fontSize: 32, fontWeight: FontWeight.bold, color: Colors.white)),
                   Row(
                     children: [
                        if (_isSelectionMode) ...[
                          IconButton(
                            icon: const Icon(Icons.delete, color: Colors.redAccent), 
                            onPressed: _deleteSelected
                          ),
                          IconButton(
                            icon: const Icon(Icons.select_all, color: Colors.white70),
                            onPressed: _selectAll,
                          ),
                        ],
                        
                        IconButton(
                          icon: Icon(_isSelectionMode ? Icons.check : Icons.checklist, color: _isSelectionMode ? Colors.cyanAccent : Colors.white), 
                          onPressed: () {
                             setState(() {
                               _isSelectionMode = !_isSelectionMode;
                               if (!_isSelectionMode) _selectedIds.clear();
                             });
                          }
                        ), 

                       PopupMenuButton<String>(
                         icon: Icon(Icons.more_vert, color: Colors.white),
                         onSelected: (v) {
                           if (v == 'settings') {
                              Navigator.push(context, MaterialPageRoute(builder: (_) => const PhoneSettingsScreen()));
                           }
                         },
                         itemBuilder: (context) => [
                           PopupMenuItem(value: 'settings', child: Text("Settings")),
                           PopupMenuItem(value: 'blocked', child: Text("Blocked Numbers")),
                         ]
                       ),
                     ],
                   )
                 ],
               ),
               const SizedBox(height: 16),
               Row(
                 children: [
                   _buildSegment("All"),
                   const SizedBox(width: 32),
                   _buildSegment("Missed"),
                 ],
               ),
               Divider(color: Colors.white24, height: 1),
            ],
          ),
        ),

        // LIST
        Expanded(
          child: Container(
            color: Colors.transparent,
            child: _isLoading 
                ? const Center(child: CircularProgressIndicator(color: Colors.cyanAccent))
                : visibleRecents.isEmpty 
                    ? Center(child: Text("No history", style: GoogleFonts.sourceCodePro(color: Colors.white54)))
                    : ListView.builder(
                        padding: EdgeInsets.zero,
                        itemCount: visibleRecents.length,
                        itemBuilder: (context, index) {
                           final entry = visibleRecents[index];
                           final displayName = entry.name ?? entry.number ?? "Unknown";
                           final displayNumber = entry.number ?? "";
                           final isMissed = entry.callType == CallType.missed;
                           final key = "${entry.number}_${entry.timestamp}";
                           final isSelected = _selectedIds.contains(key);
                           
                           return Container(
                             margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 0),
                             decoration: const BoxDecoration(
                               border: Border(bottom: BorderSide(color: Colors.white10, width: 0.5))
                             ),
                             child: ListTile(
                               contentPadding: EdgeInsets.symmetric(horizontal: 0, vertical: 0),
                               dense: true,
                               onTap: () {
                                 if (_isSelectionMode) {
                                   _toggleSelection(entry);
                                 } else {
                                   if (entry.number != null) {
                                      const MethodChannel('com.neuralcitadel/native').invokeMethod('placeCall', {'number': entry.number});
                                   }
                                 }
                               },
                               onLongPress: () => _toggleSelection(entry),
                               leading: _isSelectionMode 
                                  ? Icon(isSelected ? Icons.check_circle : Icons.circle_outlined, color: isSelected ? Colors.cyanAccent : Colors.white24)
                                  : const Icon(Icons.phone_in_talk, color: Colors.white24, size: 20),
                               
                               title: Text(displayName, style: GoogleFonts.outfit(color: isMissed ? Colors.redAccent : Colors.white, fontSize: 16, fontWeight: FontWeight.w500)),
                               subtitle: Row(
                                 children: [
                                     Icon(
                                        entry.callType == CallType.incoming ? Icons.call_received : 
                                        entry.callType == CallType.outgoing ? Icons.call_made : Icons.call_missed,
                                        size: 12, 
                                        color: isMissed ? Colors.red : Colors.grey
                                      ),
                                      SizedBox(width: 4),
                                      Text(displayNumber, style: GoogleFonts.sourceCodePro(color: Colors.white38, fontSize: 12)),
                                 ],
                               ),
                               
                               trailing: Row(
                                 mainAxisSize: MainAxisSize.min,
                                 children: [
                                   Text(_formatTimestamp(entry.timestamp), style: GoogleFonts.sourceCodePro(color: Colors.white38, fontSize: 12)),
                                   const SizedBox(width: 12),
                                   GestureDetector(
                                     onTap: () async {
                                        if (entry.number != null) {
                                           final service = ContactService();
                                           RichContact? contact = await service.getContactByNumber(entry.number!);
                                           
                                           contact ??= RichContact(
                                             nativeContact: Contact()..phones=[Phone(entry.number!)]..displayName=displayName
                                           );
                                           
                                           if (context.mounted) {
                                              Navigator.push(context, MaterialPageRoute(builder: (_) => ContactDetailsScreen(contact: contact!, contactService: service)));
                                           }
                                        }
                                     },
                                     child: const Icon(Icons.info_outline, color: Colors.white38, size: 22),
                                   )
                                 ],
                               ),
                             ),
                           );
                        }
                      ),
          ),
        ),
      ],
    );
  }

  Widget _buildSegment(String label) {
    final isSelected = _filter == label;
    return GestureDetector(
      onTap: () => setState(() => _filter = label),
      child: Container(
        padding: const EdgeInsets.only(bottom: 8),
        decoration: BoxDecoration(
          border: isSelected ? Border(bottom: BorderSide(color: Colors.redAccent, width: 2)) : null,
        ),
        child: Text(label, style: GoogleFonts.outfit(
          color: isSelected ? Colors.white : Colors.white54,
          fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
          fontSize: 16,
        )),
      ),
    );
  }

  Future<void> _loadRecents() async {
    final recents = await _historyService.getRecents();
    if (mounted) {
      setState(() {
        _recents
          ..clear()
          ..addAll(recents);
        _isLoading = false;
      });
    }
  }

  String _formatTimestamp(int? timestamp) {
    if (timestamp == null) return "";
    final date = DateTime.fromMillisecondsSinceEpoch(timestamp);
    final now = DateTime.now();
    final diff = now.difference(date);
    
    if (diff.inDays == 0) {
      return "${date.hour}:${date.minute.toString().padLeft(2, '0')}";
    } else if (diff.inDays == 1) {
      return "Yesterday";
    } else {
      return "${date.day}/${date.month}";
    }
  }
}
