import 'package:call_log/call_log.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:intl/intl.dart';

class HistoryService {
  // Singleton
  static final HistoryService _instance = HistoryService._internal();
  factory HistoryService() => _instance;
  HistoryService._internal();

  /// Fetch call logs
  Future<List<CallLogEntry>> getRecents() async {
    if (await Permission.phone.request().isGranted) {
       // Also logic check call log permission if separate
       if (await Permission.storage.isGranted || true) { // Some devices link storage/log
         final Iterable<CallLogEntry> entries = await CallLog.get();
         return entries.toList();
       }
    }
    return [];
  }

  String formatTimestamp(int? timestamp) {
    if (timestamp == null) return "";
    final date = DateTime.fromMillisecondsSinceEpoch(timestamp);
    final now = DateTime.now();
    
    // Today
    if (date.year == now.year && date.month == now.month && date.day == now.day) {
      return DateFormat('h:mm a').format(date);
    }
    // Yesterday
    if (date.year == now.year && date.month == now.month && date.day == now.day - 1) {
      return "Yesterday";
    }
    
    return DateFormat('MMM d').format(date);
  }

  String getCallTypeIcon(CallType? type) {
    switch (type) {
      case CallType.incoming: return "IN";
      case CallType.outgoing: return "OUT";
      case CallType.missed: return "MISSED";
      case CallType.rejected: return "REJECTED";
      case CallType.blocked: return "BLOCKED";
      default: return "";
    }
  }
}
