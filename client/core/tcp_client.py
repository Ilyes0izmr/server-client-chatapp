import socket
import threading
import time
from typing import Callable, Optional
from .client_base import ClientBase
from .message_protocol import ChatMessage, MessageType
import matplotlib.pyplot as plt

class TCPClient(ClientBase):
    """TCP client implementation"""
    
    def __init__(self, host, port, buffer_size=4096, encoding="utf-8", timeout=10):
        super().__init__(host, port, buffer_size, encoding, timeout)
        self.socket = None
        self.receive_callback = None
        self.receive_thread = None
        self.should_listen = False
        self.lock = threading.Lock()
        self.username = None
        self._recv_buffer = b""
    
    def connect(self) -> bool:
        """Connect to TCP server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.host, self.port))
            self.is_connected = True
            self.logger.info(f"Connected to TCP server at {self.host}:{self.port}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to TCP server: {e}")
            self.is_connected = False
            return False
    
    def send_message(self, message: str, username: str = None) -> bool:
        """Send message to server"""
        if not self.is_connected or not self.socket:
            self.logger.error("Not connected to server")
            return False
        
        try:
            chat_message = ChatMessage.create_text_message(message, username)
            message_data = chat_message.to_json().encode(self.encoding)
            
            # Send message length first (4 bytes)
            message_len = len(message_data)
            self.socket.sendall(message_len.to_bytes(4, byteorder='big'))
            
            # Send actual message
            self.socket.sendall(message_data)
            self.logger.debug(f"Message sent: {message}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            self.is_connected = False
            return False
    
    def send_connect_message(self, username: str) -> bool:
        """Send connection message to server"""
        if not self.is_connected or not self.socket:
            return False
        
        try:
            self.username = username
            chat_message = ChatMessage.create_connect_message(username)
            message_data = chat_message.to_json().encode(self.encoding)
            
            message_len = len(message_data)
            self.socket.sendall(message_len.to_bytes(4, byteorder='big'))
            self.socket.sendall(message_data)
            
            self.logger.info(f"Sent connect message for user: {username}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send connect message: {e}")
            return False
    
    def send_disconnect_message(self) -> bool:
        """Send disconnect message to server"""
        if not self.is_connected or not self.socket:
            return False
        
        try:
            chat_message = ChatMessage.create_disconnect_message(self.username)
            message_data = chat_message.to_json().encode(self.encoding)
            
            message_len = len(message_data)
            self.socket.sendall(message_len.to_bytes(4, byteorder='big'))
            self.socket.sendall(message_data)
            
            self.logger.info("Sent disconnect message")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send disconnect message: {e}")
            return False
    
    def receive_message(self) -> Optional[ChatMessage]:
        """Receive a single message from server"""
        if not self.is_connected or not self.socket:
            return None
        
        try:
            # First receive message length
            length_data = self.socket.recv(4)
            if not length_data:
                self.logger.debug("Server closed connection")
                self.is_connected = False
                return None
            
            message_len = int.from_bytes(length_data, byteorder='big')
            
            # Receive the actual message
            received_data = b""
            while len(received_data) < message_len:
                chunk = self.socket.recv(min(self.buffer_size, message_len - len(received_data)))
                if not chunk:
                    break
                received_data += chunk
            
            if received_data:
                message_str = received_data.decode(self.encoding)
                chat_message = ChatMessage.from_json(message_str)
                return chat_message
            
        except socket.timeout:
            self.logger.debug("Receive timeout")
        except ConnectionResetError:
            self.logger.error("Connection reset by server")
            self.is_connected = False
        except Exception as e:
            self.logger.error(f"Error receiving message: {e}")
            self.is_connected = False
        
        return None
    
    def start_listening(self, callback: Callable[[ChatMessage], None]):
        """Start background thread to listen for messages"""
        self.receive_callback = callback
        self.should_listen = True
        self.receive_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.receive_thread.start()
    
    def _listen_loop(self):
        """Background thread loop for receiving messages"""
        while self.should_listen and self.is_connected:
            try:
                message = self.receive_message()
                if message and self.receive_callback:
                    self.receive_callback(message)
                elif not self.is_connected:
                    break
            except Exception as e:
                self.logger.error(f"Error in listen loop: {e}")
                break
            time.sleep(0.1)
        
        self.logger.debug("Listen loop ended")
    
    def stop_listening(self):
        """Stop the background listening thread"""
        self.should_listen = False
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=1.0)
    
    def disconnect(self):
        """Disconnect from server"""
        if self.is_connected:
            self.send_disconnect_message()
        
        self.stop_listening()
        self.is_connected = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            finally:
                self.socket = None
        self.logger.info("Disconnected from server")


    def connection_test_calculation(self):
        if not self.is_connected or not self.socket:
            print("❌ Not connected — aborting test.")
            return

        print("\n📡 Running TCP Connection Test (10 packets - excluding first from results)...")
        all_latencies = []  # Store all 10 measurements

        for i in range(10):
            send_time = time.time()

            test_msg = ChatMessage(
                type=MessageType.TEST,
                content=f"",
                timestamp=send_time,
                username=self.username or "tester"
            )

            # Send
            try:
                data = test_msg.to_json().encode("utf-8")
                self.socket.sendall(len(data).to_bytes(4, "big"))
                self.socket.sendall(data)
                print(f"message sent from client : {data}")
            except Exception as e:
                all_latencies.append(None)
                print(f"[{i+1:2d}] ❌ send failed")
                continue

            # Wait up to 1 second for reply
            start = time.time()
            reply_msg = None
            while time.time() - start < 1.0:
                msg = self.receive_message()
                print(f"raw message from server is {msg}")
                if msg and msg.type == MessageType.TEST and msg.username == "server":
                    reply_msg = msg
                    break
                time.sleep(0.0001)

            if reply_msg:
                try:
                    server_recv_time = float(reply_msg.timestamp)
                    print(f"server_recv_time : {server_recv_time}")
                    latency = (server_recv_time - send_time) * 1000
                    all_latencies.append(latency)
                    print(f"[{i+1}] ✅ {latency:.1f} ms")
                except ValueError:
                    all_latencies.append(None)
                    print(f"[{i+1}] ❌ invalid time")
            else:
                all_latencies.append(None)
                print(f"[{i+1:2d}] ❌ timeout")

            time.sleep(0.001)

        # === CALCULATIONS - EXCLUDE FIRST PACKET ===
        # Use only packets 2-10 (slice from index 1 to end)
        latencies = all_latencies[1:]  # This excludes the first measurement
        
        total_packets = len(latencies)  # Should be 9
        received = sum(1 for x in latencies if x is not None)
        lost = total_packets - received
        loss_pct = (lost / total_packets) * 100
        
        print(f"\n📊 Test Results (excluding first packet):")
        print(f"   Total packets analyzed: {total_packets}")
        print(f"   Packets received: {received}")
        print(f"   Packets lost: {lost}")
        print(f"   Packet Loss: {loss_pct:.1f}%")

        if received > 0:
            valid = [x for x in latencies if x is not None]
            avg = sum(valid) / len(valid)
            min_latency = min(valid)
            max_latency = max(valid)
            print(f"   Latency - Avg: {avg:.2f} ms, Min: {min_latency:.2f} ms, Max: {max_latency:.2f} ms")
        else:
            print("   ❌ No successful measurements")

        # === PLOT - EXCLUDE FIRST PACKET ===
        plt.figure(figsize=(8, 4))
        # Plot packets 2-10 (sequence numbers 2 through 10)
        seqs = list(range(2, 11))  # This creates [2, 3, 4, ..., 10]
        plt.plot(seqs, latencies, 'o-', label="One-Way Latency (C→S)")
        plt.xlabel("Packet #")
        plt.ylabel("Latency (ms)")
        plt.title("Connection Test — Latency & Loss (Excluding First Packet)")
        plt.grid(True, alpha=0.5)
        plt.legend()
        
        if received > 0:
            stats_text = (f"Packets: {received}/{total_packets}\n"
                        f"Loss: {loss_pct:.1f}%\n"
                        f"Avg Latency: {avg:.2f} ms\n"
                        f"Min: {min_latency:.2f} ms\n"
                        f"Max: {max_latency:.2f} ms")
        else:
            stats_text = f"Packets: 0/{total_packets}\nLoss: 100.0%"
            
        plt.gcf().text(0.75, 0.7, stats_text, fontsize=10, bbox=dict(facecolor='white', alpha=0.8))
        plt.show()
        
        # Optional: Show what the first packet result was
        first_packet = all_latencies[0] if all_latencies else None
        if first_packet is not None:
            print(f"\n📝 Note: First packet latency was {first_packet:.1f} ms (excluded from results)")
        else:
            print(f"\n📝 Note: First packet was lost (excluded from results)")
    

    def receive_test_message(self) -> Optional[ChatMessage]:
        if not self.is_connected or not self.socket:
            return None

        try:
            # Set a short timeout for test responses
            self.socket.settimeout(0.01)
            
            # Keep reading until we have a complete message or timeout
            while True:
                # If we don't have the length header yet, read it
                if len(self._recv_buffer) < 4:
                    chunk = self.socket.recv(4 - len(self._recv_buffer))
                    if not chunk:
                        return None
                    self._recv_buffer += chunk
                    if len(self._recv_buffer) < 4:
                        continue  # Still don't have full header

                # We have the header - parse message length
                length_bytes = self._recv_buffer[:4]
                message_len = int.from_bytes(length_bytes, 'big')

                # Safety check
                if message_len > 1024 * 1024:  # 1 MB max
                    self.logger.error("Message too large — clearing buffer")
                    self._recv_buffer = b""
                    return None

                # Read the rest of the message if we don't have it
                total_needed = 4 + message_len
                if len(self._recv_buffer) < total_needed:
                    chunk = self.socket.recv(total_needed - len(self._recv_buffer))
                    if not chunk:
                        return None
                    self._recv_buffer += chunk
                    if len(self._recv_buffer) < total_needed:
                        continue  # Still don't have full message

                # We have a complete message - extract and process it
                json_data = self._recv_buffer[4:total_needed]
                self._recv_buffer = self._recv_buffer[total_needed:]  # Keep rest

                try:
                    message_str = json_data.decode(self.encoding)
                    chat_message = ChatMessage.from_json(message_str)
                    return chat_message
                except Exception as e:
                    self.logger.error(f"Failed to decode message: {e}")
                    continue

        except socket.timeout:
            # Expected - no data available right now
            return None
        except BlockingIOError:
            # No data available in non-blocking mode
            return None
        except Exception as e:
            self.logger.error(f"Receive error: {e}")
            self.is_connected = False
            return None