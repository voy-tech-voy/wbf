---
description: How to create a new preset YAML file for the Presets Plugin
---

# Creating a New Preset

This guide covers the complete process of creating a new preset YAML file.

## Quick Start

1. Copy the template:
   ```
   client/plugins/presets/assets/presets/_TEMPLATE.yaml
   ```

2. Save with a descriptive name:
   ```
   client/plugins/presets/assets/presets/your_preset_name.yaml
   ```

3. Restart the app or call `orchestrator.reload_presets()`

---

## Step-by-Step Instructions

### Step 1: Define Metadata

```yaml
meta:
  id: "youtube_shorts"     # Unique, snake_case
  name: "YouTube Shorts"   # Display name
  category: "social"       # Grouping category
  description: "Vertical video for YouTube Shorts"
```

### Step 2: Set Visual Style (Optional)

```yaml
style:
  accent_color: "#FF0000"  # YouTube red
  icon: "youtube"          # Icon file in client/assets/icons/
  glow_strength: "strong"
```

### Step 3: Define Parameters (Optional)

Add user-adjustable settings:

| Type | Widget | Default Type |
|------|--------|--------------|
| `toggle` | Checkbox | `true`/`false` |
| `slider` | Slider | number |
| `segmented_pill` | Button group | string |
| `dropdown` | Dropdown | string |

```yaml
parameters:
  - id: "quality"
    type: "slider"
    label: "Quality"
    default: 23
    min_value: 18
    max_value: 28
```

### Step 4: Write the Pipeline

The `command_template` uses Jinja2 templating:

```yaml
pipeline:
  - tool: "ffmpeg"
    command_template: |
      {{ tool_exe }} -y -i "{{ input_path }}"
      -vf "scale=1080:1920"
      -c:v libx264 -crf {{ quality }}
      "{{ output_path }}"
```

---

## Available Template Variables

### From System
| Variable | Type | Example |
|----------|------|---------|
| `tool_exe` | string | `C:/tools/ffmpeg.exe` |
| `input_path` | string | `video.mp4` |
| `output_path` | string | `video_preset.mp4` |

### From MediaAnalyzer (`meta.*`)
| Variable | Type | Example |
|----------|------|---------|
| `meta.fps` | float | `59.94` |
| `meta.width` | int | `1920` |
| `meta.height` | int | `1080` |
| `meta.is_landscape` | bool | `True` |
| `meta.has_audio` | bool | `True` |
| `meta.duration` | float | `45.2` |
| `meta.codec` | string | `h264` |

### From Parameters
Any parameter `id` is available directly:
- `{{ quality }}` → slider value
- `{{ fill_method }}` → selected option
- `{{ enable_feature }}` → toggle state

---

## Jinja2 Cheatsheet

### Conditionals
```yaml
{% if meta.is_landscape %}
  -vf "transpose=1"
{% endif %}
```

### If-Else
```yaml
{% if quality < 20 %}
  -preset slow
{% else %}
  -preset fast
{% endif %}
```

### Default Values
```yaml
-crf {{ quality | default(23) }}
```

### Math Operations
```yaml
-g {{ (meta.fps * 2) | int }}
```

### Set Variables
```yaml
{% set fps_filter %}
  {% if meta.fps > 30 %}fps=30{% endif %}
{% endset %}

-vf "scale=1080:1920{{ fps_filter }}"
```

---

## Visibility Rules

Hide parameters based on conditions:

```yaml
parameters:
  - id: "auto_rotate"
    type: "toggle"
    default: true

  - id: "fill_method"
    type: "segmented_pill"
    options: ["Blur", "Crop", "Fit"]
    # Only show when NOT auto-rotating a landscape video
    visibility_rule: "not (auto_rotate and meta.is_landscape)"
```

---

## Common FFmpeg Patterns

### Scale to 1080p
```yaml
-vf "scale=1920:1080:force_original_aspect_ratio=decrease"
```

### Vertical Video (9:16)
```yaml
-vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2"
```

### Blur Background Fill
```yaml
-filter_complex "[0:v]split[bg][fg];
  [bg]scale=1080:1920,crop=1080:1920,boxblur=20:10[bg_blur];
  [fg]scale=1080:1920:force_original_aspect_ratio=decrease[fg_scaled];
  [bg_blur][fg_scaled]overlay=(W-w)/2:(H-h)/2[outv]"
-map "[outv]" -map 0:a?
```

### FPS Normalization
```yaml
{% if meta.fps > 31 %}
  -vf "fps=30"
{% endif %}
```

---

## Testing Your Preset

1. Syntax check:
   ```python
   from client.plugins.presets.logic import PresetManager
   from client.core.tool_registry import get_registry
   
   manager = PresetManager(get_registry())
   preset = manager.load_preset("path/to/your_preset.yaml")
   print(preset.status)  # Should be "ready"
   ```

2. Command preview:
   ```python
   from client.plugins.presets.logic import CommandBuilder
   
   builder = CommandBuilder(get_registry())
   cmd = builder.build_command(preset.pipeline[0], {
       'input_path': 'test.mp4',
       'output_path': 'out.mp4',
       'meta': {'fps': 30, 'is_landscape': True},
       'quality': 23
   })
   print(cmd)
   ```
