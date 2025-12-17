"""
Theme Manager for the Graphics Conversion App
Handles dark/light mode detection and styling
"""

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import QApplication
import sys

class ThemeManager(QObject):
    """Manages application theming based on system preferences"""
    
    theme_changed = pyqtSignal(str)  # Emits 'dark' or 'light'
    
    def __init__(self):
        super().__init__()
        self.current_theme = 'dark'  # Default to dark mode
        
    def detect_system_theme(self) -> str:
        """Detect if system is using dark mode"""
        palette = QApplication.palette()
        # Check if the window background is darker than the text
        window_color = palette.color(QPalette.ColorRole.Window)
        text_color = palette.color(QPalette.ColorRole.WindowText)
        
        # Calculate luminance to determine if background is dark
        window_luminance = (0.299 * window_color.red() + 
                           0.587 * window_color.green() + 
                           0.114 * window_color.blue()) / 255
        
        return 'dark' if window_luminance < 0.5 else 'light'
    
    def get_current_theme(self) -> str:
        """Get the current theme"""
        return self.current_theme
    
    def set_theme(self, theme: str):
        """Set theme manually (for future toggle functionality)"""
        if theme in ['dark', 'light'] and theme != self.current_theme:
            self.current_theme = theme
            self.theme_changed.emit(theme)
    
    def get_drag_drop_styles(self) -> dict:
        """Get drag and drop area styles for current theme"""
        if self.current_theme == 'dark':
            return {
                'normal': """
                    QListWidget {
                        border: 3px dashed #555;
                        border-radius: 10px;
                        background-color: #2b2b2b;
                        color: #cccccc;
                        font-size: 14px;
                        padding: 10px;
                        font-family: 'Roboto Mono';
                    }
                    QListWidget:hover {
                        border-color: #4CAF50;
                        background-color: #333333;
                    }
                    QListWidget::item {
                        padding: 8px;
                        margin: 2px;
                        border: 1px solid #444;
                        border-radius: 5px;
                        background-color: #3c3c3c;
                        color: #ffffff;
                    }
                    QListWidget::item:selected {
                        background-color: #1976d2;
                        border-color: #2196f3;
                    }
                    QListWidget::item:hover {
                        background-color: #484848;
                    }
                """,
                'drag_over': """
                    QListWidget {
                        border: 3px dashed #4CAF50;
                        border-radius: 10px;
                        background-color: #1a4a1a;
                        color: #4CAF50;
                        font-size: 14px;
                        padding: 10px;
                        font-family: 'Roboto Mono';
                    }
                    QListWidget::item {
                        padding: 8px;
                        margin: 2px;
                        border: 1px solid #444;
                        border-radius: 5px;
                        background-color: #3c3c3c;
                        color: #ffffff;
                    }
                    QListWidget::item:selected {
                        background-color: #1976d2;
                        border-color: #2196f3;
                    }
                    QListWidget::item:hover {
                        background-color: #484848;
                    }
                """
            }
        else:
            return {
                'normal': """
                    QListWidget {
                        border: 3px dashed #aaa;
                        border-radius: 10px;
                        background-color: #f9f9f9;
                        color: #666;
                        font-size: 14px;
                        padding: 10px;
                        font-family: 'Roboto Mono';
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
                """,
                'drag_over': """
                    QListWidget {
                        border: 3px dashed #4CAF50;
                        border-radius: 10px;
                        background-color: #e8f5e8;
                        color: #2E7D32;
                        font-size: 14px;
                        padding: 10px;
                        font-family: 'Roboto Mono';
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
                """
            }
    
    def get_button_styles(self) -> str:
        """Get convert button styles for current theme (special prominent button)"""
        if self.current_theme == 'dark':
            return """
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: 2px solid #45a049;
                    padding: 10px 20px;
                    font-size: 14px;
                    font-weight: bold;
                    border-radius: 6px;
                    font-family: 'Roboto Mono';
                }
                QPushButton:hover {
                    background-color: #45a049;
                    border-color: #3d8b40;
                }
                QPushButton:pressed {
                    background-color: #3d8b40;
                    border-color: #2e6b2e;
                }
                QPushButton:disabled {
                    background-color: #555555;
                    color: #888888;
                    border-color: #666666;
                }
            """
        else:
            return """
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: 2px solid #45a049;
                    padding: 10px 20px;
                    font-size: 14px;
                    font-weight: bold;
                    border-radius: 6px;
                    font-family: 'Roboto Mono';
                }
                QPushButton:hover {
                    background-color: #45a049;
                    border-color: #3d8b40;
                }
                QPushButton:pressed {
                    background-color: #3d8b40;
                    border-color: #2e6b2e;
                }
                QPushButton:disabled {
                    background-color: #cccccc;
                    color: #666666;
                    border-color: #dddddd;
                }
            """
    
    def get_main_window_style(self) -> str:
        """Get main window stylesheet for current theme"""
        if self.current_theme == 'dark':
            return """
                QMainWindow {
                    background-color: #2b2b2b;
                    color: #ffffff;
                    font-family: 'Roboto Mono';
                }
                QMenuBar {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    border-bottom: 1px solid #555555;
                    font-family: 'Roboto Mono';
                    padding: 4px;
                }
                QMenuBar::item {
                    background-color: transparent;
                    padding: 4px 8px;
                    border-radius: 4px;
                }
                QMenuBar::item:selected {
                    background-color: #4CAF50;
                    color: white;
                }
                QMenuBar::item:pressed {
                    background-color: #45a049;
                }
                QMenu {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    border: 1px solid #555555;
                    border-radius: 4px;
                    font-family: 'Roboto Mono';
                }
                QMenu::item {
                    padding: 6px 20px;
                    border-radius: 4px;
                    margin: 1px;
                }
                QMenu::item:selected {
                    background-color: #4CAF50;
                }
                QToolBar {
                    background-color: #3c3c3c;
                    border: none;
                    border-bottom: 1px solid #555555;
                    spacing: 3px;
                    padding: 4px;
                }
                QToolBar::separator {
                    background-color: #555555;
                    width: 1px;
                    margin: 0 4px;
                }
                QPushButton {
                    background-color: #404040;
                    color: #ffffff;
                    border: 1px solid #555555;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-family: 'Roboto Mono';
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #4a4a4a;
                    border-color: #4CAF50;
                }
                QPushButton:pressed {
                    background-color: #363636;
                    border-color: #45a049;
                }
                QPushButton:disabled {
                    background-color: #2d2d2d;
                    color: #666666;
                    border-color: #444444;
                }
                QGroupBox {
                    background-color: #3c3c3c;
                    border: 2px solid #555555;
                    border-radius: 8px;
                    margin: 5px;
                    padding-top: 10px;
                    color: #ffffff;
                    font-weight: bold;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 8px 0 8px;
                    color: #ffffff;
                }
                QTabWidget::pane {
                    border: 1px solid #555555;
                    background-color: #3c3c3c;
                    border-radius: 5px;
                }
                QTabBar::tab {
                    background-color: #2b2b2b;
                    color: #cccccc;
                    padding: 8px 16px;
                    border: 1px solid #555555;
                    border-bottom: none;
                    border-radius: 5px 5px 0 0;
                    margin-right: 2px;
                }
                QTabBar::tab:selected {
                    background-color: #4CAF50;
                    color: white;
                }
                QTabBar::tab:hover {
                    background-color: #404040;
                }
                QTextEdit {
                    background-color: #2b2b2b;
                    color: #ffffff;
                    border: 1px solid #555555;
                    border-radius: 5px;
                    padding: 5px;
                }
                QStatusBar {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    border-top: 1px solid #555555;
                }
                QProgressBar {
                    border: 1px solid #555555;
                    border-radius: 5px;
                    background-color: #2b2b2b;
                    text-align: center;
                    color: white;
                }
                QProgressBar::chunk {
                    background-color: #4CAF50;
                    border-radius: 4px;
                }
                QComboBox, QSpinBox, QLineEdit {
                    background-color: #2b2b2b;
                    color: #ffffff;
                    border: 1px solid #555555;
                    border-radius: 4px;
                    padding: 4px;
                }
                QComboBox:hover, QSpinBox:hover, QLineEdit:hover {
                    border-color: #4CAF50;
                }
                QComboBox::drop-down {
                    background-color: #404040;
                    border: none;
                    border-left: 1px solid #555555;
                    border-radius: 0 4px 4px 0;
                }
                QComboBox::down-arrow {
                    image: none;
                    border: 2px solid #ffffff;
                    border-top: none;
                    border-left: 2px solid transparent;
                    border-right: 2px solid transparent;
                    width: 0;
                    height: 0;
                }
                QSlider::groove:horizontal {
                    background-color: #555555;
                    height: 6px;
                    border-radius: 3px;
                }
                QSlider::handle:horizontal {
                    background-color: #4CAF50;
                    border: 1px solid #45a049;
                    width: 16px;
                    border-radius: 8px;
                    margin: -5px 0;
                }
                QSlider::handle:horizontal:hover {
                    background-color: #45a049;
                }
                QCheckBox {
                    color: #ffffff;
                }
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                    border: 1px solid #555555;
                    border-radius: 3px;
                    background-color: #2b2b2b;
                }
                QCheckBox::indicator:checked {
                    background-color: #4CAF50;
                    border-color: #45a049;
                }
                QCheckBox::indicator:checked:hover {
                    background-color: #45a049;
                }
                QLabel {
                    color: #ffffff;
                    font-family: 'Roboto Mono';
                }
                QSplitter::handle {
                    background-color: #555555;
                    border: 1px solid #666666;
                    width: 4px;
                    height: 4px;
                    border-radius: 2px;
                }
                QSplitter::handle:hover {
                    background-color: #666666;
                }
                QSplitter::handle:pressed {
                    background-color: #777777;
                }
                QSplitter::handle {
                    background-color: #555555;
                    border: 1px solid #666666;
                    width: 4px;
                    height: 4px;
                    border-radius: 2px;
                }
                QSplitter::handle:hover {
                    background-color: #666666;
                }
                QSplitter::handle:pressed {
                    background-color: #777777;
                }
            """
        else:
            return """
                QMenuBar::item:selected {
                    background-color: #4CAF50;
                    font-family: 'Roboto Mono';
                    color: white;
                }
                QMenu::item:selected {
                    background-color: #4CAF50;
                }
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
                    border-color: #4CAF50;
                }
                QPushButton:pressed {
                    background-color: #d8d8d8;
                    border-color: #45a049;
                }
                QPushButton:disabled {
                    background-color: #f5f5f5;
                    color: #999999;
                    border-color: #dddddd;
                }
                QGroupBox {
                    border: 2px solid #cccccc;
                    border-radius: 8px;
                    margin: 5px;
                    padding-top: 10px;
                    font-weight: bold;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 8px 0 8px;
                }
                QTabWidget::pane {
                    border: 1px solid #cccccc;
                    background-color: white;
                    border-radius: 5px;
                }
                QTabBar::tab {
                    background-color: #f0f0f0;
                    padding: 8px 16px;
                    border: 1px solid #cccccc;
                    border-bottom: none;
                    border-radius: 5px 5px 0 0;
                    margin-right: 2px;
                }
                QTabBar::tab:selected {
                    background-color: #4CAF50;
                    color: white;
                }
                QTabBar::tab:hover {
                    background-color: #e0e0e0;
                }
                QProgressBar {
                    border: 1px solid #cccccc;
                    border-radius: 5px;
                    background-color: #f0f0f0;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #4CAF50;
                    border-radius: 4px;
                }
                QComboBox:hover, QSpinBox:hover, QLineEdit:hover {
                    border-color: #4CAF50;
                }
                QSlider::groove:horizontal {
                    background-color: #dddddd;
                    height: 6px;
                    border-radius: 3px;
                }
                QSlider::handle:horizontal {
                    background-color: #4CAF50;
                    border: 1px solid #45a049;
                    width: 16px;
                    border-radius: 8px;
                    margin: -5px 0;
                }
                QSlider::handle:horizontal:hover {
                    background-color: #45a049;
                }
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                    border: 1px solid #cccccc;
                    border-radius: 3px;
                    background-color: white;
                }
                QCheckBox::indicator:checked {
                    background-color: #4CAF50;
                    border-color: #45a049;
                }
                QCheckBox::indicator:checked:hover {
                    background-color: #45a049;
                }
                QSplitter::handle {
                    background-color: #cccccc;
                    border: 1px solid #aaaaaa;
                    width: 4px;
                    height: 4px;
                    border-radius: 2px;
                }
                QSplitter::handle:hover {
                    background-color: #bbbbbb;
                }
                QSplitter::handle:pressed {
                    background-color: #999999;
                }
            """
    
    def get_dialog_styles(self) -> str:
        """Generate dialog-specific styling based on current theme"""
        if self.current_theme == 'dark':
            return """
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555555;
                font-family: 'Roboto Mono';
            }
            QLabel {
                color: #ffffff;
                background-color: transparent;
                font-size: 11pt;
                font-family: 'Roboto Mono';
            }
            QCheckBox {
                color: #ffffff;
                background-color: transparent;
                spacing: 5px;
                font-family: 'Roboto Mono';
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                background-color: #404040;
                border: 1px solid #606060;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #0078d4;
                border: 1px solid #0078d4;
            }
            QDialogButtonBox {
                background-color: transparent;
            }
            QPushButton {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #606060;
                border-radius: 4px;
                padding: 6px 16px;
                font-size: 10pt;
                min-width: 80px;
                font-family: 'Roboto Mono';
            }
            QPushButton:hover {
                background-color: #4a4a4a;
                border: 1px solid #707070;
            }
            QPushButton:pressed {
                background-color: #353535;
            }
            """
        else:
            return """
            QDialog {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #cccccc;                font-family: 'Roboto Mono';            }
            QLabel {
                color: #000000;
                background-color: transparent;
                font-size: 11pt;
                font-family: 'Roboto Mono';
            }
            QCheckBox {
                color: #000000;
                background-color: transparent;
                spacing: 5px;
                font-family: 'Roboto Mono';
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #0078d4;
                border: 1px solid #0078d4;
            }
            """