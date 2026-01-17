"""
FFmpeg Settings Manager
Handles persistent storage and validation of FFmpeg configuration
"""

import os
import sys
import json
import subprocess
from pathlib import Path


class FFmpegSettings:
    """Manage FFmpeg settings with persistent storage"""
    
    def __init__(self):
        self.settings_file = self._get_settings_path()
        self.settings = self._load_settings()
        
    def _get_settings_path(self):
        """Get the path to the settings file"""
        if os.name == 'nt':
            app_data = os.getenv('LOCALAPPDATA') or os.getenv('APPDATA') or os.path.expanduser('~')
        else:
            app_data = os.getenv('XDG_CONFIG_HOME') or os.path.expanduser('~/.config')
        
        from client.version import APP_NAME
        settings_dir = os.path.join(app_data, APP_NAME)
        os.makedirs(settings_dir, exist_ok=True)
        
        return os.path.join(settings_dir, 'ffmpeg_settings.json')
    
    def _load_settings(self):
        """Load settings from file"""
        default_settings = {
            'mode': 'bundled',  # 'bundled', 'custom', 'system'
            'custom_path': '',
            'last_validated': None
        }
        
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # Merge with defaults to handle new keys
                    default_settings.update(loaded)
            except Exception as e:
                print(f"Error loading FFmpeg settings: {e}")
        
        return default_settings
    
    def _save_settings(self):
        """Save settings to file"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving FFmpeg settings: {e}")
    
    def get_mode(self):
        """Get current FFmpeg mode"""
        return self.settings.get('mode', 'bundled')
    
    def get_custom_path(self):
        """Get custom FFmpeg path"""
        return self.settings.get('custom_path', '')
    
    def set_mode(self, mode):
        """Set FFmpeg mode ('bundled', 'custom', 'system')"""
        if mode in ['bundled', 'custom', 'system']:
            self.settings['mode'] = mode
            self._save_settings()
    
    def set_custom_path(self, path):
        """Set custom FFmpeg path"""
        self.settings['custom_path'] = path
        self._save_settings()
    
    def validate_ffmpeg(self, ffmpeg_path):
        """Validate if the file is a valid ffmpeg executable"""
        if not ffmpeg_path:
            return False
            
        if not os.path.exists(ffmpeg_path):
            return False
            
        if not os.path.isfile(ffmpeg_path):
            return False
            
        # Check if filename contains 'ffmpeg'
        filename = os.path.basename(ffmpeg_path).lower()
        if 'ffmpeg' not in filename:
            return False
            
        # Try to run ffmpeg -version
        try:
            result = subprocess.run(
                [ffmpeg_path, '-version'],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # Check if output contains 'ffmpeg version'
            if result.returncode == 0 and 'ffmpeg version' in result.stdout.lower():
                return True
        except Exception as e:
            print(f"FFmpeg validation error: {e}")
            
        return False
    
    def get_bundled_ffmpeg_path(self):
        """Get the bundled FFmpeg path"""
        from client.core.conversion_engine import bundled_tools_dir, _USER_BIN_CACHE
        
        # For frozen builds
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            ffmpeg_path = os.path.join(sys._MEIPASS, 'tools', 'ffmpeg.exe')
            if not os.path.exists(ffmpeg_path) and _USER_BIN_CACHE:
                ffmpeg_path = os.path.join(_USER_BIN_CACHE, 'ffmpeg.exe')
        else:
            # Development mode
            ffmpeg_path = os.path.join(bundled_tools_dir, 'ffmpeg.exe')
        
        return ffmpeg_path if os.path.exists(ffmpeg_path) else ''
    
    def apply_settings(self):
        """Apply current settings to environment variables"""
        from client.core.conversion_engine_validation import validate_and_apply_ffmpeg
        
        mode = self.get_mode()
        custom_path = self.get_custom_path() if mode == 'custom' else ''
        
        # Use the validation module to apply settings
        success, error_msg, applied_path = validate_and_apply_ffmpeg(mode, custom_path)
        
        if not success:
            # Fallback to bundled if validation fails
            print(f"Warning: FFmpeg validation failed ({error_msg}), falling back to bundled")
            self.set_mode('bundled')
            success, error_msg, applied_path = validate_and_apply_ffmpeg('bundled', '')
            
            if not success:
                print(f"Error: Even bundled FFmpeg failed: {error_msg}")
    
    def validate_on_startup(self):
        """Validate FFmpeg configuration on app startup"""
        mode = self.get_mode()
        
        if mode == 'bundled':
            bundled_path = self.get_bundled_ffmpeg_path()
            if not bundled_path or not self.validate_ffmpeg(bundled_path):
                print("Warning: Bundled FFmpeg not found or invalid")
                return False
            return True
            
        elif mode == 'custom':
            custom_path = self.get_custom_path()
            if not custom_path or not self.validate_ffmpeg(custom_path):
                print(f"Warning: Custom FFmpeg path invalid: {custom_path}")
                # Fallback to bundled
                self.set_mode('bundled')
                return self.validate_on_startup()
            return True
            
        elif mode == 'system':
            try:
                result = subprocess.run(
                    ['ffmpeg', '-version'],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                
                if result.returncode == 0 and 'ffmpeg version' in result.stdout.lower():
                    return True
                else:
                    print("Warning: System FFmpeg invalid")
                    # Fallback to bundled
                    self.set_mode('bundled')
                    return self.validate_on_startup()
            except Exception as e:
                print(f"Warning: System FFmpeg not available: {e}")
                # Fallback to bundled
                self.set_mode('bundled')
                return self.validate_on_startup()
        
        return False


# Global instance
_ffmpeg_settings = None

def get_ffmpeg_settings():
    """Get the global FFmpeg settings instance"""
    global _ffmpeg_settings
    if _ffmpeg_settings is None:
        _ffmpeg_settings = FFmpegSettings()
    return _ffmpeg_settings
