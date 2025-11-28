"""
QSS stylesheets for the dark gray monochrome theme.
"""

class Styles:
    """Static style definitions for the chat server UI."""
    
    # Color palette - Lighter black/dark gray theme
    BACKGROUND_PRIMARY = "#1A1A1A"      # Lighter black
    BACKGROUND_SECONDARY = "#242424"    # Dark gray
    BACKGROUND_TERTIARY = "#2D2D2D"     # Medium dark gray
    BACKGROUND_HOVER = "#363636"        # Hover state
    BACKGROUND_SELECTED = "#363636"     # Selected state
    
    TEXT_PRIMARY = "#F0F0F0"            # Brighter white
    TEXT_SECONDARY = "#C0C0C0"          # Light gray
    TEXT_MUTED = "#808080"              # Medium gray
    
    BORDER_COLOR = "#404040"            # Lighter borders
    BORDER_LIGHT = "#505050"            # Brighter borders
    
    ACCENT_GREEN = "#4CAF50"
    ACCENT_RED = "#F44336"
    ACCENT_BLUE = "#2196F3"
    ACCENT_GRAY = "#666666"
    
    # Main window styles
    MAIN_WINDOW = f"""
        QMainWindow {{
            background-color: {BACKGROUND_PRIMARY};
            color: {TEXT_PRIMARY};
            font-family: "Segoe UI", "Arial", sans-serif;
            font-size: 14px;
        }}
    """
    
    # Button styles
    BUTTON_BASE = f"""
        QPushButton {{
            background-color: {BACKGROUND_TERTIARY};
            color: {TEXT_PRIMARY};
            border: 1px solid {BORDER_COLOR};
            border-radius: 8px;
            padding: 12px 16px;
            font-weight: bold;
            min-height: 20px;
        }}
        QPushButton:hover {{
            background-color: {BACKGROUND_HOVER};
            border-color: {BORDER_LIGHT};
        }}
        QPushButton:pressed {{
            background-color: {BACKGROUND_SECONDARY};
        }}
        QPushButton:disabled {{
            background-color: {BACKGROUND_SECONDARY};
            color: {TEXT_MUTED};
            border-color: {BORDER_COLOR};
        }}
    """
    
    BUTTON_UDP = f"""
        QPushButton {{
            background-color: {ACCENT_GRAY};
            color: {TEXT_PRIMARY};
            border: 1px solid {BORDER_COLOR};
            border-radius: 8px;
            padding: 12px 16px;
            font-weight: bold;
            min-height: 20px;
        }}
        QPushButton:hover {{
            background-color: {ACCENT_BLUE}40;
            border-color: {ACCENT_BLUE};
        }}
        QPushButton:disabled {{
            background-color: {BACKGROUND_SECONDARY};
            color: {TEXT_MUTED};
        }}
    """
    
    BUTTON_UDP_RUNNING = f"""
        QPushButton {{
            background-color: {ACCENT_BLUE};
            color: {BACKGROUND_PRIMARY};
            border: 1px solid {ACCENT_BLUE};
            border-radius: 8px;
            padding: 12px 16px;
            font-weight: bold;
            min-height: 20px;
        }}
    """
    
    BUTTON_STOP = f"""
        QPushButton {{
            background-color: {ACCENT_GRAY};
            color: {TEXT_PRIMARY};
            border: 1px solid {BORDER_COLOR};
            border-radius: 8px;
            padding: 12px 16px;
            font-weight: bold;
            min-height: 20px;
        }}
        QPushButton:hover {{
            background-color: {ACCENT_RED}40;
            border-color: {ACCENT_RED};
        }}
        QPushButton:disabled {{
            background-color: {BACKGROUND_SECONDARY};
            color: {TEXT_MUTED};
        }}
    """
    
    BUTTON_STOP_ACTIVE = f"""
        QPushButton {{
            background-color: {ACCENT_RED};
            color: {BACKGROUND_PRIMARY};
            border: 1px solid {ACCENT_RED};
            border-radius: 8px;
            padding: 12px 16px;
            font-weight: bold;
            min-height: 20px;
        }}
    """
    
    # Sidebar styles
    SIDEBAR = f"""
        QWidget {{
            background-color: {BACKGROUND_SECONDARY};
            border-right: 1px solid {BORDER_COLOR};
        }}
    """
    
    SIDEBAR_HEADER = f"""
        QLabel {{
            color: {TEXT_PRIMARY};
            font-size: 16px;
            font-weight: bold;
            padding: 16px 12px 8px 12px;
            background-color: transparent;
        }}
    """
    
    # Client item styles
    CLIENT_ITEM = f"""
        QWidget {{
            background-color: {BACKGROUND_TERTIARY};
            border: 1px solid {BORDER_COLOR};
            border-radius: 8px;
            margin: 4px 8px;
            padding: 0px;
        }}
    """
    
    CLIENT_ITEM_SELECTED = f"""
        QWidget {{
            background-color: {BACKGROUND_SELECTED};
            border: 1px solid {BORDER_LIGHT};
            border-radius: 8px;
            margin: 4px 8px;
            padding: 0px;
        }}
    """
    
    # Chat area styles
    CHAT_AREA = f"""
        QWidget {{
            background-color: {BACKGROUND_PRIMARY};
        }}
    """
    
    CHAT_HEADER = f"""
        QWidget {{
            background-color: {BACKGROUND_SECONDARY};
            border-bottom: 1px solid {BORDER_COLOR};
            padding: 12px 16px;
        }}
    """
    
    # Message bubble styles
    MESSAGE_BUBBLE_SERVER = f"""
        QWidget {{
            background-color: {ACCENT_BLUE}30;
            border: 1px solid {ACCENT_BLUE}50;
            border-radius: 12px;
            padding: 8px 12px;
            margin: 4px 0px;
        }}
    """
    
    MESSAGE_BUBBLE_CLIENT = f"""
        QWidget {{
            background-color: {BACKGROUND_TERTIARY};
            border: 1px solid {BORDER_COLOR};
            border-radius: 12px;
            padding: 8px 12px;
            margin: 4px 0px;
        }}
    """
    
    # Input area styles
    INPUT_AREA = f"""
        QWidget {{
            background-color: {BACKGROUND_SECONDARY};
            border-top: 1px solid {BORDER_COLOR};
            padding: 12px;
        }}
    """
    
    TEXT_EDIT = f"""
        QTextEdit {{
            background-color: {BACKGROUND_TERTIARY};
            color: {TEXT_PRIMARY};
            border: 1px solid {BORDER_COLOR};
            border-radius: 8px;
            padding: 12px;
            font-size: 14px;
            selection-background-color: {ACCENT_BLUE};
        }}
        QTextEdit:focus {{
            border-color: {BORDER_LIGHT};
        }}
    """
    
    # Scroll area styles
    SCROLL_AREA = f"""
        QScrollArea {{
            background-color: transparent;
            border: none;
        }}
        QScrollBar:vertical {{
            background-color: {BACKGROUND_SECONDARY};
            width: 12px;
            margin: 0px;
        }}
        QScrollBar::handle:vertical {{
            background-color: {BORDER_COLOR};
            border-radius: 6px;
            min-height: 20px;
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: {BORDER_LIGHT};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            border: none;
            background: none;
        }}
    """
    
    # Status dot styles
    STATUS_DOT_ACTIVE = f"""
        QLabel {{
            background-color: {ACCENT_GREEN};
            border-radius: 6px;
            min-width: 12px;
            max-width: 12px;
            min-height: 12px;
            max-height: 12px;
        }}
    """
    
    STATUS_DOT_IDLE = f"""
        QLabel {{
            background-color: {ACCENT_GRAY};
            border-radius: 6px;
            min-width: 12px;
            max-width: 12px;
            min-height: 12px;
            max-height: 12px;
        }}
    """
    
    # Disconnect button style (brighter)
    DISCONNECT_BUTTON = f"""
        QPushButton {{
            background-color: {BACKGROUND_TERTIARY};
            color: {TEXT_PRIMARY};
            border: 1px solid {BORDER_COLOR};
            border-radius: 6px;
            font-size: 14px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {ACCENT_RED}40;
            color: {ACCENT_RED};
            border-color: {ACCENT_RED};
        }}
    """