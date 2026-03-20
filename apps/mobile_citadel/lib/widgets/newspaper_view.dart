import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:path_provider/path_provider.dart';
import 'package:http/http.dart' as http;
import '../services/api_service.dart';
import '../models/app_schemas.dart';
import 'pdf_viewer_screen.dart';

class NewspaperView extends StatefulWidget {
  const NewspaperView({super.key});

  @override
  State<NewspaperView> createState() => _NewspaperViewState();
}

class _NewspaperViewState extends State<NewspaperView> {
  NewspaperSchema? _schema;
  bool _isLoadingSchema = true;
  String? _error;

  String _selectedStyle = "Classic";
  String _selectedRegion = "GLOBAL";
  String _selectedLanguage = "English";
  String? _selectedSubstyle;
  bool _isOfflineMode = false;

  bool _isGenerating = false;
  bool _isCancelled = false;
  String? _pdfPath;
  
  List<String> _logs = [];
  final ScrollController _logScrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    _loadSchema();
  }

  Future<void> _loadSchema() async {
    try {
      final api = Provider.of<ApiService>(context, listen: false);
      final schema = await api.getNewspaperSchema();
      setState(() {
        _schema = schema;
        _isLoadingSchema = false;
        if (schema.styles.isNotEmpty) _selectedStyle = schema.styles.first;
        if (schema.regions.isNotEmpty) _selectedRegion = schema.regions.first;
        // Keep English as default if present, else first
        if (schema.languages.contains("English")) {
             _selectedLanguage = "English";
        } else if (schema.languages.isNotEmpty) {
             _selectedLanguage = schema.languages.first;
        }
      });
    } catch (e) {
      if (mounted) setState(() { _error = e.toString(); _isLoadingSchema = false; });
    }
  }

  void _cancelGeneration() async {
     setState(() { _isCancelled = true; _isGenerating = false; });
     final api = Provider.of<ApiService>(context, listen: false);
     await api.cancelNewspaperGeneration();
     if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Generation Cancelled")));
  }

  void _generate() async {
      setState(() { 
        _isGenerating = true; 
        _isCancelled = false; 
        _pdfPath = null; 
        _logs = ["Initializing Publisher..."]; 
      });
      
      String? tempPath;
      
      try {
        final api = Provider.of<ApiService>(context, listen: false);
        
        await for (final line in api.generateNewspaperStream(
          style: _selectedStyle,
          region: _selectedRegion,
          language: _selectedLanguage,
          substyle: _selectedSubstyle,
          translationMode: _isOfflineMode ? 'offline' : 'online',
        )) {
          if (_isCancelled) break; 
          
          if (line.isNotEmpty) {
             setState(() {
               _logs.add(line);
             });
             // Auto-scroll
             if (_logScrollController.hasClients) {
               _logScrollController.animateTo(
                 _logScrollController.position.maxScrollExtent,
                 duration: const Duration(milliseconds: 200),
                 curve: Curves.easeOut,
               );
             }
          }

          if (line.startsWith('RESULT:') || line.contains('.pdf')) {
            String raw = line.replaceAll('RESULT:', '').trim();
            if (raw.contains('.pdf')) {
               if (raw.startsWith('"') && raw.endsWith('"')) raw = raw.substring(1, raw.length - 1);
               tempPath = raw;
            } else {
              try {
                final json = jsonDecode(line);
                 if (json['path'] != null) tempPath = json['path'];
              } catch(e) {}
            }
          }
        }
        
        if (_isCancelled) return;

        if (mounted && tempPath != null) {
          setState(() => _pdfPath = tempPath);
          _downloadAndOpenPdf(tempPath); // Auto-open in app
        }
      } catch (e) {
        if (mounted && !_isCancelled) {
          setState(() => _logs.add("Error: $e"));
        }
      } finally {
        if (mounted) setState(() => _isGenerating = false);
      }
  }

  Future<void> _downloadAndOpenPdf(String serverPath) async {
      final api = Provider.of<ApiService>(context, listen: false);
      String url = serverPath;
      String filename = "newspaper.pdf";
      
      if (!url.startsWith('http')) {
        filename = url.split(RegExp(r'[/\\]')).last;
        url = "${api.baseUrl}/static/generated/newspaper/$filename";
      }

      try {
        if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Downloading PDF...")));
        
        final response = await http.get(Uri.parse(url));
        if (response.statusCode == 200) {
           final dir = await getTemporaryDirectory();
           final file = File('${dir.path}/$filename');
           await file.writeAsBytes(response.bodyBytes);
           
           if (mounted) {
             Navigator.push(context, MaterialPageRoute(
               builder: (_) => PDFViewerScreen(filePath: file.path, fileName: filename)
             ));
           }
        } else {
           throw Exception("Download failed: ${response.statusCode}");
        }
      } catch (e) {
        if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Could not open PDF: $e")));
      }
  }
  
  // Keep _downloadPdf for external opening if needed
  // ...

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    // ... setup ...
    final List<String> substyles = (_selectedStyle == "Magazine") ? _schema!.magazineSubstyles : [];

    return Padding(
      padding: const EdgeInsets.all(16),
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ... Header ...
            Text("NEWSPAPER AGENT", style: GoogleFonts.getFont('JetBrains Mono', fontSize: 20, fontWeight: FontWeight.bold, color: theme.primaryColor, letterSpacing: 1.5)),
            const SizedBox(height: 20),
            
            // ... Selectors (Style, Region, Language) ...
            Text("PUBLICATION STYLE", style: GoogleFonts.getFont('Outfit', fontWeight: FontWeight.bold, fontSize: 12, color: Colors.grey)),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              children: _schema!.styles.map((style) {
                final isSelected = _selectedStyle == style;
                return ChoiceChip(
                  label: Text(style),
                  selected: isSelected,
                  onSelected: (v) => setState(() {
                    _selectedStyle = style; 
                    if (style != "Magazine") _selectedSubstyle = null;
                    else if (substyles.isNotEmpty) _selectedSubstyle = substyles.first;
                  }),
                  selectedColor: theme.primaryColor,
                  backgroundColor: theme.cardColor,
                  labelStyle: TextStyle(color: isSelected ? Colors.white : theme.textTheme.bodyMedium?.color),
                );
              }).toList(),
            ),

            if (substyles.isNotEmpty) ...[
               const SizedBox(height: 16),
               Text("MAGAZINE THEME (${substyles.length} Available)", style: GoogleFonts.getFont('Outfit', fontWeight: FontWeight.bold, fontSize: 12, color: Colors.grey)),
               const SizedBox(height: 8),
               Container(
                 height: 40,
                 child: ListView.builder(
                   scrollDirection: Axis.horizontal,
                   itemCount: substyles.length,
                   itemBuilder: (ctx, i) {
                      final sub = substyles[i];
                      final isSelected = _selectedSubstyle == sub;
                      return Padding(
                        padding: const EdgeInsets.only(right: 8),
                        child: ChoiceChip(
                          label: Text(sub, style: const TextStyle(fontSize: 10)),
                          selected: isSelected,
                          onSelected: (v) => setState(() => _selectedSubstyle = sub),
                          selectedColor: theme.primaryColor.withOpacity(0.7),
                        ),
                      );
                   },
                 ),
               ),
            ],
            
            const Divider(height: 32),
            
             // Region & Language Rows
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text("REGION", style: GoogleFonts.getFont('Outfit', fontWeight: FontWeight.bold, fontSize: 12, color: Colors.grey)),
                      const SizedBox(height: 8),
                      DropdownButtonFormField<String>(
                         value: _selectedRegion,
                         decoration: InputDecoration(
                           filled: true, fillColor: theme.cardColor,
                           contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 0),
                           border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                         ),
                         items: _schema!.regions.map((r) => DropdownMenuItem(value: r, child: Text(r, style: const TextStyle(fontSize: 12)))).toList(),
                         onChanged: (v) => setState(() => _selectedRegion = v!),
                      )
                    ],
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text("LANGUAGE", style: GoogleFonts.getFont('Outfit', fontWeight: FontWeight.bold, fontSize: 12, color: Colors.grey)),
                      const SizedBox(height: 8),
                       DropdownButtonFormField<String>(
                         value: _selectedLanguage,
                         decoration: InputDecoration(
                           filled: true, fillColor: theme.cardColor,
                           contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 0),
                           border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                         ),
                         items: _schema!.languages.map((l) => DropdownMenuItem(value: l, child: Text(l, style: const TextStyle(fontSize: 12)))).toList(),
                         onChanged: (v) => setState(() => _selectedLanguage = v!),
                      )
                    ],
                  ),
                ),
              ],
            ),

            const SizedBox(height: 24),

            // Translation Switch
             Container(
               padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
               decoration: BoxDecoration(
                 color: theme.cardColor,
                 borderRadius: BorderRadius.circular(12),
                 border: Border.all(color: Colors.grey.withOpacity(0.2))
               ),
               child: SwitchListTile(
                 title: Text(_isOfflineMode ? "Offline Translation (NLLB)" : "Online Translation (Google)", style: GoogleFonts.getFont('Outfit', fontWeight: FontWeight.bold)),
                 subtitle: Text(_isOfflineMode ? "Slow, runs locally on device." : "Fast, requires internet connection.", style: const TextStyle(fontSize: 12)),
                 value: _isOfflineMode,
                 onChanged: (v) => setState(() => _isOfflineMode = v),
                 activeColor: theme.primaryColor,
               ),
             ),
             
             const SizedBox(height: 40),

             // Generate Log Console (Visible if logs exist)
             if (_logs.isNotEmpty) ...[
               Container(
                 height: 150,
                 width: double.infinity,
                 padding: const EdgeInsets.all(12),
                 decoration: BoxDecoration(
                   color: Colors.black,
                   borderRadius: BorderRadius.circular(8),
                   border: Border.all(color: Colors.grey.withOpacity(0.3))
                 ),
                 child: ListView.builder(
                   controller: _logScrollController,
                   itemCount: _logs.length,
                   itemBuilder: (ctx, i) => Text(
                     _logs[i], 
                     style: GoogleFonts.firaCode(fontSize: 10, color: Colors.greenAccent)
                   ),
                 ),
               ),
               const SizedBox(height: 20),
             ],

             // Generate / Cancel Button
             SizedBox(
              width: double.infinity,
              height: 50,
              child: _isGenerating 
                ? OutlinedButton.icon(
                    onPressed: _cancelGeneration,
                    icon: const Icon(Icons.cancel, color: Colors.red),
                    label: const Text("CANCEL GENERATION", style: TextStyle(color: Colors.red)),
                    style: OutlinedButton.styleFrom(side: const BorderSide(color: Colors.red)),
                  )
                : ElevatedButton.icon(
                    icon: const Icon(Icons.print),
                    label: const Text("GENERATE EDITION"),
                    style: ElevatedButton.styleFrom(backgroundColor: theme.primaryColor, foregroundColor: Colors.white),
                    onPressed: _generate,
                  ),
            ),
            
            // Download Button
            if (_pdfPath != null && !_isGenerating) ...[
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                height: 50,
                child: OutlinedButton.icon(
                  icon: const Icon(Icons.open_in_new),
                  label: const Text("OPEN IN VIEWER"),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: theme.primaryColor,
                    side: BorderSide(color: theme.primaryColor),
                  ),
                  onPressed: () => _downloadAndOpenPdf(_pdfPath!),
                ),
              ),
           ],
           
           const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }
}
