import sys
import os
import logging
# Fix imports - add the current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer
from ui.connect_window import ConnectWindow
from ui.chat_window import ChatWindow
from core.tcp_client import TCPClient
from core.udp_client import UDPClient
from core.message_protocol import ChatMessage
from core.message_protocol import ChatMessage, MessageType
from config import ClientConfig
from utils.logger import setup_logging

class ChatClient:
    """Main chat client application"""
    
    def __init__(self):
        setup_logging()
        self.logger = logging.getLogger(__name__)
        self.client = None
        self.username = None
        self.protocol = None
        
        # UI components
        self.app = QApplication(sys.argv)
        
        # Load styles from CSS file
        styles_path = os.path.join(current_dir, 'ui', 'styles.css')
        if os.path.exists(styles_path):
            try:
                with open(styles_path, 'r') as f:
                    self.app.setStyleSheet(f.read())
            except Exception as e:
                self.logger.warning(f"Could not load styles: {e}")
        
        self.connect_window = ConnectWindow()
        self.chat_window = None
        
        # Connect signals
        self.connect_window.connected.connect(self.handle_connect)
    
    def run(self):
        """Start the client application"""
        self.connect_window.show()
        return self.app.exec()
    
    def handle_connect(self, host: str, port: int, username: str, protocol: str):
        """Handle connection attempt"""
        self.username = username
        self.protocol = protocol
        
        # Update UI
        self.connect_window.set_connecting(True, f"Connecting via {protocol}...")
        
        # Create appropriate client based on protocol
        if protocol.upper() == "TCP":
            self.client = TCPClient(host, port)
        else:
            self.client = UDPClient(host, port)
        
        # Use QTimer to avoid blocking the UI thread
        QTimer.singleShot(100, self.attempt_connection)
    
    def attempt_connection(self):
        """Attempt connection in non-blocking way"""
        try:
            if self.client.connect():
                # Connection successful
                self.connect_window.hide()
                self.show_chat_window()
                self.connect_window.show_success("Connected successfully")
            else:
                # Connection failed
                self.connect_window.set_connecting(False, "Connection failed")
                QMessageBox.critical(
                    self.connect_window, 
                    "Connection Failed", 
                    f"Could not connect to server via {self.protocol}.\n\n"
                    f"Please check:\n"
                    f"• Server address: {self.client.host}:{self.client.port}\n"
                    f"• Server is running\n"
                    f"• Firewall settings\n"
                    f"• Protocol selection"
                )
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            self.connect_window.set_connecting(False, "Connection error")
            QMessageBox.critical(
                self.connect_window,
                "Connection Error",
                f"An error occurred while connecting:\n{str(e)}"
            )
    
    def show_chat_window(self):
        """Show the main chat window"""
        self.chat_window = ChatWindow(
            self.username, 
            self.client.host, 
            self.client.port, 
            self.protocol
        )
        self.chat_window.client = self.client
        self.chat_window.message_sent.connect(self.handle_message_sent)
        self.chat_window.disconnected.connect(self.handle_disconnect)  # This should work now
        
        # Send connect message to server
        if hasattr(self.client, 'send_connect_message'):
            self.client.send_connect_message(self.username)
        
        # Start listening for messages
        self.client.start_listening(self.handle_received_message)
        
        self.chat_window.show()
        self.chat_window.add_message(f"Connected to server via {self.protocol}", is_system=True)
        self.chat_window.update_status(f"Ready to chat | Protocol: {self.protocol}", True)
    
    def handle_message_sent(self, message: str):
        """Handle sending a message"""
        if self.client and self.client.is_connected:
            success = self.client.send_message(message, self.username)
            if success:
                self.chat_window.add_message(message, is_own=True)
                self.chat_window.update_status("Message sent", True)
            else:
                self.chat_window.add_message("Failed to send message - check connection", is_system=True)
                self.chat_window.update_status("Send failed", True)
        else:
            self.chat_window.add_message("Not connected to server", is_system=True)
    
    def handle_received_message(self, chat_message: ChatMessage):
        """Handle received message from server"""
        if chat_message.type == MessageType.ERROR:
            self.chat_window.add_message(f"Error: {chat_message.content}", is_system=True)
        elif chat_message.type == MessageType.STATUS:
            self.chat_window.add_message(chat_message.content, is_system=True)
        elif chat_message.type == MessageType.MESSAGE:
            # Format the message for display
            if chat_message.username and chat_message.username != self.username:
                display_message = f"{chat_message.username}: {chat_message.content}"
                self.chat_window.add_message(display_message)
            else:
                self.chat_window.add_message(chat_message.content)
        else:
            # Handle other message types (CONNECT, DISCONNECT)
            self.chat_window.add_message(chat_message.content, is_system=True)
    
    def handle_disconnect(self):
        """Handle disconnection from UI"""
        if self.client:
            self.client.disconnect()
        
        if self.chat_window:
            self.chat_window.close()
        
        self.connect_window.set_connecting(False, "Disconnected")
        self.connect_window.show()
        self.connect_window.reset()
    
    def cleanup(self):
        """Clean up resources"""
        if self.client:
            self.client.disconnect()

def main():
    """Main entry point"""
    try:
        client = ChatClient()
        exit_code = client.run()
        client.cleanup()
        sys.exit(exit_code)
    except Exception as e:
        logging.error(f"Client error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()