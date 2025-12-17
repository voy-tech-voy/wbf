"""
Drag and Drop Area Widget
Handles file drag and drop operations for the graphics converter
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QPushButton, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QPixmap, QIcon
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
        
        # Add placeholder text when empty
        self.update_placeholder_text()
        
        layout.addWidget(self.file_list_widget)
        
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
        from PyQt5.QtWidgets import QCheckBox, QVBoxLayout, QDialog, QDialogButtonBox, QLabel
        
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
            self.file_list_widget.setStyleSheet(styles['drag_over'])
        
    def on_drag_leave(self):
        """Handle drag leave visual feedback"""
        self.reset_list_style()
        
    def reset_list_style(self):
        """Reset the list widget to default style"""
        if self.theme_manager:
            styles = self.theme_manager.get_drag_drop_styles()
            self.file_list_widget.setStyleSheet(styles['normal'])
        else:
            # Fallback to light theme
            self.file_list_widget.setStyleSheet("""
                QListWidget {
                    border: 3px dashed #aaa;
                    border-radius: 10px;
                    background-color: #f9f9f9;
                    color: #666;
                    font-size: 14px;
                    padding: 10px;
                }
                QListWidget:hover {
                    border-color: #4CAF50;
                    background-color: #f0f8f0;
                }
                QListWidget::item {
                    padding: 8px;
                    margin: 2px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    background-color: white;
                }
                QListWidget::item:selected {
                    background-color: #e3f2fd;
                    border-color: #2196f3;
                }
                QListWidget::item:hover {
                    background-color: #f5f5f5;
                }
            """)
            
    def set_theme_manager(self, theme_manager):
        """Set the theme manager and apply current theme"""
        self.theme_manager = theme_manager
        self.reset_list_style()
        
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
        from PyQt5.QtWidgets import QFileDialog, QCheckBox, QVBoxLayout, QDialog, QDialogButtonBox, QLabel
        
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
        """Update placeholder text when list is empty or add instruction overlay"""
        if len(self.file_list) == 0:
            # Add a placeholder item when empty
            placeholder_item = QListWidgetItem("📁 Drag and drop files here, click 'Add Files...' or 'Browse Folder...'\n\n📋 Supported formats:\n• Images: JPG, PNG, GIF, WEBP, TIFF, BMP\n• Videos: MP4, AVI, MOV, MKV, WEBM\n\n📂 Use 'Browse Folder...' to process entire directories")
            placeholder_item.setFlags(Qt.ItemFlag.NoItemFlags)  # Make it non-selectable
            placeholder_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Style the placeholder differently
            font = placeholder_item.font()
            font.setItalic(True)
            
            self.file_list_widget.addItem(placeholder_item)
        else:
            # Remove placeholder if files are present
            if self.file_list_widget.count() > 0:
                first_item = self.file_list_widget.item(0)
                if first_item and first_item.text().startswith("📁"):
                    self.file_list_widget.takeItem(0)
                    
    def remove_file_item(self, item):
        """Remove a file item when double-clicked"""
        if item and not item.text().startswith("📁"):  # Don't remove placeholder
            row = self.file_list_widget.row(item)
            file_path = self.file_list[row]
            
            # Remove from both lists
            self.file_list.remove(file_path)
            self.file_list_widget.takeItem(row)
            
            # Update placeholder if empty
            self.update_placeholder_text()
            
    def handle_list_key_press(self, event):
        """Handle keyboard events for the file list"""
        from PyQt5.QtCore import Qt
        
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
            from PyQt5.QtWidgets import QMenu
            from PyQt5.QtWidgets import QAction
            
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
