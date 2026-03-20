import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../../../services/contact_service.dart';
import '../../settings/neural_settings_screen.dart';
import '../contact_details_screen.dart';
import '../edit_contact_screen.dart';

class ContactsTab extends StatefulWidget {
  final ContactService contactService;
  final Function(String number) onContactSelected;

  const ContactsTab({
    super.key,
    required this.contactService,
    required this.onContactSelected,
  });

  @override
  State<ContactsTab> createState() => _ContactsTabState();
}

class _ContactsTabState extends State<ContactsTab> with AutomaticKeepAliveClientMixin {
  final TextEditingController _searchController = TextEditingController();
  List<RichContact> _contacts = [];
  bool _isLoading = true;

  @override
  bool get wantKeepAlive => true;

  @override
  void initState() {
    super.initState();
    widget.contactService.addListener(_loadContacts);
    _loadContacts();
  }

  @override
  void dispose() {
    widget.contactService.removeListener(_loadContacts);
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _loadContacts() async {
    final query = _searchController.text;
    List<RichContact> contacts;
    
    if (query.isNotEmpty) {
      contacts = await widget.contactService.searchContacts(query);
      contacts.sort((a, b) => a.displayName.compareTo(b.displayName));
    } else {
      contacts = await widget.contactService.getContacts();
      contacts.sort((a, b) => a.displayName.compareTo(b.displayName));
    }
    
    if (mounted) {
      setState(() {
        _contacts = contacts;
        _isLoading = false;
      });
    }
  }

  void _filterContacts(String query) async {
    final filtered = await widget.contactService.searchContacts(query);
    filtered.sort((a, b) => a.displayName.compareTo(b.displayName));
    
    setState(() {
      _contacts = filtered;
    });
  }

  Future<void> _showContactOptions(RichContact contact) async {
    await showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      transitionAnimationController: AnimationController(
        vsync: Navigator.of(context),
        duration: const Duration(milliseconds: 350), 
      ),
      builder: (context) => ContactOptionsSheet(
        contact: contact, 
        contactService: widget.contactService,
        onContactSelected: widget.onContactSelected,
        onReloadNeeded: _loadContacts,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    super.build(context);
    // Generate Sectioned Map for Headers ("A", "B", etc.)
    final Map<String, List<RichContact>> sections = {};
    for (var c in _contacts) {
       String letter = c.displayName.isNotEmpty ? c.displayName[0].toUpperCase() : "#";
       if (RegExp(r'[A-Z]').hasMatch(letter) == false) letter = "#";
       sections.putIfAbsent(letter, () => []).add(c);
    }
    final sortedKeys = sections.keys.toList()..sort();

    return Scaffold(
      backgroundColor: Colors.transparent,
      floatingActionButton: FloatingActionButton(
        backgroundColor: Colors.redAccent,
        child: Icon(Icons.add, color: Colors.white),
        onPressed: _showAddContactDialog,
      ),
      body: CustomScrollView(
        slivers: [
           // Header content: Profile + Groups
           SliverToBoxAdapter(
             child: Padding(
               padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
               child: Column(
                 children: [
                   // Search Bar
                   TextField(
                     controller: _searchController,
                     style: GoogleFonts.outfit(color: Colors.white),
                     onChanged: _filterContacts,
                     decoration: InputDecoration(
                        filled: true,
                        fillColor: Colors.white12,
                        prefixIcon: const Icon(Icons.search, color: Colors.white54),
                        hintText: "Search contacts",
                        hintStyle: GoogleFonts.outfit(color: Colors.white38),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(30), borderSide: BorderSide.none),
                        contentPadding: const EdgeInsets.symmetric(vertical: 0, horizontal: 20),
                     ),
                   ),
                   const SizedBox(height: 16),
                   // Profile Row
                   ListTile(
                     contentPadding: EdgeInsets.zero,
                     leading: CircleAvatar(
                       radius: 20, 
                       backgroundColor: Colors.redAccent,
                       child: Icon(Icons.person, color: Colors.white, size: 20),
                     ),
                     title: Text("Profile", style: GoogleFonts.outfit(color: Colors.white, fontSize: 18, fontWeight: FontWeight.normal)),
                     onTap: () {},
                   ),
                   // Groups Row
                   ListTile(
                     contentPadding: EdgeInsets.zero,
                     leading: CircleAvatar(
                       radius: 20, 
                       backgroundColor: Colors.redAccent,
                       child: Icon(Icons.group, color: Colors.white, size: 20),
                     ),
                     title: Text("Groups", style: GoogleFonts.outfit(color: Colors.white, fontSize: 18, fontWeight: FontWeight.normal)),
                     onTap: () {},
                   ),
                   Divider(color: Colors.white10),
                 ],
               ),
             ),
           ),

           // Sections
           SliverList(
             delegate: SliverChildBuilderDelegate(
               (context, index) {
                  if (index >= sortedKeys.length) return null;
                  final letter = sortedKeys[index];
                  final contactsInSection = sections[letter]!;
                  
                  return Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                       Padding(
                         padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                         child: Text(letter, style: GoogleFonts.sourceCodePro(color: Colors.white38, fontSize: 14)),
                       ),
                       ...contactsInSection.map((contact) => ListTile(
                         dense: true,
                         contentPadding: EdgeInsets.symmetric(horizontal: 16),
                         leading: CircleAvatar(
                           radius: 18,
                           backgroundColor: _getColorForName(contact.displayName),
                           backgroundImage: contact.nativeContact.thumbnail != null 
                              ? MemoryImage(contact.nativeContact.thumbnail!) 
                              : null,
                           child: contact.nativeContact.thumbnail == null 
                              ? Text(contact.displayName.isNotEmpty ? contact.displayName[0].toUpperCase() : "?", style: TextStyle(color: Colors.white))
                              : null,
                         ),
                         title: Text(contact.displayName, style: GoogleFonts.outfit(color: Colors.white, fontSize: 16)),
                         onLongPress: () => _showContactOptions(contact),
                         onTap: () {
                           Navigator.push(context, MaterialPageRoute(
                             builder: (_) => ContactDetailsScreen(contact: contact, contactService: widget.contactService)
                           )).then((_) => _loadContacts());
                         },
                       )).toList()
                    ],
                  );
               },
               childCount: sortedKeys.length,
             ),
           ),
           
           // Bottom padding for FAB
           SliverToBoxAdapter(child: SizedBox(height: 80)),
        ]
      ),
    );
  }

  Color _getColorForName(String name) {
     final colors = [Colors.purpleAccent, Colors.blueAccent, Colors.greenAccent, Colors.orangeAccent, Colors.cyanAccent];
     return colors[name.length % colors.length].withOpacity(0.6);
  }

  void _showAddContactDialog() async {
    final result = await Navigator.push(
       context,
       MaterialPageRoute(
         builder: (_) => EditContactScreen(contact: null, contactService: widget.contactService)
       )
    );
    if (result == true) {
      _loadContacts(); 
    }
  }
}

