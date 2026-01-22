"""
Custom PyQt6 Widgets with Dark Mode Support
Provides TimeRangeSlider, ResizeFolder, and Rotation classes
"""

from PyQt6.QtCore import Qt, pyqtSignal, QRect, QRectF, QPoint, QPointF, QSize, QPropertyAnimation, QVariantAnimation, QEasingCurve, pyqtProperty, QTimer, QObject
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QPalette, QIcon, QPixmap, QFont, QFontMetrics
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, 
    QSpinBox, QLineEdit, QGroupBox, QFormLayout, QCheckBox, QSizePolicy, 
    QApplication, QButtonGroup, QStyleOptionButton, QStyle, QFrame, QFileDialog,
    QGraphicsOpacityEffect, QGraphicsDropShadowEffect
)
from client.utils.font_manager import AppFonts, FONT_FAMILY
from client.utils.resource_path import get_resource_path
from client.gui.theme_variables import get_theme, get_color
import os
import math


class SegmentedButton(QPushButton):
    """Individual segment button for the toggle control"""
    
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(32)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)


class GenericSegmentedControl(QFrame):
    """
    Generic pill-style horizontal segmented control.
    Supports dynamic segments and unified styling.
    """
    selectionChanged = pyqtSignal(str) # Emits segment ID
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_dark = True
        self.setObjectName("SegmentContainer")
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(4, 4, 4, 4)
        self.layout.setSpacing(4)
        
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        self.button_group.idClicked.connect(self._on_group_clicked)
        
        self.buttons = {} # id -> button
        self._button_ids = {} # button -> id
        
        self._apply_styles()
        
    def add_segment(self, segment_id, label, is_checked=False, button_class=SegmentedButton):
        """Add a segment button"""
        btn = button_class(label)
        btn.setObjectName("SegmentBtn")
        
        # Add to storage
        self.buttons[segment_id] = btn
        self._button_ids[btn] = segment_id
        
        # Add to group (using hash of id as int id is unreliable, we use object mapping)
        self.button_group.addButton(btn)
        self.layout.addWidget(btn)
        
        if is_checked:
            btn.setChecked(True)
            
        return btn
        
    def set_selected(self, segment_id):
        """Programmatically select a segment"""
        if segment_id in self.buttons:
            self.buttons[segment_id].setChecked(True)
            self.selectionChanged.emit(segment_id)
            
    def get_selected(self):
        """Get ID of currently selected segment"""
        btn = self.button_group.checkedButton()
        if btn and btn in self._button_ids:
            return self._button_ids[btn]
        return None
        
    def _on_group_clicked(self, btn):
        """Handle group click"""
        if btn in self._button_ids:
            seg_id = self._button_ids[btn]
            self.selectionChanged.emit(seg_id)

    def update_theme(self, is_dark):
        self._is_dark = is_dark
        self._apply_styles()
        
    def _apply_styles(self):
        theme = get_theme(self._is_dark)
        
        # Container styles (SegmentContainer)
        # Using subtle semi-transparent white (rgba 255,255,255,12) for a "glassy" delicate feel
        self.setStyleSheet(f"""
            QFrame#SegmentContainer {{
                background-color: rgba(255, 255, 255, 12);
                border: 1px solid {theme['border_dim']};
                border-radius: 10px;
                min-height: 42px;
            }}
        """)
        
        # Button styles (SegmentBtn) injected via stylesheet
        font_family = FONT_FAMILY
        
        btn_style = f"""
            QPushButton#SegmentBtn {{
                background-color: transparent;
                color: {theme['text_secondary']};
                border: none;
                border-radius: 6px;
                padding: 10px 22px;
                font-family: '{font_family}';
                font-size: 15px;
                font-weight: 500;
            }}
            QPushButton#SegmentBtn:hover:!checked {{
                background-color: rgba(255, 255, 255, 15);
                color: {theme['text_primary']};
            }}
            QPushButton#SegmentBtn:checked {{
                background-color: rgba(255, 255, 255, 30);
                color: {theme['text_primary']};
                font-weight: 600;
            }}
        """
        self.setStyleSheet(self.styleSheet() + btn_style)


class OutputDestinationSelector(GenericSegmentedControl):
    """
    Specific implementation for Output Destination (Source/Organized/Custom).
    Handles folder picking and path display.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._custom_path = ""
        
        # Add specific segments
        self.add_segment("source", "In Source", is_checked=True)
        self.add_segment("organized", "Organized")
        self.add_segment("custom", "Custom...")
        
        # Custom path label
        self.path_label = QLabel("")
        self.path_label.setVisible(False)
        self.path_label.setMaximumWidth(150)
        
        # Initial theme variable needed for path_label style
        theme = get_theme(self._is_dark)
        self.path_label.setStyleSheet(f"font-size: 10px; color: {theme['text_secondary']}; padding-left: 8px;")
        
        self.layout.addWidget(self.path_label)
        
    def _on_group_clicked(self, btn):
        # Override to intercept custom click
        if btn not in self._button_ids: return
        
        seg_id = self._button_ids[btn]
        
        if seg_id == "custom":
            # Open folder picker
            folder = QFileDialog.getExistingDirectory(
                self, "Select Output Folder", "",
                QFileDialog.Option.ShowDirsOnly
            )
            if folder:
                self._custom_path = folder
                display = self._truncate_path(folder)
                self.path_label.setText(display)
                self.path_label.setVisible(True)
                self.path_label.setToolTip(folder)
                self.selectionChanged.emit("custom")
            else:
                # Revert to previous or default (Source) if cancelled
                self.set_selected("source")
                # set_selected emits signal, so we are good.
        else:
            self.path_label.setVisible(False)
            self.selectionChanged.emit(seg_id)
            
    def update_theme(self, is_dark):
        super().update_theme(is_dark)
        theme = get_theme(is_dark)
        self.path_label.setStyleSheet(f"font-size: 10px; color: {theme['text_secondary']}; padding-left: 8px;")

    def _truncate_path(self, path, max_len=20):
        if len(path) <= max_len: return path
        parts = path.replace("\\", "/").split("/")
        if len(parts) <= 2: return "..." + path[-(max_len-3):]
        return f".../{parts[-2]}/{parts[-1]}"

    def get_selection(self):
        return self.get_selected() or "source"

    def get_custom_path(self):
        return self._custom_path if self.get_selected() == "custom" else None
        
    def get_organized_name(self):
        return "output"

# Backward compatibility alias
SegmentedControl = OutputDestinationSelector


class GPUIndicator(QWidget):
    """
    Glowing GPU indicator that pulses with a sin wave when GPU acceleration is active.
    Shows a GPU icon that glows with clamped(sin(), 0, 1) animation cycle.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._gpu_active = False
        self._glow_phase = 0.0
        self._base_color = QColor("#00FF00")  # Green for GPU active
        self._inactive_color = QColor("#555555")  # Gray when inactive
        
        # Animation timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_glow)
        self._timer.setInterval(50)  # 20 FPS for smooth animation
        
        # Fixed size for the indicator
        self.setFixedSize(32, 32)
        self.setToolTip("GPU Acceleration")
        
    @property
    def gpu_active(self) -> bool:
        return self._gpu_active
        
    @gpu_active.setter
    def gpu_active(self, value: bool):
        self._gpu_active = value
        if value:
            self._timer.start()
            self.setToolTip("GPU Acceleration Active")
        else:
            self._timer.stop()
            self._glow_phase = 0.0
            self.setToolTip("GPU Acceleration Inactive")
        self.update()
        
    def set_gpu_active(self, active: bool):
        """Set whether GPU is currently active"""
        self.gpu_active = active
        
    def _update_glow(self):
        """Update the glow animation phase"""
        self._glow_phase += 0.15  # Speed of the glow cycle
        if self._glow_phase > math.pi * 2:
            self._glow_phase -= math.pi * 2
        self.update()
        
    def _get_glow_intensity(self) -> float:
        """Calculate glow intensity using clamped sin wave"""
        # sin() returns -1 to 1, we want 0 to 1
        # clamp(sin(phase), 0, 1) = max(0, sin(phase))
        raw = math.sin(self._glow_phase)
        return max(0.0, min(1.0, raw))
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate center and size
        center_x = self.width() // 2
        center_y = self.height() // 2
        base_radius = min(self.width(), self.height()) // 2 - 4
        
        if self._gpu_active:
            intensity = self._get_glow_intensity()
            
            # Draw glow effect (multiple translucent circles)
            glow_color = QColor(self._base_color)
            for i in range(3, 0, -1):
                glow_alpha = int(intensity * 80 / i)
                glow_color.setAlpha(glow_alpha)
                glow_radius = base_radius + (i * 3 * intensity)
                painter.setBrush(QBrush(glow_color))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(
                    QPoint(center_x, center_y),
                    int(glow_radius), int(glow_radius)
                )
            
            # Draw main circle with dynamic brightness
            brightness = int(180 + (75 * intensity))
            main_color = QColor(0, brightness, 0)
            painter.setBrush(QBrush(main_color))
            painter.setPen(QPen(QColor("#00AA00"), 2))
            painter.drawEllipse(QPoint(center_x, center_y), base_radius, base_radius)
            
            # Draw GPU text
            painter.setPen(QPen(QColor("#FFFFFF")))
            font = painter.font()
            font.setPointSize(7)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "GPU")
            
        else:
            # Inactive state - gray circle
            painter.setBrush(QBrush(self._inactive_color))
            painter.setPen(QPen(QColor("#444444"), 2))
            painter.drawEllipse(QPoint(center_x, center_y), base_radius, base_radius)
            
            # Draw GPU text (dimmed)
            painter.setPen(QPen(QColor("#888888")))
            font = painter.font()
            font.setPointSize(7)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "GPU")



