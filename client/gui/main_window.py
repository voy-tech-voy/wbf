"""
Main Window for Graphics Conversion App
Implements the layout: Top Bar | Mid Section (Drag-Drop + Commands) | Bottom Bar
"""

import sys
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMenuBar, QToolBar, QStatusBar, QSplitter,
    QListWidget, QTextEdit, QLabel, QPushButton,
    QFrame, QGroupBox, QProgressBar, QMessageBox, QDialog, QApplication,
    QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QIcon, QDragEnterEvent, QDropEvent, QFont, QMouseEvent, QAction, QColor
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QSize, pyqtSlot, pyqtProperty, QRect
import os
import ctypes
from ctypes import POINTER, Structure, c_int, byref, windll, sizeof

from .drag_drop_area import DragDropArea
from .command_panel import CommandPanel
from .output_footer import OutputFooter
from .theme_manager import ThemeManager
from client.core.conversion_engine import ConversionEngine, ToolChecker
from client.gui.custom_widgets import PresetStatusButton
from client.utils.trial_manager import TrialManager
from client.utils.font_manager import AppFonts, FONT_FAMILY_APP_NAME
from client.utils.resource_path import get_app_icon_path, get_resource_path
from client.version import APP_NAME, AUTHOR

from PyQt6.QtCore import QObject, QEvent, QTimer

DEBUG_INTERACTIVITY = True

