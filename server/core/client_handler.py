import socket
import threading
import json
from datetime import datetime
from typing import Callable, Dict
from server.core.message_protocol import MessageProtocol, MessageType
import time

class ClientHandler:
    """Handles individual TCP client connections using length-prefixed JSON protocol"""

    def __init__(self, client_socket: socket.socket, client_address: tuple, 
                 remove_callback: Callable, notify_callback: Callable,
                 message_callback: Callable = None):
        self.client_socket = client_socket
        self.client_address = client_address
        self.remove_callback = remove_callback
        self.notify_callback = notify_callback
        self.message_callback = message_callback
        self.is_running = True
        
        self.client_id = f"{client_address[0]}:{client_address[1]}"
        self.username = f"User_{abs(hash(client_address)) % 10000}"
        
        self.thread = threading.Thread(target=self._handle_client, daemon=True, name=f"ClientHandler-{self.client_id}")

    def start(self):
        print(f"🧵 Starting ClientHandler for {self.client_id}")
        self.thread.start()

    def stop(self):
        print(f"⏹ Stopping ClientHandler for {self.client_id}")
        self.is_running = False
        try:
            self.client_socket.shutdown(socket.SHUT_RDWR)
        except:
            pass
        try:
            self.client_socket.close()
        except:
            pass

    def _handle_client(self):
        try:
            self.client_socket.settimeout(1.0)
            
            # Send welcome using length-prefixed protocol
            self._send_status_message(f"Welcome! Your username: {self.username}", sender="System")

            buffer = b""  # Byte buffer for partial messages
            
            while self.is_running:
                try:
                    data = self.client_socket.recv(1024)
                    if not data:
                        print(f"📥 Client {self.client_id} closed connection")
                        break
                    
                    buffer += data
                    print(f"📥 Received {len(data)} bytes from {self.client_id} (buffer: {len(buffer)}B)")

                    # Process all complete messages in buffer
                    while len(buffer) >= 4:
                        # Read 4-byte message length (big-endian)
                        length_bytes = buffer[:4]
                        message_len = int.from_bytes(length_bytes, 'big')
                        print(f"🔍 Expected message length: {message_len} bytes")

                        # Validate length (prevent huge allocations)
                        if message_len > 1024 * 1024:  # 1MB max
                            print(f"❌ Invalid message length: {message_len}B (too large)")
                            buffer = b""
                            break

                        # Check if full message is available
                        if len(buffer) >= 4 + message_len:
                            # Extract JSON payload
                            json_data = buffer[4:4 + message_len]
                            buffer = buffer[4 + message_len:]  # Save leftover

                            try:
                                message_str = json_data.decode('utf-8')
                                print(f"🔍 Raw JSON received: {repr(message_str)}")
                                self._process_message(message_str)
                            except UnicodeDecodeError as e:
                                print(f"❌ Unicode decode error: {e}")
                                continue
                        else:
                            # Incomplete message — wait for more data
                            print(f"⏳ Incomplete message (have {len(buffer)-4}B, need {message_len}B)")
                            break

                except socket.timeout:
                    continue
                except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError) as e:
                    print(f"🔌 Connection lost with {self.client_id}: {e}")
                    break
                except OSError as e:
                    if self.is_running:
                        print(f"⚠️ Socket error: {e}")
                    break

        except Exception as e:
            if self.is_running:
                print(f"🔥 CRITICAL: {e}")
                import traceback
                traceback.print_exc()
                self.notify_callback(f"Client handler error: {e}", True)
        finally:
            self._cleanup()

    def _process_message(self, message_str: str):
        try:
            # Use MessageProtocol to decode — ensures consistency
            message_type, content, sender = MessageProtocol.decode_message(message_str)
            print(f"✅ Parsed message: type={message_type}, sender='{sender}', content='{content}'")

            if message_type is None:
                print(f"❌ Failed to decode message: {repr(message_str)}")
                return

            # Create standardized client info
            client_info = {
                'identifier': self.client_id,
                'name': self.username,
                'address': self.client_address,
                'protocol': 'TCP'
            }

            if message_type == MessageType.MESSAGE:
                if self.message_callback:
                    self.message_callback(client_info, content)
                    self.message_callback(client_info, content)
                else:
                    print("❌ No message_callback set in ClientHandler!")

            elif message_type == MessageType.TEST:
                ##server_recv_time = time.time()
                ##print(f"📢 TEST: {server_recv_time}")
                self._send_test_message((""))
                

            elif message_type == MessageType.STATUS:
                display_msg = f"{sender}: {content}" if sender else content
                self.notify_callback(display_msg)
                print(f"📢 Status: {display_msg}")

            elif message_type == MessageType.CONNECT:
                if content:
                    self.username = content
                    print(f"👤 Username set to: {self.username}")

            elif message_type == MessageType.DISCONNECT:
                print(f"👋 Disconnect requested by client")
                self.is_running = False

        except Exception as e:
            print(f"❌ Error processing message: {e}")
            import traceback
            traceback.print_exc()

    def _cleanup(self):
        print(f"🧹 Cleaning up ClientHandler for {self.client_id}")
        self.is_running = False
        if self.remove_callback:
            self.remove_callback(self.client_socket)
        try:
            self.client_socket.close()
        except:
            pass
        if self.notify_callback:
            self.notify_callback(f"Client disconnected: {self.client_id}")

    def get_client_info(self) -> dict:
        return {
            'identifier': self.client_id,
            'name': self.username,
            'address': self.client_address,
            'socket': self.client_socket
        }

    def _send_raw_message(self, message_type: MessageType, content: str, sender: str = "server") -> bool:
        """Internal: Send any message type with length prefix"""
        if not self.is_running or not self.client_socket:
            return False

        try:
            
            encoded = MessageProtocol.encode_message(message_type, content, sender)
            data = encoded.encode('utf-8')
            length = len(data)

            # Send 4-byte length (big-endian) + message
            self.client_socket.sendall(length.to_bytes(4, 'big'))
            self.client_socket.sendall(data)
            print(f"📤 SENT | {data}")
            print(f"📤 SENT {length}B | {message_type.name}: '{content}' (sender: {sender})")
            return True

        except Exception as e:
            print(f"❌ Send failed for {self.client_id}: {e}")
            self._cleanup()
            return False

    def send_message(self, message: str) -> bool:
        """Public API: Send a chat message to this client"""
        return self._send_raw_message(MessageType.MESSAGE, message, "server")

    def _send_status_message(self, content: str, sender: str = "System") -> bool:
        """Send a status message (e.g., welcome, system alerts)"""
        return self._send_raw_message(MessageType.STATUS, content, sender)

    def _send_test_message(self, content:str):
        return self._send_raw_message(MessageType.TEST, content, "server")

    def _send_connect_ack(self, username: str) -> bool:
        """Send connection acknowledgment"""
        return self._send_raw_message(MessageType.CONNECT, username, "server")

    def _send_disconnect_ack(self) -> bool:
        """Send disconnection acknowledgment"""
        return self._send_raw_message(MessageType.DISCONNECT, "", "server")