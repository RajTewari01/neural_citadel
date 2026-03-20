import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'dart:async';
import 'package:flutter/services.dart';
import 'package:flutter_contacts/flutter_contacts.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:provider/provider.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../../../services/visual_cortex_service.dart';
import '../blocked_contacts_sheet.dart';
import '../../../services/contact_service.dart';

class KeypadTab extends StatefulWidget {
  final Function(String number) onCallInitiated;
  final ContactService? contactService;

  const KeypadTab({super.key, required this.onCallInitiated, this.contactService});

  @override
  State<KeypadTab> createState() => _KeypadTabState();
}

class _KeypadTabState extends State<KeypadTab> {
  String _phoneNumber = '';
  List<Contact> _allContacts = [];
  List<Contact> _searchResults = [];
  bool _searching = false;
  Timer? _debounce;

  @override
  void initState() {
    super.initState();
    _loadContacts(); 
  }

  Future<void> _loadContacts() async {
    if (await Permission.contacts.request().isGranted) {
      final contacts = await FlutterContacts.getContacts(withProperties: true);
      if (mounted) setState(() => _allContacts = contacts);
    }
  }

  void _updateSearch(String number) {
    if (_debounce?.isActive ?? false) _debounce!.cancel();
    _debounce = Timer(const Duration(milliseconds: 300), () {
      if (!mounted) return;
      if (number.isEmpty) {
        setState(() {
          _searchResults = [];
          _searching = false;
        });
        return;
      }

      final results = _allContacts.where((contact) {
        bool numMatch = contact.phones.any((p) {
           if (p.number.contains(number)) return true;
           return p.number.replaceAll(RegExp(r'\D'), '').contains(number);
        });
        if (numMatch) return true;
        if (contact.displayName.isNotEmpty) {
           String t9Name = _toT9(contact.displayName);
           if (t9Name.contains(number)) return true;
        }
        return false;
      }).take(5).toList();

      setState(() {
        _searchResults = results;
        _searching = true;
      });
    });
  }

  String _toT9(String input) {
    String t9 = "";
    for (var char in input.toUpperCase().split('')) {
      if ("ABC".contains(char)) t9 += "2";
      else if ("DEF".contains(char)) t9 += "3";
      else if ("GHI".contains(char)) t9 += "4";
      else if ("JKL".contains(char)) t9 += "5";
      else if ("MNO".contains(char)) t9 += "6";
      else if ("PQRS".contains(char)) t9 += "7";
      else if ("TUV".contains(char)) t9 += "8";
      else if ("WXYZ".contains(char)) t9 += "9";
      else if (RegExp(r'[0-9]').hasMatch(char)) t9 += char;
    }
    return t9;
  }

  void _onDigitPress(String digit) {
    if (_phoneNumber.length < 15) {
      setState(() => _phoneNumber += digit);
      _updateSearch(_phoneNumber);
      HapticFeedback.lightImpact();
      
      // Play Native DTMF (Local or Network)
      try {
         const MethodChannel('com.neuralcitadel/native').invokeMethod("sendDtmf", {"key": digit});
      } catch (_) {}
      
      // Notify Visual Cortex to cycle color if in Rainbow Mode
      context.read<VisualCortexService>().cycleRainbowColor();
    }
  }

  void _backspace() {
    if (_phoneNumber.isNotEmpty) {
      setState(() => _phoneNumber = _phoneNumber.substring(0, _phoneNumber.length - 1));
      _updateSearch(_phoneNumber);
      HapticFeedback.selectionClick();
    }
  }

  void _clear() {
    setState(() => _phoneNumber = '');
    _updateSearch('');
    HapticFeedback.mediumImpact();
  }

  void _pasteNumber() async {
    final data = await Clipboard.getData(Clipboard.kTextPlain);
    if (data?.text != null) {
      String filtered = data!.text!.replaceAll(RegExp(r'[^0-9+*#]'), '');
      setState(() => _phoneNumber = filtered);
      _updateSearch(_phoneNumber);
      HapticFeedback.selectionClick();
    }
  }

  void _callVoicemail() {
     widget.onCallInitiated("1"); 
  }

  void _createContact() {
    if (_phoneNumber.isNotEmpty) {
       final newContact = Contact()..phones = [Phone(_phoneNumber)];
       FlutterContacts.openExternalInsert(newContact);
    }
  }

