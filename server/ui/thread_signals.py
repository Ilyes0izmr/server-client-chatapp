from PyQt6.QtCore import QObject, pyqtSignal

class ThreadSignals(QObject):
    """Thread-safe signals for cross-thread communication"""
    
    # Client management signals
    client_connected = pyqtSignal(dict)  # client_info
    client_disconnected = pyqtSignal(dict)  # client_info
    server_status = pyqtSignal(str, bool)  # message, is_error
    server_message = pyqtSignal(dict, str)  # client_info, message