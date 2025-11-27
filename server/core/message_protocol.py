import json
from enum import Enum

#TODO: i need to improve this later, maybe add more message types
class MessageType(Enum):
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    MESSAGE = "message"
    BROADCAST = "broadcast"
    STATUS = "status"

def create_message(msg_type: MessageType, content: str, sender: str = "Server"):
    """Create a JSON message"""
    return json.dumps({
        "type": msg_type.value,
        "content": content,
        "sender": sender
    })

def parse_message(data: str):
    """Parse JSON message"""
    try:
        return json.loads(data)
    except:
        return None