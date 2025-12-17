#!/usr/bin/env python3

import sys
import os

def test_paths():
    print("=== Path Testing ===")
    print(f"sys.executable: {sys.executable}")
    
    if hasattr(sys, '_MEIPASS'):
        print(f"sys._MEIPASS: {sys._MEIPASS}")
        print(f"sys._MEIPASS exists: {os.path.exists(sys._MEIPASS)}")
        
        # List contents of _MEIPASS
        if os.path.exists(sys._MEIPASS):
            print(f"Contents of sys._MEIPASS:")
            for item in os.listdir(sys._MEIPASS):
                path = os.path.join(sys._MEIPASS, item)
                if os.path.isdir(path):
                    print(f"  [DIR] {item}")
                else:
                    print(f"  [FILE] {item}")
            
            # Check for bundled_tools specifically
            bundled_tools_path = os.path.join(sys._MEIPASS, 'tools')
            print(f"bundled_tools path: {bundled_tools_path}")
            print(f"bundled_tools exists: {os.path.exists(bundled_tools_path)}")
            
            if os.path.exists(bundled_tools_path):
                print("Contents of bundled_tools:")
                for item in os.listdir(bundled_tools_path):
                    path = os.path.join(bundled_tools_path, item)
                    size = os.path.getsize(path) if os.path.isfile(path) else 0
                    print(f"  {item}: {size} bytes")
    else:
        print("sys._MEIPASS not found (running from source)")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Script directory: {os.path.dirname(os.path.abspath(__file__))}")

if __name__ == "__main__":
    test_paths()
    input("Press Enter to exit...")