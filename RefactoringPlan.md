# Safe CommandPanel Integration Plan

## Strategy: Wrapper Pattern with Fallback

Instead of replacing code, we'll **wrap** the existing tab creation methods to use the new components while keeping old code as fallback.

---

## Phase A: ImageTab Integration

### Step A1: Create Wrapper
- Add `USE_NEW_IMAGE_TAB = False` flag at top of CommandPanel
- Modify `create_image_tab()` to call new ImageTab when flag is True
- Keep old code as fallback when flag is False

### Step A2: Test with Flag OFF
- Run app - should work exactly as before
- Run unit tests - all should pass

### Step A3: Enable and Test
- Set `USE_NEW_IMAGE_TAB = True`
- Run app and test image conversion
- If issues: set flag back to False

### Step A4: Verify
- Run full test suite
- Manual test: convert an image
- Commit if passing

---

## Phase B: VideoTab Integration

Same pattern as Phase A

---

## Phase C: LoopTab Integration

Same pattern as Phase A

---

## Phase D: Cleanup (After All Tests Pass)

- Remove old tab creation code
- Remove feature flags
- Update LOC count
- Final test suite run

---

## Rollback Strategy

At any point, setting the flag to `False` restores old behavior:
```python
USE_NEW_IMAGE_TAB = False  # Instant rollback
```

---

## Current Progress

- [x] Phase A: ImageTab Integration
- [x] Phase B: VideoTab Integration  
- [x] Phase C: LoopTab Integration
- [ ] Phase D: Cleanup (partial - legacy methods still in file, needs manual review)
