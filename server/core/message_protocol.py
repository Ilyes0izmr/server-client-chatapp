import json
import time
from typing import Dict, Any, Optional, Tuple
from enum import Enum

class MessageType(Enum):
    """Types of messages supported in the chat"""
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    MESSAGE = "message"
    STATUS = "status"
    ERROR = "error"
    TEST = "test"
    ACK = "ack"  # ADD THIS

class MessageProtocol:
    """Protocol for encoding and decoding chat messages."""
    
    @staticmethod
    def encode_message(message_type: MessageType, content: str, username: str) -> str:
        """Encode a message into JSON string format"""
        message_data = {
            "type": message_type.value,  # Use .value instead of .name.lower()
            "content": content,
            "username": username,
            "timestamp": time.time(),
            "version": "1.0"
        }
        
        return json.dumps(message_data)
    
    @staticmethod
    def create_ack_message(sequence: int, test_id: str = None) -> str:
        """Create an acknowledgement message"""
        content = json.dumps({"sequence": sequence})
        if test_id:
            content = json.dumps({"sequence": sequence, "test_id": test_id})
        
        return MessageProtocol.encode_message(
            MessageType.ACK,
            content,
            "server"
        )
    
    @staticmethod
    def create_reliable_message(sequence: int, content: str, username: str) -> str:
        """Create a reliable message with sequence number"""
        enhanced_content = json.dumps({
            "sequence": sequence,
            "data": content
        })
        
        return MessageProtocol.encode_message(
            MessageType.MESSAGE,
            enhanced_content,
            username
        )
    
    @staticmethod
    def decode_message(message_str: str):
        """Decode a message string into (message_type, content, sender)"""
        try:
            # Clean up message string if needed
            if not message_str.startswith('{'):
                start_idx = message_str.find('{')
                if start_idx != -1:
                    message_str = message_str[start_idx:]
            
            data = json.loads(message_str)
            
            # Extract fields
            message_type_str = data.get('type', '')
            content = data.get('content', '')
            sender = data.get('username', '')
            
            # Convert string type to MessageType enum
            message_type_map = {
                'connect': MessageType.CONNECT,
                'message': MessageType.MESSAGE,
                'disconnect': MessageType.DISCONNECT,
                'test': MessageType.TEST,
                'status': MessageType.STATUS,
                'error': MessageType.ERROR,
                'ack': MessageType.ACK  # ADD THIS
            }
            
            message_type = message_type_map.get(message_type_str, MessageType.STATUS)
            
            return message_type, content, sender
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            return None, "", ""
        except Exception as e:
            print(f"❌ Error decoding message: {e}")
            return None, "", ""
    
    @staticmethod
    def extract_reliable_content(content: str) -> Tuple[Optional[int], str, Optional[str]]:
        """Extract sequence number and actual content from reliable message"""
        try:
            data = json.loads(content)
            if "sequence" in data and "data" in data:
                return data.get("sequence"), data.get("data"), data.get("test_id")
        except (json.JSONDecodeError, TypeError):
            pass
        return None, content, None