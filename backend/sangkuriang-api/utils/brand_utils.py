"""
Brand utilities for SANGKURIANG API
Handles brand configuration and logo management
"""

from typing import Dict, Optional, Any
from pathlib import Path
import os
from loguru import logger

# Logo size mapping
LOGO_SIZES = {
    "small": "sangkuriang-logo-small.png",
    "medium": "sangkuriang-logo-medium.png", 
    "large": "sangkuriang-logo-large.png",
    "xl": "sangkuriang-logo-xl.png",
    "svg": "sangkuriang-logo.svg",
    "favicon": "favicon.ico"
}

def get_brand_config() -> Dict[str, Any]:
    """
    Get complete brand configuration
    
    Returns:
        Dict containing brand colors, logo paths, and guidelines
    """
    try:
        config = {
            "brand": {
                "name": "SANGKURIANG",
                "tagline": "Membangun Kriptografi Nusantara, Satu Baris Kode Sekaligus",
                "description": "Ekosistem pendanaan terdesentralisasi khusus untuk proyek kriptografi berbasis Indonesia"
            },
            "colors": {
                "primary": {
                    "red": "#FF0000",
                    "white": "#FFFFFF"
                },
                "secondary": {
                    "dark_red": "#CC0000",
                    "light_gray": "#F5F5F5",
                    "dark_text": "#333333"
                },
                "accent": {
                    "gold": "#FFD700",
                    "batik_shadow": "#8B4513"
                }
            },
            "logos": {
                "available_sizes": list(LOGO_SIZES.keys()),
                "base_url": "/static/images/",
                "formats": ["png", "svg", "ico"]
            },
            "guidelines": {
                "usage": "Maintain aspect ratio, use on contrasting backgrounds",
                "restrictions": "Do not stretch, distort, or change colors",
                "accessibility": "Ensure sufficient contrast ratios for text"
            }
        }
        
        logger.info("Brand configuration retrieved successfully")
        return config
        
    except Exception as e:
        logger.error(f"Error retrieving brand configuration: {e}")
        raise

def get_logo_path(size: str) -> Optional[str]:
    """
    Get logo path by size
    
    Args:
        size: Logo size (small, medium, large, xl, svg, favicon)
        
    Returns:
        Logo filename or None if size not found
    """
    try:
        if size not in LOGO_SIZES:
            logger.warning(f"Logo size '{size}' not found")
            return None
            
        logo_filename = LOGO_SIZES[size]
        logger.info(f"Logo path retrieved for size '{size}': {logo_filename}")
        return logo_filename
        
    except Exception as e:
        logger.error(f"Error getting logo path for size '{size}': {e}")
        return None

def get_logo_url(size: str) -> Optional[str]:
    """
    Get complete logo URL
    
    Args:
        size: Logo size (small, medium, large, xl, svg, favicon)
        
    Returns:
        Complete logo URL or None if size not found
    """
    try:
        logo_path = get_logo_path(size)
        if not logo_path:
            return None
            
        return f"/static/images/{logo_path}"
        
    except Exception as e:
        logger.error(f"Error getting logo URL for size '{size}': {e}")
        return None

def validate_logo_file(size: str) -> bool:
    """
    Validate if logo file exists
    
    Args:
        size: Logo size to validate
        
    Returns:
        True if file exists, False otherwise
    """
    try:
        logo_path = get_logo_path(size)
        if not logo_path:
            return False
            
        # Check if file exists in static directory
        static_path = Path("../static/images") / logo_path
        exists = static_path.exists()
        
        if exists:
            logger.info(f"Logo file validated for size '{size}': {logo_path}")
        else:
            logger.warning(f"Logo file not found for size '{size}': {logo_path}")
            
        return exists
        
    except Exception as e:
        logger.error(f"Error validating logo file for size '{size}': {e}")
        return False

def get_available_logos() -> Dict[str, str]:
    """
    Get all available logos with their URLs
    
    Returns:
        Dict mapping size to URL
    """
    try:
        available = {}
        
        for size in LOGO_SIZES.keys():
            url = get_logo_url(size)
            if url and validate_logo_file(size):
                available[size] = url
                
        logger.info(f"Available logos retrieved: {list(available.keys())}")
        return available
        
    except Exception as e:
        logger.error(f"Error getting available logos: {e}")
        return {}

def get_brand_colors() -> Dict[str, Any]:
    """
    Get brand colors in different formats
    
    Returns:
        Dict containing colors in hex, rgb, and hsl formats
    """
    try:
        colors = {
            "primary": {
                "red": {
                    "hex": "#FF0000",
                    "rgb": "rgb(255, 0, 0)",
                    "hsl": "hsl(0, 100%, 50%)"
                },
                "white": {
                    "hex": "#FFFFFF",
                    "rgb": "rgb(255, 255, 255)",
                    "hsl": "hsl(0, 0%, 100%)"
                }
            },
            "secondary": {
                "dark_red": {
                    "hex": "#CC0000",
                    "rgb": "rgb(204, 0, 0)",
                    "hsl": "hsl(0, 100%, 40%)"
                },
                "light_gray": {
                    "hex": "#F5F5F5",
                    "rgb": "rgb(245, 245, 245)",
                    "hsl": "hsl(0, 0%, 96%)"
                },
                "dark_text": {
                    "hex": "#333333",
                    "rgb": "rgb(51, 51, 51)",
                    "hsl": "hsl(0, 0%, 20%)"
                }
            },
            "accent": {
                "gold": {
                    "hex": "#FFD700",
                    "rgb": "rgb(255, 215, 0)",
                    "hsl": "hsl(51, 100%, 50%)"
                },
                "batik_shadow": {
                    "hex": "#8B4513",
                    "rgb": "rgb(139, 69, 19)",
                    "hsl": "hsl(25, 76%, 31%)"
                }
            }
        }
        
        logger.info("Brand colors retrieved successfully")
        return colors
        
    except Exception as e:
        logger.error(f"Error retrieving brand colors: {e}")
        raise

def get_brand_css_variables() -> str:
    """
    Get CSS variables for brand colors
    
    Returns:
        CSS string with brand variables
    """
    try:
        css_vars = """
:root {
  /* Primary Colors */
  --sangkuriang-red: #FF0000;
  --sangkuriang-white: #FFFFFF;
  
  /* Secondary Colors */
  --sangkuriang-dark-red: #CC0000;
  --sangkuriang-light-gray: #F5F5F5;
  --sangkuriang-dark-text: #333333;
  
  /* Accent Colors */
  --sangkuriang-gold: #FFD700;
  --sangkuriang-batik-shadow: #8B4513;
  
  /* Logo Sizes */
  --sangkuriang-logo-small: 64px;
  --sangkuriang-logo-medium: 128px;
  --sangkuriang-logo-large: 256px;
  --sangkuriang-logo-xl: 512px;
}
"""
        
        logger.info("Brand CSS variables generated successfully")
        return css_vars
        
    except Exception as e:
        logger.error(f"Error generating brand CSS variables: {e}")
        raise