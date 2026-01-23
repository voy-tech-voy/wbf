"""
Tool Registry Protocol - Interface for plugins to depend on
"""
from typing import Protocol, Optional, List, runtime_checkable


@runtime_checkable
class ToolRegistryProtocol(Protocol):
    """
    Interface that plugins depend on.
    
    Plugins should import this Protocol, not the concrete ToolRegistry.
    This ensures plugins are agnostic to bundling logic (PyInstaller, etc.).
    """
    
    def get_tool_path(self, tool_id: str) -> Optional[str]:
        """
        Get resolved path to tool executable.
        
        Args:
            tool_id: Tool identifier (e.g., "ffmpeg")
            
        Returns:
            Absolute path to executable, or None if unavailable
        """
        ...
    
    def is_tool_available(self, tool_id: str) -> bool:
        """
        Check if tool is configured and valid.
        
        Args:
            tool_id: Tool identifier
            
        Returns:
            True if tool is available and validated
        """
        ...
    
    def get_tool_version(self, tool_id: str) -> Optional[str]:
        """
        Get detected version string.
        
        Args:
            tool_id: Tool identifier
            
        Returns:
            Version string (e.g., "7.1"), or None if unknown
        """
        ...
    
    def list_available_tools(self) -> List[str]:
        """
        List all tool IDs that are currently available.
        
        Returns:
            List of tool IDs that passed validation
        """
        ...
    
    def list_registered_tools(self) -> List[str]:
        """
        List all registered tool IDs (available or not).
        
        Returns:
            List of all registered tool IDs
        """
        ...