class EventDebugFilter(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress:
            # Only care about left click press for triggering actions
            if hasattr(event, 'button') and event.button() != Qt.MouseButton.LeftButton:
                return False
                
            # Helper to get hierarchy
            def get_hierarchy(w):
                chain = []
                curr = w
                while curr:
                    name = curr.objectName() or curr.__class__.__name__
                    chain.append(name)
                    curr = curr.parent()
                return " -> ".join(chain)
            
            hierarchy = get_hierarchy(obj)
            
            # --- 1. PRESETS STATUS ---
            top_level = None
            if hasattr(obj, 'window'):
                top_level = obj.window()
            
            preset_mode = "OFF"
            if top_level and hasattr(top_level, 'preset_status_btn'):
                if top_level.preset_status_btn._is_active:
                    preset_mode = "ON"
            
            # --- 2. DETECT LAB CLICK ---
            lab_action = None
            
            # Check hierarchy for MorphingButton
            curr = obj
            while curr:
                if "MorphingButton" in curr.__class__.__name__:
                    # Found Lab Button
                    mb = curr
                    # Check if obj is one of the sub-items
                    if hasattr(mb, '_items') and obj in mb._items:
                        idx = mb._items.index(obj)
                        type_map = {0: "IMAGE", 1: "VIDEO", 2: "LOOP"}
                        lab_action = type_map.get(idx, "UNKNOWN")
                    break
                curr = curr.parent()
            
            if lab_action:
                print(f"\n>>> DEBUG EVENT: Click inside Lab Button")
                print(f"    Preset Mode: {preset_mode}")
                print(f"    Target: {lab_action}")
            elif "PresetStatusButton" in hierarchy:
                print(f"\n>>> DEBUG EVENT: Click on Preset Button")
                print(f"    Current Mode: {preset_mode}")
                
            return False
                         
            return False 
            
        return super().eventFilter(obj, event)

class DraggableTitleBar(QFrame):
    """Custom title bar that allows dragging the window"""
    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window
        self.drag_position = None
        
    def mousePressEvent(self, event: QMouseEvent):
        """Store the mouse position when pressed"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Allow resizing on top edge - propagate to parent if near top
            if event.position().y() <= 5:
                event.ignore()
                return
                
            self.drag_position = event.globalPosition().toPoint() - self.parent_window.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event: QMouseEvent):
        """Move the window when dragging"""
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position is not None:
            self.parent_window.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
        else:
            super().mouseMoveEvent(event)
        
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Clear drag position when released"""
        self.drag_position = None
        super().mouseReleaseEvent(event)

class ClickableLabel(QLabel):
    """Custom label that emits a signal when clicked"""
    clicked = pyqtSignal()
    
    def mousePressEvent(self, event: QMouseEvent):
        """Emit signal when label is clicked"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

class MainWindow(QMainWindow):
    def __init__(self, is_trial=False):
        super().__init__()
        
        # Install interactive debugger
        if DEBUG_INTERACTIVITY:
            self._debug_filter = EventDebugFilter()
            QApplication.instance().installEventFilter(self._debug_filter)
            print("[DEBUG] Interactive Debug Filter Installed")
            
        self.is_trial = is_trial
        
        # Development mode detection
        self.DEVELOPMENT_MODE = getattr(sys, '_called_from_test', False) or __debug__ and not getattr(sys, 'frozen', False)
        
        title = APP_NAME
        if self.is_trial:
            title += " [TRIAL]"  # Shortened for title bar consistency
        if self.DEVELOPMENT_MODE:
            title += " [DEV]"
            
        self.setWindowTitle(title)
        
        # Make window frameless for custom title bar & transparent for rounded corners
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAcceptDrops(True) # Ensure window accepts drops for the overlay logic
            
        self.setGeometry(100, 100, 1200, 1000)
        self.setMinimumSize(800, 700)
        self.setMouseTracking(True)  # Enable mouse tracking for edge resize cursors
        
        if self.is_trial:
            self.trial_manager = TrialManager()
            # Auto-reset trial in development mode
            if self.DEVELOPMENT_MODE:
                print("[DEV] Resetting trial usage...")
                self.trial_manager.reset_trial_usage()
        
        # Set window icon if available
        try:
            from PyQt6.QtGui import QIcon
            from client.utils.resource_path import get_app_icon_path
            
            icon_path = get_app_icon_path()
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            print(f"Could not set window icon: {e}")
        
        # Conversion engine
        self.conversion_engine = None
        
        # Theme management
        self.theme_manager = ThemeManager()
        
        # Track mouse position for window dragging
        self.drag_position = None
        
        self.setup_ui()
        self.setup_status_bar()
        self.connect_signals()
        self.apply_theme()
        self.check_tools()
        
        # Reset drop area rendering after 1ms
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(1, self.drag_drop_area.clear_files)
        
    def setup_ui(self):
        """Setup the main user interface layout"""
        central_widget = QWidget()
        central_widget.setMouseTracking(True)
        self.setCentralWidget(central_widget)
        
        # Main vertical layout (No margins - direct window edge)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)  # No margins
        
        # Root Frame (The visible container)
        self.root_frame = QFrame()
        self.root_frame.setMouseTracking(True)
        self.root_frame.setObjectName("RootFrame")
        # No shadow effect - clean window edges
        
        main_layout.addWidget(self.root_frame)
        
        # Root Layout inside the frame
        root_layout = QVBoxLayout(self.root_frame)
        root_layout.setSpacing(0)
        root_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add custom title bar
        self.create_title_bar(root_layout)
        QApplication.processEvents()
        
        # Content area container (opaque)
        self.content_container = QFrame()
        self.content_container.setObjectName("ContentFrame")
        content_layout = QVBoxLayout(self.content_container)
        content_layout.setSpacing(5)
        content_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create unified control bar (File Buttons | Preset | Lab)
        self.create_control_bar(content_layout)
        
        # Create the middle section with splitter
        self.create_middle_section(content_layout)
        
        # Bottom section (status and progress)
        self.create_bottom_section(content_layout)
        
        # Create output footer
        self.output_footer = OutputFooter()
        self.output_footer.start_conversion.connect(self.start_conversion)
        self.output_footer.stop_conversion.connect(self.stop_conversion)
        content_layout.addWidget(self.output_footer)
        
        # Add content container to root layout
        root_layout.addWidget(self.content_container)

        # Note: Preset overlay is now inside DragDropArea
        
        # Process events to keep splash screen animated
        QApplication.processEvents()
    
    def create_control_bar(self, parent_layout):
        """Create the unified control bar with file buttons, preset, and lab button"""
        from PyQt6.QtCore import QSize
        from PyQt6.QtGui import QCursor
        from client.gui.drag_drop_area import HoverIconButton
        from client.gui.custom_widgets import PresetStatusButton, MorphingButton
        
        control_bar = QWidget()
        control_bar.setFixedHeight(64)  # Match button heights + padding
        control_bar.setObjectName("ControlBar")
        
        control_layout = QHBoxLayout(control_bar)
        control_layout.setContentsMargins(16, 8, 16, 8)
        control_layout.setSpacing(8)
        
        # --- Left Section: File Buttons ---
        icon_size = QSize(28, 28)
        
        self.add_files_btn = HoverIconButton("addfile.svg", icon_size)
        self.add_files_btn.setFixedSize(48, 48)
        self.add_files_btn.setToolTip("Add Files")
        self.add_files_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        self.add_folder_btn = HoverIconButton("addfolder.svg", icon_size)
        self.add_folder_btn.setFixedSize(48, 48)
        self.add_folder_btn.setToolTip("Add Folder")
        self.add_folder_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        self.clear_files_btn = HoverIconButton("removefile.svg", icon_size)
        self.clear_files_btn.setFixedSize(48, 48)
        self.clear_files_btn.setToolTip("Clear All")
        self.clear_files_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # Apply Styles
        # Standard Action Button Style
        base_style = """
            QPushButton {
                background-color: rgba(255, 255, 255, 5);
                border: 1px solid rgba(255, 255, 255, 20);
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 10);
                border: 1px solid rgba(255, 255, 255, 50);
            }
            QPushButton:pressed {
                background-color: rgba(0, 0, 0, 50);
            }
        """
        self.add_files_btn.setStyleSheet(base_style)
        self.add_folder_btn.setStyleSheet(base_style)
        
        # Clear Button Style (Red Outline)
        # Clear Button Style (Red Outline ONLY on Hover)
        clear_style = """
            QPushButton {
                background-color: rgba(255, 255, 255, 5);
                border: 1px solid rgba(255, 255, 255, 20);
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: rgba(255, 50, 50, 15);
                border: 1px solid #FF4444;
            }
            QPushButton:pressed {
                background-color: rgba(50, 0, 0, 50);
            }
        """
        self.clear_files_btn.setStyleSheet(clear_style)
        
        control_layout.addWidget(self.add_files_btn)
        control_layout.addWidget(self.add_folder_btn)
        control_layout.addWidget(self.clear_files_btn)
        
        # --- Spacer (Left) ---
        control_layout.addStretch()
        
        # --- Center: Preset Button ---
        self.preset_status_btn = PresetStatusButton()
        self.preset_status_btn.clicked.connect(self._on_preset_btn_clicked)
        control_layout.addWidget(self.preset_status_btn)
        
        # --- Spacer (Right) ---
        control_layout.addStretch()
        
        # --- Right: Lab Button (in fixed-width container to prevent layout shift) ---
        lab_container = QWidget()
        lab_container.setFixedWidth(220)  # Slightly larger than EXPANDED_WIDTH to prevent clipping
        lab_container_layout = QHBoxLayout(lab_container)
        lab_container_layout.setContentsMargins(0, 0, 0, 0)
        lab_container_layout.setSpacing(0)
        lab_container_layout.addStretch()  # Push lab button to right edge
        
        self.lab_btn = MorphingButton(main_icon_path="client/assets/icons/lab_icon.svg")
        self.lab_btn.add_menu_item(0, "client/assets/icons/pic_icon2.svg", "Image Conversion")
        self.lab_btn.add_menu_item(1, "client/assets/icons/vid_icon2.svg", "Video Conversion")
        self.lab_btn.add_menu_item(2, "client/assets/icons/loop_icon3.svg", "Loop Conversion")
        self.lab_btn.itemClicked.connect(self._on_lab_item_clicked)
        lab_container_layout.addWidget(self.lab_btn)
        
        control_layout.addWidget(lab_container)
        
        parent_layout.addWidget(control_bar)
        
        # Store reference
        self.control_bar = control_bar
    
    def _on_preset_btn_clicked(self):
        """Handle preset button click - show preset overlay"""
        # 1. Hide Command Panel
        self.toggle_command_panel(False)
        
        # 2. Deactivate Lab Button (Ghost style)
        if hasattr(self, 'lab_btn'):
            self.lab_btn.set_style_solid(False)
            self.lab_btn.set_main_icon("client/assets/icons/lab_icon.svg")
            
        # 3. Notify CommandPanel state
        if hasattr(self, 'command_panel'):
            self.command_panel.set_lab_mode_active(False)
            self.command_panel.set_top_bar_preset_mode(True)
            
        # 4. Show Overlay
        if hasattr(self, 'drag_drop_area'):
            self.drag_drop_area.show_preset_view()
    
    def _on_lab_item_clicked(self, item_id):
        """Handle lab button menu item click"""
        type_map = {0: "IMAGE", 1: "VIDEO", 2: "LOOP"}
        print(f"[DEBUG_MAIN] Lab item clicked. ID={item_id} ({type_map.get(item_id, 'UNKNOWN')})")
        
        # Icon paths matching tab order
        icons = [
            "client/assets/icons/pic_icon2.svg",
            "client/assets/icons/vid_icon2.svg",
            "client/assets/icons/loop_icon3.svg"
        ]
        
        # Update lab button immediately
        if 0 <= item_id < len(icons):
            self.lab_btn.set_main_icon(icons[item_id])
            self.lab_btn.set_style_solid(True)
        
        # Reset Preset button to default state (Lab mode = not in preset mode)
        if hasattr(self, 'preset_status_btn'):
            self.preset_status_btn.set_active(False)  # Reverts to "PRESETS" with ghost styling
        
        # Notify CommandPanel that Lab mode is active
        if hasattr(self, 'command_panel'):
            self.command_panel.set_lab_mode_active(True)
            self.command_panel.set_top_bar_preset_mode(False)  # Exiting preset mode
        
        
        # Forward to command panel for tab switching
        if hasattr(self, 'command_panel'):
            self.command_panel._on_tab_btn_clicked(item_id)
        
        # Only hide side buttons if panel is not already visible
        # If panel is already open (switching tabs), keep buttons visible
        panel_already_visible = self.right_frame.isVisible()
        
        if not panel_already_visible:
            # CRITICAL: Hide side buttons BEFORE panel animation starts
            # This ensures the stagger animation in toggle_command_panel controls visibility
            self._trigger_side_buttons_animation(hide=True)
            
        # Show Command Panel with animation (stagger will reveal buttons at threshold)
        self.toggle_command_panel(True)
        
    def create_title_bar(self, parent_layout):
        """Create custom title bar with logo, theme toggle, menu, and window controls"""
        # Use a custom frame to handle mouse events for dragging
        title_bar = DraggableTitleBar(self)
        title_bar.setMinimumHeight(45)
        title_bar.setMaximumHeight(45)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 5, 10, 5)
        title_layout.setSpacing(10)
        
        # Logo on the left (clickable)
        try:
            from client.utils.resource_path import get_app_icon_path
            icon_path = get_app_icon_path()
            if os.path.exists(icon_path):
                logo_label = ClickableLabel()
                icon = QIcon(icon_path)
                logo_label.setPixmap(icon.pixmap(32, 32))
                logo_label.setMaximumWidth(40)
                logo_label.setCursor(Qt.CursorShape.PointingHandCursor)
                logo_label.setStyleSheet("border: none; padding: 0px; margin: 0px; background: transparent;")
                title_layout.addWidget(logo_label)
                self.logo_label = logo_label
        except Exception as e:
            print(f"Could not load logo: {e}")
        
        # Title label (clickable)
        from client.utils.font_manager import FONT_FAMILY
        
        # Explicitly apply App Name font via HTML to ensure it works
        title_text = f'<span style="font-family: \'{FONT_FAMILY_APP_NAME}\'; font-weight: bold;">{APP_NAME}</span>'
        
        if self.is_trial:
            title_text += f'&nbsp;&nbsp;<span style="font-family: \'{FONT_FAMILY}\'; font-weight: normal; font-size: 10pt;">[ TRIAL ]</span>'
        if self.DEVELOPMENT_MODE:
            title_text += f'&nbsp;&nbsp;<span style="font-family: \'{FONT_FAMILY}\'; font-weight: normal; font-size: 10pt;">[ DEV ]</span>'
            
        title_label = ClickableLabel(title_text)
        title_label.setTextFormat(Qt.TextFormat.RichText)
        # setFont is still useful as fallback or base sizing
        title_label.setFont(AppFonts.get_app_name_font())
        title_label.setStyleSheet("color: #ffffff; border: none; padding: 0px; margin: 0px; text-decoration: none;")
        title_label.setCursor(Qt.CursorShape.PointingHandCursor)
        title_layout.addWidget(title_label)
        
        # Theme toggle button (Moon/Sun SVG)
        self.theme_toggle_btn = QPushButton()
        self.theme_toggle_btn.setMinimumWidth(40)
        self.theme_toggle_btn.setMinimumHeight(35)
        self.theme_toggle_btn.setMaximumWidth(40)
        self.theme_toggle_btn.setMaximumHeight(35)
        self.theme_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Load SVG icon for theme toggle
        try:
            svg_path = get_resource_path('client/assets/icons/sun-moon.svg')
            if os.path.exists(svg_path):
                self.sun_moon_svg_path = svg_path
                icon = QIcon(svg_path)
                self.theme_toggle_btn.setIcon(icon)
                self.theme_toggle_btn.setIconSize(QSize(24, 21))  # 60% of button size (40x35)
        except Exception as e:
            print(f"Could not load theme toggle icon: {e}")
            self.theme_toggle_btn.setText("◐")
        self.theme_toggle_btn.clicked.connect(self.toggle_theme)
        self.theme_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Create dropdown menu
        from PyQt6.QtWidgets import QMenu
        self.title_menu = QMenu()
        
        
        advanced_action = QAction("Advanced", self)
        advanced_action.triggered.connect(self.show_advanced)
        self.title_menu.addAction(advanced_action)

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        self.title_menu.addAction(about_action)
        
        show_log_action = QAction("Show Log", self)
        show_log_action.triggered.connect(self.toggle_status_bar)
        self.title_menu.addAction(show_log_action)
        
        self.title_menu.addSeparator()

        logout_action = QAction("Log Out", self)
        logout_action.triggered.connect(self.logout)
        self.title_menu.addAction(logout_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        self.title_menu.addAction(exit_action)
        
        # Status Bar Toggle
        self.status_action = QAction("Show Status Bar", self)
        self.status_action.setCheckable(True)
        self.status_action.setChecked(False) 
        self.status_action.triggered.connect(self.toggle_status_bar)
        
        self.title_menu.addSeparator()
        self.title_menu.addAction(self.status_action)
        
        # Connect logo and title clicks to menu
        if hasattr(self, 'logo_label'):
            self.logo_label.clicked.connect(self.show_title_menu)
        title_label.clicked.connect(self.show_title_menu)
        
        # Spacer
        title_layout.addStretch()
        
        # Add theme toggle before minimize buttons
        title_layout.addWidget(self.theme_toggle_btn)
        
        # Minimize button
        minimize_btn = QPushButton("—")
        minimize_btn.setMinimumWidth(45)
        minimize_btn.setMinimumHeight(35)
        minimize_btn.setMaximumWidth(45)
        minimize_btn.setMaximumHeight(35)
        minimize_btn.clicked.connect(self.showMinimized)
        minimize_btn.setFont(AppFonts.get_button_font())
        minimize_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Close button
        close_btn = QPushButton("✕")
        close_btn.setMinimumWidth(45)
        close_btn.setMinimumHeight(35)
        close_btn.setMaximumWidth(45)
        close_btn.setMaximumHeight(35)
        close_btn.clicked.connect(self.close)
        close_btn.setFont(AppFonts.get_button_font())
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        title_layout.addWidget(minimize_btn)
        title_layout.addSpacing(10)
        title_layout.addWidget(close_btn)
        
        # Store references for theme updates
        self.title_bar = title_bar
        self.title_label = title_label
        self.minimize_btn = minimize_btn
        self.close_btn = close_btn
        
        parent_layout.addWidget(title_bar)
        
    def show_title_menu(self):
        """Show the title bar menu below the title"""
        # Show menu at cursor position relative to the window
        menu_pos = self.mapToGlobal(QPoint(100, 50))
        self.title_menu.popup(menu_pos)
        
    def create_middle_section(self, parent_layout):
        """Create the split middle section with drag-drop and command areas"""
        # Create horizontal splitter for left and right panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(0)  # Hide splitter handle visual
        splitter.setStyleSheet("QSplitter::handle { background: transparent; border: none; }")
        
        # Store splitter reference for styling
        self.splitter = splitter
        
        # Left panel - Drag and Drop Area (no frame)
        left_frame = QWidget()
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        
        self.drag_drop_area = DragDropArea()
        left_layout.addWidget(self.drag_drop_area)
        
        # Right panel - Command Panel (no frame)
        right_frame = QWidget()
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        self.command_panel = CommandPanel()
        self.command_panel.setMinimumWidth(0) # Ensure it can animate from 0
        right_layout.addWidget(self.command_panel)
        
        # Store right frame reference for toggling
        self.right_frame = right_frame
        self.right_frame.setMinimumWidth(0) # Ensure frame can animate from 0
        self.right_frame.setVisible(False)  # Hidden on init
        
        # Add panels to splitter
        splitter.addWidget(left_frame)
        splitter.addWidget(right_frame)
        
        # Set initial sizes (100% left, 0% right)
        # Note: Since right_frame is hidden, sizes might be ignored, but good to set
        splitter.setSizes([1200, 0])
        
        parent_layout.addWidget(splitter)

    # =========================================================================
    # COMMAND PANEL SLIDE ANIMATION
    # =========================================================================
    # All animation logic for the right-side command panel is contained here.
    # The panel slides in from the right edge when Lab mode is activated,
    # and slides out when switching to Preset mode.
    #
    # Design Spec Reference (styles_instruction.md):
    #   - Animations should feel premium with weighted motion
    #   - OutQuad or OutBack for smooth deceleration
    #   - Spring effects add premium feel (OutBack with overshoot)
    # =========================================================================
    
    # -------------------------------------------------------------------------
    # ANIMATION CONFIGURATION - Edit these values to tune the animation feel
    # -------------------------------------------------------------------------
    
    # Panel Size
    PANEL_TARGET_RATIO = 0.4  # Right panel takes 40% of total splitter width
    
    # Panel Timing (milliseconds)
    PANEL_SHOW_DURATION_MS = 450   # Slide-in duration (snappy entrance)
    PANEL_HIDE_DURATION_MS = 500   # Slide-out duration (snappy exit with weight)
    
    # Panel Easing Curve Options:
    #   "Linear"     - Constant speed (basic)
    #   "OutQuad"    - Smooth deceleration (design spec recommended)
    #   "OutCubic"   - Smoother deceleration
    #   "OutExpo"    - Sharp start, smooth end
    #   "OutBack"    - Overshoot with spring (premium weighted feel)
    #   "OutElastic" - Bouncy spring (use sparingly)
    PANEL_SHOW_EASING = "OutBack"   # Premium weighted entrance
    PANEL_HIDE_EASING = "OutBack"   # Weighted exit with subtle overshoot
    
    # Panel Spring Parameters (only applies to OutBack easing)
    PANEL_SPRING_OVERSHOOT = 0.7   # 0.0 = no spring, 1.7 = default, 0.5-0.8 = subtle
    PANEL_HIDE_OVERSHOOT = 0.5     # Overshoot for hide animation (more subtle than show)
    
    # -------------------------------------------------------------------------
    # SIDE BUTTONS STAGGERED ANIMATION
    # -------------------------------------------------------------------------
    # Side buttons (transform controls) appear in a staggered sequence during
    # the panel slide animation. They start revealing when the panel reaches
    # a certain progress threshold and fade in one after another.
    #
    # On HIDE: Buttons hide simultaneously first, then panel slides out.
    # -------------------------------------------------------------------------
    
    # ---- SHOW Animation ----
    # When to start showing buttons (0.0 - 1.0 of panel animation progress)
    BUTTONS_REVEAL_THRESHOLD = 0.9
    
    # Stagger delay between each button appearing (milliseconds)
    BUTTONS_SHOW_STAGGER_MS = 60
    
    # Button show animation duration (milliseconds)  
    BUTTONS_SHOW_DURATION_MS = 200
    
    # Button show easing
    BUTTONS_SHOW_EASING = "OutCubic"
    
    # ---- HIDE Animation ----
    # All buttons hide simultaneously (no stagger on hide)
    BUTTONS_HIDE_DURATION_MS = 100   # Visible hide animation for better feedback
    
    # Button hide easing (InQuad = accelerate into hide)
    BUTTONS_HIDE_EASING = "InQuad"
    
    # Delay AFTER buttons start hiding before panel slides out (milliseconds)
    # This is the time for buttons to reach the panel edge
    BUTTONS_HIDE_HEAD_START_MS = 200   # Let buttons hide before panel slides out
    
    # -------------------------------------------------------------------------
    
    def toggle_command_panel(self, show):
        """
        Animate Command Panel sliding in/out from the RIGHT edge.
        
        Premium Animation Features:
        - Weighted motion with spring overshoot (OutBack easing)
        - Separate timing/easing for show vs hide 
        - MaximumWidth constraint prevents layout "pop" artifact
        - Staggered side button reveal at configurable threshold
        - Sequential hide: buttons first, then panel
        
        Args:
            show: True to slide panel in, False to slide it out
        """
        # Early exit if already in the requested state
        if show == self.right_frame.isVisible():
            return
            
        from PyQt6.QtCore import QVariantAnimation, QEasingCurve, QTimer
        
        # --- Stop any running animation ---
        if hasattr(self, '_panel_anim') and self._panel_anim.state() == QVariantAnimation.State.Running:
            self._panel_anim.stop()
        
        # --- Calculate dimensions ---
        current_sizes = self.splitter.sizes()
        total_width = sum(current_sizes)
        target_right_width = int(total_width * self.PANEL_TARGET_RATIO)
        
        # Track whether we've triggered side buttons (to avoid re-triggering)
        self._buttons_triggered = False
        
        # --- Prepare start/end values based on direction ---
        if show:
            # SHOWING: Panel slides in from right edge (0 → target width)
            # CRITICAL: Set maximumWidth to 0 BEFORE setVisible(True)
            # This prevents Qt from assigning any width during the initial layout pass
            self.right_frame.setMaximumWidth(0)
            self.right_frame.setVisible(True)
            self.splitter.setSizes([total_width, 0])
            
            start_width = 0
            end_width = target_right_width
            duration = self.PANEL_SHOW_DURATION_MS
            easing_name = self.PANEL_SHOW_EASING
            
            # Start panel animation immediately for show
            self._start_panel_animation(show, start_width, end_width, duration, easing_name, total_width, target_right_width)
        else:
            # HIDING: Sequential animation - buttons first, then panel
            # 1. Hide all buttons simultaneously
            self._trigger_side_buttons_animation(hide=True)
            
            # 2. Schedule panel to slide out AFTER buttons reach panel edge
            start_width = current_sizes[1]
            end_width = 0
            duration = self.PANEL_HIDE_DURATION_MS
            easing_name = self.PANEL_HIDE_EASING
            
            # Delay panel hide to let buttons hide first
            QTimer.singleShot(
                self.BUTTONS_HIDE_HEAD_START_MS,
                lambda: self._start_panel_animation(show, start_width, end_width, duration, easing_name, total_width, target_right_width)
            )
    
    def _start_panel_animation(self, show, start_width, end_width, duration, easing_name, total_width, target_right_width):
        """
        Internal helper to start the panel slide animation.
        
        Args:
            show: True if showing panel, False if hiding
            start_width: Starting width of the right panel
            end_width: Target width of the right panel
            duration: Animation duration in ms
            easing_name: Name of the easing curve
            total_width: Total width of the splitter
            target_right_width: Target width when fully open
        """
        from PyQt6.QtCore import QVariantAnimation, QEasingCurve
        
        # Stop any running animation
        if hasattr(self, '_panel_anim') and self._panel_anim.state() == QVariantAnimation.State.Running:
            self._panel_anim.stop()
        
        # Create and configure animation
        self._panel_anim = QVariantAnimation()
        self._panel_anim.setDuration(duration)
        
        # Build easing curve with optional spring parameters
        easing_map = {
            "Linear": QEasingCurve.Type.Linear,
            "OutQuad": QEasingCurve.Type.OutQuad,
            "OutCubic": QEasingCurve.Type.OutCubic,
            "OutExpo": QEasingCurve.Type.OutExpo,
            "OutBack": QEasingCurve.Type.OutBack,
            "OutElastic": QEasingCurve.Type.OutElastic,
            "InOutCubic": QEasingCurve.Type.InOutCubic,
            "InQuad": QEasingCurve.Type.InQuad,
        }
        
        easing_type = easing_map.get(easing_name, QEasingCurve.Type.OutQuad)
        easing_curve = QEasingCurve(easing_type)
        
        # Apply spring overshoot for OutBack easing
        if easing_name == "OutBack":
            # Use different overshoot values for show vs hide
            overshoot = self.PANEL_SPRING_OVERSHOOT if show else self.PANEL_HIDE_OVERSHOOT
            easing_curve.setOvershoot(overshoot)
        
        self._panel_anim.setEasingCurve(easing_curve)
        self._panel_anim.setStartValue(start_width)
        self._panel_anim.setEndValue(end_width)
        
        # Animation update callback
        def on_value_changed(right_width):
            # Update the maximum width constraint to match animated value
            self.right_frame.setMaximumWidth(max(0, right_width))
            
            # Update splitter proportions
            left_width = total_width - right_width
            self.splitter.setSizes([left_width, right_width])
            
            # Staggered side buttons reveal (only during show)
            if show and not self._buttons_triggered:
                progress = right_width / target_right_width if target_right_width > 0 else 0
                if progress >= self.BUTTONS_REVEAL_THRESHOLD:
                    self._buttons_triggered = True
                    self._trigger_side_buttons_animation(hide=False)
        
        self._panel_anim.valueChanged.connect(on_value_changed)
        
        # Animation finished callback
        def on_animation_finished():
            if show:
                # Remove the maximum width constraint
                self.right_frame.setMaximumWidth(16777215)  # QWIDGETSIZE_MAX
                # Ensure buttons are visible if animation finished before threshold
                if not self._buttons_triggered:
                    self._trigger_side_buttons_animation(hide=False)
            else:
                # Hide the panel completely
                self.right_frame.setVisible(False)
        
        self._panel_anim.finished.connect(on_animation_finished)
        
        # Start the animation
        self._panel_anim.start()
    
    def _trigger_side_buttons_animation(self, hide=False):
        """
        Trigger staggered animation for ALL Command Panel Side Buttons.
        
        Button Groups (animated top to bottom):
        1. Command Panel Main Folder Buttons: Max Size, Lab Presets, Manual
        2. Command Panel Transform Folder Buttons: Resize, Rotate, Time (tab-dependent)
        
        SHOW: Buttons reveal with stagger delay (one after another)
        HIDE: All buttons hide simultaneously (no stagger)
        
        Args:
            hide: True to hide buttons, False to reveal them
        """
        from PyQt6.QtCore import QTimer
        
        if not hasattr(self, 'command_panel'):
            return
        
        # Collect ALL buttons in ORDER (top to bottom)
        all_buttons = []
        
        # --- 1. Main Folder Buttons (ModeButtonsWidget) ---
        # These are at the TOP of the side button area
        if hasattr(self.command_panel, 'mode_buttons'):
            mode_btns = self.command_panel.mode_buttons
            # ModeButtonsWidget has individual button attributes (not a dict)
            if hasattr(mode_btns, 'max_size_btn'):
                all_buttons.append(mode_btns.max_size_btn)
            if hasattr(mode_btns, 'presets_btn'):
                all_buttons.append(mode_btns.presets_btn)
            if hasattr(mode_btns, 'manual_btn'):
                all_buttons.append(mode_btns.manual_btn)
        
        # --- 2. Transform Folder Buttons (SideButtonGroup) ---
        # Only add buttons for the currently active tab
        current_tab = self.command_panel.tabs.currentIndex() if hasattr(self.command_panel, 'tabs') else 0
        
        transform_group = None
        if current_tab == 0 and hasattr(self.command_panel, 'image_side_buttons'):
            transform_group = self.command_panel.image_side_buttons
        elif current_tab == 1 and hasattr(self.command_panel, 'video_side_buttons'):
            transform_group = self.command_panel.video_side_buttons
        elif current_tab == 2 and hasattr(self.command_panel, 'loop_side_buttons'):
            transform_group = self.command_panel.loop_side_buttons
        
        if transform_group and hasattr(transform_group, 'buttons'):
            # SideButtonGroup has a buttons dict
            # Get buttons in order based on their config order
            if hasattr(transform_group, 'buttons_config'):
                for config in transform_group.buttons_config:
                    btn_id = config.get('id', '')
                    if btn_id in transform_group.buttons:
                        all_buttons.append(transform_group.buttons[btn_id])
            else:
                # Fallback: just add all buttons
                all_buttons.extend(transform_group.buttons.values())
        
        # --- Trigger animation ---
        if hide:
            # HIDE: All buttons hide simultaneously (no stagger for snappy exit)
            for btn in all_buttons:
                self._hide_button(btn)
        else:
            # SHOW: Staggered reveal (top to bottom)
            for i, btn in enumerate(all_buttons):
                delay = i * self.BUTTONS_SHOW_STAGGER_MS
                QTimer.singleShot(delay, lambda b=btn: self._reveal_button(b))
    
    def _reveal_button(self, btn):
        """
        Reveal a single side button with animation.
        Uses the BUTTONS_SHOW_EASING and BUTTONS_SHOW_DURATION_MS settings.
        """
        if hasattr(btn, 'set_force_hidden'):
            # Configure the button's internal animation
            if hasattr(btn, 'animation'):
                from PyQt6.QtCore import QEasingCurve
                
                easing_map = {
                    "Linear": QEasingCurve.Type.Linear,
                    "OutQuad": QEasingCurve.Type.OutQuad,
                    "OutCubic": QEasingCurve.Type.OutCubic,
                    "OutExpo": QEasingCurve.Type.OutExpo,
                    "OutBack": QEasingCurve.Type.OutBack,
                }
                easing = easing_map.get(self.BUTTONS_SHOW_EASING, QEasingCurve.Type.OutCubic)
                btn.animation.setDuration(self.BUTTONS_SHOW_DURATION_MS)
                btn.animation.setEasingCurve(easing)
            
            # Trigger the reveal
            btn.set_force_hidden(False)
    
    def _hide_button(self, btn):
        """
        Hide a single side button with animation.
        Uses the BUTTONS_HIDE_EASING and BUTTONS_HIDE_DURATION_MS settings.
        """
        if hasattr(btn, 'set_force_hidden'):
            # Configure the button's internal animation for hide
            if hasattr(btn, 'animation'):
                from PyQt6.QtCore import QEasingCurve
                
                easing_map = {
                    "Linear": QEasingCurve.Type.Linear,
                    "InQuad": QEasingCurve.Type.InQuad,
                    "InCubic": QEasingCurve.Type.InCubic,
                    "OutQuad": QEasingCurve.Type.OutQuad,
                    "OutCubic": QEasingCurve.Type.OutCubic,
                }
                easing = easing_map.get(self.BUTTONS_HIDE_EASING, QEasingCurve.Type.InQuad)
                btn.animation.setDuration(self.BUTTONS_HIDE_DURATION_MS)
                btn.animation.setEasingCurve(easing)
            
            # Trigger the hide
            btn.set_force_hidden(True)
        
    def create_bottom_section(self, parent_layout):
        """Create the bottom section with status and progress"""
        bottom_frame = QFrame()
        bottom_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        bottom_frame.setMaximumHeight(100)
        bottom_frame.setVisible(False)  # Hide by default
        
        bottom_layout = QVBoxLayout(bottom_frame)
        
        # Status text area
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(60)
        self.status_text.setReadOnly(True)
        self.status_text.setPlainText("Ready to convert graphics files...")
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        bottom_layout.addWidget(QLabel("Status:"))
        bottom_layout.addWidget(self.status_text)
        bottom_layout.addWidget(self.progress_bar)
        
        parent_layout.addWidget(bottom_frame)
        
        # Store reference to bottom frame for toggling
        self.bottom_frame = bottom_frame
        
    def setup_menu_bar(self):
        """Hide the menu bar completely"""
        menubar = self.menuBar()
        menubar.hide()
        
    def setup_status_bar(self):
        """Setup the bottom status bar with progress bar above it"""
        # Create custom progress bar with dual-layer rendering
        from PyQt6.QtWidgets import QWidget
        from PyQt6.QtGui import QPainter, QLinearGradient, QColor
        from PyQt6.QtCore import Qt
        
        class CustomProgressBar(QWidget):
            def __init__(self, color, height=4):
                super().__init__()
                self.setFixedHeight(height)
                self.progress = 0.0 # 0.0 to 1.0
                self.color = color
                self._animation = None
                
            def set_progress(self, value, animate=True, min_duration_ms=250):
                from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, pyqtProperty
                
                target_value = max(0.0, min(1.0, value))
                
                # If not animating, set immediately
                if not animate:
                    if self._animation and self._animation.state() == QPropertyAnimation.State.Running:
                        self._animation.stop()
                    self.progress = target_value
                    self.repaint()
                    return
                
                # If new file started (target < current), reset immediately without animation
                if target_value < self.progress - 0.1:
                    if self._animation and self._animation.state() == QPropertyAnimation.State.Running:
                        self._animation.stop()
                    self.progress = target_value
                    self.repaint()
                    return
                
                # Stop current animation if running
                if self._animation and self._animation.state() == QPropertyAnimation.State.Running:
                    self._animation.stop()
                
                # Calculate animation duration based on progress distance
                distance = abs(target_value - self.progress)
                duration = max(min_duration_ms, int(distance * 500))  # At least min_duration_ms
                
                # Create smooth animation from current position
                self._animation = QPropertyAnimation(self, b"progress_value")
                self._animation.setDuration(duration)
                self._animation.setStartValue(self.progress)
                self._animation.setEndValue(target_value)
                self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
                self._animation.start()
            
            @pyqtProperty(float)
            def progress_value(self):
                return self.progress
            
            @progress_value.setter
            def progress_value(self, value):
                self.progress = value
                self.repaint()
                
            def paintEvent(self, event):
                painter = QPainter(self)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
                rect = self.rect()
                
                # Background (dark)
                painter.fillRect(rect, QColor(60, 60, 60, 80))
                
                width = int(rect.width() * self.progress)
                # Ensure at least 1px visible if > 0
                if self.progress > 0 and width == 0:
                    width = 1
                    
                if width > 0:
                    gradient = QLinearGradient(0, 0, width, 0)
                    gradient.setColorAt(0, self.color)
                    gradient.setColorAt(1, self.color.lighter(130))
                    painter.fillRect(0, 0, width, rect.height(), gradient)
                
                painter.end()

        # Progress Bar Container
        self.progress_container = QWidget()
        self.progress_container.setFixedHeight(8)  # Fixed 8px height container
        progress_layout = QVBoxLayout(self.progress_container)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(1)
        
        # Single File Progress (Blue, Top)
        self.file_progress_bar = CustomProgressBar(QColor(33, 150, 243), height=3) # Blue, Slim
        
        # Total Progress (Green, Bottom)
        self.total_progress_bar = CustomProgressBar(QColor(76, 175, 80), height=3) # Green
        
        progress_layout.addWidget(self.file_progress_bar)
        progress_layout.addWidget(self.total_progress_bar)
        
        self._completed_files_count = 0
        
        # Add progress bar to the central widget's layout (above status bar)
        if self.centralWidget():
            central_layout = self.centralWidget().layout()
            if central_layout:
                central_layout.addWidget(self.progress_container)
        
        # Status bar - hidden (no resize grip shown)
        self.status_bar = QStatusBar()
        self.status_bar.setSizeGripEnabled(False)  # Disable resize grip
        self.setStatusBar(self.status_bar)
        self.status_bar.hide()  # Hide the status bar completely
        
    def update_status(self, message):
        """Update status in both status bar and status text area"""
        self.status_bar.showMessage(message)
        self.status_text.append(f"[INFO] {message}")
        
        # Auto-scroll to bottom
        cursor = self.status_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.status_text.setTextCursor(cursor)
        
    def show_progress(self, visible=True):
        """Show or hide the progress bar"""
        self.progress_bar.setVisible(visible)
        
    def set_progress(self, value):
        """Set progress bar value (0-100)"""
        self.progress_bar.setValue(value)
    
    @pyqtSlot(int, float)
    def on_file_progress(self, file_index, progress):
        """Handle individual file progress update"""
        # Update file list item progress
        self.drag_drop_area.set_file_progress(file_index, progress)
        
        # Update separated progress bars
        if hasattr(self, 'file_progress_bar'):
            self.file_progress_bar.set_progress(progress)
            
        if hasattr(self, 'total_progress_bar'):
            # Calculate total progress
            total_files = len(self.drag_drop_area.file_list)
            if total_files > 0:
                # Base progress from completed files
                base_progress = self._completed_files_count / total_files
                # Add fraction of current file
                current_fraction = progress / total_files
                self.total_progress_bar.set_progress(base_progress + current_fraction)
        
    def connect_signals(self):
        """Connect signals between components"""
        # Connect drag-drop area signals
        self.drag_drop_area.files_added.connect(self.on_files_added)
        self.drag_drop_area.preset_applied.connect(self.on_preset_applied)
        
        # Connect drag-drop area status updates to main window
        self.drag_drop_area.update_status = self.update_status
        
        # Connect command panel signals
        self.command_panel.conversion_requested.connect(self.start_conversion)
        self.command_panel.stop_conversion_requested.connect(self.stop_conversion)
        self.command_panel.global_mode_changed.connect(self.on_mode_changed)
        self.command_panel.lab_state_changed.connect(self._on_lab_state_changed)
        
        # Connect unified control bar buttons to drag-drop area
        self.add_files_btn.clicked.connect(self.drag_drop_area.add_files_dialog)
        self.add_folder_btn.clicked.connect(self.drag_drop_area.add_folder_dialog)
        self.clear_files_btn.clicked.connect(self.drag_drop_area.clear_files)
    
    def _on_lab_state_changed(self, icon_path, is_solid):
        """Handle lab button state change from CommandPanel"""
        if hasattr(self, 'lab_btn'):
            self.lab_btn.set_main_icon(icon_path)
            self.lab_btn.set_style_solid(is_solid)
        
    def on_files_added(self, files):
        """Handle files added to drag-drop area"""
        self.update_status(f"Added {len(files)} file(s)")
        # Update footer visibility
        if hasattr(self, 'output_footer'):
            has_files = len(self.drag_drop_area.get_files()) > 0
            self.output_footer.set_has_files(has_files)
            
        # USER REQUEST: "After dragging the file the PRESET view is on"
        # Manually trigger the preset view when new files are added
        self.drag_drop_area.show_preset_view()
    
    def _on_footer_start(self):
        """Handle start button click from output footer"""
        # Build params from command panel and footer
        params = self.command_panel.get_conversion_params()
        
        # Override output settings from footer
        output_mode = self.output_footer.get_output_mode()
        if output_mode == "source":
            params['output_same_folder'] = True
            params['output_nested'] = False
            params['output_custom'] = False
        elif output_mode == "organized":
            params['output_same_folder'] = False
            params['output_nested'] = True
            params['nested_folder_name'] = self.output_footer.get_organized_name()
            params['output_custom'] = False
        elif output_mode == "custom":
            params['output_same_folder'] = False
            params['output_nested'] = False
            params['output_custom'] = True
            params['output_dir'] = self.output_footer.get_custom_path()
        
        self.start_conversion(params)
        

    def start_conversion(self, params):
        """Start the conversion process"""
        files = self.drag_drop_area.get_files()
        
        if not files:
            msg_box = QMessageBox(QMessageBox.Icon.Warning, "No Files", "Please add files for conversion first.", parent=self)
            msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowType.FramelessWindowHint)
            msg_box.setStyleSheet(self.theme_manager.get_dialog_styles())
            ok_button = msg_box.button(QMessageBox.StandardButton.Ok)
            if ok_button:
                ok_button.setDefault(True)
                ok_button.setFocus()
            msg_box.exec()
            return
            
        if self.conversion_engine and self.conversion_engine.isRunning():
            msg_box = QMessageBox(QMessageBox.Icon.Warning, "Conversion Running", "A conversion is already in progress.", parent=self)
            msg_box.setStyleSheet(self.theme_manager.get_dialog_styles())
            msg_box.exec()
            return
        
        # Initialize variants
        resize_variants = self.command_panel.get_resize_values()
        video_variants = self.command_panel.get_video_variant_values()
        
        # Set button to stop state (handled by footer)
        # Update footer state
        if hasattr(self, 'output_footer'):
            self.output_footer.set_converting(True)
        
        # Get current tab index to determine which settings to apply
        current_tab_index = self.command_panel.tabs.currentIndex()
        
        # Add resize variants to params (Only if on Image tab)
        if current_tab_index == 0 and resize_variants:
            params['resize_variants'] = resize_variants
        
        # Add video variants to params (Only if on Video tab)
        if current_tab_index == 1 and video_variants:
            params['video_variants'] = video_variants
            
        # Add rotation parameters to params based on active tab
        if current_tab_index == 0: # Images Tab
            if hasattr(self.command_panel, 'rotation_angle'):
                rotation_value = self.command_panel.rotation_angle.currentText()
                if rotation_value != "No rotation":
                    params['rotation_angle'] = rotation_value
                    
        elif current_tab_index == 1: # Videos Tab
            if hasattr(self.command_panel, 'video_rotation_angle'):
                rotation_value = self.command_panel.video_rotation_angle.currentText()
                if rotation_value != "No rotation":
                    params['rotation_angle'] = rotation_value
                    
        elif current_tab_index == 2: # GIFs Tab
            if hasattr(self.command_panel, 'gif_rotation_angle'):
                rotation_value = self.command_panel.gif_rotation_angle.currentText()
                if rotation_value != "No rotation":
                    params['gif_rotation_angle'] = rotation_value
        
        # Create and start conversion engine
        self.conversion_engine = ConversionEngine(files, params)
        
        # Connect engine signals
        self.conversion_engine.progress_updated.connect(self.set_progress)
        self.conversion_engine.file_progress_updated.connect(self.on_file_progress)
        self.conversion_engine.status_updated.connect(self.update_status)
        self.conversion_engine.file_completed.connect(self.on_file_completed)
        self.conversion_engine.conversion_finished.connect(self.on_conversion_finished)
        
        # Reset separated progress bars
        if hasattr(self, 'file_progress_bar'):
            self.file_progress_bar.set_progress(0)
        if hasattr(self, 'total_progress_bar'):
            self.total_progress_bar.set_progress(0)
            
        # Start conversion
        self.show_progress(True)
        self.set_progress(0)
        self.update_status("Starting conversion...")
        self.conversion_engine.start()
    
    def stop_conversion(self):
        """Stop the current conversion process"""
        if self.conversion_engine and self.conversion_engine.isRunning():
            self.update_status("Stopping conversion...")
            self.conversion_engine.stop_conversion()
            # The button state will be reset in on_conversion_finished
    
    @pyqtSlot(int, float)
    def on_file_progress(self, file_index, progress):
        """Handle individual file progress update"""
        self.drag_drop_area.set_file_progress(file_index, progress)
        if hasattr(self, 'file_progress_bar'):
            self.file_progress_bar.set_progress(progress, animate=True, min_duration_ms=500)
    
    def on_file_completed(self, source_file, output_file):
        """Handle completed file conversion"""
        import os
        source_name = os.path.basename(source_file)
        output_name = os.path.basename(output_file)
        self.update_status(f"✓ Converted: {source_name} → {output_name}")
        
        # Ensure blue bar reaches 100% for this file
        if hasattr(self, 'file_progress_bar'):
            self.file_progress_bar.set_progress(1.0, animate=True, min_duration_ms=500)
        
        # Mark the file as completed in the list
        # Find the file index
        for i, f in enumerate(self.drag_drop_area.file_list):
            if f == source_file:
                self.drag_drop_area.set_file_completed(i)
                self._completed_files_count += 1
                # Update total progress bar
                if hasattr(self, 'total_progress_bar'):
                    total_files = len(self.drag_drop_area.file_list)
                    if total_files > 0:
                        self.total_progress_bar.set_progress(self._completed_files_count / total_files)
                break
        
    def on_conversion_finished(self, success, message):
        """Handle conversion completion"""
        # Reset button state (handled by footer)
        # Reset footer state
        if hasattr(self, 'output_footer'):
            self.output_footer.set_converting(False)
        
        self.show_progress(False)
        self.set_progress(0)
        
        # Reset separated progress bars
        if hasattr(self, 'file_progress_bar'):
            self.file_progress_bar.set_progress(0)
        if hasattr(self, 'total_progress_bar'):
            self.total_progress_bar.set_progress(0)
        
        self._completed_files_count = 0
        
        self.update_status(message)
        
        from PyQt6.QtWidgets import QMessageBox
        from PyQt6.QtCore import Qt
        if success:
            msg_box = QMessageBox(QMessageBox.Icon.Information, "Conversion Complete", message, parent=self)
        else:
            msg_box = QMessageBox(QMessageBox.Icon.Critical, "Conversion Error", message, parent=self)
        
        # Remove title bar and make frameless
        msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowType.FramelessWindowHint)
        
        # Apply dark theme to the dialog
        msg_box.setStyleSheet(self.theme_manager.get_dialog_styles())
        msg_box.exec()
            
    def check_tools(self):
        """Check if required tools are available"""
        tools = ToolChecker.get_tool_status()
        detailed_status = ToolChecker.get_detailed_status()
        
        missing_tools = [tool for tool, available in tools.items() if not available]
        
        if missing_tools:
            from PyQt6.QtWidgets import QMessageBox
            
            # Create detailed message
            message_parts = ["Tool Status Check:\n"]
            for tool, status in detailed_status.items():
                icon = "✓" if tools[tool] else "✗"
                message_parts.append(f"{icon} {tool.title()}: {status}")
            
            message = "\n".join(message_parts)
            message += f"\n\nNote: The app will use fallback methods for missing tools."
            
            msg_box = QMessageBox(QMessageBox.Icon.Information, "Tool Status", message, parent=self)
            msg_box.setStyleSheet(self.theme_manager.get_dialog_styles())
            msg_box.exec()
        
    def apply_theme(self):
        """Apply the current theme to the main window"""
        # Apply main window styles
        main_style = self.theme_manager.get_main_window_style()
        self.setStyleSheet(main_style)
        
        # NOTE: convert_btn styling removed - button now in OutputFooter
        
        # Update drag drop area theme
        self.drag_drop_area.set_theme_manager(self.theme_manager)
        
        # Do not clear files when switching themes
        # self.drag_drop_area.clear_files()
        
        # Update command panel theme (for toggle boxes)
        is_dark = self.theme_manager.get_current_theme() == 'dark'
        if hasattr(self.command_panel, 'update_theme'):
            self.command_panel.update_theme(is_dark)
        
        # Update title bar theme
        self.update_title_bar_theme(is_dark)
        
        # Apply global QToolTip styling
        from client.gui.custom_widgets import apply_tooltip_style
        apply_tooltip_style(is_dark)
        
        # Update output footer theme
        if hasattr(self, 'output_footer'):
            self.output_footer.update_theme(is_dark)
        
    def update_title_bar_theme(self, is_dark):
        """Update title bar colors based on theme"""
        if is_dark:
            # Dark theme
            # Frosted Glass: more transparent to show blur
            bg_color = "rgba(43, 43, 43, 0.5)" 
            content_bg = "#2b2b2b"
            text_color = "#ffffff"
            btn_bg = "#404040"
            btn_hover = "#4a4a4a"
            btn_pressed = "#363636"
            border_color = "#555555"
        else:
            # Light theme
            bg_color = "rgba(232, 232, 232, 0.6)"
            content_bg = "#ffffff"
            text_color = "#000000"
            btn_bg = "#f0f0f0"
            btn_hover = "#e0e0e0"
            btn_pressed = "#d0d0d0"
            border_color = "#d0d0d0"
        
        # Title bar styling (Rounded top corners, glass bg)
        title_bar_style = f"""
            QFrame {{
                background-color: {bg_color};
                border-bottom: 1px solid {border_color};
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }}
        """
        self.title_bar.setStyleSheet(title_bar_style)
        
        # Content frame styling (Opaque, rounded bottom corners)
        if hasattr(self, 'content_container'):
            self.content_container.setStyleSheet(f"""
                QFrame#ContentFrame {{
                    background-color: {content_bg};
                    border-bottom-left-radius: 12px;
                    border-bottom-right-radius: 12px;
                }}
            """)
        
        # Title label (background: transparent)
        self.title_label.setStyleSheet(f"color: {text_color}; border: none; padding: 0px; margin: 0px; text-decoration: none; outline: none; background: transparent;")
        

        
        # Update theme toggle button icon color
        if hasattr(self, 'sun_moon_svg_path'):
            try:
                with open(self.sun_moon_svg_path, 'r', encoding='utf-8') as f:
                    svg_content = f.read()
                
                # Change stroke and fill color based on theme
                icon_color = "#ffffff" if is_dark else "#000000"
                svg_content = svg_content.replace('stroke:currentColor', f'stroke:{icon_color}')
                svg_content = svg_content.replace('stroke:#020202', f'stroke:{icon_color}')
                svg_content = svg_content.replace('stroke:#000000', f'stroke:{icon_color}')
                svg_content = svg_content.replace('stroke=#020202', f'stroke={icon_color}')
                svg_content = svg_content.replace('stroke=#000000', f'stroke={icon_color}')
                svg_content = svg_content.replace('fill:currentColor', f'fill:{icon_color}')
                svg_content = svg_content.replace('fill:#020202', f'fill:{icon_color}')
                svg_content = svg_content.replace('fill=#020202', f'fill={icon_color}')
                svg_content = svg_content.replace('fill:#000000', f'fill:{icon_color}')
                svg_content = svg_content.replace('fill:#000', f'fill:{icon_color}')
                svg_content = svg_content.replace('fill:black', f'fill:{icon_color}')
                
                # Create a temporary SVG with the new color
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False, encoding='utf-8') as tmp:
                    tmp.write(svg_content)
                    tmp_path = tmp.name
                
                # Load the colored icon
                icon = QIcon(tmp_path)
                self.theme_toggle_btn.setIcon(icon)
                self.theme_toggle_btn.setIconSize(QSize(24, 21))
                
                # Clean up temp file
                import atexit
                atexit.register(lambda: os.unlink(tmp_path) if os.path.exists(tmp_path) else None)
            except Exception as e:
                print(f"Could not update icon color: {e}")
        
        # Button styling
        btn_style = f"""
            QPushButton {{
                background-color: {btn_bg};
                color: {text_color};
                border: none;
                border-radius: 3px;
                padding: 2px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {btn_hover};
            }}
            QPushButton:pressed {{
                background-color: {btn_pressed};
            }}
        """
        self.minimize_btn.setStyleSheet(btn_style)
        self.theme_toggle_btn.setStyleSheet(btn_style)
        
        # Menu styling
        menu_bg = "#2b2b2b" if is_dark else "#f5f5f5"
        menu_text = "#ffffff" if is_dark else "#000000"

        self.title_menu.setStyleSheet(f"""
            QMenu {{
                background-color: {menu_bg};
                color: {menu_text};
                border: 1px solid {'#555555' if is_dark else '#d0d0d0'};
            }}
            QMenu::item {{
                padding: 5px 20px;
            }}
            QMenu::item:selected {{
                background-color: {'#3c3c3c' if is_dark else '#e0e0e0'};
                color: {menu_text};
            }}
        """)
        
        # Close button with red hover
        close_btn_style = f"""
            QPushButton {{
                background-color: {btn_bg};
                color: {text_color};
                border: none;
                border-radius: 3px;
                padding: 2px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #cc0000;
                color: #ffffff;
            }}
            QPushButton:pressed {{
                background-color: #990000;
                color: #ffffff;
            }}
        """
        self.close_btn.setStyleSheet(close_btn_style)
        
    def toggle_theme(self):
        """Toggle between dark and light theme"""
        current_theme = self.theme_manager.get_current_theme()
        new_theme = 'light' if current_theme == 'dark' else 'dark'
        self.theme_manager.set_theme(new_theme)
        self.apply_theme()
        
    def toggle_status_bar(self):
        """Toggle the visibility of the status bar section"""
        if hasattr(self, 'bottom_frame'):
            is_visible = self.bottom_frame.isVisible()
            self.bottom_frame.setVisible(not is_visible)

    def show_about(self):
        """Show the About dialog"""
        # Import version info
        try:
            from client.version import get_version_info
            version_info = get_version_info()
            version = version_info['version']
        except ImportError:
            version = "1.1.0"
        
        # Get theme-appropriate colors
        current_theme = self.theme_manager.get_current_theme()
        if current_theme == 'dark':
            bg_color = "#2b2b2b"
            text_color = "#ffffff" 
            muted_color = "#aaaaaa"
            accent_color = "#4a9eff"
        else:
            bg_color = "#ffffff"
            text_color = "#000000"
            muted_color = "#666666"
            accent_color = "#0066cc"
        
        about_text = f"""
        <div style="text-align: center; color: {text_color};">
        <h2 style="font-family: '{FONT_FAMILY_APP_NAME}'; color: {accent_color}; margin-bottom: 10px;">{APP_NAME}</h2>
        <p><b>Version:</b> {version}</p>
        <p><b>Author:</b> <span style="color: {text_color};">{AUTHOR}</span></p>
        </div>
        <br>
        <p style="color: {text_color};">Web export simplified.</p>
        <p style="color: {text_color};">Convert files to WebM, WebP, GIF, MP4, and other formats in just a few clicks.</p>
        <p style="color: {text_color};">Built for speed, quality, and ease of use.</p>
        <br>
        <p style="color: {text_color};">🌐 <a href="" style="color: {accent_color}; text-decoration: none;">Visit our website</a></p>
        <br>
        <p style="color: {text_color};">This software uses FFmpeg (© FFmpeg developers) licensed under the LGPL/GPL.</p>
        <p style="color: {text_color};">© 2025 {AUTHOR}. All rights reserved.</p>
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle(f"About {APP_NAME}")
        msg.setText(about_text)
        
        # Set custom icon (app logo) instead of information icon
        try:
            from client.utils.resource_path import get_app_icon_path
            icon_path = get_app_icon_path()
            if os.path.exists(icon_path):
                icon = QIcon(icon_path)
                msg.setIconPixmap(icon.pixmap(64, 64))
        except Exception as e:
            print(f"Could not set about dialog icon: {e}")
            msg.setIcon(QMessageBox.Icon.Information)
        
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        # Hide the title bar (frameless window)
        msg.setWindowFlags(msg.windowFlags() | Qt.WindowType.FramelessWindowHint)
        
        # Apply theme styling to the message box
        dialog_style = f"""
        QMessageBox {{
            background-color: {bg_color};
            color: {text_color};
            border: 1px solid #555555;
            border-radius: 8px;
        }}
        QMessageBox QLabel {{
            color: {text_color};
            background-color: {bg_color};
        }}
        QMessageBox QPushButton {{
            background-color: #0066cc;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }}
        QMessageBox QPushButton:hover {{
            background-color: #0052a3;
        }}
        QMessageBox QPushButton:pressed {{
            background-color: #003d7a;
        }}
        """
        msg.setStyleSheet(dialog_style)
        
        # Set dialog size
        msg.resize(450, 400)
        
        msg.exec()

    def show_advanced(self):
        """Show the Advanced Settings dialog"""
        from .advanced_settings_window import AdvancedSettingsWindow
        
        dialog = AdvancedSettingsWindow(parent=self, theme_manager=self.theme_manager)
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            # Settings were saved, show confirmation
            msg = QMessageBox(
                QMessageBox.Icon.Information,
                "Settings Saved",
                "Advanced settings have been saved successfully.",
                parent=self
            )
            msg.setWindowFlags(msg.windowFlags() | Qt.WindowType.FramelessWindowHint)
            msg.setStyleSheet(self.theme_manager.get_dialog_styles())
            msg.exec()
    
    def logout(self):
        """Logout from the application and show login window"""
        # Confirm logout
        msg = QMessageBox(
            QMessageBox.Icon.Question,
            "Logout",
            "Are you sure you want to logout?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            parent=self
        )
        msg.setWindowFlags(msg.windowFlags() | Qt.WindowType.FramelessWindowHint)
        msg.setStyleSheet(self.theme_manager.get_dialog_styles())
        msg.setDefaultButton(QMessageBox.StandardButton.No)
        
        if msg.exec() == QMessageBox.StandardButton.Yes:
            # Stop any running conversions
            if self.conversion_engine and self.conversion_engine.isRunning():
                self.conversion_engine.stop_conversion()
                self.conversion_engine.wait(1000)  # Wait up to 1 second
            
            # Clean up conversion engine
            self.conversion_engine = None
            
            # Get the QApplication instance
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtCore import QTimer
            app = QApplication.instance()
            
            # Prevent app from quitting when main window closes
            app.setQuitOnLastWindowClosed(False)
            
            # Define function to show login window after main window closes
            def show_login_after_close():
                try:
                    from client.gui.login_window_new import ModernLoginWindow
                    login_window = ModernLoginWindow()
                    
                    # Store reference to prevent garbage collection
                    app._login_window = login_window
                    
                    # Show login window modally
                    result = login_window.exec()
                    
                    if result == QDialog.DialogCode.Accepted:
                        # Login successful - create new main window
                        is_trial = getattr(login_window, 'is_trial', False)
                        
                        # Use centralized initialization to ensure splash screen and tool checks run
                        from client.main import initialize_main_window
                        new_main_window = initialize_main_window(is_trial=is_trial)
                        new_main_window.show()
                        # Store reference to prevent garbage collection
                        app._main_window = new_main_window
                        # Re-enable quit on last window closed
                        app.setQuitOnLastWindowClosed(True)
                    else:
                        # Login cancelled - exit application
                        app.quit()
                    
                except Exception as e:
                    print(f"Error showing login window: {e}")
                    import traceback
                    traceback.print_exc()
                    # If login window fails, exit application
                    app.quit()
            
            # Close main window
            self.close()
            
            # Use QTimer to show login window after event loop processes the close
            QTimer.singleShot(100, show_login_after_close)

    def toggle_status_bar(self, checked):
        """Toggle status bar visibility"""
        if hasattr(self, 'bottom_frame'):
            self.bottom_frame.setVisible(checked)
            
    def resizeEvent(self, event):
        """Handle resize to update overlay geometry"""
        super().resizeEvent(event)
        if hasattr(self, 'preset_overlay'):
            self.preset_overlay.setGeometry(0, 0, self.width(), self.height())

    def showEvent(self, event):
        """Override showEvent"""
        super().showEvent(event)
        self.enable_blur()
        self.enable_mouse_tracking_all()
        
    def enable_mouse_tracking_all(self):
        """Recursively enable mouse tracking for all widgets to ensure resize events propagate"""
        self.setMouseTracking(True)
        for widget in self.findChildren(QWidget):
            widget.setMouseTracking(True)
        
    def enable_blur(self):
        """Enable Windows Blur/Acrylic effect"""
        if os.name != 'nt':
            return
            
        try:
            class ACCENT_POLICY(Structure):
                _fields_ = [
                    ("AccentState", c_int),
                    ("AccentFlags", c_int),
                    ("GradientColor", c_int),
                    ("AnimationId", c_int)
                ]

            class WINDOWCOMPOSITIONATTRIBDATA(Structure):
                _fields_ = [
                    ("Attribute", c_int),
                    ("Data", ctypes.c_void_p), # Use void pointer
                    ("SizeOfData", c_int)
                ]
                
            # SetAccentPolicy constants
            ACCENT_ENABLE_BLURBEHIND = 3
            
            hwnd = int(self.winId())
            
            accent = ACCENT_POLICY()
            accent.AccentState = ACCENT_ENABLE_BLURBEHIND
            accent.GradientColor = 0 
            
            data = WINDOWCOMPOSITIONATTRIBDATA()
            data.Attribute = 19
            data.Data = ctypes.cast(byref(accent), ctypes.c_void_p)
            data.SizeOfData = sizeof(accent)
            
            windll.user32.SetWindowCompositionAttribute(hwnd, byref(data))
            
        except Exception as e:
            print(f"Failed to enable blur: {e}")


    
    def mousePressEvent(self, event):
        """Start manual window resize calculation"""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            border = 8
            w = self.width()
            h = self.height()
            
            left = pos.x() < border
            right = pos.x() > w - border
            top = pos.y() < border
            bottom = pos.y() > h - border
            
            self.resize_edge = ""
            if top: self.resize_edge += "top"
            if bottom: self.resize_edge += "bottom"
            if left: self.resize_edge += "left"
            if right: self.resize_edge += "right"
            
            if self.resize_edge:
                self.resize_start_pos = event.globalPosition().toPoint()
                self.resize_start_geo = self.geometry()
                event.accept()
                return
                    
        super().mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        """Reset resize state"""
        self.resize_edge = ""
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        """Handle manual resizing and cursor updates"""
        # Handle resizing if active
        if hasattr(self, 'resize_edge') and self.resize_edge:
            bg = self.resize_start_geo
            delta = event.globalPosition().toPoint() - self.resize_start_pos
            
            new_geo = QRect(bg)
            
            if "top" in self.resize_edge:
                new_geo.setTop(bg.top() + delta.y())
            if "bottom" in self.resize_edge:
                new_geo.setBottom(bg.bottom() + delta.y())
            if "left" in self.resize_edge:
                new_geo.setLeft(bg.left() + delta.x())
            if "right" in self.resize_edge:
                new_geo.setRight(bg.right() + delta.x())
                
            # Respect minimum size
            if new_geo.width() >= self.minimumWidth() and new_geo.height() >= self.minimumHeight():
                self.setGeometry(new_geo)
            
            event.accept()
            return

        # Regular cursor update logic
        pos = event.pos()
        border = 8
        w = self.width()
        h = self.height()
        
        left = pos.x() < border
        right = pos.x() > w - border
        top = pos.y() < border
        bottom = pos.y() > h - border
        
        # Set appropriate cursor
        if (top and left) or (bottom and right):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif (top and right) or (bottom and left):
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif left or right:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif top or bottom:
            self.setCursor(Qt.CursorShape.SizeVerCursor)
        else:
            self.unsetCursor()
            
        super().mouseMoveEvent(event)
    
    # --- Drag & Drop - Forward to DragDropArea ---
    
    def dragEnterEvent(self, event):
        """Accept drag anywhere on window, forward to DragDropArea"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            # Show overlay in DragDropArea
            if hasattr(self, 'drag_drop_area') and hasattr(self.drag_drop_area, 'preset_overlay'):
                list_widget = self.drag_drop_area.file_list_widget
                self.drag_drop_area.preset_overlay.setGeometry(
                    0, 0, list_widget.width(), list_widget.height()
                )
                self.drag_drop_area.preset_overlay.show_animated()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        """Accept drag move"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dragLeaveEvent(self, event):
        """Hide overlay when drag leaves window"""
        if hasattr(self, 'drag_drop_area') and hasattr(self.drag_drop_area, 'preset_overlay'):
            self.drag_drop_area.preset_overlay.hide_animated()
        super().dragLeaveEvent(event)
    
    def dropEvent(self, event):
        """Forward drop to DragDropArea"""
        if event.mimeData().hasUrls():
            files = []
            folders = []
            
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                import os
                if os.path.isfile(path):
                    files.append(path)
                elif os.path.isdir(path):
                    folders.append(path)
            
            # Collect all files including from folders
            all_files = files.copy()
            for folder in folders:
                folder_files = self.drag_drop_area.get_supported_files_from_folder(folder, True)
                all_files.extend(folder_files)
            
            # Store as pending in DragDropArea
            self.drag_drop_area._pending_files = all_files
            
            event.acceptProposedAction()
        else:
            event.ignore()
        
    # --- Preset Selection Handler ---
    
    def on_preset_applied(self, preset, files):
        """Handle preset applied from DragDropArea overlay"""
        file_count = len(files) if files else 0
        print(f"[Smart Drop] Applying preset: {preset.title} to {file_count} files")
        
        # 1. Add files to the DragDropArea if any
        if files:
            self.drag_drop_area.add_files(files)
        
        # 2. Configure CommandPanel with preset params
        # TODO: Implement full parameter mapping
        
        # 3. Update UI to reflect Active Preset State
        if hasattr(self, 'preset_status_btn'):
            self.preset_status_btn.set_active(True, preset.title)
            
        if hasattr(self, 'lab_btn'):
            # Set Lab button to ghost (inactive) since Preset is active
            self.lab_btn.set_style_solid(False)
            # Reset icon to default Lab icon to indicate "Preset Mode" / Neutral state
            self.lab_btn.set_main_icon("client/assets/icons/lab_icon.svg")
        
        # 4. Notify CommandPanel that Lab mode is inactive and top bar preset mode is active
        if hasattr(self, 'command_panel'):
            self.command_panel.set_lab_mode_active(False)
            self.command_panel.set_top_bar_preset_mode(True)
            
        self.update_status(f"Applied Preset: {preset.title}")
        
        # Hide Command Panel with animation (Preset mode is simple drag & drop)
        self.toggle_command_panel(False)

    def on_mode_changed(self, mode):
        """Handle global mode change (e.g. switching to Manual)"""
        # If switching away from Presets (e.g. to Manual or Max Size), reset the preset button
        if mode != "Presets" and hasattr(self, 'preset_status_btn'):
            self.preset_status_btn.set_active(False)
            
        # Notify CommandPanel that top bar preset mode is inactive
        if mode != "Presets" and hasattr(self, 'command_panel'):
            self.command_panel.set_top_bar_preset_mode(False)
