---
description: DESIGN_SPEC
---


Version: 4.0 (Consolidated)
Target Framework: Python Qt6 (PyQt6 / PySide6)
Visual Identity: Premium Industrial (Tesla Dark Mode / Apple Ceramic)
Core Values: Efficiency, Speed, Transparency, Precision.

1. DESIGN PHILOSOPHY & RULES

Dark Mode First: The application defaults to a deep, void-like dark theme. Light mode is secondary.

Frameless Unity: The OS title bar is banned. The window is a self-contained, rounded slate (Radius: 16px).

Efficiency Over Fluff:

No QGraphicsBlurEffect on the main window resizing (kills FPS).

Use semi-transparent matte colors for glass effects.

Animations must be <200ms OutQuad curves.

Hardware Visuality: GPU acceleration is a visual state. If CUDA/Metal is detected, the UI shifts from "White/Clean" to "Cyan/Turbo."

Pixel Alignment: All margins and padding follow a 4px grid (4, 8, 12, 16, 24).

2. THEME ENGINE (Variables)

The AI Agent must implement a Theme Manager to inject these values into QSS strings.

Dark Mode (Default)
Variable	Value	Description
app_bg	#0B0B0B	Deepest Void (Window Background)
surface_main	#161616	Drop Zone / Panels
surface_element	#242424	Buttons / Inputs
border_dim	#333333	Subtle Separation
border_focus	#555555	Hover/Focus State
text_primary	#F5F5F7	Main Readability
text_secondary	#86868B	Labels / Meta Data
accent_primary	#FFFFFF	Standard Action
accent_turbo	#00E0FF	GPU Active (Electric Cyan)
accent_success	#30D158	Success State
tooltip_bg	#333333	Tooltip Background
Light Mode (Reference)

Invert logic: app_bg = #F5F5F7, surface_main = #FFFFFF, text_primary = #000000.

3. WINDOW ARCHITECTURE

To achieve the premium look, the window must be decoupled from the OS frame.

Flags: Qt.WindowType.FramelessWindowHint | Qt.WidgetAttribute.WA_TranslucentBackground.

Container: A QFrame (id=RootFrame) acts as the visible body inside the transparent QMainWindow.

Shadows:

Apply QGraphicsDropShadowEffect to RootFrame.

Specs: Blur: 30px, Offset Y: 10px, Color: rgba(0,0,0, 0.7).

Note: RootFrame requires margins inside the Main Window to allow shadow rendering without clipping.

4. LAYOUT & COMPONENT STYLES (QSS)
A. The Drop Zone (Central Hero)

The area where files land. It dominates the center of the UI.

code
CSS
download
content_copy
expand_less
QFrame#DropZone {
    background-color: {{surface_main}};
    border: 2px dashed {{border_dim}};
    border-radius: 12px;
}
/* Visual Feedback on Drag Hover */
QFrame#DropZone[dragActive="true"] {
    background-color: {{surface_element}};
    border: 2px solid {{accent_primary}}; /* Becomes Solid White */
}
QLabel#DropLabel {
    color: {{text_secondary}};
    font-family: "Inter";
    font-size: 14px;
    font-weight: 600;
}
B. Action Squares (Top Left Cluster)

Three minimalist buttons above the drop zone: Add File, Add Folder, Clear.

code
CSS
download
content_copy
expand_less
QPushButton.ActionSquare {
    background-color: {{surface_element}};
    border: 1px solid {{border_dim}};
    border-radius: 8px;
    width: 36px;
    height: 36px;
}
QPushButton.ActionSquare:hover {
    background-color: {{border_dim}};
    border-color: {{border_focus}};
}
QPushButton.ActionSquare:pressed {
    background-color: #000000;
}
C. Command Panel (Modern Toggles)

Replaces checkboxes with "Tesla-style" toggle switches.

