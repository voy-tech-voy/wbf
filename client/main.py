#!/usr/bin/env python3
"""
Graphics Conversion App
A Qt-based application for converting graphics files using FFmpeg and ImageMagick
"""

import sys
import time
import os
import shutil
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QMessageBox, QDialog
from PyQt6.QtGui import QPixmap, QColor, QPainter
from PyQt6.QtCore import Qt, QRect
from client.gui.login_window_new import ModernLoginWindow
from client.gui.main_window import MainWindow
from client.utils.font_manager import AppFonts
from client.version import get_version, APP_NAME
from client.core.conversion_engine import init_bundled_tools

# Import crash reporting
try:
    from client.utils.crash_reporter import run_with_crash_protection
    from client.utils.error_reporter import get_error_reporter, log_info, log_error
    CRASH_REPORTING_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Crash reporting not available: {e}")
    CRASH_REPORTING_AVAILABLE = False

def set_dark_title_bar(window):
    """Set dark title bar for any window"""
    try:
        from ctypes import windll, byref, sizeof, c_int
        import winreg
        
        # Check if dark mode is enabled
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                           r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        apps_use_light_theme, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        
        if apps_use_light_theme == 0:  # Dark mode
            hwnd = int(window.winId())
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            value = c_int(1)
            windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_USE_IMMERSIVE_DARK_MODE,
                byref(value),
                sizeof(value)
            )
    except Exception as e:
        print(f"Could not set dark title bar: {e}")


