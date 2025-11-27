import socket
import threading
import logging
import time
from .message_protocol import MessageType, create_message, parse_message

"""
    class to hundle individual client -> in thread
"""
class ClientHandler(threading.Thread):
    def __init__(self, client_socket: socket.socket, client_address, client_id, server):
        super().__init__()
        self.client_socket = client_socket 
        self.client_address = client_address
        self.client_id = client_id
        self.server = server
        self.client_name = f"Client_{client_id}"
        self.is_running = True                        #the thread life cycle flag
        self.logger = logging.getLogger(__name__)

    """
        Main thread loop to handle client messages
    """
    def run(self):
       
        self.logger.info(f"Client handler started for {self.client_name}")
        
        try:
            while self.is_running: # keep the thread running
                # Receive data from client
                data = self.client_socket.recv(1024).decode('utf-8') #get the message from the clinet
                if not data:
                    break
                    
                # Parse and handle message
                message = parse_message(data)
                if message:
                    self.handle_message(message) #hundle the message based on its type (send it to the server) 
                    
        except Exception as e:
            self.logger.error(f"Error handling client {self.client_name}: {e}")
        finally:
            # close the scket and cleanup
            self.cleanup()
    
    def handle_message(self, message):
        """Handle different types of messages"""
        msg_type = message.get("type")
        content = message.get("content", "")
        sender = message.get("sender", self.client_name)
        
        if msg_type == MessageType.CONNECT.value:
            self.client_name = content if content else self.client_name
            self.server.notify_client_connected(self)
            
        elif msg_type == MessageType.MESSAGE.value:
            self.server.notify_message_received(self, content)
            
        elif msg_type == MessageType.DISCONNECT.value:
            self.is_running = False
    
    """
        send message to this client
    """
    def send_message(self, message: str, sender: str = "Server"):
        """send message to this client"""
        try:
            message_data = create_message(MessageType.MESSAGE, message, sender)
            self.client_socket.send(message_data.encode('utf-8'))
            return True
        except Exception as e:
            self.logger.error(f"Failed to send message to {self.client_name}: {e}")
            return False
    
    def cleanup(self):
        """Cleanup client connection"""
        self.is_running = False
        self.server.notify_client_disconnected(self)  
        try:
            self.client_socket.close()
        except:
            pass
        self.logger.info(f"Client {self.client_name} disconnected")