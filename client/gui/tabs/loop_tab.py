"""
LoopTab - Loop conversion tab component (GIF/WebM).

Extracted from CommandPanel as part of the Mediator-Shell refactoring.
This tab handles GIF and WebM loop conversion with format-specific settings.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, 
    QLineEdit, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal

from client.gui.tabs.base_tab import BaseTab
from client.gui.command_group import CommandGroup
from client.gui.custom_spinbox import CustomSpinBox
from client.gui.custom_widgets import (
    CustomComboBox, RotationButtonRow, ThemedCheckBox,
    CustomTargetSizeSpinBox, LoopFormatSelector, TimeRangeSlider
)
from client.gui.command_panel import get_combobox_style

COMBOBOX_STYLE = get_combobox_style(True)


class LoopTab(BaseTab):
    """
    Loop conversion settings tab (GIF and WebM).
    
    Provides controls for:
    - Format selection (GIF vs WebM)
    - GIF-specific: FPS, colors, dither quality, blur
    - WebM-specific: quality slider/variants
    - Resize options
    - Rotation angle
    - Time cutting and retiming
    """
    
    # Signal when format changes (GIF <-> WebM)
    format_changed = pyqtSignal(str)
    
    def __init__(self, parent=None, focus_callback=None, is_dark_mode=True):
        """
        Initialize LoopTab.
        
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
        """Create the loop tab UI elements."""
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
        
        self.settings_group = CommandGroup("")
        self.settings_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.settings_group.get_content_layout().setContentsMargins(16, 16, 16, 16)
        self.settings_group.setMinimumHeight(180)
        settings_h.addWidget(self.settings_group, 1)
        
        layout.addWidget(settings_row)
        
        # --- Format Selector (GIF/WebM) ---
        self.format_selector = LoopFormatSelector()
        self.format_selector.formatChanged.connect(self._on_format_changed)
        self.settings_group.get_content_layout().insertRow(0, self.format_selector)
        
        # --- Max Size ---
        self.max_size_spinbox = CustomTargetSizeSpinBox(
            default_value=2.0,
            on_enter_callback=self._focus_callback
        )
        self.max_size_spinbox.setToolTip("Target maximum file size in megabytes")
        self.max_size_spinbox.setVisible(False)
        self.max_size_label = QLabel("Max Size")
        self.max_size_label.setVisible(False)
        self.settings_group.add_row(self.max_size_label, self.max_size_spinbox)
        
        # --- Auto-resize ---
        self.auto_resize_checkbox = ThemedCheckBox("Auto-resize")
        self.auto_resize_checkbox.setChecked(True)
        self.auto_resize_checkbox.setVisible(False)
        self.settings_group.add_row(self.auto_resize_checkbox)
        
        # ============ GIF-SPECIFIC CONTROLS ============
        
        # Multiple variants toggle
        self.gif_variants_checkbox = ThemedCheckBox("Multiple Variants (FPS, Colors, Qualities)")
        self.gif_variants_checkbox.toggled.connect(self._toggle_gif_variants)
        self.settings_group.add_row(self.gif_variants_checkbox)
        
        # FPS
        self.gif_fps = CustomComboBox()
        self.gif_fps.addItems(["10", "12", "15", "18", "24"])
        self.gif_fps.setCurrentText("15")
        self.gif_fps_label = QLabel("FPS")
        self.settings_group.add_row(self.gif_fps_label, self.gif_fps)
        
        # FPS Variants
        self.gif_fps_variants = QLineEdit()
        self.gif_fps_variants.setPlaceholderText("e.g., 10,15,24")
        self.gif_fps_variants.setVisible(False)
        self.gif_fps_variants_label = QLabel("FPS variants")
        self.gif_fps_variants_label.setVisible(False)
        self.settings_group.add_row(self.gif_fps_variants_label, self.gif_fps_variants)
        
        # Colors
        self.gif_colors = CustomComboBox()
        self.gif_colors.addItems(["8", "16", "32", "64", "128", "256"])
        self.gif_colors.setCurrentText("256")
        self.gif_colors_label = QLabel("Colors")
        self.settings_group.add_row(self.gif_colors_label, self.gif_colors)
        
        # Colors Variants
        self.gif_colors_variants = QLineEdit()
        self.gif_colors_variants.setPlaceholderText("e.g., 64,128,256")
        self.gif_colors_variants.setVisible(False)
        self.gif_colors_variants_label = QLabel("Colors variants")
        self.gif_colors_variants_label.setVisible(False)
        self.settings_group.add_row(self.gif_colors_variants_label, self.gif_colors_variants)
        
        # Dither Quality
        self.gif_dither_slider = QSlider(Qt.Orientation.Horizontal)
        self.gif_dither_slider.setRange(0, 5)
        self.gif_dither_slider.setValue(3)
        self.gif_dither_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.gif_dither_slider.setTickInterval(1)
        self.gif_dither_value = QLabel("3")
        self.gif_dither_slider.valueChanged.connect(lambda v: self.gif_dither_value.setText(str(v)))
        self.gif_dither_label = QLabel("Quality")
        
        dither_layout = QHBoxLayout()
        dither_layout.addWidget(self.gif_dither_slider)
        dither_layout.addWidget(self.gif_dither_value)
        self.settings_group.add_row(self.gif_dither_label, dither_layout)
        
        # Dither Variants
        self.gif_dither_variants = QLineEdit()
        self.gif_dither_variants.setPlaceholderText("e.g., 0,3,5")
        self.gif_dither_variants.setVisible(False)
        self.gif_dither_variants_label = QLabel("Quality variants (0-5)")
        self.gif_dither_variants_label.setVisible(False)
        self.settings_group.add_row(self.gif_dither_variants_label, self.gif_dither_variants)
        
        # Blur
        self.gif_blur = ThemedCheckBox("Reduce banding")
        self.settings_group.add_row(self.gif_blur)
        
        # ============ WEBM-SPECIFIC CONTROLS ============
        
        # WebM variants toggle
        self.webm_variants_checkbox = ThemedCheckBox("Multiple quality variants")
        self.webm_variants_checkbox.toggled.connect(self._toggle_webm_variants)
        self.webm_variants_checkbox.setVisible(False)
        self.settings_group.add_row(self.webm_variants_checkbox)
        
        # WebM Quality
        self.webm_quality = QSlider(Qt.Orientation.Horizontal)
        self.webm_quality.setRange(0, 63)
        self.webm_quality.setValue(30)
        self.webm_quality.setVisible(False)
        self.webm_quality_value = QLabel("30")
        self.webm_quality_value.setVisible(False)
        self.webm_quality.valueChanged.connect(lambda v: self.webm_quality_value.setText(str(v)))
        self.webm_quality_label = QLabel("Quality")
        self.webm_quality_label.setVisible(False)
        
        webm_quality_layout = QHBoxLayout()
        webm_quality_layout.addWidget(self.webm_quality)
        webm_quality_layout.addWidget(self.webm_quality_value)
        self.settings_group.add_row(self.webm_quality_label, webm_quality_layout)
        
        # WebM Quality Variants
        self.webm_quality_variants = QLineEdit()
        self.webm_quality_variants.setPlaceholderText("e.g., 20,30,40")
        self.webm_quality_variants.setVisible(False)
        self.webm_quality_variants_label = QLabel("Quality variants")
        self.webm_quality_variants_label.setVisible(False)
        self.settings_group.add_row(self.webm_quality_variants_label, self.webm_quality_variants)
        
        # ============================================================
        # TRANSFORM FOLDER (Bottom)
        # ============================================================
        transform_row = QWidget()
        transform_row.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        transform_h = QHBoxLayout(transform_row)
        transform_h.setContentsMargins(0, 0, 0, 0)
        transform_h.setSpacing(0)
        
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
        
        self.multiple_resize = ThemedCheckBox("Multiple size variants")
        self.multiple_resize.toggled.connect(self._toggle_resize_mode)
        resize_layout.addWidget(self.multiple_resize)
        
        single_val_row = QHBoxLayout()
        self.resize_value_label = QLabel("Width (pixels)")
        self.resize_value = CustomSpinBox(on_enter_callback=self._focus_callback)
        self.resize_value.setRange(1, 10000)
        self.resize_value.setValue(720)
        single_val_row.addWidget(self.resize_value_label)
        single_val_row.addWidget(self.resize_value)
        resize_layout.addLayout(single_val_row)
        
        variants_row = QHBoxLayout()
        self.resize_variants_label = QLabel("Size variants")
        self.resize_variants = QLineEdit()
        self.resize_variants.setPlaceholderText("e.g., 480,720,1080")
        self.resize_variants.setText("480,720,1080")
        variants_row.addWidget(self.resize_variants_label)
        variants_row.addWidget(self.resize_variants)
        resize_layout.addLayout(variants_row)
        
        self.resize_value.setVisible(False)
        self.resize_value_label.setVisible(False)
        self.resize_variants.setVisible(False)
        self.resize_variants_label.setVisible(False)
        
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
        
        self.enable_time_cutting = ThemedCheckBox("Time range")
        self.enable_time_cutting.toggled.connect(self._toggle_time_cutting)
        
        self.time_range_slider = TimeRangeSlider(is_dark_mode=self._initial_is_dark)
        self.time_range_slider.setRange(0.0, 1.0)
        self.time_range_slider.setStartValue(0.0)
        self.time_range_slider.setEndValue(1.0)
        self.time_range_slider.setVisible(False)
        
        time_row = QHBoxLayout()
        time_row.addWidget(self.enable_time_cutting)
        time_row.addSpacing(8)
        time_row.addWidget(self.time_range_slider, 1)
        time_layout.addLayout(time_row)
        
        self.enable_retime = ThemedCheckBox("Retime")
        self.enable_retime.toggled.connect(self._toggle_retime)
        
        self.retime_slider = QSlider(Qt.Orientation.Horizontal)
        self.retime_slider.setRange(10, 30)
        self.retime_slider.setValue(10)
        self.retime_slider.setVisible(False)
        self.retime_value_label = QLabel("1.0x")
        self.retime_value_label.setVisible(False)
        self.retime_slider.valueChanged.connect(lambda v: self.retime_value_label.setText(f"{v/10:.1f}x"))
        
        retime_row = QHBoxLayout()
        retime_row.addWidget(self.enable_retime)
        retime_row.addWidget(self.retime_slider)
        retime_row.addWidget(self.retime_value_label)
        time_layout.addLayout(retime_row)
        
        self.transform_group.add_row(self.time_container)
        
        # Initially show resize, hide others
        self.rotate_container.setVisible(False)
        self.time_container.setVisible(False)
    
    def get_params(self) -> dict:
        """Collect loop conversion parameters from UI."""
        is_gif = self.format_selector.currentFormat() == "GIF"
        
        params = {
            'type': 'loop',
            'loop_format': self.format_selector.currentFormat(),
            'max_size_mb': self.max_size_spinbox.value() if self.max_size_spinbox.isVisible() else None,
            'auto_resize': self.auto_resize_checkbox.isChecked(),
            'resize_mode': self.resize_mode.currentText(),
            'resize_value': self.resize_value.value(),
            'multiple_resize': self.multiple_resize.isChecked(),
            'resize_variants': self._parse_variants(self.resize_variants.text()),
            'rotation_angle': self.rotation_angle.currentAngle(),
            'enable_time_cutting': self.enable_time_cutting.isChecked(),
            'time_start': self.time_range_slider.startValue() if self.enable_time_cutting.isChecked() else 0.0,
            'time_end': self.time_range_slider.endValue() if self.enable_time_cutting.isChecked() else 1.0,
            'retime_enabled': self.enable_retime.isChecked(),
            'retime_speed': self.retime_slider.value() / 10.0 if self.enable_retime.isChecked() else 1.0,
        }
        
        if is_gif:
            params.update({
                'gif_fps': int(self.gif_fps.currentText()),
                'gif_colors': int(self.gif_colors.currentText()),
                'gif_dither': self.gif_dither_slider.value(),
                'gif_blur': self.gif_blur.isChecked(),
                'gif_multiple_variants': self.gif_variants_checkbox.isChecked(),
                'gif_fps_variants': self._parse_variants(self.gif_fps_variants.text()),
                'gif_colors_variants': self._parse_variants(self.gif_colors_variants.text()),
                'gif_dither_variants': self._parse_variants(self.gif_dither_variants.text()),
            })
        else:
            params.update({
                'webm_quality': self.webm_quality.value(),
                'webm_multiple_variants': self.webm_variants_checkbox.isChecked(),
                'webm_quality_variants': self._parse_variants(self.webm_quality_variants.text()),
            })
        
        return params
    
    def update_theme(self, is_dark: bool):
        """Apply theme styling to all elements."""
        self._is_dark_theme = is_dark
        global COMBOBOX_STYLE
        COMBOBOX_STYLE = get_combobox_style(is_dark)
        self.resize_mode.setStyleSheet(COMBOBOX_STYLE)
        
        # Update all checkboxes
        checkboxes = [
            self.auto_resize_checkbox, self.gif_variants_checkbox, self.gif_blur,
            self.webm_variants_checkbox, self.multiple_resize,
            self.enable_time_cutting, self.enable_retime
        ]
        for checkbox in checkboxes:
            if hasattr(checkbox, 'update_theme'):
                checkbox.update_theme(is_dark)
        
        if hasattr(self.time_range_slider, 'update_theme'):
            self.time_range_slider.update_theme(is_dark)
    
    def set_mode(self, mode: str):
        """Set the size mode (Max Size, Presets, Manual)."""
        is_max_size = (mode == "Max Size")
        
        self.max_size_label.setVisible(is_max_size)
        self.max_size_spinbox.setVisible(is_max_size)
        self.auto_resize_checkbox.setVisible(is_max_size)
    
    def set_transform_mode(self, mode: str):
        """Set which transform section is visible."""
        self.resize_container.setVisible(mode == 'resize')
        self.rotate_container.setVisible(mode == 'rotate')
        self.time_container.setVisible(mode == 'time')
    
    def current_format(self) -> str:
        """Get current format (GIF or WebM)."""
        return self.format_selector.currentFormat()
    
    # -------------------------------------------------------------------------
    # PRIVATE METHODS
    # -------------------------------------------------------------------------
    
    def _on_format_changed(self, format_name: str):
        """Handle format change between GIF and WebM."""
        is_gif = (format_name == "GIF")
        
        # GIF controls
        for widget in [self.gif_variants_checkbox, self.gif_fps, self.gif_fps_label,
                      self.gif_colors, self.gif_colors_label, self.gif_dither_slider,
                      self.gif_dither_value, self.gif_dither_label, self.gif_blur]:
            widget.setVisible(is_gif)
        
        # WebM controls
        show_webm_slider = not is_gif and not self.webm_variants_checkbox.isChecked()
        show_webm_variants = not is_gif and self.webm_variants_checkbox.isChecked()
        
        self.webm_variants_checkbox.setVisible(not is_gif)
        self.webm_quality.setVisible(show_webm_slider)
        self.webm_quality_value.setVisible(show_webm_slider)
        self.webm_quality_label.setVisible(not is_gif)
        self.webm_quality_variants.setVisible(show_webm_variants)
        self.webm_quality_variants_label.setVisible(show_webm_variants)
        
        # Emit signal
        self.format_changed.emit(format_name)
        self._notify_param_change()
    
    def _toggle_gif_variants(self, enabled: bool):
        """Toggle GIF variant controls."""
        # Single value controls
        self.gif_fps.setVisible(not enabled)
        self.gif_fps_label.setVisible(not enabled)
        self.gif_colors.setVisible(not enabled)
        self.gif_colors_label.setVisible(not enabled)
        self.gif_dither_slider.setVisible(not enabled)
        self.gif_dither_value.setVisible(not enabled)
        self.gif_dither_label.setVisible(not enabled)
        
        # Variant controls
        self.gif_fps_variants.setVisible(enabled)
        self.gif_fps_variants_label.setVisible(enabled)
        self.gif_colors_variants.setVisible(enabled)
        self.gif_colors_variants_label.setVisible(enabled)
        self.gif_dither_variants.setVisible(enabled)
        self.gif_dither_variants_label.setVisible(enabled)
        
        self._notify_param_change()
    
    def _toggle_webm_variants(self, enabled: bool):
        """Toggle WebM variant controls."""
        self.webm_quality.setVisible(not enabled)
        self.webm_quality_value.setVisible(not enabled)
        self.webm_quality_variants.setVisible(enabled)
        self.webm_quality_variants_label.setVisible(enabled)
        self._notify_param_change()
    
    def _toggle_resize_mode(self, multiple: bool):
        """Toggle resize variant mode."""
        self.resize_value.setVisible(not multiple)
        self.resize_value_label.setVisible(not multiple)
        self.resize_variants.setVisible(multiple)
        self.resize_variants_label.setVisible(multiple)
        self._notify_param_change()
    
    def _on_resize_mode_changed(self, mode: str):
        """Handle resize mode change."""
        show_value = (mode != "No resize")
        
        if self.multiple_resize.isChecked():
            self.resize_variants.setVisible(show_value)
            self.resize_variants_label.setVisible(show_value)
            self.resize_value.setVisible(False)
            self.resize_value_label.setVisible(False)
        else:
            self.resize_value.setVisible(show_value)
            self.resize_value_label.setVisible(show_value)
            self.resize_variants.setVisible(False)
            self.resize_variants_label.setVisible(False)
        
        if "width" in mode.lower():
            self.resize_value_label.setText("Width (pixels)")
        elif "longer" in mode.lower():
            self.resize_value_label.setText("Longer edge (pixels)")
        elif "ratio" in mode.lower():
            self.resize_value_label.setText("Ratio (%)")
        
        self._notify_param_change()
    
    def _toggle_time_cutting(self, enabled: bool):
        """Toggle time range slider."""
        self.time_range_slider.setVisible(enabled)
        self._notify_param_change()
    
    def _toggle_retime(self, enabled: bool):
        """Toggle retime slider."""
        self.retime_slider.setVisible(enabled)
        self.retime_value_label.setVisible(enabled)
        self._notify_param_change()
    
    def _parse_variants(self, text: str) -> list:
        """Parse comma-separated variant values."""
        try:
            return [v.strip() for v in text.split(',') if v.strip()]
        except:
            return []