class ToolLoadingWindow(QWidget):
    """Lightweight frameless splash shown while bundled tools initialize."""

    def __init__(self, version_text: str):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(600, 400)

        # Create a main label to hold the splash image/content
        self.content_label = QLabel(self)
        self.content_label.setFixedSize(600, 400)
        self.content_label.setStyleSheet(
            "background-color: #1e1e1e;"
            "border-radius: 15px;"
            "border: 2px solid #333333;"
        )
        self.content_label.setAlignment(Qt.AlignCenter)

        # Try to load splash image
        from client.utils.resource_path import get_resource_path
        
        splash_path = get_resource_path('client/assets/splash.png')
        if not os.path.exists(splash_path):
            splash_path = get_resource_path('client/assets/splash.jpg')
        
        if os.path.exists(splash_path):
            pix = QPixmap(splash_path)
            if not pix.isNull():
                self.content_label.setPixmap(pix.scaled(600, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            # Create placeholder splash
            pix = QPixmap(600, 400)
            pix.fill(QColor("#1e1e1e"))
            
            painter = QPainter(pix)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Draw App Icon
            from client.utils.resource_path import get_app_icon_path
            icon_path = get_app_icon_path()
            if os.path.exists(icon_path):
                icon_pix = QPixmap(icon_path)
                icon_size = 128
                icon_pix = icon_pix.scaled(icon_size, icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                painter.drawPixmap((600 - icon_size) // 2, 80, icon_pix)
            
            # Draw App Name
            painter.setPen(QColor("#ffffff"))
            font = painter.font()
            font.setFamily("Segoe UI")
            font.setPointSize(28)
            font.setBold(True)
            painter.setFont(font)
            
            text_rect = QRect(0, 230, 600, 50)
            painter.drawText(text_rect, Qt.AlignCenter, APP_NAME)
            
            # Draw Version
            font.setPointSize(12)
            font.setBold(False)
            painter.setFont(font)
            painter.setPen(QColor("#aaaaaa"))
            
            version_rect = QRect(0, 280, 600, 30)
            painter.drawText(version_rect, Qt.AlignCenter, f"Version {version_text}")
            
            # Draw Loading Status
            painter.setPen(QColor("#4CAF50"))
            status_rect = QRect(0, 340, 600, 30)
            painter.drawText(status_rect, Qt.AlignCenter, "Initializing Environment...")
            
            painter.end()
            self.content_label.setPixmap(pix)

def main():
    """Main application entry point with comprehensive error handling"""
    profile_startup = '--profile-startup' in sys.argv
    if profile_startup:
        # Remove the flag so Qt doesn't see it
        sys.argv = [arg for arg in sys.argv if arg != '--profile-startup']
    t0 = time.perf_counter()

    if CRASH_REPORTING_AVAILABLE:
        log_info("Starting ImgApp with crash protection", "startup")
    
    # Set AppUserModelID for Windows taskbar icon
    if os.name == 'nt':
        try:
            import ctypes
            myappid = 'imgapp.converter.v1'  # arbitrary string
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

    try:
        app = QApplication(sys.argv)
        
        if profile_startup:
            t_app = time.perf_counter()
            print(f"[startup] QApplication created in {(t_app - t0)*1000:.1f} ms")
        app.setApplicationName(APP_NAME)
        app.setApplicationVersion("1.0.0")
        
        # Set global application font - single point of control
        app.setFont(AppFonts.get_base_font())
        
        # Set application icon
        try:
            from PyQt6.QtGui import QIcon
            from client.utils.resource_path import get_app_icon_path
            
            icon_path = get_app_icon_path()
            if os.path.exists(icon_path):
                app.setWindowIcon(QIcon(icon_path))
                if CRASH_REPORTING_AVAILABLE:
                    log_info(f"Application icon loaded: {icon_path}", "startup")
            else:
                if CRASH_REPORTING_AVAILABLE:
                    log_error(f"Icon file not found: {icon_path}", "icon_loading")
        except Exception as e:
            error_msg = f"Could not set application icon: {e}"
            print(error_msg)
            if CRASH_REPORTING_AVAILABLE:
                log_error(e, "icon_loading")
        
        # Show login window first
        if CRASH_REPORTING_AVAILABLE:
            log_info("Initializing login window", "startup")
            
        login = ModernLoginWindow()
        if profile_startup:
            t_login = time.perf_counter()
            print(f"[startup] Login window instantiated in {(t_login - t0)*1000:.1f} ms (since start)")
        set_dark_title_bar(login)  # Apply dark title bar to login window
        # Show login window
        if login.exec() == QDialog.DialogCode.Accepted:
            # Login successful - show main application
            if CRASH_REPORTING_AVAILABLE:
                log_info("Login successful, launching main application", "startup")

            # Show a lightweight splash while bundled tools initialize
            version_text = get_version()
            splash = ToolLoadingWindow(version_text)
            splash.show()
            app.processEvents()
            
            # Record start time to ensure minimum display duration
            splash_start_time = time.time()
            
            try:
                init_bundled_tools()
                
                # Check for FFmpeg (Critical for Lite versions)
                if not os.environ.get('FFMPEG_BINARY'):
                    # Fallback to system FFmpeg
                    system_ffmpeg = shutil.which('ffmpeg')
                    if system_ffmpeg:
                        os.environ['FFMPEG_BINARY'] = system_ffmpeg
                        if CRASH_REPORTING_AVAILABLE:
                            log_info(f"Using system FFmpeg: {system_ffmpeg}", "startup")
                    else:
                        # No FFmpeg found
                        splash.close()
                        QMessageBox.critical(None, "FFmpeg Missing", 
                            "FFmpeg was not found.\n\n"
                            "This version requires FFmpeg to be installed and available in your system PATH.\n"
                            "Please install FFmpeg or use the Full version.")
                        sys.exit(1)
                
                # Ensure splash is displayed for at least 2 seconds
                elapsed = time.time() - splash_start_time
                if elapsed < 2.0:
                    time.sleep(2.0 - elapsed)
                        
            finally:
                splash.close()

            window = MainWindow(is_trial=login.is_trial)
            set_dark_title_bar(window)  # Apply dark title bar to main window
            window.show()
            
            if CRASH_REPORTING_AVAILABLE:
                log_info("Main application window displayed", "startup")
                
            sys.exit(app.exec())
        else:
            # Login cancelled or authentication failed - exit application
            if CRASH_REPORTING_AVAILABLE:
                log_info("Login cancelled or failed, exiting application", "startup")
            sys.exit(0)
            
    except Exception as e:
        error_msg = f"Critical error in main application: {e}"
        print(error_msg)
        
        if CRASH_REPORTING_AVAILABLE:
            log_error(e, "main_application")
            # Create diagnostic report for troubleshooting
            get_error_reporter().create_diagnostic_report()
        
        # Re-raise to let emergency reporter handle it
        raise

def main_with_protection():
    """Main entry point with emergency crash protection"""
    if CRASH_REPORTING_AVAILABLE:
        return run_with_crash_protection(main)
    else:
        return main()

if __name__ == "__main__":
    # Support a headless runtime verification entry used by CI and smoke-tests.
    if '--verify-bundled-tools' in sys.argv:
        # Run the runtime verifier and return JSON+exit code. This keeps the same
        # runtime code path as the packaged executable and helps CI validate
        # extraction + checksum logic after packaging.
        import json as _json
        try:
            from client.core.conversion_engine import verify_bundled_tools
            results = verify_bundled_tools(timeout=10)
            print(_json.dumps(results, indent=2))
            # Determine success: every tool that has a path and an expected_sha256 must match
            success = True
            for entry in results.values():
                p = entry.get('path')
                if p and os.path.exists(p):
                    # if an expected value was provided and mismatch, then fail
                    if entry.get('expected_sha256') is not None and not entry.get('checksum_match'):
                        success = False
                else:
                    # path missing is a failure
                    success = False

            sys.exit(0 if success else 2)
        except Exception as e:
            print(f"verify-bundled-tools failed: {e}")
            sys.exit(3)
    else:
        main_with_protection()