  void _showMenu() {
     showModalBottomSheet(
        context: context,
        backgroundColor: Colors.black.withOpacity(0.95),
        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
        builder: (ctx) => Container(
            padding: const EdgeInsets.all(24),
            child: Column(
               mainAxisSize: MainAxisSize.min,
               children: [
                  Container(
                    width: 40, height: 4, 
                    margin: const EdgeInsets.only(bottom: 24),
                    decoration: BoxDecoration(color: Colors.white24, borderRadius: BorderRadius.circular(2))
                  ),
                  ListTile(
                    leading: const Icon(Icons.block, color: Colors.redAccent),
                    title: Text("Blocked People", style: GoogleFonts.outfit(color: Colors.white)),
                    onTap: () async {
                        Navigator.pop(ctx);
                        // Wait for menu to close smoothly before opening next sheet
                        await Future.delayed(const Duration(milliseconds: 300));
                        
                        if (mounted && widget.contactService != null) {
                           showModalBottomSheet(
                             context: context, 
                             isScrollControlled: true,
                             backgroundColor: Colors.transparent,
                             builder: (_) => BlockedContactsSheet(contactService: widget.contactService!)
                           );
                        } else {
                           if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Service unavailable")));
                        }
                    },
                  ),
               ],
            ),
        )
     );
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // 1. Search Results (Dynamic)
        if (_searchResults.isNotEmpty)
          Expanded(
            child: Consumer<VisualCortexService>(
              builder: (context, cortex, child) {
                return ListView.builder(
                  padding: const EdgeInsets.symmetric(horizontal: 24),
                  itemCount: _searchResults.length,
                  itemBuilder: (context, index) {
                     final c = _searchResults[index];
                     final color = cortex.activeColor;
                     return ListTile(
                       leading: CircleAvatar(
                         backgroundColor: Colors.white10,
                         child: Text(c.displayName.isNotEmpty ? c.displayName[0] : '#', style: TextStyle(color: color)),
                       ),
                       title: Text(c.displayName, style: GoogleFonts.outfit(color: Colors.white)),
                       subtitle: Text(c.phones.isNotEmpty ? c.phones.first.number : '', style: GoogleFonts.shareTechMono(color: Colors.white54)),
                       onTap: () {
                          if (c.phones.isNotEmpty) widget.onCallInitiated(c.phones.first.number);
                       },
                     );
                  },
                );
              }
            ),
          )
        else
          const Spacer(),

        // 2. Number Display (Dynamic)
        Consumer<VisualCortexService>(
          builder: (context, cortex, _) {
            return GestureDetector(
              onTap: _pasteNumber,
              child: Container(
                height: 80,
                alignment: Alignment.center,
                padding: const EdgeInsets.symmetric(horizontal: 32),
                child: col_number_display(context, cortex.activeColor),
              ),
            );
          }
        ),

        const SizedBox(height: 10),

        // 3. Keypad Grid (STATIC LAYOUT - DYNAMIC CONTENT)
        // We use a Builder to prevent full rebuilds of children that don't need it?
        // Actually, Consumer<VisualCortexService> needs to wrap the buttons so they change color.
        // But we want to avoid rebuilding the LAYOUT of the grid.
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 40),
          child: Consumer<VisualCortexService>(
            builder: (context, cortex, _) {
              return GridView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 3,
                  childAspectRatio: 1.6,
                  crossAxisSpacing: 20,
                  mainAxisSpacing: 16,
                ),
                itemCount: 12,
                itemBuilder: (context, index) {
                    if (index == 9) return NeonKeypadButton(
                        digit: '*', letters: '', 
                        activeColor: cortex.activeColor, 
                        isBreathing: cortex.isBreathingMode,
                        onTap: () => _onDigitPress('*'));
                    
                    if (index == 10) return NeonKeypadButton(
                        digit: '0', letters: '+', 
                        activeColor: cortex.activeColor, 
                        isBreathing: cortex.isBreathingMode,
                        onTap: () => _onDigitPress('0'), 
                        onLongPress: () => _onDigitPress('+'));
                    
                    if (index == 11) return NeonKeypadButton(
                        digit: '#', letters: '', 
                        activeColor: cortex.activeColor, 
                        isBreathing: cortex.isBreathingMode,
                        onTap: () => _onDigitPress('#'));
    
                    String digit = '${index + 1}';
                    String letters = '';
                     const map = ['','ABC','DEF','GHI','JKL','MNO','PQRS','TUV','WXYZ'];
                     if (index > 0 && index < 9) letters = map[index];
                     
                    return NeonKeypadButton(
                       digit: digit, 
                       letters: letters,
                       activeColor: cortex.activeColor,
                       isBreathing: cortex.isBreathingMode,
                       onTap: () => _onDigitPress(digit),
                       onLongPress: () {
                          if (digit == '0') _onDigitPress('+');
                          if (digit == '1') _callVoicemail();
                       },
                    );
                },
              );
            }
          ),
        ),

        const SizedBox(height: 20),

        // 4. Action Row
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 40, vertical: 20),
          child: Consumer<VisualCortexService>(
            builder: (context, cortex, _) {
              return Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  SizedBox(
                    width: 60,
                    child: IconButton(
                      icon: const Icon(Icons.menu, color: Colors.white54),
                      onPressed: _showMenu,
                    ),
                  ),
                  GestureDetector(
                    onTap: () {
                       if (_phoneNumber.isNotEmpty) widget.onCallInitiated(_phoneNumber); 
                    },
                    child: Container(
                      width: 70, height: 70,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        gradient: LinearGradient(
                           colors: [cortex.activeColor, cortex.activeColor.withOpacity(0.5)], 
                           begin: Alignment.topLeft, end: Alignment.bottomRight
                        ),
                        boxShadow: [
                          BoxShadow(color: cortex.activeColor.withOpacity(0.4), blurRadius: 15, spreadRadius: 1)
                        ],
                      ),
                      child: const Icon(Icons.call, color: Colors.black, size: 32),
                    ),
                  ),
                  SizedBox(
                    width: 60,
                    child: GestureDetector(
                      onTap: _backspace,
                      onLongPress: _clear,
                      child: Container(
                         padding: const EdgeInsets.all(12),
                         decoration: BoxDecoration(
                           shape: BoxShape.circle,
                           color: Colors.white.withOpacity(0.05),
                         ),
                         child: const Icon(Icons.backspace, color: Colors.white70, size: 24),
                      ),
                    ),
                  ),
                ],
              );
            }
          ),
        ),
      ],
    );
  }

  Widget col_number_display(BuildContext context, Color activeColor) {
     return Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16.0),
            child: FittedBox(
              fit: BoxFit.scaleDown,
              child: Text(
                _phoneNumber.isEmpty ? "" : _phoneNumber,
                style: GoogleFonts.orbitron(
                  fontSize: _phoneNumber.isEmpty ? 16 : 36,
                  color: _phoneNumber.isEmpty ? Colors.white24 : activeColor,
                  fontWeight: FontWeight.w500,
                  letterSpacing: 2,
                ),
              ),
            ),
          ),
          if (_phoneNumber.isNotEmpty && _searchResults.isEmpty)
             Padding(
               padding: const EdgeInsets.only(top: 4.0),
               child: InkWell(
                  onTap: _createContact,
                  child: Text("+ Add to Contacts", style: GoogleFonts.outfit(color: Colors.blueAccent, fontSize: 12)),
               ),
             )
        ],
     );
  }
}

