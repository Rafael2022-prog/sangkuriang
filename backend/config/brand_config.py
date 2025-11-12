"""
SANGKURIANG Brand Configuration for Python Backend
Standarisasi warna dan logo untuk aplikasi backend
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum


class LogoFormat(Enum):
    """Logo format enumeration"""
    PNG = "png"
    SVG = "svg"
    JPG = "jpg"
    ICO = "ico"


class LogoSize(Enum):
    """Logo size enumeration"""
    FAVICON = "favicon"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    XL = "xl"
    HERO = "hero"


@dataclass
class BrandColor:
    """Brand color data class"""
    hex: str
    rgb: Tuple[int, int, int]
    rgba: Tuple[int, int, int, float]
    hsl: Tuple[float, float, float]
    
    def to_css(self) -> str:
        """Convert to CSS color format"""
        return self.hex
    
    def to_rgb_string(self) -> str:
        """Convert to RGB string format"""
        return f"rgb({self.rgb[0]}, {self.rgb[1]}, {self.rgb[2]})"
    
    def to_rgba_string(self, alpha: Optional[float] = None) -> str:
        """Convert to RGBA string format"""
        a = alpha if alpha is not None else self.rgba[3]
        return f"rgba({self.rgb[0]}, {self.rgb[1]}, {self.rgb[2]}, {a})"


class SangkuriangBrand:
    """SANGKURIANG Brand Configuration"""
    
    # Primary Colors - Merah-Putih Indonesia
    PRIMARY_RED = BrandColor(
        hex="#FF0000",
        rgb=(255, 0, 0),
        rgba=(255, 0, 0, 1.0),
        hsl=(0, 100, 50)
    )
    
    PRIMARY_WHITE = BrandColor(
        hex="#FFFFFF",
        rgb=(255, 255, 255),
        rgba=(255, 255, 255, 1.0),
        hsl=(0, 0, 100)
    )
    
    # Secondary Colors
    SECONDARY_RED_DARK = BrandColor(
        hex="#CC0000",
        rgb=(204, 0, 0),
        rgba=(204, 0, 0, 1.0),
        hsl=(0, 100, 40)
    )
    
    SECONDARY_GRAY_LIGHT = BrandColor(
        hex="#F5F5F5",
        rgb=(245, 245, 245),
        rgba=(245, 245, 245, 1.0),
        hsl=(0, 0, 96)
    )
    
    SECONDARY_TEXT_DARK = BrandColor(
        hex="#333333",
        rgb=(51, 51, 51),
        rgba=(51, 51, 51, 1.0),
        hsl=(0, 0, 20)
    )
    
    # Accent Colors
    ACCENT_GOLD = BrandColor(
        hex="#FFD700",
        rgb=(255, 215, 0),
        rgba=(255, 215, 0, 1.0),
        hsl=(51, 100, 50)
    )
    
    ACCENT_BATIK_SHADOW = BrandColor(
        hex="#8B4513",
        rgb=(139, 69, 19),
        rgba=(139, 69, 19, 1.0),
        hsl=(25, 76, 31)
    )
    
    # Logo Configuration
    LOGO_CONFIG = {
        "base_path": "static/images",
        "formats": {
            LogoFormat.PNG: {
                "extension": ".png",
                "mime_type": "image/png",
                "transparent": True,
                "sizes": {
                    LogoSize.FAVICON: (16, 16),
                    LogoSize.SMALL: (64, 64),
                    LogoSize.MEDIUM: (128, 128),
                    LogoSize.LARGE: (256, 256),
                    LogoSize.XL: (512, 512),
                    LogoSize.HERO: (1024, 1024),
                }
            },
            LogoFormat.SVG: {
                "extension": ".svg",
                "mime_type": "image/svg+xml",
                "transparent": True,
                "scalable": True,
            },
            LogoFormat.JPG: {
                "extension": ".jpg",
                "mime_type": "image/jpeg",
                "transparent": False,
                "sizes": {
                    LogoSize.MEDIUM: (128, 128),
                    LogoSize.LARGE: (256, 256),
                    LogoSize.XL: (512, 512),
                }
            }
        }
    }
    
    # File Paths
    LOGO_PATHS = {
        "root_jpg": "SANGKURIANG-LOGO.jpg",
        "frontend_png": "frontend/sangkuriang-landing/public/sangkuriang-logo.png",
        "frontend_svg": "frontend/sangkuriang-landing/public/sangkuriang-logo.svg",
        "mobile_png": "mobile/assets/images/sangkuriang-logo.png",
        "mobile_svg": "mobile/assets/images/sangkuriang-logo.svg",
        "backend_png": "backend/static/images/sangkuriang-logo.png",
        "backend_svg": "backend/static/images/sangkuriang-logo.svg",
    }
    
    @classmethod
    def get_color_palette(cls) -> Dict[str, BrandColor]:
        """Get complete color palette"""
        return {
            "primary_red": cls.PRIMARY_RED,
            "primary_white": cls.PRIMARY_WHITE,
            "secondary_red_dark": cls.SECONDARY_RED_DARK,
            "secondary_gray_light": cls.SECONDARY_GRAY_LIGHT,
            "secondary_text_dark": cls.SECONDARY_TEXT_DARK,
            "accent_gold": cls.ACCENT_GOLD,
            "accent_batik_shadow": cls.ACCENT_BATIK_SHADOW,
        }
    
    @classmethod
    def get_logo_path(cls, location: str, format: LogoFormat, size: Optional[LogoSize] = None) -> str:
        """Get logo path based on location, format, and size"""
        base_paths = {
            "root": "",
            "frontend": "frontend/sangkuriang-landing/public",
            "mobile": "mobile/assets/images",
            "backend": "backend/static/images",
        }
        
        base_path = base_paths.get(location, "backend/static/images")
        
        if format == LogoFormat.PNG:
            filename = f"sangkuriang-logo-{size.value if size else 'medium'}.png"
        elif format == LogoFormat.SVG:
            filename = "sangkuriang-logo.svg"
        elif format == LogoFormat.JPG:
            filename = f"sangkuriang-logo-{size.value if size else 'large'}.jpg"
        else:
            filename = "sangkuriang-logo.png"
        
        return f"{base_path}/{filename}"
    
    @classmethod
    def get_css_variables(cls) -> str:
        """Generate CSS variables for brand colors"""
        colors = cls.get_color_palette()
        css_vars = []
        
        for name, color in colors.items():
            css_name = f"--sangkuriang-{name.replace('_', '-')}"
            css_vars.append(f"{css_name}: {color.hex};")
        
        return "\n".join(css_vars)
    
    @classmethod
    def get_gradient_css(cls, gradient_type: str = "primary") -> str:
        """Generate gradient CSS"""
        if gradient_type == "primary":
            return f"linear-gradient(135deg, {cls.PRIMARY_RED.hex} 0%, {cls.SECONDARY_RED_DARK.hex} 100%)"
        elif gradient_type == "accent":
            return f"linear-gradient(135deg, {cls.ACCENT_GOLD.hex} 0%, {cls.PRIMARY_RED.hex} 100%)"
        elif gradient_type == "batik":
            return f"linear-gradient(45deg, {cls.ACCENT_BATIK_SHADOW.hex} 0%, {cls.ACCENT_GOLD.hex} 50%, {cls.PRIMARY_RED.hex} 100%)"
        else:
            return f"linear-gradient(135deg, {cls.PRIMARY_RED.hex} 0%, {cls.SECONDARY_RED_DARK.hex} 100%)"
    
    @classmethod
    def validate_logo_usage(cls, background_color: str, logo_format: LogoFormat) -> bool:
        """Validate logo usage based on background color and format"""
        # Convert hex to RGB for comparison
        bg_rgb = cls._hex_to_rgb(background_color)
        
        # Check contrast ratio
        if logo_format == LogoFormat.PNG:
            # PNG has transparent background, good for most backgrounds
            return True
        elif logo_format == LogoFormat.JPG:
            # JPG doesn't support transparency, check background contrast
            white_contrast = cls._calculate_contrast(bg_rgb, (255, 255, 255))
            if white_contrast < 4.5:  # WCAG AA standard
                return False
        
        return True
    
    @classmethod
    def _hex_to_rgb(cls, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    @classmethod
    def _calculate_contrast(cls, color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> float:
        """Calculate contrast ratio between two colors"""
        def get_luminance(rgb: Tuple[int, int, int]) -> float:
            r, g, b = [x / 255.0 for x in rgb]
            r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
            g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
            b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
            return 0.2126 * r + 0.7152 * g + 0.0722 * b
        
        l1 = get_luminance(color1)
        l2 = get_luminance(color2)
        
        lighter = max(l1, l2)
        darker = min(l1, l2)
        
        return (lighter + 0.05) / (darker + 0.05)
    
    @classmethod
    def get_brand_guidelines(cls) -> Dict:
        """Get complete brand guidelines"""
        return {
            "colors": cls.get_color_palette(),
            "logo_config": cls.LOGO_CONFIG,
            "logo_paths": cls.LOGO_PATHS,
            "css_variables": cls.get_css_variables(),
            "gradients": {
                "primary": cls.get_gradient_css("primary"),
                "accent": cls.get_gradient_css("accent"),
                "batik": cls.get_gradient_css("batik"),
            },
            "recommendations": {
                "primary_logo_format": LogoFormat.PNG,
                "scalable_logo_format": LogoFormat.SVG,
                "print_logo_format": LogoFormat.JPG,
                "favicon_format": LogoFormat.PNG,
            }
        }


# Email Template Brand Configuration
EMAIL_BRAND_CONFIG = {
    "logo_url": "/static/images/sangkuriang-logo-large.png",
    "primary_color": SangkuriangBrand.PRIMARY_RED.hex,
    "secondary_color": SangkuriangBrand.SECONDARY_GRAY_LIGHT.hex,
    "accent_color": SangkuriangBrand.ACCENT_GOLD.hex,
    "font_family": "Arial, sans-serif",
    "font_size": "14px",
    "line_height": "1.6",
}

# PDF Report Brand Configuration
PDF_BRAND_CONFIG = {
    "logo_path": "backend/static/images/sangkuriang-logo.svg",
    "primary_color": SangkuriangBrand.PRIMARY_RED.hex,
    "secondary_color": SangkuriangBrand.SECONDARY_TEXT_DARK.hex,
    "accent_color": SangkuriangBrand.ACCENT_GOLD.hex,
    "font_family": "Helvetica",
    "font_size": 12,
    "margin": 72,  # 1 inch in points
}

# API Response Brand Configuration
API_BRAND_CONFIG = {
    "logo_base64": None,  # Will be loaded from file
    "primary_color": SangkuriangBrand.PRIMARY_RED.hex,
    "secondary_color": SangkuriangBrand.SECONDARY_TEXT_DARK.hex,
    "accent_color": SangkuriangBrand.ACCENT_GOLD.hex,
    "brand_name": "SANGKURIANG",
    "tagline": "Membangun Kriptografi Nusantara, Satu Baris Kode Sekaligus",
}


def load_logo_base64(logo_path: str) -> str:
    """Load logo and convert to base64 for API responses"""
    import base64
    
    try:
        with open(logo_path, "rb") as logo_file:
            logo_data = logo_file.read()
            return base64.b64encode(logo_data).decode('utf-8')
    except FileNotFoundError:
        return ""


def get_brand_config_for_template(template_type: str) -> Dict:
    """Get brand configuration for specific template type"""
    configs = {
        "email": EMAIL_BRAND_CONFIG,
        "pdf": PDF_BRAND_CONFIG,
        "api": API_BRAND_CONFIG,
    }
    
    config = configs.get(template_type, API_BRAND_CONFIG)
    
    # Load logo base64 for API config if not already loaded
    if template_type == "api" and not config["logo_base64"]:
        try:
            logo_path = SangkuriangBrand.LOGO_PATHS["backend_png"]
            config["logo_base64"] = load_logo_base64(logo_path)
        except:
            config["logo_base64"] = ""
    
    return config