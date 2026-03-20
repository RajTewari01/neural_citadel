import 'dart:io';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'package:image_picker/image_picker.dart';
import '../services/api_service.dart';
import '../models/app_schemas.dart';

class SurgeonView extends StatefulWidget {
  const SurgeonView({super.key});

  @override
  State<SurgeonView> createState() => _SurgeonViewState();
}

class _SurgeonViewState extends State<SurgeonView> {
  SurgeonSchema? _schema;
  bool _isLoadingSchema = true;
  String? _error;

  // Selection
  String _selectedMode = 'auto';
  String? _selectedAssetCategory; // 'clothes' or 'backgrounds'
  String? _selectedAssetName;
  String? _selectedSolidColor;

  bool _isProcessing = false;
  final ImagePicker _picker = ImagePicker();

  @override
  void initState() {
    super.initState();
    _loadSchema();
  }

  Future<void> _loadSchema() async {
    try {
      final api = Provider.of<ApiService>(context, listen: false);
      final schema = await api.getSurgeonSchema();
      setState(() {
        _schema = schema;
        _isLoadingSchema = false;
        if (schema.modes.isNotEmpty) _selectedMode = schema.modes.contains('auto') ? 'auto' : schema.modes.first;
      });
    } catch (e) {
      if (mounted) setState(() { _error = e.toString(); _isLoadingSchema = false; });
    }
  }

