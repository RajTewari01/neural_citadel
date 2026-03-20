import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../models/app_schemas.dart';
import '../services/api_service.dart';

class MovieView extends StatefulWidget {
  const MovieView({super.key});

  @override
  State<MovieView> createState() => _MovieViewState();
}

class _MovieViewState extends State<MovieView> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final TextEditingController _searchController = TextEditingController();
  final TextEditingController _urlController = TextEditingController();
  
  bool _isTorrentMode = true; // Toggle between Torrent and URL

  List<Map<String, dynamic>> _trendingMovies = [];
  bool _isLoadingTrending = false;

  // Mock Torrent Data (Fallback)
  final List<Map<String, dynamic>> _mockTorrents = [
    {"name": "Inception (2010) 1080p BluRay", "seeds": 1240, "peers": 340, "size": "2.4 GB"},
  ];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _fetchTrending();
  }

  Future<void> _fetchTrending() async {
    setState(() => _isLoadingTrending = true);
    try {
      final movies = await Provider.of<ApiService>(context, listen: false).getTrendingMovies();
      if (mounted) {
        setState(() {
          _trendingMovies = movies;
          _isLoadingTrending = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _isLoadingTrending = false);
      print("Error fetching trending: $e");
    }
  }

  @override
  void dispose() {
    _tabController.dispose();
    _searchController.dispose();
    _urlController.dispose();
    super.dispose();
  }

  Future<void> _downloadMovie(String magnetLink) async {
    if (magnetLink.isEmpty) return;
    
    ScaffoldMessenger.of(context).showSnackBar(
       const SnackBar(content: Text("Starting download... check server logs for details."), duration: Duration(seconds: 2))
    );

    try {
      final api = Provider.of<ApiService>(context, listen: false);
      await for (final line in api.downloadMovieStream(magnetLink)) {
        if (mounted && line.trim().isNotEmpty) {
           // Show progress in snackbar or strict log
           // For now, simple feedback
           if (line.contains("ERROR")) {
              ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(line), backgroundColor: Colors.red));
           } else if (line.contains("DONE")) {
              ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Download Completed!"), backgroundColor: Colors.green));
           }
        }
      }
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Error: $e")));
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Column(
      children: [
        // Title & Toggle
        Padding(
          padding: const EdgeInsets.all(16.0),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                "MOVIE COMMAND",
                style: GoogleFonts.getFont('JetBrains Mono',
                  color: const Color(0xFFF77737), // Orange accent
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 1.5,
                ),
              ),
              // Segmented Button for Mode
              Container(
                decoration: BoxDecoration(
                  color: theme.cardColor,
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: theme.dividerColor),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    _buildToggleBtn("Torrent", _isTorrentMode, () => setState(() => _isTorrentMode = true)),
                    _buildToggleBtn("URL / YT", !_isTorrentMode, () => setState(() => _isTorrentMode = false)),
                  ],
                ),
              )
            ],
          ),
        ),

        // Content
        Expanded(
          child: _isTorrentMode ? _buildTorrentSearch(theme) : _buildUrlDownloader(theme),
        ),
      ],
    );
  }

  Widget _buildToggleBtn(String label, bool isActive, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: isActive ? const Color(0xFFF77737) : Colors.transparent,
          borderRadius: BorderRadius.circular(20),
        ),
        child: Text(
          label, 
          style: GoogleFonts.getFont('Outfit', 
            fontSize: 12, 
            color: isActive ? Colors.white : Colors.grey,
            fontWeight: FontWeight.bold
          )
        ),
      ),
    );
  }

  List<dynamic> _searchResults = [];
  bool _isSearching = false;

  Future<void> _performSearch(String query) async {
    if (query.isEmpty) return;
    setState(() => _isSearching = true);
    
    try {
      final api = Provider.of<ApiService>(context, listen: false);
      final results = await api.searchMovies(query);
      setState(() {
        _searchResults = results;
        _isSearching = false;
      });
    } catch (e) {
      if (mounted) {
        setState(() => _isSearching = false);
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Search failed: $e")));
      }
    }
  }

  Widget _buildTorrentSearch(ThemeData theme) {
    bool hasQuery = _searchController.text.isNotEmpty;
    
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        children: [
          TextField(
            controller: _searchController,
            textInputAction: TextInputAction.search,
            onSubmitted: _performSearch,
            decoration: InputDecoration(
              hintText: "Search Torrents (YTS/1337x)...",
              prefixIcon: const Icon(Icons.search, color: Color(0xFFF77737)),
              filled: true,
              fillColor: theme.cardColor,
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
              suffixIcon: _isSearching 
                ? const Padding(padding: EdgeInsets.all(12), child: CircularProgressIndicator(strokeWidth: 2))
                : IconButton(icon: const Icon(Icons.arrow_forward), onPressed: () => _performSearch(_searchController.text)),
            ),
            style: GoogleFonts.getFont('Outfit'),
          ),
          const SizedBox(height: 8),
          
          if (!hasQuery && _searchResults.isEmpty) ...[
             const SizedBox(height: 8),
             Align(
               alignment: Alignment.centerLeft,
               child: Text("🔥 TRENDING MOVIES", style: GoogleFonts.getFont('JetBrains Mono', fontWeight: FontWeight.bold, color: const Color(0xFFF77737))),
             ),
             const SizedBox(height: 8),
             Expanded(
               child: _isLoadingTrending 
                 ? const Center(child: CircularProgressIndicator(color: Color(0xFFF77737))) 
                 : RefreshIndicator(
                     onRefresh: _fetchTrending,
                     color: const Color(0xFFF77737),
                     child: GridView.builder(
                       gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                         crossAxisCount: 2,
                         childAspectRatio: 0.7,
                         crossAxisSpacing: 12,
                         mainAxisSpacing: 12,
                       ),
                       itemCount: _trendingMovies.length,
                       itemBuilder: (ctx, i) {
                         final item = _trendingMovies[i];
                         final hasImage = item['medium_cover_image'] != null;
                         
                         return GestureDetector(
                           onTap: () {
                              // If trending item has torrents, pick best or show dialog.
                              // YTS items usually have 'torrents' list.
                              if (item['torrents'] != null && (item['torrents'] as List).isNotEmpty) {
                                  final torrents = item['torrents'] as List;
                                  final best = torrents.first; // Simplified
                                  final hash = best['hash'];
                                  final title = Uri.encodeComponent(item['title'] ?? 'Movie');
                                  final magnet = "magnet:?xt=urn:btih:$hash&dn=$title";
                                  _downloadMovie(magnet);
                              } else {
                                  // Trigger search for this title if no direct torrents
                                  _searchController.text = item['title_long'] ?? item['title'];
                                  _performSearch(_searchController.text);
                              }
                           },
                           child: Container(
                             decoration: BoxDecoration(
                               color: theme.cardColor,
                               borderRadius: BorderRadius.circular(12),
                               image: hasImage ? DecorationImage(
                                 image: NetworkImage(item['medium_cover_image']),
                                 fit: BoxFit.cover,
                                 colorFilter: ColorFilter.mode(Colors.black.withOpacity(0.3), BlendMode.darken)
                               ) : null,
                               border: Border.all(color: theme.dividerColor.withOpacity(0.1)),
                             ),
                             child: Stack(
                               children: [
                                 if (!hasImage)
                                   Center(child: Icon(Icons.movie, size: 48, color: theme.disabledColor)),
                                 
                                 Positioned(
                                   bottom: 0, left: 0, right: 0,
                                   child: Container(
                                     padding: const EdgeInsets.all(8),
                                     decoration: const BoxDecoration(
                                       gradient: LinearGradient(
                                         begin: Alignment.bottomCenter,
                                         end: Alignment.topCenter,
                                         colors: [Colors.black, Colors.transparent]
                                       ),
                                       borderRadius: BorderRadius.only(bottomLeft: Radius.circular(12), bottomRight: Radius.circular(12))
                                     ),
                                     child: Column(
                                       crossAxisAlignment: CrossAxisAlignment.start,
                                       children: [
                                         Text(
                                           item['title'] ?? item['name'] ?? "Unknown", 
                                           maxLines: 2, 
                                           overflow: TextOverflow.ellipsis,
                                           style: GoogleFonts.getFont('Outfit', color: Colors.white, fontWeight: FontWeight.bold, fontSize: 12)
                                         ),
                                         const SizedBox(height: 4),
                                         Row(
                                           mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                           children: [
                                             Text("${item['year'] ?? ''}", style: const TextStyle(color: Colors.white70, fontSize: 10)),
                                             Text("⭐ ${item['rating'] ?? 'N/A'}", style: const TextStyle(color: Colors.amber, fontSize: 10, fontWeight: FontWeight.bold)),
                                           ],
                                         )
                                       ],
                                     ),
                                   ),
                                 ),
                               ],
                             ),
                           ),
                         );
                       },
                     ),
                   ),
             ),
          ] else ...[
            // Search Results 
            const SizedBox(height: 8),
            // Results List
            Expanded(
              child: _searchResults.isEmpty && !_isSearching 
                ? Center(child: Text("No results found.", style: TextStyle(color: Colors.grey)))
                : ListView.builder(
                itemCount: _searchResults.length,
                itemBuilder: (ctx, i) {
                  final item = _searchResults[i];
                  // Normalize keys depending on source (YTS vs 1337x)
                  final name = item['title'] ?? item['name'] ?? 'Unknown';
                  final seeds = item['seeds'] ?? item['seeders'] ?? 0;
                  final size = item['size'] ?? item['size_bytes'] ?? 'N/A';
                  final magnet = item['magnet'] ?? item['url']; // Sometimes url is magnet
                  
                  return Container(
                    margin: const EdgeInsets.only(bottom: 8),
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: theme.cardColor.withOpacity(0.5),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: theme.dividerColor.withOpacity(0.1)),
                    ),
                    child: Row(
                      children: [
                        Expanded(
                          flex: 4,
                          child: Text(name, style: GoogleFonts.getFont('Outfit', fontWeight: FontWeight.bold)),
                        ),
                        Expanded(
                          flex: 1,
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Text("$seeds", style: GoogleFonts.getFont('JetBrains Mono', color: Colors.greenAccent, fontWeight: FontWeight.bold)),
                              Text("seeds", style: TextStyle(fontSize: 8, color: Colors.green.withOpacity(0.7))),
                            ],
                          ),
                        ),
                        Expanded(
                          flex: 1,
                          child: Text("$size", style: GoogleFonts.getFont('JetBrains Mono', fontSize: 11)),
                        ),
                        IconButton(
                          icon: const Icon(Icons.download_rounded, color: Color(0xFFF77737)),
                          onPressed: () {
                             if (magnet != null && magnet.startsWith('magnet')) {
                               _downloadMovie(magnet);
                             } else if (item['hash'] != null) {
                               // Construct from hash
                               final hash = item['hash'];
                               final title = Uri.encodeComponent(name);
                               final m = "magnet:?xt=urn:btih:$hash&dn=$title";
                               _downloadMovie(m);
                             } else {
                               ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("No magnet link found for this item.")));
                             }
                          },
                        )
                      ],
                    ),
                  );
                },
              ),
            )
          ]
        ],
      ),
    );
  }

  Widget _buildUrlDownloader(ThemeData theme) {
    return Padding(
      padding: const EdgeInsets.all(32.0),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.link, size: 64, color: theme.disabledColor),
          const SizedBox(height: 24),
          TextField(
            controller: _urlController,
            decoration: InputDecoration(
              hintText: "Paste YouTube or Direct Link...",
              prefixIcon: const Icon(Icons.paste),
              filled: true,
              fillColor: theme.cardColor,
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
            ),
          ),
          const SizedBox(height: 24),
          SizedBox(
            width: double.infinity,
            height: 50,
            child: ElevatedButton.icon(
              icon: const Icon(Icons.download),
              label: const Text("START DOWNLOAD"),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFFF77737),
                foregroundColor: Colors.white,
              ),
              onPressed: () {},
            ),
          )
        ],
      ),
    );
  }
}

