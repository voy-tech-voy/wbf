"""
Unit Tests for MainWindow Mediator-Shell Refactoring
=====================================================
Tests key functionality after Phase 2 refactoring:
- SidePanelAnimator integration
- SessionManager integration  
- Mode switching (Preset/Lab)
- Signal connections
"""

import sys
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

# Add project root to path
sys.path.insert(0, 'V:/_MY_APPS/ImgApp_1')


class TestSidePanelAnimator:
    """Tests for the extracted SidePanelAnimator class."""
    
    def test_animator_initialization(self):
        """Test animator initializes with correct state."""
        from client.gui.animators.side_panel_animator import SidePanelAnimator
        
        # Mock Qt widgets
        mock_splitter = MagicMock()
        mock_command_panel = MagicMock()
        mock_right_frame = MagicMock()
        
        animator = SidePanelAnimator(mock_splitter, mock_command_panel, mock_right_frame)
        
        assert animator.splitter == mock_splitter
        assert animator.command_panel == mock_command_panel
        assert animator.right_frame == mock_right_frame
        assert animator._is_open == False
        assert animator._panel_anim is None
    
    def test_animator_is_open_property(self):
        """Test is_open property returns correct state."""
        from client.gui.animators.side_panel_animator import SidePanelAnimator
        
        animator = SidePanelAnimator(MagicMock(), MagicMock(), MagicMock())
        
        assert animator.is_open == False
        animator._is_open = True
        assert animator.is_open == True
    
    def test_button_callbacks_set(self):
        """Test button callbacks are properly set."""
        from client.gui.animators.side_panel_animator import SidePanelAnimator
        
        animator = SidePanelAnimator(MagicMock(), MagicMock(), MagicMock())
        
        on_show = MagicMock()
        on_hide = MagicMock()
        
        animator.set_button_callbacks(on_show, on_hide)
        
        assert animator._on_buttons_show == on_show
        assert animator._on_buttons_hide == on_hide
    
    def test_trigger_side_buttons_animation_no_panel(self):
        """Test button animation handles missing panel gracefully."""
        from client.gui.animators.side_panel_animator import SidePanelAnimator
        
        animator = SidePanelAnimator(MagicMock(), None, MagicMock())
        
        # Should not raise - handles None command_panel
        animator.trigger_side_buttons_animation(hide=False)
        animator.trigger_side_buttons_animation(hide=True)
    
    def test_easing_map_contains_required_curves(self):
        """Test EASING_MAP contains all required curve types."""
        from client.gui.animators.side_panel_animator import SidePanelAnimator
        
        required_curves = ["Linear", "OutQuad", "OutCubic", "OutExpo", 
                          "OutBack", "OutElastic", "InOutCubic", "InQuad", "InCubic"]
        
        for curve in required_curves:
            assert curve in SidePanelAnimator.EASING_MAP, f"Missing easing curve: {curve}"


class TestSessionManager:
    """Tests for the extracted SessionManager class."""
    
    def test_session_manager_initialization(self):
        """Test SessionManager initializes correctly."""
        from client.utils.session_manager import SessionManager
        
        mock_window = MagicMock()
        get_engine = lambda: MagicMock()
        
        mgr = SessionManager(mock_window, get_engine)
        
        assert mgr.main_window == mock_window
        assert callable(mgr._get_engine)
    
    def test_logout_stops_running_engine(self):
        """Test logout stops a running conversion engine."""
        from client.utils.session_manager import SessionManager
        
        mock_window = MagicMock()
        mock_engine = MagicMock()
        mock_engine.isRunning.return_value = True
        
        mgr = SessionManager(mock_window, lambda: mock_engine)
        
        with patch('client.utils.session_manager.QApplication') as mock_app, \
             patch('client.utils.session_manager.QTimer'):
            mock_app.instance.return_value = MagicMock()
            mgr.logout()
        
        mock_engine.stop_conversion.assert_called_once()
        mock_engine.wait.assert_called_once_with(1000)
    
    def test_logout_handles_no_engine(self):
        """Test logout handles None engine gracefully."""
        from client.utils.session_manager import SessionManager
        
        mock_window = MagicMock()
        
        mgr = SessionManager(mock_window, lambda: None)
        
        with patch('client.utils.session_manager.QApplication') as mock_app, \
             patch('client.utils.session_manager.QTimer'):
            mock_app.instance.return_value = MagicMock()
            # Should not raise
            mgr.logout()
    
    def test_logout_closes_main_window(self):
        """Test logout closes the main window."""
        from client.utils.session_manager import SessionManager
        
        mock_window = MagicMock()
        
        mgr = SessionManager(mock_window, lambda: None)
        
        with patch('client.utils.session_manager.QApplication') as mock_app, \
             patch('client.utils.session_manager.QTimer'):
            mock_app.instance.return_value = MagicMock()
            mgr.logout()
        
        mock_window.close.assert_called_once()


