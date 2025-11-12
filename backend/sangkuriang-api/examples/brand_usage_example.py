"""
Example usage of SANGKURIANG brand utilities in FastAPI
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from utils.brand_utils import (
    get_brand_config,
    get_available_logos,
    get_logo_url,
    validate_logo_file,
    get_brand_colors
)

app = FastAPI()

@app.get("/api/v1/brand/demo")
async def brand_demo():
    """
    Demo endpoint showing brand configuration usage
    """
    try:
        # Get brand configuration
        brand_config = get_brand_config()
        
        # Get available logos
        available_logos = get_available_logos()
        
        # Get brand colors
        brand_colors = get_brand_colors()
        
        # Create demo response
        demo_data = {
            "brand_info": brand_config,
            "available_logos": available_logos,
            "brand_colors": brand_colors,
            "logo_examples": {
                "small": get_logo_url("small"),
                "medium": get_logo_url("medium"),
                "large": get_logo_url("large"),
                "svg": get_logo_url("svg"),
                "favicon": get_logo_url("favicon")
            },
            "validation_status": {
                "small": validate_logo_file("small"),
                "medium": validate_logo_file("medium"),
                "large": validate_logo_file("large"),
                "svg": validate_logo_file("svg"),
                "favicon": validate_logo_file("favicon")
            }
        }
        
        return JSONResponse(content=demo_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating brand demo: {str(e)}")

# Email template with brand colors
EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ brand_config.brand.name }} - {{ subject }}</title>
    <style>
        :root {{
            --sangkuriang-primary-red: #FF0000;
            --sangkuriang-primary-white: #FFFFFF;
            --sangkuriang-secondary-dark-red: #CC0000;
            --sangkuriang-accent-gold: #FFD700;
        }}
        
        .email-container {{
            background-color: var(--sangkuriang-primary-white);
            color: var(--sangkuriang-secondary-dark-red);
            font-family: Arial, sans-serif;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .email-header {{
            background-color: var(--sangkuriang-primary-red);
            color: var(--sangkuriang-primary-white);
            padding: 20px;
            text-align: center;
            border-radius: 8px 8px 0 0;
        }}
        
        .email-logo {{
            max-width: 200px;
            height: auto;
        }}
        
        .email-content {{
            background-color: var(--sangkuriang-primary-white);
            padding: 30px;
            border: 1px solid var(--sangkuriang-secondary-dark-red);
            border-radius: 0 0 8px 8px;
        }}
        
        .email-footer {{
            text-align: center;
            margin-top: 30px;
            padding: 20px;
            background-color: var(--sangkuriang-secondary-dark-red);
            color: var(--sangkuriang-primary-white);
            border-radius: 8px;
        }}
        
        .highlight {{
            color: var(--sangkuriang-accent-gold);
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="email-header">
            <img src="{{ logo_url }}" alt="{{ brand_config.brand.name }} Logo" class="email-logo">
            <h1>{{ brand_config.brand.name }}</h1>
            <p>{{ brand_config.brand.tagline }}</p>
        </div>
        
        <div class="email-content">
            {{ content }}
        </div>
        
        <div class="email-footer">
            <p>© {{ year }} {{ brand_config.brand.name }}. All rights reserved.</p>
            <p class="highlight">{{ brand_config.brand.description }}</p>
        </div>
    </div>
</body>
</html>
"""

def generate_brand_email(subject: str, content: str, logo_size: str = "medium") -> str:
    """
    Generate branded email template
    """
    from datetime import datetime
    
    brand_config = get_brand_config()
    logo_url = get_logo_url(logo_size)
    
    return EMAIL_TEMPLATE.format(
        subject=subject,
        content=content,
        brand_config=brand_config,
        logo_url=logo_url,
        year=datetime.now().year
    )

if __name__ == "__main__":
    # Test the functions
    print("Brand Configuration:")
    print(get_brand_config())
    
    print("\nAvailable Logos:")
    print(get_available_logos())
    
    print("\nBrand Colors:")
    print(get_brand_colors())
    
    print("\nEmail Template Example:")
    email = generate_brand_email(
        "Welcome to SANGKURIANG",
        "<p>Welcome to our decentralized funding ecosystem!</p>"
    )
    print(f"Email template generated: {len(email)} characters")