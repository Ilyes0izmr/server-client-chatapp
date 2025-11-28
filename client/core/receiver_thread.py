import threading
import time
import logging
from typing import Callable, Optional
from .message_protocol import ChatMessage

class ReceiverThread(threading.Thread):
    """Dedicated thread for receiving messages"""
    
    def __init__(self, receive_function: Callable[[], Optional[ChatMessage]], 
                 callback: Callable[[ChatMessage], None],
                 check_interval: float = 0.1):
        super().__init__(daemon=True)
        self.receive_function = receive_function
        self.callback = callback
        self.check_interval = check_interval
        self.should_run = True
        self.logger = logging.getLogger(__name__)
    
    def run(self):
        """Main thread loop"""
        self.logger.info("Receiver thread started")
        while self.should_run:
            try:
                message = self.receive_function()
                if message and self.callback:
                    self.callback(message)
            except Exception as e:
                self.logger.error(f"Error in receiver thread: {e}")
            
            time.sleep(self.check_interval)
        
        self.logger.info("Receiver thread stopped")
    
    def stop(self):
        """Stop the receiver thread"""
        self.should_run = False