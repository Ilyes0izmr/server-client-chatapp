from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QScrollArea, QTextEdit, QWidget)
from PyQt6.QtCore import Qt, pyqtSignal
import datetime

class MessageBubble(QFrame):
    """Individual message bubble in chat"""
    
    def __init__(self, message: str, is_server: bool, timestamp: datetime.datetime):
        super().__init__()
        self.message = message
        self.is_server = is_server
        self.timestamp = timestamp
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        # Sender label ------------------------------------------------------------
        sender_label = QLabel("Server" if self.is_server else "Client")
        sender_label.setObjectName("senderLabel")
        sender_label.setAlignment(Qt.AlignmentFlag.AlignRight if self.is_server else Qt.AlignmentFlag.AlignLeft)
        
        # Message bubble ------------------------------------------------------------
        bubble = QFrame()
        bubble.setObjectName("serverBubble" if self.is_server else "clientBubble")
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(12, 8, 12, 8)
        
        message_label = QLabel(self.message)
        message_label.setObjectName("messageText")
        message_label.setWordWrap(True)
        message_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        bubble_layout.addWidget(message_label)
        
        # Timestamp ------------------------------------------------------------
        time_label = QLabel(self.timestamp.strftime("%H:%M:%S"))
        time_label.setObjectName("timestamp")
        time_label.setAlignment(Qt.AlignmentFlag.AlignRight if self.is_server else Qt.AlignmentFlag.AlignLeft)
        
        layout.addWidget(sender_label)
        layout.addWidget(bubble)
        layout.addWidget(time_label)
        
        # Set alignment ------------------------------------------------------------
        if self.is_server:
            layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        else:
            layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            
        self.apply_styles()
        
    def apply_styles(self):
        self.setStyleSheet("""
            #senderLabel {
                color: #888;
                font-size: 12px;
                padding: 2px 8px;
            }
            #serverBubble {
                background-color: #2E7D32;
                border-radius: 12px;
                border-bottom-right-radius: 4px;
            }
            #clientBubble {
                background-color: #1565C0;
                border-radius: 12px;
                border-bottom-left-radius: 4px;
            }
            #messageText {
                color: #FFFFFF;
                font-size: 14px;
                background-color: transparent;
            }
            #timestamp {
                color: #666;
                font-size: 10px;
                padding: 2px 8px;
            }
        """)

