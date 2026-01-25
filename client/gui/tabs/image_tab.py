"""
ImageTab - Image conversion tab component.

Extracted from CommandPanel as part of the Mediator-Shell refactoring.
This tab handles image format, quality, resize, and rotation settings.
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
    CustomComboBox, FormatButtonRow, RotationButtonRow, 
    ThemedCheckBox, CustomTargetSizeSpinBox
)
from client.gui.command_panel import get_combobox_style

COMBOBOX_STYLE = get_combobox_style(True)  # Default dark mode


class ImageTab(BaseTab):
    """
    Image conversion settings tab.
    
    Provides controls for:
    - Output format (WebP, JPG, PNG)
    - Quality settings (single or multiple variants)
    - Max file size targeting
    - Resize options (by width, longer edge, ratio)
    - Rotation angle
    """
    
    def __init__(self, parent=None, focus_callback=None):
        """
        Initialize ImageTab.
        
        Args:
            parent: Parent widget
            focus_callback: Callback to invoke when focusing the active tab
        """
        super().__init__(parent)
        self._focus_callback = focus_callback or (lambda: None)
        self.setup_ui()
    
    def setup_ui(self):
        """Create the image tab UI elements."""
        # Use the layout from BaseTab
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
        self.format_group = CommandGroup("")
        self.format_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.format_group.get_content_layout().setContentsMargins(16, 16, 16, 16)
        self.format_group.setMinimumHeight(180)
        settings_h.addWidget(self.format_group, 1)
        
        layout.addWidget(settings_row)
        
        # --- Format Selection ---
        self.format = FormatButtonRow(["WebP", "JPG", "PNG"])
        self.format_group.get_content_layout().insertRow(0, self.format)
        
        # --- Max Size (for Max Size mode) ---
        self.max_size_spinbox = CustomTargetSizeSpinBox(
            default_value=0.2,
            on_enter_callback=self._focus_callback
        )
        self.max_size_spinbox.setRange(0.01, 100.0)
        self.max_size_spinbox.setDecimals(2)
        self.max_size_spinbox.setSensitivity(0.0025)
        self.max_size_spinbox.setToolTip("Target maximum file size in megabytes")
        self.max_size_spinbox.setVisible(False)
        self.max_size_label = QLabel("Max Size")
        self.max_size_label.setVisible(False)
        self.format_group.add_row(self.max_size_label, self.max_size_spinbox)
        
        # --- Auto-resize checkbox ---
        self.auto_resize_checkbox = ThemedCheckBox("Auto-resize")
        self.auto_resize_checkbox.setChecked(True)
        self.auto_resize_checkbox.setToolTip(
            "Change the resolution in pixels (width×height) to match desired file size in MB."
        )
        self.auto_resize_checkbox.setVisible(False)
        self.format_group.add_row(self.auto_resize_checkbox)
        
        # --- Multiple qualities ---
        self.multiple_qualities = ThemedCheckBox("Multiple qualities")
        self.multiple_qualities.toggled.connect(self._toggle_quality_mode)
        self.format_group.add_row(self.multiple_qualities)
        
        # --- Quality slider ---
        self.quality = QSlider(Qt.Orientation.Horizontal)
        self.quality.setRange(1, 100)
        self.quality.setValue(40)
        self.quality_label = QLabel("40")
        self.quality.valueChanged.connect(lambda v: self.quality_label.setText(str(v)))
        
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(self.quality)
        quality_layout.addWidget(self.quality_label)
        self.quality_row_label = QLabel("Quality")
        self.format_group.add_row(self.quality_row_label, quality_layout)
        
        # --- Quality variants ---
        self.quality_variants = QLineEdit()
        self.quality_variants.setPlaceholderText("e.g., 40, 60, 80, 95")
        self.quality_variants.setText("40, 60, 80, 95")
        self.quality_variants.setVisible(False)
        self.quality_variants_label = QLabel("Quality variants")
        self.quality_variants_label.setVisible(False)
        self.format_group.add_row(self.quality_variants_label, self.quality_variants)
        
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
        
        self.multiple_resize = ThemedCheckBox("Multiple resize variants")
        self.multiple_resize.toggled.connect(self._toggle_resize_mode)
        resize_layout.addWidget(self.multiple_resize)
        
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
        self.resize_variants_label = QLabel("Resize values")
        self.resize_variants = QLineEdit()
        self.resize_variants.setPlaceholderText("e.g., 30,50,80 or 720,1280,1920")
        self.resize_variants.setText("720,1280,1920")
        variants_row.addWidget(self.resize_variants_label)
        variants_row.addWidget(self.resize_variants)
        resize_layout.addLayout(variants_row)
        
        # Initial visibility
        self.resize_value_label.setVisible(False)
        self.resize_value.setVisible(False)
        self.resize_variants_label.setVisible(False)
        self.resize_variants.setVisible(False)
        
        self.transform_group.add_row(self.resize_container)
        
        # === ROTATION SECTION ===
        self.rotate_container = QWidget()
        rotate_layout = QVBoxLayout(self.rotate_container)
        rotate_layout.setContentsMargins(0, 0, 0, 0)
        
        self.rotation_angle = RotationButtonRow()
        rotate_layout.addWidget(self.rotation_angle)
        
        self.transform_group.add_row(self.rotate_container)
        
        # Initially show resize, hide rotate
        self.rotate_container.setVisible(False)
    
    def get_params(self) -> dict:
        """Collect image conversion parameters from UI."""
        params = {
            'type': 'image',
            'format': self.format.currentFormat(),
            'quality': self.quality.value(),
            'multiple_qualities': self.multiple_qualities.isChecked(),
            'quality_variants': self._parse_variants(self.quality_variants.text()),
            'max_size_mb': self.max_size_spinbox.value() if self.max_size_spinbox.isVisible() else None,
            'auto_resize': self.auto_resize_checkbox.isChecked(),
            'resize_mode': self.resize_mode.currentText(),
            'resize_value': self.resize_value.value(),
            'multiple_resize': self.multiple_resize.isChecked(),
            'resize_variants': self._parse_variants(self.resize_variants.text()),
            'rotation_angle': self.rotation_angle.currentAngle(),
        }
        return params
    
    def update_theme(self, is_dark: bool):
        """Apply theme styling to all elements."""
        self._is_dark_theme = is_dark
        # Update combobox style
        global COMBOBOX_STYLE
        COMBOBOX_STYLE = get_combobox_style(is_dark)
        self.resize_mode.setStyleSheet(COMBOBOX_STYLE)
        
        # Update checkboxes
        for checkbox in [self.multiple_qualities, self.auto_resize_checkbox, self.multiple_resize]:
            if hasattr(checkbox, 'update_theme'):
                checkbox.update_theme(is_dark)
    
    def set_mode(self, mode: str):
        """
        Set the size mode (Max Size, Presets, Manual).
        
        Args:
            mode: "Max Size", "Presets", or "Manual"
        """
        is_max_size = (mode == "Max Size")
        is_manual = (mode == "Manual")
        
        # Max size controls
        self.max_size_label.setVisible(is_max_size)
        self.max_size_spinbox.setVisible(is_max_size)
        self.auto_resize_checkbox.setVisible(is_max_size)
        
        # Quality controls (visible in Max Size and Manual)
        show_quality = is_max_size or is_manual
        self.quality_row_label.setVisible(show_quality and not self.multiple_qualities.isChecked())
        self.quality.setVisible(show_quality and not self.multiple_qualities.isChecked())
        self.quality_label.setVisible(show_quality and not self.multiple_qualities.isChecked())
    
    def set_transform_mode(self, mode: str):
        """Set which transform section is visible (resize or rotate)."""
        self.resize_container.setVisible(mode == 'resize')
        self.rotate_container.setVisible(mode == 'rotate')
    
    # -------------------------------------------------------------------------
    # PRIVATE METHODS
    # -------------------------------------------------------------------------
    
    def _toggle_quality_mode(self, multiple: bool):
        """Toggle between single quality slider and multiple quality variants."""
        self.quality.setVisible(not multiple)
        self.quality_label.setVisible(not multiple)
        self.quality_row_label.setVisible(not multiple)
        self.quality_variants.setVisible(multiple)
        self.quality_variants_label.setVisible(multiple)
        self._notify_param_change()
    
    def _toggle_resize_mode(self, multiple: bool):
        """Toggle between single resize value and multiple variants."""
        self.resize_value.setVisible(not multiple)
        self.resize_value_label.setVisible(not multiple)
        self.resize_variants.setVisible(multiple)
        self.resize_variants_label.setVisible(multiple)
        self._notify_param_change()
    
    def _on_resize_mode_changed(self, mode: str):
        """Handle resize mode dropdown change."""
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
        
        # Update label based on mode
        if "width" in mode.lower():
            self.resize_value_label.setText("Width (pixels)")
        elif "longer" in mode.lower():
            self.resize_value_label.setText("Longer edge (pixels)")
        elif "ratio" in mode.lower():
            self.resize_value_label.setText("Ratio (%)")
        
        self._notify_param_change()
    
    def _parse_variants(self, text: str) -> list:
        """Parse comma-separated variant values."""
        try:
            return [v.strip() for v in text.split(',') if v.strip()]
        except:
            return []
