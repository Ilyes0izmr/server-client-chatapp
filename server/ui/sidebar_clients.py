"""
Sidebar panel displaying connected clients list.
"""

from server.ui.styles import Styles
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QScrollArea, 
                           QFrame, QHBoxLayout, QVBoxLayout)
from PyQt6.QtCore import Qt, pyqtSignal
from .styles import Styles


class ClientItemWidget(QWidget):
    """Widget representing a single connected client."""
    
    clicked = pyqtSignal(str)  # Emits client identifier
    
    def __init__(self, client_info):
        super().__init__()
        self.client_info = client_info
        self.is_selected = False
        self.init_ui()
        
    def init_ui(self):
        """Initialize client item UI."""
        layout = QHBoxLayout()
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        
        # Avatar placeholder
        avatar_label = QLabel("👤")
        avatar_label.setStyleSheet(f"""
            QLabel {{
                color: {Styles.TEXT_PRIMARY};
                font-size: 16px;
                background-color: {Styles.BACKGROUND_SECONDARY};
                border-radius: 16px;
                min-width: 32px;
                max-width: 32px;
                min-height: 32px;
                max-height: 32px;
                qproperty-alignment: AlignCenter;
            }}
        """)
        
        # Client info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        # Client name/identifier
        name_label = QLabel(self.client_info.get('name', 'Unknown Client'))
        name_label.setStyleSheet(f"""
            QLabel {{
                color: {Styles.TEXT_PRIMARY};
                font-weight: bold;
                font-size: 13px;
            }}
        """)
        
        # Client address
        address_label = QLabel(self.client_info.get('identifier', 'Unknown'))
        address_label.setStyleSheet(f"""
            QLabel {{
                color: {Styles.TEXT_SECONDARY};
                font-size: 11px;
            }}
        """)
        
        # Last activity
        last_active = self.client_info.get('last_activity', 0)
        time_text = "Just now" if last_active > 0 else "Unknown"
        time_label = QLabel(time_text)
        time_label.setStyleSheet(f"""
            QLabel {{
                color: {Styles.TEXT_MUTED};
                font-size: 10px;
            }}
        """)
        
        info_layout.addWidget(name_label)
        info_layout.addWidget(address_label)
        info_layout.addWidget(time_label)
        
        # Status dot
        status_dot = QLabel()
        status_dot.setFixedSize(12, 12)
        status_dot.setStyleSheet(Styles.STATUS_DOT_ACTIVE)
        
        # Assemble layout
        layout.addWidget(avatar_label)
        layout.addLayout(info_layout)
        layout.addStretch()
        layout.addWidget(status_dot)
        
        self.setLayout(layout)
        self.update_style()
        
    def update_style(self):
        """Update widget style based on selection state."""
        if self.is_selected:
            self.setStyleSheet(Styles.CLIENT_ITEM_SELECTED)
        else:
            self.setStyleSheet(Styles.CLIENT_ITEM)
    
    def mousePressEvent(self, event):
        """Handle mouse click to select client."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.client_info['identifier'])
    
    def set_selected(self, selected: bool):
        """Set selection state."""
        self.is_selected = selected
        self.update_style()


class SidebarClients(QWidget):
    """Sidebar displaying connected clients."""
    
    client_selected = pyqtSignal(dict)  # Emits selected client info
    
    def __init__(self):
        super().__init__()
        self.clients = {}
        self.client_widgets = {}
        self.selected_client = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize sidebar UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header_label = QLabel("Connected Clients")
        header_label.setStyleSheet(Styles.SIDEBAR_HEADER)
        header_label.setFixedHeight(50)
        
        # Clients scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet(Styles.SCROLL_AREA)
        
        # Clients container
        self.clients_widget = QWidget()
        self.clients_layout = QVBoxLayout()
        self.clients_layout.setContentsMargins(0, 8, 0, 8)
        self.clients_layout.setSpacing(0)
        self.clients_layout.addStretch()
        
        self.clients_widget.setLayout(self.clients_layout)
        self.scroll_area.setWidget(self.clients_widget)
        
        # Empty state
        self.empty_label = QLabel("No clients connected")
        self.empty_label.setStyleSheet(f"""
            QLabel {{
                color: {Styles.TEXT_MUTED};
                font-size: 13px;
                qproperty-alignment: AlignCenter;
                padding: 40px;
            }}
        """)
        self.clients_layout.insertWidget(0, self.empty_label)
        
        layout.addWidget(header_label)
        layout.addWidget(self.scroll_area)
        
        self.setLayout(layout)
        self.setStyleSheet(Styles.SIDEBAR)
        self.setMinimumWidth(250)
        self.setMaximumWidth(350)
    
    def add_client(self, client_info):
        """Add a client to the sidebar."""
        client_id = client_info['identifier']
        
        if client_id in self.clients:
            return
            
        self.clients[client_id] = client_info
        
        # Remove empty state if first client
        if len(self.clients) == 1 and self.empty_label.parent():
            self.clients_layout.removeWidget(self.empty_label)
            self.empty_label.setParent(None)
        
        # Create client widget
        client_widget = ClientItemWidget(client_info)
        client_widget.clicked.connect(self.on_client_clicked)
        
        self.client_widgets[client_id] = client_widget
        self.clients_layout.insertWidget(self.clients_layout.count() - 1, client_widget)
    
    def remove_client(self, client_id):
        """Remove a client from the sidebar."""
        if client_id in self.client_widgets:
            widget = self.client_widgets[client_id]
            self.clients_layout.removeWidget(widget)
            widget.setParent(None)
            del self.client_widgets[client_id]
        
        if client_id in self.clients:
            del self.clients[client_id]
        
        # Show empty state if no clients
        if not self.clients and not self.empty_label.parent():
            self.clients_layout.insertWidget(0, self.empty_label)
        
        # Clear selection if removed client was selected
        if self.selected_client == client_id:
            self.selected_client = None
    
    def on_client_clicked(self, client_id):
        """Handle client item click."""
        # Deselect previously selected client
        if self.selected_client and self.selected_client in self.client_widgets:
            self.client_widgets[self.selected_client].set_selected(False)
        
        # Select new client
        if client_id in self.client_widgets:
            self.client_widgets[client_id].set_selected(True)
            self.selected_client = client_id
            self.client_selected.emit(self.clients[client_id])
    
    def update_client_activity(self, client_id, last_activity):
        """Update client's last activity timestamp."""
        if client_id in self.clients:
            self.clients[client_id]['last_activity'] = last_activity
            # In a real implementation, you'd update the widget here
    
    def get_selected_client(self):
        """Get currently selected client info."""
        if self.selected_client and self.selected_client in self.clients:
            return self.clients[self.selected_client]
        return None