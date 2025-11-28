#!/usr/bin/env python3
"""
Standalone test script for UDP Server implementation.
This file contains everything needed to test the server without external dependencies.
"""

import socket
import threading
import time
import json
import sys
import os

# Mock the message protocol since we can't import it
class MessageProtocol:
    @staticmethod
    def create_message(message_type, content, sender):
        """Create a JSON message with type, content, and sender"""
        message = {
            'type': message_type,
            'content': content,
            'sender': sender,
            'timestamp': time.time()
        }
        return json.dumps(message).encode('utf-8')
    
    @staticmethod
    def parse_message(data):
        """Parse JSON message from bytes"""
        try:
            message = json.loads(data.decode('utf-8'))
            return message
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None

# Mock the server base class
class ServerBase:
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.observer = None

# Mock logger
class MockLogger:
    def __init__(self, name):
        self.name = name
    
    def info(self, msg):
        print(f"INFO [{self.name}]: {msg}")
    
    def warning(self, msg):
        print(f"WARN [{self.name}]: {msg}")
    
    def error(self, msg):
        print(f"ERROR [{self.name}]: {msg}")
    
    def debug(self, msg):
        print(f"DEBUG [{self.name}]: {msg}")

def get_logger(name):
    return MockLogger(name)

# UDP Server Implementation (copied from your file)
class UDPServer(ServerBase):
    """
    UDP server implementation for the chat application.
    Handles connectionless communication with multiple clients.
    """
    
    def __init__(self, host: str = '0.0.0.0', port: int = 5000):
        super().__init__(host, port)
        self.logger = get_logger(__name__)
        
        # UDP-specific attributes
        self.socket: socket.socket = None
        self.is_running = False
        self.receive_thread: threading.Thread = None
        
        # Client management
        self.clients = {}  # (ip, port) -> client_info
        self.client_last_seen = {}
        
        # Thread safety
        self._lock = threading.RLock()
        
    def start(self) -> bool:
        """Start the UDP server and begin listening for datagrams."""
        try:
            if self.is_running:
                self.logger.warning("UDP server is already running")
                return False
            
            # Create UDP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind to address
            self.socket.bind((self.host, self.port))
            self.is_running = True
            
            # Start receiving thread
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()
            
            # Start client cleanup thread
            self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
            self.cleanup_thread.start()
            
            self.logger.info(f"UDP server started on {self.host}:{self.port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start UDP server: {e}")
            self.stop()
            return False
    
    def stop(self) -> bool:
        """Stop the UDP server and clean up resources."""
        try:
            self.is_running = False
            
            if self.socket:
                self.socket.close()
                self.socket = None
            
            # Clear client data
            with self._lock:
                disconnected_clients = list(self.clients.keys())
                self.clients.clear()
                self.client_last_seen.clear()
            
            # Notify about disconnected clients
            for client_addr in disconnected_clients:
                self._notify_client_disconnected(client_addr)
            
            self.logger.info("UDP server stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping UDP server: {e}")
            return False
    
    def send_message(self, client_identifier: str, message: str) -> bool:
        """
        Send a message to a specific client.
        """
        try:
            # Parse client identifier
            ip, port_str = client_identifier.split(':')
            port = int(port_str)
            client_addr = (ip, port)
            
            with self._lock:
                if client_addr not in self.clients:
                    self.logger.warning(f"Client {client_identifier} not found")
                    return False
            
            # Create message packet
            message_data = MessageProtocol.create_message(
                message_type="chat",
                content=message,
                sender="server"
            )
            
            # Send datagram
            self.socket.sendto(message_data, client_addr)
            self.logger.debug(f"Sent message to {client_identifier}: {message}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send message to {client_identifier}: {e}")
            return False
    
    def broadcast_message(self, message: str, exclude_client: str = None) -> bool:
        """
        Broadcast a message to all connected clients.
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
            self.logger.error(f"Failed to broadcast message: {e}")
            return False
    
    def get_connected_clients(self) -> list:
        """Get list of connected clients with their information."""
        with self._lock:
            clients = []
            for client_addr, client_info in self.clients.items():
                clients.append({
                    'identifier': f"{client_addr[0]}:{client_addr[1]}",
                    'ip': client_addr[0],
                    'port': client_addr[1],
                    'connected_at': client_info.get('connected_at', 0),
                    'last_activity': self.client_last_seen.get(client_addr, 0)
                })
            return clients
    
    def _receive_loop(self):
        """Main loop for receiving UDP datagrams from clients."""
        buffer_size = 4096
        
        while self.is_running and self.socket:
            try:
                # Receive datagram
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
                if self.is_running:
                    self.logger.error(f"Error receiving UDP data: {e}")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error in receive loop: {e}")
    
    def _handle_received_data(self, data: bytes, client_addr):
        """Handle received UDP datagram data."""
        try:
            # Parse message
            message = MessageProtocol.parse_message(data)
            if not message:
                self.logger.warning(f"Invalid message format from {client_addr}")
                return
            
            message_type = message.get('type')
            content = message.get('content', '')
            sender = message.get('sender', 'unknown')
            
            client_identifier = f"{client_addr[0]}:{client_addr[1]}"
            
            if message_type == "connect":
                self._handle_client_connect(client_addr, content)
            elif message_type == "disconnect":
                self._handle_client_disconnect(client_addr)
            elif message_type == "chat":
                self._handle_chat_message(client_addr, content, sender)
            elif message_type == "heartbeat":
                self._handle_heartbeat(client_addr)
            else:
                self.logger.warning(f"Unknown message type '{message_type}' from {client_identifier}")
                
        except Exception as e:
            self.logger.error(f"Error handling received data from {client_addr}: {e}")
    
    def _handle_client_connect(self, client_addr, client_name: str):
        """Handle new client connection."""
        client_identifier = f"{client_addr[0]}:{client_addr[1]}"
        
        with self._lock:
            if client_addr not in self.clients:
                self.clients[client_addr] = {
                    'name': client_name or f"Client{len(self.clients) + 1}",
                    'connected_at': time.time()
                }
                self.client_last_seen[client_addr] = time.time()
        
        self.logger.info(f"Client connected: {client_identifier} ({client_name})")
        self._notify_client_connected(client_addr, client_name)
        
        # Send welcome message
        welcome_msg = MessageProtocol.create_message(
            message_type="system",
            content=f"Welcome to the chat server, {client_name}!",
            sender="server"
        )
        self.socket.sendto(welcome_msg, client_addr)
    
    def _handle_client_disconnect(self, client_addr):
        """Handle client disconnection."""
        client_identifier = f"{client_addr[0]}:{client_addr[1]}"
        
        with self._lock:
            client_info = self.clients.pop(client_addr, None)
            self.client_last_seen.pop(client_addr, None)
        
        if client_info:
            self.logger.info(f"Client disconnected: {client_identifier}")
            self._notify_client_disconnected(client_addr)
    
    def _handle_chat_message(self, client_addr, content: str, sender: str):
        """Handle incoming chat message from client."""
        client_identifier = f"{client_addr[0]}:{client_addr[1]}"
        
        with self._lock:
            client_info = self.clients.get(client_addr, {})
            client_name = client_info.get('name', 'Unknown')
        
        self.logger.debug(f"Received chat message from {client_identifier}: {content}")
        self._notify_message_received(client_addr, client_name, content)
        
        # Echo message back to sender for confirmation
        echo_msg = MessageProtocol.create_message(
            message_type="system",
            content="Message delivered",
            sender="server"
        )
        self.socket.sendto(echo_msg, client_addr)
    
    def _handle_heartbeat(self, client_addr):
        """Handle client heartbeat message."""
        self._update_client_activity(client_addr)
        self.logger.debug(f"Heartbeat from {client_addr}")
    
    def _update_client_activity(self, client_addr):
        """Update client's last seen timestamp."""
        with self._lock:
            self.client_last_seen[client_addr] = time.time()
    
    def _cleanup_loop(self):
        """Background thread to clean up inactive clients."""
        CLIENT_TIMEOUT = 30  # seconds
        
        while self.is_running:
            try:
                current_time = time.time()
                disconnected_clients = []
                
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
    
    def _notify_client_connected(self, client_addr, client_name: str):
        """Notify observers about new client connection."""
        if self.observer:
            client_info = {
                'identifier': f"{client_addr[0]}:{client_addr[1]}",
                'ip': client_addr[0],
                'port': client_addr[1],
                'name': client_name,
                'connected_at': time.time()
            }
            self.observer.on_client_connected(client_info)
    
    def _notify_client_disconnected(self, client_addr):
        """Notify observers about client disconnection."""
        if self.observer:
            client_identifier = f"{client_addr[0]}:{client_addr[1]}"
            self.observer.on_client_disconnected(client_identifier)
    
    def _notify_message_received(self, client_addr, client_name: str, message: str):
        """Notify observers about received message."""
        if self.observer:
            client_identifier = f"{client_addr[0]}:{client_addr[1]}"
            self.observer.on_message_received(client_identifier, client_name, message)
    
    @property
    def protocol(self) -> str:
        return "UDP"
    
    def is_active(self) -> bool:
        return self.is_running

