from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QScrollArea, QTextEdit, QWidget)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QKeyEvent
import qtawesome as qta
import datetime


class MessageBubble(QFrame):
    def __init__(self, message: str, is_server: bool, timestamp: datetime.datetime):
        super().__init__()
        self.message = message
        self.is_server = is_server
        self.timestamp = timestamp
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(2)
        
        # Sender label
        sender_label = QLabel("Server" if self.is_server else "Client")
        sender_label.setObjectName("senderLabel")
        sender_label.setAlignment(Qt.AlignmentFlag.AlignRight if self.is_server else Qt.AlignmentFlag.AlignLeft)
        
        # Message bubble
        bubble = QFrame()
        bubble.setObjectName("serverBubble" if self.is_server else "clientBubble")
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(15, 20, 15, 10)
        
        message_label = QLabel(self.message)
        message_label.setObjectName("messageText")
        message_label.setWordWrap(True)
        message_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        bubble_layout.addWidget(message_label)
        
        # Timestamp
        time_label = QLabel(self.timestamp.strftime("%H:%M:%S"))
        time_label.setObjectName("timestamp")
        time_label.setAlignment(Qt.AlignmentFlag.AlignRight if self.is_server else Qt.AlignmentFlag.AlignLeft)
        
        layout.addWidget(sender_label)
        layout.addWidget(bubble)
        layout.addWidget(time_label)
        
        if self.is_server:
            layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        else:
            layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            
        self.apply_styles()
        
    def apply_styles(self):
        self.setStyleSheet("""
            #senderLabel {
                color: #8a9cb5;
                font-size: 12px;
                padding: 2px 10px;
            }
            #serverBubble {
                background-color: #00dcff;
                border-radius: 14px;
                border-bottom-right-radius: 6px;
            }
            #clientBubble {
                background-color: #64b5f6;
                border-radius: 14px;
                border-bottom-left-radius: 6px;
            }
            #messageText {
                color: #0c121c;
                font-size: 14px;
                font-weight: 500;
                background-color: transparent;
            }
            #timestamp {
                color: #6c7a94;
                font-size: 11px;
                padding: 2px 10px;
            }
        """)


