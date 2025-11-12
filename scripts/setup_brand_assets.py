"""
Setup script for SANGKURIANG brand assets
Copies logo files from frontend to backend static directories
"""

import shutil
import os
from pathlib import Path

def copy_brand_assets():
    """Copy brand assets from frontend to backend and mobile directories"""
    
    # Define source and destination paths
    frontend_logos = Path("r:/SANGKURIANG/frontend/sangkuriang-landing/public")
    backend_static = Path("r:/SANGKURIANG/backend/static/images")
    mobile_assets = Path("r:/SANGKURIANG/mobile/assets/images")
    
    # Create destination directories if they don't exist
    backend_static.mkdir(parents=True, exist_ok=True)
    mobile_assets.mkdir(parents=True, exist_ok=True)
    
    # Source files to copy
    logo_files = [
        "sangkuriang-logo.png",
        "sangkuriang-logo.svg",
        "favicon.ico"
    ]
    
    print("🎨 Setting up SANGKURIANG brand assets...")
    
    # Copy to backend static directory
    print(f"📁 Copying to backend: {backend_static}")
    for logo_file in logo_files:
        src = frontend_logos / logo_file
        dst = backend_static / logo_file
        
        if src.exists():
            shutil.copy2(src, dst)
            print(f"  ✅ {logo_file}")
        else:
            print(f"  ❌ {logo_file} - Source file not found")
    
    # Copy to mobile assets directory
    print(f"\n📱 Copying to mobile: {mobile_assets}")
    for logo_file in logo_files:
        src = frontend_logos / logo_file
        dst = mobile_assets / logo_file
        
        if src.exists():
            shutil.copy2(src, dst)
            print(f"  ✅ {logo_file}")
        else:
            print(f"  ❌ {logo_file} - Source file not found")
    
    # Create different sizes for backend (using PIL if available)
    try:
        from PIL import Image
        create_resized_logos(backend_static)
        print("\n📏 Created resized logo variants")
    except ImportError:
        print("\n⚠️  PIL not available - skipping resized logos")
    
    print("\n🎉 Brand assets setup complete!")

def create_resized_logos(output_dir: Path):
    """Create different size variants of the logo"""
    
    try:
        from PIL import Image
        
        # Load the main PNG logo
        main_logo = output_dir / "sangkuriang-logo.png"
        if not main_logo.exists():
            print("  ❌ Main logo not found for resizing")
            return
        
        with Image.open(main_logo) as img:
            # Define sizes
            sizes = {
                "small": (64, 64),
                "medium": (128, 128),
                "large": (256, 256),
                "xl": (512, 512)
            }
            
            for size_name, dimensions in sizes.items():
                resized = img.resize(dimensions, Image.Resampling.LANCZOS)
                output_file = output_dir / f"sangkuriang-logo-{size_name}.png"
                resized.save(output_file, "PNG")
                print(f"  ✅ Created {size_name} ({dimensions[0]}x{dimensions[1]})")
                
    except Exception as e:
        print(f"  ❌ Error creating resized logos: {e}")

if __name__ == "__main__":
    copy_brand_assets()