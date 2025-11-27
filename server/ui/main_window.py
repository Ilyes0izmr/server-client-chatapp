from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QSplitter)
from PyQt6.QtCore import Qt
from server.ui.navbar import Navbar
from server.ui.sidebar_clients import SidebarClients
from server.ui.chat_area import ChatArea
from server.core.server import TCPServer

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.server = TCPServer() # server instance 
        self.setup_ui()           # sdetup UI components
        
        #connect seerv signals to hundler methodes in main window
        self.server.client_connected_signal.connect(self.handle_client_connected)     
        self.server.client_disconnected_signal.connect(self.handle_client_disconnected)
        self.server.message_received_signal.connect(self.handle_message_received)
    
    def setup_ui(self):
        # Window configuration
        self.setWindowTitle("Chat Server")
        self.setGeometry(100, 100, 1400, 900)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a1a;
            }
        """)
        
        # Central widget
        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: #1a1a1a;")
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Navbar (top)
        self.navbar = Navbar(self.server)
        self.navbar.start_signal.connect(self.start_server) # connect start signal in navbar to start_server method that calls the server start() in server.py
        self.navbar.stop_signal.connect(self.stop_server)   # connect stop signal in navbar to stop_server method that calls the server stop() in server.py
        main_layout.addWidget(self.navbar)
        
        # Main content area (navbar + sidebar + chat)
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        content_splitter.setStyleSheet("QSplitter::handle { background-color: #333333; }")
        main_layout.addWidget(content_splitter)
        
        # Sidebar (left)
        self.sidebar = SidebarClients()
        self.sidebar.chat_signal.connect(self.open_chat)
        #TODO: fix it later it toped working
        self.sidebar.kick_signal.connect(self.kick_client) 
        content_splitter.addWidget(self.sidebar)
        
        # caht area on hte fight
        self.chat_area = ChatArea()
        self.chat_area.send_message_signal.connect(self.send_message_to_client)
        content_splitter.addWidget(self.chat_area)
        
        # Set proportions
        content_splitter.setSizes([350, 1050])
    
    def start_server(self):
        if self.server.start_server():
            self.navbar.update_status(True, self.server.port, len(self.server.clients))
    
    def stop_server(self):
        if self.server.stop_server():
            self.navbar.update_status(False)
            self.sidebar.clear_clients()
            self.chat_area.current_client = None
            self.chat_area.show_welcome_message()
            self.chat_area.set_chat_enabled(False)
    
    def handle_client_connected(self, client_handler):
        self.sidebar.add_client(client_handler) # add the client hundler to the sidebar
        self.navbar.update_status(True, self.server.port, len(self.server.clients)) #display it with its clicks and blablablabla
    
    def handle_client_disconnected(self, client_handler):
        self.sidebar.remove_client(client_handler)
        self.navbar.update_status(True, self.server.port, len(self.server.clients))
        if self.chat_area.current_client and self.chat_area.current_client.client_id == client_handler.client_id:
            self.chat_area.current_client = None
            self.chat_area.show_welcome_message()
            self.chat_area.set_chat_enabled(False)
    
    # Client → TCPServer → signal → MainWindow → ChatArea (show message) 
    def handle_message_received(self, client_handler, message):
        self.chat_area.receive_message(client_handler, message)
    
    def open_chat(self, client_handler):
        self.chat_area.switch_to_client(client_handler)
    
    # User types → ChatArea → signal → MainWindow → TCPServer → specific client
    def send_message_to_client(self, client_handler, message):
        self.server.send_message_to_client(client_handler.client_id, message)
    
    #TODO: fix it later
    def kick_client(self, client_handler):
        if self.chat_area.current_client and self.chat_area.current_client.client_id == client_handler.client_id:
            self.chat_area.current_client = None
            self.chat_area.show_welcome_message()
            self.chat_area.set_chat_enabled(False)
        
        client_handler.is_running = False
        try:
            client_handler.client_socket.close()
        except:
            pass
    
    def closeEvent(self, event):
        self.server.stop_server()
        event.accept()