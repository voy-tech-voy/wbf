"""
Presets Plugin - Preset Gallery

Overlay widget displaying a grid of preset cards.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, 
    QGridLayout, QLabel, QGraphicsOpacityEffect, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor

from typing import List
from client.plugins.presets.logic.models import PresetDefinition
from client.plugins.presets.ui.card import PresetCard


class PresetGallery(QWidget):
    """
    Overlay widget displaying preset cards in a grid.
    
    Shows inside the DragDropArea when preset selection is needed.
    
    Signals:
        preset_selected: Emitted when user clicks a preset card
        dismissed: Emitted when user clicks outside cards
    """
    
    preset_selected = pyqtSignal(object)  # PresetDefinition
    dismissed = pyqtSignal()
    
    # Layout configuration
    CARDS_PER_ROW = 4
    CARD_SPACING = 16
    PADDING = 24
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PresetGallery")
        self._cards: List[PresetCard] = []
        
        self._setup_ui()
        self._apply_styles()
        
        # Initially hidden
        self.hide()
    
    def _setup_ui(self):
        """Setup the gallery layout."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(self.PADDING, self.PADDING, self.PADDING, self.PADDING)
        main_layout.setSpacing(16)
        
        # Header
        header = QLabel("SELECT PRESET")
        header.setObjectName("GalleryHeader")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header)
        
        # Scroll area for cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent;")
        
        # Card container
        self._card_container = QWidget()
        self._card_layout = QGridLayout(self._card_container)
        self._card_layout.setSpacing(self.CARD_SPACING)
        self._card_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        
        scroll.setWidget(self._card_container)
        main_layout.addWidget(scroll, 1)
        
        # Parameter panel (shown after preset selection)
        from client.plugins.presets.ui.parameter_form import ParameterForm
        self._param_panel = QFrame()
        self._param_panel.setObjectName("ParamPanel")
        self._param_panel.setStyleSheet("""
            QFrame#ParamPanel {
                background-color: rgba(30, 30, 30, 0.95);
                border-radius: 8px;
                padding: 12px;
            }
        """)
        
        param_layout = QVBoxLayout(self._param_panel)
        param_layout.setContentsMargins(12, 12, 12, 12)
        
        self._selected_preset_label = QLabel("")
        self._selected_preset_label.setObjectName("SelectedPresetLabel")
        self._selected_preset_label.setStyleSheet("color: #00E0FF; font-size: 14px; font-weight: bold;")
        param_layout.addWidget(self._selected_preset_label)
        
        self._parameter_form = ParameterForm()
        param_layout.addWidget(self._parameter_form)
        
        self._param_panel.hide()  # Hidden until preset selected
        main_layout.addWidget(self._param_panel)
    
    def _apply_styles(self):
        """Apply gallery styling."""
        self.setStyleSheet("""
            QWidget#PresetGallery {
                background-color: rgba(18, 18, 18, 0.95);
                border-radius: 12px;
            }
            QLabel#GalleryHeader {
                color: #F5F5F7;
                font-size: 14px;
                font-weight: bold;
                padding: 8px;
                background: transparent;
            }
            QScrollArea {
                background: transparent;
            }
        """)
    
    def set_presets(self, presets: List[PresetDefinition]):
        """Populate the gallery with preset cards."""
        # Clear existing cards
        for card in self._cards:
            card.deleteLater()
        self._cards.clear()
        
        # Clear layout
        while self._card_layout.count():
            item = self._card_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add new cards
        row, col = 0, 0
        for preset in presets:
            card = PresetCard(preset)
            card.clicked.connect(self._on_card_clicked)
            self._cards.append(card)
            
            self._card_layout.addWidget(card, row, col)
            col += 1
            if col >= self.CARDS_PER_ROW:
                col = 0
                row += 1
    
    def _on_card_clicked(self, preset: PresetDefinition):
        """Handle card click - show parameters and emit selection."""
        # Show parameter panel for this preset
        if preset.parameters:
            self._selected_preset_label.setText(f"⚙ {preset.name} Settings")
            self._parameter_form.set_parameters(preset.parameters, {})
            self._param_panel.show()
        else:
            self._param_panel.hide()
        
        # Emit selection signal
        self.preset_selected.emit(preset)
    
    def mousePressEvent(self, event):
        """Handle click on background - dismiss gallery."""
        # Only dismiss if clicking on the gallery background, not on cards
        child = self.childAt(event.pos())
        if child is None or child == self:
            self.dismissed.emit()
        super().mousePressEvent(event)
    
    def show_animated(self):
        """Show the gallery with fade-in animation."""
        self.setGeometry(self.parent().rect())
        
        # Setup opacity animation
        if not hasattr(self, '_opacity_effect'):
            self._opacity_effect = QGraphicsOpacityEffect(self)
            self.setGraphicsEffect(self._opacity_effect)
        
        self._opacity_effect.setOpacity(0.0)
        self.show()
        self.raise_()
        
        self._show_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._show_anim.setDuration(200)
        self._show_anim.setStartValue(0.0)
        self._show_anim.setEndValue(1.0)
        self._show_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self._show_anim.start()
    
    def hide_animated(self):
        """Hide the gallery with fade-out animation."""
        if not hasattr(self, '_opacity_effect'):
            self.hide()
            return
        
        self._hide_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._hide_anim.setDuration(150)
        self._hide_anim.setStartValue(1.0)
        self._hide_anim.setEndValue(0.0)
        self._hide_anim.setEasingCurve(QEasingCurve.Type.InQuad)
        self._hide_anim.finished.connect(self.hide)
        self._hide_anim.start()
    
    def resizeEvent(self, event):
        """Handle parent resize."""
        if self.parent():
            self.setGeometry(self.parent().rect())
        super().resizeEvent(event)