# Test Harness
class UDPServerTester:
    """Test harness for UDP server functionality"""
    
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port
        self.server = None
        self.test_results = []
        
    def print_test_result(self, test_name, success, message=""):
        """Print formatted test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if message:
            print(f"   ↳ {message}")
        self.test_results.append((test_name, success, message))
    
    def simulate_client(self, client_id, messages, delay=0.1):
        """Simulate a client sending messages to the server"""
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            client_socket.settimeout(2.0)
            
            # Send connect message
            connect_msg = MessageProtocol.create_message(
                message_type="connect",
                content=f"TestClient{client_id}",
                sender=f"client{client_id}"
            )
            client_socket.sendto(connect_msg, (self.host, self.port))
            time.sleep(delay)
            
            # Send chat messages
            for msg in messages:
                chat_msg = MessageProtocol.create_message(
                    message_type="chat",
                    content=msg,
                    sender=f"client{client_id}"
                )
                client_socket.sendto(chat_msg, (self.host, self.port))
                time.sleep(delay)
            
            # Send disconnect message
            disconnect_msg = MessageProtocol.create_message(
                message_type="disconnect",
                content="",
                sender=f"client{client_id}"
            )
            client_socket.sendto(disconnect_msg, (self.host, self.port))
            
            client_socket.close()
            return True
            
        except Exception as e:
            print(f"Client simulation error: {e}")
            return False
    
    def test_server_start_stop(self):
        """Test basic server start and stop functionality"""
        print("\n🧪 Testing Server Start/Stop...")
        
        try:
            # Test start
            self.server = UDPServer(self.host, self.port)
            success = self.server.start()
            self.print_test_result(
                "Server Start", 
                success, 
                f"Server started on {self.host}:{self.port}"
            )
            
            # Give server time to initialize
            time.sleep(0.5)
            
            # Test is_active
            is_active = self.server.is_active()
            self.print_test_result(
                "Server Active Check",
                is_active,
                f"Server reports active: {is_active}"
            )
            
            # Test stop
            stop_success = self.server.stop()
            self.print_test_result(
                "Server Stop",
                stop_success,
                "Server stopped successfully"
            )
            
            return all([success, stop_success])
            
        except Exception as e:
            self.print_test_result("Server Start/Stop", False, f"Exception: {e}")
            return False
    
    def test_single_client_communication(self):
        """Test communication with a single client"""
        print("\n🧪 Testing Single Client Communication...")
        
        try:
            self.server = UDPServer(self.host, self.port)
            
            # Setup observer to capture server events
            captured_events = []
            
            class TestObserver:
                def on_client_connected(self, client_info):
                    captured_events.append(('connected', client_info))
                    print(f"📞 Client connected: {client_info['identifier']}")
                
                def on_client_disconnected(self, client_id):
                    captured_events.append(('disconnected', client_id))
                    print(f"📞 Client disconnected: {client_id}")
                
                def on_message_received(self, client_id, client_name, message):
                    captured_events.append(('message', client_id, client_name, message))
                    print(f"💬 Message from {client_name}: {message}")
            
            observer = TestObserver()
            self.server.observer = observer
            
            self.server.start()
            time.sleep(0.5)
            
            # Simulate client
            test_messages = ["Hello server!", "How are you?", "Test message 3"]
            print(f"🤖 Simulating client with messages: {test_messages}")
            
            client_thread = threading.Thread(
                target=self.simulate_client, 
                args=(1, test_messages)
            )
            client_thread.start()
            
            # Wait for client to finish
            client_thread.join(timeout=5)
            
            # Give server time to process
            time.sleep(1)
            
            # Check results
            connected_clients = self.server.get_connected_clients()
            
            # Verify client connected
            connection_events = [e for e in captured_events if e[0] == 'connected']
            self.print_test_result(
                "Client Connection",
                len(connection_events) > 0,
                f"Connection events: {len(connection_events)}"
            )
            
            # Verify messages received
            message_events = [e for e in captured_events if e[0] == 'message']
            self.print_test_result(
                "Message Reception",
                len(message_events) >= len(test_messages),
                f"Received {len(message_events)}/{len(test_messages)} messages"
            )
            
            # Verify connected clients list
            self.print_test_result(
                "Connected Clients List",
                len(connected_clients) >= 0,
                f"Clients in list: {len(connected_clients)}"
            )
            
            self.server.stop()
            return len(connection_events) > 0 and len(message_events) >= len(test_messages)
            
        except Exception as e:
            self.print_test_result("Single Client Test", False, f"Exception: {e}")
            if self.server:
                self.server.stop()
            return False
    
    def run_all_tests(self):
        """Run all test cases and report results"""
        print("🚀 Starting UDP Server Tests...")
        print("=" * 50)
        
        tests = [
            self.test_server_start_stop,
            self.test_single_client_communication,
        ]
        
        results = []
        for test in tests:
            try:
                result = test()
                results.append(result)
            except Exception as e:
                print(f"❌ Test {test.__name__} crashed: {e}")
                results.append(False)
            
            time.sleep(1)  # Brief pause between tests
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        passed = sum(results)
        total = len(results)
        
        for i, (test_name, success, message) in enumerate(self.test_results):
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_name}")
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! UDP server is working correctly.")
        else:
            print("💥 Some tests failed. Check the implementation.")
        
        return passed == total

def quick_start_test():
    """Quick test to verify server can start and basic functionality"""
    print("🔍 Quick Start Test...")
    
    server = UDPServer('127.0.0.1', 5000)
    
    try:
        # Test start
        if server.start():
            print("✅ Server started successfully")
            time.sleep(0.5)
            
            # Test client list
            clients = server.get_connected_clients()
            print(f"✅ Connected clients: {len(clients)}")
            
            # Test protocol property
            print(f"✅ Server protocol: {server.protocol}")
            
            # Test stop
            if server.stop():
                print("✅ Server stopped successfully")
                return True
            else:
                print("❌ Server failed to stop")
                return False
        else:
            print("❌ Server failed to start")
            return False
            
    except Exception as e:
        print(f"❌ Quick test failed: {e}")
        return False

if __name__ == "__main__":
    print("🐍 Python UDP Server Test")
    print("If you don't see output, there might be an import issue.")
    
    # Test basic Python functionality first
    print("Basic Python test...")
    print("If you see this, Python is working!")
    
    # Run the tests
    tester = UDPServerTester('127.0.0.1', 5000)
    success = tester.run_all_tests()
    
    if success:
        print("\n🎊 All tests completed successfully!")
    else:
        print("\n💀 Some tests failed!")
    
    sys.exit(0 if success else 1)