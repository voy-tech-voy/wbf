"""
VideoTab - Video conversion tab component.

Extracted from CommandPanel as part of the Mediator-Shell refactoring.
This tab handles video codec, quality, resize, rotation, and time settings.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, 
    QLineEdit, QSizePolicy
)
from PyQt6.QtCore import Qt

from client.gui.tabs.base_tab import BaseTab
from client.gui.command_group import CommandGroup
from client.gui.custom_spinbox import CustomSpinBox
from client.gui.custom_widgets import (
    CustomComboBox, RotationButtonRow, ThemedCheckBox,
    CustomTargetSizeSpinBox, VideoCodecSelector, TimeRangeSlider
)
from client.gui.theme import get_combobox_style

COMBOBOX_STYLE = get_combobox_style(True)  # Default dark mode


class VideoTab(BaseTab):
    """
    Video conversion settings tab.
    
    Provides controls for:
    - Output codec (MP4/H.264, WebM/VP9, etc.)
    - Quality settings (CRF slider or multiple variants)
    - Max file size targeting
    - Resize options (by width, longer edge, ratio)
    - Rotation angle
    - Time cutting (trim start/end)
    - Retiming (speed change)
    """
    
    def __init__(self, parent=None, focus_callback=None, is_dark_mode=True):
        """
        Initialize VideoTab.
        
        Args:
            parent: Parent widget
            focus_callback: Callback for focus management
            is_dark_mode: Initial theme state
        """
        self._focus_callback = focus_callback or (lambda: None)
        self._initial_is_dark = is_dark_mode
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Create the video tab UI elements."""
        layout = self._layout
        layout.setSpacing(8)
        
        # ============================================================
        # SETTINGS FOLDER (Top)
        # ============================================================
        settings_row = QWidget()
        settings_row.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        settings_h = QHBoxLayout(settings_row)
        settings_h.setContentsMargins(0, 0, 0, 0)
        settings_h.setSpacing(0)
        
        # Settings CommandGroup
        self.codec_group = CommandGroup("")
        self.codec_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.codec_group.get_content_layout().setContentsMargins(16, 16, 16, 16)
        self.codec_group.setMinimumHeight(180)
        settings_h.addWidget(self.codec_group, 1)
        
        layout.addWidget(settings_row)
        
        # --- Codec Selection ---
        self.codec = VideoCodecSelector()
        self.codec.codecChanged.connect(self._on_codec_changed)
        self.codec_group.get_content_layout().insertRow(0, self.codec)
        
        # --- Max Size (for Max Size mode) ---
        self.max_size_spinbox = CustomTargetSizeSpinBox(
            default_value=1.0,
            on_enter_callback=self._focus_callback
        )
        self.max_size_spinbox.setToolTip("Target maximum file size in megabytes")
        self.max_size_spinbox.setVisible(False)
        self.max_size_label = QLabel("Max Size")
        self.max_size_label.setVisible(False)
        self.codec_group.add_row(self.max_size_label, self.max_size_spinbox)
        
        # --- Auto-resize checkbox ---
        self.auto_resize_checkbox = ThemedCheckBox("Auto-resize")
        self.auto_resize_checkbox.setChecked(True)
        self.auto_resize_checkbox.setToolTip(
            "Change the resolution in pixels (width×height) to match desired file size in MB."
        )
        self.auto_resize_checkbox.setVisible(False)
        self.codec_group.add_row(self.auto_resize_checkbox)
        
        # --- Multiple qualities ---
        self.multiple_qualities = ThemedCheckBox("Multiple quality variants")
        self.multiple_qualities.toggled.connect(self._toggle_quality_mode)
        self.codec_group.add_row(self.multiple_qualities)
        
        # --- Quality slider ---
        self.quality = QSlider(Qt.Orientation.Horizontal)
        self.quality.setRange(0, 100)
        self.quality.setValue(30)
        self.quality.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.quality.setTickInterval(10)
        self.quality.setToolTip("Quality: 0=lossless, 100=worst quality\nRecommended: 30-50 for WebM")
        self.quality_label = QLabel("Quality")
        self.quality_value = QLabel("30")
        self.quality.valueChanged.connect(lambda v: self.quality_value.setText(str(v)))
        
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(self.quality)
        quality_layout.addWidget(self.quality_value)
        self.codec_group.add_row(self.quality_label, quality_layout)
        
        # --- Quality variants ---
        self.quality_variants = QLineEdit()
        self.quality_variants.setPlaceholderText("e.g., 25,40,70 (quality values 0-100)")
        self.quality_variants.setText("15,23,31")
        self.quality_variants.setVisible(False)
        self.quality_variants_label = QLabel("Quality variants")
        self.quality_variants_label.setVisible(False)
        self.codec_group.add_row(self.quality_variants_label, self.quality_variants)
        
        # ============================================================
        # TRANSFORM FOLDER (Bottom)
        # ============================================================
        transform_row = QWidget()
        transform_row.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        transform_h = QHBoxLayout(transform_row)
        transform_h.setContentsMargins(0, 0, 0, 0)
        transform_h.setSpacing(0)
        
        # Transform CommandGroup
        self.transform_group = CommandGroup("")
        self.transform_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.transform_group.get_content_layout().setContentsMargins(16, 16, 16, 16)
        self.transform_group.get_content_layout().setVerticalSpacing(12)
        self.transform_group.setFixedHeight(198)
        transform_h.addWidget(self.transform_group, 1)
        
        layout.addWidget(transform_row)
        
        # === RESIZE SECTION ===
        self.resize_container = QWidget()
        resize_layout = QVBoxLayout(self.resize_container)
        resize_layout.setContentsMargins(0, 0, 0, 0)
        resize_layout.setSpacing(8)
        
        self.resize_mode = CustomComboBox()
        self.resize_mode.addItems(["No resize", "By width (pixels)", "By longer edge (pixels)", "By ratio (percent)"])
        self.resize_mode.setStyleSheet(COMBOBOX_STYLE)
        self.resize_mode.currentTextChanged.connect(self._on_resize_mode_changed)
        resize_layout.addWidget(self.resize_mode)
        
        self.multiple_variants = ThemedCheckBox("Multiple size variants")
        self.multiple_variants.toggled.connect(self._toggle_variant_mode)
        resize_layout.addWidget(self.multiple_variants)
        
        # Single value row
        single_val_row = QHBoxLayout()
        self.resize_value_label = QLabel("Width (pixels)")
        self.resize_value = CustomSpinBox(on_enter_callback=self._focus_callback)
        self.resize_value.setRange(1, 10000)
        self.resize_value.setValue(720)
        single_val_row.addWidget(self.resize_value_label)
        single_val_row.addWidget(self.resize_value)
        resize_layout.addLayout(single_val_row)
        
        # Variants row
        variants_row = QHBoxLayout()
        self.size_variants_label = QLabel("Size variants")
        self.size_variants = QLineEdit()
        self.size_variants.setPlaceholderText("e.g., 480,720,1080 or 25%,50%,75%")
        self.size_variants.setText("480,720,1280")
        variants_row.addWidget(self.size_variants_label)
        variants_row.addWidget(self.size_variants)
        resize_layout.addLayout(variants_row)
        
        # Initial visibility
        self.resize_value.setVisible(False)
        self.resize_value_label.setVisible(False)
        self.size_variants.setVisible(False)
        self.size_variants_label.setVisible(False)
        
        self.transform_group.add_row(self.resize_container)
        
        # === ROTATION SECTION ===
        self.rotate_container = QWidget()
        rotate_layout = QVBoxLayout(self.rotate_container)
        rotate_layout.setContentsMargins(0, 0, 0, 0)
        
        self.rotation_angle = RotationButtonRow()
        rotate_layout.addWidget(self.rotation_angle)
        
        self.transform_group.add_row(self.rotate_container)
        
        # === TIME SECTION ===
        self.time_container = QWidget()
        time_layout = QVBoxLayout(self.time_container)
        time_layout.setContentsMargins(0, 0, 0, 0)
        time_layout.setSpacing(12)
        
        # Time range row
        self.enable_time_cutting = ThemedCheckBox("Time range")
        self.enable_time_cutting.toggled.connect(self._toggle_time_cutting)
        
        self.time_range_slider = TimeRangeSlider(is_dark_mode=self._initial_is_dark)
        self.time_range_slider.setRange(0.0, 1.0)
        self.time_range_slider.setStartValue(0.0)
        self.time_range_slider.setEndValue(1.0)
        self.time_range_slider.setToolTip("Drag handles to set start/end times (0%=beginning, 100%=end)")
        self.time_range_slider.setVisible(False)
        
        time_range_row = QHBoxLayout()
        time_range_row.addWidget(self.enable_time_cutting)
        time_range_row.addSpacing(8)
        time_range_row.addWidget(self.time_range_slider, 1)
        time_layout.addLayout(time_range_row)
        
        # Retime row
        self.enable_retime = ThemedCheckBox("Retime")
        self.enable_retime.toggled.connect(self._toggle_retime)
        
        self.retime_slider = QSlider(Qt.Orientation.Horizontal)
        self.retime_slider.setRange(10, 30)
        self.retime_slider.setValue(10)
        self.retime_slider.setSingleStep(1)
        self.retime_slider.setVisible(False)
        self.retime_value_label = QLabel("1.0x")
        self.retime_value_label.setVisible(False)
        self.retime_slider.valueChanged.connect(lambda v: self.retime_value_label.setText(f"{v/10:.1f}x"))
        
        retime_row = QHBoxLayout()
        retime_row.addWidget(self.enable_retime)
        retime_row.addSpacing(8)
        retime_row.addWidget(self.retime_slider, 1)
        retime_row.addWidget(self.retime_value_label)
        time_layout.addLayout(retime_row)
        
        self.transform_group.add_row(self.time_container)
        
        # Initially show resize, hide rotate and time
        self.rotate_container.setVisible(False)
        self.time_container.setVisible(False)
    
    def get_params(self) -> dict:
        """Collect video conversion parameters from UI."""
        params = {
            'type': 'video',
            'codec': self.codec.currentText(),
            'quality': self.quality.value(),
            'multiple_qualities': self.multiple_qualities.isChecked(),
            'quality_variants': self._parse_variants(self.quality_variants.text()),
            'max_size_mb': self.max_size_spinbox.value() if self.max_size_spinbox.isVisible() else None,
            'auto_resize': self.auto_resize_checkbox.isChecked(),
            'resize_mode': self.resize_mode.currentText(),
            'resize_value': self.resize_value.value(),
            'multiple_variants': self.multiple_variants.isChecked(),
            'size_variants': self._parse_variants(self.size_variants.text()),
            'rotation_angle': self.rotation_angle.currentAngle(),
            'enable_time_cutting': self.enable_time_cutting.isChecked(),
            'time_start': self.time_range_slider.startValue() if self.enable_time_cutting.isChecked() else 0.0,
            'time_end': self.time_range_slider.endValue() if self.enable_time_cutting.isChecked() else 1.0,
            'retime_enabled': self.enable_retime.isChecked(),
            'retime_speed': self.retime_slider.value() / 10.0 if self.enable_retime.isChecked() else 1.0,
        }
        return params
    
    def update_theme(self, is_dark: bool):
        """Apply theme styling to all elements."""
        self._is_dark_theme = is_dark
        global COMBOBOX_STYLE
        COMBOBOX_STYLE = get_combobox_style(is_dark)
        self.resize_mode.setStyleSheet(COMBOBOX_STYLE)
        
        # Update checkboxes
        for checkbox in [self.multiple_qualities, self.auto_resize_checkbox, 
                        self.multiple_variants, self.enable_time_cutting, self.enable_retime]:
            if hasattr(checkbox, 'update_theme'):
                checkbox.update_theme(is_dark)
        
        # Update time range slider
        if hasattr(self.time_range_slider, 'update_theme'):
            self.time_range_slider.update_theme(is_dark)
    
    def set_mode(self, mode: str):
        """Set the size mode (Max Size, Presets, Manual)."""
        is_max_size = (mode == "Max Size")
        is_manual = (mode == "Manual")
        
        # Max size controls
        self.max_size_label.setVisible(is_max_size)
        self.max_size_spinbox.setVisible(is_max_size)
        self.auto_resize_checkbox.setVisible(is_max_size)
        
        # Quality controls
        show_quality = is_max_size or is_manual
        self.quality_label.setVisible(show_quality and not self.multiple_qualities.isChecked())
        self.quality.setVisible(show_quality and not self.multiple_qualities.isChecked())
        self.quality_value.setVisible(show_quality and not self.multiple_qualities.isChecked())
    
    def set_transform_mode(self, mode: str):
        """Set which transform section is visible (resize, rotate, or time)."""
        self.resize_container.setVisible(mode == 'resize')
        self.rotate_container.setVisible(mode == 'rotate')
        self.time_container.setVisible(mode == 'time')
    
    # -------------------------------------------------------------------------
    # PRIVATE METHODS
    # -------------------------------------------------------------------------
    
    def _on_codec_changed(self, codec: str):
        """Handle codec selection change."""
        # Could adjust quality ranges based on codec
        self._notify_param_change()
    
    def _toggle_quality_mode(self, multiple: bool):
        """Toggle between single quality slider and multiple variants."""
        self.quality.setVisible(not multiple)
        self.quality_value.setVisible(not multiple)
        self.quality_label.setVisible(not multiple)
        self.quality_variants.setVisible(multiple)
        self.quality_variants_label.setVisible(multiple)
        self._notify_param_change()
    
    def _toggle_variant_mode(self, multiple: bool):
        """Toggle between single resize value and multiple variants."""
        self.resize_value.setVisible(not multiple)
        self.resize_value_label.setVisible(not multiple)
        self.size_variants.setVisible(multiple)
        self.size_variants_label.setVisible(multiple)
        self._notify_param_change()
    
    def _on_resize_mode_changed(self, mode: str):
        """Handle resize mode dropdown change."""
        show_value = (mode != "No resize")
        
        if self.multiple_variants.isChecked():
            self.size_variants.setVisible(show_value)
            self.size_variants_label.setVisible(show_value)
            self.resize_value.setVisible(False)
            self.resize_value_label.setVisible(False)
        else:
            self.resize_value.setVisible(show_value)
            self.resize_value_label.setVisible(show_value)
            self.size_variants.setVisible(False)
            self.size_variants_label.setVisible(False)
        
        # Update label based on mode
        if "width" in mode.lower():
            self.resize_value_label.setText("Width (pixels)")
        elif "longer" in mode.lower():
            self.resize_value_label.setText("Longer edge (pixels)")
        elif "ratio" in mode.lower():
            self.resize_value_label.setText("Ratio (%)")
        
        self._notify_param_change()
    
    def _toggle_time_cutting(self, enabled: bool):
        """Toggle time range slider visibility."""
        self.time_range_slider.setVisible(enabled)
        self._notify_param_change()
    
    def _toggle_retime(self, enabled: bool):
        """Toggle retime slider visibility."""
        self.retime_slider.setVisible(enabled)
        self.retime_value_label.setVisible(enabled)
        self._notify_param_change()
    
    def _parse_variants(self, text: str) -> list:
        """Parse comma-separated variant values."""
        try:
            return [v.strip() for v in text.split(',') if v.strip()]
        except:
            return []
