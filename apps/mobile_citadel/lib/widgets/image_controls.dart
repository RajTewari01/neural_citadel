import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../models/app_schemas.dart';
import '../services/api_service.dart';

class ImageControls extends StatefulWidget {
  final Function(String pipeline, String? subtype, String ratio, int? seed) onUpdate;

  const ImageControls({super.key, required this.onUpdate});

  @override
  _ImageControlsState createState() => _ImageControlsState();
}

class _ImageControlsState extends State<ImageControls> {
  // Schema State
  ImageGenSchema? _schema;
  bool _isLoading = true;
  String? _error;
  String _statusText = ""; // Added logging status

  // Flattened Pipeline Structure
  List<PipelineOption> _flattenedPipelines = [];
  PipelineOption? _selectedOption;

  String _selectedRatio = "normal"; // Default to normal
  final TextEditingController _seedController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _loadSchema();
  }

  Future<void> _loadSchema() async {
    try {
      final api = Provider.of<ApiService>(context, listen: false);
      final schema = await api.getImageGenSchema();
      setState(() {
        _schema = schema;
        _isLoading = false;
        
        // Flatten Schema
        final pipelines = <PipelineOption>[
           // ANIME (7)
           PipelineOption(label: "MeinaMix (Anime)", category: "anime", style: "anime", subtype: "meinamix"),
           PipelineOption(label: "NovaPorn (Anime)", category: "anime", style: "anime", subtype: "novaporn"),
           PipelineOption(label: "BloodOrange (Anime)", category: "anime", style: "anime", subtype: "bloodorangemix"),
           PipelineOption(label: "AbyssOrange (Anime)", category: "anime", style: "anime", subtype: "abyssorangemix"),
           PipelineOption(label: "EerieOrange (Anime)", category: "anime", style: "anime", subtype: "eerieorangemix"),
           PipelineOption(label: "Azovya RPG (Anime)", category: "anime", style: "anime", subtype: "azovya"),
           PipelineOption(label: "Shiny Sissy (Anime)", category: "anime", style: "anime", subtype: "shiny_sissy"),

           // CARS (11)
           PipelineOption(label: "Sketch (Car)", category: "car", style: "car", subtype: "sketch"),
           PipelineOption(label: "Sedan (Car)", category: "car", style: "car", subtype: "sedan"),
           PipelineOption(label: "Retro (Car)", category: "car", style: "car", subtype: "retro"),
           PipelineOption(label: "Speedtail (Car)", category: "car", style: "car", subtype: "speedtail"),
           PipelineOption(label: "F1 Racing (Car)", category: "car", style: "car", subtype: "f1"),
           PipelineOption(label: "MX5 Miata (Car)", category: "car", style: "car", subtype: "mx5"),
           PipelineOption(label: "AutoHome (Car)", category: "car", style: "car", subtype: "autohome"),
           PipelineOption(label: "AMSDR Taxi (Car)", category: "car", style: "car", subtype: "amsdr"),
           PipelineOption(label: "RX7 JDM (Car)", category: "car", style: "car", subtype: "rx7"),
           PipelineOption(label: "JetCar/Train (Car)", category: "car", style: "car", subtype: "jetcar"),
           PipelineOption(label: "Motorbike (Car)", category: "car", style: "car", subtype: "motorbike"),

           // DRAWING (4)
           PipelineOption(label: "Rachel Walker (Draw)", category: "drawing", style: "drawing", subtype: "rachel_walker"),
           PipelineOption(label: "Matcha Pixiv (Draw)", category: "drawing", style: "drawing", subtype: "matcha_pixiv"),
           PipelineOption(label: "Pareidolia (Draw)", category: "drawing", style: "drawing", subtype: "pareidolia"),
           PipelineOption(label: "Chinese Ink (Draw)", category: "drawing", style: "drawing", subtype: "chinese_ink"),

           // HYPERREALISTIC (5)
           PipelineOption(label: "Realistic Vision", category: "hyperrealistic", style: "hyperrealistic", subtype: "realistic_vision"),
           PipelineOption(label: "DreamShaper", category: "hyperrealistic", style: "hyperrealistic", subtype: "dreamshaper"),
           PipelineOption(label: "NeverEnding", category: "hyperrealistic", style: "hyperrealistic", subtype: "neverending"),
           PipelineOption(label: "Digital Potrait", category: "hyperrealistic", style: "hyperrealistic", subtype: "digital"),
           PipelineOption(label: "Typhoon", category: "hyperrealistic", style: "hyperrealistic", subtype: "typhoon"),

           // ETHNICITY (5)
           PipelineOption(label: "Asian", category: "ethnicity", style: "ethnicity", subtype: "asian"),
           PipelineOption(label: "Indian", category: "ethnicity", style: "ethnicity", subtype: "indian"),
           PipelineOption(label: "Russian", category: "ethnicity", style: "ethnicity", subtype: "russian"),
           PipelineOption(label: "European", category: "ethnicity", style: "ethnicity", subtype: "european"),
           PipelineOption(label: "Chinese", category: "ethnicity", style: "ethnicity", subtype: "chinese"),

           // PAPERCUT (2)
           PipelineOption(label: "Midjourney (Paper)", category: "papercut", style: "papercut", subtype: "midjourney"),
           PipelineOption(label: "Origami Craft (Paper)", category: "papercut", style: "papercut", subtype: "papercutcraft"),

           // DIFCONSISTENCY (3)
           PipelineOption(label: "Photo (DifCon)", category: "difconsistency", style: "difconsistency", subtype: "photo"),
           PipelineOption(label: "Detail (DifCon)", category: "difconsistency", style: "difconsistency", subtype: "detail"),
           PipelineOption(label: "Raw (DifCon)", category: "difconsistency", style: "difconsistency", subtype: "raw"),

           // NSFW (4)
           PipelineOption(label: "Lazy Mix (NSFW)", category: "nsfw", style: "nsfw", subtype: "lazy_mix"),
           PipelineOption(label: "URPM (NSFW)", category: "nsfw", style: "nsfw", subtype: "urpm"),
           PipelineOption(label: "PornMaster (NSFW)", category: "nsfw", style: "nsfw", subtype: "pornmaster"),
           PipelineOption(label: "Futa/Trans (NSFW)", category: "nsfw", style: "nsfw", subtype: "realistic_futa"),

           // HORROR (5)
           PipelineOption(label: "Portrait (Horror)", category: "horror", style: "horror", subtype: "portrait"),
           PipelineOption(label: "Character (Horror)", category: "horror", style: "horror", subtype: "character"),
           PipelineOption(label: "Scene (Horror)", category: "horror", style: "horror", subtype: "scene"),
           PipelineOption(label: "Landscape (Horror)", category: "horror", style: "horror", subtype: "landscape"),
           PipelineOption(label: "Action (Horror)", category: "horror", style: "horror", subtype: "action"),

           // GHOST (3)
           PipelineOption(label: "Close-up (Ghost)", category: "ghost", style: "ghost", subtype: "close"),
           PipelineOption(label: "Mid-Shot (Ghost)", category: "ghost", style: "ghost", subtype: "mid"),
           PipelineOption(label: "Wide-Shot (Ghost)", category: "ghost", style: "ghost", subtype: "wide"),

           // ZOMBIE (4)
           PipelineOption(label: "Close-up (Zombie)", category: "zombie", style: "zombie", subtype: "close"),
           PipelineOption(label: "Mid-Shot (Zombie)", category: "zombie", style: "zombie", subtype: "mid"),
           PipelineOption(label: "Horde (Zombie)", category: "zombie", style: "zombie", subtype: "horde"),
           PipelineOption(label: "Chinese Qing (Zombie)", category: "zombie", style: "zombie", subtype: "chinese"),

           // NO SUBTYPES
           PipelineOption(label: "Closeup Anime", category: "closeup_anime", style: "closeup_anime", subtype: null),
           PipelineOption(label: "Space / Cosmic", category: "space", style: "space", subtype: null),
           PipelineOption(label: "Diffusion Brush", category: "diffusionbrush", style: "diffusionbrush", subtype: null),
        ];
        _flattenedPipelines = pipelines;
        
        // Sort alphabetically or by category?
        // Let's keep them somewhat grouped by category for now, or just alphabetical?
        // _flattenedPipelines.sort((a,b) => a.label.compareTo(b.label));

        if (_flattenedPipelines.isNotEmpty) {
           _selectedOption = _flattenedPipelines.first;
        }
        
        if (schema.ratios.isNotEmpty) _selectedRatio = schema.ratios.first;
        _triggerUpdate();
      });
    } catch (e) {
      if (mounted) setState(() { _error = e.toString(); _isLoading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    if (_isLoading) return Container(height: 60, color: theme.cardColor, child: const Center(child: SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))));
    if (_error != null) return Container(height: 60, color: theme.cardColor, child: Center(child: Text("Error: $_error", style: const TextStyle(color: Colors.red))));
    if (_schema == null) return const SizedBox();



    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: theme.brightness == Brightness.dark ? Colors.black : const Color(0xFFFFFAFA), // Strict colors
        border: Border(top: BorderSide(color: theme.dividerColor)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Row 1: Style Selector
          // Row 1: Unified Pipeline Selector
          GestureDetector(
            onTap: _showPipelineSelector,
            child: Container(
              height: 48,
              padding: const EdgeInsets.symmetric(horizontal: 12),
              decoration: BoxDecoration(
                color: theme.cardColor,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: theme.dividerColor),
              ),
              child: Row(
                children: [
                  Icon(Icons.hub, color: theme.primaryColor, size: 20),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(
                          "Selected Pipeline",
                          style: GoogleFonts.getFont('JetBrains Mono', fontSize: 10, color: theme.textTheme.bodySmall?.color),
                        ),
                        Text(
                           _selectedOption != null 
                             ? "${_selectedOption!.label} (${_selectedOption!.category.toUpperCase()})" 
                             : "Select Pipeline...",
                           style: GoogleFonts.getFont('Outfit', fontSize: 14, fontWeight: FontWeight.bold),
                           maxLines: 1, overflow: TextOverflow.ellipsis,
                        )
                      ],
                    ),
                  ),
                  const Icon(Icons.arrow_drop_down, color: Colors.grey),
                ],
              ),
            ),
          ),
          
          const SizedBox(height: 12),
          
          // Row 2: Controls
          Row(
            children: [
              // Ratio
              _buildDropdown(
                theme, 
                value: _selectedRatio,
                items: ["normal", "portrait", "landscape"], // Hardcoded to 3 as requested
                icon: Icons.aspect_ratio,
                onChanged: (val) {
                  setState(() => _selectedRatio = val!);
                  _triggerUpdate();
                }
              ),
              const SizedBox(width: 8),

              // Seed
              Expanded(
                child: SizedBox(
                  height: 36,
                  child: TextField(
                    controller: _seedController,
                    keyboardType: TextInputType.number,
                    style: GoogleFonts.getFont('JetBrains Mono', fontSize: 12),
                    decoration: InputDecoration(
                      hintText: "Seed",
                      hintStyle: const TextStyle(fontSize: 10),
                      contentPadding: const EdgeInsets.symmetric(horizontal: 8, vertical: 0),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                      filled: true,
                      fillColor: theme.cardColor,
                    ),
                    onChanged: (_) => _triggerUpdate(),
                  ),
                ),
              ),
            ],
          ),
          
          // Show substyle description if available
          if (_selectedOption != null && _schema!.styleDetails.containsKey(_selectedOption!.category))
            Padding(
               padding: const EdgeInsets.only(top: 8),
               child: Text(
                 _schema!.styleDetails[_selectedOption?.category]?.description ?? "",
                 style: const TextStyle(fontSize: 10, color: Colors.grey),
                 maxLines: 2, overflow: TextOverflow.ellipsis,
               )
            ),
            
          const SizedBox(height: 8),
          
          // Status / Cancel Row
          if (_isLoading || _statusText.isNotEmpty)
             Container(
               padding: const EdgeInsets.all(8),
               decoration: BoxDecoration(
                 color: theme.colorScheme.surfaceVariant.withOpacity(0.3),
                 borderRadius: BorderRadius.circular(8),
                 border: Border.all(color: theme.dividerColor.withOpacity(0.5))
               ),
               child: Row(
                 children: [
                   if (_isLoading)
                     SizedBox(width: 12, height: 12, child: CircularProgressIndicator(strokeWidth: 2, color: theme.primaryColor)),
                   if (_isLoading) const SizedBox(width: 8),
                   Expanded(child: Text(_statusText, style: GoogleFonts.getFont('JetBrains Mono', fontSize: 10))),
                 ],
               ),
             )
        ],
      ),
    );
  }

  Widget _buildDropdown(ThemeData theme, {required String value, required List<String> items, required IconData icon, required Function(String?) onChanged}) {
    return Container(
      height: 36,
      padding: const EdgeInsets.symmetric(horizontal: 12),
      decoration: BoxDecoration(
        color: theme.cardColor,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: theme.dividerColor),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<String>(
          value: items.contains(value) ? value : items.first, // Safety
          icon: Padding(padding: const EdgeInsets.only(left: 8), child: Icon(icon, size: 16, color: Colors.grey)),
          isDense: true,
          onChanged: onChanged,
          items: items.map((e) {
             // Capitalize first letter
             final label = e[0].toUpperCase() + e.substring(1);
             return DropdownMenuItem(value: e, child: Text(label, style: GoogleFonts.getFont('Outfit', fontSize: 12)));
          }).toList(),
        ),
      ),
    );
  }

  void _triggerUpdate() {
    int? seed = int.tryParse(_seedController.text);
    widget.onUpdate(
      _selectedOption?.style ?? "Cinematic", 
      _selectedOption?.subtype, 
      _selectedRatio, 
      seed
    );
  }

  void _showPipelineSelector() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true, // Required for DraggableScrollableSheet
      backgroundColor: Colors.transparent, // Let sheet handle background
      builder: (ctx) => _PipelineSearchSheet(
        options: _flattenedPipelines,
        onSelect: (opt) {
          setState(() {
            _selectedOption = opt;
          });
          _triggerUpdate();
          Navigator.pop(ctx);
        }
      )
    );
  }
}

