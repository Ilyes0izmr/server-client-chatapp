"""
Main chat area for displaying and sending messages.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QScrollArea, QTextEdit, QPushButton, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from datetime import datetime
import time
from .styles import Styles


class MessageBubble(QWidget):
    """Widget representing a single message bubble."""
    
    def __init__(self, message, is_server=True, timestamp=None):
        super().__init__()
        self.message = message
        self.is_server = is_server
        self.timestamp = timestamp or time.time()
        self.init_ui()
        
    def init_ui(self):
        """Initialize message bubble UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Sender label
        sender_label = QLabel("Server" if self.is_server else "Client")
        sender_label.setStyleSheet(f"""
            QLabel {{
                color: {'#90CAF9' if self.is_server else Styles.TEXT_SECONDARY};
                font-size: 11px;
                font-weight: bold;
                padding: 0px 4px;
            }}
        """)
        sender_label.setAlignment(Qt.AlignmentFlag.AlignRight if self.is_server else Qt.AlignmentFlag.AlignLeft)
        
        # Message content - FIXED: Allow full message display
        message_label = QLabel(self.message)
        message_label.setWordWrap(True)
        message_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        message_label.setStyleSheet(f"""
            QLabel {{
                color: {Styles.TEXT_PRIMARY};
                font-size: 14px;
                font-family: "Segoe UI", "Arial", sans-serif;
                padding: 12px 16px;
                background-color: transparent;
                line-height: 1.4;
            }}
        """)
        
        # Timestamp
        time_str = datetime.fromtimestamp(self.timestamp).strftime("%H:%M:%S")
        time_label = QLabel(time_str)
        time_label.setStyleSheet(f"""
            QLabel {{
                color: {Styles.TEXT_MUTED};
                font-size: 10px;
                padding: 0px 4px 4px 4px;
            }}
        """)
        time_label.setAlignment(Qt.AlignmentFlag.AlignRight if self.is_server else Qt.AlignmentFlag.AlignLeft)
        
        # Message bubble container
        bubble_widget = QWidget()
        bubble_layout = QVBoxLayout()
        bubble_layout.setContentsMargins(0, 0, 0, 0)
        bubble_layout.setSpacing(2)
        bubble_layout.addWidget(message_label)
        bubble_layout.addWidget(time_label)
        bubble_widget.setLayout(bubble_layout)
        
        # Set bubble style based on sender
        if self.is_server:
            bubble_widget.setStyleSheet(Styles.MESSAGE_BUBBLE_SERVER)
            layout.addWidget(sender_label)
            layout.addWidget(bubble_widget)
            layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        else:
            bubble_widget.setStyleSheet(Styles.MESSAGE_BUBBLE_CLIENT)
            layout.addWidget(sender_label)
            layout.addWidget(bubble_widget)
            layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.setLayout(layout)
        
        # Set minimum width to ensure messages are readable
        self.setMinimumWidth(200)


