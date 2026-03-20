import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'package:screenshot/screenshot.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:io';

import '../../services/api_service.dart';
import '../../services/auth_service.dart';
import '../../theme/app_theme.dart';

class BugReportDialog extends StatefulWidget {
  final File screenshot;
  
  const BugReportDialog({super.key, required this.screenshot});

  @override
  State<BugReportDialog> createState() => _BugReportDialogState();
}

class _BugReportDialogState extends State<BugReportDialog> {
  final _titleCtrl = TextEditingController();
  final _descriptionCtrl = TextEditingController();
  final _stepsCtrl = TextEditingController();
  bool _isSending = false;
  String _selectedSeverity = "Critical"; // Default to Critical
  final List<File> _attachments = [];
  final ImagePicker _picker = ImagePicker();

  @override
  void initState() {
    super.initState();
    _attachments.add(widget.screenshot);
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      backgroundColor: Colors.transparent,
      insetPadding: const EdgeInsets.all(16),
      child: Container(
        decoration: BoxDecoration(
          color: const Color(0xFF0F0F10).withOpacity(0.95), // Deep matte black
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppTheme.neonBlue.withOpacity(0.5), width: 1.5),
          boxShadow: [
            BoxShadow(color: AppTheme.neonBlue.withOpacity(0.2), blurRadius: 20, spreadRadius: 2),
          ],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Header
            Container(
              padding: const EdgeInsets.all(16),
              decoration: const BoxDecoration(
                border: Border(bottom: BorderSide(color: Colors.white10)),
              ),
              child: Row(
                children: [
                  const Icon(Icons.warning_amber_rounded, color: AppTheme.neonBlue),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text("SYSTEM EXCEPTION REPORT", 
                          style: GoogleFonts.orbitron(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16, letterSpacing: 1.2)),
                        Text("Anomaly Detection Protocol Active", 
                          style: GoogleFonts.shareTechMono(color: Colors.white54, fontSize: 10)),
                      ],
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close, color: Colors.white54),
                    onPressed: () => Navigator.pop(context),
                  )
                ],
              ),
            ),
            
            // Content
            Flexible(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                     _buildLabel("SEVERITY LEVEL"),
                     Row(
                       children: [
                         _buildRadioChip("Low", Colors.green),
                         const SizedBox(width: 8),
                         _buildRadioChip("Medium", Colors.amber),
                         const SizedBox(width: 8),
                         _buildRadioChip("Critical", Colors.redAccent),
                       ],
                     ),
                     const SizedBox(height: 16),

                     _buildLabel("TITLE"),
                     _buildTextField("Brief summary of the anomaly...", _titleCtrl, singleLine: true),
                     const SizedBox(height: 16),
                     
                     _buildLabel("DETAILED LOG"),
                     _buildTextField("Describe the expected vs actual behavior...", _descriptionCtrl, lines: 4),
                     const SizedBox(height: 16),
                     
                     _buildLabel("REPRODUCTION STEPS"),
                     _buildTextField("1. ...\n2. ...", _stepsCtrl, lines: 3),
                     const SizedBox(height: 16),

                     _buildLabel("EVIDENCE CACHE (${_attachments.length} files)"),
                     const SizedBox(height: 8),
                     SizedBox(
                       height: 80,
                       child: ListView.separated(
                         scrollDirection: Axis.horizontal,
                         itemCount: _attachments.length + 1,
                         separatorBuilder: (_, __) => const SizedBox(width: 8),
                         itemBuilder: (context, index) {
                           if (index == _attachments.length) {
                             return GestureDetector(
                               onTap: _pickImages,
                               child: Container(
                                 width: 80,
                                 decoration: BoxDecoration(
                                   color: Colors.white.withOpacity(0.05),
                                   borderRadius: BorderRadius.circular(8),
                                   border: Border.all(color: Colors.white24, style: BorderStyle.solid),
                                 ),
                                 child: const Icon(Icons.add_photo_alternate, color: Colors.white54),
                               ),
                             );
                           }
                           return Stack(
                             clipBehavior: Clip.none,
                             children: [
                               GestureDetector(
                                 onTap: () => _showFullImage(_attachments[index]),
                                 child: Container(
                                   width: 80,
                                   decoration: BoxDecoration(
                                      borderRadius: BorderRadius.circular(8),
                                      border: Border.all(color: AppTheme.neonBlue.withOpacity(0.3)),
                                      image: DecorationImage(image: FileImage(_attachments[index]), fit: BoxFit.cover),
                                   ),
                                 ),
                               ),
                               Positioned(
                                 top: -5,
                                 right: -5,
                                 child: GestureDetector(
                                   onTap: () => setState(() => _attachments.removeAt(index)),
                                   child: const CircleAvatar(radius: 10, backgroundColor: Colors.red, child: Icon(Icons.close, size: 12)),
                                 ),
                               )
                             ],
                           );
                         },
                       ),
                     )
                  ],
                ),
              ),
            ),
            
            // Footer
            Padding(
              padding: const EdgeInsets.all(16),
              child: ElevatedButton(
                onPressed: _isSending ? null : _sendReport,
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.neonBlue,
                  foregroundColor: Colors.black,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                  elevation: 0,
                ),
                child: _isSending 
                  ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.black))
                  : Text("TRANSMIT DIAGNOSTICS", style: GoogleFonts.orbitron(fontWeight: FontWeight.bold, letterSpacing: 1)),
              ),
            )
          ],
        ),
      ),
    );
  }

  Widget _buildLabel(String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Text(text, style: GoogleFonts.shareTechMono(color: AppTheme.neonBlue, fontSize: 12, fontWeight: FontWeight.bold)),
    );
  }

  Widget _buildTextField(String hint, TextEditingController ctrl, {int lines = 1, bool singleLine = false}) {
      return TextField(
        controller: ctrl,
        style: const TextStyle(color: Colors.white, fontSize: 13),
        maxLines: singleLine ? 1 : lines,
        minLines: singleLine ? 1 : (lines > 2 ? 2 : 1),
        decoration: InputDecoration(
          hintText: hint,
          hintStyle: const TextStyle(color: Colors.white24),
          filled: true,
          fillColor: Colors.black38,
          contentPadding: const EdgeInsets.all(12),
          enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(4), borderSide: const BorderSide(color: Colors.white10)),
          focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(4), borderSide: const BorderSide(color: AppTheme.neonBlue)),
        ),
      );
  }

  Widget _buildRadioChip(String label, Color color) {
    bool isSelected = _selectedSeverity == label;
    return GestureDetector(
      onTap: () => setState(() => _selectedSeverity = label),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: isSelected ? color.withOpacity(0.2) : Colors.transparent,
          border: Border.all(color: isSelected ? color : Colors.white10),
          borderRadius: BorderRadius.circular(20),
        ),
        child: Text(label, style: TextStyle(color: isSelected ? color : Colors.white54, fontSize: 12, fontWeight: isSelected ? FontWeight.bold : FontWeight.normal)),
      ),
    );
  }

  void _showFullImage(File imageFile) {
    showDialog(
      context: context,
      builder: (ctx) => Dialog(
        backgroundColor: Colors.transparent,
        insetPadding: EdgeInsets.zero,
        child: Stack(
          alignment: Alignment.center,
          children: [
            InteractiveViewer(
               child: Image.file(imageFile),
            ),
            Positioned(
              top: 40,
              right: 20,
              child: IconButton(
                icon: const Icon(Icons.close, color: Colors.white, size: 30),
                onPressed: () => Navigator.pop(ctx),
              ),
            )
          ],
        ),
      )
    );
  }

  Future<void> _pickImages() async {
    final List<XFile> images = await _picker.pickMultiImage();
    if (images.isNotEmpty) {
      setState(() {
        _attachments.addAll(images.map((x) => File(x.path)));
      });
    }
  }

  Future<void> _sendReport() async {
    if (_titleCtrl.text.isEmpty) {
       ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Title is required"), backgroundColor: Colors.red));
       return;
    }

    setState(() => _isSending = true);
    
    final api = Provider.of<ApiService>(context, listen: false);
    final auth = Provider.of<AuthService>(context, listen: false);
    
    try {
      // Send only the first image for now until API supports multi-part lists
      // Real implementation would loop or send list
      // We will concatenate the description with step info for now
      String fullDesc = "SEVERITY: $_selectedSeverity\n\nTITLE: ${_titleCtrl.text}\n\nDESCRIPTION:\n${_descriptionCtrl.text}\n\nSTEPS:\n${_stepsCtrl.text}";
      
      await api.reportBug(
        description: fullDesc,
        steps: _stepsCtrl.text, // Keeping this for backward compat if param exists
        userId: auth.currentUser?['id'].toString() ?? "Anonymous",
        screenshotPath: widget.screenshot.path // Sending primary screenshot
      );

      if (mounted) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text("Diagnostics Transmitted. Files: ${_attachments.length}. ID: #${DateTime.now().millisecondsSinceEpoch.toString().substring(8)}"),
          backgroundColor: AppTheme.neonBlue,
          behavior: SnackBarBehavior.floating, 
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        ));
      }
    } catch (e) {
      if (mounted) {
         ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Transmission Failed: $e"), backgroundColor: Colors.red));
      }
    } finally {
      if (mounted) setState(() => _isSending = false);
    }
  }
}
