#!/usr/bin/env python3
"""Test script for brand utilities"""

import sys
import os
sys.path.append('.')

from utils.brand_utils import (
    get_brand_config, 
    get_available_logos, 
    get_logo_path,
    validate_logo_file
)

def test_brand_utils():
    """Test all brand utility functions"""
    print("🎨 Testing SANGKURIANG Brand Utilities...")
    
    # Test brand config
    print("\n1. Testing get_brand_config()")
    try:
        config = get_brand_config()
        print(f"   ✅ Brand Name: {config['brand']['name']}")
        print(f"   ✅ Tagline: {config['brand']['tagline']}")
        print(f"   ✅ Available Logo Sizes: {config['logos']['available_sizes']}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test logo paths
    print("\n2. Testing get_logo_path()")
    test_sizes = ['small', 'medium', 'large', 'xl', 'svg', 'favicon']
    for size in test_sizes:
        try:
            path = get_logo_path(size)
            if path:
                print(f"   ✅ {size}: {path}")
            else:
                print(f"   ⚠️  {size}: Not found")
        except Exception as e:
            print(f"   ❌ {size}: Error - {e}")
    
    # Test available logos
    print("\n3. Testing get_available_logos()")
    try:
        logos = get_available_logos()
        for size, url in logos.items():
            print(f"   ✅ {size}: {url}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test logo validation
    print("\n4. Testing validate_logo_file()")
    for size in ['small', 'medium', 'large']:
        try:
            valid = validate_logo_file(size)
            status = "✅" if valid else "❌"
            print(f"   {status} {size}: {'Valid' if valid else 'Invalid'}")
        except Exception as e:
            print(f"   ❌ {size}: Error - {e}")
    
    print("\n🎉 Brand utilities test completed!")

if __name__ == "__main__":
    test_brand_utils()