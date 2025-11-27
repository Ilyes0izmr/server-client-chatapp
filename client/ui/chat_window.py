from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, 
                            QHBoxLayout, QLineEdit, QPushButton, QLabel)
from PyQt6.QtCore import Qt, pyqtSignal

class ChatWindow(QWidget):
    send_message_signal = pyqtSignal(str)
    
    def __init__(self, client_socket):
        super().__init__()
        self.client_socket = client_socket
        self.setup_ui()
        
        # Connect socket callback
        self.client_socket.on_message_received = self.handle_incoming_message
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Status bar
        self.status_label = QLabel("Connected to server")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #00b894;
                font-weight: bold;
                padding: 5px;
                background-color: #2b2b2b;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.status_label)
        
        # Chat display area
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #404040;
                border-radius: 5px;
                padding: 10px;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.chat_display)
        
        # Input area
        input_layout = QHBoxLayout()
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message...")
        self.message_input.setStyleSheet("""
            QLineEdit {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #404040;
                border-radius: 5px;
                padding: 8px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #00b894;
            }
        """)
        self.message_input.setFixedHeight(35)
        self.message_input.returnPressed.connect(self.send_message)
        
        self.send_btn = QPushButton("Send")
        self.send_btn.setFixedSize(80, 35)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #00b894;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #00a085;
            }
        """)
        self.send_btn.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_btn)
        layout.addLayout(input_layout)
        
        # Add welcome message
        self.add_message("System", "Welcome to the chat! Start typing to send messages.")
    
    def send_message(self):
        message = self.message_input.text().strip()
        if message and self.client_socket.is_connected:
            # Send to server
            self.client_socket.send_message(message)
            # Display in chat
            self.add_message("You", message)
            self.message_input.clear()
    
    def handle_incoming_message(self, message_data):
        """Handle incoming messages from server"""
        sender = message_data.get("sender", "Unknown")
        content = message_data.get("content", "")
        
        if message_data.get("type") == "message":
            self.add_message(sender, content)
    
    def add_message(self, sender: str, message: str):
        """Add message to chat display"""
        if sender == "You":
            formatted_message = f'<div style="color: #00b894; margin: 5px 0;"><b>You:</b> {message}</div>'
        else:
            formatted_message = f'<div style="color: #74b9ff; margin: 5px 0;"><b>{sender}:</b> {message}</div>'
        
        self.chat_display.append(formatted_message)
        # Auto-scroll to bottom
        self.chat_display.verticalScrollBar().setValue(
            self.chat_display.verticalScrollBar().maximum()
        )
    
    def update_status(self, connected: bool, status_text: str = ""):
        """Update connection status"""
        if connected:
            self.status_label.setText(f"🟢 {status_text}")
            self.status_label.setStyleSheet("color: #00b894; font-weight: bold; padding: 5px; background-color: #2b2b2b;")
        else:
            self.status_label.setText("🔴 Disconnected")
            self.status_label.setStyleSheet("color: #e17055; font-weight: bold; padding: 5px; background-color: #2b2b2b;")