  Future<void> _pickAndProcessImage() async {
    try {
      final XFile? image = await _picker.pickImage(source: ImageSource.gallery);
      if (image == null) return;

      setState(() => _isProcessing = true);
      
      final api = Provider.of<ApiService>(context, listen: false);
      
      // Basic feedback
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Uploading and processing image... this may take a moment."))
      );

      final result = await api.processSurgeon(
        mode: _selectedMode,
        imagePath: image.path,
        solidColor: _selectedSolidColor,
        // For assets we'd typically need the actual asset path or ID
        // The API expects 'garment' or 'bg_image' as files if using custom, 
        // or we might need to send asset name in a different field if it's a server-side asset.
        // Assuming 'prompt' or another field handles server-side asset selection for now 
        // or that we aren't supporting server-side assets in this initial mobile implementation fully 
        // without mapping them to local files or specific ID fields.
        // Let's pass asset name as prompt for now if applicable, or just rely on mode.
        prompt: _selectedAssetName, 
      );

      if (mounted) {
        if (result['output_url'] != null) {
            // Show result
            // ideally we'd show it in a dialog or navigate to a result view
            // For now, let's show success message
             ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text("Success! Output: ${result['output_url']}"))
            );
        } else if (result['error'] != null) {
             ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Error: ${result['error']}")));
        }
      }

    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Error: $e")));
    } finally {
      if (mounted) setState(() => _isProcessing = false);
    }
  }
  
  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    if (_isLoadingSchema) return const Center(child: CircularProgressIndicator());
    if (_error != null) return Center(child: Text("Error: $_error"));
    if (_schema == null) return const Center(child: Text("No schema loaded"));

    // Determine what to show based on mode
    // background -> show solid colors OR background assets
    // clothes -> show clothes assets
    // auto -> show both? or simple toggle?

    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
           Text("IMAGE SURGEON", style: GoogleFonts.getFont('JetBrains Mono', fontSize: 20, fontWeight: FontWeight.bold, color: theme.primaryColor, letterSpacing: 1.5)),
           const SizedBox(height: 20),

          // 1. Mode Selector
          Text("OPERATION MODE", style: GoogleFonts.getFont('Outfit', fontWeight: FontWeight.bold, fontSize: 12, color: Colors.grey)),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            children: _schema!.modes.map((mode) {
              final isSelected = _selectedMode == mode;
              return ChoiceChip(
                label: Text(mode.toUpperCase()),
                selected: isSelected,
                onSelected: (v) => setState(() {
                   _selectedMode = mode;
                   // Reset sub-selections
                   _selectedAssetName = null;
                   _selectedSolidColor = null;
                }),
                selectedColor: theme.primaryColor,
                backgroundColor: theme.cardColor,
                labelStyle: TextStyle(color: isSelected ? Colors.white : theme.textTheme.bodyMedium?.color),
              );
            }).toList(),
          ),
          const Divider(height: 32),

          // 2. Dynamic Controls depending on Mode
          if (_selectedMode == 'background') ...[
             Text("BACKGROUND SOURCE", style: GoogleFonts.getFont('Outfit', fontWeight: FontWeight.bold, fontSize: 12, color: Colors.grey)),
             const SizedBox(height: 8),
             
             // Solid Colors
             Text("Solid Colors", style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
             SizedBox(
               height: 50,
               child: ListView.builder(
                 scrollDirection: Axis.horizontal,
                 itemCount: _schema!.solidColors.length,
                 itemBuilder: (ctx, i) {
                   final cName = _schema!.solidColors[i];
                   final c = _getColor(cName);
                   final isSelected = _selectedSolidColor == cName;
                   return GestureDetector(
                     onTap: () => setState(() { _selectedSolidColor = cName; _selectedAssetName = null; }),
                     child: Container(
                       margin: const EdgeInsets.only(right: 8),
                       width: 40, height: 40,
                       decoration: BoxDecoration(
                         color: c,
                         shape: BoxShape.circle,
                         border: Border.all(color: isSelected ? theme.primaryColor : Colors.grey, width: isSelected ? 3 : 1),
                       ),
                     ),
                   );
                 },
               ),
             ),
             const SizedBox(height: 16),
             // Background Assets
             if (_schema!.assets.containsKey('backgrounds')) ...[
                Text("Asset Library", style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                _buildAssetList('backgrounds'),
             ]
          ],

          if (_selectedMode == 'clothes') ...[
             Text("CLOTHING ASSETS", style: GoogleFonts.getFont('Outfit', fontWeight: FontWeight.bold, fontSize: 12, color: Colors.grey)),
             const SizedBox(height: 8),
             if (_schema!.assets.containsKey('clothes'))
                _buildAssetList('clothes')
             else 
                const Text("No clothes assets found."),
          ],
          
          if (_selectedMode == 'auto') ...[
             const Text("Automatic mode will process uploaded image with default settings."),
          ],

          const Spacer(),
          
          // Action Button
          SizedBox(
            width: double.infinity,
            height: 50,
            child: ElevatedButton.icon(
              icon: _isProcessing ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)) : const Icon(Icons.add_photo_alternate),
              label: Text(_isProcessing ? "PROCESSING..." : "SELECT PHOTO & START"),
              style: ElevatedButton.styleFrom(backgroundColor: theme.primaryColor, foregroundColor: Colors.white),
              onPressed: _isProcessing ? null : _pickAndProcessImage,
            ),
          )
        ],
      ),
    );
  }

  Widget _buildAssetList(String category) {
    final assets = _schema!.assets[category] ?? [];
    return SizedBox(
       height: 100,
       child: ListView.builder(
          scrollDirection: Axis.horizontal,
          itemCount: assets.length,
          itemBuilder: (ctx, i) {
             final name = assets[i];
             final isSelected = _selectedAssetName == name;
             return GestureDetector(
               onTap: () => setState(() { _selectedAssetName = name; _selectedSolidColor = null; }),
               child: Container(
                 width: 80,
                 margin: const EdgeInsets.only(right: 8),
                 decoration: BoxDecoration(
                   color: isSelected ? Theme.of(context).primaryColor.withOpacity(0.1) : Theme.of(context).cardColor,
                   border: isSelected ? Border.all(color: Theme.of(context).primaryColor) : null,
                   borderRadius: BorderRadius.circular(8),
                 ),
                 child: Center(child: Text(name, textAlign: TextAlign.center, style: TextStyle(fontSize: 12))),
               ),
             );
          },
       ),
    );
  }

  Color _getColor(String name) {
    switch(name.toLowerCase()) {
      case 'white': return Colors.white;
      case 'red': return Colors.red;
      case 'green': return Colors.green;
      case 'blue': return Colors.blue;
      case 'gray': case 'grey': return Colors.grey;
      case 'yellow': return Colors.yellow;
      case 'cyan': return Colors.cyan;
      case 'magenta': return const Color(0xFFFF00FF);
      case 'orange': return Colors.orange;
      case 'pink': return Colors.pink;
      case 'purple': return Colors.purple;
      default: return Colors.black;
    }
  }
}
