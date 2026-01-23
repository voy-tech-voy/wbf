"""
Presets Plugin - Custom Exceptions
"""


class PresetError(Exception):
    """Base exception for preset-related errors"""
    pass


class PresetLoadError(PresetError):
    """Error loading or parsing a preset YAML file"""
    def __init__(self, preset_path: str, message: str):
        self.preset_path = preset_path
        super().__init__(f"Failed to load preset '{preset_path}': {message}")


class PresetValidationError(PresetError):
    """Error validating preset schema or requirements"""
    def __init__(self, preset_id: str, message: str):
        self.preset_id = preset_id
        super().__init__(f"Validation failed for preset '{preset_id}': {message}")


class ToolNotAvailableError(PresetError):
    """Required tool not found in registry"""
    def __init__(self, tool_id: str):
        self.tool_id = tool_id
        super().__init__(f"Tool '{tool_id}' not available in registry")


class CommandBuildError(PresetError):
    """Error rendering command template"""
    def __init__(self, step_description: str, message: str):
        self.step_description = step_description
        super().__init__(f"Failed to build command for '{step_description}': {message}")