class ChatArea(QFrame):
    send_message = pyqtSignal(str, str)  # client_id, message
    disconnect_client = pyqtSignal(str)   # client_id
    
    def __init__(self):
        super().__init__()
        self.current_client = None
        self.current_client_data = None
        self.messages = []
        self.setup_ui()
        self.apply_styles()
        
    def setup_ui(self):
        self.setObjectName("chatArea")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Chat header
        header_frame = QFrame()
        header_frame.setObjectName("chatHeader")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 12, 20, 12)
        
        self.chat_title = QLabel("Select a client to chat")
        self.chat_title.setObjectName("chatTitle")
        header_layout.addWidget(self.chat_title)
        header_layout.addStretch()
        
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.setObjectName("disconnectButton")
        self.disconnect_btn.clicked.connect(self.handle_disconnect)
        self.disconnect_btn.setEnabled(False)
        header_layout.addWidget(self.disconnect_btn)
        
        layout.addWidget(header_frame)
        
        # Messages area — now expands to fill available space
        self.messages_scroll = QScrollArea()
        self.messages_scroll.setObjectName("messagesScroll")
        self.messages_scroll.setWidgetResizable(True)
        self.messages_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.messages_widget = QWidget()
        self.messages_widget.setObjectName("messagesWidget")
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setContentsMargins(20, 16, 20, 16)
        self.messages_layout.setSpacing(12)
        self.messages_layout.addStretch()
        
        self.messages_scroll.setWidget(self.messages_widget)
        layout.addWidget(self.messages_scroll, 1)  # ✅ stretch factor = 1
        
        # Input area — COMPACT (60px), with hover-enhanced send button
        input_container = QWidget()
        input_container.setObjectName("inputContainer")
        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(20, 6, 20, 12)
        input_layout.setSpacing(4)
        
        # Input row: message input + send button
        input_row = QHBoxLayout()
        input_row.setSpacing(10)
        
        self.message_input = QTextEdit()
        self.message_input.setObjectName("messageInput")
        self.message_input.setMaximumHeight(36)  # Compact
        self.message_input.setPlaceholderText("")
        self.message_input.textChanged.connect(self.on_input_changed)
        self.message_input.keyPressEvent = self._create_key_press_handler(self.message_input.keyPressEvent)
        input_row.addWidget(self.message_input)
        
        # Send button — icon only, with hover glow
        self.send_btn = QPushButton()
        self.send_btn.setObjectName("sendButton")
        self.send_btn.setIcon(qta.icon("fa5s.paper-plane", color="#0c121c", scale_factor=1.0))
        self.send_btn.setIconSize(QSize(16, 16))
        self.send_btn.setFixedSize(36, 36)
        self.send_btn.clicked.connect(self.handle_send_message)
        self.send_btn.setEnabled(False)
        input_row.addWidget(self.send_btn)
        
        input_layout.addLayout(input_row)
        
        # Hint label — concise
        self.hint_label = QLabel("⏎ send • ⇧⏎ new line")
        self.hint_label.setObjectName("hintLabel")
        input_layout.addWidget(self.hint_label)
        
        layout.addWidget(input_container)
        self.message_input.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
    def _create_key_press_handler(self, original_key_press_event):
        def key_press_handler(event):
            if event.key() == Qt.Key.Key_Return and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.handle_send_message()
                event.accept()
            else:
                original_key_press_event(event)
        return key_press_handler
        
    def apply_styles(self):
        self.setStyleSheet("""
            #chatArea {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0c121c,
                    stop:1 #0f1522
                );
                border-left: 1px solid #1e2a3a;
            }
            #chatHeader {
                background: rgba(15, 21, 34, 0.7);
                border-bottom: 1px solid #1e2a3a;
                min-height: 57px;
            }
            #chatTitle {
                color: #c5d9fd;
                font-size: 16px;
                font-weight: 600;
            }
            #disconnectButton {
                background-color: #ff5252;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: 600;
                font-size: 12px;
            }
            #disconnectButton:hover {
                background-color: #ff6b6b;
            }
            #disconnectButton:disabled {
                background-color: #3a455a;
                color: #6c7a94;
            }
            #messagesScroll {
                background: transparent;
                border: none;
            }
            #messagesWidget {
                background: transparent;
            }
            #inputContainer {
                background: rgba(15, 21, 34, 0.7);
                border-top: 1px solid #1e2a3a;
                min-height: 60px;
            }
            #messageInput {
                background-color: #0a101a;
                color: #c5d9fd;
                border: 1px solid #1e2a3a;
                border-radius: 18px;
                padding: 6px 12px;
                font-size: 14px;
                selection-background-color: rgba(0, 220, 255, 0.4);
                selection-color: #0c121c;
            }
            #messageInput:focus {
                border: 1px solid #00dcff;
                background-color: #0b111d;
            }
            #sendButton {
                background-color: #00dcff;
                border: none;
                border-radius: 18px;
                padding: 0;
            }
            #sendButton:disabled {
                background-color: #3a455a;
            }
            /* ✅ HOVER: subtle glow & brighten */
            #sendButton:hover:enabled {
                background-color: rgba(51, 238, 255, 0.9);
                box-shadow: 0 0 0 2px rgba(0, 220, 255, 0.2);
            }
            #sendButton:pressed {
                background-color: #00c0e0;
                box-shadow: 0 0 0 2px rgba(0, 220, 255, 0.3);
            }
            #hintLabel {
                color: #6c7a94;
                font-size: 10px;
                padding-left: 4px;
                margin-top: 2px;
            }
        """)
        
    # ─── Handlers & Logic ───────────────────────────────────────────────────────
    def on_input_changed(self):
        has_text = bool(self.message_input.toPlainText().strip())
        self.send_btn.setEnabled(has_text and self.current_client is not None)
        
    def handle_send_message(self):
        if not self.current_client:
            return
        message = self.message_input.toPlainText().strip()
        if not message:
            return
        self.add_message(message, is_server=True)
        self.send_message.emit(self.current_client, message)
        self.message_input.clear()
        self.send_btn.setEnabled(False)
        
    def handle_disconnect(self):
        if self.current_client:
            self.disconnect_client.emit(self.current_client)
            
    def set_current_client(self, client_id: str, client_data: dict):
        self.current_client = client_id
        self.current_client_data = client_data
        self.disconnect_btn.setEnabled(True)
        username = client_data.get('username', client_id)
        protocol = client_data.get('protocol', 'Unknown')
        self.chat_title.setText(f"Chat with {username} ({protocol})")
        self.clear_messages()
        self.add_message(f"Chat started with {username}.", is_server=True)
        self.message_input.setFocus()
        self.load_chat_history(client_id)
            
    def clear_current_client(self):
        self.current_client = None
        self.current_client_data = None
        self.disconnect_btn.setEnabled(False)
        self.chat_title.setText("Select a client to chat")
        self.clear_messages()
        self.message_input.clear()
        self.send_btn.setEnabled(False)
        
    def add_message(self, message: str, is_server: bool = False):
        timestamp = datetime.datetime.now()
        bubble = MessageBubble(message, is_server, timestamp)
        self.messages.append({
            'text': message,
            'is_server': is_server,
            'timestamp': timestamp,
            'client_id': self.current_client
        })
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, bubble)
        self.scroll_to_bottom()
        
    def add_client_message(self, client_id: str, message: str):
        if client_id == self.current_client:
            self.add_message(message, is_server=False)
        
    def load_chat_history(self, client_id: str):
        client_messages = [msg for msg in self.messages if msg['client_id'] == client_id]
        for msg in client_messages:
            bubble = MessageBubble(msg['text'], msg['is_server'], msg['timestamp'])
            self.messages_layout.insertWidget(self.messages_layout.count() - 1, bubble)
        self.scroll_to_bottom()
        
    def clear_messages(self):
        for i in reversed(range(self.messages_layout.count() - 1)):
            widget = self.messages_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
                
    def scroll_to_bottom(self):
        scrollbar = self.messages_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())