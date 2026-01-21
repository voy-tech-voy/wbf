# UI Refinement: Lab Mode & Visibility Logic

## Objective
Refine the Command Panel's UI to rigorously enforce a "clean" state when **Lab Mode** is inactive. The goal is to hide complex manual controls and retract side navigation buttons when they are not needed (i.e., when Lab Mode is OFF or when using one-click Presets).

## Core Changes

### 1. Lab Mode vs. Presets Logic
- **Lab Mode OFF (Ghost State):** This is the default "preview/simple" state.
    - **Manual Controls:** Hidden (Resize, Quality, Format options).
    - **Side Buttons:** "Shy" mode (90% hidden, retracted to the right).
- **Lab Mode ON (Solid State):** Activated by clicking the Lab icon.
    - **Manual Controls:** Fully visible and interactive.
    - **Side Buttons:** Fully visible and interactive.
- **Presets Mode:**
    - **Manual Controls:** Hidden (replaced by Presets list).
    - **Side Buttons:** "Shy" mode.

### 2. "Shy" Side Buttons
- **Behavior:** All side buttons (including tool toggles AND mode selectors like Max Size/Presets/Manual) now support a forced "hidden" state where they slide 90% off-screen (40px offset).
- **Implementation:**
    - `AnimatedSideModeButton`: Added `set_force_hidden(bool)` to override hover/selection animations and lock the button in a retracted state.
    - `SideButtonGroup` & `ModeButtonsWidget`: Updated to propagate this hidden state to all contained buttons.

### 3. Command Panel Logic
- **Initialization:** `setup_ui` now forces an immediate visibility check on startup to ensure the UI begins in the correct "clean" state.
- **State Management:**
    - Connected `lab_btn.styleChanged` signal to trigger global visibility updates.
    - `_on_global_mode_changed`: Now acts as the central enforcer, checking both the current Mode (Presets vs Manual) and the Lab Button state (Solid vs Ghost) to determine if side buttons should be hidden.
    - `on_image/video/loop_size_mode_changed`: Updated to explicitly hide manual control widgets if Lab Mode is inactive.

## Status
- **Completed:** All visibility logic is implemented and verified. The app launches with controls hidden, and toggling Lab Mode correctly reveals/hides them.
- **Next Steps:**
    - Ensure that dragging and dropping files works seamlessly with these hidden controls (i.e., defaults apply correctly).
    - Monitor user interaction with the "shy" buttons to ensure the lack of hover response in the hidden state is intuitive.
