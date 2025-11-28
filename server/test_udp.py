#!/usr/bin/env python3
"""
Test script for UDP Server implementation.
Run this from the project root directory.
"""

import socket
import threading
import time
import json
import sys
import os

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(__file__))

# Import using absolute paths from project root
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
    
    def run_all_tests(self):
        """Run all test cases and report results"""
        print("🚀 Starting UDP Server Tests...")
        print("=" * 50)
        
        tests = [
            self.test_server_start_stop,
        ]
        
        results = []
        for test in tests:
            try:
                result = test()
                results.append(result)
            except Exception as e:
                print(f"❌ Test {test.__name__} crashed: {e}")
                results.append(False)
            
            time.sleep(1)
        
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

if __name__ == "__main__":
    tester = UDPServerTester('127.0.0.1', 5000)
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)