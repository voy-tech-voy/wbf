"""
Presets Plugin - Logic Module

Exports core classes for preset management and command building.
"""
from .models import (
    PresetDefinition,
    PresetStatus,
    PipelineStep,
    PresetStyle,
    PresetConstraints,
    ParameterDefinition,
    ParameterType
)
from .manager import PresetManager
from .builder import CommandBuilder
from .exceptions import (
    PresetError,
    PresetLoadError,
    PresetValidationError,
    ToolNotAvailableError,
    CommandBuildError
)

__all__ = [
    # Models
    'PresetDefinition',
    'PresetStatus',
    'PipelineStep',
    'PresetStyle',
    'PresetConstraints',
    'ParameterDefinition',
    'ParameterType',
    # Core classes
    'PresetManager',
    'CommandBuilder',
    # Exceptions
    'PresetError',
    'PresetLoadError',
    'PresetValidationError',
    'ToolNotAvailableError',
    'CommandBuildError',
]
