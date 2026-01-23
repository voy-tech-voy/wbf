# Tool Registry Architecture

## Overview

The Tool Registry is a centralized system for managing external CLI tools (FFmpeg, ImageMagick, etc.). It handles:

- **Path Resolution**: Bundled vs System vs Custom paths
- **Validation**: Version checks and capability validation (e.g., FFmpeg codecs)
- **Persistence**: User preferences saved to JSON
- **Plugin Support**: Dependency injection for preset plugins

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Main Application                        │
│  ┌─────────────────┐    ┌─────────────────┐                 │
│  │  Advanced       │───▶│  ToolRegistry   │◀──┐             │
│  │  Settings UI    │    │                 │   │             │
│  └─────────────────┘    └────────┬────────┘   │             │
│                                  │            │ DI          │
│                                  ▼            │             │
│                         ┌────────────────┐    │             │
│                         │ ToolSettings   │    │             │
│                         │ (JSON storage) │    │             │
│                         └────────────────┘    │             │
└───────────────────────────────────────────────┼─────────────┘
                                                │
┌───────────────────────────────────────────────┼─────────────┐
│                     Preset Plugin             │             │
│  ┌─────────────────┐                          │             │
│  │ PresetProcessor │◀─────────────────────────┘             │
│  │                 │  receives ToolRegistryProtocol         │
│  └─────────────────┘                                        │
└─────────────────────────────────────────────────────────────┘
```

## ToolDescriptor

Each tool is defined by a descriptor:

```python
@dataclass
class ToolDescriptor:
    id: str                    # "ffmpeg"
    display_name: str          # "FFmpeg"
    env_var_name: str          # "FFMPEG_BINARY"
    binary_name: str           # "ffmpeg.exe"
    version_args: List[str]    # ["-version"]
    version_pattern: str       # r"version (\d+\.\d+)"
    validate_capabilities: Optional[Callable]  # FFmpeg codec check
    companions: List[str]      # ["ffprobe"]
    is_bundled: bool           # True if we ship it
```

## Plugin Integration

Plugins depend on `ToolRegistryProtocol`, not the concrete registry:

```python
class ToolRegistryProtocol(Protocol):
    def get_tool_path(self, tool_id: str) -> Optional[str]: ...
    def is_tool_available(self, tool_id: str) -> bool: ...
    def get_tool_version(self, tool_id: str) -> Optional[str]: ...
```

This makes plugins agnostic to bundling logic (PyInstaller, etc.).

## Adding a New Tool

1. Create a `ToolDescriptor` entry in `tool_registry/__init__.py`
2. (Optional) Add validation function in `validators.py`
3. The Advanced Settings UI auto-generates the configuration section

## File Structure

```
client/core/tool_registry/
├── __init__.py      # Singleton registry, tool registration
├── descriptor.py    # ToolDescriptor dataclass
├── protocol.py      # ToolRegistryProtocol interface
├── registry.py      # ToolRegistry implementation
├── validators.py    # Tool-specific validation
└── bundled.py       # PyInstaller extraction
```

## Settings Storage

User preferences are saved to:
```
%LOCALAPPDATA%/<AppName>/<tool_id>_settings.json
```

Example `ffmpeg_settings.json`:
```json
{
  "mode": "custom",
  "custom_path": "C:\\Tools\\ffmpeg.exe"
}
```
