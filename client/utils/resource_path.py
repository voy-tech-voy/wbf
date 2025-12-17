"""
Resource Path Utilities
Helper functions to locate bundled resources in both development and PyInstaller builds
"""

import os
import sys


def get_resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller
    
    Args:
        relative_path: Path relative to the project root (e.g., 'client/assets/icons/app_icon.ico')
    
    Returns:
        Absolute path to the resource
    """
    if getattr(sys, 'frozen', False):
        # Running in a PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # Running in development
        # Go up from client/utils to project root
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    return os.path.join(base_path, relative_path)


def get_app_icon_path():
    """
    Get the path to the application icon
    
    Returns:
        Absolute path to app_icon.ico
    """
    return get_resource_path(os.path.join('client', 'assets', 'icons', 'app_icon.ico'))
