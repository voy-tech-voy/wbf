"""
ThemeCoordinator - Centralized theme management.

Part of the Mediator-Shell refactoring. Provides a single point
for applying theme changes across all application components.
"""

from typing import List, Any, Protocol, runtime_checkable


@runtime_checkable
class Themeable(Protocol):
    """Protocol for components that can be themed."""
    
    def update_theme(self, is_dark: bool) -> None:
        """Apply theme styling to this component."""
        ...


class ThemeCoordinator:
    """
    Centralized theme coordinator.
    
    Manages theme state and propagates theme changes to all
    registered themeable components.
    
    Usage:
        coordinator = ThemeCoordinator()
        coordinator.register(command_panel)
        coordinator.register(title_bar)
        coordinator.set_dark_mode(True)  # Updates all components
    """
    
    def __init__(self, is_dark: bool = True):
        """
        Initialize the theme coordinator.
        
        Args:
            is_dark: Initial theme state (True = dark, False = light)
        """
        self._is_dark = is_dark
        self._components: List[Any] = []
    
    @property
    def is_dark_mode(self) -> bool:
        """Current theme state."""
        return self._is_dark
    
    def register(self, component: Any) -> None:
        """
        Register a component for theme updates.
        
        The component should have an `update_theme(is_dark: bool)` method.
        
        Args:
            component: Component to register
        """
        if component not in self._components:
            self._components.append(component)
    
    def unregister(self, component: Any) -> None:
        """
        Unregister a component from theme updates.
        
        Args:
            component: Component to unregister
        """
        if component in self._components:
            self._components.remove(component)
    
    def set_dark_mode(self, is_dark: bool) -> None:
        """
        Set theme mode and update all registered components.
        
        Args:
            is_dark: True for dark theme, False for light theme
        """
        self._is_dark = is_dark
        self._apply_theme_to_all()
    
    def toggle_theme(self) -> bool:
        """
        Toggle between dark and light theme.
        
        Returns:
            bool: New theme state (True = dark)
        """
        self._is_dark = not self._is_dark
        self._apply_theme_to_all()
        return self._is_dark
    
    def refresh(self) -> None:
        """Re-apply current theme to all components."""
        self._apply_theme_to_all()
    
    def _apply_theme_to_all(self) -> None:
        """Apply current theme to all registered components."""
        for component in self._components:
            self._apply_theme_to_component(component)
    
    def _apply_theme_to_component(self, component: Any) -> None:
        """
        Apply theme to a single component.
        
        Handles different method names for backward compatibility.
        """
        # Try standard method name first
        if hasattr(component, 'update_theme'):
            try:
                component.update_theme(self._is_dark)
                return
            except Exception as e:
                print(f"[ThemeCoordinator] Error updating {type(component).__name__}: {e}")
        
        # Try alternative method names
        if hasattr(component, 'apply_theme'):
            try:
                component.apply_theme(self._is_dark)
                return
            except Exception:
                pass
        
        if hasattr(component, 'set_theme'):
            try:
                component.set_theme(self._is_dark)
                return
            except Exception:
                pass
    
    def apply_to_list(self, components: List[Any]) -> None:
        """
        Apply current theme to a list of components without registering them.
        
        Useful for temporary or dynamically created components.
        
        Args:
            components: List of components to theme
        """
        for component in components:
            self._apply_theme_to_component(component)
    
    @property
    def component_count(self) -> int:
        """Number of registered components."""
        return len(self._components)
    
    def __repr__(self) -> str:
        mode = "dark" if self._is_dark else "light"
        return f"ThemeCoordinator(mode={mode}, components={len(self._components)})"
