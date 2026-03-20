import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:image_picker/image_picker.dart';
import 'package:path_provider/path_provider.dart';
import 'package:path/path.dart' as path;
import 'dart:io';
import '../../services/contact_service.dart';
import '../../services/physics_manager.dart';
import '../../ui/physics/physics_background.dart';
import 'package:flutter_contacts/flutter_contacts.dart';

class EditContactScreen extends StatefulWidget {
  final RichContact? contact; // null = new contact
  final ContactService contactService;
  final String? initialNumber;

  const EditContactScreen({super.key, this.contact, required this.contactService, this.initialNumber});

  @override
  State<EditContactScreen> createState() => _EditContactScreenState();
}

class _EditContactScreenState extends State<EditContactScreen> {
  late TextEditingController _nameController;
  late TextEditingController _phoneController;
  late TextEditingController _emailController;
  late TextEditingController _addressController;
  late TextEditingController _imController;
  late TextEditingController _websiteController;
  late TextEditingController _noteController;

  // Labels
  String _phoneLabel = "Mobile";
  String _emailLabel = "Home";
  String _addressLabel = "Home";
  String _imLabel = "AIM";
  
  // Image State
  File? _pickedImage;
  String? _currentImagePath;
  String _selectedTheme = "water";

  @override
  void initState() {
    super.initState();
    _selectedTheme = widget.contact?.theme ?? "water";
    _nameController = TextEditingController(text: widget.contact?.displayName ?? "");
    _phoneController = TextEditingController(text: widget.contact?.phones.isNotEmpty == true ? widget.contact!.phones.first.number : (widget.initialNumber ?? ""));
    final email = widget.contact?.nativeContact.emails.isNotEmpty == true ? widget.contact!.nativeContact.emails.first.address : "";
    _emailController = TextEditingController(text: email);
    // Basic address/note/etc extraction (simplified, usually list)
    _addressController = TextEditingController(text: widget.contact?.nativeContact.addresses.isNotEmpty == true ? widget.contact!.nativeContact.addresses.first.address : "");
    _imController = TextEditingController(); // IM not standard in basics, need advanced extraction
    _websiteController = TextEditingController(text: widget.contact?.nativeContact.websites.isNotEmpty == true ? widget.contact!.nativeContact.websites.first.url : "");
    _noteController = TextEditingController(text: widget.contact?.nativeContact.notes.isNotEmpty == true ? widget.contact!.nativeContact.notes.first.note : "");
    
    _currentImagePath = widget.contact?.customImage;
  }

  @override
  void dispose() {
    _nameController.dispose();
    _phoneController.dispose();
    _emailController.dispose();
    _addressController.dispose();
    _imController.dispose();
    _websiteController.dispose();
    _noteController.dispose();
    super.dispose();
  }
  
  Future<void> _pickImage() async {
    final picker = ImagePicker();
    final pickedFile = await picker.pickImage(source: ImageSource.gallery);

    if (pickedFile != null) {
      setState(() {
        _pickedImage = File(pickedFile.path);
      });
    }
  }

  Future<String?> _saveImageToLocal(File image) async {
    try {
      final appDir = await getApplicationDocumentsDirectory();
      final id = widget.contact?.id ?? "new_${DateTime.now().millisecondsSinceEpoch}";
      final fileName = 'contact_${id}_${DateTime.now().millisecondsSinceEpoch}${path.extension(image.path)}';
      final savedImage = await image.copy('${appDir.path}/$fileName');
      return savedImage.path;
    } catch (e) {
      debugPrint("Error saving image: $e");
      return null;
    }
  }

