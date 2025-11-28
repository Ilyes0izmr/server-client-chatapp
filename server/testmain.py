import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from server.ui.main_window import ServerMainWindow
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont

def main():
    """Launch the server GUI application."""
    app = QApplication(sys.argv)
    
    # Set application-wide font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    window = ServerMainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()