from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout
from PyQt6.QtCore import Qt
from server.ui.components.left_panel import LeftPanel
from server.ui.components.clients_sidebar import ClientsSidebar
from server.ui.components.chat_area import ChatArea
from server.ui.thread_signals import ThreadSignals
from server.core.tcp_server import TCPServer
from server.core.udp_server import UDPServer

class ServerMainWindow(QMainWindow):
    """Main server window with complete chat functionality"""
    
    def __init__(self):
        super().__init__()
        self.tcp_server = None
        self.udp_server = None
        
        # Create thread-safe signals
        self.thread_signals = ThreadSignals()
        
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        # Main window setup ------------------------------------------------------------
        self.setWindowTitle("ChatServ - Server Control")
        self.setGeometry(200, 200, 1400, 800)  # Increased width for chat
        
        # Central widget ------------------------------------------------------------
        central_widget = QWidget()
        central_widget.setObjectName("mainWindow")
        self.setCentralWidget(central_widget)
        
        # Main layout ------------------------------------------------------------
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Left panel ------------------------------------------------------------
        self.left_panel = LeftPanel()
        main_layout.addWidget(self.left_panel)
        
        # Clients sidebar ------------------------------------------------------------
        self.clients_sidebar = ClientsSidebar()
        main_layout.addWidget(self.clients_sidebar)
        
        # Chat area ------------------------------------------------------------
        self.chat_area = ChatArea()
        main_layout.addWidget(self.chat_area)
        
        # Apply styles ------------------------------------------------------------
        self.apply_styles()
        
    def apply_styles(self):
        """Apply CSS styles to main window"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0D0D0D;
            }
            #mainWindow {
                background-color: #0D0D0D;
            }
        """)
        
    def connect_signals(self):
        """Connect all signals - THREAD-SAFE VERSION"""
        # Left panel signals ------------------------------------------------------------
        self.left_panel.tcp_server_toggled.connect(self.on_tcp_toggled)
        self.left_panel.udp_server_toggled.connect(self.on_udp_toggled)
        self.left_panel.shutdown_servers.connect(self.on_shutdown)
        
        # Clients sidebar signals ------------------------------------------------------------
        self.clients_sidebar.client_kicked.connect(self.on_client_kicked)
        self.clients_sidebar.client_selected.connect(self.on_client_selected)
        
        # Chat area signals ------------------------------------------------------------
        self.chat_area.send_message.connect(self.on_send_message)
        self.chat_area.disconnect_client.connect(self.on_client_disconnect_request)
        
        # THREAD-SAFE SIGNALS ------------------------------------------------------------
        self.thread_signals.client_connected.connect(self.on_client_connected)
        self.thread_signals.client_disconnected.connect(self.on_client_disconnected)
        self.thread_signals.server_status.connect(self.on_server_status)
        self.thread_signals.server_message.connect(self.on_server_message)
        
    # Thread-safe callback wrappers ------------------------------------------------------------
    def thread_safe_client_connected(self, client_info: dict):
        """Thread-safe client connected callback"""
        self.thread_signals.client_connected.emit(client_info)
        
    def thread_safe_client_disconnected(self, client_info: dict):
        """Thread-safe client disconnected callback"""
        self.thread_signals.client_disconnected.emit(client_info)
        
    def thread_safe_server_status(self, message: str, is_error: bool = False):
        """Thread-safe server status callback"""
        self.thread_signals.server_status.emit(message, is_error)
        
    def thread_safe_server_message(self, client_info: dict, message: str):
        """Thread-safe server message callback"""
        self.thread_signals.server_message.emit(client_info, message)
        
    # Signal handlers ------------------------------------------------------------
    def on_tcp_toggled(self, running):
        """Handle TCP server toggle"""
        if running:
            self.start_tcp_server()
        else:
            self.stop_tcp_server()
        
    def on_udp_toggled(self, running):
        """Handle UDP server toggle"""
        if running:
            self.start_udp_server()
        else:
            self.stop_udp_server()
        
    def on_shutdown(self):
        """Handle shutdown all servers"""
        print("SHUTDOWN: Stopping all servers...")
        self.stop_tcp_server()
        self.stop_udp_server()
        self.clients_sidebar.clear_clients()
        self.chat_area.clear_current_client()
        
    def on_client_kicked(self, client_id: str):
        """Handle REAL client kick"""
        print(f"Kicking client: {client_id}")
        
        # Kick from TCP server
        if self.tcp_server:
            for socket_obj, client_handler in self.tcp_server.clients.items():
                if client_handler.get_client_info()['identifier'] == client_id:
                    # Stop the client handler (this will trigger disconnect)
                    client_handler.stop()
                    return
                    
        # Kick from UDP server  
        if self.udp_server:
            # Parse address and disconnect
            try:
                ip, port_str = client_id.split(':')
                client_addr = (ip, int(port_str))
                self.udp_server._handle_client_disconnect(client_addr)
            except Exception as e:
                print(f"Error kicking UDP client: {e}")
        
    def on_client_selected(self, client_id: str):
        """Handle client selection - show chat with this client"""
        print(f"🎯 DEBUG: Client selected: {client_id}")
        
        # Get client data from sidebar
        client_data = self.clients_sidebar.clients.get(client_id, {})
        print(f"🎯 DEBUG: Client data: {client_data}")
        
        # Set current client in chat area
        self.chat_area.set_current_client(client_id, client_data)
        print(f"🎯 DEBUG: Chat area current client set to: {self.chat_area.current_client}")
        
    def on_send_message(self, client_id: str, message: str):
        """Send message to client via appropriate server"""
        print(f"🚀 DEBUG: Sending message to {client_id}: {message}")
        
        # Send via TCP
        if self.tcp_server:
            print(f"🚀 DEBUG: Checking TCP server...")
            success = self.tcp_server.send_message(client_id, message)
            print(f"🚀 DEBUG: TCP send result: {success}")
            
            # Add the message to chat area immediately for visual feedback
            if success:
                self.chat_area.add_message(message, is_server=True)
            return
                        
        # Send via UDP
        if self.udp_server:
            print(f"🚀 DEBUG: Checking UDP server...")
            success = self.udp_server.send_message(client_id, message)
            print(f"🚀 DEBUG: UDP send result: {success}")
            
            # Add the message to chat area immediately for visual feedback
            if success:
                self.chat_area.add_message(message, is_server=True)
            else:
                # If send failed, still show in UI but mark as failed
                self.chat_area.add_message(f"{message} ❌ (Send failed)", is_server=True)
            return
        
        print(f"❌ DEBUG: No server available for client {client_id}")
        # Even if no server, add to chat for visual feedback
        self.chat_area.add_message(message, is_server=True)

    def on_client_disconnect_request(self, client_id: str):
        """Handle disconnect request from chat area"""
        self.on_client_kicked(client_id)  # Same as kick functionality
        
    # Server logic ------------------------------------------------------------
    def start_tcp_server(self):
        """Start TCP server with THREAD-SAFE callbacks"""
        if not self.tcp_server:
            self.tcp_server = TCPServer(host='localhost', port=5050)
            
            # Use thread-safe callbacks
            self.tcp_server.set_status_callback(self.thread_safe_server_status)
            self.tcp_server.set_message_callback(self.thread_safe_server_message)
            self.tcp_server.set_client_connected_callback(self.thread_safe_client_connected)
            self.tcp_server.set_client_disconnected_callback(self.thread_safe_client_disconnected)
        
        if self.tcp_server.start_server():
            print("TCP Server started successfully")
        else:
            print("Failed to start TCP Server")
            self.tcp_server = None
            self.left_panel.is_tcp_running = False
            self.left_panel.update_button_states()
            
    def stop_tcp_server(self):
        """Stop TCP server"""
        if self.tcp_server:
            if self.tcp_server.stop_server():
                print("TCP Server stopped successfully")
            else:
                print("Failed to stop TCP Server")
            self.tcp_server = None
            
    def start_udp_server(self):
        """Start UDP server with THREAD-SAFE callbacks - FIXED"""
        if not self.udp_server:
            self.udp_server = UDPServer(host='localhost', port=5051)
            
            # FIX: Ensure all callbacks are set for UDP
            self.udp_server.set_status_callback(self.thread_safe_server_status)
            self.udp_server.set_message_callback(self.thread_safe_server_message)
            self.udp_server.set_client_connected_callback(self.thread_safe_client_connected)
            self.udp_server.set_client_disconnected_callback(self.thread_safe_client_disconnected)
        
        if self.udp_server.start_server():
            print("UDP Server started successfully on port 5051")
        else:
            print("Failed to start UDP Server")
            self.udp_server = None
            self.left_panel.is_udp_running = False
            self.left_panel.update_button_states()
            
    def stop_udp_server(self):
        """Stop UDP server"""
        if self.udp_server:
            if self.udp_server.stop_server():
                print("UDP Server stopped successfully")
            else:
                print("Failed to stop UDP Server")
            self.udp_server = None
            
    # Client management ------------------------------------------------------------
    def on_client_connected(self, client_info: dict):
        """Handle REAL client connection from server"""
        client_id = client_info.get('identifier', 'Unknown')
        protocol = client_info.get('protocol', 'TCP')
        
        print(f"🟢 MAIN: Client connected - ID: {client_id}, Protocol: {protocol}")
        print(f"🟢 MAIN: Full client_info: {client_info}")
        
        client_data = {
            'username': client_info.get('name', f'User_{client_id}'),
            'protocol': protocol,
            'address': client_info.get('address', 'Unknown')
        }
        
        print(f"🟢 MAIN: Calling sidebar.add_client with: {client_id}")
        self.clients_sidebar.add_client(client_id, client_data)
        
    def on_client_disconnected(self, client_info: dict):
        """Handle REAL client disconnection from server"""
        client_id = client_info.get('identifier', 'Unknown')
        print(f"🔴 REAL Client disconnected: {client_id}")
        
        self.clients_sidebar.remove_client(client_id)
        
        # Clear chat if this client was selected
        if self.chat_area.current_client == client_id:
            self.chat_area.clear_current_client()
            
    # Server callbacks ------------------------------------------------------------
    def on_server_status(self, message: str, is_error: bool = False):
        """Handle server status updates"""
        prefix = "ERROR: " if is_error else "STATUS: "
        print(f"{prefix}{message}")
        
    def on_server_message(self, client_info: dict, message: str):
        """Handle incoming messages and display in chat - FIXED"""
        print(f"📨 MAIN: Full client_info received: {client_info}")
        
        # FIX: Better client_id extraction
        client_id = client_info.get('identifier', 'Unknown')
        if client_id == 'Unknown':
            address = client_info.get('address')
            if address and isinstance(address, tuple) and len(address) == 2:
                client_id = f"{address[0]}:{address[1]}"
            else:
                client_id = str(client_info.get('name', 'Unknown_Client'))
        
        print(f"📨 MAIN: Final client_id: {client_id}")
        print(f"📨 MAIN: Message: {message}")
        
        # FIX: Ensure client exists in sidebar (backup in case callback failed)
        if client_id not in self.clients_sidebar.clients:
            print(f"🆕 MAIN: Adding missing client to sidebar: {client_id}")
            client_data = {
                'username': client_info.get('name', f'User_{client_id}'),
                'protocol': client_info.get('protocol', 'UDP'),  # Default to UDP if missing
                'address': client_info.get('address', 'Unknown')
            }
            self.clients_sidebar.add_client(client_id, client_data)
        
        # FIX: Always pass message to chat area
        print(f"💬 MAIN: Sending to chat area - Client: {client_id}")
        self.chat_area.add_client_message(client_id, message)