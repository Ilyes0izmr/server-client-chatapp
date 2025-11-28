from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QGroupBox, QMessageBox,
                            QRadioButton, QButtonGroup, QFrame)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont, QIntValidator
import logging

class ConnectWindow(QWidget):
    """Window for connecting to chat server with protocol selection"""
    
    connected = pyqtSignal(str, int, str, str)  # host, port, username, protocol
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle("Chat Client - Connect to Server")
        self.setFixedSize(500, 600)  # Made it bigger to fit everything
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("CHATCLIENT")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #E0E0E0; margin-bottom: 5px;")
        main_layout.addWidget(title_label)
        
        subtitle_label = QLabel("Connect to Chat Server")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #999; font-size: 14px; margin-bottom: 20px;")
        main_layout.addWidget(subtitle_label)
        
        # Server settings group - MAKE SURE THIS IS ADDED
        server_group = QGroupBox("Server Configuration")
        server_group.setStyleSheet("""
            QGroupBox {
                background-color: #1A1A1A;
                border: 2px solid #333;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                font-weight: bold;
                color: #E0E0E0;
                font-size: 14px;
            }
            QGroupBox::title {
                color: #E0E0E0;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
            }
        """)
        
        server_layout = QVBoxLayout()
        server_layout.setSpacing(15)
        server_layout.setContentsMargins(15, 15, 15, 15)
        
        # Protocol selection
        protocol_label = QLabel("Select Protocol:")
        protocol_label.setStyleSheet("font-weight: bold; color: #E0E0E0; font-size: 14px;")
        server_layout.addWidget(protocol_label)
        
        # Radio buttons container
        radio_container = QWidget()
        radio_layout = QHBoxLayout(radio_container)
        radio_layout.setContentsMargins(0, 0, 0, 0)
        
        self.protocol_group = QButtonGroup(self)
        
        self.tcp_radio = QRadioButton("TCP (Reliable)")
        self.udp_radio = QRadioButton("UDP (Fast)")
        self.tcp_radio.setChecked(True)
        
        # Style radio buttons
        radio_style = """
            QRadioButton {
                color: #E0E0E0;
                font-size: 13px;
                padding: 8px;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
                border-radius: 8px;
                border: 2px solid #666;
            }
            QRadioButton::indicator:checked {
                background-color: #E0E0E0;
                border: 2px solid #E0E0E0;
            }
            QRadioButton::indicator:unchecked {
                background-color: #2D2D2D;
            }
        """
        self.tcp_radio.setStyleSheet(radio_style)
        self.udp_radio.setStyleSheet(radio_style)
        
        self.protocol_group.addButton(self.tcp_radio)
        self.protocol_group.addButton(self.udp_radio)
        
        radio_layout.addWidget(self.tcp_radio)
        radio_layout.addWidget(self.udp_radio)
        radio_layout.addStretch()
        
        server_layout.addWidget(radio_container)
        
        # Server address section
        server_address_label = QLabel("Server Address:")
        server_address_label.setStyleSheet("font-weight: bold; color: #E0E0E0; font-size: 14px; margin-top: 10px;")
        server_layout.addWidget(server_address_label)
        
        # Host input
        host_layout = QHBoxLayout()
        host_label = QLabel("Host:")
        host_label.setStyleSheet("color: #E0E0E0; min-width: 60px;")
        host_layout.addWidget(host_label)
        
        self.host_input = QLineEdit("localhost")
        self.host_input.setPlaceholderText("Enter server IP or hostname")
        self.host_input.setStyleSheet("""
            QLineEdit {
                background-color: #2D2D2D;
                color: #E0E0E0;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #666;
            }
        """)
        host_layout.addWidget(self.host_input)
        server_layout.addLayout(host_layout)
        
        # Port input
        port_layout = QHBoxLayout()
        port_label = QLabel("Port:")
        port_label.setStyleSheet("color: #E0E0E0; min-width: 60px;")
        port_layout.addWidget(port_label)
        
        self.port_input = QLineEdit("5050")
        self.port_input.setPlaceholderText("Server port")
        self.port_input.setValidator(QIntValidator(1, 65535))
        self.port_input.setStyleSheet("""
            QLineEdit {
                background-color: #2D2D2D;
                color: #E0E0E0;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #666;
            }
        """)
        port_layout.addWidget(self.port_input)
        server_layout.addLayout(port_layout)
        
        server_group.setLayout(server_layout)
        main_layout.addWidget(server_group)
        
        # User settings group
        user_group = QGroupBox("User Configuration")
        user_group.setStyleSheet("""
            QGroupBox {
                background-color: #1A1A1A;
                border: 2px solid #333;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                font-weight: bold;
                color: #E0E0E0;
                font-size: 14px;
            }
            QGroupBox::title {
                color: #E0E0E0;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
            }
        """)
        
        user_layout = QVBoxLayout()
        user_layout.setSpacing(15)
        user_layout.setContentsMargins(15, 15, 15, 15)
        
        username_layout = QHBoxLayout()
        username_label = QLabel("Username:")
        username_label.setStyleSheet("color: #E0E0E0; min-width: 80px;")
        username_layout.addWidget(username_label)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your display name")
        self.username_input.setStyleSheet("""
            QLineEdit {
                background-color: #2D2D2D;
                color: #E0E0E0;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #666;
            }
        """)
        username_layout.addWidget(self.username_input)
        user_layout.addLayout(username_layout)
        
        user_group.setLayout(user_layout)
        main_layout.addWidget(user_group)
        
        # Connect button
        self.connect_button = QPushButton("Connect to Server")
        self.connect_button.setStyleSheet("""
            QPushButton {
                background-color: #2D5A2D;
                color: #E0E0E0;
                border: 2px solid #3D6A3D;
                border-radius: 6px;
                padding: 12px;
                font-weight: bold;
                font-size: 14px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #357535;
                border: 2px solid #457A45;
            }
            QPushButton:pressed {
                background-color: #245224;
            }
            QPushButton:disabled {
                background-color: #1A2A1A;
                color: #666;
                border: 2px solid #2D3A2D;
            }
        """)
        self.connect_button.clicked.connect(self.connect_to_server)
        self.connect_button.setMinimumHeight(45)
        main_layout.addWidget(self.connect_button)
        
        # Status label
        self.status_label = QLabel("Ready to connect")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #999; font-size: 12px; margin-top: 10px;")
        main_layout.addWidget(self.status_label)
        
        main_layout.addStretch()
        self.setLayout(main_layout)
    
    def connect_to_server(self):
        """Attempt to connect to server"""
        host = self.host_input.text().strip()
        port_text = self.port_input.text().strip()
        username = self.username_input.text().strip()
        protocol = "TCP" if self.tcp_radio.isChecked() else "UDP"
        
        print(f"DEBUG: Protocol selected: {protocol}")  # Debug line
        
        # Validation
        if not host:
            self.show_error("Please enter a server host address")
            return
        
        if not port_text:
            self.show_error("Please enter a server port number")
            return
        
        if not username:
            self.show_error("Please enter a username")
            return
        
        try:
            port = int(port_text)
            if port < 1 or port > 65535:
                raise ValueError("Port out of range")
        except ValueError:
            self.show_error("Please enter a valid port number (1-65535)")
            return
        
        # Update UI
        self.set_connecting(True, f"Connecting via {protocol}...")
        
        # Emit connection signal
        self.connected.emit(host, port, username, protocol)
    
    def show_error(self, message):
        """Show error message"""
        QMessageBox.critical(self, "Connection Error", message)
        self.set_connecting(False, "Connection failed")
    
    def show_success(self, message):
        """Show success message"""
        self.set_connecting(False, message)
    
    def set_connecting(self, connecting, status_message=""):
        """Update UI during connection attempt"""
        self.connect_button.setEnabled(not connecting)
        self.host_input.setEnabled(not connecting)
        self.port_input.setEnabled(not connecting)
        self.username_input.setEnabled(not connecting)
        self.tcp_radio.setEnabled(not connecting)
        self.udp_radio.setEnabled(not connecting)
        
        if connecting:
            self.connect_button.setText("Connecting...")
            self.status_label.setText(status_message)
            self.status_label.setStyleSheet("color: #E0E0E0; font-size: 12px;")
        else:
            self.connect_button.setText("Connect to Server")
            self.status_label.setText(status_message)
            self.status_label.setStyleSheet("color: #999; font-size: 12px;")
    
    def reset(self):
        """Reset the connection window"""
        self.set_connecting(False, "Ready to connect")
        self.host_input.setFocus()