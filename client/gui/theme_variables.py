"""
Theme Variables for the Application
Based on Design Spec v4.0 - Premium Industrial (Tesla Dark Mode / Apple Ceramic)
"""

# ============================================
# DARK MODE (Default) - Deepest Void
# ============================================
DARK_THEME = {
    # Backgrounds
    "app_bg": "#0B0B0B",           # Deepest Void (Window Background)
    "surface_main": "#161616",     # Drop Zone / Panels
    "surface_element": "#242424",  # Buttons / Inputs
    "surface_hover": "#2a2a2a",    # Hover state for surfaces
    "surface_pressed": "#202020",  # Pressed state
    "input_bg": "#1a1a1a",         # Text input background
    
    # Borders
    "border_dim": "#333333",       # Subtle Separation
    "border_focus": "#555555",     # Hover/Focus State
    
    # Text
    "text_primary": "#F5F5F7",     # Main Readability
    "text_secondary": "#86868B",   # Labels / Meta Data
    
    # Accents
    "accent_primary": "#FFFFFF",   # Standard Action
    "accent_turbo": "#00E0FF",     # GPU Active (Electric Cyan)
    "accent_success": "#30D158",   # Success State
    
    # Status Colors
    "error": "#FF3B30",            # Error/Danger (iOS Red)
    "warning": "#FF9500",          # Warning (iOS Orange)
    "info": "#007AFF",             # Info (iOS Blue)
    
    # Scrollbar
    "scrollbar_bg": "#1a1a1a",     # Scrollbar track
    "scrollbar_thumb": "#404040",  # Scrollbar handle
    
    # Other
    "tooltip_bg": "#333333",       # Tooltip Background
}

# ============================================
# LIGHT MODE - Apple Ceramic
# ============================================
LIGHT_THEME = {
    # Backgrounds
    "app_bg": "#F5F5F7",           # Light background
    "surface_main": "#FFFFFF",     # Drop Zone / Panels
    "surface_element": "#E8E8ED",  # Buttons / Inputs
    "surface_hover": "#E0E0E5",    # Hover state for surfaces
    "surface_pressed": "#D8D8DD",  # Pressed state
    "input_bg": "#FFFFFF",         # Text input background
    
    # Borders
    "border_dim": "#D1D1D6",       # Subtle Separation
    "border_focus": "#8E8E93",     # Hover/Focus State
    
    # Text
    "text_primary": "#000000",     # Main Readability
    "text_secondary": "#6C6C70",   # Labels / Meta Data
    
    # Accents
    "accent_primary": "#000000",   # Standard Action
    "accent_turbo": "#007AFF",     # GPU Active (Blue for light mode)
    "accent_success": "#30D158",   # Success State
    
    # Status Colors
    "error": "#FF3B30",            # Error/Danger (iOS Red)
    "warning": "#FF9500",          # Warning (iOS Orange)
    "info": "#007AFF",             # Info (iOS Blue)
    
    # Scrollbar
    "scrollbar_bg": "#E8E8ED",     # Scrollbar track
    "scrollbar_thumb": "#C0C0C5",  # Scrollbar handle
    
    # Other
    "tooltip_bg": "#E8E8ED",       # Tooltip Background
}


def get_theme(is_dark: bool = True) -> dict:
    """Get theme dictionary based on mode"""
    return DARK_THEME if is_dark else LIGHT_THEME


def get_color(key: str, is_dark: bool = True) -> str:
    """Get a specific color from the theme"""
    theme = get_theme(is_dark)
    return theme.get(key, "#FF00FF")  # Magenta fallback for missing keys

class ThemeVariables:
    """Wrapper class for theme access"""
    @staticmethod
    def get_theme(is_dark: bool = True) -> dict:
        return get_theme(is_dark)
        
    @staticmethod
    def get_color(key: str, is_dark: bool = True) -> str:
        return get_color(key, is_dark)
