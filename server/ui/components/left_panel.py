from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QToolButton, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QCursor
import qtawesome as qta


# 🌌 NEBULA REVIVAL — Compact 60px Edition
NEBULA_STYLES = """
#leftPanel {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #0c121c,
        stop:1 #0f1522
    );
    border-right: 1px solid #1e2a3a;
}

QFrame#edgeSeparator {
    background: #1e2a3a;
    max-height: 1px;
    min-height: 1px;
    height: 1px;
    border: none;
    margin: 0;
}

QToolButton {
    background: transparent;
    border: none;
    padding: 6px;
    margin: 5px 0;
    border-radius: 8px;
    transition: background 0.2s ease;
}

QToolButton:hover {
    background: rgba(0, 220, 255, 0.12);
}

QToolButton:pressed {
    background: rgba(0, 220, 255, 0.20);
}

#tcpButton[running="true"],
#udpButton[running="true"] {
    color: #00dcff;
}

#tcpButton[running="true"]:hover,
#udpButton[running="true"]:hover {
    background: rgba(0, 220, 255, 0.18);
}

#tcpButton[running="true"]:pressed,
#udpButton[running="true"]:pressed {
    background: rgba(0, 220, 255, 0.25);
}

#tcpButton, #udpButton, 
#shutdownButton:disabled {
    color: #c5d9fd;
}

#shutdownButton {
    border-radius: 24px; /* 48px/2 = perfect circle */
}

#shutdownButton:enabled {
    color: #ff5252;
}

#shutdownButton:enabled:hover {
    background: rgba(255, 82, 82, 0.15);
}

#shutdownButton:enabled:pressed {
    background: rgba(255, 82, 82, 0.25);
}
"""


class EdgeSeparator(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFrameShadow(QFrame.Shadow.Sunken)
        self.setObjectName("edgeSeparator")


class LeftPanel(QFrame):
    tcp_server_toggled = pyqtSignal(bool)
    udp_server_toggled = pyqtSignal(bool)
    shutdown_servers = pyqtSignal()

    ICON_SIZE = QSize(26, 26)  # Optimized for 48px buttons

    def __init__(self):
        super().__init__()
        self.is_tcp_running = False
        self.is_udp_running = False
        self.setup_ui()
        self.setStyleSheet(NEBULA_STYLES)

    def setup_ui(self):
        self.setObjectName("leftPanel")
        self.setFixedWidth(60)  # ✅ Compact

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 16, 6, 16)  # Reduced L/R padding
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # ─── Logo ───────────────────────────────────────────────────────────────
        logo_icon = QLabel()
        logo_icon.setPixmap(
            qta.icon("fa5s.tachometer-alt", color="#c5d9fd", scale_factor=1)
            .pixmap(QSize(24, 24))  # Smaller, cleaner
        )
        logo_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_icon)

        layout.addSpacing(16)  # ↓ from 20
        layout.addWidget(EdgeSeparator())
        layout.addSpacing(12)  # ↓ from 15

        # ─── TCP Button ─────────────────────────────────────────────────────────
        self.tcp_btn = self._create_icon_button(
            icon_stopped="fa5s.arrow-alt-circle-right",
            icon_running="fa5s.circle",
            obj_name="tcpButton"
        )
        self.tcp_btn.clicked.connect(self.toggle_tcp_server)
        layout.addWidget(self.tcp_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        layout.addSpacing(10)  # ↓ from 12

        # ─── UDP Button ─────────────────────────────────────────────────────────
        self.udp_btn = self._create_icon_button(
            icon_stopped="mdi6.cloud-arrow-right",
            icon_running="mdi6.cloud-check",
            obj_name="udpButton"
        )
        self.udp_btn.clicked.connect(self.toggle_udp_server)
        layout.addWidget(self.udp_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        layout.addSpacing(10)  # ↓ from 12

        # ─── Shutdown Button ────────────────────────────────────────────────────
        self.shutdown_btn = QToolButton()
        self.shutdown_btn.setIconSize(self.ICON_SIZE)
        self.shutdown_btn.setFixedSize(48, 48)  # ✅ 48×48 fits 60px perfectly
        self.shutdown_btn.setObjectName("shutdownButton")
        self.shutdown_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.shutdown_btn.clicked.connect(self.handle_shutdown)
        self.shutdown_btn.setToolTip("Shutdown All Servers")
        self.shutdown_btn.setEnabled(False)
        self._update_shutdown_state()
        layout.addWidget(self.shutdown_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        layout.addStretch()

    def _create_icon_button(self, icon_stopped, icon_running, obj_name):
        btn = QToolButton()
        btn.setFixedSize(48, 48)  # ✅ Critical: match shutdown size
        btn.setIconSize(self.ICON_SIZE)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.setObjectName(obj_name)
        self._update_button_icon(btn, icon_stopped, icon_running, False)
        return btn

    def _update_button_icon(self, btn, icon_stopped, icon_running, running):
        color = "#00dcff" if running else "#c5d9fd"
        icon_name = icon_running if running else icon_stopped
        icon = qta.icon(icon_name, color=color, scale_factor=1.0)
        btn.setIcon(icon)
        btn.setProperty("running", running)
        server_type = btn.objectName().replace("Button", "").upper()
        btn.setToolTip(f"{'Stop' if running else 'Start'} {server_type} Server")
        btn.style().unpolish(btn)
        btn.style().polish(btn)

    # Handlers unchanged — logic remains robust
    def toggle_tcp_server(self):
        self.is_tcp_running = not self.is_tcp_running
        self._update_button_icon(self.tcp_btn, "fa5s.arrow-alt-circle-right", "fa5s.circle", self.is_tcp_running)
        self.tcp_server_toggled.emit(self.is_tcp_running)
        self._update_shutdown_state()

    def toggle_udp_server(self):
        self.is_udp_running = not self.is_udp_running
        self._update_button_icon(self.udp_btn, "mdi6.cloud-arrow-right", "mdi6.cloud-check", self.is_udp_running)
        self.udp_server_toggled.emit(self.is_udp_running)
        self._update_shutdown_state()

    def _update_shutdown_state(self):
        any_running = self.is_tcp_running or self.is_udp_running
        self.shutdown_btn.setEnabled(any_running)
        color = "#ff5252" if any_running else "#c5d9fd"  # ✅ Use #c5d9fd when disabled (not #ffffff)
        self.shutdown_btn.setIcon(qta.icon("fa5s.power-off", color=color, scale_factor=1.0))

    def handle_shutdown(self):
        was_any = self.is_tcp_running or self.is_udp_running
        self.is_tcp_running = self.is_udp_running = False
        if was_any:
            self.tcp_server_toggled.emit(False)
            self.udp_server_toggled.emit(False)
            self.shutdown_servers.emit()
        self._update_button_icon(self.tcp_btn, "fa5s.arrow-alt-circle-right", "fa5s.circle", False)
        self._update_button_icon(self.udp_btn, "mdi6.cloud-arrow-right", "mdi6.cloud-check", False)
        self._update_shutdown_state()