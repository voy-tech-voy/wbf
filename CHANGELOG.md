# ImgApp Version History

## Version 1.0.0 (2025-11-18)
**Major Release - Initial Stable Version**

### Features
- Image conversion (JPG, PNG, WEBP, BMP, TIFF)
- Video conversion (MP4, AVI, MOV, etc.)
- GIF creation from videos
- Multiple quality variants support
- Batch folder processing
- Resize options (by ratio or pixel width)
- Dark theme interface with auto-detection
- Drag & drop support
- Start/Stop conversion control
- Standalone executable packaging

### Technical
- Framework: PyQt5 (migrated from PyQt6 for better packaging)
- Virtual environment: `imgapp_venv`
- Packaging: PyInstaller single-file executable
- Dependencies: PyQt5, Pillow, ffmpeg-python

### Bug Fixes
- Fixed PyInstaller DLL loading issues by switching to PyQt5
- Resolved Start/Stop button functionality
- Fixed variant processing interruption
- Corrected theme management for all dialogs

### Known Issues
- FFmpeg must be installed separately for video conversions
- Large video files may take significant time to process