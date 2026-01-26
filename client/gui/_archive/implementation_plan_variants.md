# Implementation Plan - Unified Numeric Variant Inputs

**Goal**: Replace inconsistent `QLineEdit` usage for numeric variant inputs with a single `UnifiedVariantInput` component that handles theming and input validation globally.

## User Review Required
> [!IMPORTANT]
> This change introduces a new component `UnifiedVariantInput` and modifies all three tabs (`ImageTab`, `VideoTab`, `LoopTab`). Visual appearance of input fields might change slightly to match the global theme more strictly.

## Proposed Changes

### 1. New Component: `UnifiedVariantInput`
**File:** `client/gui/custom_widgets.py`

Create a new class `UnifiedVariantInput` inheriting from `QLineEdit`:
- **Auto-Theming**: Connects to `ThemeManager` singleton on init.
- **Styling**: Uses `Theme` class for borders, background, text, and placeholder colors.
- **Validation**:
    - Limits input to numbers, commas, and spaces.
    - Prevents invalid characters (letters, special symbols).
    - Can optionally enforce logic (e.g., "integers only" vs "floats").

```python
class UnifiedVariantInput(QLineEdit):
    # ...
```

### 2. Refactor Tabs
Refactor the following files to use `UnifiedVariantInput` instead of `QLineEdit`:

#### [MODIFY] `client/gui/tabs/image_tab.py`
- Replace `self.quality_variants = QLineEdit()`
- Replace `self.resize_variants = QLineEdit()`

#### [MODIFY] `client/gui/tabs/video_tab.py`
- Replace `self.quality_variants = QLineEdit()`
- Replace `self.size_variants = QLineEdit()`

#### [MODIFY] `client/gui/tabs/loop_tab.py`
- Replace `self.gif_fps_variants`
- Replace `self.gif_colors_variants`
- Replace `self.gif_dither_variants`
- Replace `self.webm_quality_variants`
- Replace `self.resize_variants`

### 3. Cleanup
- Remove manual `setStyleSheet` if any exists for these inputs in the tabs.
- Ensure `update_theme` in tabs delegates to the new component (though auto-connection might make this redundant, explicit calls are safe).

## Verification Plan

### Automated Tests
- Create `tests/test_unified_input.py`:
    - Test instantiation.
    - Test theme update signal connection.
    - Test text validation (accepts "10, 20", rejects "abc").

### Manual Verification
1. **Launch App**: `python -m client.main`
2. **Check Image Tab**:
    - Enable "Multiple qualities".
    - Type "10, 20, 30". Verify accepted.
    - Type "abc". Verify rejected/ignored.
    - Toggle Dark/Light mode. Verify input field colors update (bg, text, border).
3. **Check Loop Tab**:
    - Enable "Multiple Variants".
    - Check FPS variants input using same steps.
4. **Check Video Tab**:
    - Enable "Multiple size variants".
    - Check input behavior.
