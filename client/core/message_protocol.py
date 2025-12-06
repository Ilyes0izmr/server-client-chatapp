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
    TEST = "test"
    ACK = "ack"

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
        """Create message from JSON string - handles reliable messages"""
        try:
            data = json.loads(json_str)
            
            # Convert string type to MessageType enum
            message_type = MessageType(data.get("type", "message"))
            content = data.get("content", "")
            username = data.get("username")
            
            # If it's a MESSAGE type, check if it has sequence data
            if message_type == MessageType.MESSAGE:
                try:
                    msg_data = json.loads(content)
                    if "sequence" in msg_data and "data" in msg_data:
                        # This is a reliable message, extract the actual content
                        content = msg_data.get("data", "")
                except (json.JSONDecodeError, TypeError):
                    # Not a reliable message, use content as-is
                    pass
            
            return cls(
                type=message_type,
                content=content,
                timestamp=data.get("timestamp", time.time()),
                username=username,
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
    
    @classmethod
    def create_ack_message(cls, sequence: int, test_id: str = None) -> 'ChatMessage':
        """Create an acknowledgement message"""
        content = json.dumps({"sequence": sequence})
        if test_id:
            content = json.dumps({"sequence": sequence, "test_id": test_id})
        
        return cls(
            type=MessageType.ACK,
            content=content,
            timestamp=time.time(),
            username="server",  # Server sends ACKs
            version="1.0"
        )

    # Add this method to ChatMessage class
    @classmethod
    def create_reliable_message(cls, sequence: int, content: str, 
                            username: str = None, test_id: str = None) -> 'ChatMessage':
        """Create a reliable message with sequence number (still MESSAGE type)"""
        enhanced_content = json.dumps({
            "sequence": sequence,
            "data": content,
            "test_id": test_id
        })
        
        return cls(
            type=MessageType.MESSAGE,  # Still regular MESSAGE type
            content=enhanced_content,
            timestamp=time.time(),
            username=username,
            version="1.0"
        )