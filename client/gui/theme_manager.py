"""
Theme Manager for the Graphics Conversion App
Handles dark/light mode detection and styling

NOTE: This is a simplified version that delegates to the Theme class.
Most hardcoded styles have been removed in favor of Theme constants.
"""

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QPalette
from PyQt6.QtWidgets import QApplication
from client.gui.theme import Theme


class ThemeManager(QObject):
    """
    Manages application theming based on system preferences.
    
    This class now acts as a bridge between the Qt application and the
    centralized Theme class. Most styling is now done through Theme.
    """
    
    theme_changed = pyqtSignal(str)  # Emits 'dark' or 'light'
    
    def __init__(self):
        super().__init__()
        self.current_theme = 'dark'  # Default to dark mode
        Theme.set_dark_mode(True)
        
    def detect_system_theme(self) -> str:
        """Detect if system is using dark mode"""
        palette = QApplication.palette()
        window_color = palette.color(QPalette.ColorRole.Window)
        
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
            Theme.set_dark_mode(theme == 'dark')
            self.theme_changed.emit(theme)
    
    def get_drag_drop_styles(self) -> dict:
        """Get drag and drop area styles for current theme"""
        is_dark = self.current_theme == 'dark'
        Theme.set_dark_mode(is_dark)
        
        return {
            'normal': f"""
                QListWidget {{
                    border: 3px dashed {Theme.border()};
                    border-radius: {Theme.RADIUS_LG}px;
                    background-color: {Theme.surface()};
                    color: {Theme.text_muted()};
                    font-size: {Theme.FONT_SIZE_BASE}px;
                    padding: 10px;
                    font-family: '{Theme.FONT_MONO}';
                }}
                QListWidget:hover {{
                    border-color: {Theme.success()};
                    background-color: {Theme.color('surface_hover')};
                }}
                QListWidget::item {{
                    padding: 8px;
                    margin: 2px;
                    border: 1px solid {Theme.border()};
                    border-radius: 5px;
                    background-color: {Theme.surface_element()};
                    color: {Theme.text()};
                }}
                QListWidget::item:selected {{
                    background-color: {Theme.color('info')};
                    border-color: {Theme.color('info')};
                }}
                QListWidget::item:hover {{
                    background-color: {Theme.color('surface_hover')};
                }}
            """,
            'drag_over': f"""
                QListWidget {{
                    border: 3px dashed {Theme.success()};
                    border-radius: {Theme.RADIUS_LG}px;
                    background-color: {'#1a4a1a' if is_dark else '#e8f5e8'};
                    color: {Theme.success()};
                    font-size: {Theme.FONT_SIZE_BASE}px;
                    padding: 10px;
                    font-family: '{Theme.FONT_MONO}';
                }}
                QListWidget::item {{
                    padding: 8px;
                    margin: 2px;
                    border: 1px solid {Theme.border()};
                    border-radius: 5px;
                    background-color: {Theme.surface_element()};
                    color: {Theme.text()};
                }}
                QListWidget::item:selected {{
                    background-color: {Theme.color('info')};
                    border-color: {Theme.color('info')};
                }}
                QListWidget::item:hover {{
                    background-color: {Theme.color('surface_hover')};
                }}
            """
        }
    
    def get_main_window_style(self) -> str:
        """
        Get main window stylesheet for current theme.
        
        Uses Theme class for all colors, fonts, and metrics.
        """
        is_dark = self.current_theme == 'dark'
        Theme.set_dark_mode(is_dark)
        
        return f"""
            QMainWindow {{
                background-color: transparent;
                color: {Theme.text()};
                font-family: '{Theme.FONT_BODY}';
            }}
            QFrame#ContentFrame {{
                background-color: {Theme.surface()};
                border-radius: 0px 0px 5px 5px;
            }}
            QMenuBar {{
                background-color: {Theme.surface_element()};
                color: {Theme.text()};
                border-bottom: 1px solid {Theme.border()};
                font-family: '{Theme.FONT_BODY}';
                padding: 4px;
            }}
            QMenuBar::item {{
                background-color: transparent;
                padding: 4px 8px;
                border-radius: {Theme.RADIUS_SM}px;
            }}
            QMenuBar::item:selected {{
                background-color: {Theme.success()};
                color: white;
            }}
            QMenuBar::item:pressed {{
                background-color: {Theme.success()};
            }}
            QMenu {{
                background-color: {Theme.surface_element()};
                color: {Theme.text()};
                border: 1px solid {Theme.border()};
                border-radius: {Theme.RADIUS_SM}px;
                font-family: '{Theme.FONT_BODY}';
            }}
            QMenu::item {{
                padding: 6px 20px;
                border-radius: {Theme.RADIUS_SM}px;
                margin: 1px;
            }}
            QMenu::item:selected {{
                background-color: {Theme.success()};
            }}
            QToolBar {{
                background-color: {Theme.surface_element()};
                border: none;
                border-bottom: 1px solid {Theme.border()};
                spacing: 3px;
                padding: 4px;
            }}
            QToolBar::separator {{
                background-color: {Theme.border()};
                width: 1px;
                margin: 0 4px;
            }}
            QPushButton {{
                background-color: {Theme.surface_element()};
                color: {Theme.text()};
                border: 1px solid {Theme.border()};
                padding: 6px 12px;
                border-radius: {Theme.RADIUS_SM}px;
                font-family: '{Theme.FONT_BODY}';
                font-size: {Theme.FONT_SIZE_BASE - 1}px;
            }}
            QPushButton:hover {{
                background-color: {Theme.color('surface_hover')};
                border-color: {Theme.success()};
            }}
            QPushButton:pressed {{
                background-color: {Theme.color('surface_pressed')};
                border-color: {Theme.success()};
            }}
            QPushButton:disabled {{
                background-color: {Theme.bg()};
                color: {Theme.text_muted()};
                border-color: {Theme.border()};
            }}
            QGroupBox {{
                background-color: {Theme.surface_element()};
                border: none;
                border-radius: {Theme.RADIUS_MD}px;
                margin: 0px;
                padding: 0px;
                color: {Theme.text()};
                font-weight: bold;
            }}
            QGroupBox::title {{
                padding: 0px;
                margin: 0px;
            }}
            QTabWidget::pane {{
                border: 1px solid {Theme.border()};
                background-color: {Theme.surface_element()};
                border-radius: 5px;
            }}
            QTabBar::tab {{
                background-color: {Theme.surface()};
                color: {Theme.text_muted()};
                padding: 8px 16px;
                border: 1px solid {Theme.border()};
                border-bottom: none;
                border-radius: 5px 5px 0 0;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: {Theme.surface_element()};
                color: {Theme.text()};
                border-color: {Theme.success()};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {Theme.color('surface_hover')};
            }}
            QComboBox {{
                background-color: {Theme.surface_element()};
                color: {Theme.text()};
                border: 1px solid {Theme.border()};
                border-radius: {Theme.RADIUS_SM}px;
                padding: 5px 10px;
                font-family: '{Theme.FONT_BODY}';
                min-height: 20px;
            }}
            QComboBox:hover {{
                border-color: {Theme.success()};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {Theme.surface_element()};
                color: {Theme.text()};
                border: 1px solid {Theme.border()};
                selection-background-color: {Theme.success()};
            }}
            QSpinBox, QDoubleSpinBox {{
                background-color: {Theme.color('input_bg')};
                color: {Theme.text()};
                border: 1px solid {Theme.border()};
                border-radius: {Theme.RADIUS_SM}px;
                padding: 4px;
                font-family: '{Theme.FONT_BODY}';
            }}
            QSpinBox:hover, QDoubleSpinBox:hover {{
                border-color: {Theme.success()};
            }}
            QSpinBox:focus, QDoubleSpinBox:focus {{
                border-color: {Theme.accent()};
            }}
            QSpinBox::up-button, QDoubleSpinBox::up-button {{
                border: none;
                background-color: {Theme.surface_element()};
                width: 16px;
            }}
            QSpinBox::down-button, QDoubleSpinBox::down-button {{
                border: none;
                background-color: {Theme.surface_element()};
                width: 16px;
            }}
            QSlider::groove:horizontal {{
                background-color: {Theme.border()};
                height: 6px;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background-color: {Theme.success()};
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }}
            QSlider::handle:horizontal:hover {{
                background-color: {Theme.accent()};
            }}
            QProgressBar {{
                background-color: {Theme.surface_element()};
                color: {Theme.text()};
                border: 1px solid {Theme.border()};
                border-radius: {Theme.RADIUS_SM}px;
                text-align: center;
                font-family: '{Theme.FONT_BODY}';
            }}
            QProgressBar::chunk {{
                background-color: {Theme.success()};
                border-radius: {Theme.RADIUS_XS}px;
            }}
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: {Theme.color('scrollbar_bg')};
                width: 8px;
                border: none;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {Theme.color('scrollbar_thumb')};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {Theme.border_focus()};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
            QScrollBar:horizontal {{
                background: {Theme.color('scrollbar_bg')};
                height: 8px;
                border: none;
                border-radius: 4px;
            }}
            QScrollBar::handle:horizontal {{
                background: {Theme.color('scrollbar_thumb')};
                border-radius: 4px;
                min-width: 20px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {Theme.border_focus()};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: none;
            }}
            QCheckBox {{
                color: {Theme.text()};
                spacing: 5px;
                font-family: '{Theme.FONT_BODY}';
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                background-color: {Theme.surface_element()};
                border: 1px solid {Theme.border()};
                border-radius: 3px;
            }}
            QCheckBox::indicator:hover {{
                border-color: {Theme.success()};
            }}
            QCheckBox::indicator:checked {{
                background-color: {Theme.success()};
                border-color: {Theme.success()};
            }}
            QLabel {{
                color: {Theme.text()};
                font-family: '{Theme.FONT_BODY}';
            }}
            QSplitter::handle {{
                background-color: {Theme.border()};
                border: 1px solid {Theme.border_focus()};
                width: 4px;
                height: 4px;
                border-radius: 2px;
            }}
            QSplitter::handle:hover {{
                background-color: {Theme.border_focus()};
            }}
        """
    
    def get_dialog_styles(self) -> str:
        """Generate dialog-specific styling based on current theme"""
        is_dark = self.current_theme == 'dark'
        Theme.set_dark_mode(is_dark)
        
        return f"""
            QDialog {{
                background-color: {Theme.surface()};
                color: {Theme.text()};
                border: 1px solid {Theme.border()};
                font-family: '{Theme.FONT_BODY}';
            }}
            QLabel {{
                color: {Theme.text()};
                background-color: transparent;
                font-size: {Theme.FONT_SIZE_SM}pt;
                font-family: '{Theme.FONT_BODY}';
            }}
            QCheckBox {{
                color: {Theme.text()};
                background-color: transparent;
                spacing: 5px;
                font-family: '{Theme.FONT_BODY}';
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                background-color: {Theme.surface_element()};
                border: 1px solid {Theme.border()};
                border-radius: 3px;
            }}
            QCheckBox::indicator:checked {{
                background-color: {Theme.color('info')};
                border: 1px solid {Theme.color('info')};
            }}
            QDialogButtonBox {{
                background-color: transparent;
            }}
            QPushButton {{
                background-color: {Theme.surface_element()};
                color: {Theme.text()};
                border: 1px solid {Theme.border()};
                border-radius: {Theme.RADIUS_SM}px;
                padding: 6px 16px;
                font-size: 10pt;
                min-width: 80px;
                font-family: '{Theme.FONT_BODY}';
            }}
            QPushButton:hover {{
                background-color: {Theme.color('surface_hover')};
                border: 1px solid {Theme.border_focus()};
            }}
            QPushButton:pressed {{
                background-color: {Theme.color('surface_pressed')};
            }}
        """
