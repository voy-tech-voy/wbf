"""
Custom PyQt6 Widgets with Dark Mode Support
Provides TimeRangeSlider, ResizeFolder, and Rotation classes
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, 
    QSpinBox, QLineEdit, QGroupBox, QFormLayout, QCheckBox, QSizePolicy, QApplication, QButtonGroup
)
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QPoint
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QPalette
from client.utils.font_manager import AppFonts


class ModeButtonsWidget(QWidget):
    """
    Uniform mode buttons component for Max Size / Manual selection.
    Used consistently across all tabs (Images, Videos, GIFs).
    """
    
    # Signal emitted when mode changes: emits "Max Size" or "Manual"
    modeChanged = pyqtSignal(str)
    
    def __init__(self, default_mode="Manual", parent=None):
        """
        Args:
            default_mode: Either "Max Size" or "Manual"
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Set up layout with consistent padding
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 9)
        layout.setSpacing(8)
        
        # Button style - consistent across all instances
        button_style = (
            "QPushButton { padding: 6px 14px; border-radius: 6px; border: 1px solid #555555; }"
            "QPushButton:checked { background-color: #4CAF50; color: white; border-color: #43a047; }"
        )
        
        # Max Size button
        self.max_size_btn = QPushButton("Max Size")
        self.max_size_btn.setCheckable(True)
        self.max_size_btn.setStyleSheet(button_style)
        self.max_size_btn.setToolTip("Auto-optimize to fit target file size")
        self.max_size_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # Manual button
        self.manual_btn = QPushButton("Manual")
        self.manual_btn.setCheckable(True)
        self.manual_btn.setStyleSheet(button_style)
        self.manual_btn.setToolTip("Set quality settings yourself")
        self.manual_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # Button group for exclusive selection
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        self.button_group.addButton(self.max_size_btn)
        self.button_group.addButton(self.manual_btn)
        
        # Set default mode
        if default_mode == "Max Size":
            self.max_size_btn.setChecked(True)
        else:
            self.manual_btn.setChecked(True)
        
        # Connect signals
        self.max_size_btn.toggled.connect(
            lambda checked: checked and self.modeChanged.emit("Max Size")
        )
        self.manual_btn.toggled.connect(
            lambda checked: checked and self.modeChanged.emit("Manual")
        )
        
        # Add buttons to layout
        layout.addWidget(self.max_size_btn)
        layout.addWidget(self.manual_btn)
        
        # Fixed height for consistency
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    
    def get_mode(self):
        """Get current mode: 'Max Size' or 'Manual'"""
        return "Max Size" if self.max_size_btn.isChecked() else "Manual"
    
    def set_mode(self, mode):
        """Set the mode programmatically"""
        if mode == "Max Size":
            self.max_size_btn.setChecked(True)
        else:
            self.manual_btn.setChecked(True)


