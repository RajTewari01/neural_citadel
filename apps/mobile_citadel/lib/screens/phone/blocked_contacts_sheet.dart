import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../../services/contact_service.dart';

class BlockedContactsSheet extends StatefulWidget {
  final ContactService contactService;

  const BlockedContactsSheet({super.key, required this.contactService});

  @override
  State<BlockedContactsSheet> createState() => _BlockedContactsSheetState();
}

class _BlockedContactsSheetState extends State<BlockedContactsSheet> {
  List<String> _blockedNumbers = [];
  Map<String, String> _numberToName = {};
  bool _isLoading = true;
  String _searchQuery = "";

  @override
  void initState() {
    super.initState();
    _loadBlockedList();
  }

  Future<void> _loadBlockedList() async {
    setState(() => _isLoading = true);
    final blocked = await widget.contactService.getBlockedNumbers();
    
    // Resolve Names
    final allContacts = await widget.contactService.getContacts();
    final Map<String, String> nameMap = {};
    
    for (var b in blocked) {
       final cleanBlocked = b.replaceAll(RegExp(r'\D'), '');
       // Find contact with matching number
       try {
         final match = allContacts.firstWhere((c) {
            return c.phones.any((p) => p.number.replaceAll(RegExp(r'\D'), '').endsWith(cleanBlocked));
         });
         nameMap[b] = match.displayName;
       } catch (e) {
         nameMap[b] = "Unknown";
       }
    }

    if (mounted) {
      setState(() {
        _blockedNumbers = blocked;
        _numberToName = nameMap;
        _isLoading = false;
      });
    }
  }

  Future<void> _unblock(String number) async {
     await widget.contactService.unblockNumber(number);
     // Note: We don't reload immediately to allow animation to play
     // The list item will handle its own removal animation visually first
     // But for robustness, we reload after a delay
     Future.delayed(const Duration(milliseconds: 800), _loadBlockedList);
  }

  @override
  Widget build(BuildContext context) {
    final filtered = _blockedNumbers.where((n) {
       final name = _numberToName[n] ?? "";
       return n.contains(_searchQuery) || name.toLowerCase().contains(_searchQuery.toLowerCase());
    }).toList();

    return Container(
      height: MediaQuery.of(context).size.height * 0.85,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: const Color(0xFF0A0A0A), // Deep Black
        borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
        border: Border(top: BorderSide(color: Colors.redAccent.withOpacity(0.3))),
      ),
      child: Column(
        children: [
          // Handle
          Container(
            width: 40, height: 4, 
            margin: const EdgeInsets.only(bottom: 24),
            decoration: BoxDecoration(color: Colors.white24, borderRadius: BorderRadius.circular(2))
          ),
          
          Text("SYSTEM BLOCKED LIST", style: GoogleFonts.orbitron(color: Colors.redAccent, fontSize: 18, letterSpacing: 2)),
          const SizedBox(height: 24),
          
          // Search
          TextField(
            style: GoogleFonts.outfit(color: Colors.white),
            onChanged: (val) => setState(() => _searchQuery = val),
            decoration: InputDecoration(
               filled: true,
               fillColor: Colors.white12,
               prefixIcon: const Icon(Icons.search, color: Colors.white54),
               hintText: "Search blocked numbers...",
               hintStyle: GoogleFonts.outfit(color: Colors.white38),
               border: OutlineInputBorder(borderRadius: BorderRadius.circular(30), borderSide: BorderSide.none),
               contentPadding: const EdgeInsets.symmetric(horizontal: 20),
            ),
          ),
          const SizedBox(height: 16),
          
          Expanded(
            child: _isLoading 
                ? const Center(child: CircularProgressIndicator(color: Colors.redAccent))
                : filtered.isEmpty 
                    ? Center(child: Text("No blocked numbers", style: GoogleFonts.outfit(color: Colors.white38)))
                    : ListView.builder(
                        itemCount: filtered.length,
                        itemBuilder: (context, index) {
                           return BlockedItemRow(
                              number: filtered[index],
                              name: _numberToName[filtered[index]] ?? "Unknown",
                              onUnblock: () => _unblock(filtered[index]),
                           );
                        },
                      ),
          )
        ],
      ),
    );
  }
}

class BlockedItemRow extends StatefulWidget {
  final String number;
  final String name;
  final VoidCallback onUnblock;

  const BlockedItemRow({super.key, required this.number, required this.name, required this.onUnblock});

  @override
  State<BlockedItemRow> createState() => _BlockedItemRowState();
}

class _BlockedItemRowState extends State<BlockedItemRow> {
  bool _isUnblocking = false;
  bool _isUnblocked = false;

  @override
  Widget build(BuildContext context) {
    if (_isUnblocked) {
       // Green Lock -> Fade Out
       return SizedBox.shrink(); // Ideally animated size, but for now simple
    }

    return AnimatedContainer(
      duration: const Duration(milliseconds: 300),
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white10),
      ),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: Colors.redAccent.withOpacity(0.2),
          child: const Icon(Icons.block, color: Colors.redAccent, size: 20),
        ),
        title: Text(widget.name, style: GoogleFonts.outfit(color: Colors.white)),
        subtitle: Text(widget.number, style: GoogleFonts.sourceCodePro(color: Colors.white54)),
        trailing: GestureDetector(
          onTap: () async {
             if (_isUnblocking) return;
             setState(() => _isUnblocking = true);
             
             // Wait for animation
             await Future.delayed(const Duration(milliseconds: 1000)); // Simulate "Lock Opening"
             
             // UNBLOCK ACTION
             widget.onUnblock();

             if (mounted) {
               setState(() => _isUnblocked = true);
             }
          },
          child: AnimatedSwitcher(
            duration: const Duration(milliseconds: 300),
            transitionBuilder: (child, anim) => ScaleTransition(scale: anim, child: child),
            child: _isUnblocking 
                ? const Icon(Icons.lock_open, key: ValueKey('open'), color: Colors.greenAccent, size: 28)
                : const Icon(Icons.lock, key: ValueKey('locked'), color: Colors.redAccent, size: 28),
          ),
        ),
      ),
    ).animate(target: _isUnblocked ? 1 : 0).fadeOut(duration: const Duration(milliseconds: 300));
  }
}