class AnimatedSideModeButton(QPushButton):
    """
    Custom button for sidebars that slides horizontally.
    Unselected buttons move RIGHT (+8px) to hide behind the folder edge.
    Selected/hovered buttons slide LEFT (to 0) to reveal themselves.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._offset = 8  # Default: hidden behind folder (moved right)
        
        self.animation = QPropertyAnimation(self, b"pos_offset")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Connect toggled signal to handle selection state change
        self.toggled.connect(self._handle_toggled)
        self._force_hidden = False
        
    def set_force_hidden(self, hidden):
        """Set whether the button should be forced into hidden state (offset 40)"""
        if self._force_hidden == hidden:
            return
            
        self._force_hidden = hidden
        
        # Calculate new target
        if self._force_hidden:
            target = 40 # Hide 90% behind edge
        else:
            target = 0 if self.isChecked() or self.underMouse() else 8
            
        self.animation.stop()
        self.animation.setEndValue(target)
        self.animation.start()
        
    @pyqtProperty(int)
    def pos_offset(self):
        return self._offset
        
    @pos_offset.setter
    def pos_offset(self, val):
        self._offset = val
        self.update()
        
    def _handle_toggled(self, checked):
        """Update animation when selection state changes"""
        if self._force_hidden:
            return
            
        # If checked, move to 0 (flush). If unchecked and not hovering, hide behind (8).
        target = 0 if checked or self.underMouse() else 8
        if target != self._offset:
            self.animation.stop()
            self.animation.setEndValue(target)
            self.animation.start()
            
    def enterEvent(self, event):
        """Slide out (to 0) when mouse enters"""
        if not self._force_hidden:
            self.animation.stop()
            self.animation.setEndValue(0)
            self.animation.start()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """Slide back behind folder when mouse leaves, unless selected"""
        if self._force_hidden:
            return
            
        if not self.isChecked():
            self.animation.stop()
            self.animation.setEndValue(8)
            self.animation.start()
        super().leaveEvent(event)
        
    def showEvent(self, event):
        """Ensure correct initial position based on selected state"""
        super().showEvent(event)
        # Set initial offset immediately without animation
        if self._force_hidden:
            self._offset = 40
        else:
            self._offset = 0 if self.isChecked() else 8
        self.update()

    def paintEvent(self, event):
        """Draw the button shifted by the current offset"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # Translate the painter horizontally
        # offset 0 = flush, offset 8 = hidden behind folder (moved right)
        painter.translate(int(self._offset), 0)
        
        opt = QStyleOptionButton()
        self.initStyleOption(opt)
        opt.rect = QRect(0, 0, 44, self.height())
        
        # Draw the button using standard style logic
        self.style().drawControl(QStyle.ControlElement.CE_PushButton, opt, painter, self)
        painter.end()


