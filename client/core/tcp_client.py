import socket
import threading
import time
from typing import Callable, Optional
from .client_base import ClientBase
from .message_protocol import ChatMessage, MessageType

class TCPClient(ClientBase):
    """TCP client implementation"""
    
    def __init__(self, host, port, buffer_size=4096, encoding="utf-8", timeout=10):
        super().__init__(host, port, buffer_size, encoding, timeout)
        self.socket = None
        self.receive_callback = None
        self.receive_thread = None
        self.should_listen = False
        self.lock = threading.Lock()
        self.username = None
    
    def connect(self) -> bool:
        """Connect to TCP server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.host, self.port))
            self.is_connected = True
            self.logger.info(f"Connected to TCP server at {self.host}:{self.port}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to TCP server: {e}")
            self.is_connected = False
            return False
    
    def send_message(self, message: str, username: str = None) -> bool:
        """Send message to server"""
        if not self.is_connected or not self.socket:
            self.logger.error("Not connected to server")
            return False
        
        try:
            chat_message = ChatMessage.create_text_message(message, username)
            message_data = chat_message.to_json().encode(self.encoding)
            
            # Send message length first (4 bytes)
            message_len = len(message_data)
            self.socket.sendall(message_len.to_bytes(4, byteorder='big'))
            
            # Send actual message
            self.socket.sendall(message_data)
            self.logger.debug(f"Message sent: {message}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            self.is_connected = False
            return False
    
    def send_connect_message(self, username: str) -> bool:
        """Send connection message to server"""
        if not self.is_connected or not self.socket:
            return False
        
        try:
            self.username = username
            chat_message = ChatMessage.create_connect_message(username)
            message_data = chat_message.to_json().encode(self.encoding)
            
            message_len = len(message_data)
            self.socket.sendall(message_len.to_bytes(4, byteorder='big'))
            self.socket.sendall(message_data)
            
            self.logger.info(f"Sent connect message for user: {username}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send connect message: {e}")
            return False
    
    def send_disconnect_message(self) -> bool:
        """Send disconnect message to server"""
        if not self.is_connected or not self.socket:
            return False
        
        try:
            chat_message = ChatMessage.create_disconnect_message(self.username)
            message_data = chat_message.to_json().encode(self.encoding)
            
            message_len = len(message_data)
            self.socket.sendall(message_len.to_bytes(4, byteorder='big'))
            self.socket.sendall(message_data)
            
            self.logger.info("Sent disconnect message")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send disconnect message: {e}")
            return False
    
    def receive_message(self) -> Optional[ChatMessage]:
        """Receive a single message from server"""
        if not self.is_connected or not self.socket:
            return None
        
        try:
            # First receive message length
            length_data = self.socket.recv(4)
            if not length_data:
                self.logger.debug("Server closed connection")
                self.is_connected = False
                return None
            
            message_len = int.from_bytes(length_data, byteorder='big')
            
            # Receive the actual message
            received_data = b""
            while len(received_data) < message_len:
                chunk = self.socket.recv(min(self.buffer_size, message_len - len(received_data)))
                if not chunk:
                    break
                received_data += chunk
            
            if received_data:
                message_str = received_data.decode(self.encoding)
                chat_message = ChatMessage.from_json(message_str)
                return chat_message
            
        except socket.timeout:
            self.logger.debug("Receive timeout")
        except ConnectionResetError:
            self.logger.error("Connection reset by server")
            self.is_connected = False
        except Exception as e:
            self.logger.error(f"Error receiving message: {e}")
            self.is_connected = False
        
        return None
    
    def start_listening(self, callback: Callable[[ChatMessage], None]):
        """Start background thread to listen for messages"""
        self.receive_callback = callback
        self.should_listen = True
        self.receive_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.receive_thread.start()
    
    def _listen_loop(self):
        """Background thread loop for receiving messages"""
        while self.should_listen and self.is_connected:
            try:
                message = self.receive_message()
                if message and self.receive_callback:
                    self.receive_callback(message)
                elif not self.is_connected:
                    break
            except Exception as e:
                self.logger.error(f"Error in listen loop: {e}")
                break
            time.sleep(0.1)
        
        self.logger.debug("Listen loop ended")
    
    def stop_listening(self):
        """Stop the background listening thread"""
        self.should_listen = False
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=1.0)
    
    def disconnect(self):
        """Disconnect from server"""
        if self.is_connected:
            self.send_disconnect_message()
        
        self.stop_listening()
        self.is_connected = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            finally:
                self.socket = None
        self.logger.info("Disconnected from server")