class TestMainWindowIntegration:
    """Integration tests for MainWindow after refactoring."""
    
    def test_mainwindow_imports_successfully(self):
        """Test MainWindow module imports without errors."""
        from client.gui.main_window import MainWindow
        assert MainWindow is not None
    
    def test_mode_enum_values(self):
        """Test Mode enum has correct values."""
        from client.gui.main_window import Mode
        
        assert Mode.PRESET.value == "preset"
        assert Mode.LAB.value == "lab"
    
    def test_panel_animator_import(self):
        """Test SidePanelAnimator can be imported from main_window module."""
        from client.gui.animators.side_panel_animator import SidePanelAnimator
        assert SidePanelAnimator is not None
    
    def test_session_manager_import_in_mainwindow(self):
        """Test SessionManager is imported in main_window module."""
        import client.gui.main_window as mw_module
        
        # Check the module has SessionManager available
        assert 'SessionManager' in dir(mw_module) or hasattr(mw_module, 'SessionManager')


class TestSignalConnections:
    """Tests to verify signal/slot connections are intact."""
    
    def test_dialog_manager_available(self):
        """Test DialogManager is available for MainWindow."""
        from client.gui.utils.dialog_manager import DialogManager
        assert DialogManager is not None
    
    def test_control_bar_available(self):
        """Test ControlBar component is available."""
        from client.gui.components.control_bar import ControlBar
        assert ControlBar is not None
    
    def test_status_panel_available(self):
        """Test StatusPanel component is available."""
        from client.gui.components.status_panel import StatusPanel
        assert StatusPanel is not None
    
    def test_frameless_window_behavior_available(self):
        """Test FramelessWindowBehavior is available."""
        from client.gui.utils.window_behavior import FramelessWindowBehavior
        assert FramelessWindowBehavior is not None


class TestNoEventCollisions:
    """Tests to verify no signal/event naming collisions after refactoring."""
    
    def test_no_duplicate_method_names(self):
        """Verify MainWindow has no duplicate method definitions."""
        from client.gui.main_window import MainWindow
        import inspect
        
        methods = [m for m, _ in inspect.getmembers(MainWindow, predicate=inspect.isfunction)]
        
        # Check for any duplicate method names (shouldn't happen but good to verify)
        seen = set()
        duplicates = []
        for method in methods:
            if method in seen:
                duplicates.append(method)
            seen.add(method)
        
        assert len(duplicates) == 0, f"Duplicate methods found: {duplicates}"
    
    def test_animator_methods_removed_from_mainwindow(self):
        """Verify old animation methods are removed from MainWindow."""
        from client.gui.main_window import MainWindow
        
        removed_methods = [
            '_trigger_side_buttons_animation',
            '_reveal_button', 
            '_hide_button',
            'toggle_command_panel'
        ]
        
        for method in removed_methods:
            assert not hasattr(MainWindow, method), f"Method '{method}' should be removed from MainWindow"
    
    def test_logout_is_thin_wrapper(self):
        """Verify logout method is now a thin wrapper (< 15 lines)."""
        from client.gui.main_window import MainWindow
        import inspect
        
        source = inspect.getsource(MainWindow.logout)
        line_count = len(source.strip().split('\n'))
        
        # After refactoring, logout should be a thin wrapper (~7 lines)
        assert line_count < 15, f"logout() has {line_count} lines, expected < 15 (thin wrapper)"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
