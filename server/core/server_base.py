import abc
import socket 
import threading 
from typing import Optional , Callable , Dict , Any
from enum import Enum 



class ServerProtocol(Enum):
    TCP = "tcp"
    UDP = "udp"



class ServerBase(abc.ABC):
    """abstract class for the servers tcp/udp """

    def __init__(self , host: str = 'localhost' , port: int = 5050):
        self.host = host                            
        self.port = port 
        self.is_running = False 
        self.socket: Optional[socket.socket] = None 
        self.client : Dict[Any, Dict] = {}              #it will be a dict of client id , clinet hundler (for thread)
        self.message_callback: Optional[Callable] = None 
        self.status_callback: Optional[Callable] = None 

        # threading
        self.main_thread: Optional[threading.Thread] = None 
        self.stop_event = threading.Event()

        def set_message_callback(self, callback: Callable):
            """set callback for incoming messgaes"""
            self.nessage_callback = callback 

        def set_status_callback(self, callback: Callable):
            """Set callback for server status updates."""
            self.status_callback = callback

        def _notify_status(self, message: str, is_error: bool = False):
            """Notify status callback if set."""
            if self.status_callback:
                self.status_callback(message, is_error)

        def _notify_message(self, client_info: Dict, message: str):
            """Notify message callback if set."""
            if self.message_callback:
                self.message_callback(client_info, message)


        @abc.abstractmethod
        def start_server(self) -> bool:
            """
                Start the server.
                Returns: True if successful, False otherwise.
            """
            pass

        @abc.abstractmethod
        def stop_server(self) -> bool:
            """
                Stop the server.
                Returns: True if successful, False otherwise.
            """
            pass

        def send_message(self, client_identifier: Any, message: str) -> bool:
            """
                Send message to specific client.
                Args:
                    client_identifier: Client identifier (socket for TCP, addr for UDP)
                    message: Message to send
                Returns: True if successful, False otherwise
            """
            pass

        @abc.abstractmethod
        def broadcast_message(self, message: str, exclude_client: Any = None) -> bool:
            """
                Broadcast message to all connected clients.
                Args:
                    message: Message to broadcast
                    exclude_client: Client to exclude from broadcast
                Returns: True if successful, False otherwise
            """
            pass

        @abc.abstractmethod
        def handle_client_connection(self, *args, **kwargs):
            """
                Handle new client connection (TCP) or incoming datagram (UDP).
                Implementation differs between TCP and UDP.
            """
        pass

        
        @property
        @abc.abstractmethode
        def protocol(self) -> ServerProtocol:
            """Return the server protocol type."""
            pass
        
        def get_client_count(self) -> int:
            """Get number of connected clients."""
            return len(self.clients)
        
        def get_clients_info(self) -> Dict[Any, Dict]:
            """Get information about all connected clients."""
            return self.clients.copy()
        
        def is_server_running(self) -> bool:
            """Check if server is running."""
            return self.is_running
        
        def get_server_info(self) -> Dict[str, Any]:
            """Get server information."""
            return {
                'host': self.host,
                'port': self.port,
                'protocol': self.protocol.value,
                'running': self.is_running,
                'clients_count': self.get_client_count()
            }
        
        def _create_socket(self, socket_family: int, socket_type: int) -> bool:
            """Common socket creation logic."""
            try:
                self.socket = socket.socket(socket_family, socket_type)
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                return True
            except socket.error as e:
                self._notify_status(f"Socket creation failed: {e}", True)
                return False
            

        def _bind_socket(self) -> bool:
            """Common socket binding logic."""
            try:
                self.socket.bind((self.host, self.port))
                return True
            except socket.error as e:
                self._notify_status(f"Socket binding failed: {e}", True)
                return False