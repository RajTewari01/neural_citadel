import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class WritingControls extends StatefulWidget {
  final Function(String, String) onUpdate; // persona, style
  final bool isNSFW;
  final Function(bool) onNSFWToggle;

  const WritingControls({
    Key? key,
    required this.onUpdate,
    required this.isNSFW,
    required this.onNSFWToggle,
  }) : super(key: key);

  @override
  _WritingControlsState createState() => _WritingControlsState();
}

class _WritingControlsState extends State<WritingControls> {
  String _selectedPersona = "therapist";
  String _selectedStyle = "supportive";

  final Map<String, Map<String, dynamic>> _personas = {
    "reddit": {
      "name": "Reddit",
      "icon": Icons.reddit,
      "styles": ["dramatic", "wholesome", "horror", "revenge"],
    },
    "therapist": {
      "name": "Therapist",
      "icon": Icons.spa,
      "styles": ["supportive", "cbt", "motivational", "mindfulness"],
    },
    "teacher": {
      "name": "Teacher",
      "icon": Icons.school,
      "styles": ["eli5", "academic", "socratic", "practical"],
    },
    "poet": {
      "name": "Poet",
      "icon": Icons.edit_note,
      "styles": ["romantic", "gothic", "haiku", "epic"],
    },
  };
  
  final Map<String, Map<String, dynamic>> _nsfwPersonas = {
    "erotica": {
      "name": "Erotica",
      "icon": Icons.auto_stories,
      "styles": ["sensual", "hardcore", "romantic", "fantasy"],
    },
    "roleplay": {
      "name": "Roleplay",
      "icon": Icons.person_add_alt_1,
      "styles": ["dominant", "submissive", "switch", "adventure"],
    }
  };

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final activePersonas = widget.isNSFW ? _nsfwPersonas : _personas;

    // Ensure selection is valid for current mode switch
    if (!activePersonas.containsKey(_selectedPersona)) {
      _selectedPersona = activePersonas.keys.first;
      _selectedStyle = activePersonas[_selectedPersona]!["styles"][0];
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: theme.cardColor.withOpacity(0.9),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                "WRITING ENGINE V3", 
                style: GoogleFonts.getFont('JetBrains Mono', fontSize: 10, color: Colors.grey, letterSpacing: 1.5)
              ),
              Row(
                children: [
                  Text("NSFW", style: GoogleFonts.getFont('Outfit', fontSize: 10, fontWeight: FontWeight.bold, color: widget.isNSFW ? Colors.red : Colors.grey)),
                  const SizedBox(width: 8),
                  Switch(
                    value: widget.isNSFW, 
                    onChanged: widget.onNSFWToggle,
                    activeColor: Colors.red,
                    activeTrackColor: Colors.red.withOpacity(0.3),
                  ),
                ],
              )
            ],
          ),
          const SizedBox(height: 12),
          // Persona Chips
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: activePersonas.entries.map((e) {
                final isSelected = _selectedPersona == e.key;
                return Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: FilterChip(
                    label: Text(e.value["name"]),
                    avatar: Icon(e.value["icon"], size: 16, color: isSelected ? Colors.white : theme.iconTheme.color),
                    selected: isSelected,
                    onSelected: (selected) {
                      if (selected) {
                        setState(() {
                          _selectedPersona = e.key;
                          _selectedStyle = e.value["styles"][0]; // Reset style
                        });
                        widget.onUpdate(_selectedPersona, _selectedStyle);
                      }
                    },
                    backgroundColor: theme.canvasColor,
                    selectedColor: widget.isNSFW ? Colors.redAccent : theme.primaryColor,
                    labelStyle: TextStyle(color: isSelected ? Colors.white : theme.textTheme.bodyMedium?.color),
                    showCheckmark: false,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                  ),
                );
              }).toList(),
            ),
          ),
          const SizedBox(height: 12),
          // Style Selection
          Container(
             padding: const EdgeInsets.symmetric(horizontal: 12),
             decoration: BoxDecoration(
               color: theme.canvasColor,
               borderRadius: BorderRadius.circular(12),
               border: Border.all(color: theme.dividerColor.withOpacity(0.2)),
             ),
             child: DropdownButton<String>(
               value: _selectedStyle,
               isExpanded: true,
               underline: const SizedBox(),
               icon: const Icon(Icons.keyboard_arrow_down),
               items: (activePersonas[_selectedPersona]!["styles"] as List<String>).map((style) {
                 return DropdownMenuItem(
                   value: style,
                   child: Text(style.toUpperCase(), style: GoogleFonts.getFont('Outfit', fontSize: 13)),
                 );
               }).toList(),
               onChanged: (val) {
                 if (val != null) {
                   setState(() => _selectedStyle = val);
                   widget.onUpdate(_selectedPersona, val);
                 }
               },
             ),
          ),
        ],
      ),
    );
  }
}
