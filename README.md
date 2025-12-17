# Graphics Conversion App

A Qt-based desktop application for converting graphics files using FFmpeg, Gifsicle, and ImageMagick.

## Features

- **Drag & Drop Interface**: Easy file selection with unified display area
- **Folder Processing**: Process entire directories with subfolder options
- **Multiple Format Support**: Images, Videos, Audio
- **Three Conversion Types**:
  - Image conversion (JPG, PNG, WEBP, TIFF, BMP)
  - Video conversion (H.264, H.265, VP9, AV1)
  - GIF creation and optimization
- **Batch Processing**: Convert multiple files at once
- **Quality Control**: Single or multiple quality variants per image
- **Resize Options**: Scale images and videos
- **Progress Tracking**: Real-time conversion status
- **Dark Mode Support**: Automatically detects system theme + manual toggle
- **File Management**: Double-click to remove, right-click for context menu

## Requirements

### Python Packages (automatically installed):
- PyQt6
- ffmpeg-python
- Pillow

### External Tools:
- **FFmpeg** - For video/audio/image processing
- **Gifsicle** - For GIF optimization (optional)
- **ImageMagick** - For advanced image operations (optional)

## Installation

1. The Python environment is already configured with required packages
2. Install external tools:
   - **FFmpeg**: Download from https://ffmpeg.org/download.html
   - **Gifsicle**: Download from https://www.lcdf.org/gifsicle/
   - **ImageMagick**: Download from https://imagemagick.org/

## Usage

1. Run the application:
   ```
   imgapp_venv\Scripts\python.exe main.py
   ```
   Or double-click `run_app.bat`

2. **Add Files**:
   - Drag and drop files into the left panel, or
   - Click "Add Files..." button, or  
   - Click "Browse Folder..." to process entire directories
   - Drop folders directly for batch processing with options

3. **Configure Conversion**:
   - Select conversion type (Images/Videos/GIFs)
   - Adjust quality settings:
     - **Single quality**: Use slider for one quality level
     - **Multiple qualities**: Check "Multiple qualities" and enter comma-separated values (e.g., 40, 60, 80, 95)
   - Set resize options, output directory and filename options

4. **Convert**:
   - Click "Start Conversion"
   - Monitor progress in the status area

5. **Theme**:
   - Dark mode auto-detects system preference
   - Manual toggle: View → Toggle Dark Mode

## Supported Formats

### Input:
- **Images**: JPG, PNG, BMP, TIFF, GIF, WEBP
- **Videos**: MP4, AVI, MOV, MKV, FLV, WEBM
- **Audio**: MP3, WAV, FLAC, AAC, OGG

### Output:
- **Images**: JPG, PNG, WEBP, TIFF, BMP
- **Videos**: MP4 (H.264/H.265), WEBM (VP9), MP4 (AV1)
- **GIFs**: Optimized GIF files

## Interface Layout

```
┌─────────────────────────────────────────────────────┐
│ Menu Bar (File, Tools, View, Help)                 │
├─────────────────┬───────────────────────────────────┤
│ Files Panel     │ Conversion Commands Panel         │
│                 │                                   │
│ [Add Files...] [Browse Folder...] [Clear All]      │
│ ┌─────────────┐ │ ┌─ Images ─┬─ Videos ─┬─ GIFs ─┐ │
│ │📁 Drag files│ │ │ Format   │ Codec    │ Optim. │ │
│ │or folders   │ │ │ Quality  │ Bitrate  │ Colors │ │
│ │here or use  │ │ │ Resize   │ Scale    │ Delay  │ │
│ │buttons...   │ │ └──────────┴──────────┴────────┘ │
│ │             │ │                                   │
│ │• file1.jpg  │ │ Output Settings:                  │
│ │  (2.3 MB)   │ │ • Directory                       │
│ │• file2.mp4  │ │ • Filename suffix                 │
│ │  (15.7 MB)  │ │                                   │
│ └─────────────┘ │ [Start Conversion] [Preview]      │
├─────────────────┴───────────────────────────────────┤
│ Status Area:                                        │
│ Ready to convert graphics files...                  │
│ ████████████████████ 100%                          │
├─────────────────────────────────────────────────────┤
│ Status Bar: Ready | FFmpeg: ✓ Gifsicle: ✓ IM: ✓   │
└─────────────────────────────────────────────────────┘
```

## Tool Status

The application checks for required tools on startup:
- ✓ = Tool available
- ✗ = Tool missing (some features may not work)

## Development

Built with:
- **Python 3.11+**
- **PyQt6** for the GUI
- **FFmpeg-python** for media processing
- **Threading** for non-blocking conversions

## Testing (dev)

Run tests locally during development.

Recommended (install pytest):

```powershell
python -m pip install -r requirements-dev.txt
pytest -q
```

Run without pytest (lightweight runner included):

```powershell
python -m tests.run_tests_no_pytest
```

Note: the repository's tests cover bundled tools verification and checksum handling for onefile builds.