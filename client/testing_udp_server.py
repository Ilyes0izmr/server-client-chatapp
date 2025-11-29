import socket
import threading
import json
import time
import logging
from typing import Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UDPServer:
    """
    UDP Server for testing UDP client functionality
    Handles multiple clients simultaneously
    """
    
    def __init__(self, host='192.168.1.33', port=5051, buffer_size=4096):
        self.host = '192.168.1.33'
        print(f"UDP Server will run on {self.host}:{port}")
        self.port = port
        self.buffer_size = buffer_size
        self.socket = None
        self.clients = {}  # {client_address: {"username": str, "last_seen": float}}
        self.running = False
        self.sequence_number = 0
        
    def start(self):
        """Start the UDP server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind((self.host, self.port))
            self.running = True
            
            logger.info(f"UDP Server started on {self.host}:{self.port}")
            logger.info("Waiting for UDP clients...")
            
            # Start cleanup thread for inactive clients
            cleanup_thread = threading.Thread(target=self._cleanup_clients, daemon=True)
            cleanup_thread.start()
            
            # Main receive loop
            self._receive_loop()
            
        except Exception as e:
            logger.error(f"Failed to start UDP server: {e}")
        finally:
            self.stop()
    
    def _receive_loop(self):
        """Main loop for receiving UDP messages"""
        while self.running:
            try:
                data, client_addr = self.socket.recvfrom(self.buffer_size)
                
                # Handle message in a separate thread
                client_thread = threading.Thread(
                    target=self._handle_client_message,
                    args=(data, client_addr),
                    daemon=True
                )
                client_thread.start()
                
            except socket.timeout:
                continue
            except OSError as e:
                if self.running:
                    logger.error(f"Socket error: {e}")
                break
            except Exception as e:
                logger.error(f"Unexpected error in receive loop: {e}")
    
    def _handle_client_message(self, data: bytes, client_addr: tuple):
        """Handle a message from a client"""
        try:
            message_str = data.decode('utf-8')
            message_data = json.loads(message_str)
            
            message_type = message_data.get('type', 'message')
            content = message_data.get('content', '')
            username = message_data.get('username', 'Unknown')
            timestamp = message_data.get('timestamp', time.time())
            
            # Update client info
            self.clients[client_addr] = {
                "username": username,
                "last_seen": time.time()
            }
            
            logger.info(f"Received {message_type} from {username}@{client_addr}: {content}")
            
            # Handle different message types
            if message_type == 'connect':
                self._handle_connect(client_addr, username, content)
            elif message_type == 'disconnect':
                self._handle_disconnect(client_addr, username, content)
            elif message_type == 'message':
                self._handle_message(client_addr, username, content)
            else:
                self._send_error(client_addr, f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON from {client_addr}")
            self._send_error(client_addr, "Invalid message format")
        except Exception as e:
            logger.error(f"Error handling message from {client_addr}: {e}")
            self._send_error(client_addr, "Server error processing message")
    
    def _handle_connect(self, client_addr: tuple, username: str, content: str):
        """Handle client connection"""
        welcome_msg = f"Welcome {username}! You are connected via UDP. There are {len(self.clients)} clients online."
        
        # Send welcome message
        response = self._create_message(
            message_type="status",
            content=welcome_msg,
            username="Server"
        )
        self._send_to_client(client_addr, response)
        
        # Notify other clients (simulate broadcast)
        self._broadcast_message(
            f"{username} joined the chat",
            exclude_client=client_addr
        )
    
    def _handle_disconnect(self, client_addr: tuple, username: str, content: str):
        """Handle client disconnection"""
        if client_addr in self.clients:
            del self.clients[client_addr]
        
        # Notify other clients
        self._broadcast_message(
            f"{username} left the chat",
            exclude_client=client_addr
        )
        
        logger.info(f"Client {username}@{client_addr} disconnected")
    
    def _handle_message(self, client_addr: tuple, username: str, content: str):
        """Handle regular chat message"""
        # Echo the message back to the sender
        echo_response = self._create_message(
            message_type="message",
            content=f"UDP Echo: {content}",
            username="Server"
        )
        self._send_to_client(client_addr, echo_response)
        
        # Also broadcast to other clients (simulate multi-client chat)
        broadcast_msg = self._create_message(
            message_type="message",
            content=content,
            username=username
        )
        self._broadcast_message_data(broadcast_msg, exclude_client=client_addr)
        
        # Simulate UDP characteristics - occasional packet loss
        import random
        if random.random() < 0.1:  # 10% packet loss simulation
            logger.info(f"Simulated packet loss for message from {username}")
        
        # Simulate out-of-order delivery occasionally
        if random.random() < 0.2:  # 20% chance of delayed response
            threading.Timer(0.5, self._send_delayed_message, [client_addr, content]).start()
    
    def _send_delayed_message(self, client_addr: tuple, original_content: str):
        """Send a delayed message to simulate UDP out-of-order delivery"""
        delayed_msg = self._create_message(
            message_type="message",
            content=f"[DELAYED] You said: {original_content}",
            username="Server"
        )
        self._send_to_client(client_addr, delayed_msg)
    
    def _broadcast_message(self, content: str, exclude_client: tuple = None):
        """Broadcast a message to all connected clients"""
        message_data = self._create_message(
            message_type="status",
            content=content,
            username="Server"
        )
        self._broadcast_message_data(message_data, exclude_client)
    
    def _broadcast_message_data(self, message_data: dict, exclude_client: tuple = None):
        """Broadcast message data to all connected clients"""
        message_json = json.dumps(message_data)
        message_bytes = message_json.encode('utf-8')
        
        for client_addr in list(self.clients.keys()):
            if client_addr != exclude_client:
                try:
                    self.socket.sendto(message_bytes, client_addr)
                except Exception as e:
                    logger.error(f"Failed to send to {client_addr}: {e}")
    
    def _send_to_client(self, client_addr: tuple, message_data: dict):
        """Send a message to a specific client"""
        try:
            message_json = json.dumps(message_data)
            message_bytes = message_json.encode('utf-8')
            self.socket.sendto(message_bytes, client_addr)
        except Exception as e:
            logger.error(f"Failed to send to {client_addr}: {e}")
    
    def _send_error(self, client_addr: tuple, error_message: str):
        """Send an error message to client"""
        error_data = self._create_message(
            message_type="error",
            content=error_message,
            username="Server"
        )
        self._send_to_client(client_addr, error_data)
    
    def _create_message(self, message_type: str, content: str, username: str = "Server") -> Dict[str, Any]:
        """Create a message in the protocol format"""
        return {
            "type": message_type,
            "content": content,
            "username": username,
            "timestamp": time.time(),
            "version": "1.0"
        }
    
    def _cleanup_clients(self):
        """Clean up inactive clients (those who haven't sent messages in a while)"""
        while self.running:
            time.sleep(30)  # Check every 30 seconds
            current_time = time.time()
            inactive_clients = []
            
            for client_addr, client_info in self.clients.items():
                if current_time - client_info["last_seen"] > 60:  # 60 seconds timeout
                    inactive_clients.append(client_addr)
            
            for client_addr in inactive_clients:
                username = self.clients[client_addr]["username"]
                logger.info(f"Removing inactive client: {username}@{client_addr}")
                del self.clients[client_addr]
                
                # Notify about inactive client removal
                self._broadcast_message(
                    f"{username} timed out (inactive)",
                    exclude_client=client_addr
                )
    
    def stop(self):
        """Stop the UDP server"""
        self.running = False
        if self.socket:
            self.socket.close()
            self.socket = None
        logger.info("UDP Server stopped")

def main():
    """Main function to run the UDP test server"""
    import argparse
    
    parser = argparse.ArgumentParser(description='UDP Test Server for Chat App')
    parser.add_argument('--host', default='localhost', help='Server host (default: localhost)')
    parser.add_argument('--port', type=int, default=5051, help='Server port (default: 5051)')
    
    args = parser.parse_args()
    
    server = UDPServer(host=args.host, port=args.port)
    
    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        server.stop()

if __name__ == "__main__":
    main()