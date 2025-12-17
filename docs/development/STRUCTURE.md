# Project Structure (WIP reorg)

This reorganization groups files by purpose to reduce root clutter.

## Directories
- `src/` (planned): application code (`core/`, `gui/`, `assets/`, `server_*`, entry `main.py`).
- `scripts/`: build/deploy helpers (e.g., `build_release_full.bat` moved here).
- `packaging/`: PyInstaller specs and packaging resources.
- `docs/`: guides, changelogs, deployment notes, this file.
- `config/`: runtime configuration and sample license/config files.
- `tests/`: automated tests (root `test_*.py` to be consolidated).
- `build/`: build intermediates.
- `dist/`: distributable artifacts.
- `releases/`: versioned release archives/executables.
- `logs/`: runtime logs.

## Recent move
- `build_release_full.bat` → `scripts/build_release_full.bat` (root file now delegates).

## Next steps (suggested)
- Move remaining build/deploy scripts into `scripts/`.
- Group `.spec` files under `packaging/` (optionally by edition).
- Relocate configs/licensing data into `config/` with example templates.
- Consolidate tests under `tests/`.
