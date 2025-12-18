"""
Drag and Drop Area Widget
Handles file drag and drop operations for the graphics converter
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QPushButton, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QPixmap, QIcon, QAction, QPainter, QColor
import os
from pathlib import Path

class DragDropArea(QWidget):
    files_added = pyqtSignal(list)  # Signal emitted when files are added
    
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
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the drag and drop interface"""
        layout = QVBoxLayout(self)
        
        # Control buttons at top
        button_layout = QHBoxLayout()
        
        self.add_files_btn = QPushButton("Add Files...")
        self.add_files_btn.clicked.connect(self.add_files_dialog)
        
        self.add_folder_btn = QPushButton("Browse Folder...")
        self.add_folder_btn.clicked.connect(self.add_folder_dialog)
        
        self.clear_files_btn = QPushButton("Clear All")
        self.clear_files_btn.clicked.connect(self.clear_files)
        
        button_layout.addWidget(self.add_files_btn)
        button_layout.addWidget(self.add_folder_btn)
        button_layout.addWidget(self.clear_files_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # Combined file list widget that serves as both drop area and display
        self.file_list_widget = QListWidget()
        self.file_list_widget.setMinimumHeight(300)
        
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
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.on_drag_enter()
        else:
            event.ignore()
            
    def dragLeaveEvent(self, event):
        """Handle drag leave events"""
        self.on_drag_leave()
        super().dragLeaveEvent(event)
        
    def dropEvent(self, event: QDropEvent):
        """Handle file drop events"""
        files = []
        folders = []
        
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isfile(path):
                files.append(path)
            elif os.path.isdir(path):
                folders.append(path)
                
        # Add individual files
        if files:
            self.add_files(files)
            
        # Handle dropped folders
        if folders:
            self.handle_dropped_folders(folders)
            
        self.on_drag_leave()
        event.acceptProposedAction()
        
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
        """Reset the list widget to default style"""
        if self.theme_manager:
            styles = self.theme_manager.get_drag_drop_styles()
            base_style = styles['normal']
            # Append scrollbar styling
            full_style = base_style + self._get_scrollbar_style()
            self.file_list_widget.setStyleSheet(full_style)
        else:
            # Fallback to light theme
            self.file_list_widget.setStyleSheet("""
                DragDropArea {
                    border: 3px dashed #aaa;
                    border-radius: 10px;
                    background-color: #f9f9f9;
                    color: #666;
                    font-size: 14px;
                    padding: 10px;
                }
                DragDropArea:hover {
                    border-color: #4CAF50;
                    background-color: #f0f8f0;
                }
            """)
            
    def _get_scrollbar_style(self):
        """Get modern minimalistic scrollbar styling"""
        is_dark = self.theme_manager and self.theme_manager.current_theme == 'dark'
        
        if is_dark:
            return """
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
            """
        else:
            return """
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
            """
    
    def _apply_scrollbar_style(self):
        """Apply scrollbar styling to the file list widget"""
        self.reset_list_style()
    
    def set_theme_manager(self, theme_manager):
        """Set the theme manager and apply current theme"""
        self.theme_manager = theme_manager
        # Clear and rebuild with proper theme
        self.file_list_widget.clear()
        self.file_list.clear()
        self.update_placeholder_text()
        
        # Apply specific styling to the clear button (red outline)
        if self.theme_manager:
            current_theme = self.theme_manager.get_current_theme()
            if current_theme == 'dark':
                clear_button_style = """
                    QPushButton {
                        background-color: #404040;
                        color: #ffffff;
                        border: 1px solid #555555;
                        padding: 6px 12px;
                        border-radius: 4px;
                        font-size: 13px;
                    }
                    QPushButton:hover {
                        background-color: #4a4a4a;
                        border-color: #f44336;
                    }
                    QPushButton:pressed {
                        background-color: #363636;
                        border-color: #d32f2f;
                    }
                """
            else:
                clear_button_style = """
                    QPushButton {
                        background-color: #f0f0f0;
                        color: #333333;
                        border: 1px solid #cccccc;
                        padding: 6px 12px;
                        border-radius: 4px;
                        font-size: 13px;
                    }
                    QPushButton:hover {
                        background-color: #e8e8e8;
                        border-color: #f44336;
                    }
                    QPushButton:pressed {
                        background-color: #d8d8d8;
                        border-color: #d32f2f;
                    }
                """
            self.clear_files_btn.setStyleSheet(clear_button_style)
        
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
                    
                    item = QListWidgetItem(item_text)
                    item.setToolTip(f"Full path: {file_path}\nSize: {file_size}")
                    self.file_list_widget.addItem(item)
                else:
                    QMessageBox.warning(
                        self,
                        "Unsupported File",
                        f"File type {file_ext} is not supported.\n\nFile: {os.path.basename(file_path)}"
                    )
                    
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
            wrapper_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Create small centered container with transparent background
            container = QWidget()
            container.setFixedSize(200, 200)
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
            
            wrapper_layout.addWidget(container, alignment=Qt.AlignmentFlag.AlignCenter)
            
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
            self.file_list_widget.addItem(item)
            self.file_list_widget.setItemWidget(item, wrapper)
        else:
            # Remove any placeholder items if files are present
            while self.file_list_widget.count() > 0:
                first_item = self.file_list_widget.item(0)
                if first_item and self.file_list_widget.itemWidget(first_item):
                    self.file_list_widget.takeItem(0)
                else:
                    break
            # Restore original list widget styling
            self.reset_list_style()
                    
    def remove_file_item(self, item):
        """Remove a file item when double-clicked"""
        # Don't remove placeholder (which has a widget set)
        if item and not self.file_list_widget.itemWidget(item):
            row = self.file_list_widget.row(item)
            file_path = self.file_list[row]
            
            # Remove from both lists
            self.file_list.remove(file_path)
            self.file_list_widget.takeItem(row)
            
            # Update placeholder if empty
            self.update_placeholder_text()
            
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
        
        if item and not item.text().startswith("📁"):  # Only show for actual files
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
        if item and not item.text().startswith("📁"):
            row = self.file_list_widget.row(item)
            file_path = self.file_list[row]
            
            import subprocess
            try:
                subprocess.run(['explorer', '/select,', file_path])
            except:
                # Fallback: just open the folder
                folder_path = os.path.dirname(file_path)
                subprocess.run(['explorer', folder_path])
            
    def get_files(self):
        """Return the list of selected files"""
        return self.file_list.copy()

