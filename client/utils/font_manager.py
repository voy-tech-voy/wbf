"""
Centralized Font Configuration for ImgApp
Single source of truth for all fonts used in the application
"""

from PyQt5.QtGui import QFont

# Global font settings - CHANGE THESE TO UPDATE FONTS EVERYWHERE
FONT_FAMILY = "Segoe UI"  # Windows-native sans-serif font
FONT_SIZE_BASE = 11  # Base font size for the application
FONT_SIZE_TITLE = 12  # Title bar fonts
FONT_SIZE_BUTTON = 16  # Button fonts

class AppFonts:
    """Centralized font definitions"""
    
    @staticmethod
    def get_base_font(bold=False):
        """Base application font (size 10)"""
        font = QFont(FONT_FAMILY, FONT_SIZE_BASE)
        if bold:
            font.setBold(True)
        font.setStyleStrategy(QFont.PreferAntialias)
        return font
    
    @staticmethod
    def get_title_font(bold=True):
        """Title bar font (size 11)"""
        font = QFont(FONT_FAMILY, FONT_SIZE_TITLE)
        if bold:
            font.setBold(True)
        font.setStyleStrategy(QFont.PreferAntialias)
        return font
    
    @staticmethod
    def get_button_font(bold=False):
        """Button font (size 12)"""
        font = QFont(FONT_FAMILY, FONT_SIZE_BUTTON)
        if bold:
            font.setBold(True)
        font.setStyleStrategy(QFont.PreferAntialias)
        return font
    
    @staticmethod
    def get_custom_font(size=10, bold=False):
        """Custom font with specified size"""
        font = QFont(FONT_FAMILY, size)
        if bold:
            font.setBold(True)
        font.setStyleStrategy(QFont.PreferAntialias)
        return font
