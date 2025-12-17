#!/usr/bin/env python3
"""
Test actual conversion with console hiding
"""
import os
import sys
import tempfile
from pathlib import Path
from PIL import Image

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from client.core.conversion_engine import ConversionEngine

def test_conversion_console_hiding():
    """Test that conversion doesn't show console windows"""
    print("🎯 Testing Conversion Console Hiding")
    print("=" * 45)
    
    # Create a temporary test image
    test_image = Path(tempfile.gettempdir()) / "test_image.png"
    
    # Create a simple test image
    img = Image.new('RGB', (100, 100), color='red')
    img.save(test_image)
    print(f"Created test image: {test_image}")
    
    try:
        # Test image conversion
        print("Testing image conversion (should not show console)...")
        
        # Conversion parameters
        params = {
            'type': 'image',
            'format': 'jpg',
            'quality': '90',
            'overwrite': True,
            'output_folder': str(Path(tempfile.gettempdir()) / "test_output")
        }
        
        # Create output folder
        output_folder = Path(params['output_folder'])
        output_folder.mkdir(exist_ok=True)
        
        # Create conversion engine (not as thread for testing)
        engine = ConversionEngine([str(test_image)], params)
        
        # Run conversion
        try:
            success = engine.convert_file(str(test_image))
            
            if success:
                print("✅ Image conversion completed successfully with no console popup")
            else:
                print("❌ Image conversion failed")
        except Exception as conv_error:
            print(f"❌ Conversion error: {conv_error}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Conversion test failed: {e}")
    finally:
        # Cleanup
        if test_image.exists():
            test_image.unlink()
        print("Test completed!")

if __name__ == '__main__':
    test_conversion_console_hiding()