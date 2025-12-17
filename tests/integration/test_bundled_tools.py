#!/usr/bin/env python3
"""
Test script to verify bundled tools in commercial build
"""

import os
import sys
import subprocess

def test_bundled_tools():
    """Test if bundled tools can be found and executed"""
    
    # Get the directory where the executable is located
    if getattr(sys, 'frozen', False):
        # Running in a PyInstaller bundle
        bundle_dir = sys._MEIPASS
    else:
        # Running in normal Python environment
        bundle_dir = os.path.dirname(os.path.abspath(__file__))
    
    bundled_tools_dir = os.path.join(bundle_dir, 'tools')
    
    print(f"Bundle directory: {bundle_dir}")
    print(f"Looking for bundled tools in: {bundled_tools_dir}")
    print(f"Bundled tools directory exists: {os.path.exists(bundled_tools_dir)}")
    
    if os.path.exists(bundled_tools_dir):
        tools = os.listdir(bundled_tools_dir)
        print(f"Found tools: {tools}")
        
        # Test FFmpeg
        ffmpeg_path = os.path.join(bundled_tools_dir, 'ffmpeg.exe')
        if os.path.exists(ffmpeg_path):
            try:
                result = subprocess.run([ffmpeg_path, '-version'], 
                                      capture_output=True, 
                                      text=True,
                                      creationflags=subprocess.CREATE_NO_WINDOW)
                print(f"FFmpeg test: SUCCESS")
                print(f"FFmpeg version info: {result.stdout.splitlines()[0] if result.stdout else 'No output'}")
            except Exception as e:
                print(f"FFmpeg test: FAILED - {e}")
        
        # Test Gifsicle
        gifsicle_path = os.path.join(bundled_tools_dir, 'gifsicle.exe')
        if os.path.exists(gifsicle_path):
            try:
                result = subprocess.run([gifsicle_path, '--version'], 
                                      capture_output=True, 
                                      text=True,
                                      creationflags=subprocess.CREATE_NO_WINDOW)
                print(f"Gifsicle test: SUCCESS")
                print(f"Gifsicle version: {result.stdout.strip() if result.stdout else result.stderr.strip()}")
            except Exception as e:
                print(f"Gifsicle test: FAILED - {e}")
    else:
        print("Bundled tools directory not found!")

if __name__ == '__main__':
    test_bundled_tools()