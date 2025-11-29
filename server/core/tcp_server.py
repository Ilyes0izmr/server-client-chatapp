import socket
import threading
from typing import Dict, Any
from server.core.server_base import ServerBase, ServerProtocol
from server.core.client_handler import ClientHandler
from server.core.message_protocol import MessageProtocol, MessageType

class TCPServer(ServerBase):
    """TCP server implementation"""

    def __init__(self, host: str = '172.90.0.1', port: int = 5050):
        super().__init__('172.90.0.1', port)
        self.clients: Dict[socket.socket, ClientHandler] = {}
        self.client_connected_callback = None
        self.client_disconnected_callback = None
        self.message_callback = None

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

            self._notify_status(f"TCP Server started on {self.host}:{self.port}")
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
        
        client_handler = ClientHandler(
            client_socket=client_socket,
            client_address=client_address,
            remove_callback=self._remove_client,
            notify_callback=self._notify_status,
            message_callback=self._notify_message
        )
        
        self.clients[client_socket] = client_handler
    
        # Notify client connected
        if self.client_connected_callback:
            client_info = {
                'identifier': f"{client_address[0]}:{client_address[1]}",
                'name': f"User_{len(self.clients)}",
                'address': client_address,
                'protocol': 'TCP'
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