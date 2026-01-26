# Theme System - Quick Reference Guide

**Last Updated:** 2026-01-26

---

## 🚀 Quick Start

### Get ThemeManager Instance
```python
from client.gui.theme_manager import ThemeManager

theme_manager = ThemeManager.instance()  # Always use .instance()
```

### Toggle Theme
```python
ThemeManager.instance().toggle_theme()  # Switch between dark/light
```

### Get Current Theme
```python
is_dark = ThemeManager.instance().is_dark_mode()  # Returns bool
```

---

## 🎨 Using Theme Colors

### Get Solid Color
```python
from client.gui.theme import Theme

bg_color = Theme.bg()                    # App background
text_color = Theme.text()                # Primary text
accent = Theme.accent()                  # Primary accent
success = Theme.success()                # Success green
```

### Get Color with Transparency
```python
# For QSS stylesheets
glassy_bg = Theme.color_with_alpha('accent_primary', 0.047)
# Returns: "rgba(255, 255, 255, 0.047)"

# For custom painting
qcolor = Theme.to_qcolor('accent_success')  # Returns QColor object
```

---

## 🔧 Creating Theme-Aware Widgets

### ThemedCheckBox (Automatic)
```python
from client.gui.custom_widgets import ThemedCheckBox

# Just create it - auto-connects to ThemeManager!
checkbox = ThemedCheckBox("Enable feature")
# No manual theme setup needed
```

### GenericSegmentedControl (Automatic)
```python
from client.gui.custom_widgets import GenericSegmentedControl

# Just create it - auto-connects to ThemeManager!
control = GenericSegmentedControl()
control.add_segment("opt1", "Option 1", is_checked=True)
control.add_segment("opt2", "Option 2")
```

### Custom Widget (Manual Connection)
```python
from PyQt6.QtWidgets import QWidget
from client.gui.theme_manager import ThemeManager
from client.gui.theme import Theme

class MyCustomWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Connect to ThemeManager
        theme_manager = ThemeManager.instance()
        theme_manager.theme_changed.connect(self.update_theme)
        
        # Set initial theme
        self._is_dark = theme_manager.is_dark_mode()
        self._apply_style()
    
    def update_theme(self, is_dark: bool):
        """Called automatically when theme changes"""
        self._is_dark = is_dark
        self._apply_style()
    
    def _apply_style(self):
        Theme.set_dark_mode(self._is_dark)
        
        # Use Theme methods
        bg = Theme.surface()
        text = Theme.text()
        
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg};
                color: {text};
            }}
        """)
```

---

## 📐 Common Theme Values

### Colors
```python
Theme.bg()              # App background (deepest)
Theme.surface()         # Panel/card background
Theme.surface_element() # Button/input background
Theme.text()            # Primary text
Theme.text_muted()      # Secondary text
Theme.accent()          # Primary accent (white/black)
Theme.accent_turbo()    # Cyan accent
Theme.success()         # Green
Theme.error()           # Red
Theme.warning()         # Orange
Theme.border()          # Subtle border
Theme.border_focus()    # Hover/focus border
```

### Spacing
```python
Theme.SPACING_XS   # 4px
Theme.SPACING_SM   # 8px
Theme.SPACING_MD   # 12px
Theme.SPACING_LG   # 16px
Theme.SPACING_XL   # 24px
Theme.SPACING_XXL  # 32px
```

### Border Radius
```python
Theme.RADIUS_XS     # 2px  - Tiny elements
Theme.RADIUS_SM     # 4px  - Small elements
Theme.RADIUS_MD     # 8px  - Standard
Theme.RADIUS_LG     # 12px - Large containers
Theme.RADIUS_XL     # 16px - Modals
Theme.RADIUS_ROUND  # 50   - Circular
```

### Fonts
```python
Theme.FONT_BODY     # "Lexend" - UI text
Theme.FONT_DISPLAY  # "Montserrat Alternates" - App title
Theme.FONT_MONO     # "Roboto Mono" - Code/paths

Theme.FONT_SIZE_XS    # 10px
Theme.FONT_SIZE_SM    # 11px
Theme.FONT_SIZE_BASE  # 14px
Theme.FONT_SIZE_LG    # 16px
Theme.FONT_SIZE_XL    # 20px
```

---

## 🎯 Common Patterns

### Glassy Background
```python
# Semi-transparent white overlay
glassy = Theme.color_with_alpha('accent_primary', 0.047)
```

### Hover State
```python
# Slightly more opaque on hover
hover_bg = Theme.color_with_alpha('accent_primary', 0.059)
```

### Success with Transparency
```python
# Green with 80% opacity
success_fade = Theme.color_with_alpha('accent_success', 0.8)
```

---

## 🔍 Troubleshooting

### Widget Not Updating on Theme Change
**Problem:** Widget doesn't update when theme toggles

**Solution:** Ensure widget connects to ThemeManager signal:
```python
theme_manager = ThemeManager.instance()
theme_manager.theme_changed.connect(self.update_theme)
```

### Colors Look Wrong
**Problem:** Colors don't match theme

**Solution:** Always call `Theme.set_dark_mode()` before using colors:
```python
def _apply_style(self):
    Theme.set_dark_mode(self._is_dark)  # Important!
    color = Theme.text()  # Now returns correct color
```

### Multiple ThemeManager Instances
**Problem:** Creating new instances instead of using singleton

**Solution:** Always use `.instance()`:
```python
# ❌ WRONG:
theme_manager = ThemeManager()

# ✅ CORRECT:
theme_manager = ThemeManager.instance()
```

---

## 📚 File Locations

```
client/gui/
├── theme.py                    # Theme class (colors, metrics)
├── theme_manager.py            # ThemeManager singleton
├── theme_variables.py          # Color palettes (DARK_THEME, LIGHT_THEME)
├── styles/
│   └── style_factory.py        # QSS generation
└── _archive/
    ├── THEME_REFACTOR_COMPLETE.md
    ├── REFACTOR_PHASES_1-3_COMPLETE.md
    └── REFACTOR_PHASE_4_COMPLETE.md
```

---

## 🎓 Best Practices

1. **Always use singleton:** `ThemeManager.instance()`
2. **Use Theme methods:** Never hardcode colors
3. **Use color_with_alpha():** For transparency instead of rgba()
4. **Connect to signals:** Let ThemeManager notify your widgets
5. **Set dark mode:** Call `Theme.set_dark_mode()` before using colors

---

## 📞 Need Help?

1. Check `THEME_REFACTOR_COMPLETE.md` for architecture overview
2. Check `REFACTOR_PHASE_4_COMPLETE.md` for widget examples
3. Look at `ThemedCheckBox` or `GenericSegmentedControl` for reference implementations

---

**Quick Reference Version:** 1.0  
**Compatible with:** Theme System Refactor (All Phases Complete)
