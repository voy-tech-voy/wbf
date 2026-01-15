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
from PyQt6.QtGui import QPixmap, QColor, QPainter, QFont
from PyQt6.QtCore import Qt, QRect, QTimer
from client.gui.login_window_new import ModernLoginWindow, VideoPlaybackThread
from client.gui.main_window import MainWindow
from client.utils.font_manager import AppFonts
from client.version import get_version, APP_NAME
from client.core.conversion_engine import init_bundled_tools

# Import MessageManager for centralized message handling
try:
    from client.utils.message_manager import get_message_manager
    from client.config.app_config import SERVER_BASE_URL
    MESSAGE_MANAGER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: MessageManager not available: {e}")
    MESSAGE_MANAGER_AVAILABLE = False

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
    """Super simple splash window - just displays splash_pic.jpg with version info"""

    def __init__(self, version_text: str):
        super().__init__()
        
        # Load splash image
        from client.utils.resource_path import get_resource_path
        img_path = get_resource_path('client/assets/images/splash_pic.jpg')
        
        if not os.path.exists(img_path):
            print(f"❌ Splash image not found: {img_path}")
            sys.exit(1)
        
        pixmap = QPixmap(img_path)
        if pixmap.isNull():
            print(f"❌ Failed to load splash image")
            sys.exit(1)
        
        print(f"📷 Pixmap loaded: {pixmap.width()}x{pixmap.height()}, isNull: {pixmap.isNull()}")
        
        # Scale to 50% size
        scale_factor = .8
        width = int(pixmap.width() * scale_factor)
        height = int(pixmap.height() * scale_factor)
        scaled_pixmap = pixmap.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.setFixedSize(width, height)
        
        # Frameless, always on top
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        
        # Center on screen
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - width) // 2,
            (screen.height() - height) // 2
        )
        
        # Create label to display the pixmap
        label = QLabel(self)
        label.setFixedSize(width, height)
        label.setPixmap(scaled_pixmap)
        label.setScaledContents(False)  # Don't scale, show at exact size
        
        # Add version text in bottom right corner
        version_label = QLabel(self)
        version_label.setText(f"{APP_NAME} v{version_text}")
        version_label.setStyleSheet(
            "color: #999999; font-size: 11px; font-weight: normal;"
        )
        version_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        
        # Position in bottom right corner with small padding
        padding = 8
        version_label.setGeometry(
            width - 150,
            height - 25,
            145,
            20
        )
        
        print(f"✅ Splash window created: {width}x{height}")


def main():
    """Main application entry point with comprehensive error handling"""
    profile_startup = '--profile-startup' in sys.argv
    if profile_startup:
        # Remove the flag so Qt doesn't see it
        sys.argv = [arg for arg in sys.argv if arg != '--profile-startup']
    t0 = time.perf_counter()

    if CRASH_REPORTING_AVAILABLE:
        log_info("Starting ImgApp with crash protection", "startup")
    
    # Check for dev mode - skip login window
    dev_mode = os.getenv('DEV_MODE', '0') == '1'
    
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
        
        # Initialize MessageManager early in the application lifecycle
        if MESSAGE_MANAGER_AVAILABLE:
            try:
                msg_manager = get_message_manager(SERVER_BASE_URL)
                # Attempt to fetch messages from server (non-blocking, will use cache/fallback on failure)
                msg_manager.fetch_from_server(timeout=3)
                if CRASH_REPORTING_AVAILABLE:
                    log_info("MessageManager initialized successfully", "startup")
            except Exception as e:
                print(f"Warning: Failed to initialize MessageManager: {e}")
                if CRASH_REPORTING_AVAILABLE:
                    log_error(e, "message_manager_init")
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
        
        # Show login window first (unless in dev mode)
        if CRASH_REPORTING_AVAILABLE:
            if dev_mode:
                log_info("Dev mode enabled - skipping login window", "startup")
            else:
                log_info("Initializing login window", "startup")
        
        # Skip login in dev mode
        if not dev_mode:
            login = ModernLoginWindow()
            if profile_startup:
                t_login = time.perf_counter()
                print(f"[startup] Login window instantiated in {(t_login - t0)*1000:.1f} ms (since start)")
            set_dark_title_bar(login)  # Apply dark title bar to login window
            # Show login window
            if login.exec() != QDialog.DialogCode.Accepted:
                # Login cancelled or authentication failed - exit application
                if CRASH_REPORTING_AVAILABLE:
                    log_info("Login cancelled or failed, exiting application", "startup")
                sys.exit(0)
            # Login successful
            is_trial = login.is_trial
        else:
            # Dev mode - skip login
            is_trial = False

        # Login successful (or dev mode) - show main application
        if CRASH_REPORTING_AVAILABLE:
            log_info("Launching main application", "startup")

        # Show a lightweight splash while bundled tools initialize
        version_text = get_version()
        splash = ToolLoadingWindow(version_text)
        splash.show()
        splash.raise_()
        splash.activateWindow()
        
        # Force the splash to render
        splash.update()
        splash.repaint()
        for _ in range(5):
            QApplication.processEvents()
        
        print(f"🪟 Splash visible: {splash.isVisible()}")
        
        # Record start time
        splash_start_time = time.time()
        
        # Initialize bundled tools with splash visible
        init_bundled_tools()
        QApplication.processEvents()  # Keep splash responsive
        
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
        
        # Create main window in background while splash is still visible
        print("🔨 Creating main window in background...")
        window = MainWindow(is_trial=is_trial)
        set_dark_title_bar(window)  # Apply dark title bar to main window
        QApplication.processEvents()  # Process events during window creation
        print("✅ Main window created")
        
        # Ensure splash displays for minimum 2 seconds (non-blocking wait)
        MIN_SPLASH_TIME = 2.0
        elapsed = time.time() - splash_start_time
        if elapsed < MIN_SPLASH_TIME:
            remaining_ms = int((MIN_SPLASH_TIME - elapsed) * 1000)
            print(f"⏳ Waiting {remaining_ms}ms more for splash (non-blocking)...")
            # Non-blocking wait - keeps UI responsive
            end_time = time.time() + (MIN_SPLASH_TIME - elapsed)
            while time.time() < end_time:
                QApplication.processEvents()
                time.sleep(0.016)  # ~60fps update rate
        
        # Close splash and show main window simultaneously
        splash.close()
        window.show()
        print("✅ Splash closed, main window displayed")
        
        if CRASH_REPORTING_AVAILABLE:
            log_info("Main application window displayed", "startup")
            
        sys.exit(app.exec())
            
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
