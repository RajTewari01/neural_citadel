import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class CodingControls extends StatefulWidget {
  final Function(String) onModelChanged;
  final String mode;

  const CodingControls({Key? key, required this.onModelChanged, required this.mode}) : super(key: key);

  @override
  _CodingControlsState createState() => _CodingControlsState();
}

class _CodingControlsState extends State<CodingControls> {
  @override
  void initState() {
    super.initState();
    _updateModels();
  }

  @override
  void didUpdateWidget(CodingControls oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.mode != widget.mode) {
      _updateModels();
    }
  }

  void _updateModels() {
     if (widget.mode == 'hacking') {
        _models = [
           {"id": "netrunner", "name": "NetRunner V1", "icon": Icons.security}
        ];
        _selectedModel = "netrunner";
     } else {
        _models = [
          {"id": "deepseek", "name": "DeepSeek R1", "icon": Icons.psychology},
          {"id": "qwen", "name": "Qwen 2.5", "icon": Icons.code},
        ];
        _selectedModel = "deepseek";
     }
  }

  late List<Map<String, dynamic>> _models;
  String _selectedModel = "";

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: theme.cardColor.withOpacity(0.9),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            children: [
              Icon(Icons.terminal, size: 16, color: Colors.greenAccent),
              const SizedBox(width: 8),
              Text(
                widget.mode == 'hacking' ? "NET.RUNNER" : "DEV.OPERATIVE", 
                style: GoogleFonts.getFont('JetBrains Mono', fontSize: 10, color: Colors.greenAccent, letterSpacing: 1.5)
              ),
            ],
          ),
          
          Container(
            height: 32,
            decoration: BoxDecoration(
              color: isDark ? Colors.black54 : Colors.grey[200],
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: Colors.green.withOpacity(0.3)),
            ),
            child: Row(
              children: _models.map((model) {
                final isSelected = _selectedModel == model["id"];
                return InkWell(
                  onTap: () {
                    setState(() => _selectedModel = model["id"]);
                    widget.onModelChanged(_selectedModel);
                  },
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12),
                    alignment: Alignment.center,
                    decoration: BoxDecoration(
                      color: isSelected ? Colors.green.withOpacity(0.2) : Colors.transparent,
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        if (isSelected) ...[
                          Icon(model["icon"], size: 12, color: Colors.green),
                          const SizedBox(width: 4),
                        ],
                        Text(
                          model["name"],
                          style: GoogleFonts.getFont('JetBrains Mono', 
                            fontSize: 10, 
                            color: isSelected ? Colors.green : Colors.grey,
                            fontWeight: isSelected ? FontWeight.bold : FontWeight.normal
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              }).toList(),
            ),
          )
        ],
      ),
    );
  }
}
