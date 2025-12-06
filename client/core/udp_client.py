import socket
import threading
import time
import json
from typing import Callable, Optional
from .client_base import ClientBase
from .message_protocol import ChatMessage, MessageType
import matplotlib.pyplot as plt 

class UDPClient(ClientBase):
    """UDP client implementation"""
    
    def __init__(self, host, port, buffer_size=4096, encoding="utf-8", timeout=10):
        super().__init__(host, port, buffer_size, encoding, timeout)
        self.socket = None
        self.receive_callback = None
        self.receive_thread = None
        self.should_listen = False
        self.server_address = (host, port)
        self.username = None
        self.sequence_number = 0  # For message ordering
        self.pending_acknowledgements = {}  # For reliable UDP
        self.connection_verified = False  # Track if server is reachable
        self.max_retries = None  # None means infinite retries
        self.retransmit_timeout = 2.0  # Time before retransmission
        self.recovery_mode = False # If true, client is recovering from disconnect
        self.should_retransmit = False
        self.retransmit_thread = None
    
    def connect(self) -> bool:
        """Setup UDP socket and verify server is reachable"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.settimeout(1.5)  # Longer timeout for connection verification
            self.is_connected = True
            
            # Try to verify server is reachable by sending a test packet
            if self._verify_server_connection():
                self.socket.settimeout(1.0)  # Reset to normal timeout
                self.connection_verified = True
                self.logger.info(f"UDP client connected to {self.host}:{self.port}")
                return True
            else:
                self.logger.error(f"UDP server not reachable at {self.host}:{self.port}")
                self.is_connected = False
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to setup UDP client: {e}")
            self.is_connected = False
            return False
    
    def _verify_server_connection(self) -> bool:
        """Verify that the server is reachable by sending a test message"""
        try:
            # Create a test connection message
            test_message = ChatMessage.create_connect_message("test_connection")
            message_data = test_message.to_json().encode(self.encoding)
            
            # Send test message
            self.socket.sendto(message_data, self.server_address)
            self.logger.debug(f"Sent connection test to {self.server_address}")
            
            # Wait for any response (even if it's not the expected one)
            start_time = time.time()
            while time.time() - start_time < 3.0:  # 3 second timeout
                try:
                    data, addr = self.socket.recvfrom(self.buffer_size)
                    if data:
                        # If we get any response, server is reachable
                        self.logger.debug(f"Server response received from {addr}")
                        return True
                except socket.timeout:
                    continue
                except BlockingIOError:
                    continue
            
            # No response received within timeout
            self.logger.warning("No response from server during connection test")
            return False
            
        except Exception as e:
            self.logger.error(f"Error during connection verification: {e}")
            return False
    
    def send_message(self, message: str, username: str = None) -> bool:
        """Send message to server via UDP with reliability"""
        if not self.is_connected or not self.socket or not self.connection_verified:
            self.logger.error("UDP client not properly connected")
            return False
        
        try:
            # Assign sequence number
            sequence = self.sequence_number
            self.sequence_number += 1
            
            # Create reliable message with sequence
            chat_message = ChatMessage.create_reliable_message(
                sequence=sequence,
                content=message,
                username=username or self.username
            )
            message_data = chat_message.to_json().encode(self.encoding)
            
            # Send message
            bytes_sent = self.socket.sendto(message_data, self.server_address)
            
            # Track for acknowledgement
            self.pending_acknowledgements[sequence] = {
                "message": message_data,
                "sent_time": time.time(),
                "retries": 0,
                "content": message
            }
            
            self.logger.debug(f"Reliable UDP message sent (seq={sequence}): {message}")
            
            # Start retransmission thread if not running
            if not self.should_retransmit:
                self.should_retransmit = True
                self.retransmit_thread = threading.Thread(target=self._retransmit_loop, daemon=True)
                self.retransmit_thread.start()
                
            return True
        except Exception as e:
            self.logger.error(f"Failed to send UDP message: {e}")
            return False
    
    def _retransmit_loop(self):
        """Retransmit unacknowledged messages - INFINITE RETRIES"""
        while self.should_retransmit and self.is_connected:
            current_time = time.time()
            sequences_to_retransmit = []
            
            # Check for messages needing retransmission
            for seq, data in list(self.pending_acknowledgements.items()):
                elapsed = current_time - data["sent_time"]
                
                if elapsed > self.retransmit_timeout:
                    sequences_to_retransmit.append(seq)
                    data["retries"] += 1
                    data["sent_time"] = current_time
                    
                    # Log first few retries, then less frequently
                    if data["retries"] <= 3 or data["retries"] % 10 == 0:
                        self.logger.info(f"Retransmitting seq={seq} (attempt {data['retries']})")
                    
                    # Enter recovery mode if we're retrying
                    if not self.recovery_mode:
                        self.recovery_mode = True
                        self.logger.warning("Entering recovery mode - connection issues detected")
            
            # Retransmit messages
            for seq in sequences_to_retransmit:
                if seq in self.pending_acknowledgements:
                    try:
                        message_data = self.pending_acknowledgements[seq]["message"]
                        self.socket.sendto(message_data, self.server_address)
                        
                        # If successful, we might be reconnected
                        if self.recovery_mode and len(sequences_to_retransmit) > 0:
                            self.logger.info(f"Recovery attempt for seq={seq}")
                            
                    except Exception as e:
                        self.logger.error(f"Failed to retransmit seq={seq}: {e}")
            
            # Exit recovery mode if all ACKs received
            if self.recovery_mode and not self.pending_acknowledgements:
                self.recovery_mode = False
                self.logger.info("Recovery complete - all messages acknowledged")
            
            time.sleep(0.5)  # Increased sleep to reduce CPU usage during retries
    
    def send_connect_message(self, username: str) -> bool:
        """Send connection message to server via UDP"""
        if not self.is_connected or not self.socket or not self.connection_verified:
            return False
        
        try:
            self.username = username
            chat_message = ChatMessage.create_connect_message(username)
            message_data = chat_message.to_json().encode(self.encoding)
            
            self.socket.sendto(message_data, self.server_address)
            self.logger.info(f"Sent UDP connect message for user: {username}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send UDP connect message: {e}")
            return False
    
    def send_disconnect_message(self) -> bool:
        """Send disconnect message to server via UDP"""
        if not self.is_connected or not self.socket or not self.connection_verified:
            return False
        
        try:
            chat_message = ChatMessage.create_disconnect_message(self.username)
            message_data = chat_message.to_json().encode(self.encoding)
            
            self.socket.sendto(message_data, self.server_address)
            self.logger.info("Sent UDP disconnect message")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send UDP disconnect message: {e}")
            return False
    
    def receive_message(self) -> Optional[ChatMessage]:
        """Receive a single message from server via UDP"""
        if not self.is_connected or not self.socket or not self.connection_verified:
            return None
        
        try:
            data, addr = self.socket.recvfrom(self.buffer_size)
            if data:
                message_str = data.decode(self.encoding)
                chat_message = ChatMessage.from_json(message_str)
                
                # Handle ACK messages
                if chat_message.type == MessageType.ACK:
                    self._handle_ack_message(chat_message)
                    return None  # Don't pass ACKs to chat
                
                return chat_message
        except socket.timeout:
            pass
        except Exception as e:
            self.logger.error(f"Error receiving UDP message: {e}")
        
        return None
    
    def _handle_ack_message(self, chat_message: ChatMessage):
        """Handle acknowledgement from server"""
        try:
            ack_data = json.loads(chat_message.content)
            sequence = ack_data.get("sequence")
            
            if sequence is not None and sequence in self.pending_acknowledgements:
                content = self.pending_acknowledgements[sequence]["content"]
                del self.pending_acknowledgements[sequence]
                self.logger.debug(f"ACK for seq={sequence}: {content}")
                
                if not self.pending_acknowledgements:
                    self.should_retransmit = False
        except json.JSONDecodeError:
            self.logger.error("Invalid ACK format")
    
    def start_listening(self, callback: Callable[[ChatMessage], None]):
        """Start background thread to listen for UDP messages"""
        if not self.connection_verified:
            self.logger.warning("Cannot start listening - server connection not verified")
            return
            
        self.receive_callback = callback
        self.should_listen = True
        self.receive_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.receive_thread.start()
    
    def _listen_loop(self):
        """Background thread loop for receiving UDP messages"""
        while self.should_listen and self.is_connected and self.connection_verified:
            try:
                message = self.receive_message()
                if message and self.receive_callback:
                    self.receive_callback(message)
            except Exception as e:
                self.logger.error(f"Error in UDP listen loop: {e}")
                if not self.is_connected:
                    break
            time.sleep(0.05)  # Shorter delay for UDP
    
    def stop_listening(self):
        """Stop the background listening thread"""
        self.should_listen = False
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=1.0)
    
    def disconnect(self):
        """Disconnect UDP client - clear all pending messages"""
        self.should_retransmit = False

        #Clear all pending messages when disconnecting
        pending_count = len(self.pending_acknowledgements)
        if pending_count > 0:
            self.logger.warning(f"Clearing {pending_count} pending messages on disconnect")
            self.pending_acknowledgements.clear()

            if self.retransmit_thread and self.retransmit_thread.is_alive():
                self.retransmit_thread.join(timeout=2.0)
        if self.is_connected and self.connection_verified:
            self.send_disconnect_message()
        
        self.stop_listening()
        self.is_connected = False
        self.connection_verified = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            finally:
                self.socket = None
        self.logger.info("UDP client disconnected")


    def connection_test_calculation(self):
        """Run connection test: send 10 UDP test packets, measure latency & loss (excluding 1st)."""
        if not self.is_connected or not self.socket or not self.connection_verified:
            print("❌ Not connected — aborting test.")
            return

        print("\n📡 Running UDP Connection Test (10 packets - excluding first from results)...")
        all_latencies = []

        # Set socket timeout for the entire test
        original_timeout = self.socket.gettimeout()
        self.socket.settimeout(1.0)
        
        try:
            for i in range(10):
                send_time = time.time()

                # Create test message with proper content
                test_msg = ChatMessage(
                    type=MessageType.TEST,
                    content=f"test_packet_{i+1}",
                    timestamp=send_time,
                    username=self.username or "tester"
                )

                # Send via UDP
                try:
                    data = test_msg.to_json().encode(self.encoding)
                    self.socket.sendto(data, self.server_address)
                    print(f"[{i+1:2d}] SEND: {len(data)} bytes @ {send_time:.6f}")
                except Exception as e:
                    print(f"[{i+1:2d}] ❌ send failed: {e}")
                    all_latencies.append(None)
                    continue

                # Wait for reply - handle multiple message types until we get TEST reply
                reply_received = False
                start_time = time.time()
                
                while time.time() - start_time < 1.0 and not reply_received:
                    try:
                        raw_data, addr = self.socket.recvfrom(self.buffer_size)
                        recv_time = time.time()
                        msg_str = raw_data.decode(self.encoding)
                        msg = ChatMessage.from_json(msg_str)

                        # DEBUG: Print what we received
                        print(f"[{i+1:2d}] 🔍 DEBUG: Received {msg.type} from {msg.username}")

                        # Only accept TEST replies from server
                        if msg.type == MessageType.TEST and msg.username == "server":
                            # Calculate one-way latency (server echoes original timestamp)
                            server_timestamp = msg.timestamp
                            latency = (recv_time - server_timestamp) * 1000.0
                            all_latencies.append(latency)
                            print(f"[{i+1:2d}] ✅ {latency:.2f} ms")
                            reply_received = True
                        else:
                            # Ignore other message types (like CONNECT replies) and continue waiting
                            print(f"[{i+1:2d}] 🔄 Ignoring {msg.type} message, waiting for TEST reply...")
                            continue

                    except socket.timeout:
                        break  # No more data available
                    except Exception as e:
                        print(f"[{i+1:2d}] ❌ receive error: {e}")
                        break

                if not reply_received:
                    all_latencies.append(None)
                    print(f"[{i+1:2d}] ❌ timeout - no TEST reply received")

                time.sleep(0.05)  # Small gap between packets

        finally:
            # Restore original timeout
            self.socket.settimeout(original_timeout)

        # =============== RESULTS (exclude first packet) ===============
        latencies = all_latencies[1:]  # packets 2 to 10 → 9 total
        total_packets = len(latencies)
        received = sum(1 for x in latencies if x is not None)
        lost = total_packets - received
        loss_pct = (lost / total_packets) * 100 if total_packets > 0 else 0.0

        print(f"\n📊 UDP Test Results (excluding first packet):")
        print(f"   Total packets analyzed: {total_packets}")
        print(f"   Packets received: {received}")
        print(f"   Packets lost: {lost}")
        print(f"   Packet Loss: {loss_pct:.1f}%")

        avg = min_latency = max_latency = None
        if received > 0:
            valid = [x for x in latencies if x is not None]
            avg = sum(valid) / len(valid)
            min_latency = min(valid)
            max_latency = max(valid)
            print(f"   Latency - Avg: {avg:.2f} ms, Min: {min_latency:.2f} ms, Max: {max_latency:.2f} ms")
        else:
            print("   ❌ No successful measurements")

        # =============== PLOT ===============
        try:
            plt.figure(figsize=(9, 4.5))
            seq_nums = list(range(2, 11))  # [2,3,...,10]

            # Plot all points: show None as gaps (matplotlib skips NaN automatically)
            plot_latencies = [x if x is not None else float('nan') for x in latencies]
            plt.plot(seq_nums, plot_latencies, 'o-', color='#64b5f6', label="One-Way Latency (C→S)", linewidth=2, markersize=6)

            plt.xlabel("Packet #", fontsize=11)
            plt.ylabel("Latency (ms)", fontsize=11)
            plt.title("UDP Connection Test — Latency & Loss (Excluding First Packet)", fontsize=12, fontweight='bold')
            plt.grid(True, alpha=0.4)
            plt.xticks(seq_nums)
            plt.legend()

            # Stats box
            if received > 0:
                stats_text = (f"Packets: {received}/{total_packets}\n"
                            f"Loss: {loss_pct:.1f}%\n"
                            f"Avg: {avg:.2f} ms\n"
                            f"Min: {min_latency:.2f} ms\n"
                            f"Max: {max_latency:.2f} ms")
            else:
                stats_text = f"Packets: 0/{total_packets}\nLoss: 100.0%"

            plt.gcf().text(0.72, 0.68, stats_text,
                        fontsize=10,
                        bbox=dict(boxstyle="round,pad=0.4", facecolor="#2e3035", edgecolor="#555", alpha=0.9),
                        color="#e0e0e0",
                        verticalalignment='top')

            plt.tight_layout()
            plt.show()
        except Exception as e:
            self.logger.error(f"Plotting failed: {e}")
            print("✅ Test completed")    