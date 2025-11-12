# SANGKURIANG Static Images

## 📁 Directory Structure

```
static/
└── images/
    ├── sangkuriang-logo.png      # Logo utama format PNG
    ├── sangkuriang-logo.svg      # Logo format SVG (vector)
    ├── sangkuriang-logo-small.png    # Logo kecil (64x64)
    ├── sangkuriang-logo-medium.png   # Logo sedang (128x128)
    ├── sangkuriang-logo-large.png    # Logo besar (256x256)
    ├── sangkuriang-logo-xl.png       # Logo ekstra besar (512x512)
    ├── favicon.ico               # Favicon untuk web
    └── brand-colors.css          # CSS untuk warna brand
```

## 🎨 Logo Specifications

### PNG Format
- **Resolution**: Multiple sizes (64x64, 128x128, 256x256, 512x512)
- **Background**: Transparent
- **Color**: Full color
- **Usage**: Email templates, PDF reports, API responses

### SVG Format
- **Type**: Vector graphics
- **Scalable**: Infinite scaling without quality loss
- **Usage**: High-resolution displays, print materials

### Favicon
- **Format**: ICO (multi-size)
- **Sizes**: 16x16, 32x32, 48x48
- **Usage**: Browser tabs, bookmarks

## 🚀 Implementation Guide

### Flask/Django Static Files
```python
# app.py (Flask)
from flask import Flask, send_from_directory

app = Flask(__name__, static_folder='static')

@app.route('/static/images/<path:filename>')
def serve_image(filename):
    return send_from_directory('static/images', filename)

# settings.py (Django)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
```

### Email Template
```html
<!-- email-template.html -->
<!DOCTYPE html>
<html>
<head>
    <style>
        .brand-header {
            background-color: #FF0000;
            padding: 20px;
            text-align: center;
        }
        .brand-logo {
            max-width: 200px;
            height: auto;
        }
    </style>
</head>
<body>
    <div class="brand-header">
        <img src="{{ logo_url }}" alt="SANGKURIANG Logo" class="brand-logo">
    </div>
    <!-- Email content -->
</body>
</html>
```

### PDF Report
```python
# report_generator.py
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Image, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def generate_pdf_report():
    doc = SimpleDocTemplate("report.pdf", pagesize=letter)
    story = []
    
    # Add logo
    logo_path = "static/images/sangkuriang-logo-large.png"
    logo = Image(logo_path, width=200, height=67)
    story.append(logo)
    story.append(Spacer(1, 20))
    
    # Add content
    styles = getSampleStyleSheet()
    story.append(Paragraph("SANGKURIANG Report", styles['Title']))
    
    doc.build(story)
```

### API Response
```python
# api.py
from flask import jsonify
from config.brand_config import SangkuriangBrand, API_BRAND_CONFIG

@app.route('/api/brand-config')
def get_brand_config():
    config = SangkuriangBrand.get_brand_guidelines()
    return jsonify(config)

@app.route('/api/logo/<size>')
def get_logo(size):
    logo_path = SangkuriangBrand.get_logo_path("backend", LogoFormat.PNG, LogoSize(size))
    return send_file(logo_path, mimetype='image/png')
```

## 🎨 Brand Colors

### Primary Colors
- **Merah Indonesia**: `#FF0000` (RGB: 255, 0, 0)
- **Putih**: `#FFFFFF` (RGB: 255, 255, 255)

### Secondary Colors
- **Merah Tua**: `#CC0000` (RGB: 204, 0, 0)
- **Abu-abu Muda**: `#F5F5F5` (RGB: 245, 245, 245)
- **Hitam Teks**: `#333333` (RGB: 51, 51, 51)

### Accent Colors
- **Emas**: `#FFD700` (RGB: 255, 215, 0)
- **Batik Shadow**: `#8B4513` (RGB: 139, 69, 19)

## 📏 Size Guidelines

### Email Headers
- **Recommended**: 200-300px width
- **File**: `sangkuriang-logo-large.png`

### PDF Reports
- **Recommended**: 150-250px width
- **File**: `sangkuriang-logo.svg` (for best quality)

### API Responses
- **Small**: `sangkuriang-logo-small.png` (64x64)
- **Medium**: `sangkuriang-logo-medium.png` (128x128)
- **Large**: `sangkuriang-logo-large.png` (256x256)

### Web Templates
- **Favicon**: `favicon.ico`
- **Header**: `sangkuriang-logo.svg`
- **Footer**: `sangkuriang-logo-small.png`

## 🚫 Usage Guidelines

### Don'ts
- ❌ Don't stretch or distort the logo
- ❌ Don't change the logo colors
- ❌ Don't use on busy backgrounds
- ❌ Don't add drop shadows or effects
- ❌ Don't rotate or flip the logo

### Do's
- ✅ Do maintain aspect ratio
- ✅ Do use appropriate sizes
- ✅ Do use on contrasting backgrounds
- ✅ Do use the correct file format
- ✅ Do follow brand color guidelines

## 🔧 Maintenance

### File Naming Convention
```
sangkuriang-logo-[size].[ext]
sangkuriang-logo-[version]-[variant].[ext]
```

### Version Control
- Keep original files in `/docs/brand-assets/`
- Use semantic versioning (v1.0.0)
- Document changes in CHANGELOG.md

### Quality Assurance
- Test on different screen sizes
- Verify transparency in PNG files
- Check SVG scalability
- Validate file sizes for web performance

## 📞 Support

For logo and brand-related questions:
- Email: brand@sangkuriang.id
- Slack: #brand-design-team
- GitHub Issues: Label with "brand"

---

**Last Updated**: 2024-01-01
**Version**: 1.0.0
**Approved By**: SANGKURIANG Core Team