class CustomComboBox(QComboBox):
    """
    Custom combobox with controlled text/icon width ratio.
    Default: 80% text width, 20% icon width
    """
    
    def __init__(self, parent=None, text_ratio=0.8, icon_ratio=0.2):
        super().__init__(parent)
        self.text_ratio = text_ratio  # Default 80% for text
        self.icon_ratio = icon_ratio  # Default 20% for icon
        self.setMinimumWidth(200)
        self.is_dark = False
        
        # Create a custom label for the arrow area
        from PyQt6.QtWidgets import QLabel
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QFont
        self.arrow_label = QLabel("˅", self)
        self.arrow_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Create font with horizontal stretch (match CustomTargetSizeSpinBox)
        arrow_font = QFont()
        arrow_font.setPointSize(11)
        arrow_font.setStretch(200)  # 200% width stretch (match CustomTargetSizeSpinBox)
        self.arrow_label.setFont(arrow_font)
        
        self.arrow_label.setStyleSheet("background: transparent; color: #CCCCCC;")
        self.arrow_label.raise_()
        
        self._apply_custom_style(self.is_dark)
    
    def update_theme(self, is_dark):
        """Update styling based on theme"""
        self.is_dark = is_dark
        self._apply_custom_style(is_dark)
        # Update arrow label color
        arrow_color = "#AAAAAA" if is_dark else "#888888"
        self.arrow_label.setStyleSheet(f"background: transparent; color: {arrow_color};")
    
    def resizeEvent(self, event):
        """Position the arrow label when widget is resized"""
        super().resizeEvent(event)
        # Position the label in the right 24px area with vertical centering
        dropdown_width = 24
        # Add 3px top/bottom margin to prevent overlap with border
        self.arrow_label.setGeometry(self.width() - dropdown_width, 3, dropdown_width, self.height() - 6)
    
    def _apply_custom_style(self, is_dark):
        """Apply custom styling with proper width ratios"""
        # Calculate dropdown width for arrow area
        dropdown_width = 24  # Fixed width for arrow area (matches CustomTargetSizeSpinBox)
        text_offset = 8  # Left offset for text and dropdown items
        
        if is_dark:
            bg_color = "#2b2b2b"
            text_color = "#ffffff"
            border_color = "#555555"
            arrow_color = "#ffffff"
            hover_border = "#4CAF50"
            dropdown_bg = "#2b2b2b"
            menu_bg = "#2b2b2b"
            menu_text = "#ffffff"
            menu_hover = "#3d3d3d"
        else:
            bg_color = "white"
            text_color = "#333333"
            border_color = "#cccccc"
            arrow_color = "#333333"
            hover_border = "#4CAF50"
            dropdown_bg = "white"
            menu_bg = "white"
            menu_text = "#333333"
            menu_hover = "#e0e0e0"
        
        style = f"""
            QComboBox {{
                background-color: {bg_color};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 4px {dropdown_width}px 4px {text_offset}px;
            }}
            QComboBox:hover {{
                border-color: {hover_border};
            }}
            QComboBox:disabled {{
                background-color: {bg_color};
                color: {text_color};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: {dropdown_width}px;
                border: none;
                background-color: {dropdown_bg};
            }}
            QComboBox::down-arrow {{
                image: none;
                width: 20px;
                height: 20px;
                border: none;
                background-color: {dropdown_bg};
                color: {arrow_color};
                font-size: 16px;
                font-weight: bold;
            }}
            QComboBox::down-arrow:on {{
                image: none;
                width: 20px;
                height: 20px;
                border: none;
                background-color: {dropdown_bg};
                color: {arrow_color};
                font-size: 16px;
                font-weight: bold;
            }}
            QComboBox QAbstractItemView {{
                background-color: {menu_bg};
                color: {menu_text};
                selection-background-color: {menu_hover};
                selection-color: {menu_text};
                border: 1px solid {border_color};
                outline: none;
                padding-left: 15px;
            }}
            QComboBox QAbstractItemView::item {{
                background-color: {menu_bg};
                color: {menu_text};
                padding: 4px 8px 4px 15px;
                min-height: 20px;
                border: none;
                outline: none;
            }}
            QComboBox QAbstractItemView::item:hover {{
                background-color: {menu_hover};
                color: {menu_text};
            }}
            QComboBox QAbstractItemView::item:selected {{
                background-color: {menu_hover};
                color: {menu_text};
                border: none;
                outline: none;
            }}
        """
        self.setStyleSheet(style)


class SpinBoxLineEdit(QLineEdit):
    """Custom QLineEdit for spinbox that intercepts Enter/Escape keys before default handling"""
    
    enterPressed = pyqtSignal()
    escapePressed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def keyPressEvent(self, event):
        """Intercept Enter/Escape before default handling"""
        from PyQt6.QtCore import Qt
        
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.enterPressed.emit()
            event.accept()
            return  # Don't call super - prevents selectAll behavior
        
        if event.key() == Qt.Key.Key_Escape:
            self.escapePressed.emit()
            event.accept()
            return  # Don't call super
        
        # For all other keys, use default handling
        super().keyPressEvent(event)


class DragOverlay(QWidget):
    """Transparent overlay that captures mouse events for drag-to-change behavior"""
    
    def __init__(self, parent_spinbox_widget):
        super().__init__(parent_spinbox_widget)
        self.parent_widget = parent_spinbox_widget
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setMouseTracking(True)
        
        # Drag state
        self.is_dragging = False
        self.drag_start_x = 0
        self.drag_start_value = 0.0
    
    def mousePressEvent(self, event):
        """Start drag tracking on mouse press"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.drag_start_x = event.globalPosition().x()
            self.drag_start_value = self.parent_widget.spinbox.value()
            self.grabMouse()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Update value based on horizontal drag distance"""
        if self.is_dragging:
            delta_x = event.globalPosition().x() - self.drag_start_x
            
            # Only update if drag exceeds 10 pixel threshold (prevents jittery small changes)
            if abs(delta_x) >= 10:
                value_change = delta_x * self.parent_widget.drag_sensitivity
                new_value = self.drag_start_value + value_change
                
                # Clamp to range
                spinbox = self.parent_widget.spinbox
                new_value = max(spinbox.minimum(), min(new_value, spinbox.maximum()))
                spinbox.setValue(new_value)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """End drag - enter edit mode if it was a click (minimal movement)"""
        if event.button() == Qt.MouseButton.LeftButton and self.is_dragging:
            delta = abs(event.globalPosition().x() - self.drag_start_x)
            self.is_dragging = False
            self.releaseMouse()
            
            # If minimal movement, this was a click - enter text edit mode
            if delta < 3:
                # Hide overlay to allow direct interaction with lineEdit
                self.hide()
                line_edit = self.parent_widget.spinbox.lineEdit()
                line_edit.setFocus(Qt.FocusReason.MouseFocusReason)
                line_edit.selectAll()
                line_edit.setCursor(Qt.CursorShape.IBeamCursor)
            event.accept()


