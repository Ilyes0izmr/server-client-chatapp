from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QScrollArea, QWidget)
from PyQt6.QtCore import Qt, pyqtSignal

class ClientItem(QFrame):
    """Individual client item in the sidebar - NOW CLICKABLE"""
    
    client_kicked = pyqtSignal(str)  # client_id
    client_clicked = pyqtSignal(str)  # client_id
    
    def __init__(self, client_id: str, client_data: dict):
        super().__init__()
        self.client_id = client_id
        self.client_data = client_data
        self.setup_ui()
        self.apply_styles()
        
    def setup_ui(self):
        self.setObjectName("clientItem")
        self.setFixedHeight(80)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(5)
        
        # Top row: Client info and kick button
        top_layout = QHBoxLayout()
        
        # Client avatar and basic info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        # Client name/ID
        self.name_label = QLabel(self.client_data.get('username', self.client_id))
        self.name_label.setObjectName("clientName")
        info_layout.addWidget(self.name_label)
        
        # Connection type
        protocol = self.client_data.get('protocol', 'TCP')
        protocol_color = "#2E7D32" if protocol == "TCP" else "#1565C0"
        protocol_text = f"<span style='color: {protocol_color};'>{protocol}</span> • {self.client_id}"
        self.protocol_label = QLabel()
        self.protocol_label.setText(protocol_text)
        self.protocol_label.setObjectName("clientProtocol")
        info_layout.addWidget(self.protocol_label)
        
        top_layout.addLayout(info_layout)
        top_layout.addStretch()
        
        # Kick button
        self.kick_btn = QPushButton("✕")
        self.kick_btn.setObjectName("kickButton")
        self.kick_btn.setFixedSize(25, 25)
        self.kick_btn.clicked.connect(self.on_kick_clicked)
        top_layout.addWidget(self.kick_btn)
        
        layout.addLayout(top_layout)
        
        # Status indicator
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("●"))
        status_layout.addWidget(QLabel("Online"))
        status_layout.addStretch()
        layout.addLayout(status_layout)
        
    def apply_styles(self):
        self.setStyleSheet("""
            #clientItem {
                background-color: #1A1A1A;
                border: 1px solid #333;
                border-radius: 8px;
                margin: 2px;
            }
            #clientItem:hover {
                background-color: #262626;
                border-color: #555;
            }
            #clientName {
                color: #E0E0E0;
                font-weight: bold;
                font-size: 12px;
            }
            #clientProtocol {
                color: #B0B0B0;
                font-size: 10px;
            }
            #kickButton {
                background-color: #C62828;
                color: #E0E0E0;
                border: none;
                border-radius: 3px;
                font-weight: bold;
                font-size: 10px;
            }
            #kickButton:hover {
                background-color: #D32F2F;
            }
        """)
        
    def mousePressEvent(self, event):
        """Handle mouse click on the client item"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.client_clicked.emit(self.client_id)
        super().mousePressEvent(event)
        
    def on_kick_clicked(self):
        """Emit signal when kick button is clicked"""
        self.client_kicked.emit(self.client_id)

class ClientsSidebar(QFrame):
    """Sidebar showing connected clients with kick functionality"""
    
    client_kicked = pyqtSignal(str)  # client_id
    client_selected = pyqtSignal(str)  # client_id
    
    def __init__(self):
        super().__init__()
        self.clients = {}  # client_id -> client_data
        self.current_selected = None  # Track currently selected client
        self.setup_ui()
        self.apply_styles()
        
    def setup_ui(self):
        self.setObjectName("clientsSidebar")
        self.setFixedWidth(280)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 15, 10, 15)
        layout.setSpacing(15)
        
        # Header ------------------------------------------------------------
        header = QLabel("CONNECTED CLIENTS")
        header.setObjectName("clientsHeader")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Clients count ------------------------------------------------------------
        self.clients_count = QLabel("0 clients connected")
        self.clients_count.setObjectName("clientsCount")
        self.clients_count.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.clients_count)
        
        # Separator ------------------------------------------------------------
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #333;")
        layout.addWidget(separator)
        
        # Clients list area ------------------------------------------------------------
        self.clients_scroll = QScrollArea()
        self.clients_scroll.setObjectName("clientsScroll")
        self.clients_scroll.setWidgetResizable(True)
        self.clients_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.clients_widget = QWidget()
        self.clients_layout = QVBoxLayout(self.clients_widget)
        self.clients_layout.setContentsMargins(5, 5, 5, 5)
        self.clients_layout.setSpacing(8)
        self.clients_layout.addStretch()
        
        self.clients_scroll.setWidget(self.clients_widget)
        layout.addWidget(self.clients_scroll)
        
    def apply_styles(self):
        self.setStyleSheet("""
            #clientsSidebar {
                background-color: #121212;
                border-right: 1px solid #333;
            }
            #clientsHeader {
                color: #E0E0E0;
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
                border: 1px solid #333;
                border-radius: 5px;
            }
            #clientsCount {
                color: #B0B0B0;
                font-size: 12px;
                padding: 5px;
            }
            #clientsScroll {
                background-color: #0D0D0D;
                border: 1px solid #333;
                border-radius: 5px;
            }
            #clientsScroll QWidget {
                background-color: #0D0D0D;
            }
        """)
        
    def add_client(self, client_id: str, client_data: dict):
        """Add a client to the sidebar"""
        if client_id in self.clients:
            return
            
        self.clients[client_id] = client_data
        
        # Create client item
        client_item = ClientItem(client_id, client_data)
        client_item.client_kicked.connect(self.client_kicked.emit)
        client_item.client_clicked.connect(self.on_client_clicked)
        
        # Insert before the stretch
        self.clients_layout.insertWidget(self.clients_layout.count() - 1, client_item)
        
        self.update_clients_count()
        
    def remove_client(self, client_id: str):
        """Remove a client from the sidebar"""
        if client_id not in self.clients:
            return
            
        # Find and remove the client item
        for i in range(self.clients_layout.count() - 1):  # -1 to exclude stretch
            item = self.clients_layout.itemAt(i)
            if item.widget() and hasattr(item.widget(), 'client_id'):
                if item.widget().client_id == client_id:
                    item.widget().deleteLater()
                    break
        
        if client_id in self.clients:
            del self.clients[client_id]
            
        # Clear selection if this was the selected client
        if self.current_selected == client_id:
            self.current_selected = None
            
        self.update_clients_count()
        
    def on_client_clicked(self, client_id: str):
        """Handle client item click"""
        print(f"Client clicked: {client_id}")
        self.current_selected = client_id
        self.client_selected.emit(client_id)
        
        # Update visual selection
        self.update_selection_style()
        
    def update_selection_style(self):
        """Update visual style to show selected client"""
        for i in range(self.clients_layout.count() - 1):
            item = self.clients_layout.itemAt(i)
            if item.widget() and hasattr(item.widget(), 'client_id'):
                client_item = item.widget()
                is_selected = (client_item.client_id == self.current_selected)
                if is_selected:
                    client_item.setStyleSheet("#clientItem { border: 2px solid #2E7D32; }")
                else:
                    client_item.setStyleSheet("#clientItem { border: 1px solid #333; }")
        
    def update_clients_count(self):
        """Update the clients count label"""
        count = len(self.clients)
        self.clients_count.setText(f"{count} client{'s' if count != 1 else ''} connected")
        
    def clear_clients(self):
        """Remove all clients"""
        for i in reversed(range(self.clients_layout.count() - 1)):
            item = self.clients_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
                
        self.clients.clear()
        self.current_selected = None
        self.update_clients_count()