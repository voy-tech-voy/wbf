#!/usr/bin/env python3
"""
Test console hiding for ImgApp
"""
import os
import sys
import subprocess
import tempfile
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_console_hiding():
    """Test that console windows are properly hidden"""
    print("🔍 Testing Console Hiding")
    print("=" * 40)
    
    # Test bundled FFmpeg execution
    bundled_tools_dir = Path(__file__).parent / "tools"
    
    if os.name == 'nt':  # Windows
        ffmpeg_path = bundled_tools_dir / "ffmpeg.exe"
        gifsicle_path = bundled_tools_dir / "gifsicle.exe"
        
        if ffmpeg_path.exists():
            print("Testing FFmpeg with console hiding...")
            try:
                # Test with console hiding
                result = subprocess.run([str(ffmpeg_path), '-version'],
                                      capture_output=True,
                                      text=True,
                                      creationflags=subprocess.CREATE_NO_WINDOW,
                                      timeout=10)
                if result.returncode == 0:
                    print("✅ FFmpeg runs successfully with hidden console")
                else:
                    print("❌ FFmpeg failed")
            except Exception as e:
                print(f"❌ FFmpeg test failed: {e}")
        else:
            print("⚠️  FFmpeg not found in bundled_tools")
            
        if gifsicle_path.exists():
            print("Testing Gifsicle with console hiding...")
            try:
                # Test with console hiding
                result = subprocess.run([str(gifsicle_path), '--version'],
                                      capture_output=True,
                                      text=True,
                                      creationflags=subprocess.CREATE_NO_WINDOW,
                                      timeout=10)
                if result.returncode == 0:
                    print("✅ Gifsicle runs successfully with hidden console")
                else:
                    print("❌ Gifsicle failed")
            except Exception as e:
                print(f"❌ Gifsicle test failed: {e}")
        else:
            print("⚠️  Gifsicle not found in bundled_tools")
    else:
        print("⚠️  Console hiding test only applies to Windows")
    
    print("\nConsole hiding test completed!")

if __name__ == '__main__':
    test_console_hiding()