code
CSS
download
content_copy
expand_less
/* The Switch Track */
QCheckBox::indicator {
    width: 32px;
    height: 18px;
    border-radius: 9px;
}
QCheckBox::indicator:unchecked {
    background-color: {{border_dim}};
    border: 1px solid {{border_dim}};
}
QCheckBox::indicator:checked {
    background-color: {{accent_success}};
    border: 1px solid {{accent_success}};
}
/* Note: The circular knob is handled via sub-controls or custom painting in Qt6 */
D. Output Bar (Bottom Strip)

Full width. Contains Segmented Control (Left) and Start Button (Right).

1. Unified Segmented Control (The Multi-Pill)
Used for: [In Source | Organized | Custom]

code
CSS
download
content_copy
expand_less
QFrame.SegmentContainer {
    background-color: {{app_bg}}; 
    border: 1px solid {{border_dim}};
    border-radius: 10px;
    min-height: 32px;
}
QPushButton.SegmentBtn {
    background-color: transparent;
    color: {{text_secondary}};
    border: none;
    border-radius: 6px;
    padding: 6px 16px;
    font-size: 12px;
    font-weight: 500;
}
QPushButton.SegmentBtn:checked {
    background-color: {{border_dim}}; 
    color: {{text_primary}};
    font-weight: 600;
    border-top: 1px solid #444444; /* Subtle 3D light lip */
}

2. The Start Button (GPU Logic)

Standard (CPU):

code
CSS
download
content_copy
expand_less
QPushButton#BtnStart {
    background-color: {{accent_primary}};
    color: {{app_bg}};
    border-radius: 8px;
    font-weight: 700;
    padding: 8px 30px;
}

Turbo (GPU Active):

code
CSS
download
content_copy
expand_less
QPushButton#BtnStart[gpu="true"] {
    background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 {{accent_turbo}}, stop:1 #007AFF);
    color: #000000;
    border: none;
}
E. Tooltips (Global)
code
CSS
download
content_copy
expand_less
QToolTip {
    background-color: {{tooltip_bg}};
    color: {{text_primary}};
    border: 1px solid {{border_dim}};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 11px;
}
5. ANIMATION & EFFECTS (Python Side)
1. GPU Glow (The "Turbo" Effect)

Trigger: When gpu="true" on the Start Button.

Implementation:

code
Python
download
content_copy
expand_less
glow = QGraphicsDropShadowEffect()
glow.setBlurRadius(20)
glow.setColor(QColor(0, 224, 255, 100)) # Cyan with Alpha
glow.setOffset(0, 0)
btn_start.setGraphicsEffect(glow)
2. Drag & Drop Pulse

Trigger: dragEnterEvent on Drop Zone.

Effect: Animate background color from surface_main to surface_element (Duration: 150ms).

6. COMPONENT LOGIC FOR AGENT

UI_Segment_Pill Class:

Inherits QFrame.

Uses QButtonGroup (exclusive) to manage state.

Does not use separate radio buttons physically, but styles QPushButtons as checkable.

ModernToggle Class:

Inherits QCheckBox.

Uses QSS for the track, but may need a custom hit-test override for better usability.

FramelessWindow Class:

Must implement mousePress and mouseMove to handle window dragging (calculating offset from global mouse position).

Hardware Detection:

On Init, run a lightweight check for CUDA/Metal.

Set setProperty("gpu", True) on the Start Button if found.

Call style().polish(btn) to force style update.

7. LAYOUT TREE (Pseudocode)
code
Text
download
content_copy
expand_less
FramelessWindow (Transparent)
└── RootFrame (Rounded, Shadowed)
    └── QVBoxLayout (Main Layout)
        ├── TopLayout (HBox)
        │   ├── ActionSquare (Add File)
        │   ├── ActionSquare (Add Folder)
        │   ├── ActionSquare (Clear)
        │   └── Spacer
        ├── DropZone (VBox, Expanding)
        │   └── QLabel ("Drag files here...")
        ├── CommandPanel (Optional Splitter or Sidebar)
        │   └── ScrollArea -> VBox (Toggles)
        └── BottomBar (HBox)
            ├── SegmentContainer ([In Source] [Organized] [Custom])
            ├── Spacer (Expanding)
            └── BtnStart (GPU Accelerated)