class PipelineOption {
  final String label;
  final String category;
  final String style;
  final String? subtype;

  PipelineOption({required this.label, required this.category, required this.style, required this.subtype});
}

class _PipelineSearchSheet extends StatefulWidget {
  final List<PipelineOption> options;
  final Function(PipelineOption) onSelect;

  const _PipelineSearchSheet({required this.options, required this.onSelect});

  @override
  State<_PipelineSearchSheet> createState() => _PipelineSearchSheetState();
}

class _PipelineSearchSheetState extends State<_PipelineSearchSheet> {
  String _query = "";
  final ScrollController _scrollController = ScrollController(); // Used to sync scroll with drag

  IconData _getIconForCategory(String category) {
    switch (category.toLowerCase()) {
      case 'anime': return Icons.auto_awesome;
      case 'car': return Icons.directions_car_filled;
      case 'drawing': return Icons.brush;
      case 'hyperrealistic': return Icons.camera_alt;
      case 'ethnicity': return Icons.public;
      case 'papercut': return Icons.cut;
      case 'difconsistency': return Icons.science;
      case 'nsfw': return Icons.explicit;
      case 'horror': return Icons.flash_on; 
      case 'ghost': return Icons.blur_on;
      case 'zombie': return Icons.coronavirus;
      case 'space': return Icons.rocket_launch;
      case 'closeup_anime': return Icons.face_retouching_natural;
      case 'diffusionbrush': return Icons.palette;
      default: return Icons.hub;
    }
  }

