import socket
import re
import time
from datetime import datetime
from typing import Tuple, Optional, Any, Dict
from enum import Enum


class ValidationResult(Enum):
    """Validation result codes."""
    VALID = "valid"
    INVALID_IP = "invalid_ip"
    INVALID_PORT = "invalid_port"
    INVALID_FORMAT = "invalid_format"


def validate_ip(ip_address: str) -> bool:
    """
    Validate IP address format.
    
    Args:
        ip_address: IP address to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        # Check for localhost
        if ip_address.lower() in ['localhost', '127.0.0.1', '::1']:
            return True
            
        # Check IPv4 format
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if re.match(pattern, ip_address):
            parts = ip_address.split('.')
            if all(0 <= int(part) <= 255 for part in parts):
                return True
                
        # Check IPv6 format (basic check)
        if ':' in ip_address:
            socket.inet_pton(socket.AF_INET6, ip_address)
            return True
            
        return False
        
    except (ValueError, socket.error):
        return False


def validate_port(port: Any) -> bool:
    """
    Validate port number.
    
    Args:
        port: Port number to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        port_int = int(port)
        return 1 <= port_int <= 65535
    except (ValueError, TypeError):
        return False


def validate_address(host: str, port: Any) -> Tuple[bool, ValidationResult]:
    """
    Validate both IP address and port.
    
    Args:
        host: Host IP address
        port: Port number
        
    Returns:
        Tuple of (is_valid, validation_result)
    """
    if not validate_ip(host):
        return False, ValidationResult.INVALID_IP
        
    if not validate_port(port):
        return False, ValidationResult.INVALID_PORT
        
    return True, ValidationResult.VALID


def get_local_ip() -> str:
    """
    Get the local IP address of the machine.
    
    Returns:
        str: Local IP address
    """
    try:
        # Connect to a remote address to determine local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"  # Fallback to localhost


def format_timestamp(timestamp: Optional[float] = None, 
                    format_str: str = "%H:%M:%S") -> str:
    """
    Format timestamp to readable string.
    
    Args:
        timestamp: Unix timestamp (default: current time)
        format_str: Format string for datetime
        
    Returns:
        str: Formatted timestamp string
    """
    if timestamp is None:
        timestamp = time.time()
    
    return datetime.fromtimestamp(timestamp).strftime(format_str)


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        str: Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        str: Sanitized text
    """
    if not text:
        return ""
    
    # Trim to max length
    text = text[:max_length]
    
    # Remove potentially dangerous characters
    text = re.sub(r'[<>"\'&]', '', text)
    
    # Remove excessive whitespace
    text = ' '.join(text.split())
    
    return text


def format_client_info(client_info: Dict) -> str:
    """
    Format client information for display.
    
    Args:
        client_info: Client information dictionary
        
    Returns:
        str: Formatted client info string
    """
    identifier = client_info.get('identifier', 'Unknown')
    name = client_info.get('name', 'Unknown')
    ip = client_info.get('ip', 'Unknown')
    port = client_info.get('port', 'Unknown')
    
    return f"{name} ({identifier}) - {ip}:{port}"


def calculate_uptime(start_time: float) -> str:
    """
    Calculate server uptime from start timestamp.
    
    Args:
        start_time: Server start timestamp
        
    Returns:
        str: Formatted uptime string
    """
    uptime_seconds = time.time() - start_time
    return format_duration(uptime_seconds)


def is_valid_username(username: str) -> bool:
    """
    Validate username format.
    
    Args:
        username: Username to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not username or len(username) > 20:
        return False
    
    # Allow alphanumeric, underscore, and hyphen
    pattern = r'^[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, username))


def get_available_port(start_port: int = 5000, end_port: int = 6000) -> Optional[int]:
    """
    Find an available port in the specified range.
    
    Args:
        start_port: Start of port range
        end_port: End of port range
        
    Returns:
        Optional[int]: Available port number or None if none found
    """
    for port in range(start_port, end_port + 1):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    return None