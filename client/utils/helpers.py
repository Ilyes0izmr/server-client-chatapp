import socket

def get_local_ip():
    """Get local IP address"""
    try:
        # Connect to a remote address to determine local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except:
        return "127.0.0.1"

def is_valid_ip(ip):
    """Check if string is valid IP address"""
    try:
        socket.inet_pton(socket.AF_INET, ip)
        return True
    except socket.error:
        return False

def is_valid_port(port):
    """Check if port is valid"""
    try:
        return 1 <= int(port) <= 65535
    except ValueError:
        return False