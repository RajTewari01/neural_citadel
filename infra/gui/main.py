"""
Neural Citadel - PyQt6 UI Experiment
Entry point with mini floating bar support
"""

import sys
from pathlib import Path

# Add project root to sys.path to ensure 'infra' package is resolvable
# This fixes the split-brain singleton issue with ThemeManager
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication
from infra.gui.main_window import NeuralCitadelWindow
from infra.gui.mini_bar import MiniFloatingBar


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Neural Citadel")
    
    # Set app icon
    from PyQt6.QtGui import QIcon
    from pathlib import Path
    icon_path = Path(__file__).parent.parent.parent / "assets" / "apps_assets" / "gui" / "neural_citadel.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    # Create mini bar first (hidden initially)
    mini_bar = MiniFloatingBar()
    
    # Create main window
    window = NeuralCitadelWindow(mini_bar)
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
