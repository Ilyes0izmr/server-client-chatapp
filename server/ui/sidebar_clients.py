from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QScrollArea, 
                            QLabel, QPushButton, QFrame, QHBoxLayout)
from PyQt6.QtCore import Qt, pyqtSignal

class ClientWidget(QFrame):
    chat_signal = pyqtSignal(object)
    kick_signal = pyqtSignal(object)
    
    def __init__(self, client_handler):
        super().__init__()
        self.client_handler = client_handler
        self.setup_ui()
    
    def setup_ui(self):
        self.setFixedHeight(50)
        self.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border: 1px solid #333333;
                border-radius: 8px;
                margin: 3px 5px;
            }
            QFrame:hover {
                background-color: #333333;
                border: 1px solid #555555;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)
        
        # Client avatar/icon
        avatar = QLabel("👤")
        avatar.setStyleSheet("color: #74b9ff; font-size: 14px;")
        avatar.setFixedSize(20, 20)
        layout.addWidget(avatar)
        
        # Client info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        info_layout.setContentsMargins(0, 0, 0, 0)
        
        name_label = QLabel(self.client_handler.client_name)
        name_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-weight: bold;
                font-size: 12px;
                font-family: "Segoe UI", Arial, sans-serif;
            }
        """)
        
        id_label = QLabel(f"ID: {self.client_handler.client_id}")
        id_label.setStyleSheet("""
            QLabel {
                color: #b2bec3;
                font-size: 10px;
                font-family: "Segoe UI", Arial, sans-serif;
            }
        """)
        
        info_layout.addWidget(name_label)
        info_layout.addWidget(id_label)
        layout.addLayout(info_layout)
        
        layout.addStretch()
        
        # Kick button
        kick_btn = QPushButton("⨯")
        kick_btn.setFixedSize(24, 24)
        kick_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #636e72;
                border: 1px solid #636e72;
                border-radius: 4px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e17055;
                color: #ffffff;
                border: 1px solid #e17055;
            }
        """)
        kick_btn.setToolTip("Disconnect client")
        kick_btn.clicked.connect(lambda: self.kick_signal.emit(self.client_handler))
        layout.addWidget(kick_btn)
        
        # Make entire widget clickable
        self.mousePressEvent = lambda e: self.chat_signal.emit(self.client_handler)

class SidebarClients(QWidget):
    chat_signal = pyqtSignal(object)
    kick_signal = pyqtSignal(object)
    
    def __init__(self):
        super().__init__()
        self.clients = {}
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setFixedHeight(50)
        header.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border-bottom: 1px solid #333333;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(15, 0, 15, 0)
        
        title = QLabel("CONNECTED CLIENTS")
        title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
                font-family: "Segoe UI", Arial, sans-serif;
            }
        """)
        header_layout.addWidget(title)
        
        layout.addWidget(header)
        
        # Scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #1a1a1a;
            }
            QScrollBar:vertical {
                background-color: #2b2b2b;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #555555;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #777777;
            }
        """)
        
        self.clients_widget = QWidget()
        self.clients_widget.setStyleSheet("background-color: #1a1a1a;")
        self.clients_layout = QVBoxLayout(self.clients_widget)
        self.clients_layout.setSpacing(5)
        self.clients_layout.setContentsMargins(5, 10, 5, 10)
        self.clients_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll_area.setWidget(self.clients_widget)
        layout.addWidget(self.scroll_area)
        
        # Empty state
        self.empty_label = QLabel("No clients connected\n\nClients will appear here\nwhen they connect to the server")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("""
            QLabel {
                color: #636e72;
                font-size: 12px;
                font-family: "Segoe UI", Arial, sans-serif;
                padding: 40px 20px;
                background-color: transparent;
            }
        """)
        self.clients_layout.addWidget(self.empty_label)
    
    def add_client(self, client_handler):
        """Add client to sidebar"""
        # Remove empty state if it's the first client
        if self.empty_label.parent():
            self.empty_label.setParent(None)
        
        client_widget = ClientWidget(client_handler)
        client_widget.chat_signal.connect(self.chat_signal.emit)
        client_widget.kick_signal.connect(self.kick_signal.emit)
        
        self.clients[client_handler.client_id] = client_widget
        self.clients_layout.addWidget(client_widget)
    
    def remove_client(self, client_handler):
        """Remove client from sidebar"""
        client_widget = self.clients.get(client_handler.client_id)
        if client_widget:
            client_widget.deleteLater()
            del self.clients[client_handler.client_id]
        
        # Show empty state if no clients left
        if not self.clients:
            self.clients_layout.addWidget(self.empty_label)
    
    def clear_clients(self):
        """Clear all clients"""
        for client_widget in self.clients.values():
            client_widget.deleteLater()
        self.clients.clear()
        
        # Show empty state
        if not self.empty_label.parent():
            self.clients_layout.addWidget(self.empty_label)