class CustomTargetSizeSpinBox(QWidget):
    """
    Custom target size spinbox with MB suffix and theme support.
    Features delicate chevron arrows matching the CustomComboBox style.
    Supports drag-to-change: click and drag horizontally to adjust value.
    """
    
    valueChanged = pyqtSignal(float)  # Emit when value changes
    
    def __init__(self, parent=None, default_value=1.0, on_enter_callback=None):
        super().__init__(parent)
        self.is_dark = True
        self.on_enter_callback = on_enter_callback  # Callback when Enter is pressed
        
        # Import Qt classes
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QFont, QCursor
        
        # Drag state tracking
        self.drag_sensitivity = 0.01  # Value change per pixel dragged (10px = 0.1 value change)
        
        # Create custom cursor (horizontal arrows with I-beam)
        self.custom_drag_cursor = self._create_custom_cursor(is_dark=True)
        
        # Create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create spinbox without buttons
        from PyQt6.QtWidgets import QDoubleSpinBox, QAbstractSpinBox
        from PyQt6.QtGui import QRegularExpressionValidator
        from PyQt6.QtCore import QRegularExpression
        
        self.spinbox = QDoubleSpinBox()
        
        # Use custom lineEdit that intercepts Enter/Escape
        self.custom_line_edit = SpinBoxLineEdit()
        self.spinbox.setLineEdit(self.custom_line_edit)
        
        # Connect signals from custom lineEdit
        self.custom_line_edit.enterPressed.connect(self._on_enter_pressed)
        self.custom_line_edit.escapePressed.connect(self._on_escape_pressed)
        
        self.spinbox.setRange(0.1, 100.0)
        self.spinbox.setValue(default_value)
        self.spinbox.setDecimals(1)
        self.spinbox.setSingleStep(0.1)
        self.spinbox.setSuffix("")
        self.spinbox.setMinimumWidth(120)
        self.spinbox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        
        # Set validator to only allow numeric input
        validator = QRegularExpressionValidator(QRegularExpression(r"^\d*\.?\d*$"))
        self.spinbox.lineEdit().setValidator(validator)
        
        # Set focus policy to click focus - loses focus when clicking elsewhere
        self.spinbox.lineEdit().setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        
        # Install event filter on BOTH spinbox and lineEdit to catch Enter/Escape
        self.spinbox.installEventFilter(self)
        self.spinbox.lineEdit().installEventFilter(self)
        
        # Set custom cursor on lineEdit
        self.spinbox.lineEdit().setCursor(self.custom_drag_cursor)
        
        # Create custom arrow buttons
        arrow_container = QWidget()
        arrow_layout = QVBoxLayout(arrow_container)
        arrow_layout.setContentsMargins(0, 0, 0, 0)
        arrow_layout.setSpacing(0)
        
        # Create font with horizontal stretch for wider chevrons
        arrow_font = QFont()
        arrow_font.setPointSize(11)
        arrow_font.setStretch(200)  # 200% width stretch
        arrow_font.setWeight(QFont.Weight.DemiBold)  # Semi-bold weight
        
        self.up_arrow = QLabel("˄")
        self.up_arrow.setFont(arrow_font)
        self.up_arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.up_arrow.setFixedSize(24, 14)  # Fixed height to match half of spinbox
        self.up_arrow.mousePressEvent = lambda e: self.spinbox.stepUp()
        
        self.down_arrow = QLabel("˅")
        self.down_arrow.setFont(arrow_font)
        self.down_arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.down_arrow.setFixedSize(24, 14)  # Fixed height to match half of spinbox
        self.down_arrow.mousePressEvent = lambda e: self.spinbox.stepDown()
        
        arrow_layout.addWidget(self.up_arrow)
        arrow_layout.addWidget(self.down_arrow)
        arrow_container.setFixedHeight(28)  # Match spinbox height (padding included)
        
        # Connect signal
        self.spinbox.valueChanged.connect(self.valueChanged.emit)
        
        layout.addWidget(self.spinbox)
        layout.addWidget(arrow_container)
        
        # Create overlay for drag handling (sits on top of spinbox)
        self.drag_overlay = DragOverlay(self)
        self.drag_overlay.setCursor(self.custom_drag_cursor)
        
        self._apply_custom_style(self.is_dark)
    
    def _create_custom_cursor(self, is_dark=True):
        """Create custom cursor with horizontal arrows and I-beam in center
        
        Args:
            is_dark: If True, create bright cursor for dark mode. If False, dark cursor for light mode.
        """
        from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QCursor
        from PyQt6.QtCore import Qt, QPointF
        
        # Create pixmap for cursor (32x32)
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Choose colors based on theme
        if is_dark:
            # Dark mode: bright cursor with dark outline
            main_color = QColor(255, 255, 255)  # White
            outline_color = QColor(0, 0, 0)  # Black
        else:
            # Light mode: dark cursor with light outline
            main_color = QColor(0, 0, 0)  # Black
            outline_color = QColor(255, 255, 255)  # White
        
        # Draw outline first (will be behind main lines)
        pen = QPen(outline_color)
        pen.setWidth(3)
        painter.setPen(pen)
        
        # Draw outline arrows and I-beam
        painter.drawLine(10, 16, 6, 13)
        painter.drawLine(10, 16, 6, 19)
        painter.drawLine(16, 8, 16, 24)
        painter.drawLine(14, 8, 18, 8)
        painter.drawLine(14, 24, 18, 24)
        painter.drawLine(22, 16, 26, 13)
        painter.drawLine(22, 16, 26, 19)
        
        # Draw main cursor on top
        pen.setColor(main_color)
        pen.setWidth(2)
        painter.setPen(pen)
        
        # Draw left arrow <
        painter.drawLine(10, 16, 6, 13)
        painter.drawLine(10, 16, 6, 19)
        
        # Draw I-beam in center
        painter.drawLine(16, 8, 16, 24)  # Vertical line
        painter.drawLine(14, 8, 18, 8)   # Top serif
        painter.drawLine(14, 24, 18, 24) # Bottom serif
        
        # Draw right arrow >
        painter.drawLine(22, 16, 26, 13)
        painter.drawLine(22, 16, 26, 19)
        
        painter.end()
        
        return QCursor(pixmap, 16, 16)  # Hotspot at center
    
    def resizeEvent(self, event):
        """Position the drag overlay to cover the spinbox"""
        super().resizeEvent(event)
        # Position overlay to cover the spinbox (not the arrow buttons)
        spinbox_geo = self.spinbox.geometry()
        self.drag_overlay.setGeometry(spinbox_geo)
        self.drag_overlay.raise_()  # Ensure it's on top
    
    def showEvent(self, event):
        """Ensure overlay is positioned correctly when shown"""
        super().showEvent(event)
        # Delay geometry update to after layout is complete
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, self._update_overlay_geometry)
    
    def _update_overlay_geometry(self):
        """Update overlay geometry to match spinbox"""
        spinbox_geo = self.spinbox.geometry()
        self.drag_overlay.setGeometry(spinbox_geo)
        self.drag_overlay.raise_()
    
    def eventFilter(self, obj, event):
        """Filter events on spinbox and lineEdit to detect focus changes and key presses"""
        from PyQt6.QtCore import QEvent, Qt
        from PyQt6.QtWidgets import QApplication
        
        # Check for KeyPress on BOTH spinbox and lineEdit - intercept Enter/Escape
        if event.type() == QEvent.Type.KeyPress:
            if obj in (self.spinbox, self.spinbox.lineEdit()):
                if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Escape):
                    # Block further events temporarily
                    self.spinbox.lineEdit().blockSignals(True)
                    
                    # Deselect text first
                    self.spinbox.lineEdit().deselect()
                    
                    # Set focus to parent or main window to truly exit
                    main_window = self.window()
                    if main_window:
                        main_window.setFocus(Qt.FocusReason.OtherFocusReason)
                    
                    # Clear focus from spinbox
                    self.spinbox.lineEdit().clearFocus()
                    self.spinbox.clearFocus()
                    
                    # Restore drag mode
                    self._restore_drag_mode()
                    
                    # Unblock signals
                    self.spinbox.lineEdit().blockSignals(False)
                    
                    # If Enter was pressed and we have a callback, call it
                    if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and self.on_enter_callback:
                        from PyQt6.QtCore import QTimer
                        QTimer.singleShot(0, self.on_enter_callback)
                    
                    return True  # Consume the event
        
        # Focus handling on BOTH spinbox and lineEdit
        if obj in (self.spinbox, self.spinbox.lineEdit()):
            if event.type() == QEvent.Type.FocusOut:
                # Restore drag mode when losing focus (clicking elsewhere)
                # Use a slightly longer delay to ensure focus transition is complete
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(50, self._restore_drag_mode_from_focus_out)
                QTimer.singleShot(150, self._restore_drag_mode_from_focus_out)
                return False
            
            elif event.type() == QEvent.Type.FocusIn:
                self.drag_overlay.hide()
                self.spinbox.lineEdit().setCursor(Qt.CursorShape.IBeamCursor)
        
        return super().eventFilter(obj, event)
    
    def _on_enter_pressed(self):
        """Handle Enter key from custom lineEdit"""
        # Deselect text first
        self.spinbox.lineEdit().deselect()
        # Clear focus to exit edit mode
        self.spinbox.lineEdit().clearFocus()
        self.spinbox.clearFocus()
        # Restore drag mode
        self._restore_drag_mode()
        
        # Call callback if provided
        if self.on_enter_callback:
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, self.on_enter_callback)
    
    def _on_escape_pressed(self):
        """Handle Escape key from custom lineEdit"""
        # Deselect text first
        self.spinbox.lineEdit().deselect()
        # Clear focus to exit edit mode
        self.spinbox.lineEdit().clearFocus()
        self.spinbox.clearFocus()
        # Restore drag mode
        self._restore_drag_mode()
    
    def _restore_drag_mode_from_focus_out(self):
        """Restore drag mode specifically when focus is lost by clicking elsewhere.
        This version doesn't try to clear focus since it's already gone."""
        from PyQt6.QtCore import QTimer, Qt
        
        # Reset overlay drag state to fresh state
        self.drag_overlay.is_dragging = False
        self.drag_overlay.drag_start_x = 0
        self.drag_overlay.drag_start_value = 0.0
        
        # Deselect any selected text (shouldn't have any, but just in case)
        self.spinbox.lineEdit().deselect()
        
        # Restore custom cursor on lineEdit
        self.spinbox.lineEdit().setCursor(self.custom_drag_cursor)
        
        # Re-enable mouse event handling on overlay
        self.drag_overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        
        # Ensure overlay geometry is correct
        spinbox_geo = self.spinbox.geometry()
        self.drag_overlay.setGeometry(spinbox_geo)
        
        # Show overlay and ensure it's on top
        self.drag_overlay.show()
        self.drag_overlay.setVisible(True)
        self.drag_overlay.setEnabled(True)
        self.drag_overlay.raise_()
        
        # Also update after a short delay to handle any layout changes
        def _ensure_overlay():
            if not self.spinbox.lineEdit().hasFocus():
                spinbox_geo = self.spinbox.geometry()
                self.drag_overlay.setGeometry(spinbox_geo)
                self.drag_overlay.show()
                self.drag_overlay.setEnabled(True)
                self.drag_overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
                self.drag_overlay.raise_()
        
        QTimer.singleShot(10, _ensure_overlay)
        QTimer.singleShot(50, _ensure_overlay)
    
    def _restore_drag_mode(self):
        """Restore drag mode by showing overlay and resetting cursor"""
        from PyQt6.QtCore import QTimer, Qt
        
        # Reset overlay drag state to fresh state
        self.drag_overlay.is_dragging = False
        self.drag_overlay.drag_start_x = 0
        self.drag_overlay.drag_start_value = 0.0
        
        # Ensure spinbox doesn't have focus first
        if self.spinbox.lineEdit().hasFocus():
            self.spinbox.lineEdit().clearFocus()
        
        # Deselect any selected text
        self.spinbox.lineEdit().deselect()
        
        # Restore custom cursor on lineEdit
        self.spinbox.lineEdit().setCursor(self.custom_drag_cursor)
        
        # Re-enable mouse event handling on overlay
        self.drag_overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        
        # Show overlay immediately and ensure it's visible
        self.drag_overlay.show()
        self.drag_overlay.setVisible(True)
        self.drag_overlay.setEnabled(True)
        
        # Update geometry with a slight delay to ensure layout is complete
        def _update_geometry():
            self._update_overlay_geometry()
            self.drag_overlay.raise_()
            # Force overlay to be visible and enabled
            self.drag_overlay.show()
            self.drag_overlay.setEnabled(True)
            self.drag_overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        
        QTimer.singleShot(0, _update_geometry)
        QTimer.singleShot(10, _update_geometry)  # Double-check after a short delay

    
    def value(self):
        """Get current value"""
        return self.spinbox.value()
    
    def setValue(self, value):
        """Set value"""
        self.spinbox.setValue(value)
    
    def setRange(self, minimum, maximum):
        """Set the range of allowed values"""
        self.spinbox.setRange(minimum, maximum)
    
    def setDecimals(self, decimals):
        """Set number of decimal places"""
        self.spinbox.setDecimals(decimals)
    
    def setSensitivity(self, sensitivity):
        """Set drag sensitivity (value change per pixel)"""
        self.drag_sensitivity = sensitivity
    
    def setVisible(self, visible):
        """Override setVisible to apply to spinbox"""
        super().setVisible(visible)
        self.spinbox.setVisible(visible)
    
    def update_theme(self, is_dark):
        """Update styling based on theme"""
        self.is_dark = is_dark
        # Recreate cursor with new theme
        self.custom_drag_cursor = self._create_custom_cursor(is_dark=is_dark)
        self.spinbox.lineEdit().setCursor(self.custom_drag_cursor)
        self.drag_overlay.setCursor(self.custom_drag_cursor)
        self._apply_custom_style(is_dark)
    
    def _apply_custom_style(self, is_dark):
        """Apply custom styling with chevron arrows"""
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
            arrow_color = "#888888"
            hover_color = "#4CAF50"
        
        # Style the spinbox
        spinbox_style = f"""
            QDoubleSpinBox {{
                background-color: {bg_color};
                color: {text_color};
                border: 1px solid {border_color};
                border-top-left-radius: 4px;
                border-bottom-left-radius: 4px;
                border-top-right-radius: 0px;
                border-bottom-right-radius: 0px;
                padding: 4px 8px;
                min-height: 20px;
            }}
            QDoubleSpinBox:hover {{
                border-color: {hover_color};
            }}
            QDoubleSpinBox:focus {{
                border-color: {hover_color};
            }}
        """
        self.spinbox.setStyleSheet(spinbox_style)
        
        # Style the arrow labels with minimalistic appearance
        arrow_style = f"""
            QLabel {{
                background-color: {bg_color};
                color: {arrow_color};
                border: 1px solid {border_color};
                padding: 0px;
                margin: 0px;
            }}
            QLabel:hover {{
                color: {hover_color};
                border-color: {hover_color};
            }}
        """
        
        # Apply rounded corners to arrows
        self.up_arrow.setStyleSheet(arrow_style + f"""
            border-top-right-radius: 4px;
            border-bottom: none;
            border-left: none;
        """)
        
        self.down_arrow.setStyleSheet(arrow_style + f"""
            border-bottom-right-radius: 4px;
            border-top: none;
            border-left: none;
        """)


