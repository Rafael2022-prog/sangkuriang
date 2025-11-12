# SANGKURIANG Logo Assets

## 📁 File Structure

```
assets/
└── images/
    ├── sangkuriang-logo.png      # Logo utama format PNG
    ├── sangkuriang-logo.svg      # Logo format SVG (vector)
    ├── icon-16.png               # Icon kecil (16x16)
    ├── icon-32.png               # Icon sedang (32x32)
    ├── icon-64.png               # Icon besar (64x64)
    └── favicon.ico               # Favicon untuk web
```

## 🎨 Logo Specifications

### PNG Format
- **Resolution**: 1024x1024px (master)
- **Background**: Transparent
- **Color**: Full color
- **Usage**: UI components, app bar, splash screen

### SVG Format
- **Type**: Vector graphics
- **Scalable**: Infinite scaling without quality loss
- **Usage**: Large displays, print materials

### Icon Sizes
- **16x16**: Small icons, favicon
- **32x32**: Standard icons
- **64x64**: Large icons, profile pictures

## 📱 Implementation Guide

### pubspec.yaml Configuration
```yaml
flutter:
  assets:
    - assets/images/sangkuriang-logo.png
    - assets/images/sangkuriang-logo.svg
    - assets/images/icon-16.png
    - assets/images/icon-32.png
    - assets/images/icon-64.png
    - assets/images/favicon.ico
```

### Usage Examples

#### Logo Widget
```dart
import 'package:flutter/material.dart';
import '../config/brand_config.dart';

class LogoWidget extends StatelessWidget {
  final double size;
  final bool useSvg;
  
  const LogoWidget({
    Key? key,
    this.size = 128.0,
    this.useSvg = false,
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return SangkuriangBrand.logoWidget(
      size: size,
      useSvg: useSvg,
    );
  }
}
```

#### Icon Widget
```dart
class IconWidget extends StatelessWidget {
  final double size;
  
  const IconWidget({
    Key? key,
    this.size = 32.0,
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    String iconPath;
    
    if (size <= 16) {
      iconPath = 'assets/images/icon-16.png';
    } else if (size <= 32) {
      iconPath = 'assets/images/icon-32.png';
    } else {
      iconPath = 'assets/images/icon-64.png';
    }
    
    return Image.asset(
      iconPath,
      width: size,
      height: size,
      fit: BoxFit.contain,
    );
  }
}
```

#### Splash Screen
```dart
class SplashScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: SangkuriangBrand.primaryRed,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            SangkuriangBrand.logoWidget(size: 256.0),
            const SizedBox(height: 32.0),
            CircularProgressIndicator(
              color: SangkuriangBrand.primaryWhite,
            ),
          ],
        ),
      ),
    );
  }
}
```

## 🎨 Brand Guidelines

### Color Usage
- **Primary**: Merah Indonesia (#FF0000)
- **Secondary**: Putih (#FFFFFF)
- **Accent**: Emas (#FFD700)
- **Text**: Abu-abu gelap (#333333)

### Size Guidelines
- **Small**: 32-64px (icons, buttons)
- **Medium**: 128-256px (headers, cards)
- **Large**: 512px+ (splash screens, heroes)

### Don'ts
- ❌ Don't stretch or distort the logo
- ❌ Don't change the logo colors
- ❌ Don't use on busy backgrounds
- ❌ Don't rotate or flip the logo
- ❌ Don't add drop shadows or effects

### Do's
- ✅ Do maintain aspect ratio
- ✅ Do use appropriate sizes
- ✅ Do use on contrasting backgrounds
- ✅ Do use the correct file format
- ✅ Do follow brand color guidelines

## 📋 Asset Checklist

- [ ] sangkuriang-logo.png (1024x1024)
- [ ] sangkuriang-logo.svg (vector)
- [ ] icon-16.png (16x16)
- [ ] icon-32.png (32x32)
- [ ] icon-64.png (64x64)
- [ ] favicon.ico (multi-size)

## 🔧 Maintenance

### File Naming Convention
```
sangkuriang-logo-[version]-[variant].[ext]
sangkuriang-icon-[size]x[size].[ext]
```

### Version Control
- Keep original files in `/docs/brand-assets/`
- Use semantic versioning (v1.0.0)
- Document changes in CHANGELOG.md

### Quality Assurance
- Test on different screen sizes
- Verify transparency in PNG files
- Check SVG scalability
- Validate icon sharpness

---

**Last Updated**: 2024-01-01
**Version**: 1.0.0
**Approved By**: SANGKURIANG Design Team