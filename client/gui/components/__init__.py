"""
GUI Components Package - UI Components

Part of the Mediator-Shell Architecture.
"""

from client.gui.components.control_bar import ControlBar
from client.gui.components.status_panel import StatusPanel, CustomProgressBar
from client.gui.components.about_dialog import show_about_dialog

__all__ = ['ControlBar', 'StatusPanel', 'CustomProgressBar', 'show_about_dialog']