class NeonKeypadButton extends StatelessWidget {
  final String digit;
  final String letters;
  final Color activeColor;
  final bool isBreathing;
  final VoidCallback onTap;
  final VoidCallback? onLongPress;

  const NeonKeypadButton({
    super.key, 
    required this.digit, 
    required this.letters, 
    required this.activeColor,
    required this.isBreathing,
    required this.onTap,
    this.onLongPress,
  });

  @override
  Widget build(BuildContext context) {
    // RepaintBoundary isolates this button from the rest of the layout
    return RepaintBoundary(
      child: ButtonPress(
        onTap: onTap,
        onLongPress: onLongPress,
        builder: (isPressed) {
          return AnimatedContainer(
            duration: const Duration(milliseconds: 100),
            decoration: BoxDecoration(
              color: isPressed 
                  ? activeColor.withOpacity(0.4) 
                  : activeColor.withOpacity(0.05),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                 color: isPressed ? activeColor : activeColor.withOpacity(0.3), 
                 width: 1 
              ),
              boxShadow: (isPressed || isBreathing) ? [
                 BoxShadow(color: activeColor.withOpacity(0.6), blurRadius: isPressed ? 20 : 10, spreadRadius: isPressed ? 2 : 1)
              ] : [],
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(digit, style: GoogleFonts.outfit(fontSize: 28, color: Colors.white, fontWeight: isPressed ? FontWeight.bold : FontWeight.normal)),
                if (letters.isNotEmpty)
                  Text(letters, style: GoogleFonts.sourceCodePro(fontSize: 10, color: Colors.white38)),
                if (digit == '1')
                   const Padding(padding: EdgeInsets.only(top:2), child: Icon(Icons.voicemail, size: 10, color: Colors.white38))
              ],
            ).animate(
               target: isBreathing ? 1 : 0,
               onPlay: (c) => c.repeat(reverse: true)
            ).shimmer(duration: 2000.ms, color: activeColor.withOpacity(0.3)),
          );
        },
      ),
    );
  }
}

// Optimized Gesture Detector that doesn't rebuild PARENT
class ButtonPress extends StatefulWidget {
  final Widget Function(bool isPressed) builder;
  final VoidCallback onTap;
  final VoidCallback? onLongPress;
  
  const ButtonPress({super.key, required this.builder, required this.onTap, this.onLongPress});

  @override
  State<ButtonPress> createState() => _ButtonPressState();
}

class _ButtonPressState extends State<ButtonPress> {
  bool _isPressed = false;
  
  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: (_) {
         setState(() => _isPressed = true);
         HapticFeedback.lightImpact(); 
      },
      onTapUp: (_) {
         setState(() => _isPressed = false);
         widget.onTap(); 
      },
      onTapCancel: () {
         setState(() => _isPressed = false); 
      },
      onLongPress: () {
         HapticFeedback.mediumImpact();
         widget.onLongPress?.call();
      },
      child: widget.builder(_isPressed),
    );
  }
}