class ModeButtonsWidget(QWidget):
    """
    Uniform mode buttons component for Max Size / Manual selection.
    Used consistently across all tabs (Images, Videos, GIFs).
    """
    
    # Signal emitted when mode changes: emits "Max Size" or "Manual"
    modeChanged = pyqtSignal(str)
    
    def __init__(self, default_mode="Manual", orientation=Qt.Orientation.Horizontal, parent=None):
        """
        Args:
            default_mode: "Max Size", "Presets", or "Manual"
            orientation: Qt.Orientation.Horizontal or Qt.Orientation.Vertical
            parent: Parent widget
        """
        super().__init__(parent)
        self.orientation = orientation
        
        # Set up layout based on orientation
        if orientation == Qt.Orientation.Vertical:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(10)
            button_size = QSize(44, 44)
        else:
            layout = QHBoxLayout(self)
            layout.setContentsMargins(12, 0, 12, 0)
            layout.setSpacing(8)
            button_size = None
        
        # Button style - consistent across all instances
        if orientation == Qt.Orientation.Vertical:
            # Square buttons for vertical orientation - reflected horizontally
            # (Rounded on left, straight on right where it touches the panel)
            self.button_style_base = (
                "QPushButton { padding: 4px; border-top-left-radius: 8px; border-bottom-left-radius: 8px; "
                "border-top-right-radius: 0px; border-bottom-right-radius: 0px; "
                "border: 1px solid #555555; border-right: none; background-color: transparent; }"
                "QPushButton:hover { background-color: rgba(255, 255, 255, 0.1); }"
                "QPushButton:checked { background-color: #4CAF50; color: white; border-color: #43a047; }"
            )
        else:
            self.button_style_base = (
                "QPushButton { padding: 8px; border-radius: 6px; border: 1px solid #555555; background-color: transparent; }"
                "QPushButton:hover { background-color: rgba(255, 255, 255, 0.1); }"
                "QPushButton:checked { background-color: #4CAF50; color: white; border-color: #43a047; }"
            )
        
        icon_size = QSize(32, 32)  # Increased from 26x26
        
        if orientation == Qt.Orientation.Vertical:
            # Use animated version for vertical sidebar
            self.max_size_btn = AnimatedSideModeButton()
        else:
            self.max_size_btn = QPushButton()
        self.max_size_btn.setIcon(QIcon(get_resource_path("client/assets/icons/target_icon.svg")))
        self.max_size_btn.setIconSize(icon_size)
        self.max_size_btn.setCheckable(True)
        self.max_size_btn.setToolTip("Max Size: Auto-optimize to fit target file size")
        if button_size:
            self.max_size_btn.setFixedSize(button_size)
        else:
            self.max_size_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # Presets button
        if orientation == Qt.Orientation.Vertical:
            self.presets_btn = AnimatedSideModeButton()
        else:
            self.presets_btn = QPushButton()
        self.presets_btn.setIcon(QIcon(get_resource_path("client/assets/icons/presets.svg")))
        self.presets_btn.setIconSize(icon_size)
        self.presets_btn.setCheckable(True)
        self.presets_btn.setToolTip("Lab Presets: Select from social media and common aspect ratio presets")
        if button_size:
            self.presets_btn.setFixedSize(button_size)
        else:
            self.presets_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # Manual button
        if orientation == Qt.Orientation.Vertical:
            self.manual_btn = AnimatedSideModeButton()
        else:
            self.manual_btn = QPushButton()
        self.manual_btn.setIcon(QIcon(get_resource_path("client/assets/icons/settings.svg")))
        self.manual_btn.setIconSize(icon_size)
        self.manual_btn.setCheckable(True)
        self.manual_btn.setToolTip("Manual: Set quality settings yourself")
        if button_size:
            self.manual_btn.setFixedSize(button_size)
        else:
            self.manual_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # Button group for exclusive selection
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        self.button_group.addButton(self.max_size_btn)
        self.button_group.addButton(self.presets_btn)
        self.button_group.addButton(self.manual_btn)
        
        # Set default mode
        if default_mode == "Max Size":
            self.max_size_btn.setChecked(True)
        elif default_mode == "Presets":
            self.presets_btn.setChecked(True)
        else:
            self.manual_btn.setChecked(True)
        
        # Connect signals
        self.max_size_btn.toggled.connect(
            lambda checked: checked and self.modeChanged.emit("Max Size")
        )
        self.presets_btn.toggled.connect(
            lambda checked: checked and self.modeChanged.emit("Presets")
        )
        self.manual_btn.toggled.connect(
            lambda checked: checked and self.modeChanged.emit("Manual")
        )
        
        # Add buttons to layout
        layout.addWidget(self.max_size_btn)
        layout.addWidget(self.presets_btn)
        layout.addWidget(self.manual_btn)
        
        if orientation == Qt.Orientation.Vertical:
            layout.addStretch()
        
        # Initial theme application
        from client.utils.theme_utils import is_dark_mode
        self.update_theme(is_dark_mode())
        
        # Fixed size for consistency
        if orientation == Qt.Orientation.Vertical:
            self.setFixedWidth(44)
            self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        else:
            self.setFixedHeight(42)
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    
    def set_hidden_mode(self, hidden):
        """Force buttons into hidden (shy) mode"""
        if self.orientation == Qt.Orientation.Vertical:
            btn_list = [self.max_size_btn, self.presets_btn, self.manual_btn]
            for btn in btn_list:
                if hasattr(btn, 'set_force_hidden'):
                    btn.set_force_hidden(hidden)

    def _get_tinted_icon(self, icon_path, color):
        """Load SVG and apply tint color"""
        abs_path = get_resource_path(icon_path)
        if not os.path.exists(abs_path):
            return QIcon()
            
        pixmap = QPixmap(abs_path)
        if pixmap.isNull():
            return QIcon()
            
        scaled_pixmap = pixmap.scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        tinted_pixmap = QPixmap(scaled_pixmap.size())
        tinted_pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(tinted_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawPixmap(0, 0, scaled_pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(tinted_pixmap.rect(), color)
        painter.end()
        
        return QIcon(tinted_pixmap)

    def update_theme(self, is_dark):
        """Update button icons and styles based on theme"""
        icon_color = QColor(255, 255, 255) if is_dark else QColor(0, 0, 0) # White or Pure Black
        
        self.max_size_btn.setIcon(self._get_tinted_icon("client/assets/icons/target_icon.svg", icon_color))
        self.presets_btn.setIcon(self._get_tinted_icon("client/assets/icons/presets.svg", icon_color))
        self.manual_btn.setIcon(self._get_tinted_icon("client/assets/icons/settings.svg", icon_color))
        
        if is_dark:
            bg_hover = "rgba(255, 255, 255, 0.1)"
            border_color = "#555555"
        else:
            bg_hover = "rgba(0, 0, 0, 0.05)"
            border_color = "#cccccc"

        if self.orientation == Qt.Orientation.Vertical:
            button_style = (
                f"QPushButton {{ padding: 4px; border-top-left-radius: 8px; border-bottom-left-radius: 8px; "
                f"border-top-right-radius: 0px; border-bottom-right-radius: 0px; "
                f"border: 1px solid {border_color}; border-right: none; background-color: transparent; }}"
                f"QPushButton:hover {{ background-color: {bg_hover}; }}"
                "QPushButton:checked { background-color: #4CAF50; color: white; border-color: #43a047; }"
            )
        else:
            button_style = (
                f"QPushButton {{ padding: 8px; border-radius: 6px; border: 1px solid {border_color}; background-color: transparent; }}"
                f"QPushButton:hover {{ background-color: {bg_hover}; }}"
                "QPushButton:checked { background-color: #4CAF50; color: white; border-color: #43a047; }"
            )
        
        self.max_size_btn.setStyleSheet(button_style)
        self.presets_btn.setStyleSheet(button_style)
        self.manual_btn.setStyleSheet(button_style)
    
    def get_mode(self):
        """Get current mode: 'Max Size', 'Lab_presets', or 'Manual'"""
        if self.max_size_btn.isChecked():
            return "Max Size"
        elif self.presets_btn.isChecked():
            return "Lab_presets"
        return "Manual"
    
    def set_mode(self, mode):
        """Set the mode programmatically"""
        if mode == "Max Size":
            self.max_size_btn.setChecked(True)
        elif mode == "Lab_presets" or mode == "Presets":
            self.presets_btn.setChecked(True)
        else:
            self.manual_btn.setChecked(True)


class SideButtonGroup(QWidget):
    """
    General-purpose vertical side button group with custom icons.
    Used for mode selection and transform/time options on the left sidebar.
    Each button can have a custom icon, tooltip, and identifier.
    """
    
    # Signal emitted when selection changes: emits the button identifier
    selectionChanged = pyqtSignal(str)
    
    def __init__(self, buttons_config, default_selection=None, parent=None):
        """
        Args:
            buttons_config: List of dicts with keys: 'id', 'icon_path', 'tooltip'
                Example: [
                    {'id': 'resize', 'icon_path': 'client/assets/icons/scale.png', 'tooltip': 'Resize Options'},
                    {'id': 'rotate', 'icon_path': 'client/assets/icons/rotate.svg', 'tooltip': 'Rotation Options'},
                ]
            default_selection: ID of the button to select by default (first button if None)
            parent: Parent widget
        """
        super().__init__(parent)
        self.buttons = {}  # Store buttons by ID
        self.buttons_config = buttons_config
        
        # Vertical layout with proper spacing
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)  # Top/bottom padding for breathing room
        layout.setSpacing(8)  # Spacing between buttons
        
        # Button group for exclusive selection
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        
        # Create buttons from config
        for config in buttons_config:
            # Use AnimatedSideModeButton for "shy" behavior and hiding support
            btn = AnimatedSideModeButton()
            btn.setCheckable(True)
            btn.setFixedSize(QSize(44, 44))
            btn.setIconSize(QSize(24, 24))
            btn.setToolTip(config.get('tooltip', ''))
            
            # Store button by ID
            btn_id = config.get('id', '')
            self.buttons[btn_id] = btn
            btn.setProperty('button_id', btn_id)
            
            # Add to button group and layout
            self.button_group.addButton(btn)
            layout.addWidget(btn)
            
            # Connect toggled signal
            btn.toggled.connect(lambda checked, bid=btn_id: checked and self.selectionChanged.emit(bid))
        
        layout.addStretch()
        
        # Set default selection
        if default_selection and default_selection in self.buttons:
            self.buttons[default_selection].setChecked(True)
        elif buttons_config:
            first_id = buttons_config[0].get('id', '')
            if first_id in self.buttons:
                self.buttons[first_id].setChecked(True)
        
        # Fixed width for sidebar
        self.setFixedWidth(44)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        
        # Apply initial theme
        from client.utils.theme_utils import is_dark_mode
        self.update_theme(is_dark_mode())
    
    def set_hidden_mode(self, hidden, colored=True):
        """
        Force all side buttons into hidden mode (offset 40px).
        visible: if True, buttons are hidden (shy).
        colored: if True, buttons use vibrant colors. If False, grayscale.
        """
        for btn in self.buttons.values():
            if hasattr(btn, 'set_force_hidden'):
                btn.set_force_hidden(hidden)
        
        # Update button styles based on state
        from client.utils.theme_utils import is_dark_mode
        is_dark = is_dark_mode()
        
        if is_dark:
            bg_hover = "rgba(255, 255, 255, 0.1)"
            border_color = "#555555"
        else:
            bg_hover = "rgba(0, 0, 0, 0.05)"
            border_color = "#cccccc"
        
        if not colored:
            # Grayscale / No Color style
            button_style = (
                f"QPushButton {{ padding: 6px; border-top-left-radius: 8px; border-bottom-left-radius: 8px; "
                f"border-top-right-radius: 0px; border-bottom-right-radius: 0px; "
                f"border: 1px solid {border_color}; border-right: none; background-color: transparent; }}"
                f"QPushButton:hover {{ background-color: {bg_hover}; }}"
                "QPushButton:checked { background-color: rgba(128, 128, 128, 0.2); color: #888888; border-color: #666666; }"
            )
        else:
            # Vibrant Colored style
            button_style = (
                f"QPushButton {{ padding: 6px; border-top-left-radius: 8px; border-bottom-left-radius: 8px; "
                f"border-top-right-radius: 0px; border-bottom-right-radius: 0px; "
                f"border: 1px solid {border_color}; border-right: none; background-color: transparent; }}"
                f"QPushButton:hover {{ background-color: {bg_hover}; }}"
                "QPushButton:checked { background-color: #2196F3; color: white; border-color: #1e88e5; }"
            )
        
        for btn in self.buttons.values():
            btn.setStyleSheet(button_style)

    def _get_tinted_icon(self, icon_path, color):
        """Create a tinted icon from the given path"""
        abs_path = get_resource_path(icon_path)
        if not os.path.exists(abs_path):
            return QIcon()
        
        pixmap = QPixmap(abs_path)
        if pixmap.isNull():
            return QIcon()
        
        scaled_pixmap = pixmap.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        tinted_pixmap = QPixmap(scaled_pixmap.size())
        tinted_pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(tinted_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawPixmap(0, 0, scaled_pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(tinted_pixmap.rect(), color)
        painter.end()
        
        return QIcon(tinted_pixmap)
    
    def update_theme(self, is_dark):
        """Update button icons and styles based on theme"""
        icon_color = QColor(255, 255, 255) if is_dark else QColor(0, 0, 0)
        
        # Update icons for all buttons
        for config in self.buttons_config:
            btn_id = config.get('id', '')
            icon_path = config.get('icon_path', '')
            if btn_id in self.buttons and icon_path:
                self.buttons[btn_id].setIcon(self._get_tinted_icon(icon_path, icon_color))
        
        # Theme-aware styling
        if is_dark:
            bg_hover = "rgba(255, 255, 255, 0.1)"
            border_color = "#555555"
        else:
            bg_hover = "rgba(0, 0, 0, 0.05)"
            border_color = "#cccccc"
        
        button_style = (
            f"QPushButton {{ padding: 6px; border-top-left-radius: 8px; border-bottom-left-radius: 8px; "
            f"border-top-right-radius: 0px; border-bottom-right-radius: 0px; "
            f"border: 1px solid {border_color}; border-right: none; background-color: transparent; }}"
            f"QPushButton:hover {{ background-color: {bg_hover}; }}"
            "QPushButton:checked { background-color: #2196F3; color: white; border-color: #1e88e5; }"
        )
        
        for btn in self.buttons.values():
            btn.setStyleSheet(button_style)
    
    def get_selection(self):
        """Get the currently selected button ID"""
        for btn_id, btn in self.buttons.items():
            if btn.isChecked():
                return btn_id
        return None
    
    def set_selection(self, btn_id):
        """Set the selected button by ID"""
        if btn_id in self.buttons:
            self.buttons[btn_id].setChecked(True)
    
    def set_button_visible(self, btn_id, visible):
        """Show or hide a specific button"""
        if btn_id in self.buttons:
            self.buttons[btn_id].setVisible(visible)

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
                min-height: 20px;
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
    """Custom QLineEdit for spinbox that intercepts Enter/Escape keys and handles suffix painting"""
    
    enterPressed = pyqtSignal()
    escapePressed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.suffix_text = ""
        self.suffix_color = None
    
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
        
    def paintEvent(self, event):
        """Paint the suffix text after the content if set"""
        super().paintEvent(event)
        
        if self.suffix_text and self.text():
            from PyQt6.QtGui import QPainter, QColor
            
            painter = QPainter(self)
            
            # Use specified color or default to grey
            color = self.suffix_color if self.suffix_color else QColor("#888888")
            painter.setPen(color)
            
            # Simple calculation for Left-aligned text
            fm = self.fontMetrics()
            text_width = fm.horizontalAdvance(self.text())
            
            # Get content rect allowing for internal margins
            cr = self.contentsRect()
             # Adjust x based on text_width plus a small padding
            x_pos = cr.left() + text_width + 3
            
            # Vertical centering logic for baseline
            # Using rect based drawing is safer for vertical alignment
            # But specific coordinate is fine
            y_pos = (self.height() + fm.ascent() - fm.descent()) // 2
            
            # Only draw if it vaguely fits
            if x_pos < self.width():
                 painter.drawText(x_pos, y_pos, self.suffix_text)
            
            painter.end()


class DragOverlay(QWidget):
    """Transparent overlay that captures mouse events for drag-to-change behavior"""
    
    def __init__(self, parent_spinbox_widget):
        super().__init__(parent_spinbox_widget)
        self.parent_widget = parent_spinbox_widget
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)  # Prevent blank background
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)  # Make truly transparent
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
        self.custom_line_edit.suffix_text = " MB" # Set the visual suffix
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
        self.drag_overlay.hide()  # Start hidden, will show in showEvent
        
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
        if self.isVisible():
            spinbox_geo = self.spinbox.geometry()
            self.drag_overlay.setGeometry(spinbox_geo)
            self.drag_overlay.show()
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
        
        # Update suffix color
        from PyQt6.QtGui import QColor
        suffix_color = QColor("#aaaaaa") if is_dark else QColor("#888888")
        self.custom_line_edit.suffix_color = suffix_color
        
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
        self.setMinimumHeight(24)
        self.setMaximumHeight(28)
        
        # Range settings
        self.min_value = 0.0
        self.max_value = 1.0
        self.start_value = 0.0
        self.end_value = 1.0
        
        # Handle settings
        self.handle_radius = 8
        self.active_handle = None  # None, 'start', or 'end'
        
        # Padding for handles only (no text labels)
        self.padding = 10  # Reduced - only need space for handle radius
        
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


class QSvgIconWidget(QWidget):
    """
    Custom SVG icon widget that renders SVG with consistent appearance.
    Renders SVG to a high-resolution pixmap and scales it to fit the widget.
    This ensures the icon looks consistent regardless of widget size.
    """
    def __init__(self, svg_path, stroke_width=5, stroke_color=None, parent=None):
        super().__init__(parent)
        self.svg_path = svg_path
        self.stroke_width = stroke_width
        self.stroke_color = stroke_color or "black"
        self.cached_pixmap = None
        self.last_size = None
        
        # Transparent background
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Pre-render the icon
        self._render_icon()
        
    def _render_icon(self):
        """Render SVG to a high-resolution pixmap"""
        from PyQt6.QtSvg import QSvgRenderer
        from PyQt6.QtGui import QPixmap, QPainter, QColor, QIcon
        from PyQt6.QtCore import QByteArray, QRectF
        import os
        
        try:
            svg_path = self.svg_path
            if not os.path.exists(svg_path):
                from client.utils.resource_path import get_resource_path
                svg_path = get_resource_path(svg_path)
            
            # First try: Load original SVG directly using QIcon (most reliable)
            icon = QIcon(svg_path)
            if not icon.isNull():
                # Render icon to pixmap at desired size
                render_size = 256
                self.cached_pixmap = icon.pixmap(render_size, render_size)
                
                # If we need to colorize, do it on the pixmap
                if self.stroke_color and self.stroke_color.lower() != "black":
                    self._colorize_pixmap()
                return
            
            # Fallback: Try QSvgRenderer directly
            renderer = QSvgRenderer(svg_path)
            if renderer.isValid():
                render_size = 256
                self.cached_pixmap = QPixmap(render_size, render_size)
                self.cached_pixmap.fill(QColor(0, 0, 0, 0))  # Transparent
                
                painter = QPainter(self.cached_pixmap)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                renderer.render(painter, QRectF(0, 0, render_size, render_size))
                painter.end()
                
                if self.stroke_color and self.stroke_color.lower() != "black":
                    self._colorize_pixmap()
                return
            
            print(f"Error: Could not load SVG: {svg_path}")
            
        except Exception as e:
            print(f"Error rendering SVG icon: {e}")
            import traceback
            traceback.print_exc()
    
    def _colorize_pixmap(self):
        """Colorize the cached pixmap to match stroke_color"""
        if not self.cached_pixmap:
            return
        
        from PyQt6.QtGui import QPainter, QColor
        from PyQt6.QtCore import Qt
        
        # Create a colored version by compositing
        color = QColor(self.stroke_color)
        
        # Use CompositionMode to tint the pixmap
        painter = QPainter(self.cached_pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(self.cached_pixmap.rect(), color)
        painter.end()
    
    def paintEvent(self, event):
        """Paint the cached pixmap scaled to widget size"""
        if not self.cached_pixmap:
            return
        
        from PyQt6.QtGui import QPainter
        from PyQt6.QtCore import QRectF
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # Scale pixmap to fit widget while maintaining aspect ratio
        widget_size = min(self.width(), self.height())
        target_rect = QRectF(
            (self.width() - widget_size) / 2,
            (self.height() - widget_size) / 2,
            widget_size,
            widget_size
        )
        
        painter.drawPixmap(target_rect.toRect(), self.cached_pixmap)
        painter.end()
    
    def update_color(self, color):
        """Update the icon color and re-render"""
        old_color = self.stroke_color
        self.stroke_color = color
        
        # Re-render the icon with new color
        self._render_icon()
        self.update()
    
    def sizeHint(self):
        """Provide default size hint"""
        from PyQt6.QtCore import QSize
        return QSize(64, 64)


class SquareButtonRow(QWidget):
    """
    Container that enforces square aspect ratio for buttons in a horizontal row.
    Button side length (S) equals container height (H): S=H.
    Buttons are distributed evenly across the horizontal space.
    Gap = (Width - (Count × Height)) / (Count + 1)
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.buttons = []
        
        # No layout manager - we manually position buttons in resizeEvent
        self.setMinimumHeight(48)
        self.setMaximumHeight(180)
        
        # Allow vertical expansion to fill available space
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
    def addButton(self, button):
        """Add a button to the row"""
        self.buttons.append(button)
        button.setParent(self)
        button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        button.show()
        # Trigger layout update when state changes to handle resizing
        button.toggled.connect(self._update_layout)

    def minimumSizeHint(self):
        """Return minimum size needed"""
        from PyQt6.QtCore import QSize
        if not self.buttons:
            return QSize(100, 40)
        
        # Minimum: 40px height, enough width for all buttons with small gaps
        min_size = 40
        num_buttons = len(self.buttons)
        min_gap = 4
        # Add a bit of buffer for expansion
        total_width = int((min_size * num_buttons + min_gap * (num_buttons + 1)) * 1.05)
        
        return QSize(max(0, min(total_width, 16777215)), min_size)

    def _update_layout(self):
        """Trigger layout update"""
        self._layout_buttons()
    
    def resizeEvent(self, event):
        """Position buttons as squares based on container height with even distribution"""
        super().resizeEvent(event)
        self._layout_buttons()

    def _layout_buttons(self):
        if not self.buttons:
            return
            
        # Get container dimensions
        container_width = max(0, self.width())
        container_height = max(1, self.height())
        num_buttons = len(self.buttons)
        
        if num_buttons == 0:
            return
        
        # Calculate availability
        min_gap = 4
        available_width_for_buttons = container_width - (min_gap * (num_buttons + 1))
        
        # Calculate base size. 
        # A checked button is 5% larger. To be safe, assume we need a bit more space.
        # Effective units = count + 0.05
        width_based_size = int(available_width_for_buttons / (num_buttons + 0.05)) if num_buttons > 0 else 48
        
        height_based_size = container_height
        
        # Base button size (unchecked)
        base_size = int(max(48, min(width_based_size, height_based_size, 180)))
        
        # Determine actual sizes
        sizes = []
        total_buttons_width = 0
        for btn in self.buttons:
            if btn.isChecked():
                s = int(base_size * 1.05)
            else:
                s = base_size
            sizes.append(s)
            total_buttons_width += s
            
        # Calc gap
        remaining_space = max(0, container_width - total_buttons_width)
        gap = remaining_space // (num_buttons + 1)
        gap = max(4, gap)
        
        # Position
        x_position = gap
        for i, button in enumerate(self.buttons):
            s = sizes[i]
            button.setFixedSize(s, s)
            # Center vertically
            button.move(x_position, (container_height - s) // 2)
            x_position += s + gap



class PresetButton(QPushButton):
    """
    Unified button for presets (Social Media & Aspect Ratios).
    Handles smart icon scaling and consistent styling.
    """
    def __init__(self, name, icon_path=None, parent=None):
        super().__init__("" if icon_path else name, parent)
        self.preset_name = name
        self.setCheckable(True)
        
        # Enable heightForWidth to keep it square while filling width
        from PyQt6.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(40, 40)
        
        if icon_path:
            from PyQt6.QtGui import QIcon
            self.setIcon(QIcon(icon_path))
        
        # Set intelligent tooltip
        if ":" in name:
            self.setToolTip(f"Set aspect ratio to {name}")
        else:
            self.setToolTip(f"Set settings for {name}")

    def resizeEvent(self, event):
        """Scale icon to fill button area smartly based on preset type"""
        super().resizeEvent(event)
        if not self.icon().isNull():
            from PyQt6.QtCore import QSize
            # Base size: 80% of button area
            side = int(min(self.width(), self.height()) * 0.8)
            
            name_lower = self.preset_name.lower()
            
            # Case 1: Wide Social Icons
            if name_lower in ["youtube", "behance"]:
                # Use approx 1.5:1 ratio for wide icons
                self.setIconSize(QSize(side, int(side * 0.65)))
                
            # Case 2: Aspect Ratio Icons
            elif ":" in self.preset_name:
                try:
                    w_r, h_r = map(int, self.preset_name.split(':'))
                    if w_r > h_r:
                        self.setIconSize(QSize(side, int(side * h_r / w_r)))
                    elif h_r > w_r:
                        self.setIconSize(QSize(int(side * w_r / h_r), side))
                    else:
                        self.setIconSize(QSize(side, side))
                except ValueError:
                    self.setIconSize(QSize(side, side))
                    
            # Case 3: Standard Square Icons
            else:
                self.setIconSize(QSize(side, side))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, w):
        return w

    def update_theme(self, is_dark):
        """Update styling based on theme"""
        if is_dark:
            bg_color = "#333333"
            border_color = "#444444"
            text_color = "white"
            hover_bg = "#404040"
        else:
            bg_color = "#f0f0f0"
            border_color = "#cccccc"
            text_color = "#333333"
            hover_bg = "#e0e0e0"
            
        # Store for paintEvent fallback
        self.custom_text_color = QColor(text_color)

        checked_bg = "#4CAF50"
        checked_border = "#43a047"

        style = f"""
            QPushButton {{
                padding: 0px;
                border-radius: 6px;
                border: 1px solid {border_color};
                background-color: {bg_color};
                color: {text_color};
                font-weight: 500;
            }}
            QPushButton:checked {{
                background-color: {checked_bg};
                border-color: {checked_border};
                color: white;
            }}
            QPushButton:hover:!checked {{
                background-color: {hover_bg};
            }}
        """
        self.setStyleSheet(style)
        
    def paintEvent(self, event):
        """Paint overlaid text if icon is present but hidden, or fallback"""
        super().paintEvent(event)
        
        # Logic: If we have a preset name, but no icon was set (text mode), or explicit overwrite needed
        if not self.text() and self.preset_name:
            # Only paint text overlay for Aspect Ratio presets (containing ":")
            # Social presets typically have distinct icons (logos) and don't need text overlay
            has_colon = ":" in self.preset_name
            if not has_colon:
                 return

            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Determine color
            if self.isChecked():
                color = QColor("white")
            elif hasattr(self, 'custom_text_color'):
                color = self.custom_text_color
            else:
                color = QColor("white") # Fallback
                
            painter.setPen(color)
            
            # Bold font
            font = painter.font() if painter.font() else self.font()
            font.setBold(True)
            font.setPointSize(11)
            painter.setFont(font)
            
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.preset_name)

# Alias for backward compatibility if needed temporarily (though we will replace usages)
SocialPresetButton = PresetButton
RatioPresetButton = PresetButton


class FormatButtonRow(GenericSegmentedControl):
    """
    A row of exclusive buttons to select a format.
    Mimics QComboBox API (currentText, setCurrentText, currentTextChanged)
    for easy drop-in replacement.
    Now uses Segmented Pill style.
    """
    currentTextChanged = pyqtSignal(str)
    
    def __init__(self, formats, parent=None):
        super().__init__(parent)
        self.formats = formats
        
        for fmt in formats:
            self.add_segment(fmt, fmt)
            
        if formats:
            self.set_selected(formats[0])
            
        self.selectionChanged.connect(self.currentTextChanged.emit)
        
    def currentText(self):
        """Get the text of the currently checked segment"""
        return self.get_selected() or ""
        
    def setCurrentText(self, text):
        """Set the currently checked segment by text"""
        self.set_selected(text)
        
    def update_theme(self, is_dark):
        """Update styling based on theme"""
        super().update_theme(is_dark)
        


class RotationButtonRow(GenericSegmentedControl):
    """
    Row of buttons for rotation selection (0°, 90°, 180°, 270°).
    Now uses Segmented Pill style.
    Mimics QComboBox API for compatibility.
    """
    currentTextChanged = pyqtSignal(str)
    
    # Mapping from display text to internal value (for compatibility with existing logic)
    ROTATION_MAP = {
        "0°": "No rotation",
        "90°": "90° clockwise",
        "180°": "180°",
        "270°": "270° clockwise"
    }
    
    REVERSE_MAP = {v: k for k, v in ROTATION_MAP.items()}
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        rotations = ["0°", "90°", "180°", "270°"]
        
        for rot in rotations:
            self.add_segment(rot, rot)
            
        # Select first by default (0° = No rotation)
        self.set_selected("0°")
        
        self.selectionChanged.connect(lambda r: self.currentTextChanged.emit(self.ROTATION_MAP[r]))
            
    def currentText(self):
        """Get the internal value of the currently checked segment"""
        rot = self.get_selected() or "0°"
        return self.ROTATION_MAP.get(rot, "No rotation")
        
    def setCurrentText(self, text):
        """Set the currently checked segment by internal value"""
        # Map from internal value to display text
        display = self.REVERSE_MAP.get(text, "0°")
        self.set_selected(display)
        
    def update_theme(self, is_dark):
        """Update styling based on theme"""
        super().update_theme(is_dark)
        



from client.utils.font_manager import AppFonts, FONT_FAMILY

class AppTooltip(QLabel):
    """
    Unified, theme-aware tooltip for the entire application.
    
    Features:
    - Dark/Light mode support with automatic theme detection
    - Fade-in/out animations
    - Configurable show delay (mimics native tooltip behavior)
    - Auto-positioning above or below target widget
    - Consistent styling across the app
    
    Usage:
        # Option 1: Direct instantiation
        tooltip = AppTooltip()
        tooltip.show_for_widget(widget, "Tooltip text")
        
        # Option 2: Use helper function (recommended)
        install_app_tooltip(widget, "Tooltip text")
    """
    
    # Singleton instance for shared tooltip
    _instance = None
    
    @classmethod
    def instance(cls):
        """Get or create the shared tooltip instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        # Ensure no default margins interfere with stylesheet padding
        self.setMargin(0)
        self.setContentsMargins(0, 0, 0, 0)
        self.setWordWrap(True)  # Allow text wrapping for long tooltips
        
        # Track current theme
        self._is_dark = True
        self._apply_theme_style()
        
        # Opacity animation for fade-in/out
        self.setWindowOpacity(0.0)
        self._fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self._fade_anim.setDuration(150)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        
        # Show delay timer (500ms like native tooltips)
        self._show_delay_timer = QTimer(self)
        self._show_delay_timer.setSingleShot(True)
        self._show_delay_timer.timeout.connect(self._do_show)
        
        # Auto-hide timer (5 seconds)
        self._auto_hide_timer = QTimer(self)
        self._auto_hide_timer.setSingleShot(True)
        self._auto_hide_timer.timeout.connect(self.hide_tooltip)
        
        # Pending show data
        self._pending_text = ""
        self._pending_pos = None
        self._target_widget = None
        
    # Explicit padding constants (pixels)
    PADDING_H = 14  # Horizontal padding (left + right each)
    PADDING_V = 10  # Vertical padding (top + bottom each)
    
    def _apply_theme_style(self):
        """Apply styling based on current theme."""
        from client.utils.theme_utils import is_dark_mode
        self._is_dark = is_dark_mode()
        
        if self._is_dark:
            bg_color = "#1E1E1E"
            border_color = "#4CAF50"
            text_color = "#FFFFFF"
        else:
            bg_color = "#E0E0E0"
            border_color = "#4CAF50"
            text_color = "#000000"
        
        # Explicit padding in stylesheet for consistent spacing
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                color: {text_color};
                border-radius: 6px;
                font-family: '{FONT_FAMILY}', sans-serif;
                font-size: 14px;
                font-weight: 500;
                padding: {self.PADDING_V}px {self.PADDING_H}px;
            }}
        """)
        
    def update_theme(self, is_dark: bool):
        """Update tooltip styling for theme change."""
        self._is_dark = is_dark
        self._apply_theme_style()
        
    def show_message(self, text: str, target_pos_global: QPoint, delay_ms: int = 0):
        """
        Show tooltip centered above target_pos_global.
        
        Args:
            text: Tooltip text (supports newlines)
            target_pos_global: Global position (typically top-center of target widget)
            delay_ms: Delay before showing (0 for immediate)
        """
        # =====================================================
        # CRITICAL: Immediately reset before showing new tooltip
        # This fixes issues when rapidly switching between widgets
        # =====================================================
        
        # 1. Stop ALL timers immediately
        self._show_delay_timer.stop()
        self._auto_hide_timer.stop()
        
        # 2. Stop animation and disconnect signals
        self._fade_anim.stop()
        try:
            self._fade_anim.finished.disconnect(self._on_fade_out_finished)
        except TypeError:
            pass
        
        # 3. If currently visible, force immediate hide and full reset
        if self.isVisible() or self.windowOpacity() > 0:
            self.hide()
            self.setWindowOpacity(0.0)
            self.move(-10000, -10000)
            
            # Reset ALL layout properties
            self.setMargin(0)
            self.setContentsMargins(0, 0, 0, 0)
            self.setStyleSheet("")
            self.setMinimumSize(0, 0)
            self.setMaximumSize(16777215, 16777215)
            self.resize(0, 0)
            self.setText("")
            self.updateGeometry()
            
            # Process events to ensure reset takes effect
            QApplication.processEvents()
        
        # Store new pending data
        self._pending_text = text
        self._pending_pos = target_pos_global
        
        if delay_ms > 0:
            self._show_delay_timer.start(delay_ms)
        else:
            self._do_show()
            
    def show_for_widget(self, widget: QWidget, text: str, delay_ms: int = 500):
        """
        Show tooltip for a widget with automatic positioning.
        
        Args:
            widget: Target widget to show tooltip for
            text: Tooltip text
            delay_ms: Delay before showing (default 500ms like native)
        """
        self._target_widget = widget
        
        # Calculate position: center-top of widget
        global_pos = widget.mapToGlobal(QPoint(widget.width() // 2, 0))
        self.show_message(text, global_pos, delay_ms)
        
    def _do_show(self):
        """Actually display the tooltip after delay."""
        if not self._pending_text or not self._pending_pos:
            return
        
        # =====================================================
        # CRITICAL: Complete reset cycle before showing new tooltip
        # When rapidly switching, the widget may be animating or 
        # have stale geometry. We must fully reset BEFORE configuring.
        # =====================================================
        
        # 1. Stop ALL timers that could interfere
        self._auto_hide_timer.stop()
        
        # 2. Stop animation and disconnect ALL signals
        self._fade_anim.stop()
        try:
            self._fade_anim.finished.disconnect(self._on_fade_out_finished)
        except TypeError:
            pass  # Not connected
        
        # 3. Force immediate hide (not animated)
        self.hide()
        
        # 4. Process events to ensure hide takes effect before we reconfigure
        QApplication.processEvents()
        
        # 5. Reset opacity to 0 (will fade in fresh)
        self.setWindowOpacity(0.0)
        
        # 6. Move off-screen to prevent flash at old position
        self.move(-10000, -10000)
        
        # 7. Reset ALL margin/padding properties to defaults
        self.setMargin(0)
        self.setContentsMargins(0, 0, 0, 0)
        
        # 8. Clear stylesheet completely before reapplying
        self.setStyleSheet("")
        
        # 9. Clear ALL size constraints and geometry
        self.setMinimumSize(0, 0)
        self.setMaximumSize(16777215, 16777215)  # QWIDGETSIZE_MAX
        self.resize(0, 0)  # Clear to absolute minimum
        
        # 10. Clear text to force fresh layout calculation
        self.setText("")
        
        # 11. Force geometry update
        self.updateGeometry()
        
        # =====================================================
        # Now configure and show the new tooltip
        # =====================================================
        
        # Apply theme styling (includes padding via stylesheet)
        self._apply_theme_style()
        
        # Set text (no manual space padding - stylesheet handles it)
        self.setText(self._pending_text)
        
        # Center text alignment
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Calculate size using QFontMetrics for precise control
        from PyQt6.QtGui import QFontMetrics, QFont
        
        font = QFont(FONT_FAMILY, 14)
        font.setWeight(QFont.Weight.Medium)
        fm = QFontMetrics(font)
        
        # Calculate text bounding rect (supports multi-line)
        max_width = 350
        text_rect = fm.boundingRect(0, 0, max_width, 0, 
                                    Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignLeft,
                                    self._pending_text)
        
        # Calculate total size: text + padding (both sides) + border
        total_width = text_rect.width() + (self.PADDING_H * 2) + 2
        total_height = text_rect.height() + (self.PADDING_V * 2) + 2
        
        # Apply fixed size
        self.setFixedSize(total_width, total_height)
        
        # Calculate position
        x = self._pending_pos.x() - (total_width // 2)
        y = self._pending_pos.y() - total_height - 8
        
        # Screen boundary checks
        screen = QApplication.primaryScreen()
        if screen:
            screen_rect = screen.availableGeometry()
            
            if x < screen_rect.left():
                x = screen_rect.left() + 4
            elif x + total_width > screen_rect.right():
                x = screen_rect.right() - total_width - 4
                
            if y < screen_rect.top():
                if self._target_widget:
                    y = self._pending_pos.y() + self._target_widget.height() + 8
                else:
                    y = self._pending_pos.y() + 24
        
        # Move and show
        self.move(x, y)
        self.show()
        
        # Fade in animation
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(0.97)
        self._fade_anim.start()
        
        # Auto-hide timer
        self._auto_hide_timer.start(5000)
        
    def hide_tooltip(self):
        """Hide the tooltip with fade-out animation."""
        self._show_delay_timer.stop()
        self._auto_hide_timer.stop()
        
        if self.isVisible():
            self._fade_anim.stop()
            self._fade_anim.setStartValue(self.windowOpacity())
            self._fade_anim.setEndValue(0.0)
            self._fade_anim.finished.connect(self._on_fade_out_finished)
            self._fade_anim.start()
        else:
            self.hide()
            
    def _on_fade_out_finished(self):
        """Called when fade-out animation completes."""
        try:
            self._fade_anim.finished.disconnect(self._on_fade_out_finished)
        except:
            pass
        self.hide()
        self.setWindowOpacity(0.0)
        
    def cancel_pending(self):
        """Cancel any pending tooltip show."""
        self._show_delay_timer.stop()
        self._pending_text = ""
        self._pending_pos = None
        self._target_widget = None


class TooltipEventFilter(QObject):
    """
    Event filter that intercepts hover events to show native QToolTip.
    Uses Qt's built-in tooltip system for reliable behavior.
    """
    
    def __init__(self, target_widget: QWidget, tooltip_text: str = None):
        super().__init__(target_widget)
        self._target = target_widget
        self._custom_text = tooltip_text
        # Set native tooltip on the widget
        if tooltip_text:
            self._target.setToolTip(tooltip_text)
        self._target.installEventFilter(self)
        
    def eventFilter(self, obj, event):
        if obj != self._target:
            return False
            
        event_type = event.type()
        
        if event_type == 10:  # QEvent.Type.Enter
            text = self._custom_text or self._target.toolTip()
            if text:
                # Use native QToolTip - much more reliable
                from PyQt6.QtWidgets import QToolTip
                from PyQt6.QtCore import QPoint
                
                # Position above widget center
                global_pos = self._target.mapToGlobal(
                    QPoint(self._target.width() // 2, -8)
                )
                QToolTip.showText(global_pos, text, self._target)
                
        elif event_type == 11:  # QEvent.Type.Leave
            from PyQt6.QtWidgets import QToolTip
            QToolTip.hideText()
            
        return False


def install_app_tooltip(widget: QWidget, text: str = None) -> TooltipEventFilter:
    """
    Install tooltip on a widget using Qt's native QToolTip system.
    
    If text is provided, it overrides any existing toolTip.
    If text is None, the widget's existing toolTip() will be used.
    
    Args:
        widget: The widget to add tooltip to
        text: Optional tooltip text (uses widget.toolTip() if None)
        
    Returns:
        The event filter instance (keep reference if you need to modify)
        
    Usage:
        install_app_tooltip(my_button, "Click to submit")
        # or if already has setToolTip:
        my_button.setToolTip("Click to submit")
        install_app_tooltip(my_button)
    """
    return TooltipEventFilter(widget, text)


def apply_tooltip_style(is_dark: bool = True):
    """
    Apply global QToolTip styling to match app theme.
    Call this when initializing the app or changing themes.
    
    Args:
        is_dark: Whether dark mode is active
    """
    from client.utils.font_manager import FONT_FAMILY
    
    if is_dark:
        bg_color = "#1E1E1E"
        border_color = "#808080"  # Greyish border
        text_color = "#FFFFFF"
    else:
        bg_color = "#E0E0E0"
        border_color = "#808080"  # Greyish border
        text_color = "#000000"
    
    tooltip_style = f"""
        QToolTip {{
            background-color: {bg_color};
            border: 1px solid {border_color};
            color: {text_color};
            border-radius: 0px;
            font-family: '{FONT_FAMILY}', sans-serif;
            font-size: 14px;
            font-weight: 500;
            padding: 6px 10px;
            max-width: 300px;
        }}
    """
    
    app = QApplication.instance()
    if app:
        current_style = app.styleSheet() or ""
        # Remove old QToolTip style if exists
        import re
        current_style = re.sub(r'QToolTip\s*\{[^}]*\}', '', current_style)
        app.setStyleSheet(current_style + tooltip_style)


# Alias for backwards compatibility
ModernTooltip = AppTooltip


class LoopFormatSelector(QWidget):
    """
    Conditional format selector for Loop tab.
    - Two primary segments: GIF and WebM
    - When WebM is selected, shows a segmented control for AV1/VP9
    - Uses GenericSegmentedControl for both rows
    """
    formatChanged = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)
        
        # Row 1: Primary format segments (GIF / WebM)
        self.primary_control = GenericSegmentedControl()
        self.webm_btn = self.primary_control.add_segment("webm", "WebM")
        self.gif_btn = self.primary_control.add_segment("gif", "GIF", is_checked=True)
        
        main_layout.addWidget(self.primary_control)
        
        # Row 2: Codec selector (only visible for WebM)
        self.codec_row = QWidget()
        codec_layout = QHBoxLayout(self.codec_row)
        codec_layout.setContentsMargins(0, 4, 0, 0)
        codec_layout.setSpacing(0)
        
        self.codec_control = GenericSegmentedControl()
        self.av1_btn = self.codec_control.add_segment("av1", "💎 AV1", is_checked=True)
        self.vp9_btn = self.codec_control.add_segment("vp9", "⚡ VP9")
        
        codec_layout.addWidget(self.codec_control)
        codec_layout.addStretch()
        main_layout.addWidget(self.codec_row)
        
        # Tooltip setup
        install_app_tooltip(self.av1_btn, "Smaller file size. Slower encoding time.\nBest for performance.")
        install_app_tooltip(self.vp9_btn, "Bigger file size. Faster encoding.")
        
        # Set defaults
        self.codec_row.setVisible(False)
        
        # Connect signals
        self.primary_control.selectionChanged.connect(self._on_primary_changed)
        self.codec_control.selectionChanged.connect(self._on_codec_changed)
        
        from client.utils.theme_utils import is_dark_mode
        self.update_theme(is_dark_mode())
        
    def _on_primary_changed(self, seg_id):
        """Handle primary format change"""
        self.codec_row.setVisible(seg_id == "webm")
        self._emit_format()
        
    def _on_codec_changed(self, seg_id):
        """Handle codec change"""
        self._emit_format()
            
    def _emit_format(self):
        """Emit the current format string"""
        self.formatChanged.emit(self.currentText())
            
    def currentText(self):
        """Get the current format string"""
        if self.primary_control.get_selected() == "gif":
            return "GIF"
        else:
            codec = "AV1" if self.codec_control.get_selected() == "av1" else "VP9"
            return f"WebM ({codec})"
            
    def setCurrentText(self, text):
        """Set the current format"""
        if text == "GIF":
            self.primary_control.set_selected("gif")
        elif "WebM" in text:
            self.primary_control.set_selected("webm")
            if "VP9" in text:
                self.codec_control.set_selected("vp9")
            else:
                self.codec_control.set_selected("av1")
                
    def update_theme(self, is_dark):
        """Update styling based on theme"""
        self.primary_control.update_theme(is_dark)
        self.codec_control.update_theme(is_dark)
            
    def currentText(self):
        """Get the current format string (compatibility with FormatButtonRow)"""
        if self.gif_btn.isChecked():
            return "GIF"
        else:
            codec = "AV1" if self.av1_btn.isChecked() else "VP9"
            return f"WebM ({codec})"
            
    def setCurrentText(self, text):
        """Set the current format (compatibility)"""
        if text == "GIF":
            self.gif_btn.setChecked(True)
        elif "WebM" in text:
            self.webm_btn.setChecked(True)
            if "VP9" in text:
                self.vp9_btn.setChecked(True)
            else:
                self.av1_btn.setChecked(True)
                
    def update_theme(self, is_dark):
        """Update styling based on theme"""
        if is_dark:
            bg_color = "transparent"
            border_color = "#555555"
            text_color = "#eeeeee"
            hover_bg = "rgba(255, 255, 255, 0.1)"
        else:
            bg_color = "transparent"
            border_color = "#cccccc"
            text_color = "#333333"
            hover_bg = "rgba(0, 0, 0, 0.05)"
            
        # Primary buttons style (larger)
        primary_style = f"""
            QPushButton {{
                padding: 10px 20px;
                border-radius: 8px;
                border: 2px solid {border_color};
                background-color: {bg_color};
                color: {text_color};
                font-weight: 600;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background-color: {hover_bg};
            }}
            QPushButton:checked {{
                background-color: #4CAF50;
                border-color: #43a047;
                color: white;
                font-weight: bold;
            }}
        """
        self.gif_btn.setStyleSheet(primary_style)
        self.webm_btn.setStyleSheet(primary_style)
        
        # Codec buttons style (smaller, segmented look)
        codec_style = f"""
            QPushButton {{
                padding: 8px 16px;
                border-radius: 4px;
                border: 1px solid {border_color};
                background-color: {bg_color};
                color: {text_color};
                font-weight: 500;
                font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: {hover_bg};
            }}
            QPushButton:checked {{
                background-color: #2196F3;
                border-color: #1976D2;
                color: white;
                font-weight: bold;
            }}
        """
        self.av1_btn.setStyleSheet(codec_style)
        self.vp9_btn.setStyleSheet(codec_style)

class HardwareAwareCodecButton(QPushButton):
    """
    Checkable button for codec selection with hardware acceleration visual effects.
    Replaces circuit trace with internal glow on hover.
    Now optimized for Segmented Controls.
    """
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        # Fixed size policy to match other segmented buttons
        self.setMinimumHeight(40)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # GPU state
        self._gpu_available = False
        self._is_hovered = False
        
        # Glow Animation properties
        self._glow_opacity = 0.0
        self._glow_direction = 1
        self._glow_timer = QTimer(self)
        self._glow_timer.timeout.connect(self._update_glow)
        self._glow_timer.setInterval(33) # ~30 FPS
        
    def set_gpu_available(self, available: bool):
        self._gpu_available = available
        self.update()
        
    def enterEvent(self, event):
        self._is_hovered = True
        if self._gpu_available:
            self._glow_timer.start()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self._is_hovered = False
        self._glow_timer.stop()
        self._glow_opacity = 0.0
        self.update()
        super().leaveEvent(event)
        
    def _update_glow(self):
        """Pulse the internal glow opacity"""
        # Pulse between 0.05 and 0.25 opacity
        step = 0.015
        self._glow_opacity += step * self._glow_direction
        
        if self._glow_opacity >= 0.25:
            self._glow_opacity = 0.25
            self._glow_direction = -1
        elif self._glow_opacity <= 0.05:
            self._glow_opacity = 0.05
            self._glow_direction = 1
        self.update()
        
    def paintEvent(self, event):
        # Let default painting happen (background, border, text)
        super().paintEvent(event)
        
        if self._gpu_available:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Always draw bolt icon if GPU available
            self._draw_bolt_icon(painter)
            
            # Draw internal glow only on hover
            if self._is_hovered:
                self._draw_internal_glow(painter)
                
            painter.end()
            
    def _draw_bolt_icon(self, painter):
        # Position in top-right corner
        icon_size = 8
        x = self.width() - icon_size - 6
        y = 6
        
        painter.setPen(Qt.PenStyle.NoPen)
        # Cyan if checked or hovered, dimmer turquoise if not
        color = QColor("#00F3FF") if self.isChecked() or self._is_hovered else QColor("#00AAAA")
        if not self.isChecked() and not self._is_hovered:
             color.setAlpha(180)
             
        painter.setBrush(QBrush(color))
        
        # Simple bolt polygon
        bolt = [
            QPoint(x + 5, y),
            QPoint(x + 1, y + 4),
            QPoint(x + 4, y + 4),
            QPoint(x + 3, y + 8),
            QPoint(x + 7, y + 3),
            QPoint(x + 4, y + 3),
        ]
        painter.drawPolygon(bolt)

    def _draw_internal_glow(self, painter):
        """Draw a pulsing internal glow"""
        color = QColor("#00F3FF")
        color.setAlphaF(self._glow_opacity)
        
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Draw rounded rect slightly inside border
        # Assuming 8px border radius for button, let's use 6px for glow
        rect = self.rect().adjusted(2, 2, -2, -2)
        painter.drawRoundedRect(rect, 6, 6)


class VideoCodecSelector(GenericSegmentedControl):
    """
    Selector for video codecs (H.264, H.265, AV1) with hardware acceleration indicators.
    Now uses Segmented Pill style.
    """
    codecChanged = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # We use HardwareAwareCodecButton as the segment button class
        self.btn_h264 = self.add_segment("h264", "H.264", is_checked=True, button_class=HardwareAwareCodecButton)
        self.btn_h265 = self.add_segment("h265", "H.265", button_class=HardwareAwareCodecButton)
        self.btn_av1 = self.add_segment("av1", "AV1", button_class=HardwareAwareCodecButton)
        
        self.selectionChanged.connect(lambda: self.codecChanged.emit(self.currentText()))

            
    def currentText(self):
        """Get the current format string for compatibility"""
        sel = self.get_selected()
        if sel == "h264": return "MP4 (H.264)"
        if sel == "h265": return "MP4 (H.265)"
        if sel == "av1": return "MP4 (AV1)"
        return "MP4 (H.264)"
        
    def setCurrentText(self, text):
        """Set the current format for compatibility"""
        if "H.264" in text: self.set_selected("h264")
        elif "H.265" in text or "HEVC" in text: self.set_selected("h265")
        elif "AV1" in text: self.set_selected("av1")
        
    def update_gpu_status(self, available_codecs):
        """Update buttons based on GPU availability"""
        self.btn_h264.set_gpu_available('h264' in available_codecs)
        self.btn_h265.set_gpu_available('hevc' in available_codecs)
        self.btn_av1.set_gpu_available('av1' in available_codecs)

    def update_theme(self, is_dark):
        """Update styling based on theme"""
        super().update_theme(is_dark)





class MorphingButton(QPushButton):
    """
    Button that morphs between icon-only and expanded menu.
    """
    # Signals
    toggled_state = pyqtSignal(bool)
    expanded = pyqtSignal(bool)
    styleChanged = pyqtSignal(bool)  # Emitted when solid/ghost style changes
    itemClicked = pyqtSignal(object)  # Emits item ID
    
    # Constants
    COLLAPSED_SIZE = 48
    EXPAND_DELAY_MS = 200
    ANIMATION_DURATION = 400  # Luxurious weighted motion: 650ms
    EXPANDED_WIDTH = 200
    STAGGER_DELAY = 50 # ms between items
    
    # Debug flag for alignment visualization
    DEBUG_ALIGNMENT = False
    
    # Expansion directions (currently supports LEFT expansion as per spec)
    LEFT = 'left'
    
    def __init__(self, main_icon_path=None, parent=None):
        super().__init__(parent)
        
        # State
        self._is_expanded = False
        self._is_hovered = False
        self._is_solid_style = False # False = Ghost, True = Solid
        self._active_item_id = None
        self._items = [] # List of item widgets
        self._item_animations = [] # Keep animations alive to prevent GC
        self._main_icon_path = main_icon_path
        self._is_dark = True
        self._current_pixmap = None
        self._current_icon = None
        self._current_icon_grey = None  # Grey-tinted icon for inactive state
        
        # UI Setup
        self._setup_ui()
        
        # Timers
        self._hover_timer = QTimer(self)
        self._hover_timer.setSingleShot(True)
        self._hover_timer.setInterval(self.EXPAND_DELAY_MS)
        self._hover_timer.timeout.connect(self._expand)
        
        self._collapse_timer = QTimer(self)
        self._collapse_timer.setSingleShot(True)
        self._collapse_timer.setInterval(100)
        self._collapse_timer.timeout.connect(self._collapse)
        
        self._flash_timer = QTimer(self)
        self._flash_timer.setSingleShot(True)
        self._flash_timer.setInterval(150)
        self._flash_timer.timeout.connect(self._reset_flash)
        self._is_flashing = False

        # Base Styling
        self.setFixedHeight(self.COLLAPSED_SIZE)
        self.setMinimumWidth(self.COLLAPSED_SIZE)
        self.setMaximumWidth(self.COLLAPSED_SIZE)
        
        # Weighted Motion with Delicate Spring: 650ms with subtle overshoot
        self._width_anim = QPropertyAnimation(self, b"animWidth")
        self._width_anim.setDuration(self.ANIMATION_DURATION)
        
        # OutBack easing: Smooth deceleration with gentle spring overshoot
        # Amplitude controls the spring intensity (lower = more subtle)
        easing = QEasingCurve(QEasingCurve.Type.OutBack)
        easing.setOvershoot(.8)  # Delicate spring effect (default is 1.70158)
        self._width_anim.setEasingCurve(easing)
        
        self._update_main_icon()

    @pyqtProperty(int)
    def animWidth(self):
        return self.width()

    @animWidth.setter
    def animWidth(self, w):
        self.setFixedWidth(w)
        self.update()
        
    def _setup_ui(self):
        # Menu Container
        self._menu_container = QWidget(self)
        self._menu_container.setVisible(False)
        self._menu_layout = QHBoxLayout(self._menu_container)
        self._menu_layout.setContentsMargins(8, 0, 48, 0) # Right margin to avoid overlap with icon pos
        self._menu_layout.setSpacing(8)
        
        self._menu_container.setParent(self)
        self._icon_opacity_val = 1.0
        
    @pyqtProperty(float)
    def iconOpacity(self):
        return self._icon_opacity_val

    @iconOpacity.setter
    def iconOpacity(self, val):
        self._icon_opacity_val = val
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        curr_width = self.width()
        curr_height = self.height()
        radius = curr_height / 2
        
        # Background color
        bg_color = QColor("#00AA00") if self._is_solid_style else QColor(255, 255, 255, 12)
        
        # Border
        border_color = QColor(255, 255, 255, 25)
        if self._is_flashing:
            border_color = QColor(255, 255, 255, 255)
        elif not self._is_solid_style:
            border_color = QColor(255, 255, 255, 75)
            
        painter.setPen(QPen(border_color, 1.5 if self._is_flashing else 1))
        painter.setBrush(QBrush(bg_color))
        
        # Use integer coordinates to be absolutely safe with PyQt6 overloads.
        # This fixes the TypeError: argument 1 has unexpected type 'float'
        # Fix clipping: inset by 1px so border stroke (width 1-1.5) is inside bounds
        painter.drawRoundedRect(1, 1, int(curr_width)-2, int(curr_height)-2, int(radius), int(radius))

        # DEBUG: Draw red dot at center to verify alignment
        if self.DEBUG_ALIGNMENT:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("red"))
            cx = int(curr_width / 2)
            cy = int(curr_height / 2)
            # Draw ellipse centered on (cx, cy) - need to offset by radius
            painter.drawEllipse(cx - 3, cy - 3, 6, 6)
        
        
        # Draw Main Icon using QIcon.paint() for sharp, centered rendering
        if self._current_icon and not self._current_icon.isNull() and self._icon_opacity_val > 0:
            painter.setOpacity(self._icon_opacity_val)
            
            # Calculate icon area - anchored to right when expanded
            icon_x = 0
            if self._is_expanded or self.width() > self.COLLAPSED_SIZE:
                icon_x = self.width() - self.COLLAPSED_SIZE
            
            # The target rect for the icon - matches the visible circle area (1px border inset)
            # The circle is drawn at (1,1) with size (COLLAPSED_SIZE-2, COLLAPSED_SIZE-2)
            # so we center the icon within that same visible area
            target_rect = QRect(icon_x + 1, 1, self.COLLAPSED_SIZE - 2, self.COLLAPSED_SIZE - 2)
            
            # Calculate icon size as 66% of button
            icon_size = int(self.COLLAPSED_SIZE * 0.66)
            if icon_size % 2 == 1:
                icon_size += 1
            
            # Center the icon rect within target_rect
            icon_rect = QRect(
                target_rect.x() + (target_rect.width() - icon_size) // 2,
                target_rect.y() + (target_rect.height() - icon_size) // 2,
                icon_size,
                icon_size
            )
            
            # DEBUG: Draw semi-transparent blue background for icon area
            if self.DEBUG_ALIGNMENT:
                painter.setBrush(QColor(0, 0, 255, 150))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRect(icon_rect)
            
            # Draw icon using pixmap at explicit coordinates for perfect centering
            # ALWAYS use original SVG-based icon to get pixmap (preserves proper scaling)
            # Apply grey tint at paint time if in ghost/inactive state
            
            apply_grey_tint = not self._is_solid_style
            
            # Get pixmap from ORIGINAL icon (not the pre-created grey one)
            pixmap = self._current_icon.pixmap(icon_size, icon_size)
            if not pixmap.isNull():
                # Apply grey tinting at paint time if needed
                if apply_grey_tint:
                    # Create a grey-tinted copy of the pixmap
                    # CRITICAL: Preserve devicePixelRatio for proper DPI scaling
                    grey_pixmap = QPixmap(pixmap.size())
                    grey_pixmap.setDevicePixelRatio(pixmap.devicePixelRatio())
                    grey_pixmap.fill(Qt.GlobalColor.transparent)
                    tint_painter = QPainter(grey_pixmap)
                    tint_painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                    tint_painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
                    tint_painter.drawPixmap(0, 0, pixmap)
                    tint_painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
                    tint_painter.fillRect(grey_pixmap.rect(), QColor(136, 136, 136))
                    tint_painter.end()
                    pixmap = grey_pixmap
                
                # Draw pixmap scaled to icon_rect - this handles DPI scaling properly
                # The pixmap may be larger due to devicePixelRatio, but drawPixmap with QRect scales it
                painter.drawPixmap(icon_rect, pixmap)
            
            painter.setOpacity(1.0)
            
    def set_main_icon(self, icon_path):
        self._main_icon_path = icon_path
        self._update_main_icon()
        
    def _update_main_icon(self):
        if self._main_icon_path:
            abs_path = get_resource_path(self._main_icon_path)
            if os.path.exists(abs_path):
                # Store the icon for direct painting (same method as menu buttons)
                self._current_icon = QIcon(abs_path)
                self._current_pixmap = None  # Clear pixmap, we'll use icon directly
                
                # Create grey-tinted icon for inactive/ghost state
                icon_size = int(self.COLLAPSED_SIZE * 0.66)
                if icon_size % 2 == 1:
                    icon_size += 1
                pixmap = self._current_icon.pixmap(icon_size, icon_size)
                if not pixmap.isNull():
                    grey_pixmap = QPixmap(pixmap.size())
                    grey_pixmap.fill(Qt.GlobalColor.transparent)
                    painter = QPainter(grey_pixmap)
                    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
                    painter.drawPixmap(0, 0, pixmap)
                    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
                    # Use a medium grey (#888888) for inactive state
                    painter.fillRect(grey_pixmap.rect(), QColor(136, 136, 136))
                    painter.end()
                    self._current_icon_grey = QIcon(grey_pixmap)
                else:
                    self._current_icon_grey = None
                    
                self.update()
            
    def add_menu_item(self, item_id, icon_path, tooltip=""):
        """Add an icon-based item to the expansion menu"""
        btn = QPushButton()
        btn.setFixedSize(32, 32)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Icon
        if icon_path:
            abs_path = get_resource_path(icon_path)
            if os.path.exists(abs_path):
                btn.setIcon(QIcon(abs_path))
                btn.setIconSize(QSize(20, 20))
        
        # Styling for icon buttons
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.2);
            }}
        """)
        
        # IMPORTANT: Use default arg to capture item_id by VALUE, not reference
        # This fixes the closure bug where all buttons would emit the last item_id
        btn.clicked.connect(lambda checked=False, iid=item_id: self._on_item_clicked(iid))
        self._menu_layout.addWidget(btn)
        self._items.append(btn)
        
        op = QGraphicsOpacityEffect(btn)
        btn.setGraphicsEffect(op)
        op.setOpacity(0)
        
    def set_style_solid(self, is_solid):
        if self._is_solid_style != is_solid:
            self._is_solid_style = is_solid
            self._update_main_icon()
            self.update()
            self.styleChanged.emit(is_solid)
            
    @property
    def is_solid(self):
        return self._is_solid_style
        
    def flash_border(self):
        self._is_flashing = True
        self.update()
        self._flash_timer.start()
        
    def _reset_flash(self):
        self._is_flashing = False
        self.update()

    def update_theme(self, is_dark):
        self._is_dark = is_dark
        self._update_main_icon()
        self.update()

    def _on_item_clicked(self, item_id):
        type_map = {0: "IMAGE", 1: "VIDEO", 2: "LOOP"}
        print(f"[DEBUG_INTERNAL] MorphingButton item clicked. ID={item_id} ({type_map.get(item_id, 'UNKNOWN')})")
        self._active_item_id = item_id
        self.itemClicked.emit(item_id)
        self._collapse()
        self.flash_border()
        
    def enterEvent(self, event):
        super().enterEvent(event)
        self._is_hovered = True
        self._collapse_timer.stop()
        if not self._is_expanded:
            self._hover_timer.start()
            
    def leaveEvent(self, event):
        super().leaveEvent(event)
        self._is_hovered = False
        self._hover_timer.stop()
        if self._is_expanded:
            self._collapse_timer.start()
            
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Icon positioning handled in paintEvent now
        
        self._menu_container.resize(self.width(), self.height())
            
    def _expand(self):
        if self._is_expanded: return
        self._is_expanded = True
        self.raise_() # Ensure button is on top of siblings when expanding
        
        # 1. Expand Width
        menu_width = self._menu_layout.sizeHint().width()
        target_width = max(160, menu_width + 48) # 48 space for the status icon at the end
        
        self._width_anim.setStartValue(self.COLLAPSED_SIZE)
        self._width_anim.setEndValue(target_width)
        self._width_anim.start()
        
        # 2. Main Icon Shift (Fade slightly or just stay at right)
        self.icon_anim_op = QPropertyAnimation(self, b"iconOpacity")
        self.icon_anim_op.setDuration(300)
        self.icon_anim_op.setStartValue(1.0)
        self.icon_anim_op.setEndValue(0.4) # Keep it visible but faded
        self.icon_anim_op.start()
        
        # 3. Menu Items In
        self._menu_container.setVisible(True)
        self._item_animations.clear()  # Clear previous animations
        for i, btn in enumerate(self._items):
            anim = QPropertyAnimation(btn.graphicsEffect(), b"opacity")
            anim.setDuration(250)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            self._item_animations.append(anim)  # Keep reference to prevent GC
            QTimer.singleShot(i * self.STAGGER_DELAY, anim.start)
            
        self.expanded.emit(True)
        
    def _collapse(self):
        if not self._is_expanded: return
        if self._is_hovered: return
        self._is_expanded = False
        
        # 1. Collapse Width
        self._width_anim.setStartValue(self.width())
        self._width_anim.setEndValue(self.COLLAPSED_SIZE)
        self._width_anim.finished.connect(self._on_collapse_finished)
        self._width_anim.start()
        
        # 2. Main Icon Back
        self.icon_anim_op.setStartValue(0.4)
        self.icon_anim_op.setEndValue(1.0)
        self.icon_anim_op.start()
        
        # 3. Hide Menu
        self._menu_container.setVisible(False)
        for btn in self._items:
            btn.graphicsEffect().setOpacity(0)
            
        self.expanded.emit(False)

    def _on_collapse_finished(self):
        try:
            self._width_anim.finished.disconnect(self._on_collapse_finished)
        except: pass
        if not self._is_expanded:
            self.setFixedWidth(self.COLLAPSED_SIZE)
            self.update()



