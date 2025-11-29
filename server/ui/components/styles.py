LEFT_PANEL_STYLES = """
/* Left Panel - Black Monochrome + Purple Accent */
#leftPanel {
    background-color: #2D1B40;  /* Deep purple (better than #4A148C for contrast) */
    border-right: 1px solid #443355;
    color: #E0E0E0;
}

#logo {
    font-size: 20px;
    font-weight: bold;
    color: #FFFFFF;
    text-align: center;
    padding: 12px 0;
    margin-bottom: 10px;
    letter-spacing: 1px;
}

/* Separator - thin, elegant */
#separator {
    background-color: #554466;
    height: 1px;
    margin: 10px 15px;
}

/* Icon Buttons - Compact, clean, no hover */
QToolButton {
    text-align: left;
    padding: 10px 14px;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 500;
    color: #E0E0E0;
    background: transparent;
    border: 2px solid transparent;
    min-height: 40px;
}

/* No hover effects — as requested */
QToolButton:hover {
    background: transparent;
    border: 2px solid transparent;
}

/* TCP Button - Green theme */
#tcpButton {
    border-color: #2E7D32;
}

#tcpButton[running="true"] {
    color: #A5D6A7;
    border-color: #4CAF50;
}

/* UDP Button - Blue theme */
#udpButton {
    border-color: #1565C0;
}

#udpButton[running="true"] {
    color: #90CAF9;
    border-color: #42A5F5;
}

/* Shutdown Button */
#shutdownButton {
    background: #1E1328;
    border: 2px solid #616161;
    color: #9E9E9E;
    min-height: 44px;
}

#shutdownButton:enabled {
    color: #FF8A80;
    border-color: #E57373;
    background: #1E1328;
}

/* Ensure icon alignment */
QToolButton::icon {
    left: 4px;
    top: 0;
}
"""
STYLES = {
    'left_panel': LEFT_PANEL_STYLES,
}

# Optional: for legacy compat
__all__ = ['STYLES', 'LEFT_PANEL_STYLES']