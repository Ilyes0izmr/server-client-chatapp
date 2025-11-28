import socket
import threading
import time
from typing import Dict, Tuple, Optional
from server.core.server_base import ServerBase, ServerProtocol
from server.core.message_protocol import MessageProtocol, MessageType

class UDPServer(ServerBase):
    """UDP Server Implementation"""

    def __init__(self, host: str = 'localhost', port: int = 5051):
        super().__init__(host, port)
        self.clients: Dict[Tuple[str, int], dict] = {}
        self.client_last_seen: Dict[Tuple[str, int], float] = {}
        self._lock = threading.RLock()
        self.receive_thread: Optional[threading.Thread] = None
        self.cleanup_thread: Optional[threading.Thread] = None

    def start_server(self) -> bool:
        """Start the UDP server."""
        if self.is_running:
            self._notify_status("UDP server is already running", False)
            return False
        
        # Create UDP socket
        if not self._create_socket(socket.AF_INET, socket.SOCK_DGRAM):
            return False
        
        if not self._bind_socket():
            return False
        
        self.is_running = True
        self._stop_event.clear()
        
        # Start receiving thread
        self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.receive_thread.start()
        
        # Start client cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
        
        self._notify_status(f"UDP server started on {self.host}:{self.port}", False)
        return True

    def stop_server(self) -> bool:
        """Stop the UDP server."""
        self.is_running = False
        self._stop_event.set()
        
        if self.socket:
            self.socket.close()
            self.socket = None
        
        # Clear client data and notify about disconnections
        with self._lock:
            disconnected_clients = list(self.clients.values())
            self.clients.clear()
            self.client_last_seen.clear()
        
        # Notify about disconnected clients
        for client_info in disconnected_clients:
            if hasattr(self, 'client_disconnected_callback') and self.client_disconnected_callback:
                self.client_disconnected_callback(client_info)
        
        self._notify_status("UDP server stopped", False)
        return True

    def send_message(self, client_identifier: any, message: str) -> bool:
        """Send message to specific client."""
        try:
            # Parse client identifier
            if isinstance(client_identifier, str):
                ip, port_str = client_identifier.split(':')
                port = int(port_str)
                client_addr = (ip, port)
            else:
                client_addr = client_identifier
            
            with self._lock:
                if client_addr not in self.clients:
                    return False
            
            # Create message using MessageProtocol
            message_data = MessageProtocol.encode_message(
                MessageType.MESSAGE,
                message,
                "server"
            ).encode('utf-8')
            
            # Send datagram
            self.socket.sendto(message_data, client_addr)
            return True
            
        except Exception as e:
            print(f"UDP send error: {e}")
            return False

    def _handle_client_connection(self, data: bytes, client_addr: Tuple[str, int]):
        """Handle incoming UDP datagram - REQUIRED ABSTRACT METHOD"""
        print(f"🟢 UDP: Received data from {client_addr[0]}:{client_addr[1]}")
        self._update_client_activity(client_addr)
        self._handle_received_data(data, client_addr)

    def _receive_loop(self):
        """Main loop for receiving UDP datagrams."""
        while self.is_running and self.socket and not self._stop_event.is_set():
            try:
                data, client_addr = self.socket.recvfrom(4096)
                if data:
                    # Call the abstract method implementation
                    self._handle_client_connection(data, client_addr)
            except socket.timeout:
                continue
            except OSError:
                break
            except Exception as e:
                print(f"UDP receive error: {e}")
                continue

    def _handle_received_data(self, data: bytes, client_addr: Tuple[str, int]):
        """Handle received UDP data."""
        try:
            message_str = data.decode('utf-8')
            message = MessageProtocol.decode_message(message_str)
            
            print(f"🔍 UDP DEBUG: Raw message: {message}")
            
            if not message:
                print(f"🟡 UDP: Invalid message format from {client_addr}")
                return
            
            # FIX: Check if message is a tuple and extract properly
            if isinstance(message, tuple):
                # If it's a tuple, assume it's (message_type, content, sender)
                message_type_enum, content, sender = message
                message_type = message_type_enum.value
            elif isinstance(message, dict):
                # If it's a dict, use the normal approach
                message_type = message.get('type')
                content = message.get('content', '')
                sender = message.get('sender', 'Unknown')
            else:
                print(f"🟡 UDP: Unknown message format: {type(message)}")
                return
            
            print(f"🟢 UDP: Received {message_type} from {client_addr}: {content}")
            
            if message_type == MessageType.CONNECT.value:
                self._handle_client_connect(client_addr, content or sender)
            elif message_type == MessageType.DISCONNECT.value:
                self._handle_client_disconnect(client_addr)
            elif message_type == MessageType.MESSAGE.value:
                self._handle_chat_message(client_addr, content)
            elif message_type == MessageType.STATUS.value:
                # Handle status messages (like "User aaa connected")
                print(f"📊 UDP: Status message: {content}")
            else:
                print(f"🟡 UDP: Unknown message type: {message_type}")
                
        except Exception as e:
            print(f"❌ UDP handle data error: {e}")
            import traceback
            traceback.print_exc()

    def _handle_client_connect(self, client_addr: Tuple[str, int], client_name: str):
        """Handle new client connection."""
        client_identifier = f"{client_addr[0]}:{client_addr[1]}"
        
        print(f"🟢 UDP: Handling client connect - {client_identifier}")
        
        with self._lock:
            if client_addr not in self.clients:
                client_info = {
                    'identifier': client_identifier,
                    'name': client_name or f"UDP_User_{client_identifier}",
                    'username': client_name or f"UDP_User_{client_identifier}",
                    'protocol': 'UDP',  # CRITICAL: This makes clients appear in sidebar
                    'address': client_addr
                }
                self.clients[client_addr] = client_info
                self.client_last_seen[client_addr] = time.time()
                
                # NOTIFY UI ABOUT NEW CLIENT
                if hasattr(self, 'client_connected_callback') and self.client_connected_callback:
                    print(f"🟢 UDP: Calling connection callback for {client_identifier}")
                    self.client_connected_callback(client_info)
                else:
                    print(f"❌ UDP: Connection callback not available!")
        
        self._notify_status(f"UDP Client connected: {client_identifier}", False)
        
        # Send welcome message
        welcome_msg = MessageProtocol.encode_message(
            MessageType.STATUS,
            f"Welcome {client_name}!",
            "server"
        ).encode('utf-8')
        self.socket.sendto(welcome_msg, client_addr)

    def _handle_client_disconnect(self, client_addr: Tuple[str, int]):
        """Handle client disconnection."""
        client_identifier = f"{client_addr[0]}:{client_addr[1]}"
        
        with self._lock:
            client_info = self.clients.pop(client_addr, None)
            self.client_last_seen.pop(client_addr, None)
        
        if client_info and hasattr(self, 'client_disconnected_callback') and self.client_disconnected_callback:
            print(f"🔴 UDP: Calling disconnect callback for {client_identifier}")
            self.client_disconnected_callback(client_info)
            
        self._notify_status(f"UDP Client disconnected: {client_identifier}", False)

    def _handle_chat_message(self, client_addr: Tuple[str, int], content: str):
        """Handle chat message from client."""
        print(f"🟢 UDP: Handling chat message from {client_addr}")
        
        # If client doesn't exist, auto-create them
        with self._lock:
            if client_addr not in self.clients:
                print(f"🟡 UDP: Auto-creating client {client_addr}")
                self._handle_client_connect(client_addr, f"UDP_User_{client_addr[0]}:{client_addr[1]}")
            
            client_info = self.clients.get(client_addr, {})
        
        # NOTIFY UI ABOUT MESSAGE
        if self.message_callback:
            print(f"📨 UDP: Message from {client_info.get('identifier')}: {content}")
            self._notify_message(client_info, content)
        else:
            print(f"❌ UDP: Message callback not set!")

    def _update_client_activity(self, client_addr: Tuple[str, int]):
        """Update client's last seen timestamp."""
        with self._lock:
            self.client_last_seen[client_addr] = time.time()

    def _cleanup_loop(self):
        """Clean up inactive clients."""
        while self.is_running and not self._stop_event.is_set():
            try:
                current_time = time.time()
                disconnected_clients = []
                
                with self._lock:
                    for client_addr, last_seen in self.client_last_seen.items():
                        if current_time - last_seen > 30:  # 30 second timeout
                            disconnected_clients.append(client_addr)
                
                for client_addr in disconnected_clients:
                    print(f"🟡 UDP: Cleaning up inactive client {client_addr}")
                    self._handle_client_disconnect(client_addr)
                
                time.sleep(5)
            except Exception as e:
                print(f"UDP cleanup error: {e}")
                time.sleep(5)

    @property
    def protocol(self) -> ServerProtocol:
        return ServerProtocol.UDP