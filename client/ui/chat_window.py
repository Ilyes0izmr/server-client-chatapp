from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                            QLineEdit, QPushButton, QStatusBar, QMainWindow,
                            QLabel, QFrame)
from PyQt6.QtCore import pyqtSignal, Qt, QDateTime
from PyQt6.QtGui import QTextCursor, QFont, QTextCharFormat, QTextCursor
import logging
import time

class ChatWindow(QMainWindow):
    """Main chat interface window with black monochrome theme"""
    
    message_sent = pyqtSignal(str)
    disconnected = pyqtSignal()
    
    def __init__(self, username, host, port, protocol):
        super().__init__()
        self.username = username
        self.host = host
        self.port = port
        self.protocol = protocol
        self.logger = logging.getLogger(__name__)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle(f"Chat Client - {self.username} | {self.host}:{self.port} ({self.protocol})")
        self.setGeometry(200, 200, 800, 600)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        central_widget.setLayout(layout)
        
        # Header
        header_frame = QFrame()
        header_layout = QHBoxLayout()
        header_frame.setLayout(header_layout)
        
        connection_info = QLabel(f"Connected to {self.host}:{self.port} via {self.protocol}")
        connection_info.setStyleSheet("color: #999; font-size: 12px;")
        header_layout.addWidget(connection_info)
        
        header_layout.addStretch()
        
        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.setProperty("class", "disconnect-button")
        self.disconnect_button.clicked.connect(self.disconnect)
        header_layout.addWidget(self.disconnect_button)
        
        layout.addWidget(header_frame)
        
        # Chat display area
        self.chat_display = QTextEdit()
        self.chat_display.setObjectName("chatDisplay")
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Consolas", 11))
        layout.addWidget(self.chat_display)
        
        # Message input area
        input_frame = QFrame()
        input_layout = QHBoxLayout()
        input_frame.setLayout(input_layout)
        
        self.message_input = QTextEdit()
        self.message_input.setMaximumHeight(80)
        self.message_input.setPlaceholderText("Type your message here... (Press Ctrl+Enter to send)")
        self.message_input.textChanged.connect(self.on_text_changed)
        input_layout.addWidget(self.message_input)
        
        self.send_button = QPushButton("Send")
        self.send_button.setMinimumHeight(80)
        self.send_button.setEnabled(False)
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)
        
        layout.addWidget(input_frame)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status("Connected", True)
    
    def on_text_changed(self):
        """Enable/disable send button based on input"""
        has_text = bool(self.message_input.toPlainText().strip())
        self.send_button.setEnabled(has_text)
    
    def send_message(self):
        """Send message to server"""
        message = self.message_input.toPlainText().strip()
        if message:
            self.message_sent.emit(message)
            self.message_input.clear()
            self.send_button.setEnabled(False)
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.send_message()
            event.accept()
        else:
            super().keyPressEvent(event)
    
    def add_message(self, message: str, is_own: bool = False, is_system: bool = False):
        """Add message to chat display with proper formatting"""
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")
        
        # Move cursor to end
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # Prepare HTML based on message type
        if is_system:
            html = f'''
            <div class="system-message">
                {message}
                <br><span style="color: #666; font-size: 10px;">[{timestamp}]</span>
            </div>
            '''
        elif is_own:
            html = f'''
            <div class="client-message">
                <div style="font-weight: bold; color: #E0E0E0;">You</div>
                <div style="margin: 4px 0;">{message}</div>
                <div style="color: #666; font-size: 10px; text-align: right;">[{timestamp}]</div>
            </div>
            '''
        else:
            # Server or other user message
            if ":" in message:
                parts = message.split(":", 1)
                sender = parts[0].strip()
                content = parts[1].strip()
                html = f'''
                <div class="server-message">
                    <div style="font-weight: bold; color: #E0E0E0;">{sender}</div>
                    <div style="margin: 4px 0;">{content}</div>
                    <div style="color: #666; font-size: 10px;">[{timestamp}]</div>
                </div>
                '''
            else:
                html = f'''
                <div class="server-message">
                    <div style="margin: 4px 0;">{message}</div>
                    <div style="color: #666; font-size: 10px;">[{timestamp}]</div>
                </div>
                '''
        
        # Insert HTML
        self.chat_display.append(html)
        
        # Scroll to bottom
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def update_status(self, message: str, is_connected: bool = None):
        """Update status bar message"""
        if is_connected is not None:
            status = "🟢 Connected" if is_connected else "🔴 Disconnected"
            self.status_bar.showMessage(f"{status} | {message}")
        else:
            self.status_bar.showMessage(message)
    
    def disconnect(self):
        """Handle disconnect"""
        self.disconnected.emit()
        self.close()
    
    def closeEvent(self, event):
        """Handle window close event"""
        self.disconnected.emit()
        event.accept()