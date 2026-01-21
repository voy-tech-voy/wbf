"""
Output Footer Widget
A unified bottom bar with segmented output destination toggle and Start button.
Based on Design Spec v4.0 - Premium Industrial
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel,
    QSizePolicy, QGraphicsOpacityEffect, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtGui import QColor, QFont

from client.utils.font_manager import FONT_FAMILY, FONT_FAMILY_APP_NAME, FONT_SIZE_BUTTON
from client.gui.theme_variables import get_theme, get_color
from client.gui.custom_widgets import SegmentedControl





class OutputFooter(QWidget):
    """
    Unified output footer bar with segmented destination toggle and Start button.
    Based on Design Spec v4.0 - Output Bar (Bottom Strip)
    """
    
    start_conversion = pyqtSignal()
    stop_conversion = pyqtSignal()
    output_mode_changed = pyqtSignal(str)  # "source", "organized", "custom"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_dark = True
        self._is_converting = False
        self._has_files = False
        self._gpu_available = False
        
        self.setMinimumHeight(56)
        self.setMaximumHeight(64)
        
        # Opacity effect for dynamic visibility
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity_effect)
        self._opacity_effect.setOpacity(0.4)  # Start dimmed
        
        # Opacity animation
        self._opacity_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._opacity_anim.setDuration(200)  # <200ms per design spec
        self._opacity_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        
        self._setup_ui()
        self._apply_styles()
        
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)  # 4px grid: 16 = 4*4
        layout.setSpacing(16)
        
        # Left side: Segmented toggle
        self.segment_control = SegmentedControl()
        self.segment_control.selectionChanged.connect(self._on_mode_changed)
        self.segment_control.setMaximumWidth(600) # Increased width to prevent clipping
        layout.addWidget(self.segment_control)
        
        # Tooltip for "Organized" mode
        self.organized_tooltip = QLabel("Everything in its own folder")
        self.organized_tooltip.setVisible(False)
        layout.addWidget(self.organized_tooltip)
        
        # Spacer
        layout.addStretch()
        
        # Right side: Start button
        self.start_btn = QPushButton("START")
        self.start_btn.setObjectName("BtnStart")
        self.start_btn.setMinimumWidth(120)
        self.start_btn.setMinimumHeight(40)
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.clicked.connect(self._on_start_clicked)
        self.start_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.start_btn)
        
        # Set default selection AFTER UI is fully built to avoid AttributeError
        self.segment_control.set_selected("organized")
        
    def _on_mode_changed(self, mode):
        # Show tooltip for organized mode
        self.organized_tooltip.setVisible(mode == "organized")
        self.output_mode_changed.emit(mode)
        
    def _on_start_clicked(self):
        if self._is_converting:
            self.stop_conversion.emit()
        else:
            self.start_conversion.emit()
    
    def set_converting(self, is_converting):
        """Set the conversion state"""
        self._is_converting = is_converting
        self._update_button_state()
        
    def _update_button_state(self):
        if self._is_converting:
            self.start_btn.setText("STOP")
            self._apply_stop_style()
        else:
            self.start_btn.setText("START")
            self._apply_start_style()
            
    def set_has_files(self, has_files):
        """Update appearance based on whether files are present"""
        if has_files == self._has_files:
            return
        self._has_files = has_files
        
        # Animate opacity (150ms per design spec for drag effect)
        self._opacity_anim.stop()
        self._opacity_anim.setStartValue(self._opacity_effect.opacity())
        self._opacity_anim.setEndValue(1.0 if has_files else 0.4)
        self._opacity_anim.start()
        
        # Enable/disable interaction
        self.setEnabled(has_files)
        
    def set_gpu_available(self, gpu_available):
        """Set GPU availability for turbo styling"""
        self._gpu_available = gpu_available
        self.start_btn.setProperty("gpu", gpu_available)
        self.start_btn.style().polish(self.start_btn)
        self._apply_start_style()
        
    def get_output_mode(self):
        """Get the current output mode"""
        return self.segment_control.get_selection()
    
    def get_custom_path(self):
        """Get custom path if in custom mode"""
        return self.segment_control.get_custom_path()
    
    def get_organized_name(self):
        """Get organized folder name"""
        return self.segment_control.get_organized_name()
        
    def update_theme(self, is_dark):
        self._is_dark = is_dark
        self.segment_control.update_theme(is_dark)
        self._apply_styles()
        
    def _apply_styles(self):
        theme = get_theme(self._is_dark)
        
        # Container styling
        self.setStyleSheet(f"""
            OutputFooter {{
                background-color: {theme['surface_main']};
                border-top: 1px solid {theme['border_dim']};
            }}
        """)
        
        self._apply_start_style()
        
        # Tooltip styling
        self.organized_tooltip.setStyleSheet(
            f"font-size: 10px; color: {theme['text_secondary']}; font-style: italic;"
        )
        
    def _apply_start_style(self):
        theme = get_theme(self._is_dark)
        
        if self._gpu_available:
            # GPU Turbo style with gradient and glow
            self.start_btn.setStyleSheet(f"""
                QPushButton#BtnStart {{
                    background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, 
                        stop:0 {theme['accent_turbo']}, stop:1 #007AFF);
                    color: #000000;
                    border: none;
                    border-radius: 8px;
                    font-family: '{FONT_FAMILY_APP_NAME}';
                    font-size: {FONT_SIZE_BUTTON}px;
                    font-weight: 700;
                    padding: 8px 30px;
                }}
                QPushButton#BtnStart:hover {{
                    background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, 
                        stop:0 #00F0FF, stop:1 #0088FF);
                }}
                QPushButton#BtnStart:pressed {{
                    background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, 
                        stop:0 #00C0DD, stop:1 #0066DD);
                }}
            """)
            
            # Add GPU glow effect
            glow = QGraphicsDropShadowEffect()
            glow.setBlurRadius(20)
            glow.setColor(QColor(0, 224, 255, 100))  # Cyan with Alpha
            glow.setOffset(0, 0)
            self.start_btn.setGraphicsEffect(glow)
        else:
            # Standard (CPU) style
            self.start_btn.setStyleSheet(f"""
                QPushButton#BtnStart {{
                    background-color: {theme['accent_primary']};
                    color: {theme['app_bg']};
                    border: none;
                    border-radius: 8px;
                    font-family: '{FONT_FAMILY_APP_NAME}';
                    font-size: {FONT_SIZE_BUTTON}px;
                    font-weight: 700;
                    padding: 8px 30px;
                }}
                QPushButton#BtnStart:hover {{
                    background-color: {theme['border_focus']};
                    color: {theme['text_primary']};
                }}
                QPushButton#BtnStart:pressed {{
                    background-color: {theme['border_dim']};
                }}
                QPushButton#BtnStart:disabled {{
                    background-color: {theme['surface_element']};
                    color: {theme['text_secondary']};
                }}
            """)
            # Remove glow if any
            self.start_btn.setGraphicsEffect(None)
        
    def _apply_stop_style(self):
        theme = get_theme(self._is_dark)
        
        self.start_btn.setStyleSheet(f"""
            QPushButton#BtnStart {{
                background-color: transparent;
                border: 2px solid #FF3B30;
                border-radius: 8px;
                color: #FF3B30;
                font-family: '{FONT_FAMILY_APP_NAME}';
                font-size: {FONT_SIZE_BUTTON}px;
                font-weight: 700;
                padding: 8px 30px;
            }}
            QPushButton#BtnStart:hover {{
                background-color: #FF3B30;
                color: white;
            }}
            QPushButton#BtnStart:pressed {{
                background-color: #D32F2F;
                color: white;
            }}
        """)
        # Remove glow during stop state
        self.start_btn.setGraphicsEffect(None)
