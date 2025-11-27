from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, 
                            QHBoxLayout, QLineEdit, QPushButton, QLabel, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal

class ChatArea(QWidget):
    send_message_signal = pyqtSignal(object, str)
    
    def __init__(self):
        super().__init__()
        self.current_client = None
        self.chat_histories = {}
        self.setup_ui()
    
    def setup_ui(self):
        self.setStyleSheet("background-color: #1a1a1a;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        self.header_frame = QFrame()
        self.header_frame.setFixedHeight(70)
        self.header_frame.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border-bottom: 1px solid #333333;
            }
        """)
        header_layout = QVBoxLayout(self.header_frame)
        header_layout.setContentsMargins(25, 12, 25, 12)
        
        self.client_name_label = QLabel("💬 Select a client to start chatting")
        self.client_name_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-weight: bold;
                font-size: 16px;
                font-family: "Segoe UI", Arial, sans-serif;
            }
        """)
        
        self.client_status_label = QLabel("Click on any connected client from the sidebar")
        self.client_status_label.setStyleSheet("""
            QLabel {
                color: #b2bec3;
                font-size: 12px;
                font-family: "Segoe UI", Arial, sans-serif;
            }
        """)
        
        header_layout.addWidget(self.client_name_label)
        header_layout.addWidget(self.client_status_label)
        layout.addWidget(self.header_frame)
        
        # Chat display area
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #ffffff;
                border: none;
                padding: 20px;
                font-size: 13px;
                font-family: "Segoe UI", Arial, sans-serif;
                line-height: 1.4;
            }
        """)
        layout.addWidget(self.chat_display)
        
        # Input area
        input_frame = QFrame()
        input_frame.setFixedHeight(70)
        input_frame.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border-top: 1px solid #333333;
            }
        """)
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(20, 15, 20, 15)
        input_layout.setSpacing(12)
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message...")
        self.message_input.setStyleSheet("""
            QLineEdit {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 20px;
                padding: 12px 18px;
                font-size: 13px;
                font-family: "Segoe UI", Arial, sans-serif;
            }
            QLineEdit:focus {
                border: 1px solid #74b9ff;
                background-color: #4a4a4a;
            }
            QLineEdit:disabled {
                background-color: #2d3436;
                color: #636e72;
            }
        """)
        self.message_input.returnPressed.connect(self.send_message)
        
        self.send_btn = QPushButton("Send")
        self.send_btn.setFixedSize(80, 45)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #74b9ff;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
                font-family: "Segoe UI", Arial, sans-serif;
            }
            QPushButton:hover {
                background-color: #0984e3;
            }
            QPushButton:disabled {
                background-color: #2d3436;
                color: #636e72;
            }
        """)
        self.send_btn.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_btn)
        layout.addWidget(input_frame)
        
        # Initially disable input
        self.set_chat_enabled(False)
        self.show_welcome_message()
    
    def set_chat_enabled(self, enabled: bool):
        self.message_input.setEnabled(enabled)
        self.send_btn.setEnabled(enabled)
        if enabled:
            self.message_input.setFocus()
    
    def show_welcome_message(self):
        self.chat_display.clear()
        welcome_html = """
        <div style='text-align: center; padding: 80px 40px; color: #636e72; font-family: "Segoe UI", Arial, sans-serif;'>
            <div style='font-size: 48px; margin-bottom: 20px;'>💬</div>
            <h2 style='color: #b2bec3; font-weight: normal; margin-bottom: 15px;'>Server Chat Interface</h2>
            <p style='line-height: 1.6; font-size: 14px;'>
                Select a client from the sidebar to start a conversation<br>
                Monitor all connected clients and communicate individually
            </p>
        </div>
        """
        self.chat_display.setHtml(welcome_html)
    
    def switch_to_client(self, client_handler):
        self.current_client = client_handler
        self.client_name_label.setText(f"💬 Chat with {client_handler.client_name}")
        self.client_status_label.setText(f"Client ID: {client_handler.client_id} • Ready to chat")
        
        client_id = client_handler.client_id
        if client_id not in self.chat_histories:
            self.chat_histories[client_id] = []
            self.add_message("System", f"Chat started with {client_handler.client_name}", is_system=True)
        
        self.display_chat_history(client_id)
        self.set_chat_enabled(True)
    
    def display_chat_history(self, client_id: int):
        self.chat_display.clear()
        for sender, message, is_system in self.chat_histories[client_id]:
            if is_system:
                self.add_message(sender, message, is_system=True, add_to_history=False)
            else:
                self.add_message(sender, message, add_to_history=False)
    
    def add_message(self, sender: str, message: str, is_system: bool = False, add_to_history: bool = True):
        if is_system:
            formatted_message = f'''
            <div style="text-align: center; margin: 20px 0;">
                <span style="color: #636e72; font-style: italic; font-size: 12px; background-color: #2b2b2b; padding: 4px 12px; border-radius: 10px;">
                    {message}
                </span>
            </div>
            '''
        elif sender == "You":
            formatted_message = f'''
            <div style="margin: 15px 0; text-align: right;">
                <div style="display: inline-block; max-width: 70%;">
                    <div style="color: #00b894; font-size: 11px; margin-bottom: 3px; padding-right: 5px;">You</div>
                    <div style="background: linear-gradient(135deg, #00b894, #00a085); color: #ffffff; padding: 10px 15px; border-radius: 18px; border-bottom-right-radius: 5px; word-wrap: break-word;">
                        {message}
                    </div>
                </div>
            </div>
            '''
        else:
            formatted_message = f'''
            <div style="margin: 15px 0; text-align: left;">
                <div style="display: inline-block; max-width: 70%;">
                    <div style="color: #74b9ff; font-size: 11px; margin-bottom: 3px; padding-left: 5px;">{sender}</div>
                    <div style="background-color: #2b2b2b; color: #ffffff; padding: 10px 15px; border-radius: 18px; border-bottom-left-radius: 5px; word-wrap: break-word;">
                        {message}
                    </div>
                </div>
            </div>
            '''
        
        self.chat_display.append(formatted_message)
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        if add_to_history and self.current_client:
            client_id = self.current_client.client_id
            if client_id not in self.chat_histories:
                self.chat_histories[client_id] = []
            self.chat_histories[client_id].append((sender, message, is_system))
    
    def send_message(self):
        if not self.current_client:
            return
            
        message = self.message_input.text().strip()
        if message:
            self.send_message_signal.emit(self.current_client, message)
            self.add_message("You", message)
            self.message_input.clear()
    
    def receive_message(self, client_handler, message: str):
        if self.current_client and self.current_client.client_id == client_handler.client_id:
            self.add_message(client_handler.client_name, message)
        else:
            client_id = client_handler.client_id
            if client_id not in self.chat_histories:
                self.chat_histories[client_id] = []
            self.chat_histories[client_id].append((client_handler.client_name, message, False))