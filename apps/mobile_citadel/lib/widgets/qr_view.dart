import 'dart:async';
import 'dart:convert';
import 'dart:math';
import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'package:http/http.dart' as http;
import 'dart:io';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';
import '../services/api_service.dart';
import '../models/app_schemas.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:gal/gal.dart';
import 'package:flutter_svg/flutter_svg.dart';

// =============================================================================
// DESIGN SYSTEM - LIME GREEN + YELLOW GRADIENT
// =============================================================================

class QRColors {
  // Primary: Lime Green + Yellow
  static const Color primary = Color(0xFF84CC16);      // Lime green
  static const Color secondary = Color(0xFFEAB308);    // Yellow
  static const Color accent = Color(0xFFA3E635);       // Bright lime
  
  // Backgrounds: Pure blacks (NO TINT!)
  static const Color bgDeep = Color(0xFF000000);       // Pure black
  static const Color bgCard = Color(0xFF050505);       // Almost black
  static const Color bgSurface = Color(0xFF0A0A0A);    // Very dark
  
  // Glass border (subtle white)
  static const Color glassBorder = Color(0x15FFFFFF);  // 8% white
  
  // Text
  static const Color textPrimary = Color(0xFFFFFFFF);
  static const Color textSecondary = Color(0xB3FFFFFF); // 70% white
  static const Color textMuted = Color(0x66FFFFFF);     // 40% white
  
  // Gradients: Lime Green to Yellow
  static const List<Color> primaryGradient = [Color(0xFF84CC16), Color(0xFFEAB308)];
  static const List<Color> accentGradient = [Color(0xFFA3E635), Color(0xFFFACC15)];
  static const List<Color> glowGradient = [Color(0xFF84CC16), Color(0xFFA3E635), Color(0xFFEAB308)];
}

// =============================================================================
// GLASS CARD - PURE FROSTED GLASS (NO COLOR!)
// =============================================================================

class GlassCard extends StatelessWidget {
  final Widget child;
  final double blur;
  final EdgeInsetsGeometry? padding;
  final EdgeInsetsGeometry? margin;
  final BorderRadius? borderRadius;
  final bool showBorder;
  final Color? glowColor;
  final double? width;
  final double? height;

  const GlassCard({
    super.key,
    required this.child,
    this.blur = 30,
    this.padding,
    this.margin,
    this.borderRadius,
    this.showBorder = true,
    this.glowColor,
    this.width,
    this.height,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: width,
      height: height,
      margin: margin,
      decoration: BoxDecoration(
        borderRadius: borderRadius ?? BorderRadius.circular(20),
        boxShadow: glowColor != null ? [
          BoxShadow(
            color: glowColor!.withOpacity(0.25),
            blurRadius: 30,
            spreadRadius: -5,
          ),
        ] : null,
      ),
      child: ClipRRect(
        borderRadius: borderRadius ?? BorderRadius.circular(20),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: blur, sigmaY: blur),
          child: Container(
            padding: padding ?? const EdgeInsets.all(16),
            decoration: BoxDecoration(
              // PURE GLASS: Only very subtle white overlay for visibility
              color: Colors.white.withOpacity(0.03),
              borderRadius: borderRadius ?? BorderRadius.circular(20),
              border: showBorder ? Border.all(
                color: Colors.white.withOpacity(0.08),
                width: 1,
              ) : null,
            ),
            child: child,
          ),
        ),
      ),
    );
  }
}

// =============================================================================
// QR STUDIO VIEW - MAIN WIDGET
// =============================================================================

class QRView extends StatefulWidget {
  const QRView({super.key});

  @override
  State<QRView> createState() => _QRViewState();
}

class _QRViewState extends State<QRView> with TickerProviderStateMixin {
  late TabController _tabController;
  late AnimationController _spinController;
  late AnimationController _pulseController;
  
  // Schema State
  QRSchema? _schema;
  bool _isLoadingSchema = true;
  String? _schemaError;

  // Handler Selection
  QRHandlerSchema? _selectedHandler;
  Map<String, List<QRHandlerSchema>> _groupedHandlers = {};
  String _searchQuery = '';
  bool _showHandlerPicker = false;
  String? _selectedCategory;
  
  // Dynamic Inputs
  final Map<String, dynamic> _dynamicValues = {};
  final Map<String, TextEditingController> _controllers = {}; 

  // Generation State
  bool _isGenerating = false;
  String? _resultPath;
  String _statusMessage = '';
  List<String> _chatMessages = [];
  String? _sessionId;
  StreamSubscription? _sseSubscription;
  
  // Gradient Options - Default to lime green/yellow
  Color _startColor = const Color(0xFF84CC16);  // Lime green
  Color _endColor = const Color(0xFFEAB308);    // Yellow
  String _gradientType = 'radial';
  String _moduleDrawer = 'rounded';
  String? _logoPath;
  
  // Diffusion Options
  final TextEditingController _promptController = TextEditingController();

