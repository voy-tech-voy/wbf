"""
Custom SpinBox Widget with Chevron Arrows
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSpinBox, QSizePolicy
from PyQt6.QtCore import pyqtSignal, Qt, QEvent
from PyQt6.QtGui import QFont


class CustomSpinBox(QWidget):
    """
    Custom integer spinbox with chevron arrows matching CustomTargetSizeSpinBox style.
    """
    
    valueChanged = pyqtSignal(int)
    
    def __init__(self, parent=None, default_value=100, on_enter_callback=None):
        super().__init__(parent)
        self.is_dark = True
        self.on_enter_callback = on_enter_callback
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        from PyQt6.QtWidgets import QAbstractSpinBox
        
        self.spinbox = QSpinBox()
        self.spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spinbox.setValue(default_value)
        self.spinbox.setMinimumWidth(120)
        self.spinbox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # Install event filter
        self.spinbox.installEventFilter(self)
        self.spinbox.lineEdit().installEventFilter(self)
        
        # Create arrow buttons
        arrow_container = QWidget()
        arrow_layout = QVBoxLayout(arrow_container)
        arrow_layout.setContentsMargins(0, 0, 0, 0)
        arrow_layout.setSpacing(0)
        
        arrow_font = QFont()
        arrow_font.setPointSize(11)
        arrow_font.setStretch(200)
        arrow_font.setWeight(QFont.Weight.DemiBold)
        
        self.up_arrow = QLabel("˄")
        self.up_arrow.setFont(arrow_font)
        self.up_arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.up_arrow.setFixedSize(24, 14)
        self.up_arrow.mousePressEvent = lambda e: self.spinbox.stepUp()
        
        self.down_arrow = QLabel("˅")
        self.down_arrow.setFont(arrow_font)
        self.down_arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.down_arrow.setFixedSize(24, 14)
        self.down_arrow.mousePressEvent = lambda e: self.spinbox.stepDown()
        
        arrow_layout.addWidget(self.up_arrow)
        arrow_layout.addWidget(self.down_arrow)
        arrow_container.setFixedHeight(28)
        
        self.spinbox.valueChanged.connect(self.valueChanged.emit)
        
        layout.addWidget(self.spinbox)
        layout.addWidget(arrow_container)
        
        self._apply_custom_style(self.is_dark)
    
    def eventFilter(self, obj, event):
        """Handle Enter/Escape key presses"""
        if event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if self.on_enter_callback:
                    self.on_enter_callback()
                return True
        return super().eventFilter(obj, event)
    
    def value(self):
        return self.spinbox.value()
    
    def setValue(self, value):
        self.spinbox.setValue(value)
    
    def setRange(self, min_val, max_val):
        self.spinbox.setRange(min_val, max_val)
    
    def setSuffix(self, suffix):
        self.spinbox.setSuffix(suffix)
    
    def setVisible(self, visible):
        super().setVisible(visible)
        self.spinbox.setVisible(visible)
    
    def update_theme(self, is_dark):
        self.is_dark = is_dark
        self._apply_custom_style(is_dark)
    
    def _apply_custom_style(self, is_dark):
        if is_dark:
            bg_color = "#2b2b2b"
            text_color = "#ffffff"
            border_color = "#555555"
            arrow_color = "#888888"
            hover_color = "#4CAF50"
        else:
            bg_color = "white"
            text_color = "#333333"
            border_color = "#cccccc"
            arrow_color = "#666666"
            hover_color = "#4CAF50"
        
        spinbox_style = f"""
            QSpinBox {{
                background-color: {bg_color};
                color: {text_color};
                border: 1px solid {border_color};
                border-right: none;
                border-top-left-radius: 4px;
                border-bottom-left-radius: 4px;
                padding: 4px 8px;
                font-size: 13px;
            }}
            QSpinBox:hover {{
                border-color: {hover_color};
            }}
            QSpinBox:focus {{
                border-color: {hover_color};
            }}
        """
        self.spinbox.setStyleSheet(spinbox_style)
        
        arrow_style = f"""
            QLabel {{
                background-color: {bg_color};
                color: {arrow_color};
                border: 1px solid {border_color};
                border-left: none;
            }}
            QLabel:hover {{
                background-color: {'#3d3d3d' if is_dark else '#f0f0f0'};
            }}
        """
        
        self.up_arrow.setStyleSheet(arrow_style + f"""
            border-top-right-radius: 4px;
            border-bottom: none;
        """)
        
        self.down_arrow.setStyleSheet(arrow_style + f"""
            border-bottom-right-radius: 4px;
            border-top: none;
        """)
