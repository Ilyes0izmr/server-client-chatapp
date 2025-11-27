from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QPushButton, 
                            QLabel, QFrame, QVBoxLayout)  # ADD QVBoxLayout
from PyQt6.QtCore import pyqtSignal, Qt
from server.core.server import TCPServer

class Navbar(QWidget):
    start_signal = pyqtSignal()
    stop_signal = pyqtSignal()
    broadcast_signal = pyqtSignal(str)
    
    def __init__(self, server: TCPServer):
        super().__init__()
        self.server = server
        self.setup_ui()
    
    def setup_ui(self):
        # Navbar container
        self.setFixedHeight(60)
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                border-bottom: 2px solid #333333;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(15)
        
        # Logo/Title
        title = QLabel("💬 CHAT SERVER")
        title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 18px;
                font-weight: bold;
                font-family: "Segoe UI", Arial, sans-serif;
            }
        """)
        title.setFixedWidth(150)
        layout.addWidget(title)
        
        # Server Control Section
        control_frame = QFrame()
        control_frame.setStyleSheet("QFrame { background-color: transparent; }")
        control_layout = QHBoxLayout(control_frame)
        control_layout.setSpacing(10)
        control_layout.setContentsMargins(0, 0, 0, 0)
        
        # Start Button
        self.start_btn = QPushButton("🚀 START SERVER")
        self.start_btn.setFixedSize(140, 35)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #00b894;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
                font-family: "Segoe UI", Arial, sans-serif;
            }
            QPushButton:hover {
                background-color: #00a085;
            }
            QPushButton:disabled {
                background-color: #2d3436;
                color: #636e72;
            }
        """)
        self.start_btn.clicked.connect(self.start_signal.emit)
        control_layout.addWidget(self.start_btn)
        
        # Stop Button
        self.stop_btn = QPushButton("🛑 STOP SERVER")
        self.stop_btn.setFixedSize(140, 35)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #e17055;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
                font-family: "Segoe UI", Arial, sans-serif;
            }
            QPushButton:hover {
                background-color: #d63031;
            }
            QPushButton:disabled {
                background-color: #2d3436;
                color: #636e72;
            }
        """)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_signal.emit)
        control_layout.addWidget(self.stop_btn)
        
        layout.addWidget(control_frame)
        
        # Status Section
        status_frame = QFrame()
        status_frame.setStyleSheet("QFrame { background-color: transparent; }")
        status_layout = QVBoxLayout(status_frame)
        status_layout.setSpacing(2)
        status_layout.setContentsMargins(0, 0, 0, 0)
        
        self.status_label = QLabel("🔴 SERVER OFFLINE")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #e17055;
                font-weight: bold;
                font-size: 12px;
                font-family: "Segoe UI", Arial, sans-serif;
            }
        """)
        
        self.clients_label = QLabel("No clients connected")
        self.clients_label.setStyleSheet("""
            QLabel {
                color: #b2bec3;
                font-size: 11px;
                font-family: "Segoe UI", Arial, sans-serif;
            }
        """)
        
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.clients_label)
        layout.addWidget(status_frame)
        
        layout.addStretch()
    
    def update_status(self, is_running: bool, port: int = 5000, client_count: int = 0):
        if is_running:
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.status_label.setText(f"🟢 SERVER RUNNING • PORT {port}")
            self.status_label.setStyleSheet("color: #00b894; font-weight: bold; font-size: 12px;")
            self.clients_label.setText(f"📊 {client_count} client(s) connected")
        else:
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.status_label.setText("🔴 SERVER OFFLINE")
            self.status_label.setStyleSheet("color: #e17055; font-weight: bold; font-size: 12px;")
            self.clients_label.setText("No clients connected")