  // Color Presets - Greens, Yellows, and vibrant colors
  static const List<Color> colorPresets = [
    // Lime Greens
    Color(0xFF84CC16), Color(0xFFA3E635), Color(0xFF65A30D), Color(0xFF4D7C0F), Color(0xFF22C55E),
    // Yellows & Golds
    Color(0xFFEAB308), Color(0xFFFACC15), Color(0xFFFFD700), Color(0xFFFFC107), Color(0xFFFFB300),
    // Oranges
    Color(0xFFFF9800), Color(0xFFFF6D00), Color(0xFFF97316), Color(0xFFEA580C), Color(0xFFDC2626),
    // Teals & Greens
    Color(0xFF10B981), Color(0xFF14B8A6), Color(0xFF06B6D4), Color(0xFF0EA5E9), Color(0xFF3B82F6),
    // Electric Colors
    Color(0xFF76FF03), Color(0xFFFFEA00), Color(0xFF00E676), Color(0xFF1DE9B6), Color(0xFF00BCD4),
    // Pure Colors
    Color(0xFFFFFFFF), Color(0xFF000000), Color(0xFF00C853), Color(0xFFFFAB00), Color(0xFF00E5FF),
  ];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _spinController = AnimationController(vsync: this, duration: const Duration(seconds: 2))..repeat();
    _pulseController = AnimationController(vsync: this, duration: const Duration(milliseconds: 2000))..repeat(reverse: true);
    _loadSchema();
  }

  @override
  void dispose() {
    _tabController.dispose();
    _spinController.dispose();
    _pulseController.dispose();
    _promptController.dispose();
    _sseSubscription?.cancel();
    for (var c in _controllers.values) { c.dispose(); }
    super.dispose();
  }

  Future<void> _loadSchema() async {
    setState(() => _isLoadingSchema = true);
    try {
      final api = Provider.of<ApiService>(context, listen: false);
      final schema = await api.getQRSchema();
      setState(() {
        _schema = schema;
        _isLoadingSchema = false;
        if (schema.handlers.isNotEmpty) {
          _selectHandler(schema.handlers.firstWhere((h) => h.id == 'url', orElse: () => schema.handlers.first));
        }
        _filterHandlers(''); 
      });
    } catch (e) {
      if (mounted) setState(() {
        _schemaError = e.toString();
        _isLoadingSchema = false;
      });
    }
  }
  
  void _selectHandler(QRHandlerSchema handler) {
    setState(() {
      _selectedHandler = handler;
      _controllers.forEach((k, c) => c.dispose());
      _controllers.clear();
      _dynamicValues.clear();
      
      for (var param in handler.params) {
        if (param.type == 'str' || param.type == 'int' || param.type == 'float' || param.type == 'text') {
          _controllers[param.name] = TextEditingController(text: param.defaultValue?.toString() ?? '');
          _dynamicValues[param.name] = param.defaultValue;
        } else if (param.type == 'bool') {
          _dynamicValues[param.name] = param.defaultValue ?? false;
        }
      }
      _showHandlerPicker = false;
      _addChatMessage('✓ ${handler.name}');
    });
  }

  void _filterHandlers(String query) {
    if (_schema == null) return;
    setState(() {
      _searchQuery = query;
      List<QRHandlerSchema> filtered;
      if (query.isEmpty) {
        filtered = List.from(_schema!.handlers);
      } else {
        filtered = _schema!.handlers.where((h) => 
          h.name.toLowerCase().contains(query.toLowerCase()) || 
          h.category.toLowerCase().contains(query.toLowerCase())
        ).toList();
      }
      
      if (_selectedCategory != null) {
        filtered = filtered.where((h) => h.category == _selectedCategory).toList();
      }
      
      _groupedHandlers = {};
      for (var h in filtered) {
        if (!_groupedHandlers.containsKey(h.category)) {
          _groupedHandlers[h.category] = [];
        }
        _groupedHandlers[h.category]!.add(h);
      }
      for (var key in _groupedHandlers.keys) {
        _groupedHandlers[key]!.sort((a, b) => a.name.compareTo(b.name));
      }
    });
  }

  void _addChatMessage(String msg) {
    setState(() {
      _chatMessages.add(msg);
      if (_chatMessages.length > 4) _chatMessages.removeAt(0);
    });
  }

  void _randomColors() {
    final random = Random();
    final idx1 = random.nextInt(colorPresets.length);
    var idx2 = random.nextInt(colorPresets.length);
    while (idx2 == idx1) idx2 = random.nextInt(colorPresets.length);
    
    setState(() {
      _startColor = colorPresets[idx1];
      _endColor = colorPresets[idx2];
    });
    
    _addChatMessage('🎲 Random colors');
    _generateQR('gradient');
  }

  Future<void> _generateQR(String mode) async {
    if (_selectedHandler == null) return;
    
    setState(() {
      _isGenerating = true;
      _resultPath = null;
      _statusMessage = 'Preparing...';
    });
    _addChatMessage('⏳ Generating...');
    
    try {
      final api = Provider.of<ApiService>(context, listen: false);
      
      Map<String, dynamic> p = {};
      for (var param in _selectedHandler!.params) {
        if (_controllers.containsKey(param.name)) {
          p[param.name] = _controllers[param.name]!.text;
        } else if (_dynamicValues.containsKey(param.name)) {
          p[param.name] = _dynamicValues[param.name];
        }
      }
      String dataPayload = p.isEmpty ? "{}" : jsonEncode(p);

      if (mode == 'diffusion') {
        _sessionId = DateTime.now().millisecondsSinceEpoch.toString();
        _addChatMessage('⏳ Loading AI...');
        
        final stream = api.generateQRStream(
          dataPayload,
          handler: _selectedHandler!.id,
          prompt: _promptController.text,
          sessionId: _sessionId!,
        );
        
        _sseSubscription = stream.listen(
          (event) {
            if (!mounted) return;
            final data = jsonDecode(event);
            setState(() {
              _statusMessage = data['status'] ?? '';
              if (data['status'] == 'complete') {
                _resultPath = data['path'];
                _isGenerating = false;
                _addChatMessage('✓ Done!');
              } else if (data['status'] == 'cancelled') {
                _isGenerating = false;
                _addChatMessage('✕ Cancelled');
              } else {
                _addChatMessage('⏳ ${data['status']}');
              }
            });
          },
          onError: (e) {
            if (mounted) {
              setState(() => _isGenerating = false);
              _addChatMessage('✕ Error');
            }
          },
        );
      } else {
        final path = await api.generateQR(
          dataPayload, 
          handler: _selectedHandler!.id,
          mode: mode,
          colors: mode == 'gradient' 
            ? ['#${_startColor.value.toRadixString(16).padLeft(8, '0').substring(2)}', 
               '#${_endColor.value.toRadixString(16).padLeft(8, '0').substring(2)}'] 
            : null,
          gradientType: mode == 'gradient' ? _gradientType : null,
          moduleDrawer: mode == 'gradient' ? _moduleDrawer : null,
          logoPath: mode == 'gradient' ? _logoPath : null,
        );
        
        setState(() {
          _resultPath = path;
          _isGenerating = false;
        });
        _addChatMessage('✓ Done!');
        HapticFeedback.mediumImpact();
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isGenerating = false);
        _addChatMessage('✕ Failed');
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('$e'), backgroundColor: Colors.red.shade900)
        );
      }
    }
  }

  Future<void> _cancelGeneration() async {
    if (_sessionId == null) return;
    try {
      final api = Provider.of<ApiService>(context, listen: false);
      await api.cancelQR(_sessionId!);
      _sseSubscription?.cancel();
      setState(() {
        _isGenerating = false;
        _statusMessage = 'Cancelled';
      });
    } catch (e) {}
  }

  void _showFullscreenPreview() {
    if (_resultPath == null) return;
    HapticFeedback.mediumImpact();
    
    showGeneralDialog(
      context: context,
      barrierDismissible: true,
      barrierLabel: 'Dismiss',
      barrierColor: Colors.black87,
      transitionDuration: const Duration(milliseconds: 300),
      pageBuilder: (ctx, anim1, anim2) {
        return FadeTransition(
          opacity: anim1,
          child: ScaleTransition(
            scale: Tween<double>(begin: 0.8, end: 1.0).animate(
              CurvedAnimation(parent: anim1, curve: Curves.easeOutBack),
            ),
            child: Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    // QR Image
                    Container(
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(24),
                        boxShadow: [
                          BoxShadow(
                            color: QRColors.primary.withOpacity(0.4),
                            blurRadius: 50,
                            spreadRadius: 10,
                          ),
                        ],
                      ),
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(24),
                        child: Builder(
                          builder: (context) {
                            // Construct full URL if relative
                            final api = Provider.of<ApiService>(context, listen: false);
                            String url = _resultPath!;
                            if (url.startsWith('/')) {
                              url = '${api.baseUrl}$url';
                            }
                            
                            if (url.endsWith('.svg')) {
                              return SvgPicture.network(
                                url,
                                width: 300,
                                height: 300,
                                fit: BoxFit.contain,
                                placeholderBuilder: (ctx) => Container(
                                  width: 300, height: 300,
                                  color: QRColors.bgCard,
                                  child: Center(child: CircularProgressIndicator(color: QRColors.primary)),
                                ),
                              );
                            }
                            
                            return Image.network(
                              url,
                              width: 300,
                              height: 300,
                              fit: BoxFit.contain,
                              loadingBuilder: (ctx, child, progress) {
                                if (progress == null) return child;
                                return Container(
                                  width: 300, height: 300,
                                  color: QRColors.bgCard,
                                  child: Center(child: CircularProgressIndicator(color: QRColors.primary)),
                                );
                              },
                              errorBuilder: (ctx, err, stack) => Container(
                                width: 300, height: 300,
                                color: QRColors.bgCard,
                                child: Column(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    Icon(Icons.broken_image, color: Colors.white, size: 40),
                                    SizedBox(height: 8),
                                    Text('Failed to load', style: GoogleFonts.outfit(color: Colors.white70)),
                                  ],
                                ),
                              ),
                            );
                          }
                        ),
                      ),
                    ),
                    const SizedBox(height: 32),
                    
                    // Action Buttons
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        // Share Button - Opens native share sheet
                        _buildActionBtn(
                          icon: Icons.share,
                          label: 'SHARE',
                          onTap: () async {
                            Navigator.pop(ctx);
                            await _shareQRNative();
                          },
                        ),
                        const SizedBox(width: 16),
                        
                        // Download Button
                        _buildActionBtn(
                          icon: Icons.download,
                          label: 'DOWNLOAD',
                          onTap: () => _downloadQR(ctx),
                        ),
                      ],
                    ),
                    const SizedBox(height: 24),
                    
                    // Close hint (no underline)
                    Text('Tap outside to close', style: GoogleFonts.outfit(
                      color: QRColors.textMuted, fontSize: 12, decoration: TextDecoration.none)),
                  ],
                ),
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildActionBtn({required IconData icon, required String label, required VoidCallback onTap}) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(16),
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
              decoration: BoxDecoration(
                gradient: const LinearGradient(colors: QRColors.primaryGradient),
                borderRadius: BorderRadius.circular(16),
                boxShadow: [
                  BoxShadow(color: QRColors.primary.withOpacity(0.4), blurRadius: 12),
                ],
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(icon, color: Colors.white, size: 20),
                  const SizedBox(width: 10),
                  Text(label, style: GoogleFonts.outfit(
                    color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14)),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _shareQRNative() async {
    if (_resultPath == null) return;
    
    try {
      HapticFeedback.mediumImpact();
      
      // Get image bytes
      Uint8List imageBytes;
      if (_resultPath!.startsWith('http://') || _resultPath!.startsWith('https://')) {
        final response = await http.get(Uri.parse(_resultPath!));
        if (response.statusCode != 200) throw Exception('Failed to fetch image');
        imageBytes = response.bodyBytes;
      } else {
        final file = File(_resultPath!);
        if (!await file.exists()) throw Exception('File not found');
        imageBytes = await file.readAsBytes();
      }
      
      // Save to temp file for sharing
      final tempDir = await getTemporaryDirectory();
      final tempFile = File('${tempDir.path}/qr_share_${DateTime.now().millisecondsSinceEpoch}.png');
      await tempFile.writeAsBytes(imageBytes);
      
      // Open native share sheet
      await Share.shareXFiles(
        [XFile(tempFile.path)],
        text: 'Check out my QR Code!',
        subject: 'QR Code',
      );
      
      // Cleanup temp file after share
      Future.delayed(const Duration(seconds: 5), () => tempFile.delete().catchError((_) {}));
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Share failed: $e'), backgroundColor: Colors.red),
      );
    }
  }

  Future<void> _downloadQR(BuildContext dialogContext) async {
    if (_resultPath == null) return;
    
    // Show loading overlay
    showDialog(
      context: dialogContext,
      barrierDismissible: false,
      barrierColor: Colors.black54,
      builder: (ctx) => Center(
        child: Container(
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            color: QRColors.bgCard,
            borderRadius: BorderRadius.circular(16),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              SizedBox(
                width: 40, height: 40,
                child: CircularProgressIndicator(
                  color: QRColors.primary,
                  strokeWidth: 3,
                ),
              ),
              const SizedBox(height: 16),
              Text('Downloading...', style: GoogleFonts.outfit(
                color: QRColors.textPrimary, 
                fontSize: 14, 
                decoration: TextDecoration.none,
              )),
            ],
          ),
        ),
      ),
    );
    
    try {
      Uint8List imageBytes;
      final path = _resultPath!;
      
      // Get image bytes - handle all path types
      if (path.startsWith('http://') || path.startsWith('https://')) {
        // Full URL
        final response = await http.get(Uri.parse(path));
        if (response.statusCode != 200) throw Exception('HTTP ${response.statusCode}');
        imageBytes = response.bodyBytes;
      } else if (path.startsWith('/static/') || path.startsWith('/qr/')) {
        // Relative server path - prepend base URL
        final api = Provider.of<ApiService>(context, listen: false);
        final fullUrl = '${api.baseUrl}$path';
        final response = await http.get(Uri.parse(fullUrl));
        if (response.statusCode != 200) throw Exception('HTTP ${response.statusCode}');
        imageBytes = response.bodyBytes;
      } else {
        // Local file path
        final sourceFile = File(path);
        if (!await sourceFile.exists()) throw Exception('File not found');
        imageBytes = await sourceFile.readAsBytes();
      }
      
      // Save to temp first
      final tempDir = await getTemporaryDirectory();
      final tempFile = File('${tempDir.path}/QR_${DateTime.now().millisecondsSinceEpoch}.png');
      await tempFile.writeAsBytes(imageBytes);
      
      // Save to Gallery using Gal
      await Gal.putImage(tempFile.path);
      
      // Close dialogs
      if (context.mounted) {
        Navigator.pop(dialogContext); // loading
        Navigator.pop(dialogContext); // preview
      }
      
      // Haptic feedback for success
      HapticFeedback.heavyImpact();
      
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Row(
              children: const [
                Icon(Icons.check_circle, color: QRColors.accent, size: 20),
                SizedBox(width: 10),
                Text('Saved to Gallery'),
              ],
            ),
            backgroundColor: QRColors.bgCard,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
      
    } catch (e) {
      if (context.mounted) {
        Navigator.pop(dialogContext); // Close loading
        
        // Show detailed error
        String message = 'Download failed: $e';
        if (e is GalException) {
           message = 'Gallery Error: ${e.type.toString()}';
        }
        
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
             content: Text(message), 
             backgroundColor: Colors.red,
             duration: const Duration(seconds: 5),
          ),
        );
      }
      debugPrint('Download failed: $e');
    }
  }

  IconData _getIcon(String category) {
    final c = category.toLowerCase();
    if (c.contains('social')) return Icons.people_outline;
    if (c.contains('web')) return Icons.language;
    if (c.contains('communication')) return Icons.chat_bubble_outline;
    if (c.contains('location')) return Icons.location_on_outlined;
    if (c.contains('wifi')) return Icons.wifi;
    if (c.contains('finance')) return Icons.account_balance_wallet_outlined;
    if (c.contains('contact')) return Icons.contact_page_outlined;
    if (c.contains('calendar')) return Icons.calendar_today_outlined;
    if (c.contains('media')) return Icons.play_circle_outline;
    if (c.contains('developer')) return Icons.code;
    if (c.contains('security')) return Icons.security;
    if (c.contains('iot')) return Icons.devices_other;
    return Icons.qr_code_2;
  }

  void _showServerHelp() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: QRColors.bgCard,
        title: Row(
          children: [
            Icon(Icons.dns, color: QRColors.primary),
            SizedBox(width: 10),
            Text('Server Setup', style: GoogleFonts.outfit(color: Colors.white)),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildStep('1', 'Open Terminal/PowerShell on PC'),
            _buildStep('2', 'Run: python infra/server/main.py'),
            _buildStep('3', 'Check IP: Run "ipconfig"'),
            _buildStep('4', 'Find IPv4 Address (e.g. 192.168.x.x)'),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.black26,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: QRColors.primary.withOpacity(0.3)),
              ),
              child: Text(
                'Note: Ensure your phone and PC are on the same Wi-Fi network.',
                style: TextStyle(color: QRColors.textMuted, fontSize: 12),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            child: Text('Close', style: TextStyle(color: QRColors.primary)),
            onPressed: () => Navigator.pop(ctx),
          ),
        ],
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      ),
    );
  }

  Widget _buildStep(String num, String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        children: [
          Container(
            width: 24, height: 24,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: QRColors.primary.withOpacity(0.2),
              shape: BoxShape.circle,
            ),
            child: Text(num, style: TextStyle(color: QRColors.primary, fontWeight: FontWeight.bold, fontSize: 12)),
          ),
          const SizedBox(width: 12),
          Expanded(child: Text(text, style: GoogleFonts.outfit(color: QRColors.textSecondary))),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoadingSchema) {
      return Container(
        color: QRColors.bgDeep.withOpacity(0.5),
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              CircularProgressIndicator(color: QRColors.primary),
              const SizedBox(height: 16),
              Text("Loading QR Studio...", style: TextStyle(color: QRColors.textSecondary)),
            ],
          ),
        ),
      );
    }
    if (_schemaError != null) {
      return Container(
        color: QRColors.bgDeep.withOpacity(0.5),
        child: Center(
          child: GlassCard(
             width: 320,
             padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
             blur: 40,
             borderRadius: BorderRadius.circular(24),
             child: Column(
               mainAxisSize: MainAxisSize.min,
               children: [
                 Container(
                   padding: const EdgeInsets.all(16),
                   decoration: BoxDecoration(
                     color: Colors.white.withOpacity(0.05),
                     shape: BoxShape.circle,
                   ),
                   child: Icon(Icons.wifi_off_rounded, color: Colors.white54, size: 28),
                 ),
                 const SizedBox(height: 20),
                 Text("CONNECTION LOST", style: GoogleFonts.jetBrainsMono(
                   fontSize: 14, fontWeight: FontWeight.bold, letterSpacing: 2, color: Colors.white)),
                 const SizedBox(height: 8),
                 Text("The neural link to Citadel is severed.", 
                   textAlign: TextAlign.center,
                   style: GoogleFonts.outfit(color: QRColors.textMuted, fontSize: 13)),
                 const SizedBox(height: 28),
                 Row(
                   children: [
                     Expanded(
                       child: OutlinedButton(
                         onPressed: _showServerHelp,
                         style: OutlinedButton.styleFrom(
                           foregroundColor: Colors.white,
                           side: BorderSide(color: Colors.white24),
                           padding: const EdgeInsets.symmetric(vertical: 14),
                           shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                         ),
                         child: Text("DEBUG", style: GoogleFonts.outfit(fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 1)),
                       ),
                     ),
                     const SizedBox(width: 12),
                     Expanded(
                        child: Container(
                          height: 48,
                          decoration: BoxDecoration(
                            gradient: LinearGradient(
                              colors: [const Color(0xFF00E5FF).withOpacity(0.5), const Color(0xFFFF4081).withOpacity(0.5)],
                            ),
                            borderRadius: BorderRadius.circular(12),
                            boxShadow: [
                              BoxShadow(color: const Color(0xFF00E5FF).withOpacity(0.4), blurRadius: 12),
                            ],
                          ),
                          child: ElevatedButton(
                            onPressed: _loadSchema,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.transparent,
                              shadowColor: Colors.transparent,
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                            ),
                            child: Text("RETRY", style: GoogleFonts.outfit(fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 1, color: Colors.white)),
                          ),
                        ),
                     ),
                   ],
                 )
               ],
             ),
          ),
        ),
      );
    }
    if (_schema == null) return Container(color: QRColors.bgDeep);

    return Container(
      decoration: BoxDecoration(
        // 50% transparent to see through to app background
        color: QRColors.bgDeep.withOpacity(0.5),
      ),
      child: Column(
        children: [
          _buildHeader(),
          _buildTabBar(),
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                _buildTabContent('svg'),
                _buildTabContent('gradient'),
                _buildTabContent('diffusion'),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader() {
    return GlassCard(
      margin: const EdgeInsets.fromLTRB(16, 12, 16, 8),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      glowColor: QRColors.primary,
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              gradient: const LinearGradient(colors: QRColors.primaryGradient),
              borderRadius: BorderRadius.circular(14),
              boxShadow: [
                BoxShadow(color: QRColors.primary.withOpacity(0.5), blurRadius: 16),
              ],
            ),
            child: const Icon(Icons.qr_code_scanner, color: Colors.white, size: 26),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                ShaderMask(
                  shaderCallback: (bounds) => const LinearGradient(
                    colors: QRColors.glowGradient,
                  ).createShader(bounds),
                  child: Text("QR STUDIO", style: GoogleFonts.jetBrainsMono(
                    fontSize: 20, fontWeight: FontWeight.bold, letterSpacing: 3, color: Colors.white,
                  )),
                ),
                const SizedBox(height: 2),
                Text("${_schema?.handlers.length ?? 300}+ Templates", 
                  style: TextStyle(fontSize: 12, color: QRColors.textSecondary)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTabBar() {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      child: GlassCard(
        padding: const EdgeInsets.all(4),
        blur: 30,
        child: TabBar(
          controller: _tabController,
          indicator: BoxDecoration(
            gradient: const LinearGradient(colors: QRColors.primaryGradient),
            borderRadius: BorderRadius.circular(14),
            boxShadow: [
              BoxShadow(color: QRColors.primary.withOpacity(0.4), blurRadius: 12),
            ],
          ),
          dividerColor: Colors.transparent,
          indicatorSize: TabBarIndicatorSize.tab,
          labelColor: Colors.white,
          unselectedLabelColor: QRColors.textMuted,
          labelStyle: GoogleFonts.outfit(fontWeight: FontWeight.w600, fontSize: 13),
          tabs: const [
            Tab(text: "Standard"),
            Tab(text: "Gradient"),
            Tab(text: "AI Art"),
          ],
        ),
      ),
    );
  }

  Widget _buildTabContent(String mode) {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Column(
        children: [
          _buildQRPreview(),
          const SizedBox(height: 16),
          if (_chatMessages.isNotEmpty) ...[
            _buildChatMessages(),
            const SizedBox(height: 16),
          ],
          if (mode == 'diffusion') ...[
            _buildPromptInput(),
            const SizedBox(height: 16),
          ],
          _buildHandlerSelector(),
          const SizedBox(height: 16),
          _buildDynamicForm(),
          if (mode == 'gradient') ...[
            const SizedBox(height: 16),
            _buildGradientOptions(),
          ],
          const SizedBox(height: 24),
          _buildActionButtons(mode),
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  Widget _buildQRPreview() {
    return GestureDetector(
      onTap: _resultPath != null ? _showFullscreenPreview : null,
      child: AnimatedBuilder(
        animation: _pulseController,
        builder: (context, child) {
          final glowIntensity = _resultPath != null ? 0.4 + (_pulseController.value * 0.3) : 0.2;
          
          return Container(
            width: 220,
            height: 220,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(28),
              boxShadow: [
                BoxShadow(
                  color: (_resultPath != null || _isGenerating ? QRColors.primary : QRColors.secondary)
                      .withOpacity(glowIntensity),
                  blurRadius: 50,
                  spreadRadius: 5,
                ),
              ],
            ),
            child: GlassCard(
              padding: EdgeInsets.zero,
              borderRadius: BorderRadius.circular(28),
              blur: 30,
              glowColor: _resultPath != null ? QRColors.primary : null,
              child: ClipRRect(
                borderRadius: BorderRadius.circular(28),
                child: _buildPreviewContent(),
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildPreviewContent() {
    if (_isGenerating) {
      return Stack(
        alignment: Alignment.center,
        children: [
          // Spinning ring
          RotationTransition(
            turns: _spinController,
            child: Container(
              width: 140,
              height: 140,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: SweepGradient(
                  colors: [
                    Colors.transparent,
                    QRColors.primary,
                    QRColors.accent,
                    Colors.transparent,
                  ],
                ),
              ),
              child: Center(
                child: Container(
                  width: 120, height: 120,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: QRColors.bgDeep,
                  ),
                ),
              ),
            ),
          ),
          Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.auto_awesome, color: QRColors.primary, size: 32),
              const SizedBox(height: 12),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Text(
                  _statusMessage,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(fontSize: 11, color: QRColors.textSecondary, height: 1.2),
                  textAlign: TextAlign.center,
                ),
              ),
            ],
          ),
        ],
      );
    }
    
    if (_resultPath != null) {
      return Stack(
        fit: StackFit.expand,
        children: [
          Padding(
            padding: const EdgeInsets.all(20),
            child: Builder(
              builder: (context) {
                final api = Provider.of<ApiService>(context, listen: false);
                String url = _resultPath!;
                if (url.startsWith('/')) {
                  url = '${api.baseUrl}$url';
                }
                
                if (url.endsWith('.svg')) {
                  return SvgPicture.network(
                    url,
                    fit: BoxFit.contain,
                    placeholderBuilder: (ctx) => Center(child: CircularProgressIndicator(
                      strokeWidth: 2, color: QRColors.primary)),
                  );
                }
                
                return Image.network(
                  url,
                  fit: BoxFit.contain,
                  loadingBuilder: (ctx, child, progress) {
                    if (progress == null) return child;
                    return Center(child: CircularProgressIndicator(
                      strokeWidth: 2, color: QRColors.primary));
                  },
                  errorBuilder: (ctx, err, stack) => Center(
                    child: Icon(Icons.error_outline, color: Colors.red, size: 40),
                  ),
                );
              }
            ),
          ),
          Positioned(
            bottom: 16, right: 16,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
              decoration: BoxDecoration(
                gradient: const LinearGradient(colors: QRColors.primaryGradient),
                borderRadius: BorderRadius.circular(20),
                boxShadow: [
                  BoxShadow(color: QRColors.primary.withOpacity(0.5), blurRadius: 12),
                ],
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.share, color: Colors.white, size: 14),
                  const SizedBox(width: 6),
                  Text("Share", style: TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.w600)),
                ],
              ),
            ),
          ),
        ],
      );
    }
    
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.qr_code_2, size: 70, color: QRColors.textMuted),
          const SizedBox(height: 12),
          Text("Your QR Code", style: GoogleFonts.outfit(
            fontSize: 14, color: QRColors.textMuted, fontWeight: FontWeight.w500)),
        ],
      ),
    );
  }

  Widget _buildChatMessages() {
    return GlassCard(
      padding: const EdgeInsets.all(14),
      blur: 20,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: _chatMessages.map((msg) {
          final isSuccess = msg.startsWith('✓');
          final isError = msg.startsWith('✕');
          final color = isSuccess ? QRColors.accent : (isError ? Colors.red : QRColors.primary);
          
          return Padding(
            padding: const EdgeInsets.symmetric(vertical: 3),
            child: Row(
              children: [
                Container(
                  width: 6, height: 6,
                  decoration: BoxDecoration(shape: BoxShape.circle, color: color),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(msg, style: TextStyle(fontSize: 12, color: color)),
                ),
              ],
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _buildPromptInput() {
    return GlassCard(
      padding: const EdgeInsets.all(4),
      blur: 20,
      child: TextField(
        controller: _promptController,
        maxLines: 2,
        style: TextStyle(fontSize: 14, color: QRColors.textPrimary),
        decoration: InputDecoration(
          labelText: "AI Art Prompt",
          labelStyle: TextStyle(color: QRColors.textSecondary),
          hintText: "Cyberpunk city, neon lights...",
          hintStyle: TextStyle(color: QRColors.textMuted),
          border: InputBorder.none,
          contentPadding: const EdgeInsets.all(16),
          prefixIcon: Icon(Icons.auto_awesome, color: QRColors.primary),
        ),
      ),
    );
  }

  Widget _buildHandlerSelector() {
    final categories = _schema?.handlers.map((h) => h.category).toSet().toList() ?? [];
    categories.sort();
    
    return GlassCard(
      padding: EdgeInsets.zero,
      blur: 20,
      child: Column(
        children: [
          InkWell(
            onTap: () => setState(() => _showHandlerPicker = !_showHandlerPicker),
            borderRadius: BorderRadius.circular(20),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(colors: QRColors.primaryGradient),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Icon(_getIcon(_selectedHandler?.category ?? ''), 
                      color: Colors.white, size: 22),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(_selectedHandler?.name ?? "Select Template", 
                          style: GoogleFonts.outfit(fontSize: 15, fontWeight: FontWeight.w600, color: QRColors.textPrimary)),
                        Row(
                          children: [
                            Text(_selectedHandler?.category.toUpperCase() ?? "", 
                              style: TextStyle(fontSize: 10, color: QRColors.textMuted, letterSpacing: 0.5)),
                            if (_selectedHandler != null) ...[
                              const SizedBox(width: 8),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                decoration: BoxDecoration(
                                  color: QRColors.primary.withOpacity(0.2),
                                  borderRadius: BorderRadius.circular(6),
                                ),
                                child: Text('${_selectedHandler!.params.length} params',
                                  style: TextStyle(fontSize: 9, color: QRColors.primary)),
                              ),
                            ],
                          ],
                        ),
                      ],
                    ),
                  ),
                  AnimatedRotation(
                    turns: _showHandlerPicker ? 0.5 : 0,
                    duration: const Duration(milliseconds: 200),
                    child: Icon(Icons.keyboard_arrow_down, color: QRColors.textSecondary),
                  ),
                ],
              ),
            ),
          ),
          
          if (_showHandlerPicker) ...[
            Divider(color: QRColors.glassBorder, height: 1),
            Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                children: [
                  // Search - GLASS BLUR
                  ClipRRect(
                    borderRadius: BorderRadius.circular(16),
                    child: BackdropFilter(
                      filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
                      child: Container(
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.05),
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: Colors.white.withOpacity(0.1)),
                          boxShadow: [
                            BoxShadow(
                              color: QRColors.primary.withOpacity(0.1),
                              blurRadius: 20,
                              spreadRadius: -5,
                            ),
                          ],
                        ),
                        child: TextField(
                          style: GoogleFonts.outfit(
                            color: QRColors.textPrimary,
                            fontSize: 15,
                            fontWeight: FontWeight.w500,
                          ),
                          decoration: InputDecoration(
                            hintText: "Search ${_schema?.handlers.length ?? 300}+ templates...",
                            hintStyle: GoogleFonts.outfit(color: QRColors.textMuted),
                            prefixIcon: Container(
                              padding: const EdgeInsets.all(12),
                              child: ShaderMask(
                                shaderCallback: (bounds) => const LinearGradient(
                                  colors: QRColors.primaryGradient,
                                ).createShader(bounds),
                                child: const Icon(Icons.search, size: 22, color: Colors.white),
                              ),
                            ),
                            border: InputBorder.none,
                            contentPadding: const EdgeInsets.symmetric(vertical: 16, horizontal: 8),
                          ),
                          onChanged: _filterHandlers,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  
                  // Category Chips
                  SizedBox(
                    height: 36,
                    child: ListView(
                      scrollDirection: Axis.horizontal,
                      children: [
                        _buildCategoryChip(null, 'All'),
                        ...categories.map((c) => _buildCategoryChip(c, c)),
                      ],
                    ),
                  ),
                  const SizedBox(height: 12),
                  
                  // Handler List
                  SizedBox(
                    height: 200,
                    child: ListView.builder(
                      itemCount: _groupedHandlers.length,
                      itemBuilder: (ctx, i) {
                        final category = _groupedHandlers.keys.elementAt(i);
                        final handlers = _groupedHandlers[category]!;
                        
                        return Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Padding(
                              padding: const EdgeInsets.only(top: 8, bottom: 6),
                              child: Text(category.toUpperCase(), 
                                style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, 
                                  color: QRColors.textMuted, letterSpacing: 1)),
                            ),
                            Wrap(
                              spacing: 6,
                              runSpacing: 6,
                              children: handlers.map((h) => _buildHandlerChip(h)).toList(),
                            ),
                          ],
                        );
                      },
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildCategoryChip(String? category, String label) {
    final isSelected = _selectedCategory == category;
    return GestureDetector(
      onTap: () {
        setState(() => _selectedCategory = category);
        _filterHandlers(_searchQuery);
      },
      child: Container(
        margin: const EdgeInsets.only(right: 8),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        decoration: BoxDecoration(
          gradient: isSelected ? const LinearGradient(colors: QRColors.primaryGradient) : null,
          color: isSelected ? null : QRColors.bgSurface,
          borderRadius: BorderRadius.circular(20),
          border: isSelected ? null : Border.all(color: QRColors.glassBorder),
        ),
        child: Text(label, style: TextStyle(
          fontSize: 12,
          color: isSelected ? Colors.white : QRColors.textSecondary,
          fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
        )),
      ),
    );
  }

  Widget _buildHandlerChip(QRHandlerSchema handler) {
    final isSelected = handler.id == _selectedHandler?.id;
    return GestureDetector(
      onTap: () => _selectHandler(handler),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          gradient: isSelected ? const LinearGradient(colors: QRColors.primaryGradient) : null,
          color: isSelected ? null : QRColors.bgSurface,
          borderRadius: BorderRadius.circular(10),
          border: isSelected ? null : Border.all(color: QRColors.glassBorder),
          boxShadow: isSelected ? [
            BoxShadow(color: QRColors.primary.withOpacity(0.4), blurRadius: 8),
          ] : null,
        ),
        child: Text(handler.name, style: TextStyle(
          fontSize: 12,
          color: isSelected ? Colors.white : QRColors.textSecondary,
          fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
        )),
      ),
    );
  }

  Widget _buildDynamicForm() {
    if (_selectedHandler == null || _selectedHandler!.params.isEmpty) {
      return const SizedBox.shrink();
    }
    
    return GlassCard(
      padding: const EdgeInsets.all(16),
      blur: 20,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('PARAMETERS', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, 
            color: QRColors.textMuted, letterSpacing: 1)),
          const SizedBox(height: 12),
          ..._selectedHandler!.params.map((param) {
            final controller = _controllers[param.name];
            
            if (param.type == 'str' || param.type == 'int' || param.type == 'text') {
              return Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Container(
                  decoration: BoxDecoration(
                    color: QRColors.bgSurface,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: QRColors.glassBorder),
                  ),
                  child: TextField(
                    controller: controller,
                    style: TextStyle(color: QRColors.textPrimary),
                    decoration: InputDecoration(
                      labelText: '${param.name.replaceAll('_', ' ').toUpperCase()}${param.required ? ' *' : ''}',
                      labelStyle: TextStyle(color: QRColors.textSecondary, fontSize: 12),
                      hintText: 'Enter value...',
                      hintStyle: TextStyle(color: QRColors.textMuted),
                      border: InputBorder.none,
                      contentPadding: const EdgeInsets.all(16),
                    ),
                  ),
                ),
              );
            } else if (param.type == 'bool') {
              return Container(
                margin: const EdgeInsets.only(bottom: 12),
                decoration: BoxDecoration(
                  color: QRColors.bgSurface,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: SwitchListTile(
                  title: Text(param.name.replaceAll('_', ' ').toUpperCase(), 
                    style: TextStyle(fontSize: 13, color: QRColors.textPrimary)),
                  value: _dynamicValues[param.name] ?? false,
                  onChanged: (v) => setState(() => _dynamicValues[param.name] = v),
                  activeColor: QRColors.primary,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
              );
            }
            return const SizedBox.shrink();
          }),
        ],
      ),
    );
  }

  Widget _buildGradientOptions() {
    return GlassCard(
      padding: const EdgeInsets.all(16),
      blur: 20,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('COLORS', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, 
                color: QRColors.textMuted, letterSpacing: 1)),
              GestureDetector(
                onTap: _randomColors,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(colors: QRColors.accentGradient),
                    borderRadius: BorderRadius.circular(20),
                    boxShadow: [
                      BoxShadow(color: QRColors.accent.withOpacity(0.4), blurRadius: 8),
                    ],
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.casino, color: Colors.white, size: 14),
                      const SizedBox(width: 6),
                      Text('Random', style: TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.w600)),
                    ],
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          
          Row(
            children: [
              Expanded(child: _buildColorSelector('Start', _startColor, (c) => setState(() => _startColor = c))),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                child: Icon(Icons.arrow_forward, color: QRColors.textMuted, size: 20),
              ),
              Expanded(child: _buildColorSelector('End', _endColor, (c) => setState(() => _endColor = c))),
            ],
          ),
          const SizedBox(height: 20),
          
          Text('GRADIENT TYPE', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, 
            color: QRColors.textMuted, letterSpacing: 1)),
          const SizedBox(height: 10),
          Row(
            children: [
              _buildOptionChip('radial', 'Radial', Icons.radio_button_checked, _gradientType == 'radial', 
                () => setState(() => _gradientType = 'radial')),
              _buildOptionChip('horizontal', 'Horiz', Icons.swap_horiz, _gradientType == 'horizontal',
                () => setState(() => _gradientType = 'horizontal')),
              _buildOptionChip('vertical', 'Vert', Icons.swap_vert, _gradientType == 'vertical',
                () => setState(() => _gradientType = 'vertical')),
              _buildOptionChip('diagonal', 'Diag', Icons.north_east, _gradientType == 'diagonal',
                () => setState(() => _gradientType = 'diagonal')),
            ],
          ),
          const SizedBox(height: 16),
          
          Text('MODULE STYLE', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, 
            color: QRColors.textMuted, letterSpacing: 1)),
          const SizedBox(height: 10),
          Row(
            children: [
              _buildOptionChip('rounded', 'Round', Icons.rounded_corner, _moduleDrawer == 'rounded',
                () => setState(() => _moduleDrawer = 'rounded')),
              _buildOptionChip('square', 'Square', Icons.crop_square, _moduleDrawer == 'square',
                () => setState(() => _moduleDrawer = 'square')),
              _buildOptionChip('circle', 'Circle', Icons.circle_outlined, _moduleDrawer == 'circle',
                () => setState(() => _moduleDrawer = 'circle')),
              _buildOptionChip('gapped', 'Gapped', Icons.grid_view, _moduleDrawer == 'gapped',
                () => setState(() => _moduleDrawer = 'gapped')),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildColorSelector(String label, Color current, Function(Color) onPicked) {
    return GestureDetector(
      onTap: () => _showColorPicker(label, current, onPicked),
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: current.withOpacity(0.2),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: current, width: 2),
          boxShadow: [
            BoxShadow(color: current.withOpacity(0.3), blurRadius: 12),
          ],
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(width: 24, height: 24, decoration: BoxDecoration(
              color: current, shape: BoxShape.circle,
              boxShadow: [BoxShadow(color: current.withOpacity(0.6), blurRadius: 10)],
            )),
            const SizedBox(width: 10),
            Text(label, style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13, color: QRColors.textPrimary)),
          ],
        ),
      ),
    );
  }

  void _showColorPicker(String label, Color current, Function(Color) onPicked) {
    double hue = HSLColor.fromColor(current).hue;
    double saturation = HSLColor.fromColor(current).saturation;
    double lightness = HSLColor.fromColor(current).lightness;
    
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setModalState) => Container(
          height: MediaQuery.of(context).size.height * 0.75,
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [QRColors.bgCard, QRColors.bgDeep],
            ),
            borderRadius: const BorderRadius.vertical(top: Radius.circular(28)),
          ),
          child: Column(
            children: [
              const SizedBox(height: 12),
              Container(width: 40, height: 4, decoration: BoxDecoration(
                color: QRColors.glassBorder, borderRadius: BorderRadius.circular(2))),
              const SizedBox(height: 20),
              Text('Select $label Color', style: GoogleFonts.outfit(
                fontSize: 20, fontWeight: FontWeight.bold, color: QRColors.textPrimary)),
              const SizedBox(height: 24),
              
              // Preview
              Container(
                width: 90, height: 90,
                decoration: BoxDecoration(
                  color: HSLColor.fromAHSL(1, hue, saturation, lightness).toColor(),
                  shape: BoxShape.circle,
                  boxShadow: [BoxShadow(
                    color: HSLColor.fromAHSL(1, hue, saturation, lightness).toColor().withOpacity(0.6),
                    blurRadius: 30, spreadRadius: 5,
                  )],
                ),
              ),
              const SizedBox(height: 28),
              
              // Sliders
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 24),
                child: Column(
                  children: [
                    _buildSlider('HUE', hue, 0, 360, (v) => setModalState(() => hue = v)),
                    _buildSlider('SATURATION', saturation, 0, 1, (v) => setModalState(() => saturation = v)),
                    _buildSlider('LIGHTNESS', lightness, 0, 1, (v) => setModalState(() => lightness = v)),
                  ],
                ),
              ),
              
              const SizedBox(height: 20),
              Text('QUICK PRESETS', style: TextStyle(fontSize: 10, color: QRColors.textMuted, letterSpacing: 1)),
              const SizedBox(height: 12),
              
              SizedBox(
                height: 100,
                child: GridView.builder(
                  padding: const EdgeInsets.symmetric(horizontal: 24),
                  scrollDirection: Axis.horizontal,
                  gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 2, mainAxisSpacing: 8, crossAxisSpacing: 8,
                  ),
                  itemCount: colorPresets.length,
                  itemBuilder: (ctx, i) => GestureDetector(
                    onTap: () {
                      onPicked(colorPresets[i]);
                      Navigator.pop(ctx);
                    },
                    child: Container(
                      decoration: BoxDecoration(
                        color: colorPresets[i],
                        shape: BoxShape.circle,
                        border: Border.all(color: QRColors.glassBorder, width: 2),
                        boxShadow: [
                          BoxShadow(color: colorPresets[i].withOpacity(0.4), blurRadius: 8),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
              
              const Spacer(),
              
              Padding(
                padding: const EdgeInsets.all(24),
                child: SizedBox(
                  width: double.infinity,
                  height: 56,
                  child: ElevatedButton(
                    onPressed: () {
                      onPicked(HSLColor.fromAHSL(1, hue, saturation, lightness).toColor());
                      Navigator.pop(ctx);
                    },
                    style: ElevatedButton.styleFrom(
                      padding: EdgeInsets.zero,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                    ),
                    child: Ink(
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(colors: QRColors.primaryGradient),
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: Container(
                        alignment: Alignment.center,
                        child: Text('APPLY', style: GoogleFonts.outfit(
                          fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white, letterSpacing: 1)),
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSlider(String label, double value, double min, double max, Function(double) onChanged) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: TextStyle(fontSize: 10, color: QRColors.textMuted, letterSpacing: 1)),
        SliderTheme(
          data: SliderTheme.of(context).copyWith(
            trackHeight: 8,
            thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 10),
            activeTrackColor: QRColors.primary,
            inactiveTrackColor: QRColors.bgSurface,
            thumbColor: Colors.white,
          ),
          child: Slider(value: value, min: min, max: max, onChanged: onChanged),
        ),
      ],
    );
  }

  Widget _buildOptionChip(String value, String label, IconData icon, bool isSelected, VoidCallback onTap) {
    return Expanded(
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          margin: const EdgeInsets.only(right: 8),
          padding: const EdgeInsets.symmetric(vertical: 10),
          decoration: BoxDecoration(
            gradient: isSelected ? const LinearGradient(colors: QRColors.primaryGradient) : null,
            color: isSelected ? null : QRColors.bgSurface,
            borderRadius: BorderRadius.circular(10),
            border: isSelected ? null : Border.all(color: QRColors.glassBorder),
            boxShadow: isSelected ? [
              BoxShadow(color: QRColors.primary.withOpacity(0.4), blurRadius: 8),
            ] : null,
          ),
          child: Column(
            children: [
              Icon(icon, size: 18, color: isSelected ? Colors.white : QRColors.textSecondary),
              const SizedBox(height: 4),
              Text(label, style: TextStyle(fontSize: 9, color: isSelected ? Colors.white : QRColors.textSecondary)),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildActionButtons(String mode) {
    return Column(
      children: [
        SizedBox(
          width: double.infinity,
          height: 58,
          child: ElevatedButton(
            style: ElevatedButton.styleFrom(
              padding: EdgeInsets.zero,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
              elevation: 0,
            ),
            onPressed: _isGenerating ? null : () => _generateQR(mode),
            child: Ink(
              decoration: BoxDecoration(
                gradient: _isGenerating 
                  ? LinearGradient(colors: [QRColors.bgSurface, QRColors.bgCard])
                  : const LinearGradient(colors: QRColors.primaryGradient),
                borderRadius: BorderRadius.circular(18),
                boxShadow: _isGenerating ? null : [
                  BoxShadow(color: QRColors.primary.withOpacity(0.5), blurRadius: 20, offset: const Offset(0, 6)),
                ],
              ),
              child: Container(
                alignment: Alignment.center,
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    if (_isGenerating) ...[
                      SizedBox(width: 22, height: 22, 
                        child: CircularProgressIndicator(strokeWidth: 2, color: QRColors.primary)),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(_statusMessage.toUpperCase(),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          textAlign: TextAlign.center,
                          style: GoogleFonts.outfit(fontSize: 14, fontWeight: FontWeight.bold, color: QRColors.textSecondary)),
                      ),
                    ] else ...[
                      Text(_getButtonLabel(mode),
                        style: GoogleFonts.outfit(fontSize: 15, fontWeight: FontWeight.bold, color: Colors.white, letterSpacing: 1)),
                      const SizedBox(width: 10),
                      const Icon(Icons.arrow_forward, color: Colors.white, size: 20),
                    ],
                  ],
                ),
              ),
            ),
          ),
        ),
        
        if (_isGenerating && mode == 'diffusion') ...[
          const SizedBox(height: 12),
          SizedBox(
            width: double.infinity,
            height: 48,
            child: OutlinedButton(
              onPressed: _cancelGeneration,
              style: OutlinedButton.styleFrom(
                side: BorderSide(color: Colors.red.shade400, width: 2),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.close, color: Colors.red.shade400, size: 18),
                  const SizedBox(width: 8),
                  Text('CANCEL', style: GoogleFonts.outfit(
                    fontSize: 13, fontWeight: FontWeight.bold, color: Colors.red.shade400)),
                ],
              ),
            ),
          ),
        ],
      ],
    );
  }

  String _getButtonLabel(String mode) {
    switch (mode) {
      case 'svg': return 'GENERATE';
      case 'gradient': return 'GENERATE GRADIENT';
      case 'diffusion': return 'GENERATE AI ART';
      default: return 'GENERATE';
    }
  }
}
