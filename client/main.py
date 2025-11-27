import sys
import logging
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PyQt6.QtCore import Qt, QTimer
from client.core.client_socket import ClientSocket
from client.ui.connect_window import ConnectWindow
from client.ui.chat_window import ChatWindow

class ClientApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.client_socket = ClientSocket() #createa client object .. 
        self.setup_ui()
        
        # Connect the connection lost callback
        self.client_socket.on_connection_lost = self.handle_connection_lost
    
    def setup_ui(self):
        # Window configuration
        self.setWindowTitle("Chat Client")
        self.setGeometry(200, 200, 500, 400)
        
        # Central widget with stacked layout
        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)
        
        # Connect window
        self.connect_window = ConnectWindow(self.client_socket)
        self.connect_window.connect_signal.connect(self.handle_connect)
        self.central_widget.addWidget(self.connect_window)
        
        # Chat window
        self.chat_window = ChatWindow(self.client_socket)
        self.central_widget.addWidget(self.chat_window)
    #User enters IP → Connect button → handle_connect() →  ClientSocket.connect() attempts connection →
    def handle_connect(self, host: str, port: int):
        """Handle connection attempt"""
        # Update UI to show connecting state
        self.connect_window.update_status(False, "🟡 Connecting to server...")
        self.connect_window.set_connect_enabled(False)
        
        # Try to connect
        if self.client_socket.connect(host, port):
            self.connect_window.update_status(True, self.client_socket.get_connection_status())
            self.chat_window.update_status(True, "Connected to server")
            self.central_widget.setCurrentIndex(1)  # Switch to chat window
        else:
            self.connect_window.update_status(False, "🔴 Connection failed")
            self.connect_window.set_connect_enabled(True)
    
    def handle_connection_lost(self):
        """Handle server disconnection - return to connect page"""
        # Use QTimer to safely return to main thread
        QTimer.singleShot(0, self._return_to_connect_page)
    
    def _return_to_connect_page(self):
        """Actually return to connect page (called in main thread)"""
        # Switch back to connect page FIRST
        self.central_widget.setCurrentIndex(0)
        
        # Then update the status
        self.connect_window.update_status(False, "🔴 Connection lost. Server may be down.")
        self.connect_window.set_connect_enabled(True)
        
        # Add disconnect message to chat window (optional)
        self.chat_window.add_message("System", "Disconnected from server.")
    
    def closeEvent(self, event):
        """Handle window close event"""
        self.client_socket.disconnect()
        event.accept()

def main():
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    app = QApplication(sys.argv)
    
    # Set dark theme for entire application
    app.setStyleSheet("""
        QMainWindow {
            background-color: #2d3436;
        }
        QWidget {
            background-color: #2d3436;
        }
    """)
    
    window = ClientApp()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()