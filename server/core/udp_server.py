import socket
import threading
import time
from typing import Dict, Any, Tuple, Optional
from server.core.server_base import ServerBase, ServerProtocol
from server.core.message_protocol import MessageType, create_message, parse_message
from server.utils.logger import get_logger


class UDPServer(ServerBase):
    """
    UDP server implementation for the chat application.
    Handles connectionless communication with multiple clients.
    """

    def __init__(self, host: str = 'localhost', port: int = 5050):
        """
        Initialize the UDP server.
        
        Args:
            host: Host address to bind to
            port: Port number to listen on
        """
        super().__init__(host, port)
        self.logger = get_logger(__name__)
        
        # UDP-specific attributes
        self.clients: Dict[Tuple[str, int], Dict] = {}  # (ip, port) -> client_info
        self.client_last_seen: Dict[Tuple[str, int], float] = {}
        
        # Thread safety
        self._lock = threading.RLock()
        
        # UDP uses a different thread structure than TCP
        self.receive_thread: Optional[threading.Thread] = None
        self.cleanup_thread: Optional[threading.Thread] = None

    def start_server(self) -> bool:
        """
        Start the UDP server and begin listening for datagrams.
        
        Returns:
            bool: True if server started successfully, False otherwise
        """
        try:
            if self.is_running:
                self._notify_status("UDP server is already running", False)
                return False
            
            # Create UDP socket using base class method
            if not self._create_socket(socket.AF_INET, socket.SOCK_DGRAM):
                return False
            
            # Bind socket using base class method
            if not self._bind_socket():
                return False
            
            self.is_running = True
            self.stop_event.clear()
            
            # Start receiving thread
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()
            
            # Start client cleanup thread
            self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
            self.cleanup_thread.start()
            
            self._notify_status(f"UDP server started on {self.host}:{self.port}", False)
            self.logger.info(f"UDP server started on {self.host}:{self.port}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to start UDP server: {e}"
            self._notify_status(error_msg, True)
            self.logger.error(error_msg)
            self.stop_server()
            return False

    def stop_server(self) -> bool:
        """
        Stop the UDP server and clean up resources.
        
        Returns:
            bool: True if server stopped successfully, False otherwise
        """
        try:
            self.is_running = False
            self.stop_event.set()
            
            if self.socket:
                self.socket.close()
                self.socket = None
            
            # Clear client data and notify about disconnections
            with self._lock:
                disconnected_clients = list(self.clients.keys())
                self.clients.clear()
                self.client_last_seen.clear()
            
            # Notify about disconnected clients
            for client_addr in disconnected_clients:
                client_identifier = f"{client_addr[0]}:{client_addr[1]}"
                self._notify_status(f"Client disconnected: {client_identifier}", False)
            
            self._notify_status("UDP server stopped", False)
            self.logger.info("UDP server stopped")
            return True
            
        except Exception as e:
            error_msg = f"Error stopping UDP server: {e}"
            self._notify_status(error_msg, True)
            self.logger.error(error_msg)
            return False

    def send_message(self, client_identifier: Any, message: str) -> bool:
        """
        Send a message to a specific client.
        
        Args:
            client_identifier: Client identifier in format "ip:port"
            message: Message content to send
            
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        try:
            # Parse client identifier - format is "ip:port"
            if isinstance(client_identifier, str):
                ip, port_str = client_identifier.split(':')
                port = int(port_str)
                client_addr = (ip, port)
            else:
                # Assume it's already a tuple (ip, port)
                client_addr = client_identifier
            
            with self._lock:
                if client_addr not in self.clients:
                    self.logger.warning(f"Client {client_identifier} not found")
                    return False
            
            # Create message packet using your message protocol
            message_data = create_message(
                MessageType.MESSAGE,
                message,
                "server"
            ).encode('utf-8')
            
            # Send datagram
            self.socket.sendto(message_data, client_addr)
            self.logger.debug(f"Sent message to {client_identifier}: {message}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to send message to {client_identifier}: {e}"
            self.logger.error(error_msg)
            return False

    def broadcast_message(self, message: str, exclude_client: Any = None) -> bool:
        """
        Broadcast a message to all connected clients.
        
        Args:
            message: Message content to broadcast
            exclude_client: Client identifier to exclude from broadcast
            
        Returns:
            bool: True if broadcast was successful for all clients, False if any failed
        """
        try:
            with self._lock:
                clients_to_message = list(self.clients.keys())
            
            success = True
            for client_addr in clients_to_message:
                client_identifier = f"{client_addr[0]}:{client_addr[1]}"
                
                # Skip excluded client
                if exclude_client and client_identifier == exclude_client:
                    continue
                
                if not self.send_message(client_identifier, message):
                    success = False
            
            if success:
                self.logger.debug(f"Broadcast message to {len(clients_to_message)} clients: {message}")
            else:
                self.logger.warning("Some clients failed to receive broadcast message")
                
            return success
            
        except Exception as e:
            error_msg = f"Failed to broadcast message: {e}"
            self.logger.error(error_msg)
            return False

    def handle_client_connection(self, *args, **kwargs):
        """
        Handle incoming UDP datagrams.
        
        Note: For UDP, this is called from the receive loop for each datagram.
        Unlike TCP, UDP doesn't have persistent connections, so we handle each
        datagram individually.
        """
        # For UDP, client connections are handled in _receive_loop
        # This method is kept for interface compatibility
        pass

    def _receive_loop(self):
        """
        Main loop for receiving UDP datagrams from clients.
        
        Runs in a separate thread and continuously listens for incoming datagrams.
        When a datagram is received, it processes the data and updates client activity.
        """
        buffer_size = 4096  # Maximum datagram size
        
        while self.is_running and self.socket and not self.stop_event.is_set():
            try:
                # Receive datagram - this blocks until data is available
                data, client_addr = self.socket.recvfrom(buffer_size)
                
                if not data:
                    continue
                
                # Update client activity
                self._update_client_activity(client_addr)
                
                # Process the received data
                self._handle_received_data(data, client_addr)
                
            except socket.timeout:
                continue
            except OSError as e:
                if self.is_running and not self.stop_event.is_set():
                    self.logger.error(f"Error receiving UDP data: {e}")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error in receive loop: {e}")

    def _handle_received_data(self, data: bytes, client_addr: Tuple[str, int]):
        """
        Handle received UDP datagram data.
        
        Args:
            data: Raw bytes received from the client
            client_addr: Tuple of (IP, port) identifying the client
        """
        try:
            # Parse message using your message protocol
            message_str = data.decode('utf-8')
            message = parse_message(message_str)
            
            if not message:
                self.logger.warning(f"Invalid message format from {client_addr}")
                return
            
            message_type = message.get('type')
            content = message.get('content', '')
            sender = message.get('sender', 'unknown')
            
            client_identifier = f"{client_addr[0]}:{client_addr[1]}"
            
            # Route to appropriate handler based on message type
            if message_type == MessageType.CONNECT.value:
                self._handle_client_connect(client_addr, content)
            elif message_type == MessageType.DISCONNECT.value:
                self._handle_client_disconnect(client_addr)
            elif message_type == MessageType.MESSAGE.value:
                self._handle_chat_message(client_addr, content, sender)
            elif message_type == MessageType.STATUS.value:
                self._handle_status_message(client_addr, content)
            else:
                self.logger.warning(f"Unknown message type '{message_type}' from {client_identifier}")
                
        except Exception as e:
            self.logger.error(f"Error handling received data from {client_addr}: {e}")

    def _handle_client_connect(self, client_addr: Tuple[str, int], client_name: str):
        """
        Handle new client connection request.
        
        Args:
            client_addr: Tuple of (IP, port) identifying the client
            client_name: Name provided by the client during connection
        """
        client_identifier = f"{client_addr[0]}:{client_addr[1]}"
        
        with self._lock:
            if client_addr not in self.clients:
                self.clients[client_addr] = {
                    'name': client_name or f"Client{len(self.clients) + 1}",
                    'connected_at': time.time(),
                    'address': client_addr
                }
                self.client_last_seen[client_addr] = time.time()
        
        self.logger.info(f"Client connected: {client_identifier} ({client_name})")
        self._notify_status(f"Client connected: {client_identifier}", False)
        
        # Notify message callback about connection
        client_info = {
            'identifier': client_identifier,
            'name': client_name,
            'address': client_addr,
            'connected_at': time.time()
        }
        self._notify_message(client_info, f"{client_name} connected")
        
        # Send welcome message using your message protocol
        welcome_msg = create_message(
            MessageType.STATUS,
            f"Welcome to the chat server, {client_name}!",
            "server"
        ).encode('utf-8')
        self.socket.sendto(welcome_msg, client_addr)

    def _handle_client_disconnect(self, client_addr: Tuple[str, int]):
        """
        Handle client disconnection request.
        
        Args:
            client_addr: Tuple of (IP, port) identifying the client
        """
        client_identifier = f"{client_addr[0]}:{client_addr[1]}"
        
        with self._lock:
            client_info = self.clients.pop(client_addr, None)
            self.client_last_seen.pop(client_addr, None)
        
        if client_info:
            client_name = client_info.get('name', 'Unknown')
            self.logger.info(f"Client disconnected: {client_identifier}")
            self._notify_status(f"Client disconnected: {client_identifier}", False)
            
            # Notify message callback about disconnection
            client_info['identifier'] = client_identifier
            self._notify_message(client_info, f"{client_name} disconnected")

    def _handle_chat_message(self, client_addr: Tuple[str, int], content: str, sender: str):
        """
        Handle incoming chat message from client.
        
        Args:
            client_addr: Tuple of (IP, port) identifying the client
            content: The actual message content
            sender: Name of the sender
        """
        client_identifier = f"{client_addr[0]}:{client_addr[1]}"
        
        with self._lock:
            client_info = self.clients.get(client_addr, {})
            client_name = client_info.get('name', 'Unknown')
        
        self.logger.debug(f"Received chat message from {client_identifier}: {content}")
        
        # Notify message callback about the received message
        full_client_info = {
            'identifier': client_identifier,
            'name': client_name,
            'address': client_addr,
            **client_info
        }
        self._notify_message(full_client_info, content)
        
        # Send delivery confirmation
        echo_msg = create_message(
            MessageType.STATUS,
            "Message delivered",
            "server"
        ).encode('utf-8')
        self.socket.sendto(echo_msg, client_addr)

    def _handle_status_message(self, client_addr: Tuple[str, int], content: str):
        """
        Handle status message from client (can be used for heartbeats).
        
        Args:
            client_addr: Tuple of (IP, port) identifying the client
            content: Status content
        """
        self._update_client_activity(client_addr)
        self.logger.debug(f"Status message from {client_addr}: {content}")

    def _update_client_activity(self, client_addr: Tuple[str, int]):
        """
        Update client's last seen timestamp.
        
        Args:
            client_addr: Tuple of (IP, port) identifying the client
        """
        with self._lock:
            self.client_last_seen[client_addr] = time.time()

    def _cleanup_loop(self):
        """
        Background thread to clean up inactive clients.
        
        Periodically checks for clients that haven't been active recently
        and removes them from the connected clients list.
        """
        CLIENT_TIMEOUT = 30  # seconds
        
        while self.is_running and not self.stop_event.is_set():
            try:
                current_time = time.time()
                disconnected_clients = []
                
                # Identify clients that haven't been seen recently
                with self._lock:
                    for client_addr, last_seen in self.client_last_seen.items():
                        if current_time - last_seen > CLIENT_TIMEOUT:
                            disconnected_clients.append(client_addr)
                
                # Remove timed out clients
                for client_addr in disconnected_clients:
                    self._handle_client_disconnect(client_addr)
                    self.logger.info(f"Client {client_addr} timed out")
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                self.logger.error(f"Error in client cleanup loop: {e}")
                time.sleep(5)

    def get_client_count(self) -> int:
        """
        Get number of connected clients.
        
        Returns:
            int: Number of connected clients
        """
        with self._lock:
            return len(self.clients)

    def get_clients_info(self) -> Dict[Any, Dict]:
        """
        Get information about all connected clients.
        
        Returns:
            Dict: Dictionary of client information
        """
        with self._lock:
            clients_info = {}
            for client_addr, client_info in self.clients.items():
                client_identifier = f"{client_addr[0]}:{client_addr[1]}"
                clients_info[client_identifier] = {
                    'identifier': client_identifier,
                    'name': client_info.get('name', 'Unknown'),
                    'address': client_addr,
                    'connected_at': client_info.get('connected_at', 0),
                    'last_activity': self.client_last_seen.get(client_addr, 0)
                }
            return clients_info

    @property
    def protocol(self) -> ServerProtocol:
        """
        Return the server protocol type.
        
        Returns:
            ServerProtocol: UDP protocol enum value
        """
        return ServerProtocol.UDP

    def is_server_running(self) -> bool:
        """
        Check if server is running.
        
        Returns:
            bool: True if server is running, False otherwise
        """
        return self.is_running

    def get_server_info(self) -> Dict[str, Any]:
        """
        Get server information.
        
        Returns:
            Dict: Server information dictionary
        """
        return {
            'host': self.host,
            'port': self.port,
            'protocol': self.protocol.value,
            'running': self.is_running,
            'clients_count': self.get_client_count()
        }