import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:path_provider/path_provider.dart';

import '../services/api_service.dart';
import '../widgets/pdf_viewer_screen.dart';
import '../widgets/video_player_screen.dart';

class GalleryScreen extends StatefulWidget {
  const GalleryScreen({super.key});

  @override
  State<GalleryScreen> createState() => _GalleryScreenState();
}

class _GalleryScreenState extends State<GalleryScreen> {
  List<Map<String, dynamic>> _allItems = []; // Source of truth
  List<Map<String, dynamic>> _items = []; // Displayed items
  bool _isLoading = true;
  
  // Filter/Sort State
  String _activeFilter = 'All'; // All, Image, Video, Audio, PDF
  String _activeSort = 'Newest'; // Newest, Oldest, Largest, Smallest, A-Z

  @override
  void initState() {
    super.initState();
    _fetchGallery();
  }

  Future<void> _fetchGallery() async {
    final api = Provider.of<ApiService>(context, listen: false);
    final items = await api.getGalleryItems();
    if (mounted) {
      setState(() {
        _allItems = items;
        _isLoading = false;
        _applyFilters();
      });
    }
  }

  void _applyFilters() {
    List<Map<String, dynamic>> temp = List.from(_allItems);
    
    // 1. Filter
    if (_activeFilter != 'All') {
      temp = temp.where((item) {
        final type = item['type'].toString().toLowerCase();
        if (_activeFilter == 'Image') return type == 'image';
        if (_activeFilter == 'Video') return type == 'video';
        if (_activeFilter == 'Audio') return type == 'audio';
        if (_activeFilter == 'PDF') return type == 'pdf';
        return true;
      }).toList();
    }

    // 2. Sort
    temp.sort((a, b) {
      switch (_activeSort) {
        case 'Newest':
          return (b['timestamp'] as num).compareTo(a['timestamp'] as num);
        case 'Oldest':
          return (a['timestamp'] as num).compareTo(b['timestamp'] as num);
        case 'Largest':
          return (b['size'] ?? 0).compareTo(a['size'] ?? 0);
        case 'Smallest':
          return (a['size'] ?? 0).compareTo(b['size'] ?? 0);
        case 'A-Z':
          return (a['name'] as String).compareTo(b['name'] as String);
        default:
          return 0;
      }
    });

    setState(() {
      _items = temp;
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final api = Provider.of<ApiService>(context, listen: false);

    return Scaffold(
      appBar: AppBar(
        title: Text("GALLERY", style: GoogleFonts.getFont('JetBrains Mono', letterSpacing: 2)),
        centerTitle: true,
        elevation: 0,
        backgroundColor: Colors.transparent,
        actions: [
          // Filter Button
          PopupMenuButton<String>(
            icon: const Icon(Icons.filter_list),
            tooltip: 'Filter by Type',
            onSelected: (val) {
              setState(() => _activeFilter = val);
              _applyFilters();
            },
            itemBuilder: (context) => [
              const PopupMenuItem(value: 'All', child: Text('All Media')),
              const PopupMenuItem(value: 'Image', child: Text('Images')),
              const PopupMenuItem(value: 'Video', child: Text('Videos')),
              const PopupMenuItem(value: 'Audio', child: Text('Audio')),
              const PopupMenuItem(value: 'PDF', child: Text('Documents')),
            ],
          ),
          // Sort Button
          PopupMenuButton<String>(
            icon: const Icon(Icons.sort),
            tooltip: 'Sort Items',
            onSelected: (val) {
              setState(() => _activeSort = val);
              _applyFilters();
            },
            itemBuilder: (context) => [
              const PopupMenuItem(value: 'Newest', child: Text('Date: Newest')),
              const PopupMenuItem(value: 'Oldest', child: Text('Date: Oldest')),
              const PopupMenuItem(value: 'Largest', child: Text('Size: Largest')),
              const PopupMenuItem(value: 'Smallest', child: Text('Size: Smallest')),
              const PopupMenuItem(value: 'A-Z', child: Text('Name: A-Z')),
            ],
          ),
        ],
      ),
      extendBodyBehindAppBar: true,
      body: Container(
        decoration: BoxDecoration(
          color: theme.brightness == Brightness.dark ? Colors.black : const Color(0xFFFFFAFA),
        ),
        child: _isLoading 
            ? const Center(child: CircularProgressIndicator())
            : _items.isEmpty 
                ? const Center(child: Text("No generated artifacts found."))
                : GridView.builder(
                    padding: const EdgeInsets.only(top: 100, left: 16, right: 16, bottom: 16),
                    gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 2,
                      crossAxisSpacing: 12,
                      mainAxisSpacing: 12,
                      childAspectRatio: 0.8,
                    ),
                    itemCount: _items.length,
                    itemBuilder: (context, index) {
                      final item = _items[index];
                      final fullUrl = "${api.baseUrl}${item['url']}";
                      final type = item['type'];
                      
                      IconData icon;
                      Color iconColor;
                      
                      switch (type) {
                        case 'video': 
                          icon = Icons.movie_creation_outlined; 
                          iconColor = Colors.orangeAccent;
                          break;
                        case 'audio': 
                          icon = Icons.audiotrack_outlined; 
                          iconColor = Colors.pinkAccent;
                          break;
                        case 'pdf': 
                          icon = Icons.picture_as_pdf_outlined; 
                          iconColor = Colors.redAccent;
                          break;
                        case 'svg': 
                          icon = Icons.draw_outlined; 
                          iconColor = Colors.purpleAccent;
                          break;
                        default: 
                          icon = Icons.insert_drive_file_outlined; 
                          iconColor = theme.primaryColor;
                      }

                      final isImage = type == 'image';

                      return GestureDetector(
                        onTap: () => _openItem(context, item, fullUrl),
                        child: Container(
                          decoration: BoxDecoration(
                            color: theme.cardColor,
                            borderRadius: BorderRadius.circular(16),
                            border: Border.all(color: theme.dividerColor.withOpacity(0.1)),
                            image: isImage ? DecorationImage(
                              image: NetworkImage(fullUrl),
                              fit: BoxFit.cover,
                            ) : null,
                          ),
                          child: !isImage ? Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Icon(icon, size: 48, color: iconColor),
                                const SizedBox(height: 8),
                                Padding(
                                  padding: const EdgeInsets.all(8.0),
                                  child: Text(item['name'], 
                                    style: GoogleFonts.getFont('Outfit', fontWeight: FontWeight.bold, fontSize: 10), 
                                    textAlign: TextAlign.center,
                                    maxLines: 2, overflow: TextOverflow.ellipsis
                                  ),
                                ),
                              ],
                            ) : null,
                        ),
                      );
                    },
                  ),
      ),
    );
  }

  void _openItem(BuildContext context, Map<String, dynamic> item, String url) async {
     // Ensure URL is clean
     url = url.trim();
     print("Attempting to open: $url");
     final type = item['type'].toString().toLowerCase();

     if (type == 'image') {
       _showImageDialog(context, url);
     } 
     else if (type == 'video') {
       Navigator.push(context, MaterialPageRoute(
         builder: (_) => VideoPlayerScreen(videoUrl: url, fileName: item['name'])
       ));
     }
     else if (type == 'pdf') {
       _downloadAndOpenPdf(context, url, item['name']);
     }
     else {
       _launchExternal(context, url);
     }
  }

  void _showImageDialog(BuildContext context, String url) {
    showDialog(context: context, builder: (_) => Dialog(
         backgroundColor: Colors.transparent,
         insetPadding: const EdgeInsets.all(8),
         child: Stack(
           alignment: Alignment.center,
           children: [
             ClipRRect(
               borderRadius: BorderRadius.circular(12),
               child: Image.network(url),
             ),
             Positioned(
               bottom: 16,
               right: 16,
               child: FloatingActionButton.small(
                 onPressed: () => _launchExternal(context, url),
                 child: const Icon(Icons.download),
               )
             )
           ],
         ),
       ));
  }

  Future<void> _downloadAndOpenPdf(BuildContext context, String url, String filename) async {
      try {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Opening PDF...")));
        
        final response = await http.get(Uri.parse(url));
        if (response.statusCode == 200) {
           final dir = await getTemporaryDirectory();
           // Sanitize filename
           final safeName = filename.replaceAll(RegExp(r'[^\w\.-]'), '_');
           final file = File('${dir.path}/$safeName');
           await file.writeAsBytes(response.bodyBytes);
           
           if (context.mounted) {
             Navigator.push(context, MaterialPageRoute(
               builder: (_) => PDFViewerScreen(filePath: file.path, fileName: filename)
             ));
           }
        } else {
           throw Exception("Download failed: ${response.statusCode}");
        }
      } catch (e) {
        if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Could not open PDF: $e")));
      }
  }

  Future<void> _launchExternal(BuildContext context, String url) async {
     // ... (existing launch logic) ...
     try {
       final uri = Uri.parse(url);
       if (!await launchUrl(uri, mode: LaunchMode.externalApplication)) {
          throw 'Could not launch $url'; 
       }
     } catch (e) {
       print("Launch Error: $e");
       if (context.mounted) {
         ScaffoldMessenger.of(context).showSnackBar(SnackBar(
           content: Text("Error opening file: $e"), 
           backgroundColor: Colors.red
         ));
       }
     }
  }
}
