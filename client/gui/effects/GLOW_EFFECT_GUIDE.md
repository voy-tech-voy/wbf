# Glow Effect Module Guide

## Overview
The `client/gui/effects/` module provides a comprehensive Siri-like glow effect with anti-banding noise, designed for high-end UI elements.

## Architecture

```
client/gui/effects/
├── __init__.py           # Exports public classes
└── glow_effect.py        # Core implementation
    ├── GlowEffectManager # Main entry point & state manager
    ├── SiriGlowOverlay   # Animated color blob rendering + Ripple logic
    ├── GlowNoiseOverlay  # Anti-banding noise layer
    └── GlowState         # Enums for interaction states
```

## `GlowEffectManager`
This is your primary interface. Use this instead of creating overlays directly.

### Usage
```python
from client.gui.effects.glow_effect import GlowEffectManager

class MyWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 1. Initialize manager (needs widget + top-level window)
        self._glow = GlowEffectManager(self, self.window())
        
    def showEvent(self, event):
        # 2. Show glow when widget appears
        self._glow.show()
        
    def hideEvent(self, event):
        # 3. Clean up
        self._glow.hide()
        
    def moveEvent(self, event):
        # 4. Keep synced position
        self._glow.update_position()
```

---

## Configuration

All configuration is centralized in `SiriGlowOverlay` class constants.

### Glow Parameters
| Constant | Default | Description |
|----------|---------|-------------|
| `BLOB_RADIUS` | 65 | Size of color blobs (Larger = Stronger core) |
| `HUE_SHIFT_DEGREES` | 30 | Color shifting range |
| `PULSE_OPACITY_MIN` | 0.6 | Minimum opacity during pulse |

### Animation & Masking
| Constant | Default | Description |
|----------|---------|-------------|
| `HOVER_FADE_IN_MS` | 200 | Fade-in duration (ms) |
| `HOVER_FADE_OUT_MS`| 400 | Fade-out duration (ms) |
| `HOVER_MAX_OPACITY`| 1.0 | Max glow opacity (1.0 = Full Strength) |
| `MASK_INTERIOR` | True | Cut out center to preserve button text |
| `MASK_PADDING` | 10 | Cutout inset |

### Anti-Banding Noise (Glow)
| Constant | Default | Description |
|----------|---------|-------------|
| `NOISE_OPACITY` | 36 | Master noise visibility (0-255) |
| `NOISE_TILE_SIZE` | 64 | Texture tile size |
| `NOISE_EDGE_FADE_START` | 0.6 | Where radial fade begins (0.0-1.0) |

### Debugging
| Constant | Default | Description |
|----------|---------|-------------|
| `DEBUG_SHOW_NOISE_AREA` | False | Show noise boundary + gradient |
| `DEBUG_SHOW_RIPPLE_MASK` | False | Show 70% opacity white mask rings |

---

## Theory of Operation

### Hover Animation
The glow fades in/out using a `QPropertyAnimation` on `masterOpacity`.
- **Idle**: 0.0 opacity (invisible)
- **Hover**: Fades to `HOVER_MAX_OPACITY` with `InOutQuad` easing.

### Interior Masking
To keep the button text legible, the center of the glow is cut out.
1. The base glow blobs are rendered.
2. A rounded rectangle matching the button shape is drawn with `CompositionMode_DestinationOut`, creating a transparent hole.
3. The global blur effect softens the edges of this hole, limiting the glow to the edges and surrounding area.

