import json
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum

class MessageType(Enum):
    """Types of messages supported in the chat"""
    CONNECT = "connect"
    DISCONNECT = "disconnect" 
    MESSAGE = "message"
    STATUS = "status"
    ERROR = "error"

@dataclass
class ChatMessage:
    """Message protocol for chat application - Compatible with server"""
    type: MessageType  # Use 'type' instead of 'message_type'
    content: str
    timestamp: float
    username: Optional[str] = None
    version: str = "1.0"  # Add version field
    
    def to_json(self) -> str:
        """Convert message to JSON string that matches server format"""
        return json.dumps({
            "type": self.type.value,  # Use .value for Enum
            "content": self.content,
            "timestamp": self.timestamp,
            "username": self.username,
            "version": self.version
        })
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ChatMessage':
        """Create message from JSON string"""
        try:
            data = json.loads(json_str)
            
            # Convert string type to MessageType enum
            message_type = MessageType(data.get("type", "message"))
            
            return cls(
                type=message_type,
                content=data.get("content", ""),
                timestamp=data.get("timestamp", time.time()),
                username=data.get("username"),
                version=data.get("version", "1.0")
            )
        except (json.JSONDecodeError, ValueError, KeyError):
            # Return error message if parsing fails
            return cls(
                type=MessageType.ERROR,
                content="Invalid message format",
                timestamp=time.time()
            )
    
    @classmethod
    def create_text_message(cls, content: str, username: str = None) -> 'ChatMessage':
        """Create a text message"""
        return cls(
            type=MessageType.MESSAGE,
            content=content,
            timestamp=time.time(),
            username=username,
            version="1.0"
        )
    
    @classmethod
    def create_connect_message(cls, username: str = None) -> 'ChatMessage':
        """Create a connection message"""
        return cls(
            type=MessageType.CONNECT,
            content=f"User {username} connected",
            timestamp=time.time(),
            username=username,
            version="1.0"
        )
    
    @classmethod
    def create_disconnect_message(cls, username: str = None) -> 'ChatMessage':
        """Create a disconnect message"""
        return cls(
            type=MessageType.DISCONNECT,
            content=f"User {username} disconnected",
            timestamp=time.time(),
            username=username,
            version="1.0"
        )
    
    @classmethod
    def create_status_message(cls, content: str, username: str = None) -> 'ChatMessage':
        """Create a status message"""
        return cls(
            type=MessageType.STATUS,
            content=content,
            timestamp=time.time(),
            username=username,
            version="1.0"
        )
    
    @classmethod
    def create_error_message(cls, content: str, username: str = None) -> 'ChatMessage':
        """Create an error message"""
        return cls(
            type=MessageType.ERROR,
            content=content,
            timestamp=time.time(),
            username=username,
            version="1.0"
        )