---
description: Tool Registry architecture for external CLI tools (FFmpeg, ImageMagick)
---

# Tool Registry System

## Quick Reference

The app uses a centralized `ToolRegistry` to manage external CLI tools. Plugins receive the registry via dependency injection.

## Key Files

| File | Purpose |
|------|---------|
| `client/core/tool_registry/descriptor.py` | `ToolDescriptor` dataclass |
| `client/core/tool_registry/protocol.py` | `ToolRegistryProtocol` interface for plugins |
| `client/core/tool_registry/registry.py` | Main `ToolRegistry` implementation |
| `client/core/tool_registry/validators.py` | Tool-specific validation (FFmpeg codecs) |
| `client/core/tool_registry/bundled.py` | PyInstaller extraction logic |

## Adding a New Tool

1. Register in `client/core/tool_registry/__init__.py`:
```python
registry.register(ToolDescriptor(
    id="newtool",
    display_name="New Tool",
    env_var_name="NEWTOOL_BINARY",
    binary_name="newtool.exe",
))
```

2. The Advanced Settings UI auto-generates configuration section.

## Plugin Integration

Plugins must:
- Accept `ToolRegistryProtocol` in constructor
- Use `registry.get_tool_path(tool_id)` to get paths
- Use `registry.is_tool_available(tool_id)` to check availability
- Never import concrete registry, only the Protocol

## Environment Variables

Tools are exposed via `os.environ['{TOOL}_BINARY']` for subprocess calls.
