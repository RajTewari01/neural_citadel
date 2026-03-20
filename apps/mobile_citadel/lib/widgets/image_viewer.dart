import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:url_launcher/url_launcher.dart';
import 'dart:math' as math;

/// Full-screen image viewer with pinch-to-zoom and pan
class ImageViewer extends StatefulWidget {
  final String imageUrl;
  final String? heroTag;

  const ImageViewer({super.key, required this.imageUrl, this.heroTag});

  static void show(BuildContext context, String imageUrl, {String? heroTag}) {
    Navigator.of(context).push(
      PageRouteBuilder(
        opaque: false,
        barrierDismissible: true,
        barrierColor: Colors.black87,
        pageBuilder: (_, __, ___) => ImageViewer(imageUrl: imageUrl, heroTag: heroTag),
        transitionsBuilder: (_, animation, __, child) {
          return FadeTransition(opacity: animation, child: child);
        },
      ),
    );
  }

  @override
  State<ImageViewer> createState() => _ImageViewerState();
}

class _ImageViewerState extends State<ImageViewer> {
  final TransformationController _controller = TransformationController();
  bool _showControls = true;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _resetZoom() {
    _controller.value = Matrix4.identity();
  }

  @override
  Widget build(BuildContext context) {
    final imageWidget = widget.imageUrl.startsWith('http')
        ? Image.network(
            widget.imageUrl,
            fit: BoxFit.contain,
            loadingBuilder: (ctx, child, progress) {
              if (progress == null) return child;
              return Center(
                child: CircularProgressIndicator(
                  value: progress.expectedTotalBytes != null
                      ? progress.cumulativeBytesLoaded / progress.expectedTotalBytes!
                      : null,
                  color: Colors.white,
                ),
              );
            },
            errorBuilder: (_, __, ___) => const Icon(Icons.broken_image, size: 64, color: Colors.white54),
          )
        : Image.asset(widget.imageUrl, fit: BoxFit.contain);

    return GestureDetector(
      onTap: () => setState(() => _showControls = !_showControls),
      child: Scaffold(
        backgroundColor: Colors.transparent,
        body: Stack(
          children: [
            // Zoomable Image
            Center(
              child: InteractiveViewer(
                transformationController: _controller,
                minScale: 0.5,
                maxScale: 4.0,
                child: widget.heroTag != null
                    ? Hero(tag: widget.heroTag!, child: imageWidget)
                    : imageWidget,
              ),
            ),

            // Top Controls
            if (_showControls)
              Positioned(
                top: MediaQuery.of(context).padding.top + 8,
                left: 8,
                right: 8,
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    // Close button
                    IconButton(
                      icon: Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: Colors.black54,
                          borderRadius: BorderRadius.circular(24),
                        ),
                        child: const Icon(Icons.close, color: Colors.white),
                      ),
                      onPressed: () => Navigator.pop(context),
                    ),
                    // Actions
                    Row(
                      children: [
                        IconButton(
                          icon: Container(
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              color: Colors.black54,
                              borderRadius: BorderRadius.circular(24),
                            ),
                            child: const Icon(Icons.refresh, color: Colors.white),
                          ),
                          onPressed: _resetZoom,
                        ),
                        IconButton(
                          icon: Container(
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              color: Colors.black54,
                              borderRadius: BorderRadius.circular(24),
                            ),
                            child: const Icon(Icons.download, color: Colors.white),
                          ),
                          onPressed: () async {
                            try {
                              String url = widget.imageUrl.trim();
                              final uri = Uri.parse(url);
                              if (!await launchUrl(uri, mode: LaunchMode.externalApplication)) {
                                 throw 'Could not launch $url';
                              }
                            } catch (e) {
                              debugPrint("Download Error: $e");
                               ScaffoldMessenger.of(context).showSnackBar(
                                 SnackBar(content: Text('Error launching URL: $e'), backgroundColor: Colors.red),
                               );
                            }
                          },
                        ),
                        IconButton(
                          icon: Container(
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              color: Colors.black54,
                              borderRadius: BorderRadius.circular(24),
                            ),
                            child: const Icon(Icons.share, color: Colors.white),
                          ),
                          onPressed: () {
                            // TODO: Share functionality
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(content: Text('Share not implemented')),
                            );
                          },
                        ),
                      ],
                    ),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }
}
