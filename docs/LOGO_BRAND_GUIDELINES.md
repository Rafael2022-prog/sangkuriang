# Panduan Standarisasi Logo dan Ikon SANGKURIANG

## 📋 Ringkasan

Dokumen ini menjelaskan standarisasi penggunaan logo dan ikon SANGKURIANG untuk menjaga konsistensi brand identity di seluruh platform dan aplikasi.

## 🎨 Format Logo yang Tersedia

### 1. Logo Utama
- **File**: `SANGKURIANG-LOGO.jpg` (root directory)
- **Format**: JPG/JPEG
- **Kegunaan**: Dokumen resmi, presentasi, materi cetak
- **Warna**: Full color dengan background

### 2. Logo PNG (Transparan)
- **File**: `frontend/sangkuriang-landing/public/sangkuriang-logo.png`
- **Format**: PNG dengan transparan background
- **Kegunaan**: Web, aplikasi mobile, UI/UX
- **Warna**: Full color tanpa background

### 3. Logo SVG (Vector)
- **File**: `frontend/sangkuriang-landing/public/sangkuriang-logo.svg`
- **Format**: SVG vector
- **Kegunaan**: Web responsive, scaling besar, animasi
- **Warna**: Vector format dengan transparan background

## 📏 Ukuran Standar

### Logo PNG
- **Favicon**: 16x16, 32x32, 48x48 px
- **Small**: 64x64 px
- **Medium**: 128x128 px
- **Large**: 256x256 px
- **Extra Large**: 512x512 px
- **Hero Banner**: 1024x1024 px

### Logo SVG
- **Flexible**: Dapat discaling tanpa batas
- **Minimum**: 16x16 px
- **Recommended**: Gunakan untuk semua ukuran di atas 256px

## 🎯 Implementasi di Aplikasi

### Frontend (Next.js)
```tsx
// Header component
import Image from 'next/image';

export function Header() {
  return (
    <header>
      <Image
        src="/sangkuriang-logo.svg" // Gunakan SVG untuk scalability
        alt="SANGKURIANG Logo"
        width={120}
        height={40}
        priority
        className="h-8 w-auto"
      />
    </header>
  );
}
```

### Mobile (Flutter)
```dart
// pubspec.yaml
flutter:
  assets:
    - assets/images/sangkuriang-logo.png
    - assets/images/sangkuriang-logo.svg

// Usage in widget
Image.asset(
  'assets/images/sangkuriang-logo.png',
  width: 120,
  height: 40,
  fit: BoxFit.contain,
)
```

### Backend/API
```python
# Logo configuration for email templates, reports, etc.
LOGO_CONFIG = {
    'email_header': '/static/images/sangkuriang-logo.png',
    'pdf_report': '/static/images/sangkuriang-logo.svg',
    'favicon': '/static/images/favicon.ico'
}
```

## 🎨 Warna Brand SANGKURIANG

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

## 📱 Responsive Guidelines

### Mobile First
- Gunakan logo dengan lebar minimum 80px
- Pastikan logo tetap terbaca di layar kecil
- Gunakan format PNG untuk performa optimal

### Tablet
- Logo width: 100-150px
- Gunakan SVG untuk kualitas tinggi

### Desktop
- Logo width: 120-200px
- Gunakan SVG untuk scalability terbaik

## 🚫 Don'ts

❌ **JANGAN**:
- Merubah warna logo
- Memutar/membalik logo
- Menambah efek bayangan (drop shadow)
- Membesarkan logo melebihi 200% dari ukuran asli (kecuali SVG)
- Menggunakan logo dalam background yang membuatnya tidak terbaca
- Memotong atau merubah proporsi logo

✅ **DO**:
- Gunakan logo dalam warna aslinya
- Pertahankan proporsi aspek ratio
- Gunakan background kontras untuk keterbacaan
- Simpan logo dalam folder yang terstruktur
- Gunakan format yang sesuai dengan kebutuhan

## 📁 Struktur Folder Logo

```
SANGKURIANG/
├── docs/
│   ├── LOGO_BRAND_GUIDELINES.md (ini)
│   └── BRAND_ASSETS/
│       ├── logos/
│       │   ├── sangkuriang-logo-master.jpg
││       │   ├── sangkuriang-logo-transparent.png
││       │   └── sangkuriang-logo-vector.svg
│       ├── icons/
│       │   ├── favicon.ico
││       │   ├── icon-16.png
││       │   ├── icon-32.png
││       │   └── icon-64.png
│       └── colors/
│           └── brand-colors.css
├── frontend/
│   └── sangkuriang-landing/
│       └── public/
│           ├── sangkuriang-logo.png
│           └── sangkuriang-logo.svg
├── mobile/
│   └── assets/
│       └── images/
│           ├── sangkuriang-logo.png
│           └── sangkuriang-logo.svg
└── backend/
    └── static/
        └── images/
            ├── sangkuriang-logo.png
            └── sangkuriang-logo.svg
```

## 🔄 Update dan Maintenance

### Version Control
- Semua perubahan logo harus melalui review tim
- Gunakan semantic versioning untuk logo updates
- Dokumentasikan semua perubahan dalam CHANGELOG

### File Naming Convention
```
sangkuriang-logo-[version]-[variant].[ext]
Contoh:
- sangkuriang-logo-v1-master.png
- sangkuriang-logo-v2-dark-theme.svg
- sangkuriang-logo-v3-mobile-optimized.png
```

## 📞 Contact

Untuk pertanyaan tentang penggunaan logo dan brand guidelines:
- Email: brand@sangkuriang.id
- Slack: #brand-design-team
- Issue Tracker: GitHub Issues dengan label "brand"

---

## ✅ Implementation Checklist

### Backend (Python/FastAPI)
- [x] Brand configuration module (`config/brand_config.py`)
- [x] Static files serving (`static/images/`)
- [x] API endpoints for brand assets (`/api/v1/brand/*`)
- [x] Brand utilities (`sangkuriang-api/utils/brand_utils.py`)

### Frontend (Next.js/React)
- [x] Brand guidelines CSS (`src/styles/brand-guidelines.css`)
- [x] Brand logo component (`src/components/BrandLogo.tsx`)
- [x] CSS variables and utility classes
- [x] Responsive design support

### Mobile (Flutter/Dart)
- [x] Brand configuration (`lib/config/brand_config.dart`)
- [x] Brand logo widget (`lib/widgets/brand_logo_widget.dart`)
- [x] Logo size and variant enums
- [x] Asset declarations in `pubspec.yaml`

### Documentation
- [x] Logo usage guidelines (this file)
- [x] Asset README files
- [x] Implementation examples
- [x] Brand setup script (`scripts/setup_brand_assets.py`)

### Assets
- [x] Logo files copied to all platforms
- [x] Multiple size variants
- [x] SVG and PNG formats
- [x] Favicon support

---

**Last Updated**: $(date +%Y-%m-%d)
**Version**: 1.0.0
**Approved By**: SANGKURIANG Core Team