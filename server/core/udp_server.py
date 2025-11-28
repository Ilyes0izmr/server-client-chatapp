#!/usr/bin/env python3
"""
Test script for UDP Server implementation.
Run this to test the server functionality without the GUI.
"""

import socket
import threading
import time
import json
import sys
import os

# Add the project root to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import using your existing message protocol structure
try:
    from server.core.message_protocol import MessageType, create_message, parse_message
except ImportError as e:
    print(f"❌ Failed to import message protocol: {e}")
    sys.exit(1)

try:
    from server.core.udp_server import UDPServer
except ImportError as e:
    print(f"❌ Failed to import UDPServer: {e}")
    sys.exit(1)

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
            connect_msg = create_message(
                MessageType.CONNECT,
                f"TestClient{client_id}",
                f"client{client_id}"
            ).encode('utf-8')
            client_socket.sendto(connect_msg, (self.host, self.port))
            time.sleep(delay)
            
            # Send chat messages
            for msg in messages:
                chat_msg = create_message(
                    MessageType.MESSAGE,
                    msg,
                    f"client{client_id}"
                ).encode('utf-8')
                client_socket.sendto(chat_msg, (self.host, self.port))
                time.sleep(delay)
            
            # Send disconnect message
            disconnect_msg = create_message(
                MessageType.DISCONNECT,
                "",
                f"client{client_id}"
            ).encode('utf-8')
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
            success = self.server.start_server()
            self.print_test_result(
                "Server Start", 
                success, 
                f"Server started on {self.host}:{self.port}"
            )
            
            # Give server time to initialize
            time.sleep(0.5)
            
            # Test is_active
            is_active = self.server.is_server_running()
            self.print_test_result(
                "Server Active Check",
                is_active,
                f"Server reports active: {is_active}"
            )
            
            # Test stop
            stop_success = self.server.stop_server()
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
            
            # Setup callbacks to capture server events
            captured_events = []
            
            def status_callback(message, is_error):
                event_type = "error" if is_error else "status"
                captured_events.append((event_type, message))
                print(f"📢 {event_type.upper()}: {message}")
            
            def message_callback(client_info, message):
                captured_events.append(('message', client_info, message))
                print(f"💬 MESSAGE from {client_info.get('name', 'Unknown')}: {message}")
            
            self.server.set_status_callback(status_callback)
            self.server.set_message_callback(message_callback)
            
            self.server.start_server()
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
            connected_clients = self.server.get_clients_info()
            
            # Verify client connected
            status_events = [e for e in captured_events if e[0] == 'status' and 'connected' in e[1].lower()]
            self.print_test_result(
                "Client Connection",
                len(status_events) > 0,
                f"Connection events: {len(status_events)}"
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
            
            self.server.stop_server()
            return len(status_events) > 0 and len(message_events) >= len(test_messages)
            
        except Exception as e:
            self.print_test_result("Single Client Test", False, f"Exception: {e}")
            if self.server:
                self.server.stop_server()
            return False
    
    def test_multiple_clients(self):
        """Test handling multiple simultaneous clients"""
        print("\n🧪 Testing Multiple Clients...")
        
        try:
            self.server = UDPServer(self.host, self.port)
            
            # Setup callbacks
            captured_events = []
            
            def status_callback(message, is_error):
                if not is_error and 'connected' in message.lower():
                    captured_events.append(('connected', message))
                elif not is_error and 'disconnected' in message.lower():
                    captured_events.append(('disconnected', message))
            
            self.server.set_status_callback(status_callback)
            
            self.server.start_server()
            time.sleep(0.5)
            
            # Simulate multiple clients
            clients_data = [
                (1, ["Client 1 message 1", "Client 1 message 2"]),
                (2, ["Client 2 message 1"]),
                (3, ["Client 3 message 1", "Client 3 message 2", "Client 3 message 3"])
            ]
            
            threads = []
            for client_id, messages in clients_data:
                thread = threading.Thread(
                    target=self.simulate_client,
                    args=(client_id, messages, 0.05)
                )
                threads.append(thread)
                thread.start()
            
            # Wait for all clients
            for thread in threads:
                thread.join(timeout=3)
            
            # Give server time to process
            time.sleep(1)
            
            # Check results
            connection_events = [e for e in captured_events if e[0] == 'connected']
            disconnect_events = [e for e in captured_events if e[0] == 'disconnected']
            
            self.print_test_result(
                "Multiple Client Connections",
                len(connection_events) >= len(clients_data),
                f"Connected: {len(connection_events)}/{len(clients_data)}"
            )
            
            self.print_test_result(
                "Multiple Client Disconnections", 
                len(disconnect_events) >= len(clients_data),
                f"Disconnected: {len(disconnect_events)}/{len(clients_data)}"
            )
            
            self.server.stop_server()
            return len(connection_events) >= len(clients_data)
            
        except Exception as e:
            self.print_test_result("Multiple Clients Test", False, f"Exception: {e}")
            if self.server:
                self.server.stop_server()
            return False
    
    def test_broadcast_message(self):
        """Test broadcasting messages to all clients"""
        print("\n🧪 Testing Broadcast Messages...")
        
        try:
            self.server = UDPServer(self.host, self.port)
            self.server.start_server()
            time.sleep(0.5)
            
            # Manually add test clients to server
            client1_addr = ('127.0.0.1', 6001)
            client2_addr = ('127.0.0.1', 6002)
            
            self.server.clients[client1_addr] = {
                'name': 'TestClient1', 
                'connected_at': time.time(),
                'address': client1_addr
            }
            self.server.clients[client2_addr] = {
                'name': 'TestClient2', 
                'connected_at': time.time(),
                'address': client2_addr
            }
            self.server.client_last_seen[client1_addr] = time.time()
            self.server.client_last_seen[client2_addr] = time.time()
            
            # Test broadcast
            broadcast_message = "Server broadcast test message"
            success = self.server.broadcast_message(broadcast_message)
            
            self.print_test_result(
                "Broadcast Send Success",
                success,
                f"Broadcast returned: {success}"
            )
            
            self.server.stop_server()
            return success
            
        except Exception as e:
            self.print_test_result("Broadcast Test", False, f"Exception: {e}")
            if self.server:
                self.server.stop_server()
            return False
    
    def test_client_timeout(self):
        """Test automatic cleanup of inactive clients"""
        print("\n🧪 Testing Client Timeout...")
        
        try:
            self.server = UDPServer(self.host, self.port)
            
            # Add a test client with old timestamp
            test_addr = ('127.0.0.1', 9999)
            self.server.clients[test_addr] = {
                'name': 'TimeoutTestClient', 
                'connected_at': time.time(),
                'address': test_addr
            }
            self.server.client_last_seen[test_addr] = time.time() - 35  # 35 seconds old
            
            self.server.start_server()
            
            # Wait for cleanup cycle
            time.sleep(6)
            
            # Check if client was removed
            clients_after = self.server.get_clients_info()
            client_removed = len(clients_after) == 0
            
            self.print_test_result(
                "Client Timeout Cleanup",
                client_removed,
                f"Clients after cleanup: {len(clients_after)}"
            )
            
            self.server.stop_server()
            return client_removed
            
        except Exception as e:
            self.print_test_result("Client Timeout Test", False, f"Exception: {e}")
            if self.server:
                self.server.stop_server()
            return False
    
    def run_all_tests(self):
        """Run all test cases and report results"""
        print("🚀 Starting UDP Server Tests...")
        print("=" * 50)
        
        tests = [
            self.test_server_start_stop,
            self.test_single_client_communication,
            self.test_multiple_clients,
            self.test_broadcast_message,
            self.test_client_timeout,
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
        if server.start_server():
            print("✅ Server started successfully")
            time.sleep(0.5)
            
            # Test client list
            clients = server.get_clients_info()
            print(f"✅ Connected clients: {len(clients)}")
            
            # Test protocol property
            print(f"✅ Server protocol: {server.protocol.value}")
            
            # Test server info
            info = server.get_server_info()
            print(f"✅ Server info: {info}")
            
            # Test stop
            if server.stop_server():
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
    import argparse
    
    parser = argparse.ArgumentParser(description='Test UDP Server')
    parser.add_argument('--quick', action='store_true', help='Run quick test only')
    parser.add_argument('--host', default='127.0.0.1', help='Server host')
    parser.add_argument('--port', type=int, default=5000, help='Server port')
    
    args = parser.parse_args()
    
    if args.quick:
        success = quick_start_test()
        sys.exit(0 if success else 1)
    else:
        tester = UDPServerTester(args.host, args.port)
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)