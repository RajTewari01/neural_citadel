import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../contact_details_screen.dart';
import '../../../services/contact_service.dart';
import '../../../services/database_service.dart';
import '../../../theme/app_theme.dart';
import 'dart:io';
import 'dart:typed_data';

class FavoritesTab extends StatefulWidget {
  final ContactService contactService;
  final Function(String number) onContactSelected;

  const FavoritesTab({super.key, required this.contactService, required this.onContactSelected});

  @override
  State<FavoritesTab> createState() => _FavoritesTabState();
}

class _FavoritesTabState extends State<FavoritesTab> with AutomaticKeepAliveClientMixin {
  final TextEditingController _searchController = TextEditingController();
  List<RichContact> _favorites = []; 
  bool _isLoading = true;
  
  @override
  bool get wantKeepAlive => true;

  @override
  void initState() {
    super.initState();
    widget.contactService.addListener(_fetchFavorites);
    _fetchFavorites();
  }

  @override
  void dispose() {
    widget.contactService.removeListener(_fetchFavorites);
    _searchController.dispose(); // Also good practice
    super.dispose();
  }

  Future<void> _fetchFavorites() async {
    // await widget.contactService.init(); // Init done in Dialer
    final allContacts = await widget.contactService.getContacts();
    final starred = allContacts.where((c) => c.isStarred).toList();
    
    if (mounted) {
      setState(() {
        _favorites = starred;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    super.build(context);
    if (_isLoading) {
      return Center(child: CircularProgressIndicator(color: AppTheme.neonBlue));
    }

    final query = _searchController.text.toLowerCase();
    final displayedFavorites = _favorites.where((c) {
        if (query.isEmpty) return true;
        return c.displayName.toLowerCase().contains(query) || 
               (c.phones.isNotEmpty && c.phones.first.number.contains(query));
    }).toList();

    return Scaffold(
      backgroundColor: Colors.transparent,
      floatingActionButton: FloatingActionButton(
        backgroundColor: Colors.cyanAccent,
        child: const Icon(Icons.star_border, color: Colors.black),
        onPressed: _showAddFavoritePicker,
      ),
      body: Column(
        children: [
            Padding(
               padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
               child: TextField(
                 controller: _searchController,
                 style: GoogleFonts.outfit(color: Colors.white),
                 onChanged: (_) => setState((){}),
                 decoration: InputDecoration(
                    filled: true, fillColor: Colors.white12,
                    prefixIcon: const Icon(Icons.search, color: Colors.white54),
                    hintText: "Search favorites",
                    hintStyle: GoogleFonts.outfit(color: Colors.white38),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(30), borderSide: BorderSide.none),
                    contentPadding: const EdgeInsets.symmetric(vertical: 0, horizontal: 20),
                 ),
               )
            ),
            Expanded(
               child: displayedFavorites.isEmpty
                 ? (_favorites.isEmpty 
                     ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.star_border, size: 48, color: Colors.white.withOpacity(0.2)),
                            const SizedBox(height: 16),
                            Text("No Favorites Yet", style: GoogleFonts.orbitron(color: Colors.white38, fontSize: 16)),
                          ],
                        ),
                       )
                     : Center(child: Text("No matches found", style: GoogleFonts.outfit(color: Colors.white38)))
                   )
                 : GridView.builder(
                      padding: const EdgeInsets.all(16),
                      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                        crossAxisCount: 3,
                        crossAxisSpacing: 16,
                        mainAxisSpacing: 16,
                        childAspectRatio: 0.8,
                      ),
                      itemCount: displayedFavorites.length,
                      itemBuilder: (context, index) {
                        final contact = displayedFavorites[index];
                        final rawName = contact.displayName;
                        final hasName = rawName.isNotEmpty;
                        final number = contact.phones.isNotEmpty ? contact.phones.first.number : "";
                        final displayName = hasName ? rawName : number;

                        final dynamic photo = contact.customImage != null 
                            ? File(contact.customImage!) 
                            : contact.nativeContact.thumbnail; 

                        return Stack(
                          children: [
                            GestureDetector(
                              onTap: () => number.isNotEmpty ? widget.onContactSelected(number) : null,
                              onLongPress: () {
                                 showDialog(
                                    context: context,
                                    builder: (context) => AlertDialog(
                                       backgroundColor: const Color(0xFF1E1E1E),
                                       title: Text("Remove Favorite?", style: GoogleFonts.orbitron(color: Colors.white)),
                                       content: Text("Remove $displayName from favorites?", style: GoogleFonts.outfit(color: Colors.white70)),
                                       actions: [
                                          TextButton(
                                            onPressed: () => Navigator.pop(context),
                                            child: const Text("CANCEL", style: TextStyle(color: Colors.white54)),
                                          ),
                                          TextButton(
                                            onPressed: () async {
                                               Navigator.pop(context);
                                               await widget.contactService.setFavorite(contact, false);
                                               _fetchFavorites(); 
                                            },
                                            child: const Text("REMOVE", style: TextStyle(color: Colors.redAccent)),
                                          )
                                       ]
                                    )
                                 );
                              },
                              child: Container(
                                width: double.infinity,
                                decoration: BoxDecoration(
                                  color: Colors.white.withOpacity(0.05),
                                  borderRadius: BorderRadius.circular(16),
                                  border: Border.all(color: Colors.white.withOpacity(0.1)),
                                ),
                                child: Column(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    CircleAvatar(
                                      radius: 30,
                                      backgroundColor: AppTheme.neonBlue.withOpacity(0.2),
                                      backgroundImage: photo is File 
                                          ? FileImage(photo) as ImageProvider
                                          : (photo is Uint8List ? MemoryImage(photo) : null),
                                      child: photo == null 
                                         ? Text(displayName.isNotEmpty ? displayName[0].toUpperCase() : "#", 
                                             style: GoogleFonts.orbitron(color: AppTheme.neonBlue, fontSize: 24)) 
                                         : null,
                                    ),
                                    const SizedBox(height: 12),
                                    Padding(
                                      padding: const EdgeInsets.symmetric(horizontal: 8.0),
                                      child: Text(
                                        displayName,
                                        style: GoogleFonts.outfit(color: Colors.white, fontWeight: FontWeight.bold),
                                        maxLines: 1,
                                        overflow: TextOverflow.ellipsis,
                                        textAlign: TextAlign.center,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                            
                            Positioned(
                              top: 8, right: 8,
                              child: GestureDetector(
                                onTap: () {
                                   Navigator.push(context, MaterialPageRoute(builder: (_) => 
                                      ContactDetailsScreen(contact: contact, contactService: widget.contactService)
                                   )).then((_) => _fetchFavorites());
                                },
                                child: Container(
                                  padding: const EdgeInsets.all(6),
                                  decoration: BoxDecoration(color: Colors.black54, shape: BoxShape.circle),
                                  child: const Icon(Icons.info_outline, color: Colors.white70, size: 16),
                                ),
                              ),
                            )
                          ],
                        );
                      }
                   )
            )
        ]
      ),
    );
  }

  void _showAddFavoritePicker() async {
      final allContacts = await widget.contactService.getContacts();
      final available = allContacts.where((c) => !c.isStarred).toList();
      available.sort((a,b) => a.displayName.compareTo(b.displayName));
      
      if (!mounted) return;

      showModalBottomSheet(
        context: context,
        backgroundColor: const Color(0xFF1E1E1E),
        isScrollControlled: true,
        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
        builder: (context) {
           String pickerQuery = "";
           return StatefulBuilder(
             builder: (context, setSheetState) {
               final filtered = available.where((c) {
                  if (pickerQuery.isEmpty) return true;
                  return c.displayName.toLowerCase().contains(pickerQuery.toLowerCase()) || 
                         (c.phones.isNotEmpty && c.phones.first.number.contains(pickerQuery));
               }).toList();

               return Container(
                 height: MediaQuery.of(context).size.height * 0.85,
                 padding: const EdgeInsets.all(16),
                 child: Column(
                   children: [
                     Text("Add Favorite", style: GoogleFonts.orbitron(color: Colors.cyanAccent, fontSize: 20)),
                     const SizedBox(height: 16),
                     TextField(
                       style: GoogleFonts.outfit(color: Colors.white),
                       onChanged: (val) {
                          setSheetState(() { pickerQuery = val; });
                       },
                       decoration: InputDecoration(
                          filled: true, fillColor: Colors.white12,
                          prefixIcon: const Icon(Icons.search, color: Colors.white54),
                          hintText: "Search to add...",
                          hintStyle: GoogleFonts.outfit(color: Colors.white38),
                          border: OutlineInputBorder(borderRadius: BorderRadius.circular(30), borderSide: BorderSide.none),
                          contentPadding: const EdgeInsets.symmetric(vertical: 0, horizontal: 20),
                       ),
                     ),
                     const SizedBox(height: 16),
                     Expanded(
                       child: filtered.isEmpty 
                          ? Center(child: Text("No matches", style: GoogleFonts.outfit(color: Colors.white54)))
                          : ListView.builder(
                              itemCount: filtered.length,
                              itemBuilder: (context, index) {
                                 final c = filtered[index];
                                 return ListTile(
                                   leading: CircleAvatar(
                                     backgroundColor: Colors.white10,
                                     child: Text(c.displayName.isNotEmpty ? c.displayName[0] : "#", style: const TextStyle(color: Colors.white)),
                                   ),
                                   title: Text(c.displayName, style: GoogleFonts.outfit(color: Colors.white)),
                                   trailing: const Icon(Icons.add_circle_outline, color: Colors.greenAccent),
                                   onTap: () async {
                                      Navigator.pop(context);
                                      await widget.contactService.setFavorite(c, true);
                                      _fetchFavorites();
                                   },
                                 );
                              }
                          ),
                     )
                   ],
                 ),
               );
             }
           );
        }
      );
  }
}
