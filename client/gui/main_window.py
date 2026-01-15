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
    QFrame, QGroupBox, QProgressBar, QMessageBox
)
from PyQt6.QtGui import QIcon, QDragEnterEvent, QDropEvent, QFont, QMouseEvent, QAction
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QSize, pyqtSlot, pyqtProperty

from .drag_drop_area import DragDropArea
from .command_panel import CommandPanel
from .theme_manager import ThemeManager
from client.core.conversion_engine import ConversionEngine, ToolChecker
from client.utils.trial_manager import TrialManager
from client.utils.font_manager import AppFonts
from client.version import APP_NAME, AUTHOR

class DraggableTitleBar(QFrame):
    """Custom title bar that allows dragging the window"""
    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window
        self.drag_position = None
        
    def mousePressEvent(self, event: QMouseEvent):
        """Store the mouse position when pressed"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.parent_window.frameGeometry().topLeft()
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event: QMouseEvent):
        """Move the window when dragging"""
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position is not None:
            self.parent_window.move(event.globalPosition().toPoint() - self.drag_position)
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
        self.is_trial = is_trial
        
        # Development mode detection
        DEVELOPMENT_MODE = getattr(sys, '_called_from_test', False) or __debug__ and not getattr(sys, 'frozen', False)
        
        title = APP_NAME
        if self.is_trial:
            title += " [TRIAL MODE]"
        if DEVELOPMENT_MODE:
            title += " [DEV MODE]"
            
        self.setWindowTitle(title)
        
        # Make window frameless for custom title bar
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
            
        self.setGeometry(100, 100, 1200, 1000)
        self.setMinimumSize(800, 700)
        
        if self.is_trial:
            self.trial_manager = TrialManager()
            # Auto-reset trial in development mode
            if DEVELOPMENT_MODE:
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
        self.setCentralWidget(central_widget)
        
        # Main vertical layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add custom title bar
        self.create_title_bar(main_layout)
        
        # Content area with normal spacing
        content_layout = QVBoxLayout()
        content_layout.setSpacing(5)
        content_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create the middle section with splitter
        self.create_middle_section(content_layout)
        
        # Bottom section (status and progress)
        self.create_bottom_section(content_layout)
        
        main_layout.addLayout(content_layout)
        
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
                logo_label.setStyleSheet("border: none; padding: 0px; margin: 0px;")
                title_layout.addWidget(logo_label)
                self.logo_label = logo_label
        except Exception as e:
            print(f"Could not load logo: {e}")
        
        # Title label (clickable)
        title_label = ClickableLabel(self.windowTitle())
        title_label.setFont(AppFonts.get_title_font())
        title_label.setStyleSheet("color: #ffffff; font-weight: bold; border: none; padding: 0px; margin: 0px; text-decoration: none;")
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
            svg_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'icons', 'sun-moon.svg')
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
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        self.title_menu.addAction(about_action)
        
        show_log_action = QAction("Show Log", self)
        show_log_action.triggered.connect(self.toggle_status_bar)
        self.title_menu.addAction(show_log_action)
        
        self.title_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        self.title_menu.addAction(exit_action)
        
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
        right_layout.addWidget(self.command_panel)
        
        # Add panels to splitter
        splitter.addWidget(left_frame)
        splitter.addWidget(right_frame)
        
        # Set initial sizes (60% left, 40% right)
        splitter.setSizes([720, 480])
        
        parent_layout.addWidget(splitter)
        
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
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready for image conversion")
        
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
        
        # Connect drag-drop area status updates to main window
        self.drag_drop_area.update_status = self.update_status
        
        # Connect command panel signals
        self.command_panel.conversion_requested.connect(self.start_conversion)
        self.command_panel.stop_conversion_requested.connect(self.stop_conversion)
        
    def on_files_added(self, files):
        """Handle files added to drag-drop area"""
        self.update_status(f"Added {len(files)} file(s)")
        
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
        
        # Set button to stop state
        self.command_panel.set_conversion_state(True)
        
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
        # Reset button state
        self.command_panel.set_conversion_state(False)
        self.command_panel.convert_btn.setEnabled(True)  # Re-enable button
        
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
        
        # Apply button styles to convert button
        button_style = self.theme_manager.get_button_styles()
        self.command_panel.convert_btn.setStyleSheet(button_style)
        
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
        
    def update_title_bar_theme(self, is_dark):
        """Update title bar colors based on theme"""
        if is_dark:
            # Dark theme
            bg_color = "#3c3c3c"
            text_color = "#ffffff"
            btn_bg = "#404040"
            btn_hover = "#4a4a4a"
            btn_pressed = "#363636"
        else:
            # Light theme
            bg_color = "#e8e8e8"
            text_color = "#000000"
            btn_bg = "#f0f0f0"
            btn_hover = "#e0e0e0"
            btn_pressed = "#d0d0d0"
        
        # Title bar styling
        title_bar_style = f"""
            QFrame {{
                background-color: {bg_color};
                border-bottom: 1px solid {'#555555' if is_dark else '#d0d0d0'};
            }}
        """
        self.title_bar.setStyleSheet(title_bar_style)
        
        # Title label (clean styling without decoration)
        self.title_label.setStyleSheet(f"color: {text_color}; font-weight: bold; border: none; padding: 0px; margin: 0px; text-decoration: none; outline: none;")
        
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
        menu_hover = "#404040" if is_dark else "#e0e0e0"
        menu_style = f"""
            QMenu {{
                background-color: {menu_bg};
                color: {menu_text};
                border: 1px solid {'#555555' if is_dark else '#d0d0d0'};
            }}
            QMenu::item:selected {{
                background-color: {menu_hover};
                color: {menu_text};
            }}
        """
        self.title_menu.setStyleSheet(menu_style)
        
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
        <h2 style="color: {accent_color}; margin-bottom: 10px;">{APP_NAME}</h2>
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


