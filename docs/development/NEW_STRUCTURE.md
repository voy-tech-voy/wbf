# ImgApp New Project Structure

**Migration Date:** December 12, 2025  
**Migration Script:** `migrate_structure.py`  
**Rollback Available:** `ROLLBACK_MIGRATION.py`

## Overview

The project has been reorganized from a cluttered monolith (50+ files in root) into a clean, professional structure with clear separation of concerns.

## New Directory Structure

```
ImgApp_1/
├── client/              # Desktop Application (PyQt5)
│   ├── main.py         # Application entry point
│   ├── version.py      # Version information
│   ├── core/           # Business logic
│   │   ├── conversion_engine.py
│   │   └── license_manager.py
│   ├── gui/            # UI components
│   │   ├── login_window.py
│   │   ├── main_window.py
│   │   ├── command_panel.py
│   │   ├── drag_drop_area.py
│   │   └── theme_manager.py
│   ├── utils/          # Client utilities
│   │   ├── crash_reporter.py
│   │   ├── error_reporter.py
│   │   └── hardware_id.py
│   ├── config/         # Client configuration
│   │   ├── config.py
│   │   ├── local_config.py
│   │   └── local_config.json
│   └── assets/         # Icons, animations
│
├── server/             # License API Server (Flask)
│   ├── app.py         # Main Flask application
│   ├── wsgi.py        # WSGI entry point
│   └── data/          # Runtime data (licenses.json)
│
├── tools/             # Bundled conversion tools
│   ├── ffmpeg.exe
│   ├── gifsicle.exe
│   ├── checksums.json
│   └── licenses/      # Tool licenses
│
├── build/             # Build system & packaging
│   ├── scripts/       # Python build scripts
│   │   ├── build_production.py
│   │   ├── build_personal.py
│   │   ├── build_personal_full.py
│   │   └── build_personal_lite.py
│   ├── bat/           # Batch file launchers
│   │   ├── build_production.bat
│   │   ├── build_release.bat
│   │   └── run_app.bat
│   ├── specs/         # PyInstaller spec files
│   │   └── production.spec
│   └── output/        # Build artifacts (gitignored)
│
├── deployment/        # Deployment configurations
│   ├── pythonanywhere/
│   ├── railway/
│   ├── render/
│   └── nixpacks/
│
├── scripts/           # Development & utility scripts
│   ├── license_tools/ # License management
│   ├── debug/         # Debug utilities
│   ├── testing/       # Test servers
│   ├── packaging/     # Packaging utilities
│   └── utilities/     # Misc tools
│
├── tests/             # All tests organized by type
│   ├── run_tests.py   # Test runner
│   ├── unit/          # Unit tests
│   ├── integration/   # Integration tests
│   ├── e2e/           # End-to-end tests
│   ├── server/        # Server tests
│   └── platform/      # Platform-specific tests
│
└── docs/              # Documentation
    ├── client/        # Client documentation
    ├── server/        # Server documentation
    ├── build/         # Build guides
    ├── development/   # Development docs
    └── archive/       # Historical docs
```

## Key Changes

### What Moved Where

| Old Location | New Location | Purpose |
|--------------|--------------|---------|
| `main.py` | `client/main.py` | Client entry point |
| `version.py` | `client/version.py` | Version info |
| `gui/*` | `client/gui/*` | UI components |
| `core/*` | `client/core/*` | Business logic |
| `config.py` | `client/config/config.py` | Configuration |
| `emergency_crash_reporter.py` | `client/utils/crash_reporter.py` | Crash reporting |
| `windows_error_reporter.py` | `client/utils/error_reporter.py` | Error reporting |
| `cross_platform_hardware_id.py` | `client/utils/hardware_id.py` | Hardware ID |
| `assets/*` | `client/assets/*` | Assets |
| `production_license_api.py` | `server/app.py` | License API |
| `bundled_tools/*` | `tools/*` | Conversion tools |
| `build_production_windows.py` | `build/scripts/build_production.py` | Build script |
| `*.bat` (root) | `build/bat/*.bat` | Batch launchers |
| `ImgApp-v4.88.spec` | `build/specs/production.spec` | PyInstaller spec |
| `tests/*.py` | `tests/*/test_*.py` | Tests by category |
| Various `.md` (root) | `docs/*/*.md` | Organized docs |

### Import Updates

All Python files have been automatically updated with new imports:

**Before:**
```python
from gui.main_window import MainWindow
from core.conversion_engine import ConversionEngine
from config import current_config
```

**After:**
```python
from client.gui.main_window import MainWindow
from client.core.conversion_engine import ConversionEngine
from client.config.config import current_config
```

### Build System Updates

**Spec File (`build/specs/production.spec`):**
- Updated to use relative paths from spec location
- All paths now reference `client/`, `tools/`, etc.
- Hiddenimports updated for new module structure

**Build Scripts:**
- `ROOT` now points to project root (not script location)
- All file checks updated for new paths
- PyInstaller commands updated

## Benefits

1. **Clear Separation**: Client, Server, Build, Scripts, Tests all separate
2. **Scalability**: Easy to add payment webhooks, email service, trial counters
3. **Developer Friendly**: New developers can quickly understand layout
4. **Professional**: Follows industry best practices
5. **CI/CD Ready**: Clear test categories and build scripts
6. **PyInstaller Compatible**: All client code under `client/`

## Migration Log

All operations are logged in `migration_log.json`:
- File moves with source and destination
- File deletions
- Timestamps for each operation

## Rollback

If needed, run:
```bash
python ROLLBACK_MIGRATION.py
```

This will reverse all move operations (deleted files cannot be restored).

## Next Steps

After migration:

1. **Test Build:**
   ```bash
   build\bat\build_production.bat 5.0
   ```

2. **Run Tests:**
   ```bash
   python tests/run_tests.py
   ```

3. **Verify Exe:**
   - Launch built exe
   - Test license login
   - Test conversion

4. **Commit:**
   ```bash
   git add -A
   git commit -m "Refactor: Complete project restructure"
   ```

## Future Enhancements

With the new structure, these are now easy to add:

- `server/services/payment_service.py` - Payment webhooks
- `server/services/email_service.py` - Email delivery
- `client/core/trial_manager.py` - Trial/usage counters
- `server/storage/db_storage.py` - Database backend
- `server/api/routes.py` - Organize Flask routes

## Documentation Updates Needed

- Update README.md with new structure
- Update CONTRIBUTING.md (if exists)
- Update any developer setup guides
- Update deployment guides with new paths

## Files Deleted

The following were removed as duplicates or obsolete:

- Old deployment docs (consolidated into `docs/server/`)
- Duplicate Windows production docs
- Old macOS compatibility analysis
- Backup config files
- Empty directories (`core/`, `gui/`, etc.)
- Old venv (`imgapp_env/`)
- Temporary test directories
