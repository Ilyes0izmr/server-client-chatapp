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
        # Main window setup
        self.setWindowTitle("ChatServ - Server Control")
        self.setGeometry(200, 200, 940, 540)
        
        # Central widget
        central_widget = QWidget()
        central_widget.setObjectName("mainWindow")
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Left panel
        self.left_panel = LeftPanel()
        main_layout.addWidget(self.left_panel)
        
        # Clients sidebar
        self.clients_sidebar = ClientsSidebar()
        main_layout.addWidget(self.clients_sidebar)
        
        # Chat area
        self.chat_area = ChatArea()
        main_layout.addWidget(self.chat_area)
        
        # Apply styles
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
        # Left panel signals
        self.left_panel.tcp_server_toggled.connect(self.on_tcp_toggled)
        self.left_panel.udp_server_toggled.connect(self.on_udp_toggled)
        self.left_panel.shutdown_servers.connect(self.on_shutdown)
        
        # Clients sidebar signals
        self.clients_sidebar.client_kicked.connect(self.on_client_kicked)
        self.clients_sidebar.client_selected.connect(self.on_client_selected)
        
        # Chat area signals
        self.chat_area.send_message.connect(self.on_send_message)
        self.chat_area.disconnect_client.connect(self.on_client_disconnect_request)
        
        # THREAD-SAFE SIGNALS → UI
        self.thread_signals.client_connected.connect(self.on_client_connected)
        self.thread_signals.client_disconnected.connect(self.on_client_disconnected)
        self.thread_signals.server_status.connect(self.on_server_status)
        self.thread_signals.server_message.connect(self.on_server_message)
        
    # Thread-safe callback wrappers
    def thread_safe_client_connected(self, client_info: dict):
        self.thread_signals.client_connected.emit(client_info)
        
    def thread_safe_client_disconnected(self, client_info: dict):
        self.thread_signals.client_disconnected.emit(client_info)
        
    def thread_safe_server_status(self, message: str, is_error: bool = False):
        self.thread_signals.server_status.emit(message, is_error)
        
    def thread_safe_server_message(self, client_info: dict, message: str):
        self.thread_signals.server_message.emit(client_info, message)
        
    # Signal handlers
    def on_tcp_toggled(self, running):
        if running:
            self.start_tcp_server()
        else:
            self.stop_tcp_server()
        
    def on_udp_toggled(self, running):
        if running:
            self.start_udp_server()
        else:
            self.stop_udp_server()
        
    def on_shutdown(self):
        print("SHUTDOWN: Stopping all servers...")
        self.stop_tcp_server()
        self.stop_udp_server()
        self.clients_sidebar.clear_clients()
        self.chat_area.clear_current_client()
        
    def on_client_kicked(self, client_id: str):
        print(f"Kicking client: {client_id}")
        
        # Kick from TCP server
        if self.tcp_server:
            for socket_obj, client_handler in list(self.tcp_server.clients.items()):
                try:
                    if client_handler.get_client_info()['identifier'] == client_id:
                        client_handler.stop()
                        return
                except:
                    continue
                    
        # Kick from UDP server  
        if self.udp_server:
            try:
                ip, port_str = client_id.split(':')
                client_addr = (ip, int(port_str))
                self.udp_server._handle_client_disconnect(client_addr)
            except Exception as e:
                print(f"Error kicking UDP client {client_id}: {e}")
        
    def on_client_selected(self, client_id: str):
        client_data = self.clients_sidebar.clients.get(client_id, {})
        self.chat_area.set_current_client(client_id, client_data)
        
    def on_send_message(self, client_id: str, message: str):
        # Try TCP first
        if self.tcp_server:
            success = self.tcp_server.send_message(client_id, message)
            if success:
                self.chat_area.add_message(message, is_server=True)
                return
        
        # Try UDP
        if self.udp_server:
            success = self.udp_server.send_message(client_id, message)
            if success:
                self.chat_area.add_message(message, is_server=True)
            else:
                self.chat_area.add_message(f"{message} ❌ (Failed)", is_server=True)
            return
        
        # Fallback
        self.chat_area.add_message(message, is_server=True)

    def on_client_disconnect_request(self, client_id: str):
        self.on_client_kicked(client_id)
        
    # Server logic
    def start_tcp_server(self):
        if not self.tcp_server:
            self.tcp_server = TCPServer(host='192.168.1.56', port=5050)
            self.tcp_server.set_status_callback(self.thread_safe_server_status)
            self.tcp_server.set_message_callback(self.thread_safe_server_message)
            self.tcp_server.set_client_connected_callback(self.thread_safe_client_connected)
            self.tcp_server.set_client_disconnected_callback(self.thread_safe_client_disconnected)
        
        if self.tcp_server.start_server():
            print("✅ TCP Server started on port 5050")
        else:
            print("❌ Failed to start TCP Server")
            self.tcp_server = None
            self.left_panel.is_tcp_running = False
            
    def stop_tcp_server(self):
        if self.tcp_server:
            self.tcp_server.stop_server()
            print("⏹️ TCP Server stopped")
            self.tcp_server = None
            
    def start_udp_server(self):
        if not self.udp_server:
            self.udp_server = UDPServer(host='192.168.1.56', port=5051)
            self.udp_server.set_status_callback(self.thread_safe_server_status)
            self.udp_server.set_message_callback(self.thread_safe_server_message)
            self.udp_server.set_client_connected_callback(self.thread_safe_client_connected)
            self.udp_server.set_client_disconnected_callback(self.thread_safe_client_disconnected)
        
        if self.udp_server.start_server():
            print("✅ UDP Server started on port 5051")
        else:
            print("❌ Failed to start UDP Server")
            self.udp_server = None
            self.left_panel.is_udp_running = False
            
    def stop_udp_server(self):
        if self.udp_server:
            self.udp_server.stop_server()
            print("⏹️ UDP Server stopped")
            self.udp_server = None
            
    # 🔧 FIXED: Robust client connection handler
    def on_client_connected(self, client_info: dict):
        print(f"🟢 CLIENT CONNECTED: {client_info}")
        
        # 🔑 Extract client_id robustly
        client_id = client_info.get('identifier')
        if not client_id:
            addr = client_info.get('address')
            if isinstance(addr, tuple) and len(addr) == 2:
                client_id = f"{addr[0]}:{addr[1]}"
            else:
                name = client_info.get('name', 'anonymous')
                client_id = f"{name}_{id(client_info)}"
            print(f"🔧 Generated client_id: '{client_id}'")
        
        # Build client data
        client_data = {
            'username': client_info.get('name', 'Anonymous'),
            'protocol': client_info.get('protocol', 'Unknown'),
            'ip': client_info.get('ip', '?.?.?.?'),
            'port': client_info.get('port', '?'),
            'address': client_info.get('address', 'Unknown')
        }
        
        print(f"✅ Adding client to sidebar: ID='{client_id}'")
        self.clients_sidebar.add_client(client_id, client_data)
        
    def on_client_disconnected(self, client_info: dict):
        client_id = client_info.get('identifier')
        if not client_id:
            addr = client_info.get('address')
            if isinstance(addr, tuple) and len(addr) == 2:
                client_id = f"{addr[0]}:{addr[1]}"
        
        if client_id:
            print(f"🔴 Removing client: {client_id}")
            self.clients_sidebar.remove_client(client_id)
            
            if self.chat_area.current_client == client_id:
                self.chat_area.clear_current_client()
        else:
            print(f"⚠️ Client disconnect without identifier: {client_info}")
            
    def on_server_status(self, message: str, is_error: bool = False):
        prefix = "❌ ERROR:" if is_error else "ℹ️ STATUS:"
        print(f"{prefix} {message}")
        
    def on_server_message(self, client_info: dict, message: str):
        print(f"📨 MESSAGE: {message} from {client_info}")
        
        # Extract client_id (same logic as on_client_connected)
        client_id = client_info.get('identifier')
        if not client_id:
            addr = client_info.get('address')
            if isinstance(addr, tuple) and len(addr) == 2:
                client_id = f"{addr[0]}:{addr[1]}"
            else:
                client_id = "unknown"
        
        # Ensure client exists in sidebar (race condition protection)
        if client_id not in self.clients_sidebar.clients:
            print(f"🆕 Auto-adding missing client: {client_id}")
            client_data = {
                'username': client_info.get('name', 'Anonymous'),
                'protocol': client_info.get('protocol', 'UDP'),
                'ip': client_info.get('ip', '?.?.?.?'),
                'port': client_info.get('port', '?')
            }
            self.clients_sidebar.add_client(client_id, client_data)
        
        # Deliver to chat
        self.chat_area.add_client_message(client_id, message)