class ChatArea(QFrame):
    """Chat area for messaging with selected client"""
    
    send_message = pyqtSignal(str, str)  # client_id, message
    disconnect_client = pyqtSignal(str)  # client_id
    
    def __init__(self):
        super().__init__()
        self.current_client = None
        self.current_client_data = None
        self.messages = []  # Store message history
        self.setup_ui()
        self.apply_styles()
        
    def setup_ui(self):
        self.setObjectName("chatArea")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Chat header ------------------------------------------------------------
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
        
        # Messages area ------------------------------------------------------------
        self.messages_scroll = QScrollArea()
        self.messages_scroll.setObjectName("messagesScroll")
        self.messages_scroll.setWidgetResizable(True)
        self.messages_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.messages_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.messages_widget = QWidget()
        self.messages_widget.setObjectName("messagesWidget")
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setContentsMargins(15, 15, 15, 15)
        self.messages_layout.setSpacing(10)
        self.messages_layout.addStretch()  # Push messages to top
        
        self.messages_scroll.setWidget(self.messages_widget)
        layout.addWidget(self.messages_scroll)
        
        # Input area ------------------------------------------------------------
        input_frame = QFrame()
        input_frame.setObjectName("inputFrame")
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(15, 12, 15, 15)
        
        self.message_input = QTextEdit()
        self.message_input.setObjectName("messageInput")
        self.message_input.setMaximumHeight(80)
        self.message_input.setPlaceholderText("Type your message... (Enter to send, Shift+Enter for new line)")
        self.message_input.textChanged.connect(self.on_input_changed)
        
        # Override keyPressEvent for Enter key handling
        self.message_input.keyPressEvent = self._create_key_press_handler(self.message_input.keyPressEvent)
        
        input_layout.addWidget(self.message_input)
        
        self.send_btn = QPushButton("Send")
        self.send_btn.setObjectName("sendButton")
        self.send_btn.clicked.connect(self.handle_send_message)
        self.send_btn.setEnabled(False)
        self.send_btn.setFixedWidth(80)
        input_layout.addWidget(self.send_btn)
        
        layout.addWidget(input_frame)
        
        # Set focus policy to ensure the input can receive focus
        self.message_input.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
    def _create_key_press_handler(self, original_key_press_event):
        """Create a custom key press handler that preserves the original functionality"""
        def key_press_handler(event):
            print(f"🔑 DEBUG: Key pressed - key: {event.key()}, modifiers: {event.modifiers()}")
            
            if event.key() == Qt.Key.Key_Return and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                print("🔑 DEBUG: Enter pressed without Shift - sending message")
                self.handle_send_message()
                event.accept()
            else:
                print("🔑 DEBUG: Other key - passing to QTextEdit")
                # Call the original keyPressEvent
                original_key_press_event(event)
                
        return key_press_handler
        
    def apply_styles(self):
        self.setStyleSheet("""
            #chatArea {
                background-color: #0D0D0D;
                border-left: 1px solid #333;
            }
            #chatHeader {
                background-color: #121212;
                border-bottom: 1px solid #333;
                min-height: 50px;
            }
            #chatTitle {
                color: #E0E0E0;
                font-size: 16px;
                font-weight: bold;
                padding: 5px;
            }
            #disconnectButton {
                background-color: #C62828;
                color: #E0E0E0;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 100px;
            }
            #disconnectButton:hover {
                background-color: #D32F2F;
            }
            #disconnectButton:disabled {
                background-color: #424242;
                color: #666;
            }
            #messagesScroll {
                background-color: #0D0D0D;
                border: none;
                min-height: 400px;
            }
            #messagesWidget {
                background-color: #0D0D0D;
            }
            #inputFrame {
                background-color: #121212;
                border-top: 1px solid #333;
                min-height: 100px;
            }
            #messageInput {
                background-color: #1A1A1A;
                color: #E0E0E0;
                border: 1px solid #333;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                min-height: 60px;
                selection-background-color: #2E7D32;
            }
            #messageInput:focus {
                border: 1px solid #2E7D32;
            }
            #sendButton {
                background-color: #2E7D32;
                color: #E0E0E0;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
                min-width: 80px;
            }
            #sendButton:disabled {
                background-color: #424242;
                color: #666;
            }
            #sendButton:hover:enabled {
                background-color: #388E3C;
            }
            #sendButton:pressed {
                background-color: #1B5E20;
            }
        """)
        
    def on_input_changed(self):
        """Enable send button when there's text"""
        has_text = bool(self.message_input.toPlainText().strip())
        print(f"📝 DEBUG: Input changed - has text: {has_text}, current client: {self.current_client}")
        self.send_btn.setEnabled(has_text and self.current_client is not None)
        
    def handle_send_message(self):
        """Send message to current client"""
        print(f"📤 DEBUG: Send button clicked")
        print(f"📤 DEBUG: Current client: {self.current_client}")
        print(f"📤 DEBUG: Button enabled: {self.send_btn.isEnabled()}")
        print(f"📤 DEBUG: Input text: '{self.message_input.toPlainText()}'")
        
        if not self.current_client:
            print("❌ DEBUG: No client selected, cannot send")
            return
            
        message = self.message_input.toPlainText().strip()
        if not message:
            print("❌ DEBUG: No message text, cannot send")
            return
            
        print(f"📤 DEBUG: Sending message: '{message}' to {self.current_client}")
        
        # Add message to chat immediately for visual feedback
        self.add_message(message, is_server=True)
        
        # Emit signal to send to server
        self.send_message.emit(self.current_client, message)
        print(f"📤 DEBUG: Signal emitted to server")
        
        # Clear input and reset button state
        self.message_input.clear()
        self.send_btn.setEnabled(False)
        print("📤 DEBUG: Message sent and input cleared")
        
    def handle_disconnect(self):
        """Disconnect current client"""
        if self.current_client:
            print(f"🔌 DEBUG: Disconnecting client: {self.current_client}")
            self.disconnect_client.emit(self.current_client)
            
    def set_current_client(self, client_id: str, client_data: dict):
        """Set the current client for chatting"""
        print(f"💬 DEBUG: Setting current client: {client_id}")
        
        self.current_client = client_id
        self.current_client_data = client_data
        self.disconnect_btn.setEnabled(True)
        
        # Update title
        username = client_data.get('username', client_id)
        protocol = client_data.get('protocol', 'Unknown')
        self.chat_title.setText(f"Chat with {username} ({protocol})")
        print(f"💬 DEBUG: Chat title set to: {self.chat_title.text()}")
        
        # Clear previous messages and load chat history
        self.clear_messages()
        
        # Add a welcome message to verify chat is working
        welcome_msg = f"Chat started with {username}. Send a message!"
        self.add_message(welcome_msg, is_server=True)
        
        # Set focus to message input
        self.message_input.setFocus()
        print(f"💬 DEBUG: Focus set to message input")
        
        # Load any existing chat history
        self.load_chat_history(client_id)
        print(f"💬 DEBUG: Chat history loaded for: {client_id}")
            
    def clear_current_client(self):
        """Clear current client selection"""
        self.current_client = None
        self.current_client_data = None
        self.disconnect_btn.setEnabled(False)
        self.chat_title.setText("Select a client to chat")
        self.clear_messages()
        self.message_input.clear()
        self.send_btn.setEnabled(False)
        
    def add_message(self, message: str, is_server: bool = False):
        """Add a message to the chat"""
        timestamp = datetime.datetime.now()
        bubble = MessageBubble(message, is_server, timestamp)
        
        # Store message in history
        self.messages.append({
            'text': message,
            'is_server': is_server,
            'timestamp': timestamp,
            'client_id': self.current_client
        })
        
        # Add to layout (before the stretch)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, bubble)
        
        # Auto-scroll to bottom
        self.scroll_to_bottom()
        print(f"💬 DEBUG: Message added to chat - {'Server' if is_server else 'Client'}: {message}")
        
    def add_client_message(self, client_id: str, message: str):
        """Add a message received from a client"""
        print(f"📨 DEBUG: Adding client message from {client_id}: '{message}'")
        print(f"📨 DEBUG: Current chat client: {self.current_client}")
        
        if client_id == self.current_client:
            self.add_message(message, is_server=False)
            print(f"📨 DEBUG: Message displayed in chat area")
        else:
            print(f"📨 DEBUG: Message not displayed - different client")
        
    def load_chat_history(self, client_id: str):
        """Load chat history for client"""
        # Filter messages for this client
        client_messages = [msg for msg in self.messages if msg['client_id'] == client_id]
        
        for msg in client_messages:
            bubble = MessageBubble(msg['text'], msg['is_server'], msg['timestamp'])
            self.messages_layout.insertWidget(self.messages_layout.count() - 1, bubble)
            
        self.scroll_to_bottom()
        
    def clear_messages(self):
        """Clear all messages from chat"""
        for i in reversed(range(self.messages_layout.count() - 1)):
            item = self.messages_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater() 
                
    def scroll_to_bottom(self):
        """Scroll messages area to bottom"""
        scrollbar = self.messages_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def test_chat_interaction(self):
        """Test method to verify chat area is working"""
        print("🧪 TEST: Testing chat area interaction...")
        
        # Test 1: Check if message input exists and is visible
        print(f"🧪 TEST: Message input exists: {self.message_input is not None}")
        print(f"🧪 TEST: Message input is visible: {self.message_input.isVisible()}")
        print(f"🧪 TEST: Message input is enabled: {self.message_input.isEnabled()}")
        
        # Test 2: Check if send button exists and is connected
        print(f"🧪 TEST: Send button exists: {self.send_btn is not None}")
        print(f"🧪 TEST: Send button is visible: {self.send_btn.isVisible()}")
        print(f"🧪 TEST: Send button is enabled: {self.send_btn.isEnabled()}")
        
        # Test 3: Manually set a client for testing
        test_client_id = "127.0.0.1:12345"
        test_client_data = {'username': 'TestUser', 'protocol': 'TCP', 'address': ('127.0.0.1', 12345)}
        self.set_current_client(test_client_id, test_client_data)
        
        # Test 4: Try to type in the input
        self.message_input.setPlainText("Test message")
        print(f"🧪 TEST: Input text set to: '{self.message_input.toPlainText()}'")
        print(f"🧪 TEST: Send button enabled after text: {self.send_btn.isEnabled()}")
        
        # Clear the test
        self.message_input.clear()
        self.clear_current_client()