#!/usr/bin/env python3
"""
Download Roboto Mono fonts from Google Fonts
This script downloads the required font files for bundling
"""

import os
import urllib.request
import sys
from pathlib import Path

# Font files from Google Fonts GitHub repository
FONTS_TO_DOWNLOAD = {
    'RobotoMono-Regular.ttf': 'https://github.com/google/roboto/raw/main/fonts/RobotoMono-Regular.ttf',
    'RobotoMono-Bold.ttf': 'https://github.com/google/roboto/raw/main/fonts/RobotoMono-Bold.ttf',
    'RobotoMono-Italic.ttf': 'https://github.com/google/roboto/raw/main/fonts/RobotoMono-Italic.ttf',
    'RobotoMono-BoldItalic.ttf': 'https://github.com/google/roboto/raw/main/fonts/RobotoMono-BoldItalic.ttf',
}

def download_fonts():
    """Download Roboto Mono fonts"""
    fonts_dir = Path(__file__).resolve().parent / 'client' / 'assets' / 'fonts'
    
    # Create directory if it doesn't exist
    fonts_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Downloading fonts to: {fonts_dir}")
    
    for filename, url in FONTS_TO_DOWNLOAD.items():
        filepath = fonts_dir / filename
        
        # Skip if already exists
        if filepath.exists():
            print(f"✓ {filename} already exists")
            continue
        
        try:
            print(f"Downloading {filename}...")
            urllib.request.urlretrieve(url, filepath)
            print(f"✓ Downloaded {filename}")
        except Exception as e:
            print(f"✗ Failed to download {filename}: {e}")
            return False
    
    # List files
    print(f"\nFonts in {fonts_dir}:")
    for f in fonts_dir.glob('*.ttf'):
        size_kb = f.stat().st_size / 1024
        print(f"  - {f.name} ({size_kb:.1f} KB)")
    
    return True

if __name__ == '__main__':
    success = download_fonts()
    sys.exit(0 if success else 1)