class PresetStatusButton(QWidget):
    """
    Advanced Preset Button component.
    Handles dynamic width transitions, conditional marquee scrolling, 
    and styling states (Ghost vs Solid).
    """
    clicked = pyqtSignal()
    
    # Constants
    MIN_WIDTH = 130  # Minimum to fit "PRESETS" text
    MAX_WIDTH = 280  # Max for longer preset names
    PADDING = 60  # 30px left + 30px right for wider look
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(48)
        
        # State
        self._text = "PRESETS"
        self._is_active = False # False = Manual/Ghost, True = Preset/Solid
        self._is_hovered = False
        self._bg_color = QColor(255, 255, 255, 12) # Ghost default
        self._text_color = QColor(255, 255, 255, 150) # Inactive text
        self._current_width = self.MIN_WIDTH
        self._temp_shrink = False # Flag to temporarily shrink button (e.g. when Lab button expands)
        
        # Animations
        self._width_anim = QPropertyAnimation(self, b"animWidth", self)
        self._width_anim.setDuration(400)
        self._width_anim.setEasingCurve(QEasingCurve.Type.OutElastic) # Spring effect
        
        # Premium Glow Effect (Outer glow with breathing animation)
        # Matches glow_effect.md specification
        self._glow = QGraphicsDropShadowEffect(self)
        self._glow.setBlurRadius(15)  # Mid-range blur
        self._glow.setColor(QColor(0, 224, 255, 100))  # Cyan with alpha
        self._glow.setOffset(0, 0)  # Centered glow (no offset)
        self._glow.setEnabled(False)  # Only enabled on hover
        self.setGraphicsEffect(self._glow)
        
        # Breathing animation for glow (3-second cycle)
        self._glow_anim = QPropertyAnimation(self._glow, b"blurRadius")
        self._glow_anim.setDuration(3000)  # 3-second full cycle
        self._glow_anim.setStartValue(10)   # Inhale: smaller blur
        self._glow_anim.setEndValue(25)     # Exhale: larger blur
        self._glow_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)  # Organic breathing
        self._glow_anim.setLoopCount(-1)  # Infinite loop
        
        # Color animation for breathing (opacity changes)
        self._glow_color_anim = QVariantAnimation(self)
        self._glow_color_anim.setDuration(3000)
        self._glow_color_anim.setStartValue(QColor(0, 224, 255, 80))   # Dim
        self._glow_color_anim.setEndValue(QColor(0, 224, 255, 150))    # Bright
        self._glow_color_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._glow_color_anim.setLoopCount(-1)
        
        def update_glow_color(color):
            self._glow.setColor(color)
        self._glow_color_anim.valueChanged.connect(update_glow_color)
        
        # Calculate proper initial width based on text
        self._calculate_and_set_initial_width()

    @pyqtProperty(int)
    def animWidth(self):
        return self._current_width

    @animWidth.setter
    def animWidth(self, w):
        self._current_width = w
        self.setFixedWidth(w)
        self.update()
    
    def _calculate_and_set_initial_width(self):
        """Calculate and set initial width using the exact drawing font"""
        # Use the same font configuration as paintEvent
        font = QFont()
        font.setFamily(FONT_FAMILY)
        font.setPixelSize(16)
        font.setWeight(QFont.Weight.DemiBold)  # Use bold weight for measurement
        fm = QFontMetrics(font)
        text_width = fm.horizontalAdvance(self._text)
        initial_width = max(self.MIN_WIDTH, min(self.MAX_WIDTH, text_width + self.PADDING))
        self._current_width = initial_width
        self.setFixedWidth(initial_width)
        
    def shrink_for_overlap(self, shrink):
        """Temporarily shrink button to make room for other widgets"""
        if self._temp_shrink == shrink:
            return
            
        self._temp_shrink = shrink
        
        # Recalculate width target
        self._update_width()

    def set_active(self, is_active, text="PRESETS"):
        self._is_active = is_active
        self._text = text.upper()
        
        
        # Update colors/style
        if self._is_active:
            # Active: Solid Green
            self._bg_color = QColor("#00AA00") 
            self._text_color = QColor(255, 255, 255, 255)
        else:
            # Manual: Ghost
            self._bg_color = QColor(255, 255, 255, 12)
            self._text_color = QColor(255, 255, 255, 100) # Faded
            
        self._update_width()
        self.update()
            
    def _update_width(self):
        """Update width based on text content (always fits text)"""
        if self._temp_shrink:
            target = self.MIN_WIDTH
        else:
            # Always calculate width to fit text using exact UI font
            font = QFont()
            font.setFamily(FONT_FAMILY)
            font.setPixelSize(16)
            font.setWeight(QFont.Weight.DemiBold) # Use bold for safe measurement
            fm = QFontMetrics(font)
            text_width = fm.horizontalAdvance(self._text)
            target = max(self.MIN_WIDTH, min(self.MAX_WIDTH, text_width + self.PADDING))
            
        # Animate Width
        if self.width() != target:
            self._width_anim.stop()
            self._width_anim.setStartValue(self.width())
            self._width_anim.setEndValue(target)
            self._width_anim.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        radius = h / 2
        
        # Draw Background
        # Hover effect on background
        bg = self._bg_color
        if self._is_hovered and not self._is_active:
            bg = QColor(255, 255, 255, 25)
        elif self._is_hovered and self._is_active:
             bg = self._bg_color.lighter(110)

        painter.setBrush(QBrush(bg))
        
        # Draw Border (Ghost only)
        if not self._is_active:
            border_color = QColor(255, 255, 255, 50)
            if self._is_hovered: border_color = QColor(255, 255, 255, 100)
            painter.setPen(QPen(border_color, 1))
        else:
            painter.setPen(Qt.PenStyle.NoPen)
            
        # Fix clipping: inset by 1px so border stroke is inside bounds
        painter.drawRoundedRect(1, 1, w-2, h-2, int(radius), int(radius))
        
        # Draw Text
        painter.setPen(self._text_color)
        font = self.font()
        font.setFamily(FONT_FAMILY)
        font.setWeight(QFont.Weight.DemiBold if self._is_active else QFont.Weight.Medium)
        font.setPixelSize(16)
        painter.setFont(font)
        
        # Calculate text bounds
        fm = QFontMetrics(font)
        text_width = fm.horizontalAdvance(self._text)
        avail_width = w - self.PADDING
        
        # Clipping region for text
        painter.setClipRect(16, 0, w - 32, h)
        
        # Standard drawing (with ellipsis if needed)
        if text_width > avail_width:
             # Elide
             elided = fm.elidedText(self._text, Qt.TextElideMode.ElideRight, avail_width)
             painter.drawText(QRect(16, 0, w - 32, h), Qt.AlignmentFlag.AlignCenter, elided)
        else:
             # Center
             painter.drawText(QRect(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, self._text)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Click Animation (Scale down/up logic is complex in pure QWidget without transform, 
            # simpler to just update visual state or invoke action)
            self.clicked.emit()
            
    def enterEvent(self, event):
        self._is_hovered = True
        self._glow.setEnabled(True)
        # Start breathing animation
        self._glow_anim.start()
        self._glow_color_anim.start()
        self.update()
            
    def leaveEvent(self, event):
        self._is_hovered = False
        self._glow.setEnabled(False)
        # Stop breathing animation
        self._glow_anim.stop()
        self._glow_color_anim.stop()
        self.update()
