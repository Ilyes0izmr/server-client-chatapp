from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QStatusBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QDateTime
from PyQt6.QtGui import QTextCursor, QFont
from pathlib import Path

from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtCore import Qt

class MessageInput(QTextEdit):
    '''
        to add custom behavior for ENTER key
    '''
    enter_pressed = pyqtSignal()  # signal to tell ChatWindow to send

    def __init__(self):
        super().__init__()

    def keyPressEvent(self, event: QKeyEvent):
        # SHIFT + ENTER → newline
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
                return super().keyPressEvent(event)

            # ENTER alone → send
            self.enter_pressed.emit()
            return  # block normal newline

        # otherwise normal behavior
        return super().keyPressEvent(event)


class ChatWindow(QMainWindow):

    message_sent = pyqtSignal(str)
    disconnected = pyqtSignal()

    def __init__(self, username, host, port, protocol):
        super().__init__()
        self.username = username
        self.host = host
        self.port = port
        self.protocol = protocol
        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        self.setWindowTitle(f"Chat - {self.username}")
        self.resize(900, 600)

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        info = QLabel(f"Connected to {self.host}:{self.port} ({self.protocol})")
        info.setObjectName("topInfo")
        header.addWidget(info)
        header.addStretch()

        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.setProperty("class", "disconnect")
        self.disconnect_btn.clicked.connect(self.disconnect)
        header.addWidget(self.disconnect_btn)

        self.test_btn = QPushButton("Test Connection")
        self.test_btn.setProperty("class", "accent")  # or create new style
        self.test_btn.clicked.connect(self._run_test)
        header.addWidget(self.test_btn)

        layout.addLayout(header)

        # Chat feed
        self.chat_display = QTextEdit()
        self.chat_display.setObjectName("chatDisplay")
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Consolas", 11))
        layout.addWidget(self.chat_display)

        # Bottom input
        bottom = QHBoxLayout()
        bottom.setContentsMargins(0, 0, 0, 0)
        bottom.setSpacing(8)

        self.message_input = MessageInput()
        self.message_input.enter_pressed.connect(self._send_msg)
        self.message_input.setMinimumHeight(32)
        self.message_input.setMaximumHeight(80)
        self.message_input.textChanged.connect(
            lambda: self.send_btn.setEnabled(bool(self.message_input.toPlainText().strip()))
        )
        bottom.addWidget(self.message_input)

        self.send_btn = QPushButton("Send")
        self.send_btn.setProperty("class", "accent")
        self.send_btn.setEnabled(False)
        self.send_btn.clicked.connect(self._send_msg)
        bottom.addWidget(self.send_btn)

        layout.addLayout(bottom)

        # Status
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Connected")

    def apply_styles(self):
        css = Path(__file__).parent / "styles.css"
        if css.exists():
            from PyQt6.QtWidgets import QApplication
            QApplication.instance().setStyleSheet(css.read_text())

    # ----------------------------
    # Messaging
    # ----------------------------

    def update_status(self, message, ok=True):
        """Compatibility with old code."""
        icon = "🟣" if ok else "🔴"
        try:
            self.status.showMessage(f"{icon} {message}")
        except:
            pass


    def _send_msg(self):
        msg = self.message_input.toPlainText().rstrip()

        if not msg:
            return
        self.message_input.clear()

        # DO NOT ADD MESSAGE HERE — prevent duplicates
        self.message_sent.emit(msg)

    def add_message(self, message, is_own=False, is_system=False):
        ts = QDateTime.currentDateTime().toString("HH:mm")

        # Escape HTML symbols
        message = message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        message = message.replace("\n", "<br>")

        if is_system:
            html = f"""
            <div style="
                color:#bbaaff;
                font-style:italic;
                margin:6px 0;
            ">
                [{ts}] {message}
            </div>
            """
        elif is_own:
            # RIGHT aligned
            html = f"""
            <div style="
                text-align:right;
                margin:8px 0;
                padding:6px 10px;
                background:#35363b;
                border-radius:6px;
                display:inline-block;
                float:right;
                max-width:70%;
                clear:both;
            ">
                <span style="color:#ffffff;">[{ts}]</span>
                <span style="color:#d4c5ff;">You:</span>
                <span style="color:#ffffff;"> {message}</span>
            </div>
            <div style="clear:both;"></div>
            """
        else:
            # LEFT aligned
            html = f"""
            <div style="
                text-align:left;
                margin:8px 0;
                padding:6px 10px;
                background:#2e3035;
                border-radius:6px;
                display:inline-block;
                float:left;
                max-width:70%;
                clear:both;
            ">
                <span style="color:#ffffff;">[{ts}]</span>
                <span style="color:#c6d4ff;">Server:</span>
                <span style="color:#ffffff;"> {message}</span>
            </div>
            <div style="clear:both;"></div>
            """

        self.chat_display.append(html)
        self.chat_display.moveCursor(QTextCursor.MoveOperation.End)



    def _run_test(self):
        if hasattr(self, 'client') and self.client and self.client.is_connected:
            self.update_status("Running connection test...", True)
            try:
                
                self.client.connection_test_calculation()
                self.update_status("Test completed", True)
            except Exception as e:
                self.add_message(f"Test failed: {e}", is_system=True)
                self.update_status("Test failed", False)
        else:
            self.add_message("❌ Not connected — cannot run test", is_system=True)
            self.update_status("Not connected", False)
    # ----------------------------
    def disconnect(self):
        self.disconnected.emit()
        self.close()
