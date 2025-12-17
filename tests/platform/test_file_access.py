#!/usr/bin/env python3
"""
Test file access in commercial build context
"""

import sys
import os

def test_file_access():
    print("=" * 60)
    print("TESTING FILE ACCESS IN BUNDLED CONTEXT")
    print("=" * 60)
    
    print(f"sys.executable: {sys.executable}")
    print(f"sys.frozen: {getattr(sys, 'frozen', False)}")
    print(f"Current working directory: {os.getcwd()}")
    
    if getattr(sys, 'frozen', False):
        # Running in a PyInstaller bundle
        bundle_dir = sys._MEIPASS
        print(f"Bundle directory (_MEIPASS): {bundle_dir}")
    else:
        # Running in normal Python
        bundle_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"Script directory: {bundle_dir}")
    
    # Test different paths for licenses.json
    test_paths = [
        'licenses.json',
        './licenses.json',
        os.path.join(os.getcwd(), 'licenses.json'),
        os.path.join(bundle_dir, 'licenses.json'),
        os.path.join(os.path.dirname(sys.executable), 'licenses.json') if getattr(sys, 'frozen', False) else None
    ]
    
    print(f"\nTesting different paths for licenses.json:")
    for i, path in enumerate(test_paths):
        if path is None:
            continue
        exists = os.path.exists(path)
        abs_path = os.path.abspath(path)
        print(f"  {i+1}. {path}")
        print(f"     → {abs_path}")
        print(f"     → {'✅ EXISTS' if exists else '❌ NOT FOUND'}")
        if exists and path.endswith('licenses.json'):
            try:
                import json
                with open(path, 'r') as f:
                    data = json.load(f)
                print(f"     → Contains {len(data)} licenses")
            except Exception as e:
                print(f"     → ❌ Error reading: {e}")
    
    # Test what files are actually available in the working directory
    print(f"\nFiles in current working directory:")
    try:
        files = os.listdir(os.getcwd())
        json_files = [f for f in files if f.endswith('.json')]
        if json_files:
            print(f"  JSON files: {json_files}")
        else:
            print(f"  No JSON files found")
        print(f"  Total files: {len(files)}")
    except Exception as e:
        print(f"  ❌ Error listing files: {e}")

if __name__ == "__main__":
    test_file_access()