  Color _getColorForCategory(String category) {
     // A subtle color tint mapping
    switch (category.toLowerCase()) {
      case 'anime': return Colors.pinkAccent;
      case 'car': return Colors.blueAccent;
      case 'horror': return Colors.redAccent;
      case 'zombie': return Colors.greenAccent;
      case 'nsfw': return Colors.deepOrangeAccent;
      case 'space': return Colors.purpleAccent;
      default: return Colors.white;
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    
    // Filter
    final filtered = widget.options.where((opt) {
       final q = _query.toLowerCase();
       return opt.label.toLowerCase().contains(q) || opt.category.toLowerCase().contains(q);
    }).toList();

    return DraggableScrollableSheet(
      initialChildSize: 0.5, // Start at 50% height
      minChildSize: 0.4,     // Minimum 40%
      maxChildSize: 0.9,     // Expand to 90%
      builder: (context, scrollController) {
        return Container(
          decoration: BoxDecoration(
            color: isDark ? const Color(0xFF101010) : Colors.white,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
            boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.4), blurRadius: 20)],
          ),
          child: Column(
            children: [
              // Drag Handle
              Center(
                child: Container(
                  margin: const EdgeInsets.only(top: 12, bottom: 8),
                  width: 40, height: 4,
                  decoration: BoxDecoration(color: Colors.grey.withOpacity(0.3), borderRadius: BorderRadius.circular(2))
                ),
              ),

              // Search Bar
              Padding(
                 padding: const EdgeInsets.fromLTRB(20, 8, 20, 20),
                 child: TextField(
                   autofocus: false,
                   style: GoogleFonts.getFont('Outfit', fontSize: 16),
                   decoration: InputDecoration(
                     hintText: "Search styles...",
                     hintStyle: TextStyle(color: Colors.grey.withOpacity(0.6)),
                     prefixIcon: Icon(Icons.search, color: theme.primaryColor),
                     filled: true,
                     fillColor: isDark ? const Color(0xFF1E1E1E) : Colors.grey[100],
                     border: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: BorderSide.none),
                     contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14)
                   ),
                   onChanged: (v) => setState(() => _query = v),
                 )
              ),
              
              Expanded(
                child: ListView.builder(
                  controller: scrollController, // Vital for DraggableScrollableSheet
                  padding: const EdgeInsets.symmetric(horizontal: 12),
                  itemCount: filtered.length,
                  itemBuilder: (ctx, i) {
                    final item = filtered[i];
                    final icon = _getIconForCategory(item.category);
                    final color = _getColorForCategory(item.category);

                    return TweenAnimationBuilder<double>(
                      tween: Tween(begin: 0.0, end: 1.0),
                      duration: Duration(milliseconds: 300 + (i * 30).clamp(0, 500)),
                      curve: Curves.easeOutCubic,
                      builder: (context, val, child) {
                        return Opacity(
                          opacity: val,
                          child: Transform.translate(
                            offset: Offset(0, 20 * (1 - val)),
                            child: child
                          ),
                        );
                      },
                      child: Container(
                        margin: const EdgeInsets.only(bottom: 8),
                        decoration: BoxDecoration(
                          color: isDark ? const Color(0xFF1A1A1A) : Colors.white,
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: Colors.white.withOpacity(isDark ? 0.05 : 0.5)),
                        ),
                        child: ListTile(
                          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                          leading: Container(
                            padding: const EdgeInsets.all(10),
                            decoration: BoxDecoration(
                              color: color.withOpacity(0.15),
                              shape: BoxShape.circle,
                            ),
                            child: Icon(icon, size: 20, color: color),
                          ),
                          title: Text(
                            item.label, 
                            style: GoogleFonts.getFont('Outfit', fontWeight: FontWeight.w600, fontSize: 15)
                          ),
                          subtitle: Text(
                            item.category.toUpperCase(), 
                            style: GoogleFonts.getFont('JetBrains Mono', fontSize: 10, color: Colors.grey)
                          ),
                          trailing: const Icon(Icons.arrow_forward_ios, size: 12, color: Colors.grey),
                          onTap: () {
                             HapticFeedback.lightImpact();
                             widget.onSelect(item);
                          },
                        ),
                      ),
                    );
                  },
                ),
              )
            ],
          ),
        );
      }
    );
  }
}