class ChatWindow(QWidget):
    """Main chat area for server-client communication."""
    
    message_sent = pyqtSignal(str)  # Emits message content
    disconnect_client = pyqtSignal()  # Emits disconnect request
    
    def __init__(self):
        super().__init__()
        self.current_client = None
        self.chat_histories = {}  # Store chat history per client
        self.init_ui()
        
    def init_ui(self):
        """Initialize chat window UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        self.header_widget = QWidget()
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(16, 12, 16, 12)
        
        self.client_label = QLabel("Select a client to chat")
        self.client_label.setStyleSheet(f"""
            QLabel {{
                color: {Styles.TEXT_PRIMARY};
                font-size: 16px;
                font-weight: bold;
            }}
        """)
        
        # Disconnect button - FIXED: Just "X" icon
        self.disconnect_btn = QPushButton("✕")
        self.disconnect_btn.setFixedSize(32, 32)
        self.disconnect_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Styles.BACKGROUND_TERTIARY};
                color: {Styles.TEXT_PRIMARY};
                border: 1px solid {Styles.BORDER_COLOR};
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Styles.ACCENT_RED}40;
                color: {Styles.ACCENT_RED};
                border-color: {Styles.ACCENT_RED};
            }}
            QPushButton:disabled {{
                background-color: {Styles.BACKGROUND_SECONDARY};
                color: {Styles.TEXT_MUTED};
            }}
        """)
        self.disconnect_btn.clicked.connect(self.disconnect_client.emit)
        self.disconnect_btn.setEnabled(False)
        
        header_layout.addWidget(self.client_label)
        header_layout.addStretch()
        header_layout.addWidget(self.disconnect_btn)
        
        self.header_widget.setLayout(header_layout)
        self.header_widget.setStyleSheet(Styles.CHAT_HEADER)
        
        # Messages area
        self.messages_scroll = QScrollArea()
        self.messages_scroll.setWidgetResizable(True)
        self.messages_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.messages_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.messages_scroll.setStyleSheet(Styles.SCROLL_AREA)
        
        self.messages_widget = QWidget()
        self.messages_layout = QVBoxLayout()
        self.messages_layout.setContentsMargins(16, 16, 16, 16)
        self.messages_layout.setSpacing(12)  # Increased spacing between messages
        self.messages_layout.addStretch()
        
        self.messages_widget.setLayout(self.messages_layout)
        self.messages_scroll.setWidget(self.messages_widget)
        
        # Input area
        input_widget = QWidget()
        input_widget.setStyleSheet(Styles.INPUT_AREA)
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(8)
        
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Type a message... (Shift+Enter for new line, Enter to send)")
        self.message_input.setMaximumHeight(100)
        self.message_input.setStyleSheet(Styles.TEXT_EDIT)
        self.message_input.textChanged.connect(self.on_text_changed)
        
        # Install event filter for Enter/Shift+Enter handling
        self.message_input.installEventFilter(self)
        
        self.send_btn = QPushButton("Send")
        self.send_btn.setFixedSize(80, 50)
        self.send_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Styles.ACCENT_GRAY};
                color: {Styles.TEXT_PRIMARY};
                border: 1px solid {Styles.BORDER_COLOR};
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover:enabled {{
                background-color: {Styles.ACCENT_BLUE};
                border-color: {Styles.ACCENT_BLUE};
            }}
            QPushButton:disabled {{
                background-color: {Styles.BACKGROUND_SECONDARY};
                color: {Styles.TEXT_MUTED};
            }}
        """)
        self.send_btn.clicked.connect(self.send_message)
        self.send_btn.setEnabled(False)
        
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_btn)
        
        input_widget.setLayout(input_layout)
        
        # Assemble main layout
        layout.addWidget(self.header_widget)
        layout.addWidget(self.messages_scroll)
        layout.addWidget(input_widget)
        
        self.setLayout(layout)
        self.setStyleSheet(Styles.CHAT_AREA)
    
    def eventFilter(self, obj, event):
        """Handle key events for the message input."""
        if obj == self.message_input and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return:
                if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
                    # Shift+Enter - allow new line (default behavior)
                    return False
                else:
                    # Enter - send message
                    self.send_message()
                    return True  # Event handled
        return super().eventFilter(obj, event)
    
    def on_text_changed(self):
        """Handle text input changes."""
        text = self.message_input.toPlainText().strip()
        self.send_btn.setEnabled(bool(text) and self.current_client is not None)
    
    def send_message(self):
        """Send the current message."""
        text = self.message_input.toPlainText().strip()
        if text and self.current_client:
            # Add to current chat
            self.add_message_to_current_chat(text, is_server=True)
            self.message_sent.emit(text)
            self.message_input.clear()
    
    def add_message_to_current_chat(self, message, is_server=True, timestamp=None):
        """Add a message to the current chat and store in history."""
        if not self.current_client:
            return
            
        # Store message in history
        client_id = self.current_client['identifier']
        if client_id not in self.chat_histories:
            self.chat_histories[client_id] = []
        
        message_data = {
            'message': message,
            'is_server': is_server,
            'timestamp': timestamp or time.time()
        }
        self.chat_histories[client_id].append(message_data)
        
        # Add to UI if this is the current client
        if self.current_client and self.current_client['identifier'] == client_id:
            self.add_message_to_ui(message, is_server, timestamp)
    
    def add_message_to_ui(self, message, is_server=True, timestamp=None):
        """Add a message to the UI only."""
        bubble = MessageBubble(message, is_server, timestamp)
        # Insert before the stretch at the end
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, bubble)
        
        # Scroll to bottom with a slight delay
        QTimer.singleShot(10, self.scroll_to_bottom)
    
    def scroll_to_bottom(self):
        """Scroll messages area to bottom."""
        scrollbar = self.messages_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def set_current_client(self, client_info):
        """Set the currently active client for chatting."""
        # Save current scroll position if switching clients
        if self.current_client:
            self.save_chat_state()
        
        self.current_client = client_info
        if client_info:
            client_name = client_info.get('name', 'Unknown')
            self.client_label.setText(f"Chat with {client_name}")
            self.disconnect_btn.setEnabled(True)
            
            # Load chat history for this client
            self.load_chat_history(client_info['identifier'])
        else:
            self.client_label.setText("Select a client to chat")
            self.disconnect_btn.setEnabled(False)
            self.clear_messages_ui()
    
    def save_chat_state(self):
        """Save the current chat state before switching clients."""
        # Chat history is already stored in self.chat_histories
        pass
    
    def load_chat_history(self, client_id):
        """Load chat history for a client."""
        # Clear current messages
        self.clear_messages_ui()
        
        # Load messages from history
        if client_id in self.chat_histories:
            for msg_data in self.chat_histories[client_id]:
                self.add_message_to_ui(
                    msg_data['message'], 
                    msg_data['is_server'], 
                    msg_data['timestamp']
                )
        else:
            # Add welcome message for new clients
            self.add_message_to_ui("Hello! How can I help you?", is_server=True)
            self.add_message_to_ui("Hi, I'm testing the connection.", is_server=False)
    
    def clear_messages_ui(self):
        """Clear all messages from the chat UI (not history)."""
        for i in reversed(range(self.messages_layout.count())):
            item = self.messages_layout.itemAt(i)
            if item.widget():
                # Keep the stretch widget at the end
                if i == self.messages_layout.count() - 1:
                    continue
                item.widget().setParent(None)
        
        # Ensure stretch remains at the end
        has_stretch = False
        for i in range(self.messages_layout.count()):
            item = self.messages_layout.itemAt(i)
            if item and item.spacerItem():
                has_stretch = True
                break
        
        if not has_stretch:
            self.messages_layout.addStretch()
    
    def add_message(self, message, is_server=True, timestamp=None):
        """Public method to add messages (for external use)."""
        self.add_message_to_current_chat(message, is_server, timestamp)