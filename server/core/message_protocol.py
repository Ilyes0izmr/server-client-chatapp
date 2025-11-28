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
    def encode_message(message_type: MessageType, content: str, username: str) -> str:
        """Encode a message into JSON string format"""
        import json
        import time
        
        message_data = {
            "type": message_type.name.lower(),  # "message" or "status"
            "content": content,
            "username": username,
            "timestamp": time.time(),
            "version": "1.0"
        }
        
        return json.dumps(message_data)
        
    @staticmethod
    def decode_message(message_str: str):
        """Decode a message string into (message_type, content, sender)"""
        try:
            print(f"🔍 MESSAGE PROTOCOL DEBUG: Decoding message: {message_str}")
            
            # Check if the message starts with unexpected characters
            if not message_str.startswith('{'):
                # Try to find the JSON part
                start_idx = message_str.find('{')
                if start_idx != -1:
                    message_str = message_str[start_idx:]
                    print(f"🔍 MESSAGE PROTOCOL DEBUG: Fixed message string: {message_str}")
                else:
                    print(f"❌ MESSAGE PROTOCOL DEBUG: No JSON found in message: {message_str}")
                    return None, "", ""
            
            # Parse JSON
            import json
            data = json.loads(message_str)
            
            # Extract fields with defaults
            message_type_str = data.get('type', '')
            content = data.get('content', '')
            sender = data.get('username', '')
            
            # Convert string type to MessageType enum
            if message_type_str == 'connect':
                message_type = MessageType.STATUS
            elif message_type_str == 'message':
                message_type = MessageType.MESSAGE
            elif message_type_str == 'disconnect':
                message_type = MessageType.STATUS
            else:
                message_type = MessageType.STATUS  # Default to STATUS
            
            print(f"🔍 MESSAGE PROTOCOL DEBUG: Decoded - type: {message_type}, content: '{content}', sender: '{sender}'")
            return message_type, content, sender
            
        except json.JSONDecodeError as e:
            print(f"❌ MESSAGE PROTOCOL DEBUG: JSON decode error: {e}")
            return None, "", ""
        except Exception as e:
            print(f"❌ MESSAGE PROTOCOL DEBUG: Error decoding message: {e}")
            return None, "", ""