  Future<void> _save() async {
    if (_nameController.text.isEmpty && _phoneController.text.isEmpty) return;

    try {
        if (widget.contact == null || widget.contact!.id.isEmpty) {
          // New Contact or Saving Unsaved Recents
          final newId = await widget.contactService.addContact(_nameController.text, "", _phoneController.text);
          if (newId != null) {
             String? newImagePath;
             if (_pickedImage != null) {
                 // Creating logic for image saving requires a valid ID usually, but our helper generates a temp ID if null
                 newImagePath = await _saveImageToLocal(_pickedImage!);
             }
             
             await widget.contactService.updateNeuralProfile(
               newId,
               theme: _selectedTheme,
               imagePath: newImagePath,
             );
          }
        } else {
           // Update Existing Native
           final native = widget.contact!.nativeContact;
           native.displayName = _nameController.text;
           native.name.first = _nameController.text.split(" ").first;
           native.name.last = _nameController.text.split(" ").length > 1 ? _nameController.text.split(" ").sublist(1).join(" ") : "";
           
           // Phones (Overwrite first or add)
           if (native.phones.isNotEmpty) {
             native.phones[0].number = _phoneController.text;
             native.phones[0].label = _phoneLabelsMap[_phoneLabel] ?? PhoneLabel.mobile;
           } else {
             native.phones = [Phone(_phoneController.text, label: _phoneLabelsMap[_phoneLabel] ?? PhoneLabel.mobile)];
           }
           
           // Emails
           if (_emailController.text.isNotEmpty) {
             if (native.emails.isNotEmpty) native.emails[0].address = _emailController.text;
             else native.emails = [Email(_emailController.text)];
           }
           
           // Addresses
           if (_addressController.text.isNotEmpty) {
             if (native.addresses.isNotEmpty) native.addresses[0].address = _addressController.text;
             else native.addresses = [Address(_addressController.text)];
           }
           
           // Notes
           if (_noteController.text.isNotEmpty) {
             if (native.notes.isNotEmpty) native.notes[0].note = _noteController.text;
             else native.notes = [Note(_noteController.text)];
           }
           
           await native.update();
           
           // Update Neural Profile (Image)
           String? newImagePath = _currentImagePath;
           if (_pickedImage != null) {
              newImagePath = await _saveImageToLocal(_pickedImage!);
           }
           
           await widget.contactService.updateNeuralProfile(
             widget.contact!.id,
             imagePath: newImagePath,
             theme: _selectedTheme,
           );
        }
        
        if (mounted) Navigator.pop(context, true);
    } catch (e) {
       debugPrint("Error saving contact: $e");
       if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Error saving: $e")));
    }
  }

  static const Map<String, PhoneLabel> _phoneLabelsMap = {
    "Mobile": PhoneLabel.mobile, "Home": PhoneLabel.home, "Work": PhoneLabel.work, "Main": PhoneLabel.main
  };

