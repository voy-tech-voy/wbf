"""
ImgApp Version Information
"""

APP_NAME = "webatchify"
AUTHOR = "Voy-tech"

__version__ = "1.1.0"
__author__ = AUTHOR
__email__ = "contact@imgapp.dev"
__description__ = f"{APP_NAME} - Professional graphics conversion with license system"
__license__ = "MIT"

# Version history
VERSION_HISTORY = {
    "1.0.0": {
        "release_date": "2025-11-18",
        "description": "Initial stable release",
        "features": [
            "Multi-format image/video conversion",
            "Batch processing with variants",
            "Dark theme interface",
            "Standalone executable packaging"

        ]
    },
    "1.1.0": {
        "release_date": "2025-11-18",
        "description": "Professional release with authentication system",
        "features": [
            "Hardware-bound license authentication system",
            "Development mode bypass for testing",
            "Complete rebrand to ImageWave Converter",
            "Custom branding and icons",
            "Improved UI with dark splitter styling",
            "Increased window height for better UX",
            "Flask API server for license management",
            "Offline license validation support",
            "Windows dark mode detection",
            "Professional login interface"
        ]
    }
}

def get_version():
    """Return current version string"""
    return __version__

def get_version_info():
    """Return detailed version information"""
    return {
        "version": __version__,
        "author": __author__,
        "description": __description__,
        "license": __license__
    }