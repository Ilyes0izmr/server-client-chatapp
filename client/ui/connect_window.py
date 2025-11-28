from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QGroupBox, QMessageBox,
    QRadioButton, QButtonGroup
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QIntValidator
from pathlib import Path


class ConnectWindow(QWidget):

    connected = pyqtSignal(str, int, str, str)

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.apply_styles()
        self.connect_btn.setProperty("class", "accent")


    def init_ui(self):
        self.setWindowTitle("Connect")
        self.setFixedSize(500, 520)

        main = QVBoxLayout(self)
        main.setContentsMargins(20, 20, 20, 20)
        main.setSpacing(16)

        # Title
        title = QLabel("CHATCLIENT")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main.addWidget(title)

        subtitle = QLabel("Connect to Chat Server")
        subtitle.setObjectName("subtitleLabel")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main.addWidget(subtitle)

        # --- SERVER GROUP ---
        server_box = QGroupBox("Server Settings")
        server_layout = QVBoxLayout(server_box)
        server_layout.setSpacing(12)

        # protocol
        proto_label = QLabel("Protocol")
        proto_label.setStyleSheet("font-weight:600;")
        server_layout.addWidget(proto_label)

        proto_row = QHBoxLayout()

        self.tcp = QRadioButton("TCP")
        self.tcp.setChecked(True)
        self.udp = QRadioButton("UDP")

        self.proto_group = QButtonGroup(self)
        self.proto_group.addButton(self.tcp)
        self.proto_group.addButton(self.udp)

        proto_row.addWidget(self.tcp)
        proto_row.addWidget(self.udp)
        proto_row.addStretch()

        server_layout.addLayout(proto_row)

        # Host row
        host_row = QHBoxLayout()
        host_row.addWidget(QLabel("Host:"))
        self.host_input = QLineEdit("localhost")
        self.host_input.setPlaceholderText("Server address")
        self.host_input.setMinimumHeight(38)
        host_row.addWidget(self.host_input)
        server_layout.addLayout(host_row)

        # Port row
        port_row = QHBoxLayout()
        port_row.addWidget(QLabel("Port:"))
        self.port_input = QLineEdit("5050")
        self.port_input.setPlaceholderText("Server port")
        self.port_input.setMinimumHeight(38)
        self.port_input.setValidator(QIntValidator(1, 65535))
        port_row.addWidget(self.port_input)
        server_layout.addLayout(port_row)

        main.addWidget(server_box)

        # --- USER GROUP ---
        user_box = QGroupBox("User Settings")
        user_layout = QVBoxLayout(user_box)
        user_layout.setSpacing(12)

        user_row = QHBoxLayout()
        user_row.addWidget(QLabel("Username:"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Display name")
        self.username_input.setMinimumHeight(38)
        user_row.addWidget(self.username_input)
        user_layout.addLayout(user_row)

        main.addWidget(user_box)

        # connect button
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setProperty("class", "accent")
        self.connect_btn.setMinimumHeight(42)
        self.connect_btn.clicked.connect(self.connect_to_server)
        main.addWidget(self.connect_btn)

        # status text
        self.status = QLabel("Ready")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setObjectName("statusText")
        main.addWidget(self.status)

        main.addStretch()

    # -----------------------------------------------------------

    def apply_styles(self):
        css = Path(__file__).parent / "styles.css"
        if css.exists():
            from PyQt6.QtWidgets import QApplication
            QApplication.instance().setStyleSheet(css.read_text())

    # -----------------------------------------------------------

        # -----------------------------------------------------------
    # Compatibility method – needed because main.py still calls it
    # -----------------------------------------------------------
    def set_connecting(self, connecting: bool, status_message: str = ""):
        """Keep compatibility with the old logic."""
        self.connect_btn.setEnabled(not connecting)
        self.host_input.setEnabled(not connecting)
        self.port_input.setEnabled(not connecting)
        self.username_input.setEnabled(not connecting)
        self.tcp.setEnabled(not connecting)
        self.udp.setEnabled(not connecting)

        if connecting:
            self.connect_btn.setText("Connecting…")
            self.status.setText(status_message or "Connecting…")
        else:
            self.connect_btn.setText("Connect")
            self.status.setText(status_message or "Ready")


    def connect_to_server(self):

        host = self.host_input.text().strip()
        port = self.port_input.text().strip()
        user = self.username_input.text().strip()
        protocol = "TCP" if self.tcp.isChecked() else "UDP"

        if not host:
            return self.error("Enter server host")
        if not port:
            return self.error("Enter port number")
        if not user:
            return self.error("Enter username")

        try:
            p = int(port)
            if not (1 <= p <= 65535):
                raise ValueError
        except:
            return self.error("Invalid port (1–65535)")

        self.status.setText(f"Connecting via {protocol}…")
        self.connected.emit(host, p, user, protocol)

    # -----------------------------------------------------------

    def show_success(self, message):
        """Compatibility with old main.py"""
        self.status.setText(message)

    def set_connecting(self, connecting: bool, status_message: str = ""):
        """Compatibility with old main.py."""
        self.connect_btn.setEnabled(not connecting)
        self.host_input.setEnabled(not connecting)
        self.port_input.setEnabled(not connecting)
        self.username_input.setEnabled(not connecting)
        self.tcp.setEnabled(not connecting)
        self.udp.setEnabled(not connecting)

        if connecting:
            self.connect_btn.setText("Connecting…")
            self.status.setText(status_message or "Connecting…")
        else:
            self.connect_btn.setText("Connect")
            self.status.setText(status_message or "Ready")

    def reset(self):
        """Restore input fields after disconnect."""
        self.connect_btn.setEnabled(True)
        self.connect_btn.setText("Connect")

        self.host_input.setEnabled(True)
        self.port_input.setEnabled(True)
        self.username_input.setEnabled(True)
        self.tcp.setEnabled(True)
        self.udp.setEnabled(True)

        self.status.setText("Ready")

    def disconnect(self):
        self.disconnected.emit()
        self.close()


    def error(self, msg):
        QMessageBox.critical(self, "Error", msg)
        self.status.setText("Error")
