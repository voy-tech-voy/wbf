"""
Presets Plugin - Preset Card Widget

A 3:4 ratio card widget displaying preset information.
Based on .agent/preset_card_spec.md design specification.
"""
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPixmap, QIcon, QColor, QPainter

from client.plugins.presets.logic.models import PresetDefinition
from client.utils.resource_path import get_resource_path
from client.gui.theme import Theme


class PresetCard(QFrame):
    """
    Preset card widget following the 3:4 "Monolith" design.
    
    Layout:
    +---------------------------+
    |   [ ZONE A: ICON ]        |  1:1 square
    |   Centered glyph          |
    +---------------------------+
    |   [ ZONE B: TEXT ]        |  Remaining
    |   Title (bold)            |
    |   Subtitle (mono)         |
    +---------------------------+
    
    Signals:
        clicked: Emitted when card is clicked, passes PresetDefinition
    """
    
    clicked = pyqtSignal(object)  # Emits PresetDefinition
    
    # Card dimensions (3:4 ratio)
    CARD_WIDTH = 120
    CARD_HEIGHT = 160
    ICON_SIZE = 48  # Icon size within the chamber
    
    def __init__(self, preset: PresetDefinition, parent=None):
        super().__init__(parent)
        self._preset = preset
        self._is_available = preset.is_available
        
        self.setFixedSize(self.CARD_WIDTH, self.CARD_HEIGHT)
        self.setObjectName("PresetCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self._setup_ui()
        self._apply_styles()
        
        # Ghost effect for unavailable presets
        if not self._is_available:
            self._apply_ghost_effect()
    
    def _setup_ui(self):
        """Setup the card layout with icon and text zones."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 12)
        layout.setSpacing(0)
        
        # Zone A: Icon Chamber (stretch factor 3)
        self.icon_label = QLabel()
        self.icon_label.setObjectName("CardIcon")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._load_icon()
        layout.addWidget(self.icon_label, 3)
        
        # Zone B: Text Base (stretch factor 1)
        self.title_label = QLabel(self._preset.name.upper())
        self.title_label.setObjectName("CardTitle")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subtitle_text = self._preset.subtitle or self._preset.description[:20]
        self.subtitle_label = QLabel(subtitle_text)
        self.subtitle_label.setObjectName("CardSubtitle")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(self.title_label, 0)
        layout.addWidget(self.subtitle_label, 0)
    
    def _load_icon(self):
        """Load the preset icon."""
        icon_name = self._preset.style.icon
        
        # Try to load from assets
        icon_path = get_resource_path(f"client/assets/icons/{icon_name}.svg")
        
        try:
            if icon_path:
                icon = QIcon(icon_path)
                pixmap = icon.pixmap(self.ICON_SIZE, self.ICON_SIZE)
                self.icon_label.setPixmap(pixmap)
            else:
                # Fallback: use first letter as icon
                self.icon_label.setText(self._preset.name[0].upper())
                self.icon_label.setStyleSheet("""
                    font-size: 32px;
                    font-weight: bold;
                    color: #F5F5F7;
                """)
        except Exception:
            self.icon_label.setText(self._preset.name[0].upper())
    
    def _apply_styles(self):
        """Apply the card styling from design spec."""
        accent = self._preset.style.accent_color
        
        self.setStyleSheet(f"""
            QFrame#PresetCard {{
                background-color: {Theme.surface()};
                border: 1px solid {Theme.border()};
                border-radius: {Theme.RADIUS_LG}px;
            }}
            QFrame#PresetCard:hover {{
                background-color: {Theme.color('surface_hover')};
                border: 1px solid {Theme.border_focus()};
            }}
            QLabel#CardIcon {{
                background-color: transparent;
                padding: 10px;
            }}
            QLabel#CardTitle {{
                color: {Theme.text()};
                font-size: {Theme.FONT_SIZE_SM}px;
                font-weight: bold;
                background: transparent;
                margin-bottom: 2px;
            }}
            QLabel#CardSubtitle {{
                color: {Theme.text_muted()};
                font-size: {Theme.FONT_SIZE_XS}px;
                background: transparent;
            }}
        """)
    
    def _apply_ghost_effect(self):
        """Apply ghost effect for unavailable presets."""
        opacity = QGraphicsOpacityEffect(self)
        opacity.setOpacity(0.4)
        self.setGraphicsEffect(opacity)
        self.setCursor(Qt.CursorShape.ForbiddenCursor)
    
    def set_drag_active(self, active: bool):
        """Set drag-active state for visual feedback."""
        if active:
            self.setStyleSheet(self.styleSheet() + f"""
                QFrame#PresetCard {{
                    background-color: rgba(0, 224, 255, 0.1);
                    border: 2px solid {Theme.accent_turbo()};
                }}
                QLabel#CardSubtitle {{
                    color: {Theme.accent_turbo()};
                }}
            """)
        else:
            self._apply_styles()
    
    def mousePressEvent(self, event):
        """Handle click - emit preset."""
        if event.button() == Qt.MouseButton.LeftButton and self._is_available:
            self.clicked.emit(self._preset)
        super().mousePressEvent(event)
    
    @property
    def preset(self) -> PresetDefinition:
        """Get the preset definition."""
        return self._preset
