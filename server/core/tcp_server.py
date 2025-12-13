import socket
import threading
from typing import Dict, Any
from server.core.server_base import ServerBase, ServerProtocol
from server.core.client_handler import ClientHandler
from server.core.message_protocol import MessageProtocol, MessageType
import ssl
from pathlib import Path


class TCPServer(ServerBase):
    """TCP server implementation"""

    def __init__(self, host: str = '0.0.0.0', port: int = 5050):
        super().__init__(host, port)
        self.clients: Dict[socket.socket, ClientHandler] = {}
        self.client_connected_callback = None
        self.client_disconnected_callback = None
        self.message_callback = None
        self.ssl_context = None
        
        # Setup SSL
        self._setup_ssl_context()
    
    def _setup_ssl_context(self):
        """Setup SSL context for server"""
        try:
            self.ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            
            # Load server certificate and private key
            certs_dir = Path(__file__).parent.parent.parent / "certs"
            cert_file = certs_dir / "server.crt"
            key_file = certs_dir / "server.key"
            
            if cert_file.exists() and key_file.exists():
                self.ssl_context.load_cert_chain(
                    certfile=str(cert_file),
                    keyfile=str(key_file)
                )
                print(f"🔐 SSL: Loaded certificates from {certs_dir}")
            else:
                print(f"⚠️ SSL: Certificate files not found in {certs_dir}")
                print("⚠️ SSL: Generating self-signed certificates...")
                self._generate_self_signed_cert()
            
            # Optional: Require client certificates
            # self.ssl_context.verify_mode = ssl.CERT_REQUIRED
            # self.ssl_context.load_verify_locations(cafile=str(certs_dir / "client.crt"))
            
        except Exception as e:
            print(f"❌ SSL setup failed: {e}")
            self.ssl_context = None

    @property
    def protocol(self) -> ServerProtocol:
        return ServerProtocol.TCP

    def set_message_callback(self, callback):
        """Set message callback for incoming client messages"""
        self.message_callback = callback

    def set_client_connected_callback(self, callback):
        """Set client connected callback"""
        self.client_connected_callback = callback

    def set_client_disconnected_callback(self, callback):
        """Set client disconnected callback"""
        self.client_disconnected_callback = callback

    def start_server(self) -> bool:
        if self.is_running:
            self._notify_status("Server already running")
            return True

        if not self._create_socket(socket.AF_INET, socket.SOCK_STREAM):
            return False

        if not self._bind_socket():
            return False

        try:
            self.socket.listen()
            self.is_running = True
            self._stop_event.clear()

            self.main_thread = threading.Thread(target=self._accept_connections, daemon=True)
            self.main_thread.start()

            status_msg = f"TCP Server started on {self.host}:{self.port}"
            if self.ssl_context:
                status_msg += " (SSL enabled)"
            self._notify_status(status_msg)
            
            return True

        except socket.error as e:
            self._notify_status(f"Failed to start server: {e}", True)
            self.is_running = False
            return False

    def stop_server(self) -> bool:
        if not self.is_running:
            self._notify_status("Server not running")
            return True

        self._notify_status("Stopping server...")
        self.is_running = False
        self._stop_event.set()

        for client_handler in list(self.clients.values()):
            client_handler.stop()

        self.clients.clear()

        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None

        self._notify_status("TCP Server stopped")
        return True

    def send_message(self, client_identifier: Any, message: str) -> bool:
        """Send message to specific client - IMPLEMENT ABSTRACT METHOD"""
        print(f"🔧 TCP SERVER DEBUG: Looking for client {client_identifier} to send: '{message}'")
        
        for socket_obj, client_handler in self.clients.items():
            handler_client_id = client_handler.get_client_info()['identifier']
            if handler_client_id == client_identifier:
                print(f"🔧 TCP SERVER DEBUG: Found client, sending message")
                return client_handler.send_message(message)
        
        print(f"❌ TCP SERVER DEBUG: Client {client_identifier} not found")
        return False

    def _accept_connections(self):
        while self.is_running and not self._stop_event.is_set():
            try:
                self.socket.settimeout(1.0)
                client_socket, client_address = self.socket.accept()
                self._handle_client_connection(client_socket, client_address)
            except socket.timeout:
                continue
            except OSError:
                break
            except Exception as e:
                if self.is_running:
                    self._notify_status(f"Error accepting connection: {e}", True)

    def _handle_client_connection(self, client_socket: socket.socket, client_address: tuple):
        print(f"🔍 TCP SERVER DEBUG: New client connection from {client_address}")
        
        # Wrap with SSL if available
        ssl_socket = None
        if self.ssl_context:
            try:
                ssl_socket = self.ssl_context.wrap_socket(
                    client_socket,
                    server_side=True
                )
                print(f"🔐 SSL: Secure connection established with {client_address}")
            except ssl.SSLError as e:
                print(f"❌ SSL handshake failed with {client_address}: {e}")
                client_socket.close()
                return
        else:
            ssl_socket = client_socket
            print(f"⚠️ SSL: Plain connection with {client_address} (no SSL)")
        
        client_handler = ClientHandler(
            client_socket=ssl_socket,  # Pass SSL socket
            client_address=client_address,
            remove_callback=self._remove_client,
            notify_callback=self._notify_status,
            message_callback=self._notify_message,
            ssl_enabled=self.ssl_context is not None
        )
        
        self.clients[ssl_socket] = client_handler
    
        # Notify client connected
        if self.client_connected_callback:
            client_info = {
                'identifier': f"{client_address[0]}:{client_address[1]}",
                'name': f"User_{len(self.clients)}",
                'address': client_address,
                'protocol': 'TCP',
                'ssl': self.ssl_context is not None
            }
            self.client_connected_callback(client_info)
        
        client_handler.start()
        print(f"🔍 TCP SERVER DEBUG: Client handler started for {client_address}")

    def _remove_client(self, client_socket: socket.socket):
        if client_socket in self.clients:
            client_handler = self.clients[client_socket]
            client_info = client_handler.get_client_info()
            client_info['protocol'] = 'TCP'
            
            # Notify client disconnected
            if self.client_disconnected_callback:
                self.client_disconnected_callback(client_info)
                
            del self.clients[client_socket]
            print(f"🔍 TCP SERVER DEBUG: Client removed: {client_info['identifier']}")

    def _notify_message(self, client_info: Dict, message: str):
        """Notify message callback if set"""
        print(f"🔍 TCP SERVER DEBUG: Received message from {client_info['identifier']}: '{message}'")
        print(f"🔍 TCP SERVER DEBUG: Message callback available: {self.message_callback is not None}")
        
        if self.message_callback:
            self.message_callback(client_info, message)
        else:
            print(f"❌ TCP SERVER DEBUG: No message callback set in TCPServer!") 