"""
Custom PyQt6 Widgets with Dark Mode Support
Provides TimeRangeSlider, ResizeFolder, and Rotation classes
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, 
    QSpinBox, QLineEdit, QGroupBox, QFormLayout, QCheckBox, QSizePolicy, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QPoint
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QPalette
from client.utils.font_manager import AppFonts


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
        
        # Create font with horizontal stretch
        arrow_font = QFont()
        arrow_font.setPointSize(11)
        arrow_font.setStretch(150)  # 150% width stretch
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
        # Position the label in the right 20px area with vertical centering
        dropdown_width = 20
        # Add 2px top margin to center the arrow better
        self.arrow_label.setGeometry(self.width() - dropdown_width, 2, dropdown_width, self.height() - 4)
    
    def _apply_custom_style(self, is_dark):
        """Apply custom styling with proper width ratios"""
        # Calculate dropdown width for arrow area
        dropdown_width = 20  # Fixed width for arrow area
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
        self.setMinimumHeight(85)
        self.setMaximumHeight(95)
        
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
            
            # Draw value labels with proper bounds clamping
            painter.setPen(QPen(self.text_color))
            font = AppFonts.get_custom_font(8)  # 8pt font for labels
            painter.setFont(font)
            
            start_text = f"{self.start_value * 100:.0f}%"
            end_text = f"{self.end_value * 100:.0f}%"
            
            # Position labels below handles with clipping prevention
            start_text_rect = painter.boundingRect(0, 0, 100, 20, Qt.AlignmentFlag.AlignCenter, start_text)
            start_label_y = self.height() // 2 + self.handle_radius + 8
            # Ensure text stays within padding bounds
            start_label_x = max(self.padding + start_text_rect.width() // 2, 
                               min(start_pixel, self.width() - self.padding - start_text_rect.width() // 2))
            start_text_rect.moveCenter(QPoint(start_label_x, start_label_y))
            painter.drawText(start_text_rect, Qt.AlignmentFlag.AlignCenter, start_text)
            
            end_text_rect = painter.boundingRect(0, 0, 100, 20, Qt.AlignmentFlag.AlignCenter, end_text)
            end_label_y = self.height() // 2 + self.handle_radius + 8
            # Ensure text stays within padding bounds
            end_label_x = max(self.padding + end_text_rect.width() // 2, 
                             min(end_pixel, self.width() - self.padding - end_text_rect.width() // 2))
            end_text_rect.moveCenter(QPoint(end_label_x, end_label_y))
            painter.drawText(end_text_rect, Qt.AlignmentFlag.AlignCenter, end_text)
            
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
