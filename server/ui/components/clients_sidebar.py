from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QScrollArea, QWidget)
from PyQt6.QtCore import Qt, pyqtSignal

class ClientItem(QFrame):
    client_kicked = pyqtSignal(str)
    client_clicked = pyqtSignal(str)
    
    def __init__(self, client_id: str, client_data: dict):
        super().__init__()
        self.client_id = client_id
        self.client_data = client_data
        self.is_selected = False
        self.setup_ui()
        self.apply_styles()
        
    def setup_ui(self):
        self.setObjectName("clientItem")
        self.setFixedHeight(72)  # tighter height
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)
        
        # Top row: Name, protocol, kick
        top_layout = QHBoxLayout()
        
        # Name
        self.name_label = QLabel(self.client_data.get('username', self.client_id))
        self.name_label.setObjectName("clientName")
        top_layout.addWidget(self.name_label)
        top_layout.addStretch()
        
        # Kick button
        self.kick_btn = QPushButton("✕")
        self.kick_btn.setObjectName("kickButton")
        self.kick_btn.setFixedSize(24, 24)
        self.kick_btn.clicked.connect(self.on_kick_clicked)
        top_layout.addWidget(self.kick_btn)
        
        layout.addLayout(top_layout)
        
        # Protocol + ID row
        protocol = self.client_data.get('protocol', 'TCP')
        protocol_color = "#00dcff" if protocol == "TCP" else "#64b5f6"
        self.protocol_label = QLabel(f"<span style='color:{protocol_color}'>{protocol}</span> • {self.client_id[:6]}…")
        self.protocol_label.setObjectName("clientProtocol")
        layout.addWidget(self.protocol_label)
        
        # Status dot (subtle)
        status_layout = QHBoxLayout()
        status_dot = QLabel("●")
        status_dot.setStyleSheet("color: #00dcff; font-size: 14px;")
        status_layout.addWidget(status_dot)
        status_layout.addWidget(QLabel("Online"))
        status_layout.addStretch()
        layout.addLayout(status_layout)
        
    def apply_styles(self):
        # Base style — will be overridden on hover/select
        self.setStyleSheet(self.get_style(False, False))
        
    def get_style(self, hovered=False, selected=False):
        bg = "#141a26" if hovered else "#0f1420"
        border_color = "#00dcff" if selected else ("#1e2a3a" if hovered else "#182232")
        border_width = "2px" if selected else "1px"
        return f"""
            #clientItem {{
                background-color: {bg};
                border: {border_width} solid {border_color};
                border-radius: 10px;
                margin: 3px 0;
            }}
            #clientName {{
                color: #c5d9fd;
                font-weight: 600;
                font-size: 13px;
            }}
            #clientProtocol {{
                color: #8a9cb5;
                font-size: 11px;
            }}
            #kickButton {{
                background-color: #ff5252;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
                padding: 0;
            }}
            #kickButton:hover {{
                background-color: #ff6b6b;
            }}
        """
        
    def enterEvent(self, event):
        self.setStyleSheet(self.get_style(hovered=True, selected=self.is_selected))
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self.setStyleSheet(self.get_style(hovered=False, selected=self.is_selected))
        super().leaveEvent(event)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.client_clicked.emit(self.client_id)
        super().mousePressEvent(event)
        
    def on_kick_clicked(self):
        self.client_kicked.emit(self.client_id)

    def set_selected(self, selected: bool):
        self.is_selected = selected
        hovered = self.underMouse()
        self.setStyleSheet(self.get_style(hovered=hovered, selected=selected))


class ClientsSidebar(QFrame):
    client_kicked = pyqtSignal(str)
    client_selected = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.clients = {}
        self.current_selected = None
        self.setup_ui()
        self.apply_styles()
        
    def setup_ui(self):
        self.setObjectName("clientsSidebar")
        self.setFixedWidth(300)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(2)
        
        # Header
        header = QLabel("CLIENTS ONLINE")
        header.setObjectName("clientsHeader")
        header.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(header)
        
        # Count
        self.clients_count = QLabel("0 connected")
        self.clients_count.setObjectName("clientsCount")
        self.clients_count.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.clients_count)
        
        # Separator — matched to main panel
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setObjectName("edgeSeparator")
        layout.addWidget(separator)
        
        # Scroll area
        self.clients_scroll = QScrollArea()
        self.clients_scroll.setObjectName("clientsScroll")
        self.clients_scroll.setWidgetResizable(True)
        self.clients_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.clients_widget = QWidget()
        self.clients_layout = QVBoxLayout(self.clients_widget)
        self.clients_layout.setContentsMargins(5, 5, 5, 5)
        self.clients_layout.setSpacing(6)
        self.clients_layout.addStretch()
        
        self.clients_scroll.setWidget(self.clients_widget)
        layout.addWidget(self.clients_scroll)
        
    def apply_styles(self):
        self.setStyleSheet("""
            #clientsSidebar {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0c121c,
                    stop:1 #0f1522
                );
                border-right: 1px solid #1e2a3a;
            }
            #clientsHeader {
                color: #c5d9fd;
                font-size: 15px;
                font-weight: 600;
            }
            #clientsCount {
                color: #8a9cb5;
                font-size: 12px;
                margin-bottom: 4px;
            }
            #edgeSeparator {
                background: #1e2a3a;
                max-height: 1px;
                min-height: 1px;
            }
            #clientsScroll {
                background: transparent;
                border: none;
            }
            #clientsScroll QWidget {
                background: transparent;
            }
        """)
        
    def add_client(self, client_id: str, client_data: dict):
        if client_id in self.clients:
            return
            
        self.clients[client_id] = client_data
        client_item = ClientItem(client_id, client_data)
        client_item.client_kicked.connect(self.client_kicked.emit)
        client_item.client_clicked.connect(self.on_client_clicked)
        
        self.clients_layout.insertWidget(self.clients_layout.count() - 1, client_item)
        self.update_clients_count()
        
    def remove_client(self, client_id: str):
        if client_id not in self.clients:
            return
            
        for i in range(self.clients_layout.count() - 1):
            widget = self.clients_layout.itemAt(i).widget()
            if widget and getattr(widget, 'client_id', None) == client_id:
                widget.deleteLater()
                break
                
        self.clients.pop(client_id, None)
        
        if self.current_selected == client_id:
            self.current_selected = None
            self.client_selected.emit("")  # deselect
            
        self.update_clients_count()
        
    def on_client_clicked(self, client_id: str):
        # Deselect previous
        if self.current_selected:
            prev = self._find_client_item(self.current_selected)
            if prev:
                prev.set_selected(False)
                
        # Select new
        self.current_selected = client_id
        current = self._find_client_item(client_id)
        if current:
            current.set_selected(True)
            
        self.client_selected.emit(client_id)
        
    def _find_client_item(self, client_id: str):
        for i in range(self.clients_layout.count() - 1):
            widget = self.clients_layout.itemAt(i).widget()
            if widget and getattr(widget, 'client_id', None) == client_id:
                return widget
        return None
        
    def update_clients_count(self):
        count = len(self.clients)
        self.clients_count.setText(f"{count} connected")
        
    def clear_clients(self):
        for i in reversed(range(self.clients_layout.count() - 1)):
            widget = self.clients_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        self.clients.clear()
        self.current_selected = None
        self.update_clients_count()