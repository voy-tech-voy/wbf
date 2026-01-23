"""
Presets Plugin - Orchestrator

Entry point that connects the logic layer with the UI layer.
Receives ToolRegistryProtocol via Dependency Injection.
"""
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QObject, pyqtSignal

from client.plugins.presets.logic import PresetManager, CommandBuilder, PresetDefinition, MediaAnalyzer
from client.plugins.presets.ui import PresetGallery, ParameterForm

if TYPE_CHECKING:
    from client.core.tool_registry.protocol import ToolRegistryProtocol


class PresetOrchestrator(QObject):
    """
    Controller connecting preset logic with UI.
    
    Responsible for:
    - Loading presets via PresetManager
    - Displaying gallery via PresetGallery
    - Building commands via CommandBuilder when preset is selected
    - Analyzing media via MediaAnalyzer for smart presets
    
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
        self._analyzer = MediaAnalyzer(registry)
        
        # Initialize UI
        self._gallery = PresetGallery(parent_widget)
        self._gallery.preset_selected.connect(self._on_preset_selected)
        self._gallery.dismissed.connect(self._on_gallery_dismissed)
        
        # Parameter form (created lazily per preset)
        self._parameter_form: Optional[ParameterForm] = None
        self._selected_preset: Optional[PresetDefinition] = None
        
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
        """Handle preset selection from gallery - gallery stays open to show parameters."""
        print(f"[PresetOrchestrator] Preset selected: {preset.name}")
        self._selected_preset = preset  # Track selected preset
        # Gallery stays open - user can adjust parameters
        # Gallery closes only on: background click, presets button, or lab button
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
    
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze a media file and return metadata.
        
        Args:
            file_path: Path to media file
            
        Returns:
            Dict with meta fields (fps, is_landscape, etc.)
        """
        return self._analyzer.analyze(file_path)
    
    def setup_parameter_form(self, preset: PresetDefinition, meta: Dict[str, Any] = None):
        """
        Setup or update the parameter form for a preset.
        
        Args:
            preset: The selected preset
            meta: Media metadata for visibility rules
        """
        self._selected_preset = preset
        
        if self._parameter_form is None:
            self._parameter_form = ParameterForm()
        
        self._parameter_form.set_parameters(preset.parameters, meta or {})
    
    def get_parameter_values(self) -> Dict[str, Any]:
        """
        Get current parameter values from the form.
        
        Returns:
            Dict of parameter id -> value
        """
        if self._parameter_form:
            return self._parameter_form.get_values()
        
        # Fall back to defaults if no form
        if self._selected_preset:
            return {p.id: p.default for p in self._selected_preset.parameters}
        
        return {}
    
    @property
    def selected_preset(self) -> Optional[PresetDefinition]:
        """Get the currently selected preset."""
        return self._selected_preset
    
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
    
    @property
    def analyzer(self) -> MediaAnalyzer:
        """Get the media analyzer."""
        return self._analyzer
    
    @property
    def parameter_form(self) -> Optional[ParameterForm]:
        """Get the parameter form widget."""
        return self._parameter_form
