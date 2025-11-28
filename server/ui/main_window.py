"""
Main server application window with three-panel layout - UDP Only
"""

import sys
import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                           QSplitter, QPushButton, QLabel, QFrame, QScrollArea,
                           QApplication)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

# Import from the same package using relative imports
from .navbar import NavBar
from .sidebar_clients import SidebarClients
from .chat_window import ChatWindow
from .styles import Styles


class ControlPanel(QWidget):
    """Left control panel with server control buttons."""
    
    # Signals
    udp_server_toggled = pyqtSignal(bool)
    stop_server_clicked = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.is_udp_running = False
        self.init_ui()
        
    def init_ui(self):
        """Initialize control panel UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(12)
        
        # App title
        title_label = QLabel("CHATSERV")
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {Styles.TEXT_PRIMARY};
                font-size: 18px;
                font-weight: bold;
                font-family: "Monospace", "Courier New";
                qproperty-alignment: AlignCenter;
                padding: 8px;
                border-bottom: 1px solid {Styles.BORDER_COLOR};
                margin-bottom: 8px;
            }}
        """)
        
        # Server control buttons - UDP Only
        self.udp_btn = QPushButton("📡 UDP Server")  
        self.udp_btn.setFixedHeight(50)
        self.udp_btn.clicked.connect(self.toggle_udp_server)
        
        self.stop_btn = QPushButton("⏹ Stop Server")
        self.stop_btn.setFixedHeight(50)
        self.stop_btn.clicked.connect(self.stop_server_clicked.emit)
        self.stop_btn.setEnabled(False)
        
        # Update button styles
        self.update_button_styles()
        
        # Add widgets to layout
        layout.addWidget(title_label)
        layout.addWidget(self.udp_btn)
        layout.addWidget(self.stop_btn)
        layout.addStretch()
        
        self.setLayout(layout)
        self.setStyleSheet(Styles.SIDEBAR)
        self.setMinimumWidth(180)
        self.setMaximumWidth(220)
    
    def update_button_styles(self):
        """Update button styles based on server states."""
        # UDP Button  
        if self.is_udp_running:
            self.udp_btn.setStyleSheet(Styles.BUTTON_UDP_RUNNING)
            self.udp_btn.setText("📡 UDP (Running)")
        else:
            self.udp_btn.setStyleSheet(Styles.BUTTON_UDP)
            self.udp_btn.setText("📡 UDP Server")
        
        # Stop Button
        if self.is_udp_running:
            self.stop_btn.setStyleSheet(Styles.BUTTON_STOP_ACTIVE)
            self.stop_btn.setEnabled(True)
        else:
            self.stop_btn.setStyleSheet(Styles.BUTTON_STOP)
            self.stop_btn.setEnabled(False)
    
    def toggle_udp_server(self):
        """Toggle UDP server state."""
        self.is_udp_running = not self.is_udp_running
        self.update_button_styles()
        self.udp_server_toggled.emit(self.is_udp_running)
    
    def set_server_state(self, udp_running: bool):
        """Set server running state."""
        self.is_udp_running = udp_running
        self.update_button_styles()


class MainWindow(QMainWindow):
    """Main server application window."""
    
    def __init__(self):
        super().__init__()
        self.udp_server = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize main window UI."""
        self.setWindowTitle("Chat Server - UDP")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Navigation bar
        self.navbar = NavBar()
        main_layout.addWidget(self.navbar)
        
        # Content area (control panel + sidebar + chat)
        content_widget = QWidget()
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Control panel (left)
        self.control_panel = ControlPanel()
        self.control_panel.udp_server_toggled.connect(self.on_udp_toggled)
        self.control_panel.stop_server_clicked.connect(self.on_stop_server)
        
        # Splitter for sidebar and chat area
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Client sidebar (middle)
        self.sidebar = SidebarClients()
        self.sidebar.client_selected.connect(self.on_client_selected)
        
        # Chat area (right)
        self.chat_window = ChatWindow()
        self.chat_window.message_sent.connect(self.on_message_sent)
        self.chat_window.disconnect_client.connect(self.on_disconnect_client)
        
        # Add widgets to splitter
        splitter.addWidget(self.sidebar)
        splitter.addWidget(self.chat_window)
        splitter.setSizes([300, 700])  # Initial sizes
        
        # Assemble content layout
        content_layout.addWidget(self.control_panel)
        content_layout.addWidget(splitter)
        content_widget.setLayout(content_layout)
        
        main_layout.addWidget(content_widget)
        central_widget.setLayout(main_layout)
        
        # Apply styles
        self.setStyleSheet(Styles.MAIN_WINDOW)
        
        # Demo data (remove in production)
        self.setup_demo_data()
    
    def setup_demo_data(self):
        """Setup demo data for testing UI."""
        # Add some demo clients
        demo_clients = [
            {
                'identifier': '192.168.1.10:54321',
                'name': 'Client #1',
                'ip': '192.168.1.10',
                'port': 54321,
                'connected_at': 1234567890,
                'last_activity': 1234567890
            },
            {
                'identifier': '192.168.1.11:54322', 
                'name': 'Client #2',
                'ip': '192.168.1.11',
                'port': 54322,
                'connected_at': 1234567890,
                'last_activity': 1234567890
            }
        ]
        
        for client in demo_clients:
            self.sidebar.add_client(client)
    
    def on_udp_toggled(self, running: bool):
        """Handle UDP server toggle."""
        print(f"UDP Server {'started' if running else 'stopped'}")
        self.navbar.update_server_status(running)
        
        # TODO: Implement actual UDP server start/stop
        if running:
            # Start UDP server
            pass
        else:
            # Stop UDP server
            pass
    
    def on_stop_server(self):
        """Handle stop server."""
        print("Stopping server")
        self.control_panel.set_server_state(False)
        self.navbar.update_server_status(False)
        
        # TODO: Implement actual server stopping
        # Stop UDP server
    
    def on_client_selected(self, client_info):
        """Handle client selection in sidebar."""
        print(f"Selected client: {client_info['name']}")
        self.chat_window.set_current_client(client_info)
        
        # Only add welcome message if this is a new conversation
        client_id = client_info['identifier']
        if (client_id not in self.chat_window.chat_histories or 
        len(self.chat_window.chat_histories[client_id]) == 0):
            self.chat_window.add_message("Hello! How can I help you?", is_server=True)
            self.chat_window.add_message("Hi, I'm testing the connection.", is_server=False)
    
    def on_message_sent(self, message):
        """Handle message sent from chat window."""
        print(f"Message sent: {message}")
        # TODO: Send message to selected client
    
    def on_disconnect_client(self):
        """Handle client disconnect request."""
        current_client = self.chat_window.current_client
        if current_client:
            print(f"Disconnecting client: {current_client['name']}")
            # TODO: Implement client disconnection
            self.sidebar.remove_client(current_client['identifier'])
            self.chat_window.set_current_client(None)