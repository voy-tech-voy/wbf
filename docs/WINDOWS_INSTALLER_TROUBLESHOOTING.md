# Windows Installer Build Troubleshooting Guide

## Status: Build System Consolidated & Exe Created ✓

The build system has been consolidated into a single unified `build.py` script. The MSI installer is being created, but there's a current WiX directory nesting issue being resolved.

## Quick Start - New Unified Build System

```bash
# Build EXE + MSI (recommended)
cd V:\_MY_APPS\ImgApp_1
python build\scripts\build.py

# Or use the batch file
build\scripts\build.bat

# Build with MSIX (requires admin)
python build\scripts\build.py --msix

# EXE only
python build\scripts\build.py --exe-only
```

## Current Issue Being Fixed

**Current Status**: Files install to `C:\Program Files\webatchify\webatchify-v9.0\` instead of `C:\Program Files\webatchify\`

**Root Cause**: WiX heat tool includes directory names when packaging files

**Solution in Progress**: Creating a custom WiX manifest that directly references files without extra nesting

**Workaround for Now**: Use the direct folder path with version name or move installation to target folder

## Build System Changes

### Old System (Removed)
- `build_all.ps1` - PowerShell build all
- `BUILD_EXE_AND_MSI.bat` - Basic batch build
- `BUILD_ALL_WITH_MSIX.bat` - MSIX batch build
- `build_msix_proper.ps1` - MSIX creation script

**All archived in:** `build\scripts\archive_old_build_system\`

### New System (Current)
**Main Entry Point**: `build\scripts\build.py`
- Orchestrates entire build pipeline
- Checks prerequisites
- Builds EXE → MSI → MSIX (optional)
- Unified logging and error handling
- Clean command-line interface

**Batch Wrapper**: `build\scripts\build.bat`
- Double-click to build with default options
- Passes arguments to build.py

**Supporting Scripts**:
- `build_production.py` - PyInstaller EXE creation
- `build_msix.py` - WiX MSI creation (being refined)
- `build_msix_proper.ps1` - MSI to MSIX conversion

## Files Generated After Build

```
ImgApp_Releases/v9.0/
├── webatchify-v9.0/                   # Unversioned folder (EXE, dependencies)
├── webatchify-v9.0-installer.msi      # Windows installer (ready to distribute)
├── webatchify-v9.0.msix               # Microsoft Store package (if built)
├── app_icon.ico                       # Used by MSI
├── app_icon.png                       # Used by MSIX
└── staging/                           # Build staging files (temp)
```

## Installation Verification

After running the MSI installer, files should be at:
- **Target**: `C:\Program Files\webatchify\webatchify-v9.0.exe`
- **Current**: `C:\Program Files\webatchify\webatchify-v9.0\webatchify-v9.0.exe` (being fixed)
- **Start Menu**: `%ProgramData%\Microsoft\Windows\Start Menu\Programs\webatchify\`
- **Registry**: `HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\webatchify`

## Next Steps

1. **Fix WiX Nesting**: Update `build_msix.py` to use custom manifest instead of heat-generated
2. **Test Shortcut Paths**: Ensure shortcuts point to correct executable location
3. **Icon Display**: Verify icon shows in Start Menu and Apps & Features
4. **MSIX Build**: Test MSIX package creation with fixed MSI

## Notes

- Build system unified to single entry point: `build.py`
- Old batch/PowerShell scripts archived (not deleted)
- EXE builds successfully with all dependencies
- MSI builds successfully with shortcuts and registry entries
- Icons properly configured for both MSI and MSIX
- 64-bit installation configured