class ContactOptionsSheet extends StatefulWidget {
  final RichContact contact;
  final ContactService contactService;
  final Function(String) onContactSelected;
  final VoidCallback onReloadNeeded;

  const ContactOptionsSheet({
    super.key, 
    required this.contact, 
    required this.contactService,
    required this.onContactSelected,
    required this.onReloadNeeded,
  });

  @override
  State<ContactOptionsSheet> createState() => _ContactOptionsSheetState();
}

class _ContactOptionsSheetState extends State<ContactOptionsSheet> {
  bool _isBlocked = false;
  String? _blockedPhone;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _checkBlockStatus();
  }

  Future<void> _checkBlockStatus() async {
    final blockedNumbers = await widget.contactService.getBlockedNumbers();
    bool isBlocked = false;
    String? blockedPhone;
                  
    for (var p in widget.contact.phones) {
        final clean = p.number.replaceAll(RegExp(r'\D'), '');
        if (blockedNumbers.any((b) => b.replaceAll(RegExp(r'\D'), '').endsWith(clean))) { 
           isBlocked = true;
           blockedPhone = p.number;
           break;
        }
    }
    
    if (mounted) {
      setState(() {
        _isBlocked = isBlocked;
        _blockedPhone = blockedPhone;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    // Current live state
    final isStarred = widget.contact.isStarred;

    return Container(
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
            color: Colors.black.withOpacity(0.9),
            borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
            border: Border(top: BorderSide(color: Colors.cyanAccent.withOpacity(0.3))),
            boxShadow: [
              BoxShadow(color: Colors.cyanAccent.withOpacity(0.1), blurRadius: 20, spreadRadius: 0)
            ]
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Handle Bar
            Container(
              width: 40, height: 4, 
              decoration: BoxDecoration(color: Colors.white24, borderRadius: BorderRadius.circular(2)),
              margin: const EdgeInsets.only(bottom: 24)
            ),
                        
            Text(
              widget.contact.displayName,
              style: GoogleFonts.orbitron(
                color: Colors.cyanAccent,
                fontSize: 22,
                fontWeight: FontWeight.bold,
              ),
            ).animate().fadeIn().moveY(begin: 10, end: 0),
                        
            if (widget.contact.profession != null)
                Text(
                '${widget.contact.profession} // ${widget.contact.location ?? "Unknown Sector"}',
                style: GoogleFonts.sourceCodePro(
                  color: Colors.white54,
                  fontSize: 12,
                ),
              ).animate().fadeIn(delay: 100.ms),

            const SizedBox(height: 32),
                        
            // ACTIONS
            ListTile(
              leading: Icon(isStarred ? Icons.star : Icons.star_border, color: Colors.yellowAccent),
              title: Text(isStarred ? 'Remove from Favorites' : 'Add to Favorites', style: GoogleFonts.outfit(color: Colors.white)),
              onTap: () async {
                setState(() {
                  widget.contact.isStarred = !isStarred; 
                });
                
                await widget.contactService.setFavorite(widget.contact, !isStarred); 
                widget.onReloadNeeded();
              },
            ).animate().slideX(begin: -0.1).fadeIn(duration: 200.ms),

            ListTile(
              leading: _isLoading 
                  ? SizedBox(width: 24, height: 24, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white38))
                  : Icon(_isBlocked ? Icons.block : Icons.remove_circle_outline, color: _isBlocked ? Colors.red : Colors.pinkAccent),
              title: Text(_isBlocked ? 'Unblock Contact' : 'Block Contact', style: GoogleFonts.outfit(color: Colors.white)),
              subtitle: _isBlocked ? Text("Unblocks ${_blockedPhone ?? 'number'}", style: TextStyle(color: Colors.white38)) : null,
              onTap: _isLoading ? null : () async {
                setState(() => _isLoading = true);
                
                if (_isBlocked) {
                    for (var p in widget.contact.phones) {
                      await widget.contactService.unblockNumber(p.number);
                    }
                } else {
                    for (var p in widget.contact.phones) {
                      await widget.contactService.blockNumber(p.number);
                    }
                }
                
                // Re-check
                await _checkBlockStatus();
              },
            ).animate().slideX(begin: -0.1, delay: 50.ms).fadeIn(duration: 200.ms),

            ListTile(
              leading: const Icon(Icons.delete, color: Colors.redAccent),
              title: Text('Delete Contact', style: GoogleFonts.outfit(color: Colors.white)),
              onTap: () async {
                Navigator.pop(context);
                await widget.contactService.deleteContact(widget.contact);
                widget.onReloadNeeded();
              },
            ).animate().slideX(begin: -0.1, delay: 100.ms).fadeIn(duration: 200.ms),

            ListTile(
              leading: const Icon(Icons.edit, color: Colors.purpleAccent),
              title: Text('Edit Contact', style: GoogleFonts.outfit(color: Colors.white)),
              onTap: () async {
                  Navigator.pop(context); 
                  final result = await Navigator.push(context, MaterialPageRoute(builder: (_) => EditContactScreen(contact: widget.contact, contactService: widget.contactService)));
                  if (result == true) widget.onReloadNeeded();
              },
            ).animate().slideX(begin: -0.1, delay: 150.ms).fadeIn(duration: 200.ms),
                        
            const Divider(color: Colors.white12, height: 32),

            if (widget.contact.phones.isNotEmpty)
              ...widget.contact.phones.map((phone) => ListTile(
                leading: const Icon(Icons.call, color: Colors.greenAccent),
                title: Text(phone.number, style: GoogleFonts.sourceCodePro(color: Colors.white70)),
                onTap: () {
                  Navigator.pop(context);
                  widget.onContactSelected(phone.number);
                },
              ).animate().fadeIn(delay: 300.ms)),
          ],
        ),
    );
  }
}
