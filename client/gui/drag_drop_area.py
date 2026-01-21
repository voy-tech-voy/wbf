"""
Drag and Drop Area Widget
Handles file drag and drop operations for the graphics converter
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QPushButton, QFileDialog, QMessageBox, QStyledItemDelegate
)
from PyQt6.QtCore import Qt, pyqtSignal, QEvent, QSize, QByteArray
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QPixmap, QIcon, QAction, QPainter, QColor, QCursor, QBrush
from PyQt6.QtSvg import QSvgRenderer
import os
import subprocess
import tempfile
import re
from pathlib import Path
from client.utils.resource_path import get_resource_path
from client.utils.resource_path import get_resource_path
from client.gui.theme_variables import get_theme, get_color
from client.gui.custom_widgets import PresetStatusButton

class HoverIconButton(QPushButton):
    """Button that changes its SVG icon colors based on hover state and theme"""
    def __init__(self, svg_name, icon_size=QSize(28, 28), parent=None):
        super().__init__(parent)
        self.svg_path = get_resource_path(f"client/assets/icons/{svg_name}")
        self.icon_size = icon_size
        self._is_dark = False
        
        self.setMouseTracking(True)
        self.setIconSize(icon_size)
        
        self.normal_icon = None
        self.hover_icon = None
        
        self.update_icons()
        if self.normal_icon:
            self.setIcon(self.normal_icon)

    def enterEvent(self, event):
        if self.hover_icon:
            self.setIcon(self.hover_icon)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.normal_icon:
            self.setIcon(self.normal_icon)
        super().leaveEvent(event)

    def set_dark_mode(self, is_dark):
        if self._is_dark != is_dark:
            self._is_dark = is_dark
            self.update_icons()
            self.setIcon(self.hover_icon if self.underMouse() else self.normal_icon)

    def update_icons(self):
        if not os.path.exists(self.svg_path):
            return
            
        # Read SVG
        with open(self.svg_path, 'r') as f:
            svg_content = f.read()
        
        # Determine theme base color (black or white) for the main outline
        base_color = "white" if self._is_dark else "black"
        
        # 1. Adjust main outline color based on theme
        # Replace black strokes with base_color
        svg_base = svg_content.replace('stroke="black"', f'stroke="{base_color}"')
        svg_base = svg_base.replace('stroke="#000000"', f'stroke="{base_color}"')
        svg_base = svg_base.replace('stroke="#000"', f'stroke="{base_color}"')
        
        # 2. Create the Normal version (colored curves -> gray)
        # Replace green (#4CAF50) and red (#D32F2F) with grey
        gray_color = "#888888"
        svg_normal = svg_base.replace('#4CAF50', gray_color).replace('#4caf50', gray_color)
        svg_normal = svg_normal.replace('#D32F2F', gray_color).replace('#d32f2f', gray_color)
        
        # 3. Create the Hover version (original colored curves)
        svg_hover = svg_base
        
        # Generate Icons
        def svg_to_icon(content):
            try:
                renderer = QSvgRenderer(QByteArray(content.encode('utf-8')))
                # Render at high resolution (2x) for sharp look
                pixmap = QPixmap(self.icon_size * 2)
                pixmap.fill(Qt.GlobalColor.transparent)
                painter = QPainter(pixmap)
                renderer.render(painter)
                painter.end()
                return QIcon(pixmap)
            except:
                import traceback
                traceback.print_exc()
                return QIcon()

        self.normal_icon = svg_to_icon(svg_normal)
        self.hover_icon = svg_to_icon(svg_hover)

class FileListItemWidget(QWidget):
    """Custom widget for list items with hover-based remove button and progress indicator"""
    remove_clicked = pyqtSignal()
    
    def __init__(self, text, file_path=None, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.installEventFilter(self)
        self._hovered = False
        self.file_path = file_path
        self._is_completed = False  # Track if conversion is complete
        
        # Set transparent background
        self.setStyleSheet("background-color: transparent;")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)  # Give more space vertically
        layout.setSpacing(10)
        
        # Thumbnail label (48x48 square)
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(48, 48)
        self.thumbnail_label.setScaledContents(False)
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setStyleSheet("background: #1a1a1a; border: 1px solid #444; border-radius: 4px;")
        
        # Load thumbnail if file_path provided
        if file_path:
            self.load_thumbnail(file_path)
        
        layout.addWidget(self.thumbnail_label)
        
        # Text label - expand to fill height
        self.text_label = QLabel(text)
        self.text_label.setStyleSheet("background: transparent; border: none;")
        self.text_label.setWordWrap(False)  # Prevent wrapping
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.text_label, 1)
        
        # Remove button (X) - use MinimumExpanding to not constrain the layout
        self.remove_btn = QPushButton("✕")
        self.remove_btn.setMaximumSize(28, 28)  # Max size instead of fixed
        self.remove_btn.setMinimumSize(24, 24)
        self.remove_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.remove_btn.setVisible(False)  # Hidden by default
        self.remove_btn.clicked.connect(self.remove_clicked.emit)
        layout.addWidget(self.remove_btn, 0, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        
        self.update_button_style(False)
    
    def set_completed(self):
        """Mark item as completed"""
        self._is_completed = True
    
    def update_theme(self, is_dark):
        """Update widget colors based on theme"""
        if is_dark:
            text_color = "#ffffff"
            thumb_bg = "#1a1a1a"
            thumb_border = "#444"
        else:
            text_color = "#333333"
            thumb_bg = "#f5f5f5"
            thumb_border = "#cccccc"
        
        self.text_label.setStyleSheet(f"background: transparent; border: none; color: {text_color};")
        self.thumbnail_label.setStyleSheet(f"background: {thumb_bg}; border: 1px solid {thumb_border}; border-radius: 4px;")
        
    def sizeHint(self):
        """Return the recommended size for the widget"""
        from PyQt6.QtCore import QSize
        # Don't set a specific width - let the parent container define it
        # Just return height; width will be handled by the parent list widget
        return QSize(0, 56)  # Width 0 means fill available space
    
    def minimumSizeHint(self):
        """Return the minimum recommended size"""
        from PyQt6.QtCore import QSize
        return QSize(0, 50)  # Width 0 means fill available space
        
    def eventFilter(self, obj, event):
        if obj == self:
            if event.type() == QEvent.Type.Enter:
                self._hovered = True
                self.remove_btn.setVisible(True)
            elif event.type() == QEvent.Type.Leave:
                self._hovered = False
                self.remove_btn.setVisible(False)
        return super().eventFilter(obj, event)
    
    def load_thumbnail(self, file_path):
        """Load and display thumbnail for the file"""
        try:
            from PyQt6.QtGui import QPixmap
            from pathlib import Path
            import subprocess
            
            file_ext = Path(file_path).suffix.lower()
            pixmap = None
            
            # For images, load directly
            if file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp', '.gif']:
                pixmap = QPixmap(file_path)
            
            # For videos, extract first frame
            elif file_ext in ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.webm', '.m4v']:
                pixmap = self.extract_video_thumbnail(file_path)
            
            # If thumbnail loaded successfully, scale and display
            if pixmap and not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    48, 48,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.thumbnail_label.setPixmap(scaled_pixmap)
            else:
                # Show file type icon as fallback
                self.set_fallback_icon(file_ext)
        except Exception as e:
            print(f"Failed to load thumbnail: {e}")
            self.set_fallback_icon(Path(file_path).suffix.lower())
    
    def extract_video_thumbnail(self, video_path):
        """Extract first frame from video as thumbnail"""
        try:
            # Get ffmpeg path from environment (set by init_bundled_tools)
            ffmpeg_path = os.environ.get('FFMPEG_BINARY', 'ffmpeg')
            
            # Create temp file for thumbnail
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                thumb_path = tmp.name
            
            try:
                # Extract frame at 0.5 seconds (safer than 1s for short videos)
                cmd = [
                    str(ffmpeg_path),
                    '-ss', '0.5',
                    '-i', str(video_path),
                    '-vframes', '1',
                    '-vf', 'scale=128:-1',
                    '-q:v', '2',  # High quality JPEG
                    '-y',
                    thumb_path
                ]
                
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    timeout=5,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                
                if os.path.exists(thumb_path) and os.path.getsize(thumb_path) > 0:
                    pixmap = QPixmap(thumb_path)
                    try:
                        os.remove(thumb_path)
                    except:
                        pass
                    
                    if not pixmap.isNull():
                        return pixmap
                    else:
                        print(f"Failed to load pixmap from thumbnail")
                else:
                    print(f"Thumbnail file not created or empty. Return code: {result.returncode}")
                    if result.stderr:
                        stderr_text = result.stderr.decode('utf-8', errors='ignore')[:300]
                        print(f"FFmpeg stderr: {stderr_text}")
                
            finally:
                # Clean up temp file if it exists
                if os.path.exists(thumb_path):
                    try:
                        os.remove(thumb_path)
                    except:
                        pass
            
        except subprocess.TimeoutExpired:
            print(f"Video thumbnail extraction timed out for {video_path}")
        except Exception as e:
            print(f"Video thumbnail extraction failed: {e}")
            import traceback
            traceback.print_exc()
        
        return None
    
    def set_fallback_icon(self, file_ext):
        """Set a fallback icon based on file type"""
        # Simple text-based icon
        if file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp', '.gif']:
            icon_text = "🖼"
        elif file_ext in ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.webm', '.m4v']:
            icon_text = "🎬"
        elif file_ext in ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a']:
            icon_text = "🎵"
        else:
            icon_text = "📄"
        
        self.thumbnail_label.setText(icon_text)
        self.thumbnail_label.setStyleSheet(
            "background: #1a1a1a; border: 1px solid #444; border-radius: 4px; "
            "font-size: 24px; color: #888;"
        )
    
    def update_button_style(self, is_dark_theme):
        """Update button styling based on theme"""
        if is_dark_theme:
            btn_style = """
                QPushButton {
                    background-color: transparent;
                    color: #888888;
                    border: none;
                    font-size: 16px;
                    font-weight: bold;
                    padding: 0px;
                }
                QPushButton:hover {
                    color: #ff4444;
                    background-color: rgba(255, 68, 68, 0.1);
                    border-radius: 3px;
                }
                QPushButton:pressed {
                    color: #ff0000;
                    background-color: rgba(255, 0, 0, 0.2);
                }
            """
            text_style = "background: transparent; border: none; color: #ffffff; font-size: 13px;"
        else:
            btn_style = """
                QPushButton {
                    background-color: transparent;
                    color: #999999;
                    border: none;
                    font-size: 16px;
                    font-weight: bold;
                    padding: 0px;
                }
                QPushButton:hover {
                    color: #ff4444;
                    background-color: rgba(255, 68, 68, 0.1);
                    border-radius: 3px;
                }
                QPushButton:pressed {
                    color: #ff0000;
                    background-color: rgba(255, 0, 0, 0.2);
                }
            """
            text_style = "background: transparent; border: none; color: #333333; font-size: 13px;"
        
        self.remove_btn.setStyleSheet(btn_style)
        self.text_label.setStyleSheet(text_style)
        
        # Update thumbnail border color based on theme
        current_thumb_style = self.thumbnail_label.styleSheet()
        if is_dark_theme:
            thumb_style = "background: #1a1a1a; border: 1px solid #444; border-radius: 4px;"
            if "font-size" in current_thumb_style:  # Has emoji fallback
                thumb_style += " font-size: 24px; color: #888;"
        else:
            thumb_style = "background: #f5f5f5; border: 1px solid #ddd; border-radius: 4px;"
            if "font-size" in current_thumb_style:  # Has emoji fallback
                thumb_style += " font-size: 24px; color: #666;"
        
        self.thumbnail_label.setStyleSheet(thumb_style)

class DragDropArea(QWidget):
    files_added = pyqtSignal(list)  # Signal emitted when files are added
    preset_applied = pyqtSignal(object, list)  # Emits (preset, files) when preset selected
    
    # Supported file extensions for graphics conversion
    SUPPORTED_EXTENSIONS = {
        'images': ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp', '.gif'],
        'videos': ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.webm', '.m4v'],
        'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a']
    }
    
    def __init__(self):
        super().__init__()
        self.file_list = []
        self.theme_manager = None  # Will be set by parent
        self.setAcceptDrops(True)  # Enable drag/drop on the main widget
        self._current_processing_index = -1  # Track which file is being processed
        self._pending_files = None  # Files waiting for preset selection
        self.setup_ui()
        self._setup_overlay()
    
    def set_file_progress(self, file_index, progress):
        """Set progress for a specific file in the list (0.0 to 1.0) - No-op now"""
        # Progress display removed - only show completion
        pass
    
    def set_file_completed(self, file_index):
        """Mark a file as completed"""
        if 0 <= file_index < self.file_list_widget.count():
            item = self.file_list_widget.item(file_index)
            # Store completion state in item data
            item.setData(Qt.ItemDataRole.UserRole + 1, True)
            
            # Mark the widget as completed (no visual change)
            widget = self.file_list_widget.itemWidget(item)
            if widget and hasattr(widget, 'set_completed'):
                widget.set_completed()

    def set_preset_active(self, active, text="PRESETS"):
        """Update the state of the integrated preset button"""
        if hasattr(self, 'preset_status_btn'):
            self.preset_status_btn.set_active(active, text)
    
    def clear_all_progress(self):
        """Clear progress indicators from all files"""
        for i in range(self.file_list_widget.count()):
            item = self.file_list_widget.item(i)
            widget = self.file_list_widget.itemWidget(item)
            if widget and hasattr(widget, 'clear_progress'):
                widget.clear_progress()
        self._current_processing_index = -1
        
    def setup_ui(self):
        """Setup the drag and drop interface"""
        layout = QVBoxLayout(self)
        
        # Control buttons at top
        button_layout = QHBoxLayout()
        icon_size = QSize(28, 28)  # 28px icon in 48px square
        
        self.add_files_btn = HoverIconButton("addfile.svg", icon_size)
        self.add_files_btn.setFixedSize(48, 48)
        self.add_files_btn.setToolTip("Add Files")
        self.add_files_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.add_files_btn.clicked.connect(self.add_files_dialog)
        
        self.add_folder_btn = HoverIconButton("addfolder.svg", icon_size)
        self.add_folder_btn.setFixedSize(48, 48)
        self.add_folder_btn.setToolTip("Add Folder")
        self.add_folder_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.add_folder_btn.clicked.connect(self.add_folder_dialog)
        
        self.clear_files_btn = HoverIconButton("removefile.svg", icon_size)
        self.clear_files_btn.setFixedSize(48, 48)
        self.clear_files_btn.setToolTip("Clear All")
        self.clear_files_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.clear_files_btn.clicked.connect(self.clear_files)
        
        # Apply ActionSquare object name for identification
        self.add_files_btn.setObjectName("ActionSquare")
        self.add_folder_btn.setObjectName("ActionSquare")
        self.clear_files_btn.setObjectName("ActionSquare")
        
        button_layout.addWidget(self.add_files_btn)
        button_layout.addWidget(self.add_folder_btn)
        button_layout.addWidget(self.clear_files_btn)
        button_layout.addStretch()
        
        # Presets Button (Right Aligned)
        self.preset_status_btn = PresetStatusButton()
        self.preset_status_btn.clicked.connect(self.show_preset_view)
        button_layout.addWidget(self.preset_status_btn)
        
        layout.addLayout(button_layout)
        
        # Combined file list widget that serves as both drop area and display
        self.file_list_widget = QListWidget()
        self.file_list_widget.setObjectName("DropZone")  # V4.0 branding
        self.file_list_widget.setMinimumHeight(300)
        
        # Disable dashed focus rectangle
        self.file_list_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        # Initial styling will be set by theme manager
        self.reset_list_style()
        
        # Disable drag/drop on the list widget - we handle it on the parent
        self.file_list_widget.setAcceptDrops(False)
        
        # Connect double-click to remove file
        self.file_list_widget.itemDoubleClicked.connect(self.remove_file_item)
        
        # Add keyboard delete functionality
        self.file_list_widget.keyPressEvent = self.handle_list_key_press
        
        # Add context menu for file operations
        self.file_list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_list_widget.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.file_list_widget)
        
        # Initialize with cleared state
        self.file_list_widget.clear()
        
    def _setup_overlay(self):
        """Setup the preset overlay inside the drop area"""
        from client.gui.preset_overlay import PresetOverlay
        
        # Parent to file_list_widget to stay inside the list styling
        # self.file_list_widget is defined in setup_ui
        self.preset_overlay = PresetOverlay(self.file_list_widget)
        self.preset_overlay.hide()
        self.preset_overlay.preset_selected.connect(self._on_preset_selected)
        self.preset_overlay.dismissed.connect(self._on_overlay_dismissed)
        
        # Match border radius of the container
        current_style = self.preset_overlay.styleSheet()
        self.preset_overlay.setStyleSheet(current_style + "\nQWidget#PresetOverlay { border-radius: 12px; }")
    
    def show_preset_view(self):
        """Manually show the preset overlay (e.g. from Presets button)"""
        if hasattr(self, 'preset_overlay') and hasattr(self, 'file_list_widget'):
            self.preset_overlay.setGeometry(0, 0, self.file_list_widget.width(), self.file_list_widget.height())
            self.preset_overlay.show_animated()

    def _on_preset_selected(self, preset_obj):
        """Handle preset card click"""
        self.preset_overlay.hide_animated()
        
        # Update button state immediately (don't wait for signal round-trip)
        self.set_preset_active(True, preset_obj.title)
        
        if self._pending_files:
            # Emit signal with preset and files
            self.preset_applied.emit(preset_obj, self._pending_files)
            self._pending_files = None
        else:
            # No files pending - Emit for global preset change
            self.preset_applied.emit(preset_obj, [])
    
    def _on_overlay_dismissed(self):
        """Handle click on overlay background"""
        self.preset_overlay.hide_animated()
        
        if self._pending_files:
            # Add files without preset
            self.add_files(self._pending_files)
            self._pending_files = None
    
    def resizeEvent(self, event):
        """Update placeholder size and overlay geometry"""
        super().resizeEvent(event)
        
        # Update overlay geometry to cover the file list widget
        if hasattr(self, 'preset_overlay') and hasattr(self, 'file_list_widget'):
            self.preset_overlay.setGeometry(0, 0, self.file_list_widget.width(), self.file_list_widget.height())
        
        if hasattr(self, 'file_list_widget') and self.file_list_widget.count() == 1:
            item = self.file_list_widget.item(0)
            if item and item.data(Qt.ItemDataRole.UserRole) == "PLACEHOLDER":
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(10, self.update_placeholder_size)

    def update_placeholder_size(self):
        """Specifically update the placeholder item size to match viewport"""
        if hasattr(self, 'file_list_widget') and self.file_list_widget.count() == 1:
            item = self.file_list_widget.item(0)
            if item and item.data(Qt.ItemDataRole.UserRole) == "PLACEHOLDER":
                viewport_size = self.file_list_widget.viewport().size()
                if viewport_size.height() > 50:
                    item.setSizeHint(viewport_size)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Show overlay when files are dragged over"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            # Show overlay
            if hasattr(self, 'preset_overlay') and hasattr(self, 'file_list_widget'):
                self.preset_overlay.setGeometry(0, 0, self.file_list_widget.width(), self.file_list_widget.height())
                self.preset_overlay.show_animated()
        else:
            event.ignore()
            
    def dragLeaveEvent(self, event):
        """Hide overlay when drag leaves"""
        if hasattr(self, 'preset_overlay'):
            self.preset_overlay.hide_animated()
        event.accept()
        
    def dropEvent(self, event: QDropEvent):
        """Store files as pending and wait for user action"""
        if event.mimeData().hasUrls():
            files = []
            folders = []
            
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if os.path.isfile(path):
                    files.append(path)
                elif os.path.isdir(path):
                    folders.append(path)
            
            # Collect all files including from folders
            all_files = files.copy()
            for folder in folders:
                folder_files = self.get_supported_files_from_folder(folder, True)
                all_files.extend(folder_files)
            
            # Store as pending - overlay stays visible
            self._pending_files = all_files
            
            event.acceptProposedAction()
        else:
            event.ignore()
        
    def handle_dropped_folders(self, folders):
        """Handle dropped folder(s) with user options"""
        from PyQt6.QtWidgets import QCheckBox, QVBoxLayout, QDialog, QDialogButtonBox, QLabel
        
        if len(folders) == 1:
            folder_name = os.path.basename(folders[0])
            title = f"Process Folder: {folder_name}"
        else:
            title = f"Process {len(folders)} Folders"
            
        # Create options dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Folder Drop Options")
        dialog.setFixedSize(400, 250)
        
        # Apply theme styling
        if hasattr(self, 'theme_manager'):
            dialog.setStyleSheet(self.theme_manager.get_dialog_styles())
        
        layout = QVBoxLayout(dialog)
        
        if len(folders) == 1:
            layout.addWidget(QLabel(f"Dropped folder: {folder_name}"))
        else:
            layout.addWidget(QLabel(f"Dropped {len(folders)} folder(s):"))
            for folder in folders[:3]:  # Show first 3
                layout.addWidget(QLabel(f"• {os.path.basename(folder)}"))
            if len(folders) > 3:
                layout.addWidget(QLabel(f"• ... and {len(folders) - 3} more"))
                
        layout.addWidget(QLabel("\nChoose processing options:"))
        
        # Include subfolders option
        include_subfolders = QCheckBox("Include subfolders (recursive)")
        include_subfolders.setChecked(False)
        layout.addWidget(include_subfolders)
        
        # Show file count preview
        preview_label = QLabel("")
        layout.addWidget(preview_label)
        
        def update_preview():
            total_count = 0
            for folder in folders:
                total_count += self.count_supported_files(folder, include_subfolders.isChecked())
            preview_label.setText(f"Found {total_count} supported file(s) total")
        
        include_subfolders.toggled.connect(update_preview)
        update_preview()  # Initial count
        
        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            all_files = []
            for folder in folders:
                folder_files = self.get_supported_files_from_folder(folder, include_subfolders.isChecked())
                all_files.extend(folder_files)
                
            if all_files:
                self.add_files(all_files)
                self.update_status(f"Added {len(all_files)} files from {len(folders)} folder(s)")
            else:
                QMessageBox.information(self, "No Files Found", "No supported files found in the dropped folder(s).")
                
    def update_status(self, message):
        """Emit a status update (to be connected by parent)"""
        # This will be connected to the main window's update_status method
        pass
        
    def on_drag_enter(self):
        """Handle drag enter visual feedback"""
        if self.theme_manager:
            styles = self.theme_manager.get_drag_drop_styles()
            full_style = styles['drag_over'] + self._get_scrollbar_style()
            self.file_list_widget.setStyleSheet(full_style)
        
    def on_drag_leave(self):
        """Handle drag leave visual feedback"""
        self.reset_list_style()
        
    def reset_list_style(self):
        """Reset the list widget to default style using V4.0 Theme Variables"""
        is_dark = True
        if self.theme_manager:
            is_dark = self.theme_manager.current_theme == 'dark'
            
        surface_main = get_color("surface_main", is_dark)
        border_dim = get_color("border_dim", is_dark)
        border_focus = get_color("border_focus", is_dark)
        text_primary = get_color("text_primary", is_dark)
        
        # Base DropZone style
        base_style = f"""
            QListWidget#DropZone {{
                background-color: {surface_main};
                border: 2px dashed {border_dim};
                border-radius: 12px;
                color: {text_primary};
                font-size: 14px;
                padding: 10px;
                outline: none;
            }}
            QListWidget#DropZone:hover {{
                border-color: {border_focus};
                background-color: {surface_main}; /* Keep same or slightly lighter? */
            }}
        """
        # Append scrollbar styling
        full_style = base_style + self._get_scrollbar_style()
        self.file_list_widget.setStyleSheet(full_style)
        
        # Restore completion backgrounds for completed items
        is_dark = self.theme_manager and self.theme_manager.current_theme == 'dark'
        
        for i in range(self.file_list_widget.count()):
            item = self.file_list_widget.item(i)
            if item:
                # Update widget theme colors (this also restores completion background if applicable)
                widget = self.file_list_widget.itemWidget(item)
                if widget and hasattr(widget, 'update_theme'):
                    widget.update_theme(is_dark)
            
    def _get_scrollbar_style(self):
        """Get modern minimalistic scrollbar styling with grey item selection"""
        is_dark = self.theme_manager and self.theme_manager.current_theme == 'dark'
        
        if is_dark:
            return """
                QListWidget::item {
                    outline: none;
                    border: none;
                }
                QListWidget::item:selected {
                    background-color: #3a3a3a;
                    color: #ffffff;
                    outline: none;
                    border: none;
                }
                QListWidget::item:focus {
                    outline: none;
                    border: none;
                }
                QListWidget::item:selected:focus {
                    background-color: #3a3a3a;
                    outline: none;
                    border: none;
                }
                QListWidget::item:hover:!selected {
                    background-color: #4a4a4a;
                }
                QScrollBar:vertical {
                    background: #1a1a1a;
                    width: 10px;
                    border: none;
                    border-radius: 5px;
                }
                QScrollBar::handle:vertical {
                    background: #404040;
                    border-radius: 5px;
                    min-height: 30px;
                }
                QScrollBar::handle:vertical:hover {
                    background: #505050;
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    height: 0px;
                }
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                    background: none;
                }
                QScrollBar:horizontal {
                    background: #1a1a1a;
                    height: 10px;
                    border: none;
                    border-radius: 5px;
                }
                QScrollBar::handle:horizontal {
                    background: #404040;
                    border-radius: 5px;
                    min-width: 30px;
                }
                QScrollBar::handle:horizontal:hover {
                    background: #505050;
                }
                QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                    width: 0px;
                }
                QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                    background: none;
                }
            """
        else:
            return """
                QListWidget::item {
                    outline: none;
                    border: none;
                }
                QListWidget::item:selected {
                    background-color: #d3d3d3;
                    color: #333333;
                    outline: none;
                    border: none;
                }
                QListWidget::item:focus {
                    outline: none;
                    border: none;
                }
                QListWidget::item:selected:focus {
                    background-color: #d3d3d3;
                    outline: none;
                    border: none;
                }
                QListWidget::item:hover:!selected {
                    background-color: #e0e0e0;
                }
                QScrollBar:vertical {
                    background: #f0f0f0;
                    width: 10px;
                    border: none;
                    border-radius: 5px;
                }
                QScrollBar::handle:vertical {
                    background: #c0c0c0;
                    border-radius: 5px;
                    min-height: 30px;
                }
                QScrollBar::handle:vertical:hover {
                    background: #a0a0a0;
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    height: 0px;
                }
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                    background: none;
                }
                QScrollBar:horizontal {
                    background: #f0f0f0;
                    height: 10px;
                    border: none;
                    border-radius: 5px;
                }
                QScrollBar::handle:horizontal {
                    background: #c0c0c0;
                    border-radius: 5px;
                    min-width: 30px;
                }
                QScrollBar::handle:horizontal:hover {
                    background: #a0a0a0;
                }
                QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                    width: 0px;
                }
                QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                    background: none;
                }
            """
    
    def _apply_scrollbar_style(self):
        """Apply scrollbar styling to the file list widget"""
        self.reset_list_style()
    
    def set_theme_manager(self, theme_manager):
        """Set the theme manager and apply current theme"""
        self.theme_manager = theme_manager
        # Only update styles, don't clear files (preserves list when switching themes)
        self.reset_list_style()
        self.update_placeholder_text()
        
        # Apply specific styling to the buttons (compact icon buttons)
        if self.theme_manager:
            current_theme = self.theme_manager.get_current_theme()
            is_dark = current_theme == 'dark'
            
            # Update icons for theme and hover behavior
            self.add_files_btn.set_dark_mode(is_dark)
            self.add_folder_btn.set_dark_mode(is_dark)
            self.clear_files_btn.set_dark_mode(is_dark)
            
            # Apply V4 Action Button Styling
            self._update_action_buttons_style(is_dark)

    def _update_action_buttons_style(self, is_dark):
        """Apply ActionSquare styling from theme variables"""
        surface_element = get_color("surface_element", is_dark)
        border_dim = get_color("border_dim", is_dark)
        border_focus = get_color("border_focus", is_dark)
        
        # Spec: Rounded square, surface_element bg, border_dim border
        style = f"""
            QPushButton {{
                background-color: {surface_element};
                border: 1px solid {border_dim};
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: {border_dim};
                border-color: {border_focus};
            }}
            QPushButton:pressed {{
                background-color: #000000;
            }}
        """
        for btn in [self.add_files_btn, self.add_folder_btn, self.clear_files_btn]:
            btn.setStyleSheet(style)
        
    def add_files_dialog(self):
        """Open file dialog to add files"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select files for conversion",
            "",
            "All Supported (*.jpg *.jpeg *.png *.bmp *.tiff *.gif *.mp4 *.avi *.mov *.mkv *.mp3 *.wav);;Images (*.jpg *.jpeg *.png *.bmp *.tiff *.gif);;Videos (*.mp4 *.avi *.mov *.mkv);;Audio (*.mp3 *.wav *.flac);;All Files (*)"
        )
        
        if files:
            self.add_files(files)
            
    def add_folder_dialog(self):
        """Open folder dialog to add all supported files from a directory"""
        from PyQt6.QtWidgets import QFileDialog, QCheckBox, QVBoxLayout, QDialog, QDialogButtonBox, QLabel
        
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select folder to process all supported files",
            ""
        )
        
        if folder:
            # Create options dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Folder Processing Options")
            dialog.setFixedSize(400, 200)
            
            # Apply theme styling
            if hasattr(self, 'theme_manager'):
                dialog.setStyleSheet(self.theme_manager.get_dialog_styles())
            
            layout = QVBoxLayout(dialog)
            
            layout.addWidget(QLabel(f"Selected folder: {os.path.basename(folder)}"))
            layout.addWidget(QLabel("Choose processing options:"))
            
            # Include subfolders option
            include_subfolders = QCheckBox("Include subfolders (recursive)")
            include_subfolders.setChecked(False)
            layout.addWidget(include_subfolders)
            
            # Show file count preview
            preview_label = QLabel("")
            layout.addWidget(preview_label)
            
            def update_preview():
                count = self.count_supported_files(folder, include_subfolders.isChecked())
                preview_label.setText(f"Found {count} supported file(s)")
            
            include_subfolders.toggled.connect(update_preview)
            update_preview()  # Initial count
            
            # Dialog buttons
            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                files = self.get_supported_files_from_folder(folder, include_subfolders.isChecked())
                if files:
                    self.add_files(files)
                else:
                    QMessageBox.information(self, "No Files Found", "No supported files found in the selected folder.")
                    
    def count_supported_files(self, folder_path, include_subfolders=False):
        """Count supported files in folder"""
        count = 0
        folder = Path(folder_path)
        
        if include_subfolders:
            # Recursive search
            for file_path in folder.rglob('*'):
                if file_path.is_file() and self.is_supported_file(file_path.suffix.lower()):
                    count += 1
        else:
            # Only direct files in folder
            for file_path in folder.iterdir():
                if file_path.is_file() and self.is_supported_file(file_path.suffix.lower()):
                    count += 1
                    
        return count
        
    def get_supported_files_from_folder(self, folder_path, include_subfolders=False):
        """Get list of supported files from folder"""
        files = []
        folder = Path(folder_path)
        
        try:
            if include_subfolders:
                # Recursive search
                for file_path in folder.rglob('*'):
                    if file_path.is_file() and self.is_supported_file(file_path.suffix.lower()):
                        files.append(str(file_path))
            else:
                # Only direct files in folder
                for file_path in folder.iterdir():
                    if file_path.is_file() and self.is_supported_file(file_path.suffix.lower()):
                        files.append(str(file_path))
                        
            # Sort files for consistent ordering
            files.sort()
            
        except PermissionError:
            QMessageBox.warning(self, "Access Denied", f"Cannot access folder: {folder_path}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error reading folder: {str(e)}")
            
        return files
            
    def add_files(self, files):
        """Add files to the conversion list"""
        added_files = []
        unsupported_count = 0
        
        for file_path in files:
            if file_path not in self.file_list:
                # Check if file type is supported
                file_ext = Path(file_path).suffix.lower()
                if self.is_supported_file(file_ext):
                    self.file_list.append(file_path)
                    added_files.append(file_path)
                    
                    # Add to list widget with file info
                    file_name = os.path.basename(file_path)
                    file_size = self.get_file_size(file_path)
                    item_text = f"{file_name} ({file_size})"
                    
                    # Create custom widget for the item
                    item = QListWidgetItem()
                    item.setToolTip(f"Full path: {file_path}\nSize: {file_size}")
                    
                    # Create custom widget with remove button and thumbnail
                    item_widget = FileListItemWidget(item_text, file_path, self)
                    is_dark = self.theme_manager and self.theme_manager.current_theme == 'dark'
                    item_widget.update_button_style(is_dark)
                    
                    # Connect remove button - use closure to capture the widget
                    def create_remove_handler(widget):
                        def handler():
                            # Find the index by iterating through list
                            for i in range(self.file_list_widget.count()):
                                if self.file_list_widget.itemWidget(self.file_list_widget.item(i)) == widget:
                                    self.remove_file_by_index(i)
                                    break
                        return handler
                    
                    item_widget.remove_clicked.connect(create_remove_handler(item_widget))
                    
                    # Set size and add to list
                    item.setSizeHint(item_widget.sizeHint())
                    self.file_list_widget.addItem(item)
                    self.file_list_widget.setItemWidget(item, item_widget)
                else:
                    unsupported_count += 1
        
        # Show single consolidated dialog if there were unsupported files
        if unsupported_count > 0:
            self.show_unsupported_files_dialog(unsupported_count)
                    
        if added_files:
            self.files_added.emit(added_files)
            self.update_placeholder_text()
            
    def get_file_size(self, file_path):
        """Get human readable file size"""
        try:
            size = os.path.getsize(file_path)
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024:
                    return f"{size:.1f} {unit}"
                size /= 1024
            return f"{size:.1f} TB"
        except:
            return "Unknown size"
        
    def is_supported_file(self, extension):
        """Check if file extension is supported"""
        for category, extensions in self.SUPPORTED_EXTENSIONS.items():
            if extension in extensions:
                return True
        return False
        
    def clear_files(self):
        """Clear all files from the list"""
        self.file_list.clear()
        self.file_list_widget.clear()
        self.update_placeholder_text()
        
    def update_placeholder_text(self):
        """Update placeholder - show centered red container when empty"""
        if len(self.file_list) == 0:
            # Clear all items first to avoid duplicates
            self.file_list_widget.clear()
            
            # Create a transparent wrapper
            wrapper = QWidget()
            wrapper.setStyleSheet("background-color: transparent; border: none;")
            wrapper_layout = QVBoxLayout(wrapper)
            wrapper_layout.setContentsMargins(0, 0, 0, 0)
            # Align center vertically, but let it stretch horizontally
            wrapper_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            
            # Create small centered container with transparent background
            container = QWidget()
            # Remove fixed size to adapt to width
            from PyQt6.QtWidgets import QSizePolicy
            container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            container.setStyleSheet("background-color: transparent;")
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Load SVG icon with grey color
            svg_label = QLabel()
            svg_label.setStyleSheet("background-color: transparent;")
            svg_path = Path(__file__).parent.parent / "assets" / "icons" / "drag_drop.svg"
            if svg_path.exists():
                # Apply grey color effect to the icon
                from PyQt6.QtGui import QPainter, QColor
                from PyQt6.QtWidgets import QGraphicsColorizeEffect
                
                pixmap = QPixmap(str(svg_path))
                # Scale to fit container
                pixmap = pixmap.scaledToWidth(150, Qt.TransformationMode.SmoothTransformation)
                svg_label.setPixmap(pixmap)
                
                # Apply grey colorize effect
                colorize_effect = QGraphicsColorizeEffect()
                colorize_effect.setColor(QColor(128, 128, 128))  # Grey color
                colorize_effect.setStrength(1.0)
                svg_label.setGraphicsEffect(colorize_effect)
            
            svg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            container_layout.addWidget(svg_label, alignment=Qt.AlignmentFlag.AlignCenter)
            
            # Add text label below the icon
            text_label = QLabel("drag and drop media files here")
            text_label.setStyleSheet("""
                background-color: transparent;
                color: #888888;
                font-size: 14px;
                padding-top: 10px;
            """)
            text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            container_layout.addWidget(text_label, alignment=Qt.AlignmentFlag.AlignCenter)
            
            wrapper_layout.addWidget(container)
            
            # Get current style and completely override item styling
            if self.theme_manager:
                styles = self.theme_manager.get_drag_drop_styles()
                base_style = styles['normal']
            else:
                base_style = ""
            
            # Replace ALL item styling to be transparent with no borders/padding
            modified_style = base_style.replace(
                'background-color: #3c3c3c;', 
                'background-color: transparent;'
            ).replace(
                'background-color: white;',
                'background-color: transparent;'
            ).replace(
                'border: 1px solid #444;',
                'border: none;'
            ).replace(
                'border: 1px solid #ddd;',
                'border: none;'
            ).replace(
                'margin: 2px;',
                'margin: 0px;'
            ).replace(
                'padding: 8px;',
                'padding: 0px;'
            )
            # Add scrollbar styling
            modified_style += self._get_scrollbar_style()
            self.file_list_widget.setStyleSheet(modified_style)
            
            # Add wrapper to list widget with full vertical height
            item = QListWidgetItem()
            # Use a large enough size to fill the area
            viewport_size = self.file_list_widget.viewport().size()
            if viewport_size.height() < 100:  # If not properly sized yet
                item.setSizeHint(self.file_list_widget.size())
            else:
                item.setSizeHint(viewport_size)
            item.setBackground(Qt.GlobalColor.transparent)
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            # Mark as placeholder with special data
            item.setData(Qt.ItemDataRole.UserRole, "PLACEHOLDER")
            self.file_list_widget.addItem(item)
            self.file_list_widget.setItemWidget(item, wrapper)
        else:
            # Remove any placeholder items if files are present
            items_to_remove = []
            for i in range(self.file_list_widget.count()):
                item = self.file_list_widget.item(i)
                if item and item.data(Qt.ItemDataRole.UserRole) == "PLACEHOLDER":
                    items_to_remove.append(i)
            
            # Remove placeholder items in reverse order
            for i in reversed(items_to_remove):
                self.file_list_widget.takeItem(i)
            
            # Restore original list widget styling
            self.reset_list_style()
                    
    def remove_file_by_index(self, index):
        """Remove a file by its index in the list"""
        if 0 <= index < len(self.file_list):
            # Remove from file list
            self.file_list.pop(index)
            
            # Remove from widget
            self.file_list_widget.takeItem(index)
            
            # Update placeholder if empty
            self.update_placeholder_text()
            
    def remove_file_item(self, item):
        """Remove a file item when double-clicked"""
        if item:
            row = self.file_list_widget.row(item)
            if 0 <= row < len(self.file_list):
                self.remove_file_by_index(row)
    
    def show_unsupported_files_dialog(self, count):
        """Show a single consolidated dialog for unsupported files"""
        from PyQt6.QtWidgets import QDialog
        from PyQt6.QtGui import QFont
        
        dialog = QDialog(self)
        dialog.setWindowTitle("")  # No title bar text
        dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        dialog.setFixedSize(400, 150)
        dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)  # Remove close button
        
        # Apply theme styling
        if self.theme_manager:
            dialog.setStyleSheet(self.theme_manager.get_dialog_styles())
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Message label
        message_label = QLabel(f"There were {count} unsupported file(s).\nSkipped {count} file(s).")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = message_label.font()
        font.setPointSize(11)
        message_label.setFont(font)
        layout.addWidget(message_label)
        
        # OK button
        ok_button = QPushButton("OK")
        ok_button.setFixedWidth(80)
        ok_button.clicked.connect(dialog.accept)
        
        # Center the button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        dialog.exec()
            
    def handle_list_key_press(self, event):
        """Handle keyboard events for the file list"""
        from PyQt6.QtCore import Qt
        
        # Handle Delete and Backspace keys to remove selected items
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            selected_items = self.file_list_widget.selectedItems()
            if selected_items:
                # Remove items in reverse order to maintain correct indices
                for item in reversed(selected_items):
                    if not item.text().startswith("📁"):  # Don't remove placeholder
                        row = self.file_list_widget.row(item)
                        file_path = self.file_list[row]
                        
                        # Remove from both lists
                        self.file_list.remove(file_path)
                        self.file_list_widget.takeItem(row)
                
                # Update placeholder if empty
                self.update_placeholder_text()
        else:
            # Call the original key press event handler for other keys
            QListWidget.keyPressEvent(self.file_list_widget, event)
            
    def show_context_menu(self, position):
        """Show context menu for file operations"""
        item = self.file_list_widget.itemAt(position)
        
        # Only show for actual files (not placeholder)
        if item and item.data(Qt.ItemDataRole.UserRole) != "PLACEHOLDER":
            from PyQt6.QtWidgets import QMenu
            
            menu = QMenu(self)
            
            # Remove action
            remove_action = QAction("Remove File", self)
            remove_action.triggered.connect(lambda: self.remove_file_item(item))
            menu.addAction(remove_action)
            
            # Show file location action
            show_action = QAction("Show in Explorer", self)
            show_action.triggered.connect(lambda: self.show_in_explorer(item))
            menu.addAction(show_action)
            
            menu.exec(self.file_list_widget.mapToGlobal(position))
            
    def show_in_explorer(self, item):
        """Open file location in Windows Explorer"""
        if item and item.data(Qt.ItemDataRole.UserRole) != "PLACEHOLDER":
            row = self.file_list_widget.row(item)
            if 0 <= row < len(self.file_list):
                file_path = self.file_list[row]
                
                import subprocess
                try:
                    # Use the file_path with proper formatting for Windows Explorer
                    folder_path = os.path.dirname(file_path)
                    if os.path.isdir(folder_path):
                        # Open Explorer and highlight the file
                        subprocess.Popen(['explorer', '/select,', os.path.normpath(file_path)])
                except Exception as e:
                    print(f"Error opening Explorer: {e}")
                    # Fallback: just open the folder
                    try:
                        folder_path = os.path.dirname(file_path)
                        if os.path.isdir(folder_path):
                            subprocess.Popen(['explorer', os.path.normpath(folder_path)])
                    except Exception as e2:
                        print(f"Error opening folder: {e2}")
            
    def get_files(self):
        """Return the list of selected files"""
        return self.file_list.copy()

