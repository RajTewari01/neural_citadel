import 'package:flutter/material.dart';

enum VideoOverlayMode {
  hidden,
  background, // Full Screen, behind UI
  floating,   // Draggable, Interactive
}

class DraggableVideoOverlay extends StatefulWidget {
  final Widget videoView;
  final VideoOverlayMode mode;
  final VoidCallback onMaximize;

  const DraggableVideoOverlay({
    Key? key,
    required this.videoView,
    required this.mode,
    required this.onMaximize,
  }) : super(key: key);

  @override
  _DraggableVideoOverlayState createState() => _DraggableVideoOverlayState();
}

class _DraggableVideoOverlayState extends State<DraggableVideoOverlay> {
  Offset _position = const Offset(20, 50); // Initial floating position
  bool _isDragging = false;

  @override
  Widget build(BuildContext context) {
    print("Overlay Rebuild: Mode=${widget.mode}");

    if (widget.mode == VideoOverlayMode.hidden) {
      return const SizedBox.shrink();
    }

    if (widget.mode == VideoOverlayMode.background) {
      // FULL SCREEN BACKGROUND
      // Uses IgnorePointer so touches pass through to InCallScreen UI
      return Positioned.fill(
        child: IgnorePointer(
          ignoring: true, 
          child: widget.videoView, // The Native View
        ),
      );
    }

    // FLOATING MODE
    // 9:16 Aspect Ratio (e.g., 90x160)
    const double width = 100;
    const double height = 177; // 9:16 approx

    final screenSize = MediaQuery.of(context).size;

    // Ensure initial position is valid (Bottom Right default)
    if (_position == const Offset(20, 50)) {
        _position = Offset(
            screenSize.width - width - 16, 
            screenSize.height - height - 100
        );
    }

    return Positioned(
      left: _position.dx,
      top: _position.dy,
      child: GestureDetector(
        onPanUpdate: (details) {
          setState(() {
            _position += details.delta;
            _isDragging = true;
          });
        },
        onPanEnd: (_) => setState(() => _isDragging = false),
        onTap: () {
            if (!_isDragging) {
                widget.onMaximize();
            }
        },
        child: Material(
          elevation: 8,
          color: Colors.black,
          borderRadius: BorderRadius.circular(12),
          clipBehavior: Clip.antiAlias,
          child: SizedBox(
            width: width,
            height: height,
            child: Stack(
              children: [
                // 1. The Video
                widget.videoView,

                // 2. Overlay Gradient/border
                Container(
                  decoration: BoxDecoration(
                    border: Border.all(color: Colors.white.withOpacity(0.2), width: 1),
                    borderRadius: BorderRadius.circular(12),
                    gradient: LinearGradient(
                      colors: [Colors.black54, Colors.transparent],
                      begin: Alignment.bottomCenter,
                      end: Alignment.topCenter
                    )
                  ),
                ),
                
                // 3. Expand Icon (Optional hint)
                /*
                const Center(
                    child: Icon(Icons.open_in_full, color: Colors.white38, size: 24)
                )
                */
              ],
            ),
          ),
        ),
      ),
    );
  }
}
