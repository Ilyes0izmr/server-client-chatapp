import socket
import threading
import logging
import json
from typing import Optional, Callable

class ClientSocket:
    """init socket client """
    def __init__(self):
        self.socket: Optional[socket.socket] = None
        self.is_connected = False
        self.receive_thread: Optional[threading.Thread] = None
        self.logger = logging.getLogger(__name__)
        
        # Callbacks for UI updates
        self.on_message_received: Optional[Callable] = None
        self.on_connection_lost: Optional[Callable] = None  # Server disconnection callback
    
    """Connect to server"""
    def connect(self, host: str, port: int) -> bool:
        """Connect to the server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)  # Set timeout for connection
            self.socket.connect((host, port))
            self.socket.settimeout(None)  
            self.is_connected = True
            
            # Start receiving messages in a separate thread
            self.receive_thread = threading.Thread(target=self._receive_messages)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
            self._send_message("connect", "Client connected")
            
            self.logger.info(f"Connected to {host}:{port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            self.is_connected = False
            return False
    
    def _receive_messages(self):
        """Receive messages from server"""
        while self.is_connected:
            try:
                data = self.socket.recv(1024).decode('utf-8')
                if not data:  # Server closed connection
                    self.logger.info("Server closed the connection")
                    self._handle_connection_lost()
                    break
                    
                message = json.loads(data)
                if self.on_message_received:
                    self.on_message_received(message)
                    
            except ConnectionResetError:
                self.logger.info("Connection reset by server")
                self._handle_connection_lost()
                break
            except ConnectionAbortedError:
                self.logger.info("Connection aborted by server")
                self._handle_connection_lost()
                break
            except Exception as e:
                if self.is_connected:
                    self.logger.error(f"Error receiving message: {e}")
                    self._handle_connection_lost()
                break
    
    def _handle_connection_lost(self):
        """Handle server disconnection"""
        self.is_connected = False
        if self.on_connection_lost:
            self.on_connection_lost() 
    
    def send_message(self, message: str):
        """Send message to server"""
        if self.is_connected and self.socket:
            try:
                self._send_message("message", message)
                return True
            except Exception as e:
                self.logger.error(f"Failed to send message: {e}")
                self._handle_connection_lost()
                return False
        return False
    
    def _send_message(self, msg_type: str, content: str):
        """Send formatted message"""
        message_data = json.dumps({
            "type": msg_type,
            "content": content,
            "sender": "Client"
        })
        self.socket.send(message_data.encode('utf-8'))
    
    def disconnect(self):
        """Disconnect from server"""
        try:
            self.is_connected = False
            if self.socket:
                self._send_message("disconnect", "Client disconnecting")
                self.socket.close()
            self.logger.info("Disconnected from server")
        except Exception as e:
            self.logger.error(f"Error disconnecting: {e}")
    
    def get_connection_status(self) -> str:
        """Get current connection status"""
        if self.is_connected and self.socket:
            return f"Connected - Socket: {self.socket.fileno()}"
        return "Not connected"