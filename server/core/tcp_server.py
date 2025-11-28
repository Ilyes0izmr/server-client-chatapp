import socket
import threading
from typing import Dict
from server.core.server_base import ServerBase, ServerProtocol
from server.core.client_handler import ClientHandler

class TCPServer(ServerBase):
    """TCP server implementation"""

    def __init__(self, host: str = 'localhost', port: int = 5050):
        super().__init__(host, port)
        self.clients: Dict[socket.socket, ClientHandler] = {}

    @property
    def protocol(self) -> ServerProtocol:
        return ServerProtocol.TCP

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
                    self._notify_status(f"Error: {e}", True)

    def _handle_client_connection(self, client_socket: socket.socket, client_address: tuple):
        client_handler = ClientHandler(
            client_socket=client_socket,
            client_address=client_address,
            remove_callback=self._remove_client,
            notify_callback=self._notify_status
        )
        self.clients[client_socket] = client_handler
        client_handler.start()

    def _remove_client(self, client_socket: socket.socket):
        if client_socket in self.clients:
            del self.clients[client_socket]

    def send_message(self, client_identifier: socket.socket, message: str) -> bool:
        if client_identifier in self.clients:
            return self.clients[client_identifier].send_message(message)
        return False