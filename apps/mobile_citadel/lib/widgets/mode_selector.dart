import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class ModeSelector extends StatefulWidget {
  final Function(String, String) onModeSelected; // id, label
  final String currentModeId;

  const ModeSelector({
    super.key,
    required this.onModeSelected,
    required this.currentModeId,
  });

  @override
  _ModeSelectorState createState() => _ModeSelectorState();
}

class _ModeSelectorState extends State<ModeSelector> {
  final TextEditingController _searchController = TextEditingController();
  List<Map<String, dynamic>> _filteredModes = [];

  static const List<Map<String, dynamic>> _modes = [
    {
      "id": "reasoning",
      "label": "Reasoning",
      "desc": "DeepSeek R1 for complex logic & planning",
      "icon": Icons.psychology_rounded,
      "color": Color(0xFFFF6B6B), // Red/Salmon
    },
    {
      "id": "writing",
      "label": "Creative Writer",
      "desc": "Storytelling, personas & roleplay",
      "icon": Icons.edit_note_rounded,
      "color": Color(0xFF4ECDC4), // Teal
    },
    {
      "id": "coding",
      "label": "Dev Mode",
      "desc": "Code generation & debugging",
      "icon": Icons.terminal_rounded,
      "color": Color(0xFF00FF9D), // Matrix Green
    },
    {
      "id": "hacking",
      "label": "NetRunner",
      "desc": "Cybersecurity & penetration testing",
      "icon": Icons.security_rounded,
      "color": Color(0xFF9000FF), // Neon Purple
    },
    {
      "id": "image",
      "label": "Image Gen", // Renamed from Flux Imaging
      "desc": "Generate high-fidelity artwork",
      "icon": Icons.palette_rounded,
      "color": Color(0xFFFFBE0B), // Amber
    },
    {
      "id": "surgeon",
      "label": "Image Surgeon",
      "desc": "Edit, inpaint & modify images",
      "icon": Icons.medical_services_rounded,
      "color": Color(0xFF06D6A0), // Emerald
    },
    {
      "id": "qr",
      "label": "QR Studio",
      "desc": "Generate styled & functional QR codes",
      "icon": Icons.qr_code_2_rounded,
      "color": Color(0xFF3A86FF), // Blue
    },
    {
      "id": "movie",
      "label": "Movie Command",
      "desc": "Search & download media content",
      "icon": Icons.movie_filter_rounded,
      "color": Color(0xFFFF006E), // Hot Pink
    },
    {
      "id": "newspaper",
      "label": "Newspaper Agent",
      "desc": "Generate journalist-style reports",
      "icon": Icons.newspaper_rounded,
      "color": Color(0xFFFF4081), // Pink Accent
    },
  ];

  @override
  void initState() {
    super.initState();
    _filteredModes = List.from(_modes);
  }

  void _filterModes(String query) {
    setState(() {
      if (query.isEmpty) {
        _filteredModes = List.from(_modes);
      } else {
        _filteredModes = _modes.where((m) => 
          m['label'].toLowerCase().contains(query.toLowerCase()) || 
          m['desc'].toLowerCase().contains(query.toLowerCase())
        ).toList();
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    
    // Strict Theme Backgrounds
    final bgColor = isDark ? Colors.black : const Color(0xFFFFFAFA); // Rose White

    return Container(
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Handle
            Container(
              margin: const EdgeInsets.only(top: 12, bottom: 8),
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: Colors.grey.withOpacity(0.3),
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
              child: Column(
                children: [
                   Text(
                    "Select Neural Mode",
                    style: GoogleFonts.getFont('Outfit', 
                      fontSize: 18, 
                      fontWeight: FontWeight.w600,
                      color: isDark ? Colors.white : Colors.black87
                    ),
                  ),
                  const SizedBox(height: 12),
                  // Search Bar
                  TextField(
                    controller: _searchController,
                    onChanged: _filterModes,
                    decoration: InputDecoration(
                      hintText: "Search Modes...",
                      prefixIcon: const Icon(Icons.search),
                      filled: true,
                      fillColor: isDark ? Colors.grey[900] : Colors.white,
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                      contentPadding: const EdgeInsets.symmetric(vertical: 0, horizontal: 16),
                    ),
                  ),
                ],
              ),
            ),

            Flexible(
              child: ListView.separated(
                shrinkWrap: true,
                physics: const BouncingScrollPhysics(),
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                itemCount: _filteredModes.length,
                separatorBuilder: (c, i) => const SizedBox(height: 8),
                itemBuilder: (context, index) {
                  final mode = _filteredModes[index];
                  final isSelected = mode["id"] == widget.currentModeId; // Fixed variable access
                  
                  return _buildModeTile(context, mode, isSelected, isDark);
                },
              ),
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  Widget _buildModeTile(BuildContext context, Map<String, dynamic> mode, bool isSelected, bool isDark) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: () {
          // onModeSelected callback already handles Navigator.pop in ChatScreen
          widget.onModeSelected(mode["id"], mode["label"]);
        },
        borderRadius: BorderRadius.circular(16),
        child: Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: isSelected 
                ? (isDark ? Colors.white.withOpacity(0.08) : Colors.black.withOpacity(0.05))
                : Colors.transparent,
            borderRadius: BorderRadius.circular(16),
            border: isSelected 
                ? Border.all(color: mode["color"], width: 1.5)
                : Border.all(color: Colors.transparent),
          ),
          child: Row(
            children: [
              // Icon Box
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: (mode["color"] as Color).withOpacity(0.2),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  mode["icon"],
                  color: mode["color"],
                  size: 24,
                ),
              ),
              const SizedBox(width: 16),
              
              // Text Info
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      mode["label"],
                      style: GoogleFonts.getFont('Outfit',
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                        color: isDark ? Colors.white : Colors.black87,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      mode["desc"],
                      style: GoogleFonts.getFont('Outfit',
                        fontSize: 12,
                        color: Colors.grey,
                      ),
                    ),
                  ],
                ),
              ),
              
              // Selected Check
              if (isSelected)
                Icon(Icons.check_circle_rounded, color: mode["color"], size: 24),
            ],
          ),
        ),
      ),
    );
  }
}

