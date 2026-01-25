"""
Presets Plugin - Category Filter Bar

Dynamic filter bar with exclusive toggle buttons for filtering presets by category.
Single selection mode with "ALL" button to show all presets.
"""
from typing import List, Optional
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QButtonGroup
from PyQt6.QtCore import pyqtSignal

from client.plugins.presets.logic.models import PresetDefinition
from client.gui.theme import Theme


class CategoryFilterBar(QWidget):
    """
    Horizontal bar with category toggle buttons.
    
    Behavior:
    - Dynamically generates buttons from preset categories
    - Single selection (exclusive) - only one category active at a time
    - "ALL" button shows all presets (default state)
    
    Signals:
        filterChanged: Emitted when selection changes
    """
    
    filterChanged = pyqtSignal()
    
    # Special key for "ALL" button
    ALL_KEY = "__all__"
    
    # Styling constants
    BUTTON_PADDING_H = 16  # Horizontal padding inside button
    BUTTON_PADDING_V = 8   # Vertical padding inside button
    BUTTON_SPACING = 8     # Gap between buttons
    BUTTON_HEIGHT = 32
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._buttons: dict[str, QPushButton] = {}
        self._selected_category: Optional[str] = None  # None or category name
        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)
        
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 8, 0, 8)
        self._layout.setSpacing(self.BUTTON_SPACING)
        
        # Center buttons with stretch on both sides
        self._layout.addStretch()  # Leading stretch
        self._layout.addStretch()  # Trailing stretch

    
    def set_categories(self, presets: List[PresetDefinition]) -> None:
        """
        Extract unique categories from presets and create buttons.
        
        Args:
            presets: List of preset definitions to extract categories from
        """
        # Clear existing buttons (but keep stretches)
        self._clear_buttons()
        
        # Extract unique categories
        categories = sorted(set(p.category for p in presets if p.category))
        
        # Insert buttons between the two stretches
        # Layout: [Stretch] [Buttons...] [Stretch]
        insert_index = 1  # After first stretch
        
        # Create "ALL" button first
        all_btn = self._create_button(self.ALL_KEY, "ALL")
        all_btn.setChecked(True)  # Default selection
        self._buttons[self.ALL_KEY] = all_btn
        self._button_group.addButton(all_btn)
        self._layout.insertWidget(insert_index, all_btn)
        insert_index += 1
        
        # Create buttons for each category
        for category in categories:
            display_name = category.upper()  # UPPERCASE labels
            btn = self._create_button(category, display_name)
            self._buttons[category] = btn
            self._button_group.addButton(btn)
            self._layout.insertWidget(insert_index, btn)
            insert_index += 1
        
        # Set initial state
        self._selected_category = None  # None = ALL
        self._update_button_styles()
    
    def _create_button(self, key: str, display_name: str) -> QPushButton:
        """Create a pill-shaped toggle button."""
        btn = QPushButton(display_name)
        btn.setCheckable(True)
        btn.setChecked(False)
        
        # Adaptive width: let Qt calculate based on text + padding
        btn.setFixedHeight(self.BUTTON_HEIGHT)
        btn.setStyleSheet(self._get_button_style(checked=False))
        
        # Connect click signal
        btn.clicked.connect(lambda checked, k=key: self._on_button_clicked(k))
        
        return btn
    
    def _on_button_clicked(self, key: str) -> None:
        """Handle button click - exclusive selection."""
        if key == self.ALL_KEY:
            self._selected_category = None
        else:
            self._selected_category = key
        
        # Update button styles
        self._update_button_styles()
        
        # Emit filter changed signal
        self.filterChanged.emit()
    
    def _update_button_styles(self) -> None:
        """Update all button styles based on selection."""
        for key, btn in self._buttons.items():
            is_selected = (key == self.ALL_KEY and self._selected_category is None) or \
                          (key == self._selected_category)
            btn.setStyleSheet(self._get_button_style(is_selected))
            btn.setChecked(is_selected)
    
    def _get_button_style(self, checked: bool) -> str:
        """Get CSS stylesheet for button based on state."""
        if checked:
            return f"""
                QPushButton {{
                    background-color: {Theme.accent_turbo()};
                    color: #000000;
                    border: none;
                    font-weight: bold;
                    font-size: {Theme.FONT_SIZE_SM}px;
                    border-radius: {self.BUTTON_HEIGHT // 2}px;
                    padding: {self.BUTTON_PADDING_V}px {self.BUTTON_PADDING_H}px;
                }}
                QPushButton:hover {{
                    background-color: #33E8FF;
                }}
            """
        else:
            return f"""
                QPushButton {{
                    background-color: {Theme.surface_element()};
                    color: {Theme.text_muted()};
                    border: 1px solid {Theme.border()};
                    font-size: {Theme.FONT_SIZE_SM}px;
                    border-radius: {self.BUTTON_HEIGHT // 2}px;
                    padding: {self.BUTTON_PADDING_V}px {self.BUTTON_PADDING_H}px;
                }}
                QPushButton:hover {{
                    background-color: {Theme.color('surface_hover')};
                    color: {Theme.text()};
                }}
            """
    
    def get_active_categories(self) -> List[str]:
        """
        Get list of currently selected categories.
        
        Returns:
            List with single category name, or empty list for "ALL".
        """
        if self._selected_category is None:
            return []  # Empty = show all
        return [self._selected_category]
    
    def _clear_buttons(self) -> None:
        """Remove all existing buttons (preserve stretches)."""
        # Remove from button group first
        for btn in self._buttons.values():
            self._button_group.removeButton(btn)
            btn.deleteLater()
        self._buttons.clear()
        self._selected_category = None
        
        # Clear only button widgets, preserve the two stretch items
        # Layout structure: [Stretch] [Buttons...] [Stretch]
        # Remove items from index 1 to count-2 (preserve stretches at 0 and last)
        while self._layout.count() > 2:
            item = self._layout.takeAt(1)  # Always remove at index 1
            if item.widget():
                item.widget().deleteLater()
    
    def reset_filters(self) -> None:
        """Reset to 'ALL' state."""
        self._selected_category = None
        self._update_button_styles()
        self.filterChanged.emit()
