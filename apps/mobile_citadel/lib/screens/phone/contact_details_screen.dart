import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:image_picker/image_picker.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:path_provider/path_provider.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:qr_flutter/qr_flutter.dart';
import 'package:flutter/services.dart';
import 'dart:io';
import 'package:call_log/call_log.dart';

import '../../services/contact_service.dart';
import '../../services/history_service.dart';
import '../../services/database_service.dart';
import '../../ui/physics/physics_background.dart';
import '../../services/physics_manager.dart';
import 'edit_contact_screen.dart';
import '../../main.dart'; // For startOutgoingCall

class ContactDetailsScreen extends StatefulWidget {
  final RichContact contact;
  final ContactService contactService;

  const ContactDetailsScreen({super.key, required this.contact, required this.contactService});

  @override
  State<ContactDetailsScreen> createState() => _ContactDetailsScreenState();
}

class _ContactDetailsScreenState extends State<ContactDetailsScreen> {
  final HistoryService _historyService = HistoryService();
  late RichContact _displayContact;
  late bool _isStarred;
  bool _isBlocked = false;
  bool _loadingBlockStatus = true;
  
  @override
  void initState() {
    super.initState();
    _displayContact = widget.contact;
    _isStarred = widget.contact.isStarred;
    _checkBlockStatus();
    _loadHighRes();
  }
  
  Future<void> _checkBlockStatus() async {
     if (_displayContact.phones.isNotEmpty) {
        final number = _displayContact.phones.first.number;
        final blockedList = await widget.contactService.getBlockedNumbers();
        // Normalize comparison
        bool isNativeBlocked = blockedList.any((b) => b.replaceAll(RegExp(r'\D'), '') == number.replaceAll(RegExp(r'\D'), ''));
        if (mounted) {
           setState(() {
              _isBlocked = isNativeBlocked;
              _loadingBlockStatus = false;
           });
        }
     } else {
        if (mounted) setState(() => _loadingBlockStatus = false);
     }
  }

  Future<void> _loadHighRes() async {
     if (_displayContact.id.isNotEmpty) {
        final highRes = await widget.contactService.getNativeContact(_displayContact.id);
        if (highRes != null && highRes.photo != null && mounted) {
           setState(() {
              _displayContact = RichContact(
                 nativeContact: highRes,
                 neuralContact: _displayContact.neuralContact
              );
           });
        }
     }
  }

  Future<void> _editContact() async {
      final result = await Navigator.push(
        context, 
        MaterialPageRoute(builder: (_) => EditContactScreen(contact: _displayContact, contactService: widget.contactService))
      );
      if (result == true) {
          await widget.contactService.refreshContacts();
          var updated = (await widget.contactService.getContacts())
             .cast<RichContact?>()
             .firstWhere((c) => c!.id == _displayContact.id, orElse: () => null);
          
          if (updated == null && _displayContact.phones.isNotEmpty) {
              updated = await widget.contactService.getContactByNumber(_displayContact.phones.first.number);
          }
          
          if (updated != null && mounted) {
             setState(() {
                _displayContact = updated!;
             });
          }
      }
  }

