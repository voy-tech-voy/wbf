"""
Presets Plugin

A modular plugin for managing conversion presets.
Uses YAML-defined presets with ToolRegistry integration.
"""
from client.plugins.presets.orchestrator import PresetOrchestrator
from client.plugins.presets.logic import (
    PresetManager,
    CommandBuilder,
    PresetDefinition,
    PresetStatus
)
from client.plugins.presets.ui import PresetCard, PresetGallery

__all__ = [
    'PresetOrchestrator',
    'PresetManager',
    'CommandBuilder',
    'PresetDefinition',
    'PresetStatus',
    'PresetCard',
    'PresetGallery',
]
