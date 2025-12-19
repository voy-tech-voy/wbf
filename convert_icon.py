#!/usr/bin/env python3
"""Convert ICO to PNG for MSIX"""
from PIL import Image
import os

ico_path = "client/assets/icons/app_icon.ico"
png_path = "client/assets/icons/app_icon.png"

if os.path.exists(ico_path):
    try:
        # Load ICO and convert to PNG
        img = Image.open(ico_path)
        img.save(png_path, "PNG")
        size = os.path.getsize(png_path)
        print(f"✅ Created {png_path} ({size} bytes)")
    except Exception as e:
        print(f"❌ Error: {e}")
else:
    print(f"❌ Icon file not found: {ico_path}")
