"""
Custom widgets package for the application.

This package contains extracted complex widgets from custom_widgets.py
for better organization and maintainability.
"""

# Import extracted widgets for backward compatibility
from .file_list_item import FileListItemWidget

__all__ = [
    'FileListItemWidget',
]

