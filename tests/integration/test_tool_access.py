#!/usr/bin/env python3

import sys
import os

def get_bundled_tool_path(tool_name):
    """Get the path to a bundled tool, handling both development and PyInstaller environments"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller bundle - tools are in the temporary extraction directory
        base_path = sys._MEIPASS
    else:
        # Development environment - tools are relative to script
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    tool_path = os.path.join(base_path, 'tools', tool_name)
    return tool_path

def test_tool_paths():
    print("=== Tool Path Testing ===")
    
    ffmpeg_path = get_bundled_tool_path('ffmpeg.exe')
    gifsicle_path = get_bundled_tool_path('gifsicle.exe')
    
    print(f"FFmpeg path: {ffmpeg_path}")
    print(f"FFmpeg exists: {os.path.exists(ffmpeg_path)}")
    if os.path.exists(ffmpeg_path):
        print(f"FFmpeg size: {os.path.getsize(ffmpeg_path)} bytes")
    
    print(f"Gifsicle path: {gifsicle_path}")
    print(f"Gifsicle exists: {os.path.exists(gifsicle_path)}")
    if os.path.exists(gifsicle_path):
        print(f"Gifsicle size: {os.path.getsize(gifsicle_path)} bytes")

if __name__ == "__main__":
    test_tool_paths()
    input("Press Enter to exit...")