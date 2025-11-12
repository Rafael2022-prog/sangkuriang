#!/usr/bin/env python3
"""
Simple test script for SANGKURIANG brand endpoints
"""

import json
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from utils.brand_utils import (
    get_brand_config,
    get_available_logos,
    get_logo_path,
    validate_logo_file,
    get_brand_colors
)

def test_brand_config():
    """Test brand configuration"""
    print("🧪 Testing Brand Configuration...")
    try:
        config = get_brand_config()
        print(f"✅ Brand config retrieved successfully")
        print(f"   Brand Name: {config['brand']['name']}")
        print(f"   Tagline: {config['brand']['tagline']}")
        print(f"   Colors available: {len(config['colors'])}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_available_logos():
    """Test available logos"""
    print("\n🧪 Testing Available Logos...")
    try:
        logos = get_available_logos()
        print(f"✅ Available logos: {list(logos.keys())}")
        for size, url in logos.items():
            print(f"   {size}: {url}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_logo_validation():
    """Test logo file validation"""
    print("\n🧪 Testing Logo Validation...")
    try:
        sizes = ['small', 'medium', 'large', 'xl', 'svg', 'favicon']
        all_valid = True
        for size in sizes:
            is_valid = validate_logo_file(size)
            status = "✅" if is_valid else "❌"
            print(f"   {status} {size}: {'Valid' if is_valid else 'Invalid'}")
            if not is_valid:
                all_valid = False
        return all_valid
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_brand_colors():
    """Test brand colors"""
    print("\n🧪 Testing Brand Colors...")
    try:
        colors = get_brand_colors()
        print(f"✅ Brand colors retrieved")
        for category, color_data in colors.items():
            print(f"   {category.title()}:")
            for name, formats in color_data.items():
                if isinstance(formats, dict):
                    print(f"     {name}: {formats.get('hex', 'N/A')}")
                else:
                    print(f"     {name}: {formats}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 SANGKURIANG Brand Guidelines Test Suite")
    print("=" * 50)
    
    tests = [
        test_brand_config,
        test_available_logos,
        test_logo_validation,
        test_brand_colors,
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ All {total} tests passed!")
        return 0
    else:
        print(f"❌ {total - passed} out of {total} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())