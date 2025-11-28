"""
Top navigation bar with server controls and status.
"""

from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QLabel, QPushButton, 
                           QVBoxLayout, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from .styles import Styles


class NavBar(QWidget):
    """Top navigation bar with server status and controls."""
    
    def __init__(self):
        super().__init__()
        self.is_udp_running = False
        self.init_ui()
        
    def init_ui(self):
        """Initialize the navigation bar UI."""
        layout = QHBoxLayout()
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(16)
        
        # App logo/title
        title_label = QLabel("CHATSERV - UDP")
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {Styles.TEXT_PRIMARY};
                font-size: 20px;
                font-weight: bold;
                font-family: "Monospace", "Courier New";
            }}
        """)
        
        # Status indicator
        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet(f"""
            QLabel {{
                color: {Styles.ACCENT_RED};
                font-size: 16px;
                font-weight: bold;
            }}
        """)
        self.status_label = QLabel("Stopped")
        self.status_label.setStyleSheet(f"color: {Styles.TEXT_SECONDARY};")
        
        status_layout = QHBoxLayout()
        status_layout.addWidget(self.status_indicator)
        status_layout.addWidget(self.status_label)
        status_layout.setSpacing(8)
        
        status_widget = QWidget()
        status_widget.setLayout(status_layout)
        
        # Spacer
        layout.addWidget(title_label)
        layout.addStretch()
        layout.addWidget(status_widget)
        layout.addStretch()
        
        self.setLayout(layout)
        self.setFixedHeight(60)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {Styles.BACKGROUND_SECONDARY};
                border-bottom: 1px solid {Styles.BORDER_COLOR};
            }}
        """)
    
    def update_server_status(self, udp_running: bool):
        """Update server status display."""
        self.is_udp_running = udp_running
        
        if udp_running:
            self.status_indicator.setStyleSheet(f"""
                QLabel {{
                    color: {Styles.ACCENT_GREEN};
                    font-size: 16px;
                    font-weight: bold;
                }}
            """)
            self.status_label.setText("Running (UDP)")
        else:
            self.status_indicator.setStyleSheet(f"""
                QLabel {{
                    color: {Styles.ACCENT_RED};
                    font-size: 16px;
                    font-weight: bold;
                }}
            """)
            self.status_label.setText("Stopped")