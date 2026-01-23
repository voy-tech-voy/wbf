"""
Presets Plugin - Orchestrator

Entry point that connects the logic layer with the UI layer.
Receives ToolRegistryProtocol via Dependency Injection.
"""
from typing import Optional, List, TYPE_CHECKING
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QObject, pyqtSignal

from client.plugins.presets.logic import PresetManager, CommandBuilder, PresetDefinition
from client.plugins.presets.ui import PresetGallery

if TYPE_CHECKING:
    from client.core.tool_registry.protocol import ToolRegistryProtocol


class PresetOrchestrator(QObject):
    """
    Controller connecting preset logic with UI.
    
    Responsible for:
    - Loading presets via PresetManager
    - Displaying gallery via PresetGallery
    - Building commands via CommandBuilder when preset is selected
    
    Signals:
        preset_selected: Emitted when user selects a preset (PresetDefinition)
        gallery_dismissed: Emitted when gallery is dismissed without selection
    """
    
    preset_selected = pyqtSignal(object)  # PresetDefinition
    gallery_dismissed = pyqtSignal()
    
    def __init__(self, registry: 'ToolRegistryProtocol', parent_widget: QWidget):
        """
        Initialize the orchestrator.
        
        Args:
            registry: Tool registry for validation and path resolution (injected)
            parent_widget: Widget to parent the gallery overlay to
        """
        super().__init__(parent_widget)
        
        self._registry = registry
        self._parent_widget = parent_widget
        
        # Initialize logic components
        self._manager = PresetManager(registry)
        self._builder = CommandBuilder(registry)
        
        # Initialize UI
        self._gallery = PresetGallery(parent_widget)
        self._gallery.preset_selected.connect(self._on_preset_selected)
        self._gallery.dismissed.connect(self._on_gallery_dismissed)
        
        # Load presets
        self._presets: List[PresetDefinition] = []
        self.reload_presets()
    
    def reload_presets(self):
        """Load/reload all presets from disk."""
        self._presets = self._manager.load_all()
        self._gallery.set_presets(self._presets)
        print(f"[PresetOrchestrator] Loaded {len(self._presets)} presets")
    
    def show_gallery(self):
        """Show the preset gallery overlay."""
        # Ensure gallery fills parent
        if self._parent_widget:
            self._gallery.setGeometry(0, 0, 
                self._parent_widget.width(), 
                self._parent_widget.height())
        self._gallery.show_animated()
    
    def hide_gallery(self):
        """Hide the preset gallery overlay."""
        self._gallery.hide_animated()
    
    def is_gallery_visible(self) -> bool:
        """Check if gallery is currently visible."""
        return self._gallery.isVisible()
    
    def _on_preset_selected(self, preset: PresetDefinition):
        """Handle preset selection from gallery."""
        print(f"[PresetOrchestrator] Preset selected: {preset.name}")
        self._gallery.hide_animated()
        self.preset_selected.emit(preset)
    
    def _on_gallery_dismissed(self):
        """Handle gallery dismissal."""
        self._gallery.hide_animated()
        self.gallery_dismissed.emit()
    
    def build_commands(self, preset: PresetDefinition, context: dict) -> List[str]:
        """
        Build executable commands for a preset.
        
        Args:
            preset: The selected preset
            context: Variables for template rendering (input_path, output_path, etc.)
            
        Returns:
            List of command strings
        """
        return self._builder.build_pipeline(preset, context)
    
    @property
    def presets(self) -> List[PresetDefinition]:
        """Get all loaded presets."""
        return self._presets
    
    @property
    def available_presets(self) -> List[PresetDefinition]:
        """Get only available presets (tools present)."""
        return [p for p in self._presets if p.is_available]
    
    @property
    def gallery(self) -> PresetGallery:
        """Get the gallery widget."""
        return self._gallery
