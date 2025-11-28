"""
CSS styles for the chat application - Black Monochrome Theme
"""

LEFT_PANEL_STYLES = """
/* Left Panel Styles */
#leftPanel {
    background-color: #4A148C;  /* Purple background */
    border-right: 2px solid #333;
}

#logo {
    font-size: 20px;
    font-weight: bold;
    color: #E0E0E0;
    padding: 15px;
    border: 2px solid #E0E0E0;
    border-radius: 8px;
    margin-bottom: 10px;
}

/* Separator Styles */
#separator {
    background-color: #E0E0E0;
    height: 2px;
    margin: 15px 0;
}

/* Button Styles - NO HOVER EFFECTS */
#tcpButton {
    background-color: #2E7D32;  /* Green */
    color: #E0E0E0;
    border: 2px solid #1B5E20;
    border-radius: 8px;
    padding: 12px;
    font-weight: bold;
    font-size: 14px;
    min-height: 45px;
}

#tcpButton[running="true"] {
    background-color: #1B5E20;
    border-color: #E0E0E0;
}

#udpButton {
    background-color: #1565C0;  /* Blue */
    color: #E0E0E0;
    border: 2px solid #0D47A1;
    border-radius: 8px;
    padding: 12px;
    font-weight: bold;
    font-size: 14px;
    min-height: 45px;
}

#udpButton[running="true"] {
    background-color: #0D47A1;
    border-color: #E0E0E0;
}

#shutdownButton {
    background-color: #424242;  /* Gray when disabled */
    color: #9E9E9E;
    border: 2px solid #616161;
    border-radius: 8px;
    padding: 12px;
    font-weight: bold;
    font-size: 14px;
    min-height: 45px;
}

#shutdownButton:enabled {
    background-color: #C62828;  /* Red when enabled */
    color: #E0E0E0;
    border-color: #B71C1C;
}
"""

# Export all styles
STYLES = {
    'left_panel': LEFT_PANEL_STYLES,
}