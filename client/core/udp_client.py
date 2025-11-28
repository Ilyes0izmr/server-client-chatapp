import socket
import threading
import time
from typing import Callable, Optional
from .client_base import ClientBase
from .message_protocol import ChatMessage, MessageType

class UDPClient(ClientBase):
    """UDP client implementation"""
    
    def __init__(self, host, port, buffer_size=4096, encoding="utf-8", timeout=10):
        super().__init__(host, port, buffer_size, encoding, timeout)
        self.socket = None
        self.receive_callback = None
        self.receive_thread = None
        self.should_listen = False
        self.server_address = (host, port)
        self.username = None
        self.sequence_number = 0  # For message ordering
        self.pending_acknowledgements = {}  # For reliable UDP
    
    def connect(self) -> bool:
        """Setup UDP socket (UDP is connectionless)"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.settimeout(1.0)  # Shorter timeout for UDP
            self.is_connected = True
            self.logger.info(f"UDP client ready to send to {self.host}:{self.port}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup UDP client: {e}")
            self.is_connected = False
            return False
    
    def send_message(self, message: str, username: str = None) -> bool:
        """Send message to server via UDP"""
        if not self.is_connected or not self.socket:
            self.logger.error("UDP client not initialized")
            return False
        
        try:
            chat_message = ChatMessage.create_text_message(message, username)
            message_data = chat_message.to_json().encode(self.encoding)
            
            # For UDP, we just send the datagram
            self.socket.sendto(message_data, self.server_address)
            self.logger.debug(f"UDP message sent: {message}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send UDP message: {e}")
            return False
    
    def send_connect_message(self, username: str) -> bool:
        """Send connection message to server via UDP"""
        if not self.is_connected or not self.socket:
            return False
        
        try:
            self.username = username
            chat_message = ChatMessage.create_connect_message(username)
            message_data = chat_message.to_json().encode(self.encoding)
            
            self.socket.sendto(message_data, self.server_address)
            self.logger.info(f"Sent UDP connect message for user: {username}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send UDP connect message: {e}")
            return False
    
    def send_disconnect_message(self) -> bool:
        """Send disconnect message to server via UDP"""
        if not self.is_connected or not self.socket:
            return False
        
        try:
            chat_message = ChatMessage.create_disconnect_message(self.username)
            message_data = chat_message.to_json().encode(self.encoding)
            
            self.socket.sendto(message_data, self.server_address)
            self.logger.info("Sent UDP disconnect message")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send UDP disconnect message: {e}")
            return False
    
    def receive_message(self) -> Optional[ChatMessage]:
        """Receive a single message from server via UDP"""
        if not self.is_connected or not self.socket:
            return None
        
        try:
            data, addr = self.socket.recvfrom(self.buffer_size)
            if data:
                message_str = data.decode(self.encoding)
                chat_message = ChatMessage.from_json(message_str)
                
                # If server didn't set username, use the address
                if not chat_message.username and chat_message.type == MessageType.MESSAGE:
                    chat_message.username = f"Server@{addr[0]}"
                
                return chat_message
        except socket.timeout:
            # Expected for UDP - no data available
            pass
        except Exception as e:
            self.logger.error(f"Error receiving UDP message: {e}")
        
        return None
    
    def start_listening(self, callback: Callable[[ChatMessage], None]):
        """Start background thread to listen for UDP messages"""
        self.receive_callback = callback
        self.should_listen = True
        self.receive_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.receive_thread.start()
    
    def _listen_loop(self):
        """Background thread loop for receiving UDP messages"""
        while self.should_listen and self.is_connected:
            try:
                message = self.receive_message()
                if message and self.receive_callback:
                    self.receive_callback(message)
            except Exception as e:
                self.logger.error(f"Error in UDP listen loop: {e}")
                if not self.is_connected:
                    break
            time.sleep(0.05)  # Shorter delay for UDP
    
    def stop_listening(self):
        """Stop the background listening thread"""
        self.should_listen = False
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=1.0)
    
    def disconnect(self):
        """Disconnect UDP client"""
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
        self.logger.info("UDP client disconnected")