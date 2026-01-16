"""
Command Panel Widget
Provides conversion commands and options for ffmpeg, gifsicle, and ImageMagick
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QLineEdit,
    QGroupBox, QFormLayout, QTabWidget, QTextEdit, QSlider, QRadioButton, QSizePolicy, QButtonGroup,
    QProgressBar, QFrame
)
from client.utils.font_manager import AppFonts, FONT_FAMILY, FONT_SIZE_BUTTON
from client.gui.custom_widgets import TimeRangeSlider, ResizeFolder, RotationOptions, CustomComboBox, CustomTargetSizeSpinBox, ModeButtonsWidget
from client.gui.custom_spinbox import CustomSpinBox
from client.gui.command_group import CommandGroup
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
                "background-color: transparent; "
                "color: #d32f2f; "
                "border: 2px solid #d32f2f; "
                "border-radius: 8px; "
                "padding: 12px 0px; "
                "font-weight: bold; "
            ),
            "stop_hover": "background-color: #d32f2f; color: white; border-color: #b71c1c;",
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
    """Get QComboBox style that respects dark/light mode with chevron arrow"""
    bg_color = "#2b2b2b" if is_dark else "#ffffff"
    text_color = "white" if is_dark else "black"
    border_color = "#555555" if is_dark else "#cccccc"
    dropdown_bg = bg_color  # Match main background
    arrow_color = "#AAAAAA" if is_dark else "#888888"
    
    return (
        f"QComboBox {{ "
        f"background-color: {bg_color}; "
        f"color: {text_color}; "
        f"border: 1px solid {border_color}; "
        f"border-radius: 4px; "
        f"padding: 4px 25px 4px 8px; "
        f"}} "
        f"QComboBox:hover {{ border-color: #4CAF50; }} "
        f"QComboBox::drop-down {{ "
        f"subcontrol-origin: padding; "
        f"subcontrol-position: top right; "
        f"width: 20px; "
        f"border: none; "
        f"background-color: {dropdown_bg}; "
        f"}} "
        f"QComboBox::down-arrow {{ "
        f"image: none; "
        f"width: 0; "
        f"height: 0; "
        f"border-left: 5px solid transparent; "
        f"border-right: 5px solid transparent; "
        f"border-top: 6px solid {arrow_color}; "
        f"margin-right: 5px; "
        f"}} "
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
    
    def resizeEvent(self, event):
        """Handle resize to keep tab bar stretched to full width"""
        super().resizeEvent(event)
        if hasattr(self, 'tabs'):
            tab_bar = self.tabs.tabBar()
            # Force tab bar to match tab widget width (account for borders)
            new_width = self.tabs.width() - 6
            if new_width > 0:
                tab_bar.setFixedWidth(new_width)
    
    def showEvent(self, event):
        """Handle show to ensure tabs are properly sized"""
        super().showEvent(event)
        QTimer.singleShot(0, self._update_tab_bar_width)
    
    def _update_tab_bar_width(self):
        """Update tab bar width to fill the tab widget"""
        if hasattr(self, 'tabs'):
            tab_bar = self.tabs.tabBar()
            new_width = self.tabs.width() - 6
            if new_width > 0:
                tab_bar.setFixedWidth(new_width)

    def _create_label_with_icon(self, text, icon_path):
        """Create a QLabel with an icon and text"""
        from PyQt6.QtGui import QPixmap, QPainter
        import os
        
        container = QWidget()
        container.setMinimumHeight(28)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Create red square placeholder (16x16)
        icon_label = QLabel()
        icon_label.setFixedSize(16, 16)
        icon_label.setStyleSheet("background-color: red;")
        
        # Create text label
        text_label = QLabel(text)
        text_label.setWordWrap(False)
        
        layout.addWidget(icon_label)
        layout.addWidget(text_label)
        layout.addStretch()
        
        return container

    def _create_group_box(self, title, icon_path, size_policy=None):
        """Create a standardized group box with icon and title.
        
        This ensures consistent styling across all tabs:
        - Same padding and margins
        - Same icon size and placement
        - Same title styling
        
        Args:
            title: The group box title text
            icon_path: Path to the icon file
            size_policy: Optional QSizePolicy.Policy for vertical sizing
            
        Returns:
            tuple: (group_box, content_layout) - the group box and its form layout for content
        """
        group = QGroupBox()
        group.setTitle("")  # Will add icon+text manually
        
        if size_policy:
            group.setSizePolicy(group.sizePolicy().horizontalPolicy(), size_policy)
        else:
            group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        # Outer layout for the group
        outer_layout = QVBoxLayout(group)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)
        
        # Title widget with icon
        title_widget = self._create_label_with_icon(title, icon_path)
        title_widget.setStyleSheet("font-weight: bold; padding: 10px 12px; background-color: transparent;")
        outer_layout.addWidget(title_widget)
        
        # Content form layout with consistent margins
        content_layout = QFormLayout()
        content_layout.setContentsMargins(12, 8, 12, 12)
        content_layout.setVerticalSpacing(8)
        outer_layout.addLayout(content_layout)
        
        return group, content_layout
        
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
                getattr(self, 'image_auto_resize_checkbox', None),
                getattr(self, 'video_auto_resize_checkbox', None),
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
        
        # Update CustomTargetSizeSpinBox widgets
        from client.gui.custom_widgets import CustomTargetSizeSpinBox
        target_size_spinboxes = self.findChildren(CustomTargetSizeSpinBox)
        for spinbox in target_size_spinboxes:
            spinbox.update_theme(is_dark)
        
        # Update CustomSpinBox widgets
        from client.gui.custom_spinbox import CustomSpinBox
        custom_spinboxes = self.findChildren(CustomSpinBox)
        for spinbox in custom_spinboxes:
            spinbox.update_theme(is_dark)
        
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
        layout.setSpacing(0)  # We'll manually add spacers
        layout.setContentsMargins(0, 0, 0, 0)  # Remove default margins
        
        # DEBUG: Color the main layout margins - COMMENTED OUT
        # self.setStyleSheet("""
        #     QWidget#CommandPanel { 
        #         background-color: rgba(255, 0, 255, 100); 
        #         border: 3px solid magenta; 
        #     }
        # """)
        # self.setObjectName("CommandPanel")
        
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
        
        # Initialize UI state to match default mode selections
        self.on_image_size_mode_changed("Max Size")
        self.on_video_size_mode_changed("Max Size")
        self.on_gif_size_mode_changed("Max Size")
        
        # Make tab buttons fill available width
        tab_bar = self.tabs.tabBar()
        tab_bar.setExpanding(True)  # Key setting to expand tabs
        tab_bar.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        from PyQt6.QtWidgets import QTabBar
        tab_bar.setUsesScrollButtons(False)
        self.tabs.setDocumentMode(False)  # Keep False to allow expanding
        
        # Force the tab bar to fill the width
        tab_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        tab_bar.setMinimumWidth(0)  # Allow shrinking
        
        # Initial width update will happen in showEvent
        
        # Stylesheet for tabs
        self.tabs.setStyleSheet("""
            QTabBar::tab {
                padding: 8px 16px 13px 16px;
                min-height: 32px;
                margin-bottom: 0px;
                border-bottom: 2px solid #888888;
            }
            QTabBar::tab:selected {
                border-bottom: 2px solid #00AA00;
                margin-bottom: 0px;
            }
            QTabWidget::pane {
                border: none;
                margin-top: 0px;
                padding-top: 2px;
                padding-bottom: 0px;
                margin-bottom: 0px;
                background-color: transparent;
            }
        """)
        # DEBUG: Tab colors - COMMENTED OUT
        # QTabBar::tab { background-color: rgba(0, 255, 0, 100); }
        # QTabBar::tab:selected { background-color: rgba(0, 255, 0, 200); }
        # QTabWidget::pane { background-color: rgba(255, 128, 0, 150); }
        # QTabWidget { border: 3px solid cyan; background-color: rgba(255, 255, 0, 200); }
        
        layout.addWidget(self.tabs)
        
        # DEBUG: Visual marker for tabs widget bottom edge
        tabs_end_marker = QWidget()
        tabs_end_marker.setFixedHeight(0)  # Set to 0
        tabs_end_marker.setStyleSheet("background-color: rgba(255, 0, 0, 255);")  # Bright red line
        tabs_end_label = QLabel("TABS-WIDGET-END", tabs_end_marker)
        tabs_end_label.setStyleSheet("color: white; font-size: 9px; font-weight: bold;")
        tabs_end_label.move(2, -6)
        layout.addWidget(tabs_end_marker)
        
        # DEBUG: Gap between tabs and output folder
        layout.addWidget(self._create_debug_spacer(8))
        
        # Output settings
        output_group = self.create_output_settings()
        layout.addWidget(output_group)
        
        # DEBUG: Gap between output folder and convert button
        layout.addWidget(self._create_debug_spacer(9))
        
        # Control buttons
        button_layout = self.create_control_buttons()
        layout.addLayout(button_layout)
        
        # Install event filter on all input fields for Enter key handling
        self._install_input_field_filters()
        
    def _install_input_field_filters(self):
        """Install event filter on all input fields to handle Enter key"""
        from client.gui.custom_widgets import CustomTargetSizeSpinBox
        
        # Get all CustomTargetSizeSpinBox lineEdits to exclude them (they handle Enter themselves)
        custom_spinbox_lineedits = set()
        custom_spinboxes = self.findChildren(CustomTargetSizeSpinBox)
        for custom_spinbox in custom_spinboxes:
            custom_spinbox_lineedits.add(custom_spinbox.spinbox.lineEdit())
        
        # Find all QLineEdit widgets (excluding those in CustomTargetSizeSpinBox)
        line_edits = self.findChildren(QLineEdit)
        for line_edit in line_edits:
            if line_edit not in custom_spinbox_lineedits:
                line_edit.installEventFilter(self)
        
        # Find all QSpinBox widgets (including their internal lineEdits)
        spin_boxes = self.findChildren(QSpinBox)
        for spin_box in spin_boxes:
            spin_box.lineEdit().installEventFilter(self)
        
        # Find all QDoubleSpinBox widgets - but exclude those inside CustomTargetSizeSpinBox
        double_spin_boxes = self.findChildren(QDoubleSpinBox)
        for double_spin_box in double_spin_boxes:
            if double_spin_box.lineEdit() not in custom_spinbox_lineedits:
                double_spin_box.lineEdit().installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """Filter Enter key presses in input fields to switch focus to active tab button"""
        from PyQt6.QtCore import QEvent, Qt
        
        # Check if this is a KeyPress event
        if event.type() == QEvent.Type.KeyPress:
            # Explicitly allow arrow keys to propagate (for spinbox navigation)
            if event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Left, Qt.Key.Key_Right):
                return False  # Let arrow keys pass through
            
            # Handle Enter/Return keys only
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                # Check if the object is an input field
                if isinstance(obj, QLineEdit):
                    # Clear focus from the input field first
                    obj.clearFocus()
                    
                    # Set focus to the tab button
                    self._focus_active_tab()
                    
                    return True  # Event handled
        
        # Let all other events propagate normally
        return False  # Changed from super().eventFilter() to explicit False
    
    def _focus_active_tab(self):
        """Set focus to the currently active tab button"""
        from PyQt6.QtWidgets import QApplication
        # Clear current focus first
        focus_widget = QApplication.focusWidget()
        if focus_widget:
            focus_widget.clearFocus()
        tab_bar = self.tabs.tabBar()
        tab_bar.setFocus()

    def mousePressEvent(self, event):
        """Clicking empty canvas should clear focus and focus active tab"""
        super().mousePressEvent(event)
        child = self.childAt(event.position().toPoint())
        if child is None or child == self:
            self._focus_active_tab()
    
    def _create_mode_separator(self):
        """Create a grey separator line to divide Mode section from parameters"""
        from PyQt6.QtWidgets import QFrame
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Plain)
        separator.setStyleSheet("background-color: #555555; margin: 4px 0px;")
        separator.setFixedHeight(1)
        return separator
    
    def _create_debug_spacer(self, number):
        """Create a spacer for gaps between sections"""
        # DEBUG: Colored spacers - COMMENTED OUT
        # colors = {
        #     1: "rgba(255, 0, 0, 200)", 2: "rgba(255, 128, 0, 200)", 3: "rgba(255, 255, 0, 200)",
        #     4: "rgba(0, 255, 0, 200)", 5: "rgba(0, 255, 255, 200)", 6: "rgba(0, 128, 255, 200)",
        #     7: "rgba(128, 0, 255, 200)", 8: "rgba(255, 0, 255, 200)", 9: "rgba(255, 192, 203, 200)",
        # }
        spacer = QWidget()
        spacer.setFixedHeight(8)
        # DEBUG: Uncomment to show colored spacers
        # spacer.setStyleSheet(f"background-color: {colors.get(number, 'rgba(128, 128, 128, 200)')};")
        # label = QLabel(f"{number}-GAP-8px", spacer)
        # label.setStyleSheet("color: black; font-size: 9px; font-weight: bold; background: rgba(255,255,255,180); padding: 1px;")
        # label.move(2, -1)
        return spacer
        
    def create_image_tab(self):
        """Create image conversion options tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)  # We'll manually add spacers
        
        # Settings group (Mode + Format + Quality)
        format_group = CommandGroup("Settings", "client/assets/icons/settings.png")
        
        # Add mode buttons
        self.image_mode_buttons = format_group.add_mode_buttons(default_mode="Max Size")
        self.image_mode_buttons.modeChanged.connect(self.on_image_size_mode_changed)
        self.image_size_mode_value = "manual"
        
        # Target Size - FIRST (shown in Max Size mode)
        self.image_max_size_spinbox = CustomTargetSizeSpinBox(
            default_value=0.2,
            on_enter_callback=self._focus_active_tab
        )
        self.image_max_size_spinbox.setRange(0.01, 100.0)  # Allow smaller sizes for images
        self.image_max_size_spinbox.setDecimals(2)  # Two decimal places for precision
        self.image_max_size_spinbox.setSensitivity(0.0025)  # Lower sensitivity (40px = 0.1 value change)
        self.image_max_size_spinbox.setToolTip("Target maximum file size in megabytes")
        self.image_max_size_spinbox.setVisible(False)
        self.image_max_size_label = QLabel("Max Size (MB)")
        self.image_max_size_label.setVisible(False)
        format_group.add_row(self.image_max_size_label, self.image_max_size_spinbox)

        # Auto-resize checkbox (for Max Size mode)
        self.image_auto_resize_checkbox = QCheckBox("Auto-resize")
        self.image_auto_resize_checkbox.setChecked(True)
        self.image_auto_resize_checkbox.setStyleSheet(TOGGLE_STYLE)
        self.image_auto_resize_checkbox.setToolTip(
            "Change the resolution in pixels (width×height) to match desired file size in MB."
        )
        self.image_auto_resize_checkbox.setVisible(False)
        format_group.add_row(self.image_auto_resize_checkbox)
        
        # Format dropdown - SECOND
        self.image_format = CustomComboBox()
        self.image_format.addItems(["WebP", "JPG", "PNG", "TIFF", "BMP"])
        format_group.add_row("Format", self.image_format)

        # Multiple qualities option - THIRD
        self.multiple_qualities = QCheckBox("Multiple qualities")
        self.multiple_qualities.toggled.connect(self.toggle_quality_mode)
        self.multiple_qualities.setStyleSheet(TOGGLE_STYLE)
        format_group.add_row(self.multiple_qualities)
        
        # Quality settings
        self.image_quality = QSlider(Qt.Orientation.Horizontal)
        self.image_quality.setRange(1, 100)
        self.image_quality.setValue(40)
        self.image_quality_label = QLabel("40")
        self.image_quality.valueChanged.connect(lambda v: self.image_quality_label.setText(str(v)))
        
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(self.image_quality)
        quality_layout.addWidget(self.image_quality_label)
        self.image_quality_row_label = QLabel("Quality")
        format_group.add_row(self.image_quality_row_label, quality_layout)
        
        # Quality variants input (hidden by default)
        self.quality_variants = QLineEdit()
        self.quality_variants.setPlaceholderText("e.g., 40, 60, 80, 95")
        self.quality_variants.setText("40, 60, 80, 95")
        self.quality_variants.setVisible(False)
        self.quality_variants_label = QLabel("Quality variants")
        self.quality_variants_label.setVisible(False)
        format_group.add_row(self.quality_variants_label, self.quality_variants)
        
        layout.addWidget(format_group)
        
        # DEBUG: Gap between folders
        layout.addWidget(self._create_debug_spacer(3))
        
        # Transform options (Resize + Rotation combined)
        transform_group = CommandGroup(
            "Transform", "client/assets/icons/transform.svg", size_policy=QSizePolicy.Policy.Maximum
        )
        
        # Resize mode selection
        self.image_resize_mode = CustomComboBox()
        self.image_resize_mode.addItems(["No resize", "By width (pixels)", "By longer edge (pixels)", "By ratio (percent)"])
        self.image_resize_mode.setStyleSheet(COMBOBOX_STYLE)
        self.image_resize_mode.currentTextChanged.connect(self.on_image_resize_ui_changed)
        transform_group.add_row("Resize", self.image_resize_mode, with_icon=True)
        
        # Multiple resize option
        self.multiple_resize = QCheckBox("Multiple resize variants")
        self.multiple_resize.toggled.connect(self.toggle_resize_mode)
        self.multiple_resize.setStyleSheet(TOGGLE_STYLE)
        transform_group.add_row(self.multiple_resize)
        
        # Single resize value input
        self.resize_value = CustomSpinBox(on_enter_callback=self._focus_active_tab)
        self.resize_value.setRange(1, 10000)
        self.resize_value.setValue(720)  # Default for pixels
        self.resize_value.setVisible(False)
        self.resize_value_label = QLabel("Width (pixels)")
        self.resize_value_label.setVisible(False)
        transform_group.add_row(self.resize_value_label, self.resize_value)
        
        # Multiple resize input (hidden by default)
        self.resize_variants = QLineEdit()
        self.resize_variants.setPlaceholderText("e.g., 30,50,80 or 720,1280,1920")
        self.resize_variants.setText("720,1280,1920")
        self.resize_variants.setVisible(False)
        self.resize_variants_label = QLabel("Resize values")
        self.resize_variants_label.setVisible(False)
        transform_group.add_row(self.resize_variants_label, self.resize_variants)
        
        # Gray separator bar
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Plain)
        separator.setStyleSheet("background-color: #555555; margin: 8px 0px;")
        separator.setFixedHeight(1)
        transform_group.add_row(separator)
        
        # Rotation options
        self.image_rotation_angle = CustomComboBox()
        self.image_rotation_angle.addItems(["No rotation", "90° clockwise", "180°", "270° clockwise"])
        self.image_rotation_angle.setStyleSheet(COMBOBOX_STYLE)
        transform_group.add_row("Rotation", self.image_rotation_angle, with_icon=True)
        
        # Set fixed height to prevent jumping when controls show/hide
        transform_group.setFixedHeight(180)
        
        layout.addWidget(transform_group)
        
        return tab
        
    def create_video_tab(self):
        """Create video conversion options tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)  # We'll manually add spacers
        
        # Settings group (Mode + Format + Quality)
        codec_group = CommandGroup("Settings", "client/assets/icons/settings.png")
        
        # Add mode buttons
        self.video_mode_buttons = codec_group.add_mode_buttons(default_mode="Max Size")
        self.video_mode_buttons.modeChanged.connect(self.on_video_size_mode_changed)
        self.video_size_mode_value = "manual"
        
        # Target Size - FIRST (shown in Max Size mode)
        self.video_max_size_spinbox = CustomTargetSizeSpinBox(
            default_value=1.0,
            on_enter_callback=self._focus_active_tab
        )
        self.video_max_size_spinbox.setToolTip("Target maximum file size in megabytes")
        self.video_max_size_spinbox.setVisible(False)
        self.video_max_size_label = QLabel("Max Size (MB)")
        self.video_max_size_label.setVisible(False)
        codec_group.add_row(self.video_max_size_label, self.video_max_size_spinbox)

        # Auto-resize checkbox (for Max Size mode)
        self.video_auto_resize_checkbox = QCheckBox("Auto-resize")
        self.video_auto_resize_checkbox.setChecked(True)
        self.video_auto_resize_checkbox.setStyleSheet(TOGGLE_STYLE)
        self.video_auto_resize_checkbox.setToolTip(
            "Change the resolution in pixels (width×height) to match desired file size in MB."
        )
        self.video_auto_resize_checkbox.setVisible(False)
        codec_group.add_row(self.video_auto_resize_checkbox)
        
        # Format dropdown - SECOND
        self.video_codec = CustomComboBox()
        self.video_codec.addItems(["WebM (VP9, faster)", "WebM (AV1, slower)", "MP4 (H.264)", "MP4 (H.265)", "MP4 (AV1)"])
        self.video_codec.currentTextChanged.connect(self.on_video_codec_changed)
        codec_group.add_row("Format", self.video_codec)

        # Quality (CRF) slider for WebM
        self.video_quality = QSlider(Qt.Orientation.Horizontal)
        self.video_quality.setRange(0, 100)
        self.video_quality.setValue(30)  # Maps to CRF 23 (good quality)
        self.video_quality.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.video_quality.setTickInterval(10)
        self.video_quality.setToolTip("Quality: 0=lossless, 100=worst quality\nRecommended: 30-50 for WebM")
        self.video_quality_label = QLabel("Quality")
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
        codec_group.add_row(self.multiple_video_qualities)
        
        # Quality controls
        codec_group.add_row(self.video_quality_label, quality_layout)
        
        # Video quality variant inputs (hidden by default)
        self.video_quality_variants = QLineEdit()
        self.video_quality_variants.setPlaceholderText("e.g., 25,40,70 (quality values 0-100)")
        self.video_quality_variants.setText("15,23,31")
        self.video_quality_variants.setVisible(False)
        self.video_quality_variants.editingFinished.connect(self.validate_video_quality_variants)
        self.video_quality_variants_label = QLabel("Quality variants")
        self.video_quality_variants_label.setVisible(False)
        codec_group.add_row(self.video_quality_variants_label, self.video_quality_variants)
        
        # Set initial state for bitrate and quality visibility
        self.on_video_codec_changed(self.video_codec.currentText())
        
        layout.addWidget(codec_group)
        
        # DEBUG: Gap between folders
        layout.addWidget(self._create_debug_spacer(4))
        
        # Transform options (Resize + Rotation combined)
        transform_group = CommandGroup(
            "Transform", "client/assets/icons/transform.svg", size_policy=QSizePolicy.Policy.Maximum
        )
        
        # Resize mode selection
        self.video_resize_mode = CustomComboBox()
        self.video_resize_mode.addItems(["No resize", "By width (pixels)", "By longer edge (pixels)", "By ratio (percent)"])
        self.video_resize_mode.setStyleSheet(COMBOBOX_STYLE)
        self.video_resize_mode.currentTextChanged.connect(self.on_video_resize_ui_changed)
        transform_group.add_row("Resize", self.video_resize_mode, with_icon=True)
        
        # Multiple video size variants option
        self.multiple_video_variants = QCheckBox("Multiple size variants")
        self.multiple_video_variants.toggled.connect(self.toggle_video_variant_mode)
        self.multiple_video_variants.setStyleSheet(TOGGLE_STYLE)
        transform_group.add_row(self.multiple_video_variants)
        
        # Single resize value input (hidden by default)
        self.video_resize_value = CustomSpinBox(on_enter_callback=self._focus_active_tab)
        self.video_resize_value.setRange(1, 10000)
        self.video_resize_value.setValue(1920)
        self.video_resize_value.setVisible(False)
        self.video_resize_value_label = QLabel("Width (pixels)")
        self.video_resize_value_label.setVisible(False)
        transform_group.add_row(self.video_resize_value_label, self.video_resize_value)
        
        # Video size variant inputs (hidden by default)
        self.video_size_variants = QLineEdit()
        self.video_size_variants.setPlaceholderText("e.g., 480,720,1080 or 25%,50%,75%")
        self.video_size_variants.setText("480,720,1080")
        self.video_size_variants.setVisible(False)
        self.video_size_variants_label = QLabel("Size variants")
        self.video_size_variants_label.setVisible(False)
        transform_group.add_row(self.video_size_variants_label, self.video_size_variants)
        
        # Gray separator bar
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Plain)
        separator.setStyleSheet("background-color: #555555; margin: 8px 0px;")
        separator.setFixedHeight(1)
        transform_group.add_row(separator)
        
        # Rotation options
        self.video_rotation_angle = CustomComboBox()
        self.video_rotation_angle.addItems(["No rotation", "90° clockwise", "180°", "270° clockwise"])
        self.video_rotation_angle.setStyleSheet(COMBOBOX_STYLE)
        transform_group.add_row("Rotation", self.video_rotation_angle, with_icon=True)
        
        # Set fixed height to prevent jumping when controls show/hide
        transform_group.setFixedHeight(180)
        
        layout.addWidget(transform_group)
        
        # DEBUG: Gap between folders
        layout.addWidget(self._create_debug_spacer(5))
        
        # Time Options group
        time_group = CommandGroup(
            "Time Options", "client/assets/icons/time.png", size_policy=QSizePolicy.Policy.Maximum
        )
        
        # Time range toggle (controls range slider visibility)
        self.enable_time_cutting = QCheckBox("Time range")
        self.enable_time_cutting.setStyleSheet(TOGGLE_STYLE)
        self.enable_time_cutting.toggled.connect(self.toggle_time_cutting)
        
        # Time range slider with dark mode support
        self.time_range_slider = TimeRangeSlider(is_dark_mode=self.is_dark_mode)
        self.time_range_slider.setRange(0.0, 1.0)
        self.time_range_slider.setStartValue(0.0)
        self.time_range_slider.setEndValue(1.0)
        self.time_range_slider.setToolTip("Drag the handles to set start and end times (0% = beginning, 100% = end)")
        self.time_range_slider.setVisible(False)
        
        # Put toggle and slider on same row
        time_range_row = QHBoxLayout()
        time_range_row.addWidget(self.enable_time_cutting)
        time_range_row.addSpacing(8)  # Small gap between toggle and slider
        time_range_row.addWidget(self.time_range_slider, 1)  # stretch=1
        time_group.add_row(time_range_row)

        # Retime controls
        self.enable_retime = QCheckBox("Retime")
        self.enable_retime.setStyleSheet(TOGGLE_STYLE)
        self.enable_retime.toggled.connect(self.toggle_retime)

        self.retime_slider = QSlider(Qt.Orientation.Horizontal)
        self.retime_slider.setRange(10, 30)  # 1.0x to 3.0x in 0.1 steps
        self.retime_slider.setValue(10)
        self.retime_slider.setSingleStep(1)
        self.retime_slider.setVisible(False)
        self.retime_value_label = QLabel("1.0x")
        self.retime_value_label.setVisible(False)
        self.retime_slider.valueChanged.connect(lambda v: self.retime_value_label.setText(f"{v/10:.1f}x"))
        
        # Put toggle and slider on same row
        retime_row = QHBoxLayout()
        retime_row.addWidget(self.enable_retime)
        retime_row.addSpacing(8)  # Small gap between toggle and slider
        retime_row.addWidget(self.retime_slider, 1)  # stretch=1
        retime_row.addWidget(self.retime_value_label)
        time_group.add_row(retime_row)
        
        layout.addWidget(time_group)
        
        return tab
        
    def create_gif_tab(self):
        """Create GIF conversion options tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)  # We'll manually add spacers
        
        # Settings group (Mode + Format + Quality)
        self.ffmpeg_group = CommandGroup("Settings", "client/assets/icons/settings.png")
        
        # Add mode buttons
        self.gif_mode_buttons = self.ffmpeg_group.add_mode_buttons(default_mode="Max Size")
        self.gif_mode_buttons.modeChanged.connect(self.on_gif_size_mode_changed)

        # Target Size - SECOND
        self.gif_max_size_spinbox = CustomTargetSizeSpinBox(
            default_value=2.0,
            on_enter_callback=self._focus_active_tab
        )
        self.gif_max_size_spinbox.setToolTip("Target maximum file size in megabytes")
        self.gif_max_size_spinbox.setVisible(False)
        self.gif_max_size_label = QLabel("Max Size (MB)")
        self.gif_max_size_label.setVisible(False)
        self.ffmpeg_group.add_row(self.gif_max_size_label, self.gif_max_size_spinbox)

        # Auto-resize checkbox (for Max Size mode)
        self.gif_auto_resize_checkbox = QCheckBox("Auto-resize")
        self.gif_auto_resize_checkbox.setChecked(True)  # Enabled by default
        self.gif_auto_resize_checkbox.setStyleSheet(TOGGLE_STYLE)
        self.gif_auto_resize_checkbox.setToolTip(
            "Change the resolution in pixels (width×height) to match desired file size in MB."
        )
        self.gif_auto_resize_checkbox.setVisible(False)
        self.ffmpeg_group.add_row(self.gif_auto_resize_checkbox)

        # Estimation info label (hidden by default)
        self.gif_size_estimate_label = QLabel("")
        self.gif_size_estimate_label.setStyleSheet("color: #888; font-style: italic;")
        self.gif_size_estimate_label.setVisible(False)
        self.gif_size_estimate_label.setWordWrap(True)
        # Don't add to layout - we'll manage visibility separately to avoid empty row space
        # self.ffmpeg_group.add_row("", self.gif_size_estimate_label)

        # Multiple variants toggle
        self.gif_ffmpeg_variants = QCheckBox("Multiple Variants (FPS, Colors, Qualities)")
        self.gif_ffmpeg_variants.setStyleSheet(TOGGLE_STYLE)
        self.gif_ffmpeg_variants.toggled.connect(self.toggle_gif_ffmpeg_variants)
        self.ffmpeg_group.add_row(self.gif_ffmpeg_variants)

        # FPS
        self.ffmpeg_gif_fps = CustomComboBox()
        self.ffmpeg_gif_fps.addItems(["10", "12", "15", "18", "24"])
        self.ffmpeg_gif_fps.setCurrentText("15")
        self.ffmpeg_gif_fps_label = QLabel("FPS")
        self.ffmpeg_group.add_row(self.ffmpeg_gif_fps_label, self.ffmpeg_gif_fps)

        # FPS Variants
        self.ffmpeg_gif_fps_variants = QLineEdit()
        self.ffmpeg_gif_fps_variants.setPlaceholderText("e.g., 10,15,24")
        self.ffmpeg_gif_fps_variants.setVisible(False)
        self.ffmpeg_gif_fps_variants_label = QLabel("FPS variants")
        self.ffmpeg_gif_fps_variants_label.setVisible(False)
        self.ffmpeg_group.add_row(self.ffmpeg_gif_fps_variants_label, self.ffmpeg_gif_fps_variants)

        # Colors
        self.ffmpeg_gif_colors = CustomComboBox()
        self.ffmpeg_gif_colors.addItems(["8", "16", "32", "64", "128", "256"])
        self.ffmpeg_gif_colors.setCurrentText("256")
        self.ffmpeg_gif_colors_label = QLabel("Colors")
        self.ffmpeg_group.add_row(self.ffmpeg_gif_colors_label, self.ffmpeg_gif_colors)

        # Colors Variants
        self.ffmpeg_gif_colors_variants = QLineEdit()
        self.ffmpeg_gif_colors_variants.setPlaceholderText("e.g., 64,128,256")
        self.ffmpeg_gif_colors_variants.setVisible(False)
        self.ffmpeg_gif_colors_variants_label = QLabel("Colors variants")
        self.ffmpeg_gif_colors_variants_label.setVisible(False)
        self.ffmpeg_group.add_row(self.ffmpeg_gif_colors_variants_label, self.ffmpeg_gif_colors_variants)

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
        # self.ffmpeg_group.add_row(self.ffmpeg_gif_dither_label, self.ffmpeg_gif_dither)

        # Dither Quality Slider
        self.gif_dither_quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.gif_dither_quality_slider.setRange(0, 5)
        self.gif_dither_quality_slider.setValue(3)  # Default to best quality (floyd_steinberg)
        self.gif_dither_quality_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.gif_dither_quality_slider.setTickInterval(1)
        
        self.gif_dither_quality_label = QLabel("3")
        self.gif_dither_quality_slider.valueChanged.connect(self.update_dither_quality_label)
        
        dither_quality_layout = QHBoxLayout()
        dither_quality_layout.addWidget(self.gif_dither_quality_slider)
        dither_quality_layout.addWidget(self.gif_dither_quality_label)
        self.gif_dither_quality_row_label = QLabel("Quality")
        self.ffmpeg_group.add_row(self.gif_dither_quality_row_label, dither_quality_layout)

        # Dither Variants
        self.ffmpeg_gif_dither_variants = QLineEdit()
        self.ffmpeg_gif_dither_variants.setPlaceholderText("e.g., 0,3,5")
        self.ffmpeg_gif_dither_variants.setVisible(False)
        self.ffmpeg_gif_dither_variants_label = QLabel("Quality variants (0-5)")
        self.ffmpeg_gif_dither_variants_label.setVisible(False)
        self.ffmpeg_group.add_row(self.ffmpeg_gif_dither_variants_label, self.ffmpeg_gif_dither_variants)

        # Blur
        self.ffmpeg_gif_blur = QCheckBox("Reduce banding")
        self.ffmpeg_gif_blur.setStyleSheet(TOGGLE_STYLE)
        self.ffmpeg_group.add_row(self.ffmpeg_gif_blur)

        layout.addWidget(self.ffmpeg_group)
        
        # DEBUG: Gap between folders
        layout.addWidget(self._create_debug_spacer(6))
        
        # Transform options (Resize + Rotation combined)
        transform_group = CommandGroup(
            "Transform", "client/assets/icons/transform.svg", size_policy=QSizePolicy.Policy.Maximum
        )
        
        # Resize mode selection
        self.gif_resize_mode = CustomComboBox()
        self.gif_resize_mode.addItems(["No resize", "By width (pixels)", "By longer edge (pixels)", "By ratio (percent)"])
        self.gif_resize_mode.setStyleSheet(COMBOBOX_STYLE)
        self.gif_resize_mode.currentTextChanged.connect(self.on_gif_resize_ui_changed)
        transform_group.add_row("Resize", self.gif_resize_mode, with_icon=True)
        
        # Multiple resize variants option
        self.gif_multiple_resize = QCheckBox("Multiple size variants")
        self.gif_multiple_resize.toggled.connect(self.toggle_gif_resize_variant_mode)
        self.gif_multiple_resize.setStyleSheet(TOGGLE_STYLE)
        transform_group.add_row(self.gif_multiple_resize)
        
        # Single resize value input (hidden by default)
        self.gif_resize_value = CustomSpinBox(on_enter_callback=self._focus_active_tab)
        self.gif_resize_value.setRange(1, 10000)
        self.gif_resize_value.setValue(720)
        self.gif_resize_value.setVisible(False)
        self.gif_resize_value_label = QLabel("Width (pixels)")
        self.gif_resize_value_label.setVisible(False)
        transform_group.add_row(self.gif_resize_value_label, self.gif_resize_value)
        
        # Resize variant inputs (hidden by default)
        self.gif_resize_variants = QLineEdit()
        self.gif_resize_variants.setPlaceholderText("e.g., 480,720,1080")
        self.gif_resize_variants.setText("480,720,1080")
        self.gif_resize_variants.setVisible(False)
        self.gif_resize_variants_label = QLabel("Size variants")
        self.gif_resize_variants_label.setVisible(False)
        transform_group.add_row(self.gif_resize_variants_label, self.gif_resize_variants)
        
        # Gray separator bar
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Plain)
        separator.setStyleSheet("background-color: #555555; margin: 8px 0px;")
        separator.setFixedHeight(1)
        transform_group.add_row(separator)
        
        # Rotation options
        self.gif_rotation_angle = CustomComboBox()
        self.gif_rotation_angle.addItems(["No rotation", "90° clockwise", "180°", "270° clockwise"])
        self.gif_rotation_angle.setStyleSheet(COMBOBOX_STYLE)
        transform_group.add_row("Rotation", self.gif_rotation_angle, with_icon=True)
        
        # Set fixed height to prevent jumping when controls show/hide
        transform_group.setFixedHeight(180)
        
        layout.addWidget(transform_group)
        
        # DEBUG: Gap between folders
        layout.addWidget(self._create_debug_spacer(7))
        
        # Time Options group
        gif_time_group = CommandGroup(
            "Time Options", "client/assets/icons/time.png", size_policy=QSizePolicy.Policy.Maximum
        )
        
        # Time range toggle
        self.gif_enable_time_cutting = QCheckBox("Time range")
        self.gif_enable_time_cutting.setStyleSheet(TOGGLE_STYLE)
        self.gif_enable_time_cutting.toggled.connect(self.toggle_gif_time_cutting)
        
        # Time range slider with dark mode support
        self.gif_time_range_slider = TimeRangeSlider(is_dark_mode=self.is_dark_mode)
        self.gif_time_range_slider.setRange(0.0, 1.0)
        self.gif_time_range_slider.setStartValue(0.0)
        self.gif_time_range_slider.setEndValue(1.0)
        self.gif_time_range_slider.setToolTip("Drag the handles to set start and end times (0% = beginning, 100% = end)")
        self.gif_time_range_slider.setVisible(False)
        
        # Put toggle and slider on same row
        gif_time_range_row = QHBoxLayout()
        gif_time_range_row.addWidget(self.gif_enable_time_cutting)
        gif_time_range_row.addSpacing(8)  # Small gap between toggle and slider
        gif_time_range_row.addWidget(self.gif_time_range_slider, 1)  # stretch=1
        gif_time_group.add_row(gif_time_range_row)

        # Retime controls for GIF conversion
        self.gif_enable_retime = QCheckBox("Retime")
        self.gif_enable_retime.setStyleSheet(TOGGLE_STYLE)
        self.gif_enable_retime.toggled.connect(self.toggle_gif_retime)

        self.gif_retime_slider = QSlider(Qt.Orientation.Horizontal)
        self.gif_retime_slider.setRange(10, 30)
        self.gif_retime_slider.setValue(10)
        self.gif_retime_slider.setSingleStep(1)
        self.gif_retime_slider.setVisible(False)
        self.gif_retime_value_label = QLabel("1.0x")
        self.gif_retime_value_label.setVisible(False)
        self.gif_retime_slider.valueChanged.connect(lambda v: self.gif_retime_value_label.setText(f"{v/10:.1f}x"))

        # Put toggle and slider on same row
        gif_retime_row = QHBoxLayout()
        gif_retime_row.addWidget(self.gif_enable_retime)
        gif_retime_row.addSpacing(8)  # Small gap between toggle and slider
        gif_retime_row.addWidget(self.gif_retime_slider, 1)  # stretch=1
        gif_retime_row.addWidget(self.gif_retime_value_label)
        gif_time_group.add_row(gif_retime_row)
        
        layout.addWidget(gif_time_group)
        
        # DEBUG: Spacer at end of tab content - COMMENTED OUT
        # end_spacer = QWidget()
        # end_spacer.setFixedHeight(0)
        # end_spacer.setStyleSheet("background-color: rgba(255, 255, 255, 200);")
        # end_label = QLabel("TAB-END", end_spacer)
        # end_label.setStyleSheet("color: black; font-size: 9px; font-weight: bold;")
        # end_label.move(2, -1)
        # layout.addWidget(end_spacer)
        
        # STRETCH-AREA removed
        
        # Apply initial size mode visibility (Max Size default)
        self.on_gif_size_mode_changed("Max Size")
        
        return tab

    def create_output_settings(self):
        """Create output directory and naming settings"""
        group = CommandGroup("Output", "client/assets/icons/output.png")
        
        # Output location options
        self.output_mode_same = QRadioButton("Same folder as source")
        self.output_mode_nested = QRadioButton("Nested folder inside source")
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
        nested_layout.addSpacing(10)  # Add 10px spacing between label and input
        nested_layout.addWidget(self.nested_output_name)
        nested_layout.setContentsMargins(0, 10, 0, 0)  # Add 10px top margin

        group.add_row(self.output_mode_same)
        group.add_row(nested_layout)

        # Toggle for custom output directory (as radio button)
        self.output_mode_custom = QRadioButton("Custom")
        self.output_mode_custom.setChecked(False)
        self.output_mode_custom.toggled.connect(self.on_custom_output_toggled)
        # Apply shared green toggle styling
        self.output_mode_custom.setStyleSheet(TOGGLE_STYLE)
        
        # Custom output directory section (hidden by default)
        self.output_dir = QLineEdit()
        self.output_dir.setPlaceholderText("Select output directory")
        self.output_dir.setVisible(False)
        
        self.browse_output_btn = QPushButton("Browse...")
        self.browse_output_btn.clicked.connect(self.browse_output_directory)
        self.browse_output_btn.setVisible(False)
        
        custom_layout = QHBoxLayout()
        custom_layout.addWidget(self.output_mode_custom)
        custom_layout.addSpacing(10)  # Add 10px spacing between toggle and input
        custom_layout.addWidget(self.output_dir)
        custom_layout.addWidget(self.browse_output_btn)
        
        group.add_row(custom_layout)
        
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
            
            # Get size mode settings
            image_size_mode = getattr(self, 'image_size_mode_value', 'manual')
            
            params.update({
                'type': 'image',
                'format': self.image_format.currentText().lower(),
                'quality': self.image_quality.value(),
                'image_size_mode': image_size_mode,  # 'manual' or 'max_size'
                'image_max_size_mb': self.image_max_size_spinbox.value() if image_size_mode == 'max_size' else None,
                'image_auto_resize': self.image_auto_resize_checkbox.isChecked() if image_size_mode == 'max_size' else False,
                'quality_variants': quality_variants,
                'multiple_qualities': self.multiple_qualities.isChecked(),
                'resize_variants': resize_values,
                'current_resize': current_resize,
                'rotation_angle': self.image_rotation_angle.currentText(),
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
            
            # Get video size mode settings
            video_size_mode = getattr(self, 'video_size_mode_value', 'manual')
            
            # Handle video size variants
            if hasattr(self, 'multiple_video_variants') and self.multiple_video_variants.isChecked():
                video_variants = self.get_video_variant_values()
                params.update({
                    'type': 'video',
                    'codec': self.video_codec.currentText(),
                    'quality': self.video_quality.value(),
                    'video_size_mode': video_size_mode,  # 'manual' or 'max_size'
                    'video_max_size_mb': self.video_max_size_spinbox.value() if video_size_mode == 'max_size' else None,
                    'video_auto_resize': self.video_auto_resize_checkbox.isChecked() if video_size_mode == 'max_size' else False,
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
                    'video_size_mode': video_size_mode,  # 'manual' or 'max_size'
                    'video_max_size_mb': self.video_max_size_spinbox.value() if video_size_mode == 'max_size' else None,
                    'video_auto_resize': self.video_auto_resize_checkbox.isChecked() if video_size_mode == 'max_size' else False,
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
        self.image_quality_row_label.setVisible(not checked)
        self.quality_variants.setVisible(checked)
        self.quality_variants_label.setVisible(checked)
    
    def toggle_resize_mode(self, checked):
        """Toggle between single and multiple resize modes"""
        # Show/hide appropriate controls
        self.resize_value.setVisible(not checked)
        self.resize_value_label.setVisible(not checked)
        self.resize_variants.setVisible(checked)
        self.resize_variants_label.setVisible(checked)
        
        # Update default values and placeholder based on current mode
        if checked:
            current_mode = self.image_resize_mode.currentText()
            # Auto-select "By longer edge" if currently "No resize"
            if current_mode == "No resize":
                self.image_resize_mode.setCurrentText("By longer edge (pixels)")
                current_mode = "By longer edge (pixels)"
            
            if current_mode == "By ratio (percent)":
                self.resize_variants.setPlaceholderText("e.g., 33,66,90")
                self.resize_variants.setText("33,66")
            else:
                self.resize_variants.setPlaceholderText("e.g., 720,1280,1920")
                self.resize_variants.setText("720,1280,1920")
        else:
            # Set single resize default based on mode
            current_mode = self.image_resize_mode.currentText()
            if current_mode == "By width (pixels)" or current_mode == "By longer edge (pixels)":
                if self.resize_value.value() != 720:
                    self.resize_value.setValue(720)
            elif current_mode == "By ratio (percent)":
                if self.resize_value.value() != 50:
                    self.resize_value.setValue(50)
    
    def on_resize_value_changed(self, value):
        """Save the current resize value based on the current mode"""
        current_mode = self.resize_mode.currentText()
        if current_mode == "By width (pixels)":
            self.last_pixel_value = value
        elif current_mode == "By ratio (percent)":
            self.last_percent_value = value
    
    def get_resize_values(self):
        """Get list of resize values from input - simplified version"""
        resize_mode = self.image_resize_mode.currentText()
        
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
                    elif resize_mode == "By longer edge (pixels)":
                        # Prefix with "L" for longer edge
                        width = int(value)
                        if width > 0:
                            values.append(f"L{width}")
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
                value = self.resize_value.value() if hasattr(self, 'resize_value') else 100
                return [f"{value}%"]
            elif resize_mode == "By width (pixels)":
                value = self.resize_value.value() if hasattr(self, 'resize_value') else 1920
                return [str(value)]
            elif resize_mode == "By longer edge (pixels)":
                value = self.resize_value.value() if hasattr(self, 'resize_value') else 1920
                return [f"L{value}"]
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
        self.gif_dither_quality_label.setText(str(value))

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
        # DEBUG: Print mode changes - COMMENTED OUT
        # print(f"🔵 DEBUG: on_gif_size_mode_changed called with mode='{mode}'")
        
        # Ignore if triggered by resize dropdown values (only care about Max Size vs Manual)
        if mode not in ["Max Size", "Manual"]:
            # print(f"🔵 DEBUG: Ignoring mode '{mode}' - not Max Size or Manual")
            return

        is_max_size = (mode == "Max Size")
        # print(f"🔵 DEBUG: is_max_size={is_max_size}")
        self.gif_size_mode_value = "max_size" if is_max_size else "manual"
        
        # Show/hide max size controls
        self.gif_max_size_label.setVisible(is_max_size)
        self.gif_max_size_spinbox.setVisible(is_max_size)
        self.gif_auto_resize_checkbox.setVisible(is_max_size)
        # self.gif_size_estimate_label.setVisible(is_max_size)  # REMOVED - not in layout anymore
        
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
            
            self.gif_size_estimate_label.setText("")
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

    def on_image_resize_ui_changed(self, mode):
        """Handle Image resize dropdown change - update UI visibility only"""
        # Do not affect settings mode!
        # Uncheck multi-variant toggle if switching to "No resize"
        if mode == "No resize" and hasattr(self, 'multiple_resize') and self.multiple_resize.isChecked():
            self.multiple_resize.blockSignals(True)
            self.multiple_resize.setChecked(False)
            self.multiple_resize.blockSignals(False)
            # Manually trigger the toggle handler to update UI
            self.toggle_resize_mode(False)
        
        # Only show/hide resize input when not in "multiple variants" mode
        if hasattr(self, 'multiple_resize') and self.multiple_resize.isChecked():
            # Update multi-resize defaults when mode changes
            if mode == "By ratio (percent)":
                self.resize_variants.setPlaceholderText("e.g., 33,66,90")
                self.resize_variants.setText("33,66")
            elif mode in ["By width (pixels)", "By longer edge (pixels)"]:
                self.resize_variants.setPlaceholderText("e.g., 720,1280,1920")
                self.resize_variants.setText("720,1280,1920")
            return
            
        if mode == "No resize":
            self.resize_value.setVisible(False)
            self.resize_value_label.setVisible(False)
        else:
            self.resize_value.setVisible(True)
            self.resize_value_label.setVisible(True)
            
            if mode == "By width (pixels)":
                self.resize_value_label.setText("Width (pixels):")
                current_val = self.resize_value.value()
                self.resize_value.setRange(1, 10000)
                if current_val < 1 or current_val > 10000 or current_val == 50:
                    self.resize_value.setValue(720)
            elif mode == "By longer edge (pixels)":
                self.resize_value_label.setText("Longer edge (px):")
                current_val = self.resize_value.value()
                self.resize_value.setRange(1, 10000)
                if current_val < 1 or current_val > 10000 or current_val == 50:
                    self.resize_value.setValue(720)
            elif mode == "By ratio (percent)":
                self.resize_value_label.setText("Percentage:")
                # Check value BEFORE changing range (Qt clamps automatically)
                current_val = self.resize_value.value()
                self.resize_value.setRange(1, 200)
                if current_val < 1 or current_val > 200:
                    self.resize_value.setValue(50)

    def on_video_resize_ui_changed(self, mode):
        """Handle Video resize dropdown change - update UI visibility only"""
        # Do not affect settings mode!
        # Uncheck multi-variant toggle if switching to "No resize"
        if mode == "No resize" and hasattr(self, 'multiple_video_variants') and self.multiple_video_variants.isChecked():
            self.multiple_video_variants.blockSignals(True)
            self.multiple_video_variants.setChecked(False)
            self.multiple_video_variants.blockSignals(False)
            # Manually trigger the toggle handler to update UI
            self.toggle_video_variant_mode(False)
        
        # Only show/hide resize input when not in "multiple variants" mode
        if hasattr(self, 'multiple_video_variants') and self.multiple_video_variants.isChecked():
            # Update multi-resize defaults when mode changes
            if mode == "By ratio (percent)":
                self.video_size_variants.setPlaceholderText("e.g., 33,66,90")
                self.video_size_variants.setText("33,66")
            elif mode in ["By width (pixels)", "By longer edge (pixels)"]:
                self.video_size_variants.setPlaceholderText("e.g., 480,720,960")
                self.video_size_variants.setText("480,720,960")
            return
            
        if mode == "No resize":
            self.video_resize_value.setVisible(False)
            self.video_resize_value_label.setVisible(False)
        else:
            self.video_resize_value.setVisible(True)
            self.video_resize_value_label.setVisible(True)
            
            if mode == "By width (pixels)":
                self.video_resize_value_label.setText("Width (pixels):")
                current_val = self.video_resize_value.value()
                self.video_resize_value.setRange(1, 10000)
                if current_val < 1 or current_val > 10000 or current_val == 50:
                    self.video_resize_value.setValue(640)
            elif mode == "By longer edge (pixels)":
                self.video_resize_value_label.setText("Longer edge (px):")
                current_val = self.video_resize_value.value()
                self.video_resize_value.setRange(1, 10000)
                if current_val < 1 or current_val > 10000 or current_val == 50:
                    self.video_resize_value.setValue(640)
            elif mode == "By ratio (percent)":
                self.video_resize_value_label.setText("Percentage:")
                # Check value BEFORE changing range (Qt clamps automatically)
                current_val = self.video_resize_value.value()
                self.video_resize_value.setRange(1, 200)
                if current_val < 1 or current_val > 200:
                    self.video_resize_value.setValue(50)

    def on_gif_resize_ui_changed(self, mode):
        """Handle GIF resize dropdown change - update UI visibility only"""
        # Do not affect settings mode!
        # Uncheck multi-variant toggle if switching to "No resize"
        if mode == "No resize" and hasattr(self, 'gif_multiple_resize') and self.gif_multiple_resize.isChecked():
            # Uncheck the toggle and update UI
            self.gif_multiple_resize.setChecked(False)
            # Hide the variant controls
            self.gif_resize_variants.setVisible(False)
            self.gif_resize_variants_label.setVisible(False)
            # Note: No need to show single resize controls since "No resize" hides them anyway
        
        # Only show/hide resize input when not in "multiple variants" mode
        if hasattr(self, 'gif_multiple_resize') and self.gif_multiple_resize.isChecked():
            return
            
        if mode == "No resize":
            self.gif_resize_value.setVisible(False)
            self.gif_resize_value_label.setVisible(False)
        else:
            self.gif_resize_value.setVisible(True)
            self.gif_resize_value_label.setVisible(True)
            
            if mode == "By width (pixels)":
                self.gif_resize_value_label.setText("Width (pixels):")
                current_val = self.gif_resize_value.value()
                self.gif_resize_value.setRange(1, 10000)
                if current_val < 1 or current_val > 10000 or current_val == 33:
                    self.gif_resize_value.setValue(360)
            elif mode == "By longer edge (pixels)":
                self.gif_resize_value_label.setText("Longer edge (px):")
                current_val = self.gif_resize_value.value()
                self.gif_resize_value.setRange(1, 10000)
                if current_val < 1 or current_val > 10000 or current_val == 33:
                    self.gif_resize_value.setValue(360)
            elif mode == "By ratio (percent)":
                self.gif_resize_value_label.setText("Percentage:")
                # Check value BEFORE changing range (Qt clamps automatically)
                current_val = self.gif_resize_value.value()
                self.gif_resize_value.setRange(1, 200)
                if current_val < 1 or current_val > 200:
                    self.gif_resize_value.setValue(33)

    def on_image_size_mode_changed(self, mode):
        """Handle Image size mode change between Manual and Max Size"""
        # Ignore if triggered by resize dropdown values (only care about Max Size vs Manual)
        if mode not in ["Max Size", "Manual"]:
            return
            
        is_max_size = (mode == "Max Size")
        self.image_size_mode_value = "max_size" if is_max_size else "manual"
        
        # Show/hide max size controls
        self.image_max_size_label.setVisible(is_max_size)
        self.image_max_size_spinbox.setVisible(is_max_size)
        self.image_auto_resize_checkbox.setVisible(is_max_size)
        
        if is_max_size:
            # Hide manual quality controls in Max Size mode
            self.multiple_qualities.setChecked(False)
            self.multiple_qualities.setVisible(False)
            
            self.image_quality.setVisible(False)
            self.image_quality_label.setVisible(False)
            self.image_quality_row_label.setVisible(False)
            
            self.quality_variants.setVisible(False)
            self.quality_variants_label.setVisible(False)
        else:
            # Show manual controls in Manual mode
            self.multiple_qualities.setVisible(True)
            
            # Show quality controls based on multiple_qualities state
            variants_enabled = self.multiple_qualities.isChecked()
            self.image_quality.setVisible(not variants_enabled)
            self.image_quality_label.setVisible(not variants_enabled)
            self.image_quality_row_label.setVisible(not variants_enabled)
            
            self.quality_variants.setVisible(variants_enabled)
            self.quality_variants_label.setVisible(variants_enabled)

    def on_video_size_mode_changed(self, mode):
        """Handle Video size mode change between Manual and Max Size"""
        # Ignore if triggered by resize dropdown values (only care about Max Size vs Manual)
        if mode not in ["Max Size", "Manual"]:
            return
            
        is_max_size = (mode == "Max Size")
        self.video_size_mode_value = "max_size" if is_max_size else "manual"
        
        # Show/hide max size controls
        self.video_max_size_label.setVisible(is_max_size)
        self.video_max_size_spinbox.setVisible(is_max_size)
        self.video_auto_resize_checkbox.setVisible(is_max_size)
        
        if is_max_size:
            # Hide manual quality controls in Max Size mode
            self.multiple_video_qualities.setChecked(False)
            self.multiple_video_qualities.setVisible(False)
            
            self.video_quality.setVisible(False)
            self.video_quality_label.setVisible(False)
            self.video_quality_value.setVisible(False)
            
            self.video_quality_variants.setVisible(False)
            self.video_quality_variants_label.setVisible(False)
        else:
            # Show manual controls in Manual mode
            self.multiple_video_qualities.setVisible(True)
            
            # Show quality controls based on multiple_qualities state
            variants_enabled = self.multiple_video_qualities.isChecked()
            self.video_quality.setVisible(not variants_enabled)
            self.video_quality_label.setVisible(not variants_enabled)
            self.video_quality_value.setVisible(not variants_enabled)
            
            self.video_quality_variants.setVisible(variants_enabled)
            self.video_quality_variants_label.setVisible(variants_enabled)

    def toggle_video_variant_mode(self, checked):
        """Toggle between single and multiple video size variant modes"""
        # Show/hide video variant controls
        self.video_size_variants.setVisible(checked)
        self.video_size_variants_label.setVisible(checked)
        
        # Auto-select "By longer edge" if currently "No resize" when enabling variants
        if checked and self.video_resize_mode.currentText() == "No resize":
            self.video_resize_mode.setCurrentText("By longer edge (pixels)")
        
        # Hide single resize controls when using variants
        if checked:
            self.video_resize_value.setVisible(False)
            self.video_resize_value_label.setVisible(False)
            # Update placeholder and default values based on current mode
            current_mode = self.video_resize_mode.currentText()
            if current_mode == "By ratio (percent)":
                self.video_size_variants.setPlaceholderText("e.g., 33,66,90")
                self.video_size_variants.setText("33,66")
            else:
                self.video_size_variants.setPlaceholderText("e.g., 480,720,960")
                self.video_size_variants.setText("480,720,960")
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
                        self.video_resize_value.setValue(640)
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
        # Uncheck multi-variant toggle if switching to "No resize"
        if mode == "No resize" and hasattr(self, 'gif_multiple_resize') and self.gif_multiple_resize.isChecked():
            self.gif_multiple_resize.blockSignals(True)
            self.gif_multiple_resize.setChecked(False)
            self.gif_multiple_resize.blockSignals(False)
            # Manually trigger the toggle handler to update UI
            self.toggle_gif_resize_variant_mode(False)
        
        # Check if multiple variants mode is active - if so, don't show single controls
        multiple_enabled = hasattr(self, 'gif_multiple_resize') and self.gif_multiple_resize.isChecked()
        
        if mode == "No resize" or multiple_enabled:
            self.gif_resize_value.setVisible(False)
            self.gif_resize_value_label.setVisible(False)
        elif mode == "By ratio (percent)":
            self.gif_resize_value.setVisible(True)
            self.gif_resize_value_label.setVisible(True)
            self.gif_resize_value_label.setText("Percentage:")
            current_val = self.gif_resize_value.value()
            self.gif_resize_value.setRange(1, 200)
            if current_val < 1 or current_val > 200:
                self.gif_resize_value.setValue(33)  # Default 33%
            self.gif_resize_value.setSuffix("")
        elif mode == "By width (pixels)":
            self.gif_resize_value.setVisible(True)
            self.gif_resize_value_label.setVisible(True)
            self.gif_resize_value_label.setText("Width (pixels):")
            current_val = self.gif_resize_value.value()
            self.gif_resize_value.setRange(1, 10000)
            if current_val < 1 or current_val > 10000 or current_val == 33:
                self.gif_resize_value.setValue(360)  # Default 360px
            self.gif_resize_value.setSuffix("")
            
        # Update variants if multiple mode is enabled
        if multiple_enabled:
            if mode == "By ratio (percent)":
                self.gif_resize_variants.setPlaceholderText("e.g., 33,66,90")
                self.gif_resize_variants.setText("33,66")
            else:
                self.gif_resize_variants.setPlaceholderText("e.g., 240,360,480")
                self.gif_resize_variants.setText("240,360,480")
                
    def toggle_gif_resize_variant_mode(self, checked):
        """Toggle between single and multiple GIF resize variant modes"""
        # Show/hide resize variant controls
        self.gif_resize_variants.setVisible(checked)
        self.gif_resize_variants_label.setVisible(checked)
        
        # Auto-select "By longer edge" if currently "No resize" when enabling variants
        if checked and self.gif_resize_mode.currentText() == "No resize":
            self.gif_resize_mode.setCurrentText("By longer edge (pixels)")
        
        # Hide single resize controls when using variants
        if checked:
            self.gif_resize_value.setVisible(False)
            self.gif_resize_value_label.setVisible(False)
            # Update placeholder and default values based on current mode
            current_mode = self.gif_resize_mode.currentText()
            if current_mode == "By width (pixels)" or current_mode == "By longer edge (pixels)":
                self.gif_resize_variants.setPlaceholderText("e.g., 240,360,480")
                self.gif_resize_variants.setText("240,360,480")
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










