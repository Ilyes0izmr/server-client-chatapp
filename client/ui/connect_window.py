from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QLineEdit, QFrame)
from PyQt6.QtCore import pyqtSignal, Qt

class ConnectWindow(QWidget):
    connect_signal = pyqtSignal(str, int)
    
    def __init__(self, client_socket):
        super().__init__()
        self.client_socket = client_socket
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Title
        title = QLabel("🔗 Connect to Chat Server")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 20px;
                font-weight: bold;
                padding: 10px;
                font-family: "Segoe UI", Arial, sans-serif;
            }
        """)
        layout.addWidget(title)
        
        layout.addSpacing(30)
        
        # Server IP Input
        ip_frame = QFrame()
        ip_frame.setStyleSheet("QFrame { background-color: transparent; }")
        ip_layout = QHBoxLayout(ip_frame)
        ip_layout.setContentsMargins(0, 0, 0, 0)
        
        ip_label = QLabel("Server IP:")
        ip_label.setStyleSheet("color: white; font-size: 12px; font-family: 'Segoe UI', Arial, sans-serif;")
        ip_label.setFixedWidth(80)
        
        self.ip_entry = QLineEdit()
        self.ip_entry.setPlaceholderText("localhost")
        self.ip_entry.setText("localhost")
        self.ip_entry.setStyleSheet("""
            QLineEdit {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #404040;
                border-radius: 5px;
                padding: 8px;
                font-size: 12px;
                font-family: "Segoe UI", Arial, sans-serif;
            }
            QLineEdit:focus {
                border: 1px solid #00b894;
            }
        """)
        self.ip_entry.setFixedHeight(35)
        
        ip_layout.addWidget(ip_label)
        ip_layout.addWidget(self.ip_entry)
        layout.addWidget(ip_frame)
        
        layout.addSpacing(20)
        
        # Connect Button
        self.connect_btn = QPushButton("🚀 Connect to Server")
        self.connect_btn.setFixedSize(200, 40)
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #00b894;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 12px;
                font-family: "Segoe UI", Arial, sans-serif;
            }
            QPushButton:hover {
                background-color: #00a085;
            }
            QPushButton:disabled {
                background-color: #636e72;
                color: #b2bec3;
            }
        """)
        self.connect_btn.clicked.connect(self.connect_to_server)
        layout.addWidget(self.connect_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addSpacing(20)
        
        # Status Label
        self.status_label = QLabel("⚪ Status: Ready to connect")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #b2bec3;
                font-weight: bold;
                font-size: 12px;
                padding: 8px;
                font-family: "Segoe UI", Arial, sans-serif;
            }
        """)
        layout.addWidget(self.status_label)
        
        layout.addStretch()
    
    def connect_to_server(self):
        host = self.ip_entry.text()
        port = 5000
        
        # Emit signal to parent
        self.connect_signal.emit(host, port)
    
    def update_status(self, connected: bool, status_text: str = ""):
        """Update connection status"""
        if connected:
            self.status_label.setText(f"🟢 {status_text}")
            self.status_label.setStyleSheet("color: #00b894; font-weight: bold; font-size: 12px; padding: 8px;")
        else:
            self.status_label.setText(status_text)
            self.status_label.setStyleSheet("color: #e17055; font-weight: bold; font-size: 12px; padding: 8px;")
    
    def set_connect_enabled(self, enabled: bool):
        """Enable or disable connect button"""
        self.connect_btn.setEnabled(enabled)
        if enabled:
            self.ip_entry.setEnabled(True)