"""
Tool Descriptor - Data model for external CLI tools
"""
from dataclasses import dataclass, field
from typing import Optional, Callable, List, Tuple


@dataclass
class ToolDescriptor:
    """Complete descriptor for an external CLI tool."""
    
    # Identity
    id: str                              # e.g., "ffmpeg"
    display_name: str                    # e.g., "FFmpeg"
    
    # Environment
    env_var_name: str                    # e.g., "FFMPEG_BINARY"
    binary_name: str                     # e.g., "ffmpeg.exe" on Windows
    
    # Version Detection
    version_args: List[str] = field(default_factory=lambda: ["-version"])
    version_pattern: str = r"version (\d+[\.\d]*)"
    min_version: Optional[str] = None
    
    # Advanced Validation (for tools like FFmpeg that need codec checks)
    # Callable signature: (path: str) -> (success: bool, error_msg: str, details: list)
    validate_capabilities: Optional[Callable[[str], Tuple[bool, str, List[str]]]] = None
    required_capabilities: List[str] = field(default_factory=list)
    
    # Companion Tools (auto-derived from same directory)
    companions: List[str] = field(default_factory=list)  # e.g., ["ffprobe"]
    
    # Bundling
    is_bundled: bool = False             # Whether we ship this tool
    bundle_subpath: str = "tools"        # Path within _MEIPASS
    
    # UI Configuration
    supports_system_mode: bool = True
    supports_custom_mode: bool = True
    file_filter: str = "Executable (*.exe);;All Files (*.*)"