class TimeRangeSlider(QWidget):
    """
    Custom range slider with two handles for selecting a range of values.
    Used for time cutting and retime operations.
    Supports dark mode with theme-aware colors.
    """
    
    # Signals emitted when values change
    rangeChanged = pyqtSignal(float, float)  # start_value, end_value
    
    def __init__(self, parent=None, is_dark_mode=True):
        super().__init__(parent)
        self.setMinimumHeight(40)
        self.setMaximumHeight(50)
        
        # Range settings
        self.min_value = 0.0
        self.max_value = 1.0
        self.start_value = 0.0
        self.end_value = 1.0
        
        # Handle settings
        self.handle_radius = 8
        self.active_handle = None  # None, 'start', or 'end'
        
        # Padding for text and handles
        self.padding = 20  # Space from edges for text labels and handles - increased for safety
        
        # Theme colors (will be set based on mode)
        self.is_dark_mode = is_dark_mode
        self.update_theme_colors(is_dark_mode)
        
        self.setMouseTracking(True)
    
    def update_theme_colors(self, is_dark_mode):
        """Update colors based on theme - always use blue for consistency"""
        self.is_dark_mode = is_dark_mode
        # Use blue colors for both dark and light modes
        self.track_color = QColor(200, 200, 200)
        self.range_color = QColor(33, 150, 243)  # Blue
        self.handle_color = QColor(33, 150, 243)
        self.handle_border_color = QColor(21, 101, 192)
        # Adjust text color based on mode for better contrast
        self.text_color = QColor(200, 200, 200) if is_dark_mode else QColor(50, 50, 50)
        self.update()
    
    def setRange(self, min_val, max_val):
        """Set the minimum and maximum values"""
        self.min_value = min_val
        self.max_value = max_val
        self.update()
    
    def setStartValue(self, value):
        """Set the start value"""
        self.start_value = max(self.min_value, min(value, self.end_value))
        self.update()
        self.rangeChanged.emit(self.start_value, self.end_value)
    
    def setEndValue(self, value):
        """Set the end value"""
        self.end_value = max(self.start_value, min(value, self.max_value))
        self.update()
        self.rangeChanged.emit(self.start_value, self.end_value)
    
    def getStartValue(self):
        """Get the start value"""
        return self.start_value
    
    def getEndValue(self):
        """Get the end value"""
        return self.end_value
    
    def valueToPixel(self, value):
        """Convert value to pixel position with padding"""
        available_width = self.width() - 2 * self.padding
        if available_width <= 0:
            return self.padding
        if self.max_value == self.min_value:
            return self.padding + available_width // 2
        ratio = (value - self.min_value) / (self.max_value - self.min_value)
        return self.padding + int(ratio * available_width)
    
    def pixelToValue(self, pixel):
        """Convert pixel position to value with padding"""
        available_width = self.width() - 2 * self.padding
        if available_width <= 0:
            return self.min_value
        # Clamp pixel to valid range
        pixel = max(self.padding, min(pixel, self.width() - self.padding))
        ratio = (pixel - self.padding) / available_width
        ratio = max(0.0, min(1.0, ratio))
        return self.min_value + ratio * (self.max_value - self.min_value)
    
    def paintEvent(self, event):
        """Paint the range slider with proper error handling"""
        try:
            painter = QPainter(self)
            if not painter.isActive():
                return
            
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Draw track using padding for safe rendering area
            track_y = self.height() // 2 - 2
            track_rect = QRect(self.padding, track_y, 
                              self.width() - 2 * self.padding, 4)
            painter.fillRect(track_rect, self.track_color)
            
            # Draw range
            start_pixel = self.valueToPixel(self.start_value)
            end_pixel = self.valueToPixel(self.end_value)
            range_rect = QRect(start_pixel, track_y, 
                              end_pixel - start_pixel, 4)
            painter.fillRect(range_rect, self.range_color)
            
            # Draw handles
            start_center = QPoint(start_pixel, self.height() // 2)
            end_center = QPoint(end_pixel, self.height() // 2)
            
            # Start handle
            painter.setPen(QPen(self.handle_border_color, 2))
            painter.setBrush(QBrush(self.handle_color))
            painter.drawEllipse(start_center, self.handle_radius, self.handle_radius)
            
            # End handle
            painter.drawEllipse(end_center, self.handle_radius, self.handle_radius)
            
            # Percentage labels removed per user request
            
            painter.end()
        except Exception as e:
            print(f"Error in TimeRangeSlider.paintEvent: {e}")
    
    def mousePressEvent(self, event):
        """Handle mouse press events with smart range selection"""
        try:
            if event.button() != Qt.MouseButton.LeftButton:
                self.active_handle = None
                return
            
            # Validate widget dimensions
            if self.width() <= 2 * self.handle_radius or self.height() == 0:
                self.active_handle = None
                return
            
            pos = event.pos()
            
            # Check if clicking directly on start handle
            start_pixel = self.valueToPixel(self.start_value)
            start_center = QPoint(start_pixel, self.height() // 2)
            if (pos - start_center).manhattanLength() <= self.handle_radius * 1.5:
                self.active_handle = 'start'
                return
            
            # Check if clicking directly on end handle
            end_pixel = self.valueToPixel(self.end_value)
            end_center = QPoint(end_pixel, self.height() // 2)
            if (pos - end_center).manhattanLength() <= self.handle_radius * 1.5:
                self.active_handle = 'end'
                return
            
            # For clicks not on handles, determine which handle to move based on position
            clicked_value = self.pixelToValue(pos.x())
            start_pixel = self.valueToPixel(self.start_value)
            end_pixel = self.valueToPixel(self.end_value)
            
            # If clicked inside the colored range
            if start_pixel <= pos.x() <= end_pixel:
                # Move the previously selected handle, or the closest one
                if self.active_handle == 'start' or self.active_handle is None:
                    # Determine which handle is closer
                    start_dist = abs(pos.x() - start_pixel)
                    end_dist = abs(pos.x() - end_pixel)
                    self.active_handle = 'start' if start_dist <= end_dist else 'end'
                # Keep the same handle if it was already selected
                self.mouseMoveEvent(event)
                return
            
            # If clicked to the right of the range (outside, above end)
            elif pos.x() > end_pixel:
                # Move end handle to the clicked position
                self.active_handle = 'end'
                self.mouseMoveEvent(event)
                return
            
            # If clicked to the left of the range (outside, below start)
            elif pos.x() < start_pixel:
                # Move start handle to the clicked position
                self.active_handle = 'start'
                self.mouseMoveEvent(event)
                return
                
        except Exception as e:
            print(f"Error in TimeRangeSlider.mousePressEvent: {e}")
            self.active_handle = None
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events with full validation and smart behavior"""
        if not self.active_handle:
            return
        
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            # Mouse moved without button pressed, release handle
            self.active_handle = None
            return
        
        try:
            # Validate position
            pos_x = event.pos().x()
            
            # Clamp position to valid widget range
            if pos_x < self.handle_radius:
                pos_x = self.handle_radius
            elif pos_x > self.width() - self.handle_radius:
                pos_x = self.width() - self.handle_radius
            
            value = self.pixelToValue(pos_x)
            
            # Move the active handle
            if self.active_handle == 'start':
                self.setStartValue(value)
            elif self.active_handle == 'end':
                self.setEndValue(value)
                
        except Exception as e:
            print(f"Error in TimeRangeSlider.mouseMoveEvent: {e}")
            # Don't reset handle here, let mouseReleaseEvent do it
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        try:
            if event.button() == Qt.MouseButton.LeftButton:
                self.active_handle = None
        except Exception as e:
            print(f"Error in TimeRangeSlider.mouseReleaseEvent: {e}")
            self.active_handle = None
    
    def leaveEvent(self, event):
        """Handle mouse leave events - reset active handle"""
        try:
            self.active_handle = None
        except Exception as e:
            print(f"Error in TimeRangeSlider.leaveEvent: {e}")


class ResizeFolder(QGroupBox):
    """
    Folder/Group for resize options with multiple variant support.
    Supports single value or multiple variants for batch processing.
    """
    
    resizeChanged = pyqtSignal(dict)  # Emits dict with resize settings
    
    def __init__(self, parent=None, is_dark_mode=True, combobox_style=""):
        super().__init__("Resize Options", parent)
        self.is_dark_mode = is_dark_mode
        self.combobox_style = combobox_style
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the resize options UI"""
        layout = QFormLayout(self)
        
        # Resize mode selection
        self.resize_mode = CustomComboBox()
        self.resize_mode.addItems(["No resize", "By width (pixels)", "By ratio (percent)"])
        self.resize_mode.update_theme(self.is_dark_mode)
        self.resize_mode.currentTextChanged.connect(self.on_mode_changed)
        layout.addRow("Mode:", self.resize_mode)
        
        # Multiple variants toggle
        self.multiple_variants = QCheckBox("Multiple variants")
        self.multiple_variants.toggled.connect(self.on_variants_toggled)
        layout.addRow(self.multiple_variants)
        
        # Single value input
        self.single_value = QSpinBox()
        self.single_value.setRange(1, 10000)
        self.single_value.setValue(720)
        self.single_value.setVisible(False)
        self.single_value_label = QLabel("Width (pixels):")
        self.single_value_label.setVisible(False)
        layout.addRow(self.single_value_label, self.single_value)
        
        # Multiple variants input
        self.variants_input = QLineEdit()
        self.variants_input.setPlaceholderText("e.g., 30,50,80 or 720,1280,1920")
        self.variants_input.setText("720,1280,1920")
        self.variants_input.setVisible(False)
        self.variants_label = QLabel("Values:")
        self.variants_label.setVisible(False)
        layout.addRow(self.variants_label, self.variants_input)
    
    def on_mode_changed(self, mode):
        """Handle resize mode change"""
        if mode == "No resize":
            self.single_value.setVisible(False)
            self.single_value_label.setVisible(False)
            self.multiple_variants.setVisible(False)
            self.variants_input.setVisible(False)
            self.variants_label.setVisible(False)
        else:
            self.multiple_variants.setVisible(True)
            if self.multiple_variants.isChecked():
                self.on_variants_toggled(True)
            else:
                self.on_variants_toggled(False)
    
    def on_variants_toggled(self, checked):
        """Handle multiple variants toggle"""
        if checked:
            self.single_value.setVisible(False)
            self.single_value_label.setVisible(False)
            self.variants_input.setVisible(True)
            self.variants_label.setVisible(True)
        else:
            self.single_value.setVisible(True)
            self.single_value_label.setVisible(True)
            self.variants_input.setVisible(False)
            self.variants_label.setVisible(False)
        self.emit_changed()
    
    def get_resize_settings(self):
        """Get current resize settings as dict"""
        mode = self.resize_mode.currentText()
        if mode == "No resize":
            return {"enabled": False}
        
        return {
            "enabled": True,
            "mode": mode,
            "multiple": self.multiple_variants.isChecked(),
            "value": self.single_value.value() if not self.multiple_variants.isChecked() else None,
            "variants": self.variants_input.text() if self.multiple_variants.isChecked() else None
        }
    
    def emit_changed(self):
        """Emit change signal"""
        self.resizeChanged.emit(self.get_resize_settings())
    
    def update_theme(self, is_dark_mode, combobox_style):
        """Update theme colors"""
        self.is_dark_mode = is_dark_mode
        self.combobox_style = combobox_style
        self.resize_mode.update_theme(is_dark_mode)


class RotationOptions(QGroupBox):
    """
    Group for rotation options with dark mode support.
    Provides preset rotation angles (0°, 90°, 180°, 270°).
    """
    
    rotationChanged = pyqtSignal(str)  # Emits rotation angle string
    
    def __init__(self, parent=None, is_dark_mode=True, combobox_style=""):
        super().__init__("Rotation Options", parent)
        self.is_dark_mode = is_dark_mode
        self.combobox_style = combobox_style
        self.setSizePolicy(self.sizePolicy().horizontalPolicy(), QSizePolicy.Policy.Maximum)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup rotation UI"""
        layout = QFormLayout(self)
        
        self.rotation_angle = CustomComboBox()
        self.rotation_angle.addItems(["No rotation", "90° clockwise", "180°", "270° clockwise"])
        self.rotation_angle.update_theme(self.is_dark_mode)
        self.rotation_angle.currentTextChanged.connect(self.on_rotation_changed)
        layout.addRow("Angle:", self.rotation_angle)
    
    def on_rotation_changed(self, angle):
        """Handle rotation change"""
        self.rotationChanged.emit(angle)
    
    def get_rotation_setting(self):
        """Get current rotation setting"""
        angle = self.rotation_angle.currentText()
        if angle == "No rotation":
            return None
        elif angle == "90° clockwise":
            return 90
        elif angle == "180°":
            return 180
        elif angle == "270° clockwise":
            return 270
        return None
    
    def update_theme(self, is_dark_mode, combobox_style):
        """Update theme colors"""
        self.is_dark_mode = is_dark_mode
        self.combobox_style = combobox_style
        self.rotation_angle.update_theme(is_dark_mode)
