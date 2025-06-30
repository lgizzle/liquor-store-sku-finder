#!/usr/bin/env python3
"""
Test script to verify the minimum resolution filter
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sku_finder import SKUPictureFinder

def test_resolution_filter():
    """Test that images below 600x600 are filtered out"""
    
    finder = SKUPictureFinder(output_dir="./test_images", max_images=3)
    
    # Test with a known UPC that typically has various sized images
    test_sku = "012000161155"  # This was in our previous test results
    
    print(f"Testing resolution filter with SKU: {test_sku}")
    print("Minimum resolution requirement: 600x600 pixels")
    print("-" * 50)
    
    # Search for images
    results = finder.find_images(test_sku)
    
    print(f"Found {len(results)} images that meet minimum resolution requirements")
    
    for result in results:
        if result.local_path and os.path.exists(result.local_path):
            from PIL import Image
            with Image.open(result.local_path) as img:
                width, height = img.size
                print(f"✓ {os.path.basename(result.local_path)}: {width}x{height} pixels from {result.source}")
        else:
            print(f"- {result.title}: No local image (may have been filtered out)")
    
    print("-" * 50)
    print("Test completed! All saved images should be at least 600x600 pixels.")

if __name__ == "__main__":
    test_resolution_filter()
