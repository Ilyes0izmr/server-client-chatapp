import socket
import threading
import logging
from typing import Optional, List, Dict
from PyQt6.QtCore import QObject, pyqtSignal
from server.core.client_handler import ClientHandler
from server.core.message_protocol import MessageType, create_message

## the main server class where it manages client connections and messaging 
class TCPServer(QObject):

    """
        Signals to communicate with the UI (for thread safety)
        1) client_connected_signal: fires a signal wehn a new client connects 
        2) client_disconnected_signal: fires a signal when a client disconnects
        3) message_received_signal: fires a signal when a message is received from a client
        this are used later by the ui to update the interface . . . .
    """
    client_connected_signal = pyqtSignal(object)         
    client_disconnected_signal = pyqtSignal(object)  
    message_received_signal = pyqtSignal(object, str)
    
    """ 
        Initialize the TCP server contructor with host and port
    """
    def __init__(self, host: str = 'localhost', port: int = 5000):
        super().__init__()
        self.host = host
        self.port = port
        self.server_socket: Optional[socket.socket] = None
        self.is_running = False  
        self.clients: Dict[int, ClientHandler] = {}
        self.client_counter = 0 
        self.logger = logging.getLogger(__name__) 
        self.accept_thread: Optional[threading.Thread] = None ## speacial therad to accept conetcion to the pgm dont ffreeze 
    
    """
        start the TCP server and begin accepting connections
    """
    def start_server(self) -> bool:
        try:
            # Crreate TCP socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #allow it to reuse the address
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Bind and listen
            self.server_socket.bind(('0.0.0.0', self.port))
            self.server_socket.listen(5)
            # Set running flag
            self.is_running = True

            #make the accept thread call the accept connection methode so we avoid blocking the main thread (main page)
            self.accept_thread = threading.Thread(target=self._accept_connections)
            self.accept_thread.daemon = True # exit automatically when exiting the main pgm
            self.accept_thread.start() # start this thread
            
            # Log server start
            self.logger.info(f"Server started on {self.host}:{self.port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            return False
    

    """
        fire new thread for each client 
    """
    def _accept_connections(self):
        while self.is_running: # we keep litening for new connections in this thread
            try:
                client_socket, client_address = self.server_socket.accept() # blocking call
                self.client_counter += 1 # increment client id counter
                
                client_handler = ClientHandler(
                    client_socket, 
                    client_address, 
                    self.client_counter,
                    self
                )
                
                # store the clinet and its hundelr
                self.clients[self.client_counter] = client_handler
                #create new thread that mangaed comunication with this client
                client_handler.start()
                 
                self.logger.info(f"New client connected: {client_address}")
                
            except Exception as e:
                if self.is_running:
                    self.logger.error(f"Error accepting connection: {e}")
    
    def notify_client_connected(self, client_handler: ClientHandler):
        """Notify UI about new client"""
        self.client_connected_signal.emit(client_handler)
    
    def notify_client_disconnected(self, client_handler: ClientHandler):
        """Notify UI about client disconnect"""
        for client_id, handler in list(self.clients.items()):
            if handler == client_handler:
                del self.clients[client_id]
                break
        self.client_disconnected_signal.emit(client_handler)
    
    def notify_message_received(self, client_handler: ClientHandler, message: str):
        """Notify UI about received message"""
        self.message_received_signal.emit(client_handler, message)
    
    
    """ 
        send message to the client with the given id
    """
    def send_message_to_client(self, client_id: int, message: str):
        client = self.clients.get(client_id)  #search for cleint
        if client:
            return client.send_message(message) # send msg to him if he exist 
        return False
    

    #TODO: implement this later                                                                                    
    def broadcast_message(self, message: str):
        """Send message to all connected clients"""
        success_count = 0
        for client_id, client in list(self.clients.items()):
            if client.send_message(message):
                success_count += 1
        return success_count
    
    def get_connected_clients(self) -> List[ClientHandler]:
        """Get list of connected clients"""
        return list(self.clients.values())
    

    """
        stop the server and close all connections
    """
    def stop_server(self) -> bool:
        try:
            self.is_running = False
            
            for client in list(self.clients.values()):
                client.is_running = False
                try:
                    client.client_socket.close()
                except:
                    pass
            
            self.clients.clear()
            
            if self.server_socket:
                self.server_socket.close()
                self.server_socket = None
            
            self.logger.info("Server stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping server: {e}")
            return False
    
    #TODO: improve this later                                                                                      
    def get_server_status(self) -> str:
        """Get current server status"""
        if self.is_running:
            return f"Running on {self.host}:{self.port} - Clients: {len(self.clients)}"
        return "Stopped"