import json
import time
from typing import Dict, Any, Optional
from enum import Enum

class MessageType(Enum):
    """Types of messages supported in the chat"""
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    MESSAGE = "message"
    STATUS = "status"
    ERROR = "error"

class MessageProtocol:
    """Protocol for encoding and decoding chat messages."""
    
    @staticmethod
    def encode_message(message_type: MessageType, content: str, username: str = "", timestamp: Optional[float] = None) -> str:
        """
        Encode a message into the protocol format.
        """
        message_data = {
            'type': message_type.value,
            'content': content,
            'username': username,
            'timestamp': timestamp if timestamp is not None else time.time(),
            'version': '1.0'
        }
        
        return json.dumps(message_data)
    
    @staticmethod
    def decode_message(message_str: str) -> Optional[Dict[str, Any]]:
        """
        Decode a message from the protocol format.
        """
        try:
            message_data = json.loads(message_str)
            
            # validate required fields
            if not all(key in message_data for key in ['type', 'content', 'timestamp']):
                return None
            
            # validate message type
            valid_types = [msg_type.value for msg_type in MessageType]
            if message_data['type'] not in valid_types:
                return None
            
            return message_data
            
        except (json.JSONDecodeError, ValueError):
            return None