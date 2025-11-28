from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton, QWidget
from PyQt6.QtCore import Qt, pyqtSignal
from server.ui.components.styles import STYLES

class Separator(QWidget):
    """Horizontal separator line"""
    
    def __init__(self):
        super().__init__()
        self.setFixedHeight(2)
        self.setObjectName("separator")

class LeftPanel(QFrame):
    """Left control panel with server controls - Purple theme"""
    
    # Signals
    tcp_server_toggled = pyqtSignal(bool)
    udp_server_toggled = pyqtSignal(bool)
    shutdown_servers = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.is_tcp_running = False
        self.is_udp_running = False
        self.setup_ui()
        self.apply_styles()
        
    def setup_ui(self):
        # Panel setup ------------------------------------------------------------
        self.setObjectName("leftPanel")
        self.setFixedWidth(180)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 20, 10, 20)
        layout.setSpacing(15)
        
        # Logo Section ------------------------------------------------------------
        logo = QLabel("CHAT SERV")
        logo.setObjectName("logo")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo)
        
        layout.addWidget(Separator())
        
        # TCP Server Section ------------------------------------------------------------
        self.tcp_btn = QPushButton("START TCP SERVER")
        self.tcp_btn.setObjectName("tcpButton")
        self.tcp_btn.clicked.connect(self.toggle_tcp_server)
        layout.addWidget(self.tcp_btn)
        
        # UDP Server Section ------------------------------------------------------------
        self.udp_btn = QPushButton("START UDP SERVER")
        self.udp_btn.setObjectName("udpButton")
        self.udp_btn.clicked.connect(self.toggle_udp_server)
        layout.addWidget(self.udp_btn)
        
        layout.addWidget(Separator())
        
        # Shutdown Section ------------------------------------------------------------
        self.shutdown_btn = QPushButton("SHUTDOWN SERVERS")
        self.shutdown_btn.setObjectName("shutdownButton")
        self.shutdown_btn.clicked.connect(self.handle_shutdown)
        self.shutdown_btn.setEnabled(False)
        layout.addWidget(self.shutdown_btn)
        
        layout.addStretch()
        
    def apply_styles(self):
        """Apply CSS styles from styles.py"""
        self.setStyleSheet(STYLES['left_panel'])
        
    def toggle_tcp_server(self):
        """Toggle TCP server state"""
        self.is_tcp_running = not self.is_tcp_running
        self.update_button_states()
        self.tcp_server_toggled.emit(self.is_tcp_running)
        
    def toggle_udp_server(self):
        """Toggle UDP server state"""
        self.is_udp_running = not self.is_udp_running
        self.update_button_states()
        self.udp_server_toggled.emit(self.is_udp_running)
        
    def handle_shutdown(self):
        """Handle shutdown - stop both servers"""
        if self.is_tcp_running:
            self.is_tcp_running = False
            self.tcp_server_toggled.emit(False)
            
        if self.is_udp_running:
            self.is_udp_running = False
            self.udp_server_toggled.emit(False)
            
        self.update_button_states()
        self.shutdown_servers.emit()
        
    def update_button_states(self):
        """Update button states and appearances"""
        # TCP Button
        self.tcp_btn.setProperty("running", self.is_tcp_running)
        self.tcp_btn.setText("STOP TCP SERVER" if self.is_tcp_running else "START TCP SERVER")
        self.tcp_btn.style().unpolish(self.tcp_btn)
        self.tcp_btn.style().polish(self.tcp_btn)
        
        # UDP Button
        self.udp_btn.setProperty("running", self.is_udp_running)
        self.udp_btn.setText("STOP UDP SERVER" if self.is_udp_running else "START UDP SERVER")
        self.udp_btn.style().unpolish(self.udp_btn)
        self.udp_btn.style().polish(self.udp_btn)
        
        # Shutdown Button - enable only if any server is running
        any_server_running = self.is_tcp_running or self.is_udp_running
        self.shutdown_btn.setEnabled(any_server_running)