  @override
  Widget build(BuildContext context) {
    ImageProvider? bgImage;
     if (_pickedImage != null) {
      bgImage = FileImage(_pickedImage!);
    } else if (_currentImagePath != null && File(_currentImagePath!).existsSync()) {
      bgImage = FileImage(File(_currentImagePath!));
    } else if (widget.contact?.nativeContact.thumbnail != null) {
      bgImage = MemoryImage(widget.contact!.nativeContact.thumbnail!);
    }

    return Scaffold(
      backgroundColor: Colors.black,
      
      appBar: AppBar(
        backgroundColor: Colors.black,
        elevation: 0,
        leading: IconButton(icon: Icon(Icons.close, color: Colors.white), onPressed: () => Navigator.pop(context)),
        title: Text(widget.contact == null ? "Create contact" : "Edit contact", style: GoogleFonts.outfit(color: Colors.white, fontSize: 22)),
        actions: [
          IconButton(icon: Icon(Icons.check, color: Colors.white), onPressed: _save),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
             // Avatar Picker
             GestureDetector(
                onTap: _pickImage,
                child: Container(
                  width: 100, height: 100,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: Colors.white10,
                    image: bgImage != null ? DecorationImage(image: bgImage, fit: BoxFit.cover) : null,
                    border: Border.all(color: Colors.cyanAccent, width: 1),
                  ),
                  child: bgImage == null ? Icon(Icons.add_a_photo, color: Colors.white54) : null,
                ),
             ),
             if (bgImage != null) Padding(
               padding: const EdgeInsets.only(top: 8.0),
               child: Text("Change Photo", style: GoogleFonts.outfit(color: Colors.cyanAccent, fontSize: 12)),
             ),
             
             const SizedBox(height: 24),

            // Expansion for Name (First/Last) - simplified to one line for layout matching
             _buildField("Name", _nameController, icon: Icons.person, showExpand: true),
             const SizedBox(height: 24),
             
             _buildField("Phone", _phoneController, icon: Icons.phone, labelSelector: _phoneLabel, onLabelTap: () => _pickLabel("Phone", (v)=>setState(()=>_phoneLabel=v))),
             const SizedBox(height: 24),

             _buildField("Email", _emailController, icon: Icons.email, labelSelector: _emailLabel, onLabelTap: () => _pickLabel("Email", (v)=>setState(()=>_emailLabel=v))),
             const SizedBox(height: 24),
             
             _buildField("Address", _addressController, icon: Icons.location_on, labelSelector: _addressLabel, onLabelTap: () => _pickLabel("Address", (v)=>setState(()=>_addressLabel=v))),
             const SizedBox(height: 24),
             
             _buildField("IM", _imController, icon: Icons.chat, labelSelector: _imLabel, onLabelTap: () => _pickLabel("IM", (v)=>setState(()=>_imLabel=v))),
             const SizedBox(height: 24),

             _buildField("Website", _websiteController, icon: Icons.language),
             const SizedBox(height: 24),
             
             _buildDateSelector("Date"),
             const SizedBox(height: 24),

             _buildField("Notes", _noteController, icon: Icons.note, isMultiLine: true),
             
             const SizedBox(height: 40),
             // THEME SELECTOR (PHYSICS)
             GestureDetector(
               onTap: () => _pickTheme(),
               child: Container(
                 padding: const EdgeInsets.all(16),
                 decoration: BoxDecoration(border: Border.all(color: Colors.white24), borderRadius: BorderRadius.circular(8)),
                 child: Row(
                   mainAxisAlignment: MainAxisAlignment.spaceBetween,
                   children: [
                     Row(children: [const Icon(Icons.bubble_chart, color: Colors.white54), const SizedBox(width: 16), Text("Liquid Physics", style: GoogleFonts.outfit(color: Colors.white))]),
                     Text(_selectedTheme.toUpperCase(), style: GoogleFonts.sourceCodePro(color: Colors.cyanAccent)),
                   ],
                 ),
               ),
             ),
          ],
        ),
      ),
    );
  }

  Widget _buildField(String hint, TextEditingController controller, {IconData? icon, String? labelSelector, VoidCallback? onLabelTap, bool showExpand = false, bool isMultiLine = false}) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon ?? Icons.circle, color: Colors.white54, size: 24),
        const SizedBox(width: 16),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
               if (labelSelector != null)
                 GestureDetector(
                   onTap: onLabelTap,
                   child: Row(
                     mainAxisSize: MainAxisSize.min,
                     children: [
                       Text(labelSelector, style: GoogleFonts.outfit(color: Colors.white, fontWeight: FontWeight.bold)),
                       Icon(Icons.arrow_drop_down, color: Colors.white),
                     ],
                   ),
                 ),
               
               TextField(
                 controller: controller,
                 maxLines: isMultiLine ? 3 : 1,
                 style: GoogleFonts.outfit(color: Colors.white, fontSize: 16),
                 decoration: InputDecoration(
                   hintText: hint,
                   hintStyle: GoogleFonts.outfit(color: Colors.white38),
                   enabledBorder: UnderlineInputBorder(borderSide: BorderSide(color: Colors.white24)),
                   focusedBorder: UnderlineInputBorder(borderSide: BorderSide(color: Colors.cyanAccent)),
                   suffixIcon: showExpand ? Icon(Icons.expand_more, color: Colors.white54) : null,
                 ),
               ),
            ],
          ),
        )
      ],
    );
  }
  
  Widget _buildDateSelector(String label) {
     return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(Icons.calendar_today, color: Colors.white54, size: 24),
        const SizedBox(width: 16),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
               Text("Date", style: GoogleFonts.outfit(color: Colors.white, fontWeight: FontWeight.bold)),
               Container(
                 padding: EdgeInsets.symmetric(vertical: 12),
                  decoration: BoxDecoration(border: Border(bottom: BorderSide(color: Colors.white24))),
                  child: Text("Pick Date", style: GoogleFonts.outfit(color: Colors.white38)),
               )
            ],
          ),
        )
      ],
    );
  }

  void _pickLabel(String title, Function(String) onSelect) {
    showModalBottomSheet(context: context, builder: (ctx) => Container(
      color: Colors.black, // Dark BG
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: ["Home", "Work", "Mobile", "Other"].map((l) => ListTile(
          title: Text(l, style: TextStyle(color: Colors.white)),
          onTap: () {
            onSelect(l);
            Navigator.pop(ctx);
          },
        )).toList(),
      ),
    ));
  }

  void _pickTheme() {
    final modes = [
      PhysicsMode.gravityOrbs, 
      PhysicsMode.matrixRain, 
      PhysicsMode.cyberGrid, 
      PhysicsMode.nebulaPulse, 
      PhysicsMode.liquidMetal,
      PhysicsMode.blackHole,
      PhysicsMode.digitalDna,
      PhysicsMode.hexagonHive,
      PhysicsMode.starfieldWarp,
      PhysicsMode.audioWave,
      PhysicsMode.chineseScroll,
    ];
    
    showModalBottomSheet(
      context: context, 
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => Container(
        height: MediaQuery.of(context).size.height * 0.8,
        decoration: BoxDecoration(
           color: Colors.black,
           borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
           border: Border(top: BorderSide(color: Colors.cyanAccent.withOpacity(0.5))),
        ),
        child: Column(
          children: [
             Padding(
               padding: const EdgeInsets.all(16),
               child: Text("SELECT NEURAL ENGINE", style: GoogleFonts.orbitron(color: Colors.white, fontSize: 18)),
             ),
             Expanded(
               child: ListView.builder(
                 itemCount: modes.length,
                 itemBuilder: (context, index) {
                    final m = modes[index];
                    final name = m.toString().split('.').last.toUpperCase();
                    final isSelected = _selectedTheme == m.toString().split('.').last;
                    
                    return GestureDetector(
                      onTap: () {
                         setState(() => _selectedTheme = m.toString().split('.').last);
                         Navigator.pop(ctx);
                      },
                      child: Container(
                        height: 120,
                        margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(16),
                          child: Stack(
                            children: [
                              // 1. Full Physics Background
                              Positioned.fill(child: PhysicsBackground(mode: m)),
                              
                              // 2. 50% Transparency Overlay ("The 50 Perfect Transparency")
                              Positioned.fill(child: Container(color: Colors.black.withOpacity(0.5))),
                              
                              // 3. Text & Selection
                              Center(
                                child: Row(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                     Text(
                                       name, 
                                       style: GoogleFonts.orbitron(
                                         color: Colors.white, 
                                         fontWeight: FontWeight.bold, 
                                         fontSize: 24,
                                         letterSpacing: 2.0
                                       )
                                     ),
                                     if (isSelected) ...[
                                       const SizedBox(width: 12),
                                       const Icon(Icons.check_circle, color: Colors.cyanAccent, size: 28),
                                     ]
                                  ],
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    );
                 },
               ),
             ),
          ],
        ),
      )
    );
  }
  
  Color _getThemeColor(String t) {
     if (t.contains('matrix')) return Colors.green;
     if (t.contains('chinese')) return Colors.white;
     if (t.contains('cyber')) return Colors.cyan;
     if (t.contains('nebula')) return Colors.purple;
     if (t.contains('liquid')) return Colors.grey;
     if (t.contains('gravity')) return Colors.orange;
     return Colors.blue; 
  }
}
