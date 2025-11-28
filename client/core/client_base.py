from abc import ABC, abstractmethod
import logging

class ClientBase(ABC):
    """Abstract base class for chat clients"""
    
    def __init__(self, host, port, buffer_size=4096, encoding="utf-8", timeout=10):
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.encoding = encoding
        self.timeout = timeout
        self.is_connected = False
        self.logger = logging.getLogger(__name__)
    
    @abstractmethod
    def connect(self):
        """Establish connection to server"""
        pass
    
    @abstractmethod
    def send_message(self, message):
        """Send message to server"""
        pass
    
    @abstractmethod
    def receive_message(self):
        """Receive message from server"""
        pass
    
    @abstractmethod
    def disconnect(self):
        """Close connection"""
        pass
    
    def is_connected(self):
        """Check if client is connected"""
        return self.is_connected