  void _showQrDialog() {
    final name = _displayContact.displayName;
    final phone = _displayContact.phones.isNotEmpty ? _displayContact.phones.first.number : '';
    final email = _displayContact.nativeContact.emails.isNotEmpty 
        ? _displayContact.nativeContact.emails.first.address : '';
    
    final vCard = 'BEGIN:VCARD\nVERSION:3.0\nFN:$name\nTEL:$phone\nEMAIL:$email\nEND:VCARD';

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF0A0A0A),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16), side: const BorderSide(color: Colors.cyanAccent)),
        title: Center(child: Text("SHARE CONTACT", style: GoogleFonts.orbitron(color: Colors.cyanAccent))),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
              ),
              child: SizedBox(
                width: 200, height: 200,
                child: QrImageView(
                  data: vCard.isEmpty ? "EMPTY" : vCard,
                  version: QrVersions.auto,
                  size: 200,
                  backgroundColor: Colors.white,
                ),
              ),
            ),
            const SizedBox(height: 16),
            Text(name, style: GoogleFonts.outfit(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
            Text(phone, style: GoogleFonts.sourceCodePro(color: Colors.white54)),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: Text("CLOSE", style: GoogleFonts.orbitron(color: Colors.white54)),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    // Resolve Image to Display
    ImageProvider? bgImage;
    Widget? childContent;
    
    // Existing Custom Image
    if (_displayContact.customImage != null && File(_displayContact.customImage!).existsSync()) {
      bgImage = FileImage(File(_displayContact.customImage!));
    }
    // Native Photo (High Res) or Thumbnail
    else {
      final nativePhoto = _displayContact.nativeContact.photo;
      final nativeThumb = _displayContact.nativeContact.thumbnail;
      
      if (nativePhoto != null) {
        bgImage = MemoryImage(nativePhoto);
      } else if (nativeThumb != null) {
        bgImage = MemoryImage(nativeThumb);
      }
    }

    // Initials fallback
    if (bgImage == null) {
       childContent = Text(
          _displayContact.displayName.isNotEmpty ? _displayContact.displayName[0] : "?",
          style: GoogleFonts.orbitron(fontSize: 48, color: Colors.white),
       );
    }

    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        actions: [
          if (_displayContact.id.isNotEmpty) 
          IconButton(
            icon: Icon(
               _isStarred ? Icons.star : Icons.star_border, 
               color: Colors.yellowAccent
            ),
            onPressed: () async {
               setState(() {
                  _isStarred = !_isStarred;
               });
               await widget.contactService.setFavorite(_displayContact, _isStarred);
            },
          ),
          // Animated Block Button
          IconButton(
            icon: AnimatedSwitcher(
                    duration: const Duration(milliseconds: 300),
                    transitionBuilder: (child, anim) => ScaleTransition(scale: anim, child: child),
                    child: _loadingBlockStatus
                        ? Icon(
                            _isBlocked ? Icons.lock : Icons.lock_open,
                            key: ValueKey('loading_${_isBlocked}'),
                            color: Colors.orangeAccent
                          ).animate(onPlay: (c) => c.repeat()).shimmer(duration: 1200.ms, color: Colors.white)
                        : _isBlocked 
                            ? const Icon(Icons.lock, key: ValueKey('blocked'), color: Colors.redAccent) 
                            : const Icon(Icons.lock_open, key: ValueKey('unblocked'), color: Colors.greenAccent),
                  ),
            tooltip: _isBlocked ? "Unblock Contact" : "Block Contact",
            onPressed: () async {
               if (_loadingBlockStatus || _displayContact.phones.isEmpty) return;
               
               setState(() => _loadingBlockStatus = true);
               
               // Simulate Animation
               await Future.delayed(const Duration(milliseconds: 600)); 
               
               final number = _displayContact.phones.first.number;
               bool success = false;
               
               if (_isBlocked) {
                  // UNBLOCK
                  success = await widget.contactService.unblockNumber(number);
                  if (success) _isBlocked = false;
               } else {
                  // BLOCK
                  success = await widget.contactService.blockNumber(number);
                  if (success) _isBlocked = true;
               }
               
               if (mounted) {
                  setState(() => _loadingBlockStatus = false);
                  ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                    content: Text(success 
                        ? (_isBlocked ? "Contact Blocked" : "Contact Unblocked") 
                        : "Action Failed"),
                    backgroundColor: success ? (_isBlocked ? Colors.redAccent : Colors.greenAccent) : Colors.grey
                  ));
               }
            },
          ),
          IconButton(
            icon: const Icon(Icons.add_to_home_screen, color: Colors.cyanAccent),
            tooltip: "Add Shortcut",
            onPressed: () async {
               try {
                 const platform = MethodChannel('com.neuralcitadel/native');
                 await platform.invokeMethod('createDirectCallShortcut', {
                   'number': _displayContact.phones.isNotEmpty ? _displayContact.phones.first.number : '',
                   'name': _displayContact.displayName
                 });
                 if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Shortcut added for ${_displayContact.displayName}")));
               } catch (e) {
                 if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Shortcut created (System Default)")));
               }
            },
          ),
          IconButton(
            icon: const Icon(Icons.qr_code, color: Colors.cyanAccent),
            onPressed: _showQrDialog,
          ),
          IconButton(
            icon: const Icon(Icons.delete, color: Colors.redAccent),
            onPressed: () async {
                final confirm = await showDialog<bool>(
                  context: context,
                  builder: (ctx) => AlertDialog(
                    backgroundColor: Colors.black,
                    title: Text("Delete ${_displayContact.displayName}?", style: const TextStyle(color: Colors.white)),
                    actions: [
                      TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text("Cancel")),
                      TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text("Delete", style: TextStyle(color: Colors.redAccent))),
                    ]
                  )
                );
                
                if (confirm == true) {
                   await widget.contactService.deleteContact(_displayContact);
                   if (mounted) Navigator.pop(context);
                }
            },
          ),
          IconButton(
            icon: const Icon(Icons.edit, color: Colors.cyanAccent),
            onPressed: _editContact,
          )
        ],
      ),
      body: Stack(
        children: [
          // Physics Layer (Per Contact Theme)
          // Authentic Physics Engine
          Positioned.fill(child: PhysicsBackground(mode: _parseMode(_displayContact.theme))), 
          
          // UI Panel Opacity Overlay
          Positioned.fill(
            child: Container(color: Colors.black.withOpacity(PhysicsManager().panelOpacity))
          ),
          
          SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  // Avatar
                  GestureDetector(
                    onTap: _editContact,
                    child: Hero(
                      tag: _displayContact.id,
                      child: Container(
                        width: 120, height: 120,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          border: Border.all(color: Colors.cyanAccent, width: 2),
                          color: Colors.black45,
                          boxShadow: [BoxShadow(color: Colors.cyanAccent.withOpacity(0.3), blurRadius: 20)],
                          image: bgImage != null ? DecorationImage(image: bgImage, fit: BoxFit.cover) : null,
                        ),
                        child: Center(child: childContent),
                      ),
                    ),
                  ),
                  const SizedBox(height: 24),

                  // Name Field
                  Text(
                    _displayContact.displayName,
                    style: GoogleFonts.orbitron(fontSize: 24, color: Colors.white, fontWeight: FontWeight.bold),
                  ),

                  const SizedBox(height: 8),

                  // Phone Number(s)
                  ..._displayContact.phones.map((p) => Text(
                    p.number, 
                    style: GoogleFonts.sourceCodePro(fontSize: 16, color: Colors.white54)
                  )),

                  const SizedBox(height: 24),

                  // Action Buttons (Circular) - Matching Screenshot
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                    children: [
                       // Message
                       _buildCircularAction(Icons.chat_bubble, "Message", Colors.blueAccent, () {
                           if (_displayContact.phones.isNotEmpty) launchUrl(Uri.parse('sms:${_displayContact.phones.first.number}'));
                       }),
                       // Call (Green)
                       _buildCircularAction(Icons.call, "Call", Colors.greenAccent, () {
                           if (_displayContact.phones.isNotEmpty) {
                               startOutgoingCall(_displayContact.phones.first.number, _displayContact.displayName);
                           }
                       }),
                       // Video (Green)
                       _buildCircularAction(Icons.videocam, "Video", Colors.greenAccent, () async {
                           if (_displayContact.phones.isNotEmpty) {
                               try {
                                 const platform = MethodChannel('com.neuralcitadel/native');
                                 await platform.invokeMethod('placeVideoCall', {'number': _displayContact.phones.first.number});
                               } catch (e) {
                                 if (context.mounted) {
                                   ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Could not launch video call: $e")));
                                 }
                               }
                           }
                       }),
                    ],
                  ),

                  const SizedBox(height: 32),

                  // Phone Display
                  if (_displayContact.phones.isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 24),
                      child: Text("+${_displayContact.phones.first.number}", style: GoogleFonts.outfit(color: Colors.white, fontSize: 18)),
                    ),

                  // Call Logs Section
                  Align(alignment: Alignment.centerLeft, child: Text("Call logs", style: GoogleFonts.outfit(color: Colors.white54, fontSize: 14))),
                  const SizedBox(height: 16),
                  FutureBuilder<List<CallLogEntry>>(
                     future: _fetchContactHistory(),
                     builder: (context, snapshot) {
                        if (!snapshot.hasData) return const SizedBox.shrink();
                        final logs = snapshot.data!;
                        if (logs.isEmpty) return const Text("No recent history", style: TextStyle(color: Colors.white38));
                        
                        return Column(
                          children: logs.map((log) => Padding(
                            padding: const EdgeInsets.symmetric(vertical: 8),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Row(
                                  children: [
                                    Icon(
                                      log.callType == CallType.missed ? Icons.call_missed : 
                                      log.callType == CallType.outgoing ? Icons.call_made : Icons.call_received,
                                      size: 16,
                                      color: log.callType == CallType.missed ? Colors.redAccent : Colors.white70
                                    ),
                                    const SizedBox(width: 8),
                                    Text(_getCallStatusText(log), style: GoogleFonts.outfit(color: Colors.white70, fontSize: 16)),
                                  ],
                                ),
                                Text(_formatDate(log.timestamp), style: GoogleFonts.sourceCodePro(color: Colors.white54, fontSize: 12)),
                              ],
                            ),
                          )).toList(),
                        );
                     }
                  ),

                   const SizedBox(height: 32),
                   
                   // NOTES SECTION
                   Align(alignment: Alignment.centerLeft, child: Text("Secure Notes", style: GoogleFonts.outfit(color: Colors.white54, fontSize: 14))),
                   const SizedBox(height: 16),
                   FutureBuilder<List<Map<String, dynamic>>>(
                      future: DatabaseService().getCallNotes(_displayContact.phones.isNotEmpty ? _displayContact.phones.first.number : ''), // Safely fetch
                      builder: (context, snapshot) {
                         // While loading or if no data
                         if (!snapshot.hasData || snapshot.data!.isEmpty) {
                            return const Padding(
                              padding: EdgeInsets.symmetric(vertical: 8),
                              child: Text("No notes saved.", style: TextStyle(color: Colors.white38)),
                            );
                         }
                         
                         final notes = snapshot.data!;
                         return Column(
                          children: notes.map((note) => Container(
                             margin: const EdgeInsets.only(bottom: 12),
                             padding: const EdgeInsets.all(12),
                             decoration: BoxDecoration(
                               color: Colors.white.withOpacity(0.05),
                               borderRadius: BorderRadius.circular(8),
                               border: Border.all(color: Colors.white10)
                             ),
                             child: Row(
                               crossAxisAlignment: CrossAxisAlignment.start,
                               children: [
                                 Expanded(
                                   child: Column(
                                     crossAxisAlignment: CrossAxisAlignment.start,
                                     children: [
                                        Text(note['note'] ?? "", style: GoogleFonts.sourceCodePro(color: Colors.white70, fontSize: 14)),
                                        const SizedBox(height: 6),
                                        Text(
                                           _formatDate(note['timestamp']), 
                                           style: GoogleFonts.outfit(color: Colors.white30, fontSize: 10)
                                        )
                                     ],
                                   ),
                                 ),
                                 IconButton(
                                   icon: const Icon(Icons.delete_outline, color: Colors.redAccent, size: 20),
                                   tooltip: "Delete Note",
                                   onPressed: () => _confirmDeleteNote(note['id']),
                                 )
                               ],
                             ),
                          )).toList(),
                        );
                     }
                  ),
                  const SizedBox(height: 48), // Bottom Padding
                ],
              ),
            ),
          )
        ],
      ),
    );
  }

  Future<void> _confirmDeleteNote(int id) async {
      final confirm = await showDialog<bool>(
          context: context,
          builder: (ctx) => AlertDialog(
              backgroundColor: const Color(0xFF0F0F0F),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16), side: const BorderSide(color: Colors.redAccent, width: 1)),
              title: Text("DELETE NOTE?", style: GoogleFonts.orbitron(color: Colors.redAccent, letterSpacing: 1)),
              content: Text("This action cannot be undone.", style: GoogleFonts.sourceCodePro(color: Colors.white70)),
              actions: [
                  TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text("CANCEL", style: TextStyle(color: Colors.white54))),
                  TextButton(
                      onPressed: () => Navigator.pop(ctx, true), 
                      child: const Text("DELETE", style: TextStyle(color: Colors.redAccent, fontWeight: FontWeight.bold))
                  ),
              ]
          )
      );

      if (confirm == true) {
          await DatabaseService().deleteCallNote(id);
          if (mounted) setState(() {}); // Refresh UI
      }
  }

  Widget _buildCircularAction(IconData icon, String label, Color color, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: color, 
              shape: BoxShape.circle,
            ),
            child: Icon(icon, color: Colors.white, size: 24),
          ),
          const SizedBox(height: 8),
          Text(label, style: GoogleFonts.outfit(color: color, fontSize: 12)),
        ],
      ),
    );
  }

  Future<List<CallLogEntry>> _fetchContactHistory() async {
      try {
        final allRecents = await _historyService.getRecents();
        final contactNumbers = _displayContact.phones.map((p) => p.number.replaceAll(RegExp(r'\D'), '')).toSet();
        
        return allRecents.where((entry) {
           final entryNum = (entry.number ?? "").replaceAll(RegExp(r'\D'), '');
           if (entryNum.length >= 10) {
             return contactNumbers.any((cn) => cn.endsWith(entryNum.substring(entryNum.length - 10)));
           }
           return contactNumbers.contains(entryNum);
        }).take(5).toList();
      } catch (e) {
        debugPrint("Error fetching history: $e");
        return [];
      }
  }
  
  String _getCallStatusText(CallLogEntry log) {
     switch (log.callType) {
       case CallType.missed: return "Missed call";
       case CallType.outgoing: return "Outgoing call";
       case CallType.incoming: return "Incoming call";
       case CallType.rejected: return "Rejected call";
       case CallType.blocked: return "Blocked call";
       default: return "Unknown";
     }
  }

  String _formatDate(int? timestamp) {
     if (timestamp == null) return "";
     final date = DateTime.fromMillisecondsSinceEpoch(timestamp);
     return "${date.month}/${date.day} ${date.hour}:${date.minute.toString().padLeft(2,'0')}";
  }

  PhysicsMode _parseMode(String? theme) {
      if (theme == null) return PhysicsMode.gravityOrbs;
      try {
        return PhysicsMode.values.firstWhere(
           (e) => e.toString().split('.').last == theme
        );
      } catch (_) {
        return PhysicsMode.gravityOrbs;
      }
  }
}
