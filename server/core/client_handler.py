import socket
import threading
from typing import Callable
from server.core.message_protocol import MessageProtocol, MessageType

class ClientHandler:
    """Handles individual TCP client connections"""

    def __init__(self, client_socket: socket.socket, client_address: tuple, 
                 remove_callback: Callable, notify_callback: Callable):
        self.client_socket = client_socket
        self.client_address = client_address
        self.remove_callback = remove_callback
        self.notify_callback = notify_callback
        self.is_running = True
        
        self.client_id = f"{client_address[0]}:{client_address[1]}"
        self.username = f"User_{hash(client_address) % 10000}"
        
        self.thread = threading.Thread(target=self._handle_client, daemon=True)

    def start(self):
        self.thread.start()

    def stop(self):
        self.is_running = False
        try:
            self.client_socket.close()
        except:
            pass

    def _handle_client(self):
        try:
            welcome_msg = MessageProtocol.encode_message(
                MessageType.STATUS,
                f"Welcome! Your username: {self.username}",
                "System"
            )
            self.client_socket.send(welcome_msg.encode('utf-8'))
            
            self.notify_callback(f"Client connected: {self.client_id}")

            while self.is_running:
                data = self.client_socket.recv(1024)
                if not data:
                    break
                self._process_message(data.decode('utf-8'))
                
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            self.notify_callback(f"Client disconnected: {self.client_id}")
        except Exception as e:
            if self.is_running:
                self.notify_callback(f"Error: {e}", True)
        finally:
            self._cleanup()

    def _process_message(self, message_str: str):
        message = MessageProtocol.decode_message(message_str)
        if not message:
            return
        
        if message.get('type') == MessageType.MESSAGE.value:
            display_message = f"{self.username}: {message.get('content', '')}"
            self.notify_callback(display_message)

    def _cleanup(self):
        self.remove_callback(self.client_socket)
        try:
            self.client_socket.close()
        except:
            pass
        self.notify_callback(f"Client disconnected: {self.client_id}")

    def send_message(self, message: str) -> bool:
        try:
            self.client_socket.send(message.encode('utf-8'))
            return True
        except:
            self._cleanup()
            return False