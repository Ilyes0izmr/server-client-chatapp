import abc
import socket
import threading
from typing import Optional, Callable, Dict, Any
from enum import Enum

class ServerProtocol(Enum):
    TCP = "tcp"
    UDP = "udp"

class ServerBase(abc.ABC):
    """Abstract base class for TCP/UDP servers"""

    def __init__(self, host: str = 'localhost', port: int = 5050):
        self.host = host
        self.port = port
        self.is_running = False
        self.socket: Optional[socket.socket] = None
        self.clients: Dict[Any, Any] = {}  # Protocol-specific client storage
        self.message_callback: Optional[Callable] = None
        self.status_callback: Optional[Callable] = None
        
        # Threading
        self.main_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def set_message_callback(self, callback: Callable):
        """Set callback for incoming messages"""
        self.message_callback = callback

    def set_status_callback(self, callback: Callable):
        """Set callback for server status updates"""
        self.status_callback = callback

    def _notify_status(self, message: str, is_error: bool = False):
        """Notify status callback if set"""
        if self.status_callback:
            self.status_callback(message, is_error)

    def _notify_message(self, client_info: Dict, message: str):
        """Notify message callback if set"""
        if self.message_callback:
            self.message_callback(client_info, message)

    @abc.abstractmethod
    def start_server(self) -> bool:
        """Start the server"""
        pass

    @abc.abstractmethod
    def stop_server(self) -> bool:
        """Stop the server"""
        pass

    @abc.abstractmethod
    def send_message(self, client_identifier: Any, message: str) -> bool:
        """Send message to specific client"""
        pass

    @abc.abstractmethod
    def _handle_client_connection(self, *args, **kwargs):
        """Handle new client connection or datagram"""
        pass

    @property
    @abc.abstractmethod
    def protocol(self) -> ServerProtocol:
        """Return server protocol type"""
        pass

    def get_client_count(self) -> int:
        return len(self.clients)

    def get_clients_info(self) -> Dict[Any, Any]:
        return self.clients.copy()

    def is_server_running(self) -> bool:
        return self.is_running

    def _create_socket(self, socket_family: int, socket_type: int) -> bool:
        try:
            self.socket = socket.socket(socket_family, socket_type)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            return True
        except socket.error as e:
            self._notify_status(f"Socket creation failed: {e}", True)
            return False

    def _bind_socket(self) -> bool:
        try:
            self.socket.bind((self.host, self.port))
            return True
        except socket.error as e:
            self._notify_status(f"Socket binding failed: {e}", True)
            return False