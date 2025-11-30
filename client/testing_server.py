import socket
import threading
import json
import time

class SimpleTCPServer:
    def __init__(self, host='192.168.1.33', port=5050):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients = []
    
    def start(self):
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)
        print(f"TCP Server listening on {self.host}:{self.port}")
        
        while True:
            client_socket, address = self.socket.accept()
            print(f"New connection from {address}")
            self.clients.append(client_socket)
            
            # Start a new thread for each client
            thread = threading.Thread(target=self.handle_client, args=(client_socket, address))
            thread.daemon = True
            thread.start()
    
    def create_message(self, content, message_type="text", username="Server"):
        """Create a properly formatted JSON message"""
        return {
            "message_type": message_type,
            "content": content,
            "timestamp": time.time(),
            "username": username,
            "message_id": str(int(time.time() * 1000))
        }
    
    def handle_client(self, client_socket, address):
        while True:
            try:
                # Receive message length
                length_data = client_socket.recv(4)
                if not length_data:
                    break
                
                message_len = int.from_bytes(length_data, byteorder='big')
                
                # Receive message
                received_data = b""
                while len(received_data) < message_len:
                    chunk = client_socket.recv(min(4096, message_len - len(received_data)))
                    if not chunk:
                        break
                    received_data += chunk
                
                if received_data:
                    message_json = received_data.decode('utf-8')
                    print(f"Received: {message_json}")
                    
                    try:
                        # Parse the incoming message
                        message_data = json.loads(message_json)
                        user_message = message_data.get('content', '')
                        username = message_data.get('username', 'Unknown')
                        
                        # Create proper JSON response
                        response_data = self.create_message(
                            f"Echo: {user_message}",
                            "text",
                            "Server"
                        )
                        response_json = json.dumps(response_data)
                        response_bytes = response_json.encode('utf-8')
                        
                        # Send response length first
                        response_len = len(response_bytes)
                        client_socket.sendall(response_len.to_bytes(4, byteorder='big'))
                        
                        # Send actual response
                        client_socket.sendall(response_bytes)
                        print(f"Sent response to {username}")
                        
                    except json.JSONDecodeError:
                        print(f"Invalid JSON from {address}")
                        
            except Exception as e:
                print(f"Error with client {address}: {e}")
                break
        
        client_socket.close()
        if client_socket in self.clients:
            self.clients.remove(client_socket)
        print(f"Client {address} disconnected")

if __name__ == "__main__":
    server = SimpleTCPServer()
    server.start()