"""
Command Panel Widget
Provides conversion commands and options for ffmpeg, gifsicle, and ImageMagick
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QLineEdit,
    QGroupBox, QFormLayout, QTabWidget, QTextEdit, QSlider, QRadioButton, QSizePolicy, QButtonGroup
)
from client.utils.font_manager import AppFonts, FONT_FAMILY, FONT_SIZE_BUTTON
from client.gui.custom_widgets import TimeRangeSlider, ResizeFolder, RotationOptions, CustomComboBox
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QPoint, QTimer
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush
import json
import winreg


class DynamicFontButton(QPushButton):
    """Custom button that uses the latest font from AppFonts and font_manager variables"""
    def __init__(self, text=""):
        super().__init__(text)
        
        # Store the base style (without font properties)
        self.base_style = {
            "normal": (
                "background-color: #2196f3; "
                "color: white; "
                "border: 2px solid #43a047; "
                "border-radius: 8px; "
                "padding: 12px 0px; "
                "font-weight: bold; "
            ),
            "hover": "background-color: #43a047; color: white; border-color: #43a047;",
            "pressed": "background-color: #388e3c; color: white; border-color: #2e7d32;",
            "disabled": "background-color: #2196f3; color: #eeeeee; border-color: #bdbdbd;",
            "stop_normal": (
                "background-color: #d32f2f; "
                "color: white; "
                "border: 2px solid #b71c1c; "
                "border-radius: 8px; "
                "padding: 12px 0px; "
                "font-weight: bold; "
            ),
            "stop_hover": "background-color: #c62828; color: white; border-color: #b71c1c;",
            "stop_pressed": "background-color: #b71c1c; color: white; border-color: #9c0d0d;",
        }
        
        # Cache stylesheet to avoid constant updates
        self._cached_stylesheet = None
        
        # Initial update
        self.update_stylesheet()
        
    def update_stylesheet(self):
        """Build stylesheet with CURRENT font values from font_manager"""
        # Get current font values
        font_family = FONT_FAMILY
        font_size = FONT_SIZE_BUTTON
        
        # Build stylesheet with font properties included
        if self.text() == "Stop Conversion":
            stylesheet = (
                f"QPushButton {{ "
                f"{self.base_style['stop_normal']} "
                f"font-family: {font_family}; "
                f"font-size: {font_size}px; "
                f"}} "
                f"QPushButton:hover {{ {self.base_style['stop_hover']} }} "
                f"QPushButton:pressed {{ {self.base_style['stop_pressed']} }} "
                f"QPushButton:disabled {{ background-color: #2196f3; color: #eeeeee; border-color: #bdbdbd; }}"
            )
        else:
            stylesheet = (
                f"QPushButton {{ "
                f"{self.base_style['normal']} "
                f"font-family: {font_family}; "
                f"font-size: {font_size}px; "
                f"}} "
                f"QPushButton:hover {{ {self.base_style['hover']} }} "
                f"QPushButton:pressed {{ {self.base_style['pressed']} }} "
                f"QPushButton:disabled {{ {self.base_style['disabled']} }}"
            )
        
        # Only update if stylesheet has changed
        if stylesheet != self._cached_stylesheet:
            self._cached_stylesheet = stylesheet
            self.setStyleSheet(stylesheet)

def is_dark_mode():
    """Check if Windows is in dark mode"""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                           r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        apps_use_light_theme, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return apps_use_light_theme == 0
    except Exception:
        return False

# Determine background color based on theme
BG_COLOR = "#2b2b2b" if is_dark_mode() else "#ffffff"
TEXT_COLOR = "white" if is_dark_mode() else "black"

def get_toggle_style(is_dark):
    """Get toggle style based on theme"""
    bg_color = "#2b2b2b" if is_dark else "#ffffff"
    text_color = "white" if is_dark else "black"
    
    return (
        f"QCheckBox, QRadioButton {{ color: {text_color}; }} "
        "QCheckBox::indicator, QRadioButton::indicator { width: 16px; height: 16px; border-radius: 8px;"
        f" border: 2px solid #43a047; background: {bg_color}; }}"
        "QCheckBox::indicator:checked, QRadioButton::indicator:checked { background: #43a047; border: 2px solid #2e7d32; }"
        "QCheckBox::indicator:unchecked:hover, QRadioButton::indicator:unchecked:hover { border: 2px solid #2e7d32; }"
    )

# Initial style
TOGGLE_STYLE = get_toggle_style(is_dark_mode())

def get_combobox_style(is_dark):
    """Get QComboBox style that respects dark/light mode"""
    bg_color = "#2b2b2b" if is_dark else "#ffffff"
    text_color = "white" if is_dark else "black"
    border_color = "#555555" if is_dark else "#cccccc"
    dropdown_bg = "#404040" if is_dark else "#f0f0f0"
    
    return (
        f"QComboBox {{ "
        f"background-color: {bg_color}; "
        f"color: {text_color}; "
        f"border: 1px solid {border_color}; "
        f"border-radius: 4px; "
        f"padding: 4px; "
        f"}} "
        f"QComboBox:hover {{ border-color: #4CAF50; }} "
        f"QComboBox::drop-down {{ background-color: {dropdown_bg}; border: none; border-left: 1px solid {border_color}; }} "
        f"QComboBox::down-arrow {{ image: none; border: 2px solid {text_color}; border-top: none; border-left: 2px solid transparent; border-right: 2px solid transparent; }} "
        f"QComboBox QAbstractItemView {{ "
        f"background-color: {bg_color}; "
        f"color: {text_color}; "
        f"selection-background-color: #4CAF50; "
        f"selection-color: white; "
        f"border: 1px solid {border_color}; "
        f"}}"
    )

COMBOBOX_STYLE = get_combobox_style(is_dark_mode())


# Keep QRangeSlider as an alias for backwards compatibility
QRangeSlider = TimeRangeSlider


class CommandPanel(QWidget):
    conversion_requested = pyqtSignal(dict)  # Signal with conversion parameters
    stop_conversion_requested = pyqtSignal()  # Signal to stop conversion
    
    def __init__(self):
        super().__init__()
        self.is_dark_mode = is_dark_mode()
        self.setup_ui()
        # Ensure the convert button starts in the blue (idle) style before first use
        self.set_conversion_state(False)
        
    def update_theme(self, is_dark):
        """Update theme-dependent styles"""
        self.is_dark_mode = is_dark
        style = get_toggle_style(is_dark)
        combobox_style = get_combobox_style(is_dark)
        
        # Update all toggle controls
        toggles = self.findChildren((QCheckBox, QRadioButton))
        for toggle in toggles:
            # Only update those that use the custom toggle style
            if toggle in [
                getattr(self, 'multiple_qualities', None),
                getattr(self, 'multiple_resize', None),
                getattr(self, 'multiple_video_variants', None),
                getattr(self, 'multiple_video_qualities', None),
                getattr(self, 'enable_time_cutting', None),
                getattr(self, 'enable_retime', None),
                getattr(self, 'gif_multiple_resize', None),
                getattr(self, 'gif_enable_time_cutting', None),
                getattr(self, 'gif_enable_retime', None),
                getattr(self, 'gif_ffmpeg_variants', None),
                getattr(self, 'gif_auto_resize_checkbox', None),
                getattr(self, 'ffmpeg_gif_blur', None),
                getattr(self, 'output_mode_same', None),
                getattr(self, 'output_mode_nested', None),
                getattr(self, 'output_mode_custom', None)
            ]:
                toggle.setStyleSheet(style)
        
        # Update all ComboBox controls
        comboboxes = self.findChildren(QComboBox)
        for combobox in comboboxes:
            if isinstance(combobox, CustomComboBox):
                combobox.update_theme(is_dark)
            else:
                combobox.setStyleSheet(combobox_style)
        
        # Update custom widgets
        if hasattr(self, 'time_range_slider'):
            self.time_range_slider.update_theme_colors(is_dark)
        
        resize_folders = self.findChildren(ResizeFolder)
        for rf in resize_folders:
            rf.update_theme(is_dark, combobox_style)
        
        rotation_options = self.findChildren(RotationOptions)
        for ro in rotation_options:
            ro.update_theme(is_dark, combobox_style)
        
        # Update nested output name styling
        self._update_nested_output_style()
        
        # Update custom output directory field styling
        self._update_custom_output_style()
    
    def _update_nested_output_style(self):
        """Update nested output name field styling based on enabled state and theme"""
        is_enabled = self.nested_output_name.isEnabled()
        
        if self.is_dark_mode:
            if is_enabled:
                text_color = "#ffffff"
            else:
                text_color = "#666666"  # Grey for disabled
            bg_color = "#2b2b2b"
        else:
            if is_enabled:
                text_color = "#333333"
            else:
                text_color = "#999999"  # Grey for disabled
            bg_color = "white"
        
        style = f"""
            QLineEdit {{
                color: {text_color};
                background-color: {bg_color};
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 4px;
            }}
        """
        self.nested_output_name.setStyleSheet(style)
    
    def _update_custom_output_style(self):
        """Update custom output directory field styling based on theme"""
        if self.is_dark_mode:
            text_color = "#ffffff"
            bg_color = "#2b2b2b"
            border_color = "#555555"
        else:
            text_color = "#333333"
            bg_color = "white"
            border_color = "#cccccc"
        
        style = f"""
            QLineEdit {{
                color: {text_color};
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 3px;
                padding: 4px;
            }}
        """
        self.output_dir.setStyleSheet(style)

    def setup_ui(self):
        """Setup the command panel interface"""
        layout = QVBoxLayout(self)
        
        # Create tabbed interface for different conversion types
        self.tabs = QTabWidget()
        
        # Image conversion tab
        self.image_tab = self.create_image_tab()
        self.tabs.addTab(self.image_tab, "Images")
        
        # Video conversion tab
        self.video_tab = self.create_video_tab()
        self.tabs.addTab(self.video_tab, "Videos")
        
        # GIF conversion tab
        self.gif_tab = self.create_gif_tab()
        self.tabs.addTab(self.gif_tab, "GIFs")
        
        # Make tab buttons fill available width
        tab_bar = self.tabs.tabBar()
        tab_bar.setExpanding(True)
        tab_bar.setDocumentMode(True)
        # Force tabs to use equal sizes
        from PyQt6.QtWidgets import QTabBar
        tab_bar.setUsesScrollButtons(False)
        self.tabs.setStyleSheet("""
            QTabBar::tab {
                min-width: 0px;
                max-width: 16777215px;
                padding: 8px 16px 13px 16px;
                min-height: 32px;
                margin-bottom: 8px;
                border-bottom: 2px solid #888888;
            }
            QTabBar::tab:selected {
                border-bottom: 2px solid #00AA00;
                margin-bottom: 6px;
            }
            QTabWidget::pane {
                border-top: 2px solid palette(mid);
                margin-top: 0px;
                padding-top: 2px;
                margin-bottom: 5px;
            }
        """)
        
        layout.addWidget(self.tabs)
        
        # Output settings
        output_group = self.create_output_settings()
        layout.addWidget(output_group)
        
        # Control buttons
        button_layout = self.create_control_buttons()
        layout.addLayout(button_layout)
        
    def create_image_tab(self):
        """Create image conversion options tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Output format selection
        format_group = QGroupBox("Image Settings")
        format_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        format_layout = QFormLayout(format_group)
        
        # Format dropdown - FIRST
        self.image_format = CustomComboBox()
        self.image_format.addItems(["WebP", "JPG", "PNG", "TIFF", "BMP"])
        format_layout.addRow("Format:", self.image_format)
        
        # Multiple qualities option - SECOND
        self.multiple_qualities = QCheckBox("Multiple qualities")
        self.multiple_qualities.toggled.connect(self.toggle_quality_mode)
        self.multiple_qualities.setStyleSheet(TOGGLE_STYLE)
        format_layout.addRow(self.multiple_qualities)
        
        # Quality settings
        self.image_quality = QSlider(Qt.Orientation.Horizontal)
        self.image_quality.setRange(1, 100)
        self.image_quality.setValue(40)
        self.image_quality_label = QLabel("40")
        self.image_quality.valueChanged.connect(lambda v: self.image_quality_label.setText(str(v)))
        
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(self.image_quality)
        quality_layout.addWidget(self.image_quality_label)
        format_layout.addRow("Quality:", quality_layout)
        
        # Quality variants input (hidden by default)
        self.quality_variants = QLineEdit()
        self.quality_variants.setPlaceholderText("e.g., 40, 60, 80, 95")
        self.quality_variants.setText("40, 60, 80, 95")
        self.quality_variants.setVisible(False)
        self.quality_variants_label = QLabel("Quality variants:")
        self.quality_variants_label.setVisible(False)
        format_layout.addRow(self.quality_variants_label, self.quality_variants)
        
        layout.addWidget(format_group)
        
        # Resize options
        resize_group = QGroupBox("Resize Options")
        resize_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        resize_layout = QFormLayout(resize_group)
        
        # Resize mode selection - FIRST
        self.resize_mode = CustomComboBox()
        self.resize_mode.addItems(["No resize", "By width (pixels)", "By longer edge (pixels)", "By ratio (percent)"])
        self.resize_mode.currentTextChanged.connect(self.on_resize_mode_changed)
        resize_layout.addRow("Resize mode:", self.resize_mode)
        
        # Multiple resize option - SECOND
        self.multiple_resize = QCheckBox("Multiple resize variants")
        self.multiple_resize.toggled.connect(self.toggle_resize_mode)
        self.multiple_resize.setStyleSheet(TOGGLE_STYLE)
        resize_layout.addRow(self.multiple_resize)
        
        # Single resize value input
        self.resize_value = QSpinBox()
        self.resize_value.setRange(1, 10000)
        self.resize_value.setValue(720)  # Default for pixels
        self.resize_value.setVisible(False)
        self.resize_value_label = QLabel("Width (pixels):")
        self.resize_value_label.setVisible(False)
        resize_layout.addRow(self.resize_value_label, self.resize_value)
        
        # Multiple resize input (hidden by default)
        self.resize_variants = QLineEdit()
        self.resize_variants.setPlaceholderText("e.g., 30,50,80 or 720,1280,1920")
        self.resize_variants.setText("720,1280,1920")
        self.resize_variants.setVisible(False)
        self.resize_variants_label = QLabel("Resize values:")
        self.resize_variants_label.setVisible(False)
        resize_layout.addRow(self.resize_variants_label, self.resize_variants)
        
        layout.addWidget(resize_group)
        
        # Rotation options
        rotation_group = QGroupBox("Rotation")
        rotation_group.setSizePolicy(rotation_group.sizePolicy().horizontalPolicy(), QSizePolicy.Policy.Maximum)
        rotation_layout = QFormLayout(rotation_group)
        
        self.rotation_angle = CustomComboBox()
        self.rotation_angle.addItems(["No rotation", "90° clockwise", "180°", "270° clockwise"])
        rotation_layout.addRow("Rotation:", self.rotation_angle)
        
        layout.addWidget(rotation_group)
        
        return tab
        
    def create_video_tab(self):
        """Create video conversion options tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Video codec selection
        codec_group = QGroupBox("Video Settings")
        codec_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        codec_layout = QFormLayout(codec_group)
        
        self.video_codec = CustomComboBox()
        self.video_codec.addItems(["WebM (VP9, faster)", "WebM (AV1, slower)", "MP4 (H.264)", "MP4 (H.265)", "MP4 (AV1)"])
        self.video_codec.currentTextChanged.connect(self.on_video_codec_changed)
        codec_layout.addRow("Format:", self.video_codec)
        
        # Quality (CRF) slider for WebM
        self.video_quality = QSlider(Qt.Orientation.Horizontal)
        self.video_quality.setRange(0, 100)
        self.video_quality.setValue(30)  # Maps to CRF 23 (good quality)
        self.video_quality.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.video_quality.setTickInterval(10)
        self.video_quality.setToolTip("Quality: 0=lossless, 100=worst quality\nRecommended: 30-50 for WebM")
        self.video_quality_label = QLabel("Quality:")
        self.video_quality_value = QLabel("30")
        self.video_quality.valueChanged.connect(lambda v: self.video_quality_value.setText(str(v)))
        
        # Create horizontal layout for slider and value display
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(self.video_quality)
        quality_layout.addWidget(self.video_quality_value)
        
        # Multiple video quality variants option - ABOVE slider
        self.multiple_video_qualities = QCheckBox("Multiple quality variants")
        self.multiple_video_qualities.toggled.connect(self.toggle_video_quality_mode)
        self.multiple_video_qualities.setStyleSheet(TOGGLE_STYLE)
        codec_layout.addRow(self.multiple_video_qualities)
        
        # Quality controls
        codec_layout.addRow(self.video_quality_label, quality_layout)
        
        # Video quality variant inputs (hidden by default)
        self.video_quality_variants = QLineEdit()
        self.video_quality_variants.setPlaceholderText("e.g., 25,40,70 (quality values 0-100)")
        self.video_quality_variants.setText("15,23,31")
        self.video_quality_variants.setVisible(False)
        self.video_quality_variants.editingFinished.connect(self.validate_video_quality_variants)
        self.video_quality_variants_label = QLabel("Quality variants:")
        self.video_quality_variants_label.setVisible(False)
        codec_layout.addRow(self.video_quality_variants_label, self.video_quality_variants)
        
        # Set initial state for bitrate and quality visibility
        self.on_video_codec_changed(self.video_codec.currentText())
        
        layout.addWidget(codec_group)
        
        # Video filters
        filter_group = QGroupBox("Resize")
        filter_layout = QFormLayout(filter_group)
        
        # Resize mode selection
        self.video_resize_mode = CustomComboBox()
        self.video_resize_mode.addItems(["No resize", "By width (pixels)", "By longer edge (pixels)", "By ratio (percent)"])
        self.video_resize_mode.currentTextChanged.connect(self.on_video_resize_mode_changed)
        filter_layout.addRow("Resize mode:", self.video_resize_mode)
        
        # Multiple video size variants option - SECOND
        self.multiple_video_variants = QCheckBox("Multiple size variants")
        self.multiple_video_variants.toggled.connect(self.toggle_video_variant_mode)
        self.multiple_video_variants.setStyleSheet(TOGGLE_STYLE)
        filter_layout.addRow(self.multiple_video_variants)
        
        # Single resize value input (hidden by default)
        self.video_resize_value = QSpinBox()
        self.video_resize_value.setRange(1, 10000)
        self.video_resize_value.setValue(1920)
        self.video_resize_value.setVisible(False)
        self.video_resize_value_label = QLabel("Width (pixels):")
        self.video_resize_value_label.setVisible(False)
        filter_layout.addRow(self.video_resize_value_label, self.video_resize_value)
        
        # Video size variant inputs (hidden by default)
        self.video_size_variants = QLineEdit()
        self.video_size_variants.setPlaceholderText("e.g., 480,720,1080 or 25%,50%,75%")
        self.video_size_variants.setText("480,720,1080")
        self.video_size_variants.setVisible(False)
        self.video_size_variants_label = QLabel("Size variants:")
        self.video_size_variants_label.setVisible(False)
        filter_layout.addRow(self.video_size_variants_label, self.video_size_variants)
        
        layout.addWidget(filter_group)
        
        # Video rotation options
        rotation_group = QGroupBox("Rotation")
        rotation_layout = QFormLayout(rotation_group)
        
        self.video_rotation_angle = CustomComboBox()
        self.video_rotation_angle.addItems(["No rotation", "90° clockwise", "180°", "270° clockwise"])
        rotation_layout.addRow("Rotation:", self.video_rotation_angle)
        
        layout.addWidget(rotation_group)
        
        # Video time options (cutting + retime)
        time_group = QGroupBox("Time Options")
        time_layout = QFormLayout(time_group)
        
        # Time range toggle (controls range slider visibility)
        self.enable_time_cutting = QCheckBox("Time range")
        self.enable_time_cutting.setStyleSheet(TOGGLE_STYLE)
        self.enable_time_cutting.toggled.connect(self.toggle_time_cutting)
        time_layout.addRow(self.enable_time_cutting)
        
        # Time range slider with dark mode support
        self.time_range_slider = TimeRangeSlider(is_dark_mode=self.is_dark_mode)
        self.time_range_slider.setRange(0.0, 1.0)
        self.time_range_slider.setStartValue(0.0)
        self.time_range_slider.setEndValue(1.0)
        self.time_range_slider.setToolTip("Drag the handles to set start and end times (0% = beginning, 100% = end)")
        self.time_range_slider.setVisible(False)
        time_layout.addRow("Time Range:", self.time_range_slider)

        # Retime controls
        self.enable_retime = QCheckBox("Enable retime")
        self.enable_retime.setStyleSheet(TOGGLE_STYLE)
        self.enable_retime.toggled.connect(self.toggle_retime)
        time_layout.addRow(self.enable_retime)

        self.retime_slider = QSlider(Qt.Orientation.Horizontal)
        self.retime_slider.setRange(10, 30)  # 1.0x to 3.0x in 0.1 steps
        self.retime_slider.setValue(10)
        self.retime_slider.setSingleStep(1)
        self.retime_slider.setVisible(False)
        self.retime_value_label = QLabel("1.0x")
        self.retime_value_label.setVisible(False)
        self.retime_slider.valueChanged.connect(lambda v: self.retime_value_label.setText(f"{v/10:.1f}x"))
        
        retime_layout = QHBoxLayout()
        retime_layout.addWidget(self.retime_slider)
        retime_layout.addWidget(self.retime_value_label)
        time_layout.addRow("Playback speed:", retime_layout)
        
        layout.addWidget(time_group)
        
        return tab
        
    def create_gif_tab(self):
        """Create GIF conversion options tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # --- FFmpeg Export Options ---
        self.ffmpeg_group = QGroupBox("GIF Settings")
        self.ffmpeg_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        ffmpeg_layout = QFormLayout(self.ffmpeg_group)

        # Mode selection buttons (inside GIF Settings)
        mode_buttons_container = QWidget()
        mode_buttons_layout = QHBoxLayout(mode_buttons_container)
        mode_buttons_layout.setContentsMargins(0, 0, 0, 0)
        mode_buttons_layout.setSpacing(8)

        mode_button_style = (
            "QPushButton { padding: 6px 14px; border-radius: 6px; border: 1px solid #555555; }"
            "QPushButton:checked { background-color: #4CAF50; color: white; border-color: #43a047; }"
        )

        self.gif_mode_max_size_btn = QPushButton("Max Size")
        self.gif_mode_max_size_btn.setCheckable(True)
        self.gif_mode_max_size_btn.setStyleSheet(mode_button_style)
        self.gif_mode_max_size_btn.setToolTip("Auto-optimize to fit target file size")

        self.gif_mode_manual_btn = QPushButton("Manual")
        self.gif_mode_manual_btn.setCheckable(True)
        self.gif_mode_manual_btn.setStyleSheet(mode_button_style)
        self.gif_mode_manual_btn.setToolTip("Set quality settings yourself")

        self.gif_mode_button_group = QButtonGroup(self)
        self.gif_mode_button_group.setExclusive(True)
        self.gif_mode_button_group.addButton(self.gif_mode_max_size_btn)
        self.gif_mode_button_group.addButton(self.gif_mode_manual_btn)

        # Default: Max Size
        self.gif_mode_max_size_btn.setChecked(True)

        self.gif_mode_max_size_btn.toggled.connect(
            lambda checked: checked and self.on_gif_size_mode_changed("Max Size")
        )
        self.gif_mode_manual_btn.toggled.connect(
            lambda checked: checked and self.on_gif_size_mode_changed("Manual")
        )

        mode_buttons_layout.addWidget(self.gif_mode_max_size_btn)
        mode_buttons_layout.addWidget(self.gif_mode_manual_btn)
        ffmpeg_layout.addRow("Mode:", mode_buttons_container)

        # Max size input (hidden by default)
        self.gif_max_size_spinbox = QDoubleSpinBox()
        self.gif_max_size_spinbox.setRange(0.5, 100.0)
        self.gif_max_size_spinbox.setValue(5.0)
        self.gif_max_size_spinbox.setSuffix("")
        self.gif_max_size_spinbox.setDecimals(1)
        self.gif_max_size_spinbox.setSingleStep(0.5)
        self.gif_max_size_spinbox.setToolTip("Target maximum file size in megabytes")
        self.gif_max_size_spinbox.setVisible(False)
        self.gif_max_size_label = QLabel("Target Size (MB):")
        self.gif_max_size_label.setVisible(False)
        ffmpeg_layout.addRow(self.gif_max_size_label, self.gif_max_size_spinbox)

        # Auto-resize checkbox (for Max Size mode)
        self.gif_auto_resize_checkbox = QCheckBox("Auto-resize")
        self.gif_auto_resize_checkbox.setChecked(True)  # Enabled by default
        self.gif_auto_resize_checkbox.setStyleSheet(TOGGLE_STYLE)
        self.gif_auto_resize_checkbox.setToolTip(
            "Try resolution scaling (90%, 80%, 70%, 60%) before using very low quality settings.\n"
            "This helps maintain visual quality while meeting the target size."
        )
        self.gif_auto_resize_checkbox.setVisible(False)
        self.gif_auto_resize_label = QLabel("")  # Empty label for alignment
        self.gif_auto_resize_label.setVisible(False)
        ffmpeg_layout.addRow(self.gif_auto_resize_label, self.gif_auto_resize_checkbox)

        # Estimation info label (hidden by default)
        self.gif_size_estimate_label = QLabel("")
        self.gif_size_estimate_label.setStyleSheet("color: #888; font-style: italic;")
        self.gif_size_estimate_label.setVisible(False)
        self.gif_size_estimate_label.setWordWrap(True)
        ffmpeg_layout.addRow("", self.gif_size_estimate_label)

        # Multiple variants toggle
        self.gif_ffmpeg_variants = QCheckBox("Multiple Variants (FPS, Colors, Qualities)")
        self.gif_ffmpeg_variants.setStyleSheet(TOGGLE_STYLE)
        self.gif_ffmpeg_variants.toggled.connect(self.toggle_gif_ffmpeg_variants)
        ffmpeg_layout.addRow(self.gif_ffmpeg_variants)

        # FPS
        self.ffmpeg_gif_fps = CustomComboBox()
        self.ffmpeg_gif_fps.addItems(["10", "12", "15", "18", "24"])
        self.ffmpeg_gif_fps.setCurrentText("15")
        self.ffmpeg_gif_fps_label = QLabel("FPS:")
        ffmpeg_layout.addRow(self.ffmpeg_gif_fps_label, self.ffmpeg_gif_fps)

        # FPS Variants
        self.ffmpeg_gif_fps_variants = QLineEdit()
        self.ffmpeg_gif_fps_variants.setPlaceholderText("e.g., 10,15,24")
        self.ffmpeg_gif_fps_variants.setVisible(False)
        self.ffmpeg_gif_fps_variants_label = QLabel("FPS variants:")
        self.ffmpeg_gif_fps_variants_label.setVisible(False)
        ffmpeg_layout.addRow(self.ffmpeg_gif_fps_variants_label, self.ffmpeg_gif_fps_variants)

        # Colors
        self.ffmpeg_gif_colors = CustomComboBox()
        self.ffmpeg_gif_colors.addItems(["8", "16", "32", "64", "128", "256"])
        self.ffmpeg_gif_colors.setCurrentText("256")
        self.ffmpeg_gif_colors_label = QLabel("Colors:")
        ffmpeg_layout.addRow(self.ffmpeg_gif_colors_label, self.ffmpeg_gif_colors)

        # Colors Variants
        self.ffmpeg_gif_colors_variants = QLineEdit()
        self.ffmpeg_gif_colors_variants.setPlaceholderText("e.g., 64,128,256")
        self.ffmpeg_gif_colors_variants.setVisible(False)
        self.ffmpeg_gif_colors_variants_label = QLabel("Colors variants:")
        self.ffmpeg_gif_colors_variants_label.setVisible(False)
        ffmpeg_layout.addRow(self.ffmpeg_gif_colors_variants_label, self.ffmpeg_gif_colors_variants)

        # Dither
        # self.ffmpeg_gif_dither = CustomComboBox()
        # self.ffmpeg_gif_dither.addItems([
        #     "sierra2_4a", 
        #     "sierra2", 
        #     "floyd_steinberg", 
        #     "bayer:bayer_scale=1", 
        #     "bayer:bayer_scale=2", 
        #     "bayer:bayer_scale=3", 
        #     "none"
        # ])
        # self.ffmpeg_gif_dither.setCurrentText("sierra2_4a")
        # self.ffmpeg_gif_dither.setToolTip("Dithering algorithm to use. sierra2_4a is generally good for animations.")
        # self.ffmpeg_gif_dither_label = QLabel("Dithering:")
        # ffmpeg_layout.addRow(self.ffmpeg_gif_dither_label, self.ffmpeg_gif_dither)

        # Dither Quality Slider
        self.gif_dither_quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.gif_dither_quality_slider.setRange(0, 5)
        self.gif_dither_quality_slider.setValue(3)  # Default to best quality (floyd_steinberg)
        self.gif_dither_quality_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.gif_dither_quality_slider.setTickInterval(1)
        
        self.gif_dither_quality_label = QLabel("Quality: 3 (High)")
        self.gif_dither_quality_slider.valueChanged.connect(self.update_dither_quality_label)
        
        self.gif_dither_quality_row_label = QLabel("Quality:")
        ffmpeg_layout.addRow(self.gif_dither_quality_row_label, self.gif_dither_quality_slider)
        ffmpeg_layout.addRow("", self.gif_dither_quality_label)

        # Dither Variants
        self.ffmpeg_gif_dither_variants = QLineEdit()
        self.ffmpeg_gif_dither_variants.setPlaceholderText("e.g., 0,3,5")
        self.ffmpeg_gif_dither_variants.setVisible(False)
        self.ffmpeg_gif_dither_variants_label = QLabel("Quality variants (0-5):")
        self.ffmpeg_gif_dither_variants_label.setVisible(False)
        ffmpeg_layout.addRow(self.ffmpeg_gif_dither_variants_label, self.ffmpeg_gif_dither_variants)

        # Blur
        self.ffmpeg_gif_blur = QCheckBox("Reduce banding")
        self.ffmpeg_gif_blur.setStyleSheet(TOGGLE_STYLE)
        ffmpeg_layout.addRow(self.ffmpeg_gif_blur)

        layout.addWidget(self.ffmpeg_group)
        
        # Resize options - SECOND
        resize_group = QGroupBox("Resize")
        resize_group.setSizePolicy(resize_group.sizePolicy().horizontalPolicy(), QSizePolicy.Policy.Maximum)
        resize_layout = QFormLayout(resize_group)
        
        # Resize mode selection - FIRST
        self.gif_resize_mode = CustomComboBox()
        self.gif_resize_mode.addItems(["No resize", "By width (pixels)", "By longer edge (pixels)", "By ratio (percent)"])
        self.gif_resize_mode.setStyleSheet(COMBOBOX_STYLE)
        self.gif_resize_mode.currentTextChanged.connect(self.on_gif_resize_mode_changed)
        resize_layout.addRow("Resize mode:", self.gif_resize_mode)
        
        # Multiple resize variants option - SECOND
        self.gif_multiple_resize = QCheckBox("Multiple size variants")
        self.gif_multiple_resize.toggled.connect(self.toggle_gif_resize_variant_mode)
        self.gif_multiple_resize.setStyleSheet(TOGGLE_STYLE)
        resize_layout.addRow(self.gif_multiple_resize)
        
        # Single resize value input (hidden by default)
        self.gif_resize_value = QSpinBox()
        self.gif_resize_value.setRange(1, 10000)
        self.gif_resize_value.setValue(720)
        self.gif_resize_value.setVisible(False)
        self.gif_resize_value_label = QLabel("Width (pixels):")
        self.gif_resize_value_label.setVisible(False)
        resize_layout.addRow(self.gif_resize_value_label, self.gif_resize_value)
        
        # Resize variant inputs (hidden by default)
        self.gif_resize_variants = QLineEdit()
        self.gif_resize_variants.setPlaceholderText("e.g., 480,720,1080")
        self.gif_resize_variants.setText("480,720,1080")
        self.gif_resize_variants.setVisible(False)
        self.gif_resize_variants_label = QLabel("Size variants:")
        self.gif_resize_variants_label.setVisible(False)
        resize_layout.addRow(self.gif_resize_variants_label, self.gif_resize_variants)
        
        layout.addWidget(resize_group)
        
        # GIF rotation options - THIRD
        rotation_group = QGroupBox("Rotation")
        rotation_group.setSizePolicy(rotation_group.sizePolicy().horizontalPolicy(), QSizePolicy.Policy.Maximum)
        rotation_layout = QFormLayout(rotation_group)
        
        self.gif_rotation_angle = CustomComboBox()
        self.gif_rotation_angle.addItems(["No rotation", "90° clockwise", "180°", "270° clockwise"])
        self.gif_rotation_angle.setStyleSheet(COMBOBOX_STYLE)
        rotation_layout.addRow("Rotation:", self.gif_rotation_angle)
        
        layout.addWidget(rotation_group)
        
        # GIF time options (cutting + retime) - FOURTH
        gif_time_group = QGroupBox("Time Options")
        gif_time_group.setSizePolicy(gif_time_group.sizePolicy().horizontalPolicy(), QSizePolicy.Policy.Maximum)
        gif_time_layout = QFormLayout(gif_time_group)
        
        # Time range toggle
        self.gif_enable_time_cutting = QCheckBox("Time range")
        self.gif_enable_time_cutting.setStyleSheet(TOGGLE_STYLE)
        self.gif_enable_time_cutting.toggled.connect(self.toggle_gif_time_cutting)
        gif_time_layout.addRow(self.gif_enable_time_cutting)
        
        # Time range slider with dark mode support
        self.gif_time_range_slider = TimeRangeSlider(is_dark_mode=self.is_dark_mode)
        self.gif_time_range_slider.setRange(0.0, 1.0)
        self.gif_time_range_slider.setStartValue(0.0)
        self.gif_time_range_slider.setEndValue(1.0)
        self.gif_time_range_slider.setToolTip("Drag the handles to set start and end times (0% = beginning, 100% = end)")
        self.gif_time_range_slider.setVisible(False)
        gif_time_layout.addRow("Time Range:", self.gif_time_range_slider)

        # Retime controls for GIF conversion
        self.gif_enable_retime = QCheckBox("Enable retime")
        self.gif_enable_retime.setStyleSheet(TOGGLE_STYLE)
        self.gif_enable_retime.toggled.connect(self.toggle_gif_retime)
        gif_time_layout.addRow(self.gif_enable_retime)

        self.gif_retime_slider = QSlider(Qt.Orientation.Horizontal)
        self.gif_retime_slider.setRange(10, 30)
        self.gif_retime_slider.setValue(10)
        self.gif_retime_slider.setSingleStep(1)
        self.gif_retime_slider.setVisible(False)
        self.gif_retime_value_label = QLabel("1.0x")
        self.gif_retime_value_label.setVisible(False)
        self.gif_retime_slider.valueChanged.connect(lambda v: self.gif_retime_value_label.setText(f"{v/10:.1f}x"))

        gif_retime_layout = QHBoxLayout()
        gif_retime_layout.addWidget(self.gif_retime_slider)
        gif_retime_layout.addWidget(self.gif_retime_value_label)
        gif_time_layout.addRow("Playback speed:", gif_retime_layout)
        
        layout.addWidget(gif_time_group)
        
        # Apply initial size mode visibility (Max Size default)
        self.on_gif_size_mode_changed("Max Size")
        
        return tab

    def create_output_settings(self):
        """Create output directory and naming settings"""
        group = QGroupBox("Output Settings")
        layout = QFormLayout(group)
        
        # Output location options
        self.output_mode_same = QRadioButton("Same folder as source")
        self.output_mode_nested = QRadioButton("Nested folder inside source:")
        self.output_mode_same.setChecked(True)

        # Apply shared green toggle styling and white text
        self.output_mode_same.setStyleSheet(TOGGLE_STYLE)
        self.output_mode_nested.setStyleSheet(TOGGLE_STYLE)

        self.nested_output_name = QLineEdit("output")
        self.nested_output_name.setPlaceholderText("output")
        self.nested_output_name.setEnabled(False)  # Disabled by default
        
        # Connect toggle to enable/disable nested output name
        self.output_mode_nested.toggled.connect(self.nested_output_name.setEnabled)
        self.output_mode_nested.toggled.connect(self._update_nested_output_style)
        
        nested_layout = QHBoxLayout()
        nested_layout.addWidget(self.output_mode_nested)
        nested_layout.addWidget(self.nested_output_name)

        layout.addRow(self.output_mode_same)
        layout.addRow(nested_layout)

        # Toggle for custom output directory (as radio button)
        self.output_mode_custom = QRadioButton("Custom")
        self.output_mode_custom.setChecked(False)
        self.output_mode_custom.toggled.connect(self.on_custom_output_toggled)
        # Apply shared green toggle styling
        self.output_mode_custom.setStyleSheet(TOGGLE_STYLE)
        layout.addRow(self.output_mode_custom)
        
        # Custom output directory section (hidden by default)
        self.output_dir = QLineEdit()
        self.output_dir.setPlaceholderText("Select output directory")
        self.output_dir.setVisible(False)
        
        self.browse_output_btn = QPushButton("Browse...")
        self.browse_output_btn.clicked.connect(self.browse_output_directory)
        self.browse_output_btn.setVisible(False)
        
        output_layout = QHBoxLayout()
        output_layout.addWidget(self.output_dir)
        output_layout.addWidget(self.browse_output_btn)
        
        layout.addRow(output_layout)
        
        return group
        
    def create_control_buttons(self):
        """Create conversion control buttons"""
        layout = QVBoxLayout()
        self.convert_btn = DynamicFontButton("Start Conversion")
        self.convert_btn.clicked.connect(self.on_convert_button_clicked)
        self.is_converting = False
        
        # Make button expand to full width
        self.convert_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # DynamicFontButton handles stylesheet with font properties automatically
        layout.addWidget(self.convert_btn)
        return layout
        
    def on_convert_button_clicked(self):
        """Handle convert button click - either start or stop"""
        if self.is_converting:
            self.stop_conversion()
        else:
            self.start_conversion()
    
    def set_conversion_state(self, is_converting: bool):
        """Set the conversion state and update button appearance"""
        self.is_converting = is_converting
        
        if is_converting:
            self.convert_btn.setText("Stop Conversion")
            # Trigger stylesheet update with current font values
            self.convert_btn.update_stylesheet()
        else:
            self.convert_btn.setText("Start Conversion")
            # Trigger stylesheet update with current font values
            self.convert_btn.update_stylesheet()
    
    def stop_conversion(self):
        """Request to stop the current conversion"""
        self.stop_conversion_requested.emit()
        # Disable the button temporarily to prevent multiple clicks
        self.convert_btn.setEnabled(False)
        self.convert_btn.setText("Stopping...")
    
    def on_custom_output_toggled(self, state):
        """Handle custom output directory toggle - show controls only when custom is selected"""
        if state:  # If custom radio button is selected
            self.output_dir.setVisible(True)
            self.browse_output_btn.setVisible(True)
        else:
            self.output_dir.setVisible(False)
            self.browse_output_btn.setVisible(False)
            self.output_dir.clear()
        
    def browse_output_directory(self):
        """Browse for output directory"""
        from PyQt6.QtWidgets import QFileDialog
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.output_dir.setText(directory)
            
    def get_conversion_params(self):
        """Get current conversion parameters"""
        current_tab = self.tabs.currentIndex()
        
        params = {
            'output_dir': self.output_dir.text().strip(),
            'use_nested_output': self.output_mode_nested.isChecked(),
            'nested_output_name': (self.nested_output_name.text().strip() or 'output'),
            'suffix': '_converted',
            'overwrite': True,  # default overwrite when targeting output directory
        }
        
        if current_tab == 0:  # Images
            # Handle quality variants
            quality_variants = None
            if self.multiple_qualities.isChecked():
                variants_text = self.quality_variants.text().strip()
                if variants_text:
                    try:
                        quality_variants = [int(q.strip()) for q in variants_text.split(',') if q.strip().isdigit()]
                        quality_variants = [q for q in quality_variants if 1 <= q <= 100]  # Validate range
                    except:
                        quality_variants = None
            
            # Get resize values
            resize_values = self.get_resize_values()
            # If only one resize value, set as current_resize for single conversion
            current_resize = None
            if resize_values and len(resize_values) == 1:
                current_resize = resize_values[0]
            
            params.update({
                'type': 'image',
                'format': self.image_format.currentText().lower(),
                'quality': self.image_quality.value(),
                'quality_variants': quality_variants,
                'multiple_qualities': self.multiple_qualities.isChecked(),
                'resize_variants': resize_values,
                'current_resize': current_resize,
                'rotation_angle': self.rotation_angle.currentText(),
            })
        elif current_tab == 1:  # Videos
            # Handle video quality variants
            quality_variants = None
            if hasattr(self, 'multiple_video_qualities') and self.multiple_video_qualities.isChecked():
                variants_text = self.video_quality_variants.text().strip()
                if variants_text:
                    try:
                        quality_variants = [int(q.strip()) for q in variants_text.split(',') if q.strip().isdigit()]
                        quality_variants = [q for q in quality_variants if 0 <= q <= 100]  # Validate UI quality range
                    except:
                        quality_variants = None
            
            # Handle video size variants
            if hasattr(self, 'multiple_video_variants') and self.multiple_video_variants.isChecked():
                video_variants = self.get_video_variant_values()
                params.update({
                    'type': 'video',
                    'codec': self.video_codec.currentText(),
                    'quality': self.video_quality.value(),
                    'quality_variants': quality_variants,
                    'multiple_video_qualities': self.multiple_video_qualities.isChecked(),
                    'video_variants': video_variants,
                    'multiple_video_variants': True,
                    'rotation_angle': self.video_rotation_angle.currentText(),
                    'enable_time_cutting': self.enable_time_cutting.isChecked(),
                    'time_start': self.time_range_slider.getStartValue() if self.enable_time_cutting.isChecked() else 0.0,
                    'time_end': self.time_range_slider.getEndValue() if self.enable_time_cutting.isChecked() else 1.0,
                    'retime_enabled': self.enable_retime.isChecked(),
                    'retime_speed': self.retime_slider.value() / 10.0,
                })
            else:
                video_resize = self.get_video_resize_values()
                video_width = None
                video_scale = False
                if video_resize and len(video_resize) == 1:
                    v = video_resize[0]
                    if v.endswith('%'):
                        video_scale = True
                        video_width = v
                    else:
                        try:
                            video_width = int(v)
                            video_scale = True
                        except Exception:
                            video_width = None
                params.update({
                    'type': 'video',
                    'codec': self.video_codec.currentText(),
                    'quality': self.video_quality.value(),
                    'quality_variants': quality_variants,
                    'multiple_video_qualities': self.multiple_video_qualities.isChecked(),
                    'video_variants': [],
                    'multiple_video_variants': False,
                    'width': video_width,
                    'scale': video_scale,
                    'rotation_angle': self.video_rotation_angle.currentText(),
                    'enable_time_cutting': self.enable_time_cutting.isChecked(),
                    'time_start': self.time_range_slider.getStartValue() if self.enable_time_cutting.isChecked() else 0.0,
                    'time_end': self.time_range_slider.getEndValue() if self.enable_time_cutting.isChecked() else 1.0,
                    'retime_enabled': self.enable_retime.isChecked(),
                    'retime_speed': self.retime_slider.value() / 10.0,
                })
        elif current_tab == 2:  # GIFs
            # Get GIF variants if multiple variants is checked
            gif_variants = self.get_gif_variant_values()
            
            # Get resize values
            gif_resize_values = self.get_gif_resize_values()
            
            # Get size mode settings
            size_mode = getattr(self, 'gif_size_mode_value', 'max_size')
            
            params.update({
                'type': 'gif',
                'use_ffmpeg_gif': True,  # Always use FFmpeg
                'gif_size_mode': size_mode,  # 'manual' or 'max_size'
                'gif_max_size_mb': self.gif_max_size_spinbox.value() if size_mode == 'max_size' else None,
                'gif_auto_resize': self.gif_auto_resize_checkbox.isChecked() if size_mode == 'max_size' else False,
                'ffmpeg_fps': int(self.ffmpeg_gif_fps.currentText()),
                'ffmpeg_colors': int(self.ffmpeg_gif_colors.currentText()),
                'ffmpeg_dither': self.get_dither_string_from_quality(self.gif_dither_quality_slider.value()),
                'ffmpeg_blur': self.ffmpeg_gif_blur.isChecked(),
                'gif_resize_mode': self.gif_resize_mode.currentText(),
                'gif_resize_values': gif_resize_values,
                'rotation': self.gif_rotation_angle.currentText(),
                'enable_time_cutting': self.gif_enable_time_cutting.isChecked(),
                'time_start': self.gif_time_range_slider.getStartValue() if self.gif_enable_time_cutting.isChecked() else 0.0,
                'time_end': self.gif_time_range_slider.getEndValue() if self.gif_enable_time_cutting.isChecked() else 1.0,
                'retime_enabled': self.gif_enable_retime.isChecked(),
                'retime_speed': self.gif_retime_slider.value() / 10.0,
                'gif_variants': gif_variants,
                'multiple_gif_variants': bool(gif_variants),
            })
            
        return params
        
    def start_conversion(self):
        """Emit conversion request signal"""
        params = self.get_conversion_params()
        self.conversion_requested.emit(params)
        
    def preview_command(self):
        """Show preview of the command that would be executed"""
        params = self.get_conversion_params()
        
        # Create a simple preview dialog
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Command Preview")
        dialog.resize(600, 400)
        
        # Apply dark theme to the dialog
        from .theme_manager import ThemeManager
        theme = ThemeManager()
        dialog.setStyleSheet(theme.get_dialog_styles())
        
        layout = QVBoxLayout(dialog)
        
        preview_text = QTextEdit()
        preview_text.setReadOnly(True)
        preview_text.setPlainText(f"Conversion Parameters:\n{json.dumps(params, indent=2)}")
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        
        layout.addWidget(preview_text)
        layout.addWidget(close_btn)
        
        dialog.exec()
        
    def toggle_quality_mode(self, checked):
        """Toggle between single and multiple quality modes"""
        # Show/hide appropriate controls
        self.image_quality.setVisible(not checked)
        self.image_quality_label.setVisible(not checked)
        self.quality_variants.setVisible(checked)
        self.quality_variants_label.setVisible(checked)
        
        # Update the quality row label text
        quality_row = self.image_tab.findChild(QFormLayout).labelForField(self.image_quality.parent())
        if quality_row:
            if checked:
                quality_row.setText("Quality variants:")
            else:
                quality_row.setText("Quality:")
    
    def toggle_resize_mode(self, checked):
        """Toggle between single and multiple resize modes"""
        # Show/hide appropriate controls
        self.resize_enabled.setVisible(not checked)
        self.resize_width.setVisible(not checked)
        self.resize_variants.setVisible(checked)
        self.resize_variants_label.setVisible(checked)
    
    def on_resize_value_changed(self, value):
        """Save the current resize value based on the current mode"""
        current_mode = self.resize_mode.currentText()
        if current_mode == "By width (pixels)":
            self.last_pixel_value = value
        elif current_mode == "By ratio (percent)":
            self.last_percent_value = value
        """Get list of resize values from input - simplified version"""
        resize_mode = self.resize_mode.currentText()
        
        if resize_mode == "No resize":
            return []
            
        if hasattr(self, 'multiple_resize') and self.multiple_resize.isChecked():
            resize_text = self.resize_variants.text().strip()
            if not resize_text:
                return []
            
            # Simple split by comma and clean values
            values = []
            for value in resize_text.split(','):
                value = value.strip()
                if not value:
                    continue
                
                try:
                    if resize_mode == "By ratio (percent)":
                        # Validate percentage (1-200)
                        percent = float(value)
                        if 1 <= percent <= 200:
                            values.append(f"{percent}%")
                    else:  # By width (pixels)
                        # Validate pixel width (positive integer)
                        width = int(value)
                        if width > 0:
                            values.append(str(width))
                except (ValueError, TypeError):
                    continue  # Skip invalid values
            
            return values
        else:
            # Single resize mode - get value from input
            if resize_mode == "By ratio (percent)":
                value = self.video_resize_value.value() if hasattr(self, 'video_resize_value') else 100
                return [f"{value}%"]
            elif resize_mode == "By width (pixels)":
                value = self.video_resize_value.value() if hasattr(self, 'video_resize_value') else 1920
                return [str(value)]
            else:
                return []
    

    
    def toggle_gif_ffmpeg_variants(self, checked):
        """Toggle between single and multiple FFmpeg variant modes"""
        # Show/hide single controls
        self.ffmpeg_gif_fps.setVisible(not checked)
        self.ffmpeg_gif_fps_label.setVisible(not checked)
        self.ffmpeg_gif_colors.setVisible(not checked)
        self.ffmpeg_gif_colors_label.setVisible(not checked)
        # self.ffmpeg_gif_dither.setVisible(not checked)
        # self.ffmpeg_gif_dither_label.setVisible(not checked)
        self.gif_dither_quality_slider.setVisible(not checked)
        self.gif_dither_quality_row_label.setVisible(not checked)
        self.gif_dither_quality_label.setVisible(not checked)
        
        # Show/hide variant controls
        self.ffmpeg_gif_fps_variants.setVisible(checked)
        self.ffmpeg_gif_fps_variants_label.setVisible(checked)
        self.ffmpeg_gif_colors_variants.setVisible(checked)
        self.ffmpeg_gif_colors_variants_label.setVisible(checked)
        self.ffmpeg_gif_dither_variants.setVisible(checked)
        self.ffmpeg_gif_dither_variants_label.setVisible(checked)
        
        # Set default values if empty
        if checked:
            if not self.ffmpeg_gif_fps_variants.text():
                self.ffmpeg_gif_fps_variants.setText("10,15,24")
            if not self.ffmpeg_gif_colors_variants.text():
                self.ffmpeg_gif_colors_variants.setText("64,128,256")
            if not self.ffmpeg_gif_dither_variants.text():
                self.ffmpeg_gif_dither_variants.setText("0,3,5")

    def get_gif_variant_values(self):
        """Get all GIF variant values if multiple variants is enabled"""
        variants = {}
        
        # Check if resize variants are enabled
        if hasattr(self, 'gif_multiple_resize') and self.gif_multiple_resize.isChecked():
            resize_values = self.get_gif_resize_values()
            if resize_values:
                variants['resize'] = resize_values
        
        # Check if FFmpeg variants are enabled
        if hasattr(self, 'gif_ffmpeg_variants') and self.gif_ffmpeg_variants.isChecked():
            # FPS
            fps_text = self.ffmpeg_gif_fps_variants.text().strip()
            if fps_text:
                try:
                    fps_values = [int(x.strip()) for x in fps_text.split(',') if x.strip().isdigit()]
                    if fps_values:
                        variants['fps'] = fps_values
                except:
                    pass
            
            # Colors
            colors_text = self.ffmpeg_gif_colors_variants.text().strip()
            if colors_text:
                try:
                    colors_values = [int(x.strip()) for x in colors_text.split(',') if x.strip().isdigit()]
                    if colors_values:
                        variants['colors'] = colors_values
                except:
                    pass
            
            # Dither (Quality 0-5)
            dither_text = self.ffmpeg_gif_dither_variants.text().strip()
            if dither_text:
                try:
                    qualities = [int(x.strip()) for x in dither_text.split(',') if x.strip().isdigit()]
                    if qualities:
                        # Map qualities to dither strings
                        variants['dither'] = [self.get_dither_string_from_quality(q) for q in qualities if 0 <= q <= 5]
                except:
                    pass
        
        return variants

    def update_dither_quality_label(self, value):
        """Update dither quality label based on slider value"""
        labels = {
            0: "0 (Lowest)",
            1: "1 (Low)",
            2: "2 (Medium)",
            3: "3 (High)",
            4: "4 (Higher)",
            5: "5 (Best)"
        }
        self.gif_dither_quality_label.setText(f"Quality: {labels.get(value, str(value))}")

    def get_dither_string_from_quality(self, quality):
        """Map integer quality (0-5) to FFmpeg dither string"""
        mapping = {
            0: "none",
            1: "bayer:bayer_scale=5",
            2: "bayer:bayer_scale=4",
            3: "bayer:bayer_scale=3",
            4: "bayer:bayer_scale=1",
            5: "floyd_steinberg"
        }
        return mapping.get(quality, "floyd_steinberg")

    def on_gif_size_mode_changed(self, mode):
        """Handle GIF size mode change between Manual and Max Size"""
        is_max_size = (mode == "Max Size")
        self.gif_size_mode_value = "max_size" if is_max_size else "manual"
        
        # Show/hide max size controls
        self.gif_max_size_label.setVisible(is_max_size)
        self.gif_max_size_spinbox.setVisible(is_max_size)
        self.gif_auto_resize_checkbox.setVisible(is_max_size)
        self.gif_auto_resize_label.setVisible(is_max_size)
        self.gif_size_estimate_label.setVisible(is_max_size)
        
        if is_max_size:
            # Hide manual quality controls in Max Size mode (auto-optimized)
            self.gif_ffmpeg_variants.setChecked(False)
            self.gif_ffmpeg_variants.setVisible(False)
            
            self.ffmpeg_gif_fps_label.setVisible(False)
            self.ffmpeg_gif_fps.setVisible(False)
            self.ffmpeg_gif_fps_variants_label.setVisible(False)
            self.ffmpeg_gif_fps_variants.setVisible(False)
            
            self.ffmpeg_gif_colors_label.setVisible(False)
            self.ffmpeg_gif_colors.setVisible(False)
            self.ffmpeg_gif_colors_variants_label.setVisible(False)
            self.ffmpeg_gif_colors_variants.setVisible(False)
            
            self.gif_dither_quality_slider.setVisible(False)
            self.gif_dither_quality_row_label.setVisible(False)
            self.gif_dither_quality_label.setVisible(False)
            self.ffmpeg_gif_dither_variants_label.setVisible(False)
            self.ffmpeg_gif_dither_variants.setVisible(False)
            
            self.gif_size_estimate_label.setText(
                "Settings will be auto-optimized to fit target size. "
                "Manual settings above are used as starting point."
            )
        else:
            # Show manual controls in Manual mode
            self.gif_ffmpeg_variants.setVisible(True)
            
            self.ffmpeg_gif_fps_label.setVisible(True)
            self.ffmpeg_gif_fps.setVisible(True)
            
            self.ffmpeg_gif_colors_label.setVisible(True)
            self.ffmpeg_gif_colors.setVisible(True)
            
            self.gif_dither_quality_slider.setVisible(True)
            self.gif_dither_quality_row_label.setVisible(True)
            self.gif_dither_quality_label.setVisible(True)
            
            # Variants visibility depends on toggle state
            variants_enabled = self.gif_ffmpeg_variants.isChecked()
            self.ffmpeg_gif_fps_variants_label.setVisible(variants_enabled)
            self.ffmpeg_gif_fps_variants.setVisible(variants_enabled)
            self.ffmpeg_gif_colors_variants_label.setVisible(variants_enabled)
            self.ffmpeg_gif_colors_variants.setVisible(variants_enabled)
            self.ffmpeg_gif_dither_variants_label.setVisible(variants_enabled)
            self.ffmpeg_gif_dither_variants.setVisible(variants_enabled)
            
            self.gif_size_estimate_label.setText("")

    def toggle_video_variant_mode(self, checked):
        """Toggle between single and multiple video size variant modes"""
        # Show/hide video variant controls
        self.video_size_variants.setVisible(checked)
        self.video_size_variants_label.setVisible(checked)
        
        # Auto-select first resize option if currently "No resize" when enabling variants
        if checked and self.video_resize_mode.currentText() == "No resize":
            self.video_resize_mode.setCurrentIndex(1)  # Select "By width (pixels)"
        
        # Hide single resize controls when using variants
        if checked:
            self.video_resize_value.setVisible(False)
            self.video_resize_value_label.setVisible(False)
            # Update placeholder and default values based on current mode
            current_mode = self.video_resize_mode.currentText()
            if current_mode == "By width (pixels)":
                self.video_size_variants.setPlaceholderText("e.g., 480,720,1080")
                self.video_size_variants.setText("480,720,1080")
            else:
                self.video_size_variants.setPlaceholderText("e.g., 33,66,90")
                self.video_size_variants.setText("33,66")
        else:
            # Show single resize controls based on current mode
            current_mode = self.video_resize_mode.currentText()
            if current_mode != "No resize":
                self.video_resize_value.setVisible(True)
                self.video_resize_value_label.setVisible(True)
                # Configure the control based on current mode
                if current_mode == "By width (pixels)":
                    self.video_resize_value_label.setText("Width (pixels):")
                    self.video_resize_value.setRange(1, 10000)
                    # Set a reasonable default if current value is out of range
                    current_val = self.video_resize_value.value()
                    if current_val < 1 or current_val > 10000:
                        self.video_resize_value.setValue(1920)
                elif current_mode == "By ratio (percent)":
                    self.video_resize_value_label.setText("Percentage:")
                    self.video_resize_value.setRange(1, 200)
                    # Set a reasonable default if current_val is out of range
                    current_val = self.video_resize_value.value()
                    if current_val < 1 or current_val > 200:
                        self.video_resize_value.setValue(50)
                
    def get_video_resize_values(self):
        """Get list of video resize values from input with size validation"""
        # Check if multiple resize variants are enabled
        if hasattr(self, 'multiple_video_variants') and self.multiple_video_variants.isChecked():
            resize_text = self.video_size_variants.text().strip()
            if not resize_text:
                return []
            
            # Get current mode to determine value format
            current_mode = self.video_resize_mode.currentText() if hasattr(self, 'video_resize_mode') else "By width (pixels)"
            
            sizes = []
            for value in resize_text.split(','):
                value = value.strip()
                if value:
                    try:
                        if value.endswith('%'):
                            percent = float(value[:-1])
                            if 1 <= percent <= 200:
                                sizes.append(f"{percent}%")
                        elif current_mode == "By longer edge (pixels)":
                            width = int(value)
                            if width > 0:
                                sizes.append(f"L{width}")
                        else:
                            width = int(value)
                            if width > 0:
                                sizes.append(str(width))
                    except (ValueError, TypeError):
                        continue
            return sizes
        else:
            # Single resize mode - check if resize is enabled
            if hasattr(self, 'video_resize_mode') and self.video_resize_mode.currentText() != "No resize":
                mode = self.video_resize_mode.currentText()
                value = self.video_resize_value.value()
                
                if mode == "By ratio (percent)":
                    return [f"{value}%"]
                elif mode == "By width (pixels)":
                    return [str(value)]
                elif mode == "By longer edge (pixels)":
                    return [f"L{value}"]
            
            return []
    
    def get_video_variant_values(self):
        """Get video size variant values"""
        if not (hasattr(self, 'multiple_video_variants') and self.multiple_video_variants.isChecked()):
            return []
        
        size_text = self.video_size_variants.text().strip()
        if not size_text:
            return []
        
        # Check current resize mode to determine how to interpret values
        current_mode = self.video_resize_mode.currentText() if hasattr(self, 'video_resize_mode') else "By width (pixels)"
        
        sizes = []
        for value in size_text.split(','):
            value = value.strip()
            if value:
                try:
                    if value.endswith('%'):
                        percent = float(value[:-1])
                        if 1 <= percent <= 200:
                            sizes.append(f"{percent}%")
                    else:
                        # If mode is "By ratio (percent)", treat numeric values as percentages
                        if current_mode == "By ratio (percent)":
                            percent = float(value)
                            if 1 <= percent <= 200:
                                sizes.append(f"{percent}%")
                        else:
                            # Mode is "By width (pixels)", treat as pixel width
                            width = int(value)
                            if width > 0:
                                sizes.append(str(width))
                except (ValueError, TypeError):
                    continue
        
        return sizes

    
    def toggle_video_quality_mode(self, checked):
        """Toggle between single and multiple video quality variant modes"""
        # Show/hide video quality variant controls
        self.video_quality_variants.setVisible(checked)
        self.video_quality_variants_label.setVisible(checked)
        
        # Hide single quality controls when using variants
        if checked:
            self.video_quality.setVisible(False)
            self.video_quality_label.setVisible(False)
            self.video_quality_value.setVisible(False)
        else:
            # Show single quality controls
            self.video_quality.setVisible(True)
            self.video_quality_label.setVisible(True)
            self.video_quality_value.setVisible(True)
    
    def toggle_time_cutting(self, checked):
        """Toggle time cutting controls visibility"""
        try:
            if hasattr(self, 'time_range_slider'):
                self.time_range_slider.setVisible(checked)
        except Exception as e:
            print(f"Error toggling time cutting: {e}")

    def toggle_retime(self, checked):
        """Toggle retime slider visibility"""
        try:
            if hasattr(self, 'retime_slider'):
                self.retime_slider.setVisible(checked)
            if hasattr(self, 'retime_value_label'):
                self.retime_value_label.setVisible(checked)
        except Exception as e:
            print(f"Error toggling retime: {e}")
    
    def toggle_gif_time_cutting(self, checked):
        """Toggle GIF time cutting controls visibility"""
        try:
            if hasattr(self, 'gif_time_range_slider'):
                self.gif_time_range_slider.setVisible(checked)
        except Exception as e:
            print(f"Error toggling GIF time cutting: {e}")

    def toggle_gif_retime(self, checked):
        """Toggle GIF retime slider visibility"""
        try:
            if hasattr(self, 'gif_retime_slider'):
                self.gif_retime_slider.setVisible(checked)
            if hasattr(self, 'gif_retime_value_label'):
                self.gif_retime_value_label.setVisible(checked)
        except Exception as e:
            print(f"Error toggling GIF retime: {e}")
    
    def on_video_codec_changed(self, codec):
        """Handle video codec change to show/hide bitrate and quality controls"""
        # Show quality controls for all video formats
        self.video_quality_label.setVisible(True)
        self.video_quality.setVisible(True)
        self.video_quality_value.setVisible(True)
        self.multiple_video_qualities.setVisible(True)

    
    def get_quality_values(self):
        """Get list of quality values from input"""
        if hasattr(self, 'multiple_qualities') and self.multiple_qualities.isChecked():
            quality_text = self.quality_variants.text().strip()
            if not quality_text:
                return [75]  # Default quality
            
            try:
                qualities = [int(q.strip()) for q in quality_text.split(',') if q.strip()]
                # Validate quality values (1-100)
                qualities = [max(1, min(100, q)) for q in qualities]
                return qualities if qualities else [75]
            except ValueError:
                return [75]  # Default on error
        else:
            # Single quality mode
            if hasattr(self, 'image_quality'):
                return [self.image_quality.value()]
            return [75]


    
    def toggle_gifsicle_variant_mode(self, enabled):
        """Toggle Gifsicle optimization variant inputs"""
        # Show/hide variant inputs
        self.gif_fps_variants.setVisible(enabled)
        self.gif_fps_variants_label.setVisible(enabled)
        self.gif_optimization_variants.setVisible(enabled)
        self.gif_optimization_variants_label.setVisible(enabled)
        self.gif_colors_variants.setVisible(enabled)
        self.gif_colors_variants_label.setVisible(enabled)
        self.gif_lossy_variants.setVisible(enabled)
        self.gif_lossy_variants_label.setVisible(enabled)
        
        # Hide/show single inputs and their labels (opposite of variants)
        self.gif_fps.setVisible(not enabled)
        self.gif_fps_single_label.setVisible(not enabled)
        self.gif_optimization.setVisible(not enabled)
        self.gif_optimization_single_label.setVisible(not enabled)
        self.gif_colors.setVisible(not enabled)
        self.gif_colors_single_label.setVisible(not enabled)
        self.gif_lossy.setVisible(not enabled)
        self.gif_lossy_single_label.setVisible(not enabled)
    
    def on_gif_resize_mode_changed(self, mode):
        """Handle GIF resize mode change to update default values and labels"""
        # Check if multiple variants mode is active - if so, don't show single controls
        multiple_enabled = hasattr(self, 'gif_multiple_resize') and self.gif_multiple_resize.isChecked()
        
        if mode == "No resize" or multiple_enabled:
            self.gif_resize_value.setVisible(False)
            self.gif_resize_value_label.setVisible(False)
        elif mode == "By ratio (percent)":
            self.gif_resize_value.setVisible(True)
            self.gif_resize_value_label.setVisible(True)
            self.gif_resize_value_label.setText("Percentage:")
            self.gif_resize_value.setValue(50)  # Default 50%
            self.gif_resize_value.setSuffix("")
            self.gif_resize_value.setRange(1, 200)
        elif mode == "By width (pixels)":
            self.gif_resize_value.setVisible(True)
            self.gif_resize_value_label.setVisible(True)
            self.gif_resize_value_label.setText("Width (pixels):")
            self.gif_resize_value.setValue(720)  # Default 720px
            self.gif_resize_value.setSuffix("")
            self.gif_resize_value.setRange(1, 10000)
            
        # Update variants if multiple mode is enabled
        if multiple_enabled:
            if mode == "By ratio (percent)":
                self.gif_resize_variants.setPlaceholderText("e.g., 33,66,90")
                self.gif_resize_variants.setText("33,66")
            else:
                self.gif_resize_variants.setPlaceholderText("e.g., 480,720,1080")
                self.gif_resize_variants.setText("480,720,1080")
                
    def toggle_gif_resize_variant_mode(self, checked):
        """Toggle between single and multiple GIF resize variant modes"""
        # Show/hide resize variant controls
        self.gif_resize_variants.setVisible(checked)
        self.gif_resize_variants_label.setVisible(checked)
        
        # Auto-select first resize option if currently "No resize" when enabling variants
        if checked and self.gif_resize_mode.currentText() == "No resize":
            self.gif_resize_mode.setCurrentIndex(1)  # Select "By width (pixels)"
        
        # Hide single resize controls when using variants
        if checked:
            self.gif_resize_value.setVisible(False)
            self.gif_resize_value_label.setVisible(False)
            # Update placeholder and default values based on current mode
            current_mode = self.gif_resize_mode.currentText()
            if current_mode == "By width (pixels)":
                self.gif_resize_variants.setPlaceholderText("e.g., 480,720,1080")
                self.gif_resize_variants.setText("480,720,1080")
            else:
                self.gif_resize_variants.setPlaceholderText("e.g., 33,66,90")
                self.gif_resize_variants.setText("33,66")
        else:
            # Show single resize controls based on current mode
            current_mode = self.gif_resize_mode.currentText()
            if current_mode != "No resize":
                self.gif_resize_value.setVisible(True)
                self.gif_resize_value_label.setVisible(True)
                # Configure the control based on current mode
                if current_mode == "By width (pixels)":
                    self.gif_resize_value_label.setText("Width (pixels):")
                    self.gif_resize_value.setRange(1, 10000)
                    # Set a reasonable default if current value is out of range
                    current_val = self.gif_resize_value.value()
                    if current_val < 1 or current_val > 10000:
                        self.gif_resize_value.setValue(720)
                elif current_mode == "By ratio (percent)":
                    self.gif_resize_value_label.setText("Percentage:")
                    self.gif_resize_value.setRange(1, 200)
                    # Set a reasonable default if current value is out of range
                    current_val = self.gif_resize_value.value()
                    if current_val < 1 or current_val > 200:
                        self.gif_resize_value.setValue(50)
                
    def get_gif_resize_values(self):
        """Get list of GIF resize values from input with size validation"""
        # Check if multiple resize variants are enabled
        if hasattr(self, 'gif_multiple_resize') and self.gif_multiple_resize.isChecked():
            resize_text = self.gif_resize_variants.text().strip()
            if not resize_text:
                return []
            
            # Check current resize mode to determine how to interpret values
            current_mode = self.gif_resize_mode.currentText() if hasattr(self, 'gif_resize_mode') else "By width (pixels)"
            
            sizes = []
            for value in resize_text.split(','):
                value = value.strip()
                if value:
                    try:
                        if value.endswith('%'):
                            percent = float(value[:-1])
                            if 1 <= percent <= 200:
                                sizes.append(f"{percent}%")
                        else:
                            # If mode is "By ratio (percent)", treat numeric values as percentages
                            if current_mode == "By ratio (percent)":
                                percent = float(value)
                                if 1 <= percent <= 200:
                                    sizes.append(f"{percent}%")
                            else:
                                # Mode is "By width (pixels)", treat as pixel width
                                width = int(value)
                                if width > 0:
                                    sizes.append(str(width))
                    except (ValueError, TypeError):
                        continue
            return sizes
        else:
            # Single resize mode - check if resize is enabled
            if hasattr(self, 'gif_resize_mode') and self.gif_resize_mode.currentText() != "No resize":
                mode = self.gif_resize_mode.currentText()
                value = self.gif_resize_value.value()
                
                if mode == "By ratio (percent)":
                    return [f"{value}%"]
                elif mode == "By width (pixels)":
                    # Add size validation here if needed
                    return [str(value)]
            
            return []
    
    def on_video_resize_mode_changed(self, mode):
        """Handle video resize mode change to update default values and labels"""
        # Check if multiple variants mode is active - if so, don't show single controls
        multiple_enabled = hasattr(self, 'multiple_video_variants') and self.multiple_video_variants.isChecked()
        
        if mode == "No resize" or multiple_enabled:
            self.video_resize_value.setVisible(False)
            self.video_resize_value_label.setVisible(False)
        elif mode == "By width (pixels)":
            self.video_resize_value.setVisible(True)
            self.video_resize_value_label.setVisible(True)
            self.video_resize_value_label.setText("Width (pixels):")
            self.video_resize_value.setValue(1920)  # Default 1920px
            self.video_resize_value.setSuffix("")
            self.video_resize_value.setRange(1, 10000)
        elif mode == "By longer edge (pixels)":
            self.video_resize_value.setVisible(True)
            self.video_resize_value_label.setVisible(True)
            self.video_resize_value_label.setText("Longer edge (pixels):")
            self.video_resize_value.setValue(1080)  # Default 1080px
            self.video_resize_value.setSuffix("")
            self.video_resize_value.setRange(1, 10000)
        elif mode == "By ratio (percent)":
            self.video_resize_value.setVisible(True)
            self.video_resize_value_label.setVisible(True)
            self.video_resize_value_label.setText("Percentage:")
            self.video_resize_value.setValue(50)  # Default 50%
            self.video_resize_value.setSuffix("")
            self.video_resize_value.setRange(1, 200)
            
        # Update variants if multiple mode is enabled
        if multiple_enabled:
            if mode == "By width (pixels)":
                self.video_size_variants.setPlaceholderText("e.g., 480,720,1080")
                self.video_size_variants.setText("480,720,1080")
            elif mode == "By longer edge (pixels)":
                self.video_size_variants.setPlaceholderText("e.g., 720,1080,1440")
                self.video_size_variants.setText("720,1080,1440")
            else:
                self.video_size_variants.setPlaceholderText("e.g., 33,66,90")
                self.video_size_variants.setText("33,66")
    
    def toggle_resize_mode(self, checked):
        """Toggle between single and multiple resize variant modes"""
        # Show/hide resize variant controls
        self.resize_variants.setVisible(checked)
        self.resize_variants_label.setVisible(checked)
        
        # Hide single resize controls when using variants
        if checked:
            # Auto-select first non-"No resize" option when enabling multiple variants
            if self.resize_mode.currentText() == "No resize":
                self.resize_mode.setCurrentText("By width (pixels)")
            
            self.resize_value.setVisible(False)
            self.resize_value_label.setVisible(False)
            # Update placeholder and default values based on current mode
            current_mode = self.resize_mode.currentText()
            if current_mode == "By width (pixels)":
                self.resize_variants.setPlaceholderText("e.g., 480,720,1080")
                self.resize_variants.setText("480,720,1080")
            else:
                self.resize_variants.setPlaceholderText("e.g., 33,66,90")
                self.resize_variants.setText("33,66")
        else:
            # Show single resize controls based on current mode
            current_mode = self.resize_mode.currentText()
            if current_mode != "No resize":
                self.resize_value.setVisible(True)
                self.resize_value_label.setVisible(True)
                # Configure the control based on current mode
                if current_mode == "By width (pixels)":
                    self.resize_value_label.setText("Width (pixels):")
                    self.resize_value.setRange(1, 10000)
                    self.resize_value.setValue(720)  # Always set default
                elif current_mode == "By ratio (percent)":
                    self.resize_value_label.setText("Percentage:")
                    self.resize_value.setRange(1, 200)
                    self.resize_value.setValue(50)  # Always set default
        
    def on_resize_mode_changed(self, mode):
        """Handle resize mode change to update default values and labels"""
        # Check if multiple variants mode is active - if so, don't show single controls
        multiple_enabled = hasattr(self, 'multiple_resize') and self.multiple_resize.isChecked()
        
        if mode == "No resize" or multiple_enabled:
            self.resize_value.setVisible(False)
            self.resize_value_label.setVisible(False)
        elif mode == "By width (pixels)":
            self.resize_value.setVisible(True)
            self.resize_value_label.setVisible(True)
            self.resize_value_label.setText("Width (pixels):")
            self.resize_value.setValue(720)  # Always use default value
            self.resize_value.setSuffix("")
            self.resize_value.setRange(1, 10000)
        elif mode == "By longer edge (pixels)":
            self.resize_value.setVisible(True)
            self.resize_value_label.setVisible(True)
            self.resize_value_label.setText("Longer edge (pixels):")
            self.resize_value.setValue(960)  # Always use default value
            self.resize_value.setSuffix("")
            self.resize_value.setRange(1, 10000)
        elif mode == "By ratio (percent)":
            self.resize_value.setVisible(True)
            self.resize_value_label.setVisible(True)
            self.resize_value_label.setText("Percentage:")
            self.resize_value.setValue(50)  # Always use default value
            self.resize_value.setSuffix("")
            self.resize_value.setRange(1, 200)
            
        # Update variants if multiple mode is enabled
        if multiple_enabled:
            if mode == "By width (pixels)":
                self.resize_variants.setPlaceholderText("e.g., 720,1280,1920")
                self.resize_variants.setText("720,1280,1920")
            elif mode == "By longer edge (pixels)":
                self.resize_variants.setPlaceholderText("e.g., 720,960,1080")
                self.resize_variants.setText("720,960,1080")
            else:
                self.resize_variants.setPlaceholderText("e.g., 33,66,90")
                self.resize_variants.setText("33,66")
            
    def get_resize_values(self):
        """Get list of resize values from input"""
        # Check if multiple resize variants are enabled
        if hasattr(self, 'multiple_resize') and self.multiple_resize.isChecked():
            resize_text = self.resize_variants.text().strip()
            if not resize_text:
                return []
            
            # Check current resize mode to determine how to interpret values
            current_mode = self.resize_mode.currentText() if hasattr(self, 'resize_mode') else "By width (pixels)"
            
            sizes = []
            for value in resize_text.split(','):
                value = value.strip()
                if value:
                    try:
                        if value.endswith('%'):
                            percent = float(value[:-1])
                            if 1 <= percent <= 200:
                                sizes.append(f"{percent}%")
                        else:
                            # If mode is "By ratio (percent)", treat numeric values as percentages
                            if current_mode == "By ratio (percent)":
                                percent = float(value)
                                if 1 <= percent <= 200:
                                    sizes.append(f"{percent}%")
                            elif current_mode == "By longer edge (pixels)":
                                # Mode is "By longer edge (pixels)", prefix with "L"
                                width = int(value)
                                if width > 0:
                                    sizes.append(f"L{width}")
                            else:
                                # Mode is "By width (pixels)", treat as pixel width
                                width = int(value)
                                if width > 0:
                                    sizes.append(str(width))
                    except (ValueError, TypeError):
                        continue
            return sizes
        else:
            # Single resize mode - check if resize is enabled
            if hasattr(self, 'resize_mode') and self.resize_mode.currentText() != "No resize":
                mode = self.resize_mode.currentText()
                value = self.resize_value.value()
                
                if mode == "By ratio (percent)":
                    return [f"{value}%"]
                elif mode == "By width (pixels)":
                    return [str(value)]
                elif mode == "By longer edge (pixels)":
                    return [f"L{value}"]
            
            return []
            
    def on_gif_resize_mode_changed(self, mode):
        """Handle GIF resize mode change to update default values and labels"""
        # Check if multiple variants mode is active - if so, don't show single controls
        multiple_enabled = hasattr(self, 'gif_multiple_resize') and self.gif_multiple_resize.isChecked()
        
        if mode == "No resize" or multiple_enabled:
            self.gif_resize_value.setVisible(False)
            self.gif_resize_value_label.setVisible(False)
        elif mode == "By width (pixels)":
            self.gif_resize_value.setVisible(True)
            self.gif_resize_value_label.setVisible(True)
            self.gif_resize_value_label.setText("Width (pixels):")
            self.gif_resize_value.setValue(720)  # Default 720px
            self.gif_resize_value.setSuffix("")
            self.gif_resize_value.setRange(1, 10000)
        elif mode == "By longer edge (pixels)":
            self.gif_resize_value.setVisible(True)
            self.gif_resize_value_label.setVisible(True)
            self.gif_resize_value_label.setText("Longer edge (pixels):")
            self.gif_resize_value.setValue(720)  # Default 720px
            self.gif_resize_value.setSuffix("")
            self.gif_resize_value.setRange(1, 10000)
        elif mode == "By ratio (percent)":
            self.gif_resize_value.setVisible(True)
            self.gif_resize_value_label.setVisible(True)
            self.gif_resize_value_label.setText("Percentage:")
            self.gif_resize_value.setValue(50)  # Default 50%
            self.gif_resize_value.setSuffix("")
            self.gif_resize_value.setRange(1, 200)
            
        # Update variants if multiple mode is enabled
        if multiple_enabled:
            if mode == "By width (pixels)":
                self.gif_resize_variants.setPlaceholderText("e.g., 480,720,1080")
                self.gif_resize_variants.setText("480,720,1080")
            elif mode == "By longer edge (pixels)":
                self.gif_resize_variants.setPlaceholderText("e.g., 480,720,1080")
                self.gif_resize_variants.setText("480,720,1080")
            else:
                self.gif_resize_variants.setPlaceholderText("e.g., 33,66,90")
                self.gif_resize_variants.setText("33,66")
                
    def get_gif_resize_values(self):
        """Get list of GIF resize values from input with size validation"""
        # Check if multiple resize variants are enabled
        if hasattr(self, 'gif_multiple_resize') and self.gif_multiple_resize.isChecked():
            resize_text = self.gif_resize_variants.text().strip()
            if not resize_text:
                return []
            
            # Check current resize mode to determine how to interpret values
            current_mode = self.gif_resize_mode.currentText() if hasattr(self, 'gif_resize_mode') else "By width (pixels)"
            
            sizes = []
            for value in resize_text.split(','):
                value = value.strip()
                if value:
                    try:
                        if value.endswith('%'):
                            percent = float(value[:-1])
                            if 1 <= percent <= 200:
                                sizes.append(f"{percent}%")
                        else:
                            # If mode is "By ratio (percent)", treat numeric values as percentages
                            if current_mode == "By ratio (percent)":
                                percent = float(value)
                                if 1 <= percent <= 200:
                                    sizes.append(f"{percent}%")
                            elif current_mode == "By longer edge (pixels)":
                                # Mode is "By longer edge (pixels)", prefix with "L"
                                width = int(value)
                                if width > 0:
                                    sizes.append(f"L{width}")
                            else:
                                # Mode is "By width (pixels)", treat as pixel width
                                width = int(value)
                                if width > 0:
                                    sizes.append(str(width))
                    except (ValueError, TypeError):
                        continue
            return sizes
        else:
            # Single resize mode - check if resize is enabled
            if hasattr(self, 'gif_resize_mode') and self.gif_resize_mode.currentText() != "No resize":
                mode = self.gif_resize_mode.currentText()
                value = self.gif_resize_value.value()
                
                if mode == "By ratio (percent)":
                    return [f"{value}%"]
                elif mode == "By width (pixels)":
                    # Add size validation here if needed
                    return [str(value)]
                elif mode == "By longer edge (pixels)":
                    return [f"L{value}"]
            
            return []
    

    def validate_fps_variants(self):
        """Validate FPS variants input range (1-240)"""
        text = self.gif_fps_variants.text().strip()
        if not text:
            return
            
        try:
            values = [int(val.strip()) for val in text.split(',') if val.strip()]
            invalid_values = [val for val in values if val < 1 or val > 240]
            
            if invalid_values:
                from PyQt6.QtWidgets import QMessageBox
                msg_box = QMessageBox(QMessageBox.Icon.Warning, "Invalid FPS Values", 
                                    f"FPS values must be between 1 and 240.\n\nInvalid values found: {invalid_values}\n\nValid range: 1 to 240\n\nCommon FPS values:\n10-15 = Low motion\n24-30 = Standard motion\n60+ = High motion", 
                                    parent=self)
                # Apply dark mode styling - get parent window's theme manager
                try:
                    main_window = self
                    while main_window.parent():
                        main_window = main_window.parent()
                    if hasattr(main_window, 'theme_manager'):
                        msg_box.setStyleSheet(main_window.theme_manager.get_dialog_styles())
                except:
                    pass
                msg_box.exec()
                # Reset to valid default
                self.gif_fps_variants.setText("10,15,30")
        except ValueError:
            # Ignore non-numeric input during typing
            pass
            
    def validate_colors_variants(self):
        """Validate Colors variants input range (2-256)"""
        text = self.gif_colors_variants.text().strip()
        if not text:
            return
            
        try:
            values = [int(val.strip()) for val in text.split(',') if val.strip()]
            invalid_values = [val for val in values if val < 2 or val > 256]
            
            if invalid_values:
                from PyQt6.QtWidgets import QMessageBox
                msg_box = QMessageBox(QMessageBox.Icon.Warning, "Invalid Colors Values", 
                                    f"Colors values must be between 2 and 256.\n\nInvalid values found: {invalid_values}\n\nValid range: 2 to 256\n\nColor recommendations:\n2-16 = Very low quality\n32-64 = Low quality\n128-256 = High quality", 
                                    parent=self)
                # Apply dark mode styling - get parent window's theme manager
                try:
                    main_window = self
                    while main_window.parent():
                        main_window = main_window.parent()
                    if hasattr(main_window, 'theme_manager'):
                        msg_box.setStyleSheet(main_window.theme_manager.get_dialog_styles())
                except:
                    pass
                msg_box.exec()
                # Reset to valid default
                self.gif_colors_variants.setText("64,128,256")
        except ValueError:
            # Ignore non-numeric input during typing
            pass
            


    def validate_video_quality_variants(self):
        """Validate video quality variants input range (0-100)"""
        text = self.video_quality_variants.text().strip()
        if not text:
            return
            
        try:
            values = [int(val.strip()) for val in text.split(',') if val.strip()]
            invalid_values = [val for val in values if val < 0 or val > 100]
            
            if invalid_values:
                from PyQt6.QtWidgets import QMessageBox
                msg_box = QMessageBox(QMessageBox.Icon.Warning, "Invalid Quality Values", 
                                    f"Quality values must be between 0 and 100.\n\nInvalid values found: {invalid_values}\n\nValid range: 0 to 100\n\nQuality levels:\n0 = Lossless\n25-40 = High quality\n50-70 = Good quality (recommended)\n80-100 = Low quality", 
                                    parent=self)
                # Apply dark mode styling - get parent window's theme manager
                try:
                    main_window = self
                    while main_window.parent():
                        main_window = main_window.parent()
                    if hasattr(main_window, 'theme_manager'):
                        msg_box.setStyleSheet(main_window.theme_manager.get_dialog_styles())
                except:
                    pass
                msg_box.exec()
                # Reset to valid default
                self.video_quality_variants.setText("15,23,31")
        except ValueError:
            # Ignore non-numeric input during typing
            pass










