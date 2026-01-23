# Presets Plugin Documentation

A modular plugin for declarative video/image conversion presets using YAML definitions with Jinja2 templating.

---

## Architecture Overview

```
client/plugins/presets/
├── __init__.py              # Main exports
├── orchestrator.py          # Controller (Logic + UI connector)
├── logic/
│   ├── models.py            # Data classes
│   ├── manager.py           # YAML loader + tool validation
│   ├── builder.py           # Jinja2 command renderer
│   ├── analyzer.py          # FFprobe metadata extraction
│   └── exceptions.py        # Custom exceptions
├── ui/
│   ├── card.py              # PresetCard widget (120x160)
│   ├── gallery.py           # Overlay grid with parameter panel
│   └── parameter_form.py    # Dynamic parameter widgets
└── assets/presets/          # YAML preset definitions
    └── instagram_reel_pro.yaml
```

---

## Core Concepts

### 1. Tool Registry Integration

The plugin uses **Dependency Injection** - it receives `ToolRegistryProtocol` and never creates its own registry:

```python
from client.core.tool_registry import get_registry
from client.plugins.presets import PresetOrchestrator

registry = get_registry()
orchestrator = PresetOrchestrator(registry, parent_widget)
```

### 2. YAML Preset Schema

```yaml
meta:
  id: "preset_id"
  name: "Display Name"
  category: "social"
  description: "What this preset does"

style:
  accent_color: "#E1306C"
  icon: "instagram"

constraints:
  accepted_types: ["video"]
  accepted_extensions: [".mp4", ".mov"]

parameters:
  - id: "allow_rotate"
    type: "toggle"
    label: "Auto-Rotate"
    default: true
    visibility_rule: "not meta.is_landscape"

pipeline:
  - tool: "ffmpeg"
    command_template: |
      {{ tool_exe }} -i "{{ input_path }}"
      {% if allow_rotate and meta.is_landscape %}
        -vf "transpose=1,scale=1080:1920"
      {% endif %}
      "{{ output_path }}"
```

### 3. Jinja2 Context Variables

The command template has access to:

| Variable | Source | Example |
|----------|--------|---------|
| `tool_exe` | ToolRegistry | `C:/ffmpeg/ffmpeg.exe` |
| `input_path` | File being converted | `video.mp4` |
| `output_path` | Computed output path | `video_preset.mp4` |
| `meta.fps` | MediaAnalyzer | `60.0` |
| `meta.is_landscape` | MediaAnalyzer | `True` |
| `meta.width` | MediaAnalyzer | `1920` |
| `meta.height` | MediaAnalyzer | `1080` |
| `allow_rotate` | User parameter | `True` |
| `fill_method` | User parameter | `"Blur"` |

---

## Component Reference

### PresetManager

Loads YAML files and validates tool availability:

```python
manager = PresetManager(registry)
presets = manager.load_all()

for preset in presets:
    print(f"{preset.name}: {preset.status}")
    # Output: Instagram Reel Pro: ready
```

### CommandBuilder

Renders Jinja2 templates with context:

```python
builder = CommandBuilder(registry)

context = {
    'input_path': 'video.mp4',
    'output_path': 'out.mp4',
    'meta': {'fps': 60.0, 'is_landscape': True},
    'allow_rotate': True
}

cmd = builder.build_command(preset.pipeline[0], context)
# Output: "ffmpeg.exe -i video.mp4 -vf transpose=1,..."
```

### MediaAnalyzer

Extracts video metadata via FFprobe:

```python
analyzer = MediaAnalyzer(registry)
meta = analyzer.analyze("video.mp4")

# Returns:
# {
#     'fps': 60.0,
#     'width': 1920,
#     'height': 1080,
#     'is_landscape': True,
#     'has_audio': True,
#     'duration': 45.2
# }
```

### ParameterForm

Generates UI widgets from YAML parameters:

| Parameter Type | Widget |
|----------------|--------|
| `toggle` | QCheckBox |
| `slider` | QSlider + QLabel |
| `segmented_pill` | SegmentedPill |
| `dropdown` | QComboBox |

Visibility rules are evaluated via Jinja2.

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. User drops file → show_preset_view()                         │
├─────────────────────────────────────────────────────────────────┤
│ 2. User clicks preset card                                       │
│    └─→ Gallery shows parameter panel                             │
│    └─→ ParameterForm renders toggles/sliders                     │
│    └─→ preset_selected signal emitted                            │
├─────────────────────────────────────────────────────────────────┤
│ 3. on_preset_applied() stores _active_preset                     │
├─────────────────────────────────────────────────────────────────┤
│ 4. User clicks START                                             │
│    └─→ _start_preset_conversion()                                │
│    └─→ MediaAnalyzer.analyze() → meta dict                       │
│    └─→ orchestrator.get_parameter_values() → param dict          │
│    └─→ CommandBuilder.build_command(step, {meta, params})        │
│    └─→ subprocess.run(cmd)                                       │
├─────────────────────────────────────────────────────────────────┤
│ 5. Conversion complete                                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Creating New Presets

1. Create a YAML file in `client/plugins/presets/assets/presets/`
2. Define metadata, parameters, and pipeline steps
3. Use Jinja2 logic in `command_template` for smart behavior
4. Test with `pytest tests/test_presets_plugin.py`

### Example: TikTok Preset

```yaml
meta:
  id: "tiktok_vertical"
  name: "TikTok Vertical"
  category: "social"

style:
  accent_color: "#00F2EA"
  icon: "tiktok"

pipeline:
  - tool: "ffmpeg"
    command_template: |
      {{ tool_exe }} -y -i "{{ input_path }}"
      -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2"
      -c:v libx264 -preset fast -crf 23
      -c:a aac -b:a 128k
      "{{ output_path }}"
```

---

## Testing

Run unit tests:

```bash
pytest tests/test_presets_plugin.py -v
```

Test coverage:
- Models (PresetDefinition, PipelineStep)
- Manager (YAML loading, tool validation)
- Builder (Jinja2 rendering, defaults)
- Exceptions
- Imports
