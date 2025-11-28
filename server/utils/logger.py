import logging
import os
import sys
from datetime import datetime
from typing import Optional


def setup_logging(
    name: str,
    log_level: int = logging.INFO,
    log_to_file: bool = True,
    log_dir: str = "logs"
) -> logging.Logger:
    """
    Set up logging configuration for a module.
    
    Args:
        name: Logger name (usually __name__)
        log_level: Logging level (default: INFO)
        log_to_file: Whether to log to file (default: True)
        log_dir: Directory for log files (default: "logs")
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    if log_to_file:
        try:
            # Create logs directory if it doesn't exist
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            # Create log file with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = os.path.join(log_dir, f"server_{timestamp}.log")
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
        except Exception as e:
            print(f"Failed to setup file logging: {e}")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return setup_logging(name)


class ServerLogger:
    """
    Enhanced logger with server-specific functionality.
    """
    
    def __init__(self, name: str, server_type: str = "UDP"):
        self.logger = get_logger(name)
        self.server_type = server_type
        
    def server_start(self, host: str, port: int):
        """Log server startup."""
        self.logger.info(f"{self.server_type} Server started on {host}:{port}")
        
    def server_stop(self):
        """Log server shutdown."""
        self.logger.info(f"{self.server_type} Server stopped")
        
    def client_connected(self, client_id: str, client_info: dict):
        """Log client connection."""
        self.logger.info(f"Client connected: {client_id} - {client_info}")
        
    def client_disconnected(self, client_id: str):
        """Log client disconnection."""
        self.logger.info(f"Client disconnected: {client_id}")
        
    def message_sent(self, client_id: str, message: str):
        """Log message sent to client."""
        self.logger.debug(f"Message sent to {client_id}: {message}")
        
    def message_received(self, client_id: str, message: str):
        """Log message received from client."""
        self.logger.debug(f"Message received from {client_id}: {message}")
        
    def error(self, error_msg: str, exc_info: bool = False):
        """Log error with optional exception info."""
        self.logger.error(error_msg, exc_info=exc_info)
        
    def warning(self, warning_msg: str):
        """Log warning."""
        self.logger.warning(warning_msg)