"""
Custom PyQt6 Widgets with Dark Mode Support
Provides TimeRangeSlider, ResizeFolder, and Rotation classes
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, 
    QSpinBox, QLineEdit, QGroupBox, QFormLayout, QCheckBox, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QPoint
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush
from client.utils.font_manager import AppFonts


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
        self.setMinimumHeight(50)
        self.setMaximumHeight(60)
        
        # Range settings
        self.min_value = 0.0
        self.max_value = 1.0
        self.start_value = 0.0
        self.end_value = 1.0
        
        # Handle settings
        self.handle_radius = 8
        self.active_handle = None  # None, 'start', or 'end'
        
        # Theme colors (will be set based on mode)
        self.is_dark_mode = is_dark_mode
        self.update_theme_colors(is_dark_mode)
        
        self.setMouseTracking(True)
    
    def update_theme_colors(self, is_dark_mode):
        """Update colors based on theme"""
        self.is_dark_mode = is_dark_mode
        if is_dark_mode:
            self.track_color = QColor(100, 100, 100)
            self.range_color = QColor(76, 175, 80)  # Green
            self.handle_color = QColor(76, 175, 80)
            self.handle_border_color = QColor(56, 142, 60)
            self.text_color = QColor(200, 200, 200)
        else:
            self.track_color = QColor(200, 200, 200)
            self.range_color = QColor(33, 150, 243)  # Blue
            self.handle_color = QColor(33, 150, 243)
            self.handle_border_color = QColor(21, 101, 192)
            self.text_color = QColor(50, 50, 50)
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
        """Convert value to pixel position"""
        width = self.width() - 2 * self.handle_radius
        if self.max_value == self.min_value:
            return self.handle_radius
        ratio = (value - self.min_value) / (self.max_value - self.min_value)
        return self.handle_radius + int(ratio * width)
    
    def pixelToValue(self, pixel):
        """Convert pixel position to value"""
        width = self.width() - 2 * self.handle_radius
        if width == 0:
            return self.min_value
        ratio = (pixel - self.handle_radius) / width
        ratio = max(0.0, min(1.0, ratio))
        return self.min_value + ratio * (self.max_value - self.min_value)
    
    def paintEvent(self, event):
        """Paint the range slider with proper error handling"""
        try:
            painter = QPainter(self)
            if not painter.isActive():
                return
            
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Draw track
            track_rect = QRect(self.handle_radius, self.height() // 2 - 2, 
                              self.width() - 2 * self.handle_radius, 4)
            painter.fillRect(track_rect, self.track_color)
            
            # Draw range
            start_pixel = self.valueToPixel(self.start_value)
            end_pixel = self.valueToPixel(self.end_value)
            range_rect = QRect(start_pixel, self.height() // 2 - 2, 
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
            
            # Draw value labels
            painter.setPen(QPen(self.text_color))
            font = AppFonts.get_custom_font(8)  # 8pt font for labels
            painter.setFont(font)
            
            start_text = f"{self.start_value * 100:.0f}%"
            end_text = f"{self.end_value * 100:.0f}%"
            
            # Position labels below handles
            start_text_rect = painter.boundingRect(0, 0, 100, 20, Qt.AlignmentFlag.AlignCenter, start_text)
            start_text_rect.moveCenter(QPoint(start_pixel, self.height() // 2 + self.handle_radius + 10))
            painter.drawText(start_text_rect, Qt.AlignmentFlag.AlignCenter, start_text)
            
            end_text_rect = painter.boundingRect(0, 0, 100, 20, Qt.AlignmentFlag.AlignCenter, end_text)
            end_text_rect.moveCenter(QPoint(end_pixel, self.height() // 2 + self.handle_radius + 10))
            painter.drawText(end_text_rect, Qt.AlignmentFlag.AlignCenter, end_text)
            
            painter.end()
        except Exception as e:
            print(f"Error in TimeRangeSlider.paintEvent: {e}")
    
    def mousePressEvent(self, event):
        """Handle mouse press events with proper error handling"""
        try:
            if event.button() != Qt.MouseButton.LeftButton:
                return
            
            # Validate widget dimensions
            if self.width() <= 2 * self.handle_radius or self.height() == 0:
                return
            
            pos = event.pos()
            
            # Check if clicking on start handle
            start_pixel = self.valueToPixel(self.start_value)
            start_center = QPoint(start_pixel, self.height() // 2)
            if (pos - start_center).manhattanLength() <= self.handle_radius:
                self.active_handle = 'start'
                return
            
            # Check if clicking on end handle
            end_pixel = self.valueToPixel(self.end_value)
            end_center = QPoint(end_pixel, self.height() // 2)
            if (pos - end_center).manhattanLength() <= self.handle_radius:
                self.active_handle = 'end'
                return
            
            # Check if clicking on range bar (with tolerance for narrow ranges)
            start_pixel = self.valueToPixel(self.start_value)
            end_pixel = self.valueToPixel(self.end_value)
            vertical_tolerance = max(10, self.height() // 2)
            
            if start_pixel <= pos.x() <= end_pixel and abs(pos.y() - self.height() // 2) <= vertical_tolerance:
                # Move the closer handle
                start_dist = abs(pos.x() - start_pixel)
                end_dist = abs(pos.x() - end_pixel)
                self.active_handle = 'start' if start_dist <= end_dist else 'end'
                # Trigger move immediately
                self.mouseMoveEvent(event)
        except Exception as e:
            print(f"Error in TimeRangeSlider.mousePressEvent: {e}")
            self.active_handle = None
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events with validation"""
        if not self.active_handle:
            return
        
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            self.active_handle = None
            return
        
        try:
            # Validate position
            pos_x = event.pos().x()
            if pos_x < 0 or pos_x > self.width():
                return
            
            value = self.pixelToValue(pos_x)
            
            if self.active_handle == 'start':
                self.setStartValue(value)
            elif self.active_handle == 'end':
                self.setEndValue(value)
        except Exception as e:
            print(f"Error in TimeRangeSlider.mouseMoveEvent: {e}")
    
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
        self.resize_mode = QComboBox()
        self.resize_mode.addItems(["No resize", "By width (pixels)", "By ratio (percent)"])
        self.resize_mode.setStyleSheet(self.combobox_style)
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
        self.resize_mode.setStyleSheet(combobox_style)


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
        
        self.rotation_angle = QComboBox()
        self.rotation_angle.addItems(["No rotation", "90° clockwise", "180°", "270° clockwise"])
        self.rotation_angle.setStyleSheet(self.combobox_style)
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
        self.rotation_angle.setStyleSheet(combobox_style)
