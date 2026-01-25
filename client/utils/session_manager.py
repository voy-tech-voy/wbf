"""
Session Manager - Handles application session lifecycle.

Extracted from MainWindow to follow the Mediator-Shell pattern.
Handles logout, login window display, and app restart logic.
"""

from PyQt6.QtWidgets import QApplication, QDialog
from PyQt6.QtCore import QTimer


class SessionManager:
    """
    Manages application session lifecycle including logout and re-login.
    
    This class handles:
    - Graceful shutdown of running conversions
    - Displaying login window after logout
    - Creating new main window on successful login
    - Complete app exit on login cancel
    
    Usage:
        session_mgr = SessionManager(main_window, conversion_engine)
        session_mgr.logout()  # Handles entire logout flow
    """
    
    def __init__(self, main_window, get_conversion_engine):
        """
        Initialize session manager.
        
        Args:
            main_window: The MainWindow instance
            get_conversion_engine: Callable that returns current conversion engine
        """
        self.main_window = main_window
        self._get_engine = get_conversion_engine
    
    def logout(self):
        """
        Execute the complete logout flow.
        
        1. Stops any running conversion
        2. Closes the main window
        3. Shows login window after close
        4. Creates new main window on successful login
        5. Quits app if login cancelled
        """
        # Stop any running conversions
        engine = self._get_engine()
        if engine and engine.isRunning():
            engine.stop_conversion()
            engine.wait(1000)  # Wait up to 1 second
        
        # Get the QApplication instance
        app = QApplication.instance()
        
        # Prevent app from quitting when main window closes
        app.setQuitOnLastWindowClosed(False)
        
        # Close main window
        self.main_window.close()
        
        # Use QTimer to show login window after event loop processes the close
        QTimer.singleShot(100, lambda: self._show_login_window(app))
    
    def _show_login_window(self, app):
        """Show login window after main window closes."""
        try:
            from client.gui.login_window_new import ModernLoginWindow
            login_window = ModernLoginWindow()
            
            # Store reference to prevent garbage collection
            app._login_window = login_window
            
            # Show login window modally
            result = login_window.exec()
            
            if result == QDialog.DialogCode.Accepted:
                # Login successful - create new main window
                is_trial = getattr(login_window, 'is_trial', False)
                
                # Use centralized initialization to ensure splash screen and tool checks run
                from client.main import initialize_main_window
                new_main_window = initialize_main_window(is_trial=is_trial)
                new_main_window.show()
                
                # Store reference to prevent garbage collection
                app._main_window = new_main_window
                
                # Re-enable quit on last window closed
                app.setQuitOnLastWindowClosed(True)
            else:
                # Login cancelled - exit application
                app.quit()
                
        except Exception as e:
            print(f"Error showing login window: {e}")
            import traceback
            traceback.print_exc()
            # If login window fails, exit application
            app.quit()
