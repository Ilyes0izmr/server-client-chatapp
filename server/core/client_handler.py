# server/core/client_handler.py
import socket
import threading
import json
import ssl
from datetime import datetime
from typing import Callable, Dict, Any
import time
from server.core.message_protocol import MessageProtocol, MessageType

class ClientHandler:
    """Handles individual TCP client connections using length-prefixed JSON protocol
    with optional SSL support (ssl_enabled flag)."""

    def __init__(self,
                 client_socket: socket.socket,
                 client_address: tuple,
                 remove_callback: Callable,
                 notify_callback: Callable,
                 message_callback: Callable = None,
                 ssl_enabled: bool = False):
        self.client_socket = client_socket
        self.client_address = client_address
        self.remove_callback = remove_callback
        self.notify_callback = notify_callback
        self.message_callback = message_callback
        self.is_running = True
        self.ssl_enabled = ssl_enabled

        self.client_id = f"{client_address[0]}:{client_address[1]}"
        # keep username generation like before
        self.username = f"User_{abs(hash(client_address)) % 10000}"

        self.thread = threading.Thread(
            target=self._handle_client,
            daemon=True,
            name=f"ClientHandler-{self.client_id}"
        )

        # Tunables
        self.buffer_size = 4096

    def start(self):
        print(f"🧵 Starting ClientHandler for {self.client_id} (ssl={self.ssl_enabled})")
        self.thread.start()

    def stop(self):
        print(f"⏹ Stopping ClientHandler for {self.client_id}")
        self.is_running = False

        # Attempt graceful shutdown but keep the socket reference for remove_callback
        try:
            # If socket is SSL-wrapped, unwrap before closing (best-effort)
            if self.ssl_enabled:
                # unwrap may raise if underlying socket already closed — catch exceptions
                try:
                    if hasattr(self.client_socket, "unwrap"):
                        # unwrap returns the underlying socket
                        try:
                            # Some implementations require calling shutdown first
                            try:
                                self.client_socket.shutdown(socket.SHUT_RDWR)
                            except Exception:
                                pass
                            # Attempt unwrap
                            underlying = self.client_socket.unwrap()
                            # Close the returned underlying socket
                            try:
                                underlying.close()
                            except Exception:
                                pass
                        except ssl.SSLError:
                            # If unwrap fails, just close the ssl socket
                            try:
                                self.client_socket.close()
                            except Exception:
                                pass
                    else:
                        # No unwrap method; fallback to normal shutdown/close
                        try:
                            self.client_socket.shutdown(socket.SHUT_RDWR)
                        except Exception:
                            pass
                        try:
                            self.client_socket.close()
                        except Exception:
                            pass
                except Exception:
                    # best-effort: close
                    try:
                        self.client_socket.close()
                    except Exception:
                        pass
            else:
                try:
                    self.client_socket.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
                try:
                    self.client_socket.close()
                except Exception:
                    pass
        except Exception:
            pass

        # Call remove_callback while we still have the socket reference (tcp_server keys by socket)
        try:
            if self.remove_callback:
                self.remove_callback(self.client_socket)
        except Exception as e:
            print(f"❌ Error calling remove_callback for {self.client_id}: {e}")

        # Null out socket reference
        self.client_socket = None

    def _handle_client(self):
        try:
            # set a small timeout so the loop can check is_running frequently
            self.client_socket.settimeout(1.0)

            # Send welcome using existing status send
            self._send_status_message(f"Welcome! Your username: {self.username}", sender="System")

            buffer = b""  # Byte buffer for partial messages

            while self.is_running:
                try:
                    data = self.client_socket.recv(self.buffer_size)
                    if not data:
                        print(f"📥 Client {self.client_id} closed connection")
                        break

                    buffer += data
                    print(f"📥 Received {len(data)} bytes from {self.client_id} (buffer: {len(buffer)}B)")

                    # Process all complete messages in buffer
                    while len(buffer) >= 4:
                        length_bytes = buffer[:4]
                        message_len = int.from_bytes(length_bytes, 'big')
                        print(f"🔍 Expected message length: {message_len} bytes")

                        # Safeguard: limit message size (1MB)
                        if message_len > 1024 * 1024:
                            print(f"❌ Invalid message length: {message_len}B (too large)")
                            buffer = b""
                            break

                        # If full message present, extract and process
                        if len(buffer) >= 4 + message_len:
                            json_data = buffer[4:4 + message_len]
                            buffer = buffer[4 + message_len:]  # Save leftover
                            try:
                                message_str = json_data.decode('utf-8')
                                print(f"🔍 Raw JSON received: {repr(message_str)}")
                                self._process_message(message_str)
                            except UnicodeDecodeError as e:
                                print(f"❌ Unicode decode error from {self.client_id}: {e}")
                                continue
                        else:
                            # Not enough bytes yet; wait for more
                            print(f"⏳ Incomplete message (have {len(buffer)-4}B, need {message_len}B)")
                            break

                except socket.timeout:
                    continue
                except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError) as e:
                    print(f"🔌 Connection lost with {self.client_id}: {e}")
                    break
                except ssl.SSLError as e:
                    print(f"❌ SSL error with {self.client_id}: {e}")
                    break
                except OSError as e:
                    if self.is_running:
                        print(f"⚠️ Socket error with {self.client_id}: {e}")
                    break

        except Exception as e:
            if self.is_running:
                print(f"🔥 CRITICAL in handler {self.client_id}: {e}")
                import traceback
                traceback.print_exc()
                try:
                    if self.notify_callback:
                        self.notify_callback(f"Client handler error: {e}", True)
                except Exception:
                    pass
        finally:
            self._cleanup()

    def _process_message(self, message_str: str):
        try:
            message_type, content, sender = MessageProtocol.decode_message(message_str)
            print(f"✅ Parsed message: type={message_type}, sender='{sender}', content='{content}'")

            if message_type is None:
                print(f"❌ Failed to decode message from {self.client_id}: {repr(message_str)}")
                return

            # Standardized client info
            client_info = {
                'identifier': self.client_id,
                'name': self.username,
                'address': self.client_address,
                'protocol': 'TCP',
                'ssl': self.ssl_enabled
            }

            if message_type == MessageType.MESSAGE:
                if self.message_callback:
                    self.message_callback(client_info, content)
                else:
                    print("❌ No message_callback set in ClientHandler!")

            elif message_type == MessageType.TEST:
                # Echo back a test reply
                self._send_test_message("")

            elif message_type == MessageType.STATUS:
                display_msg = f"{sender}: {content}" if sender else content
                if self.notify_callback:
                    self.notify_callback(display_msg)
                print(f"📢 Status: {display_msg}")

            elif message_type == MessageType.CONNECT:
                if content:
                    self.username = content
                    print(f"👤 Username set to: {self.username}")

            elif message_type == MessageType.DISCONNECT:
                print(f"👋 Disconnect requested by client {self.client_id}")
                self.is_running = False

        except Exception as e:
            print(f"❌ Error processing message from {self.client_id}: {e}")
            import traceback
            traceback.print_exc()

    def _cleanup(self):
        print(f"🧹 Cleaning up ClientHandler for {self.client_id}")
        self.is_running = False

        # Ensure socket closed and remove_callback invoked (if not already)
        if self.client_socket:
            try:
                # Ensure socket is closed
                try:
                    if self.ssl_enabled and hasattr(self.client_socket, "unwrap"):
                        # attempt unwrap then close underlying - best-effort
                        try:
                            underlying = self.client_socket.unwrap()
                            try:
                                underlying.close()
                            except Exception:
                                pass
                        except Exception:
                            try:
                                self.client_socket.close()
                            except Exception:
                                pass
                    else:
                        try:
                            self.client_socket.close()
                        except Exception:
                            pass
                except Exception:
                    try:
                        self.client_socket.close()
                    except Exception:
                        pass
            except Exception:
                pass

            # notify remove_callback (tcp_server expects the socket as key)
            try:
                if self.remove_callback:
                    self.remove_callback(self.client_socket)
            except Exception as e:
                print(f"❌ Error during cleanup remove_callback for {self.client_id}: {e}")

        # Final cleanup: null out socket reference
        self.client_socket = None

        if self.notify_callback:
            try:
                self.notify_callback(f"Client disconnected: {self.client_id}")
            except Exception:
                pass

    def get_client_info(self) -> dict:
        return {
            'identifier': self.client_id,
            'name': self.username,
            'address': self.client_address,
            'socket': self.client_socket,
            'ssl': self.ssl_enabled
        }

    def _send_raw_message(self, message_type: MessageType, content: str, sender: str = "server") -> bool:
        """Internal: Send a length-prefixed message. Handles SSL send errors."""
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

        except ssl.SSLError as e:
            print(f"❌ SSL send failed for {self.client_id}: {e}")
            # Clean up connection on SSL errors
            try:
                self._cleanup()
            except Exception:
                pass
            return False
        except Exception as e:
            print(f"❌ Send failed for {self.client_id}: {e}")
            try:
                self._cleanup()
            except Exception:
                pass
            return False

    def send_message(self, message: str) -> bool:
        """Public API: Send a chat message to this client"""
        return self._send_raw_message(MessageType.MESSAGE, message, "server")

    def _send_status_message(self, content: str, sender: str = "System") -> bool:
        return self._send_raw_message(MessageType.STATUS, content, sender)

    def _send_test_message(self, content: str):
        return self._send_raw_message(MessageType.TEST, content, "server")

    def _send_connect_ack(self, username: str) -> bool:
        return self._send_raw_message(MessageType.CONNECT, username, "server")

    def _send_disconnect_ack(self) -> bool:
        return self._send_raw_message(MessageType.DISCONNECT, "", "server")
