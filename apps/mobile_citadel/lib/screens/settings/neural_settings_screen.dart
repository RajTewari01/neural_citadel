import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../../services/visual_cortex_service.dart';
import 'package:neural_citadel/services/physics_manager.dart';
import 'package:neural_citadel/ui/physics/physics_background.dart';
import 'package:image_picker/image_picker.dart';
import 'package:shared_preferences/shared_preferences.dart';

class NeuralSettingsScreen extends StatefulWidget {
  const NeuralSettingsScreen({super.key});

  @override
  State<NeuralSettingsScreen> createState() => _NeuralSettingsScreenState();
}

class _NeuralSettingsScreenState extends State<NeuralSettingsScreen> {
  final PhysicsManager _physicsManager = PhysicsManager();
  PhysicsMode _currentMode = PhysicsMode.gravityOrbs;
  
  // No local state for dialpad anymore, using Provider
  
  // Neon Colors (Moved to Service, but need local ref for UI or just access via service?)
  // Actually, let's keep a local reference or access via service to keep UI consistent.
  // The service has the canonical list. We should expose it or duplicate it safely.
  // For simplicity, I'll access the colors from the service if I can, or just keep the list here as it's static const effectively.
  final List<Color> _neonColors = [
    Colors.cyanAccent, 
    Colors.purpleAccent, 
    const Color(0xFF00FF41), // Matrix Green
    Colors.deepOrangeAccent,
    Colors.pinkAccent,
    Colors.amberAccent,
    Colors.white,
  ];

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    await _physicsManager.init();
    if (mounted) {
      setState(() {
        _currentMode = _physicsManager.currentMode;
      });
    }
  }


  Future<void> _selectMode(PhysicsMode mode) async {
    await _physicsManager.setMode(mode);
    setState(() => _currentMode = mode);
  }

  Future<void> _pickCustomPhoto() async {
    final picker = ImagePicker();
    final image = await picker.pickImage(source: ImageSource.gallery);
    if (image != null) {
      await _physicsManager.setCustomPhoto(image.path);
      setState(() => _currentMode = PhysicsMode.customPhoto);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        title: Text('NEURAL CONFIG', style: GoogleFonts.orbitron(color: Colors.cyanAccent)),
        backgroundColor: Colors.transparent,
        iconTheme: const IconThemeData(color: Colors.cyanAccent),
      ),
      body: Stack(
        children: [
            // Preview current physics behind settings
            // CRITICAL FIX: Removed Opacity widget which forces a 60fps saveLayer GPU freeze!
            // Instead, using a hardware-accelerated ColorMatrix to drop alpha without a render target buffer.
            ColorFiltered(
               colorFilter: const ColorFilter.matrix([
                  1, 0, 0, 0, 0,
                  0, 1, 0, 0, 0,
                  0, 0, 1, 0, 0,
                  0, 0, 0, 0.3, 0, // Multiply alpha by 0.3 using shader matrix directly
               ]),
               child: PhysicsBackground(mode: _currentMode),
            ),
            
            ListView(
              padding: const EdgeInsets.all(16),
              children: [
                _buildSectionHeader('PHYSICS ENGINE'),
                _buildRadioItem('Gravity Orbs', PhysicsMode.gravityOrbs),
                _buildRadioItem('Matrix Rain', PhysicsMode.matrixRain),
                _buildRadioItem('Cyber Grid', PhysicsMode.cyberGrid),
                _buildRadioItem('Nebula Pulse', PhysicsMode.nebulaPulse),
                _buildRadioItem('Liquid Metal', PhysicsMode.liquidMetal),
                _buildRadioItem('Black Hole', PhysicsMode.blackHole),
                _buildRadioItem('Digital DNA', PhysicsMode.digitalDna),
                _buildRadioItem('Hexagon Hive', PhysicsMode.hexagonHive),
                _buildRadioItem('Starfield Warp', PhysicsMode.starfieldWarp),
                _buildRadioItem('Audio Wave', PhysicsMode.audioWave),
                _buildRadioItem('Chinese Scroll', PhysicsMode.chineseScroll),
                
                const SizedBox(height: 16),
                _buildSectionHeader('VISUAL CORTEX (Dialpad)'),
                
                Consumer<VisualCortexService>(
                  builder: (context, cortex, child) {
                    return Column(
                      children: [
                        SwitchListTile(
                          title: Text('Breathing Effect', style: GoogleFonts.outfit(color: Colors.white)),
                          subtitle: Text('Keypad glows rhythmically', style: GoogleFonts.sourceCodePro(color: Colors.white38, fontSize: 10)),
                          value: cortex.isBreathingMode,
                          activeColor: Colors.cyanAccent,
                          onChanged: (val) => cortex.setBreathingMode(val),
                        ),
                        
                        SwitchListTile(
                          title: Text('Rainbow Mode', style: GoogleFonts.outfit(color: Colors.white)),
                          subtitle: Text('Cycle colors automatically', style: GoogleFonts.sourceCodePro(color: Colors.white38, fontSize: 10)),
                          value: cortex.isRainbowMode,
                          activeColor: Colors.purpleAccent,
                          onChanged: (val) => cortex.setRainbowMode(val),
                        ),
                        
                        ListTile(
                          title: Text('Base Theme Color', style: GoogleFonts.outfit(color: Colors.white)),
                          subtitle: Text(cortex.isRainbowMode ? 'Override by Rainbow Mode' : 'Tap to cycle themes', style: GoogleFonts.sourceCodePro(color: Colors.white38, fontSize: 10)),
                          trailing: Container(
                              width: 24, height: 24,
                              decoration: BoxDecoration(
                                color: cortex.isRainbowMode ? Colors.grey : _neonColors[cortex.colorIndex % _neonColors.length], 
                                shape: BoxShape.circle,
                                boxShadow: [
                                   if (!cortex.isRainbowMode) BoxShadow(color: _neonColors[cortex.colorIndex % _neonColors.length].withOpacity(0.6), blurRadius: 8)
                                ]
                              ),
                          ),
                          enabled: !cortex.isRainbowMode,
                          onTap: () {
                             int next = (cortex.colorIndex + 1) % _neonColors.length;
                             cortex.setColorIndex(next);
                          },
                        ),
                      ],
                    );
                  }
                ),

                const SizedBox(height: 16),
                _buildSectionHeader('CUSTOMIZATION'),
                
                // Physics Transparency Slider
                Padding(
                   padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
                   child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                         Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                               Text('Physics Opacity', style: GoogleFonts.outfit(color: Colors.white)),
                               Text('${(_physicsManager.physicsOpacity * 100).toInt()}%', style: GoogleFonts.sourceCodePro(color: Colors.cyanAccent)),
                            ],
                         ),
                         const SizedBox(height: 8),
                         Slider(
                            value: _physicsManager.physicsOpacity,
                            min: 0.1, // Don't let it go completely invisible, or maybe 0.0 is fine? Let's say 0.0
                            max: 1.0,
                            activeColor: Colors.cyanAccent,
                            inactiveColor: Colors.white10,
                            onChanged: (val) {
                               setState(() {
                                  // Update UI immediately (slider moves)
                                  // The PhysicsBackground ticks, so reading from manager is instant too.
                               });
                               _physicsManager.setPhysicsOpacity(val);
                            },
                         ),
                       ],
                    ),
                 ),
                 
                 // UI Panel Transparency Slider
                 Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
                    child: Column(
                       crossAxisAlignment: CrossAxisAlignment.start,
                       children: [
                          Row(
                             mainAxisAlignment: MainAxisAlignment.spaceBetween,
                             children: [
                                Text('UI Panel Opacity', style: GoogleFonts.outfit(color: Colors.white)),
                                Text('${(_physicsManager.panelOpacity * 100).toInt()}%', style: GoogleFonts.sourceCodePro(color: Colors.purpleAccent)),
                             ],
                          ),
                          const SizedBox(height: 8),
                          Slider(
                             value: _physicsManager.panelOpacity,
                             min: 0.0, 
                             max: 1.0,
                             activeColor: Colors.purpleAccent,
                             inactiveColor: Colors.white10,
                             onChanged: (val) {
                                setState(() {
                                });
                                _physicsManager.setPanelOpacity(val);
                             },
                          ),
                       ],
                    ),
                 ),
                
                 ListTile(
                  title: Text('Custom Hologram Photo', style: GoogleFonts.outfit(color: Colors.white)),
                  leading: const Icon(Icons.image, color: Colors.purpleAccent),
                  trailing: const Icon(Icons.arrow_forward_ios, color: Colors.white24, size: 16),
                  onTap: _pickCustomPhoto,
                ),
                 ListTile(
                  title: Text('Sync Google Avatars', style: GoogleFonts.outfit(color: Colors.white)),
                  subtitle: Text('Merge cloud photos with contacts', style: GoogleFonts.sourceCodePro(color: Colors.white38, fontSize: 10)),
                  leading: const Icon(Icons.cloud_sync, color: Colors.blueAccent),
                  trailing: Switch(
                      value: true, 
                      onChanged: (val) {}, 
                      activeColor: Colors.cyanAccent
                  ),
                ),
              ],
            ),
        ],
      ),
    );
  }

  Widget _buildSectionHeader(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12, top: 24),
      child: Text(
        '// $title',
        style: GoogleFonts.sourceCodePro(color: Colors.cyanAccent, fontWeight: FontWeight.bold),
      ),
    );
  }

  Widget _buildRadioItem(String label, PhysicsMode mode) {
    final isSelected = _currentMode == mode;
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        border: Border.all(color: isSelected ? Colors.cyanAccent : Colors.white10),
        borderRadius: BorderRadius.circular(8),
        color: isSelected ? Colors.cyanAccent.withOpacity(0.1) : Colors.transparent,
      ),
      child: RadioListTile<PhysicsMode>(
        title: Text(label, style: GoogleFonts.outfit(color: Colors.white)),
        value: mode,
        groupValue: _currentMode,
        onChanged: (val) {
            if (val != null) _selectMode(val);
        },
        activeColor: Colors.cyanAccent,
      ),
    );
  }
}
