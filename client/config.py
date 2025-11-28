import os

class ClientConfig:
    """Client configuration settings"""
    DEFAULT_HOST = "localhost"
    DEFAULT_TCP_PORT = 5050
    DEFAULT_UDP_PORT = 5051
    BUFFER_SIZE = 4096
    ENCODING = "utf-8"
    TIMEOUT = 10  # seconds
    
    @classmethod
    def get_tcp_config(cls):
        return {
            "host": os.getenv("CHAT_SERVER_HOST", cls.DEFAULT_HOST),
            "port": int(os.getenv("CHAT_SERVER_TCP_PORT", cls.DEFAULT_TCP_PORT)),
            "buffer_size": cls.BUFFER_SIZE,
            "encoding": cls.ENCODING,
            "timeout": cls.TIMEOUT
        }
    
    @classmethod
    def get_udp_config(cls):
        return {
            "host": os.getenv("CHAT_SERVER_HOST", cls.DEFAULT_HOST),
            "port": int(os.getenv("CHAT_SERVER_UDP_PORT", cls.DEFAULT_UDP_PORT)),
            "buffer_size": cls.BUFFER_SIZE,
            "encoding": cls.ENCODING,
            "timeout": cls.TIMEOUT
        }