# 🏔️ SANGKURIANG

> *Platform Pendanaan Terdesentralisasi untuk Proyek Kriptografi Indonesia*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Flutter](https://img.shields.io/badge/Flutter-3.16+-blue.svg)](https://flutter.dev)
[![Python](https://img.shields.io/badge/Python-3.8+-3776AB.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com)

## 📋 Table of Contents

- [Tentang SANGKURIANG](#tentang-sangkuriang)
- [Fitur Utama](#fitur-utama)
- [Arsitektur](#arsitektur)
- [Instalasi](#instalasi)
- [Penggunaan](#penggunaan)
- [API Documentation](#api-documentation)
- [Kontribusi](#kontribusi)
- [Roadmap](#roadmap)
- [Lisensi](#lisensi)
- [Kontak](#kontak)

## 🏔️ Tentang SANGKURIANG

SANGKURIANG adalah platform pendanaan terdesentralisasi pertama di Indonesia yang khusus dirancang untuk mendukung proyek-proyek kriptografi lokal. Nama ini terinspirasi dari legenda Sangkuriang yang melambangkan ketekunan, ambisi besar, dan kemampuan menciptakan sesuatu yang tampak mustahil - nilai-nilai yang sesuai dengan semangat developer kriptografi Indonesia.

### 🎯 Visi
Menjadi platform pendanaan kriptografi terdepan di Asia Tenggara yang mendukung inovasi lokal dan menciptakan ekosistem yang berkelanjutan.

### 🚀 Misi
- Menyediakan akses pendanaan yang adil untuk semua developer Indonesia
- Membangun sistem audit keamanan yang dapat diandalkan
- Menciptakan komunitas yang kolaboratif dan inklusif
- Mendorong adopsi kriptografi lokal dalam skala global

## ✨ Fitur Utama

### 🔐 Sistem Pendanaan Terdesentralisasi
- **Crowdfunding Model**: All-or-nothing dan Keep-what-you-raise
- **Multi-Payment Support**: Bank transfer, e-wallet (OVO, GoPay, Dana), kartu kredit
- **Milestone-Based Funding**: Pencairan dana berdasarkan pencapaian target
- **Transparent Tracking**: Transparansi penuh aliran dana

### 🛡️ Audit Keamanan Otomatis
- **Cryptographic Analysis**: Analisis kekuatan algoritma kriptografi
- **Quantum Resistance Testing**: Evaluasi ketahanan terhadap serangan kuantum
- **Implementation Review**: Review kode untuk kerentanan keamanan
- **Performance Testing**: Pengujian efisiensi komputasi
- **Badge System**: Sistem lencana keamanan (Platinum, Gold, Silver, Bronze)

### 📱 Aplikasi Mobile Native
- **Cross-Platform**: Android dan iOS dengan Flutter
- **Indonesian UI/UX**: Desain dengan elemen budaya Indonesia (batik, warna merah-putih)
- **Offline Support**: Fitur offline dengan sinkronisasi otomatis
- **Biometric Security**: Autentikasi biometrik untuk keamanan tambahan

### 🤝 Komunitas dan Governance
- **Decentralized Governance**: Sistem voting untuk keputusan komunitas
- **Reputation System**: Sistem reputasi untuk developer dan backer
- **Educational Resources**: Kursus, workshop, dan sertifikasi
- **Community Events**: Hackathon, meetup, dan konferensi

### 🔧 Developer Tools
- **Open Source**: Semua kode tersedia di GitHub
- **API Integration**: RESTful API dengan dokumentasi lengkap
- **SDK Support**: SDK untuk berbagai bahasa pemrograman
- **Testing Environment**: Sandbox environment untuk testing

## 🏗️ Arsitektur

```
┌─────────────────────────────────────────────────────────────┐
│                    Mobile Layer                            │
│              Flutter (Android & iOS)                        │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                    API Gateway                              │
│                  FastAPI (Python)                           │
├─────────────────────┬───────────────────────────────────────┤
│                     │                                       │
┌───────────────▼────┴────▼───────────────▼───────────────┐
│Auth│Project│Audit│Payment│Notification│Analytics│Services│
└───────────────┬───────────────┬───────────────┬───────────┘
                │               │               │
┌───────────────▼───────▼────────▼───────▼──────────────────┐
│              Infrastructure Layer                          │
│        PostgreSQL + Redis + Cloud Storage                  │
│        Docker + Kubernetes + CI/CD Pipeline               │
└─────────────────────────────────────────────────────────────┘
```

### 🛠️ Teknologi yang Digunakan

#### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL, Redis
- **Authentication**: JWT with refresh tokens
- **Payment**: Midtrans, Xendit, OVO, GoPay, Dana
- **Security**: Argon2, cryptography, python-jose
- **Testing**: pytest, pytest-asyncio

#### Mobile
- **Framework**: Flutter 3.16+
- **State Management**: Provider
- **Storage**: SharedPreferences, flutter_secure_storage
- **Networking**: HTTP, Dio
- **UI Components**: Material Design, custom Indonesian theme
- **Testing**: flutter_test, integration_test

#### DevOps & Infrastructure
- **Container**: Docker, Docker Compose
- **Orchestration**: Kubernetes (production)
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus, Grafana
- **Cloud**: AWS/GCP/Azure ready

## 🚀 Instalasi

### 📋 Prasyarat

- Python 3.8+
- Node.js 16+
- Flutter 3.16+
- PostgreSQL 12+
- Redis 6+
- Docker & Docker Compose (opsional)

### 🔧 Instalasi Cepat

#### 1. Clone Repository
```bash
git clone https://github.com/sangkuriang/sangkuriang.git
cd sangkuriang
```

#### 2. Setup Environment
```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

#### 3. Install Dependencies
```bash
# Backend dependencies
cd backend/sangkuriang-api
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Mobile dependencies
cd ../../mobile
flutter pub get
```

#### 4. Setup Database
```bash
# Run database migrations
cd backend/sangkuriang-api
alembic upgrade head
```

#### 5. Jalankan Aplikasi
```bash
# Backend server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Mobile app (di terminal terpisah)
cd mobile
flutter run
```

### 🐳 Instalasi dengan Docker

```bash
# Build dan jalankan semua services
docker-compose up -d

# Cek status
docker-compose ps

# Logs
docker-compose logs -f
```

## 📖 Penggunaan

### 🌐 Web Dashboard
Akses dashboard admin di `http://localhost:8000/admin`

Default credentials:
- Username: `admin@sangkuriang.id`
- Password: `admin123`

### 📱 Mobile App
1. Install aplikasi di device/emulator
2. Daftar akun baru atau login
3. Jelajahi proyek yang tersedia
4. Lakukan pendanaan atau ajukan audit
5. Monitor progress dan hasil

### 🔗 API Integration
```python
import requests

# Login
response = requests.post('http://localhost:8000/api/v1/auth/login', json={
    'email': 'user@example.com',
    'password': 'password123'
})
token = response.json()['access_token']

# Get projects
headers = {'Authorization': f'Bearer {token}'}
projects = requests.get('http://localhost:8000/api/v1/projects', headers=headers)
print(projects.json())
```

## 📚 Dokumentasi

- [📖 Whitepaper](docs/WHITEPAPER.md) - Dokumen teknis dan visi proyek
- [🔌 API Documentation](docs/API_DOCUMENTATION.md) - Panduan integrasi API
- [📱 Flutter Integration Guide](docs/FLUTTER_INTEGRATION_GUIDE.md) - Panduan integrasi Flutter
- [🚀 Deployment Guide](docs/DEPLOYMENT.md) - Panduan deployment production
- [🧪 Testing Guide](docs/TESTING.md) - Panduan testing dan QA

## 🧪 Testing

### Backend Testing
```bash
cd backend/sangkuriang-api
pytest tests/ -v --cov=.
```

### Mobile Testing
```bash
cd mobile
flutter test
flutter drive --target=test_driver/app.dart
```

### Integration Testing
```bash
# Run integration tests
cd scripts
./run-integration-tests.sh
```

## 🤝 Kontribusi

Kami menyambut kontribusi dari komunitas! Silakan lihat [CONTRIBUTING.md](CONTRIBUTING.md) untuk pedoman kontribusi.

### 🎯 Cara Berkontribusi

1. **Fork** repository ini
2. **Create** branch fitur Anda (`git checkout -b feature/AmazingFeature`)
3. **Commit** perubahan Anda (`git commit -m 'Add some AmazingFeature'`)
4. **Push** ke branch (`git push origin feature/AmazingFeature`)
5. **Open** Pull Request

### 🏷️ Good First Issues
Lihat [issues dengan label "good first issue"](https://github.com/sangkuriang/sangkuriang/labels/good%20first%20issue) untuk memulai kontribusi.

## 📈 Roadmap

### 🎯 Q4 2025 - Foundation ✅
- [x] Desain arsitektur sistem
- [x] MVP backend development
- [x] Basic authentication system (JWT implementation)
- [x] Payment gateway integration (OVO, GoPay, Dana)
- [x] Mobile app completion (Flutter Android/iOS)
- [x] Basic audit engine (crypto analysis)

### 🚀 Q1 2026 - Core Features ✅
- [x] Full crowdfunding platform
- [x] Advanced audit engine (quantum resistance, NIST compliance)
- [x] Community governance system (decentralized governance)
- [x] Reputation system (developer & project reputation)
- [x] Analytics dashboard (monitoring & metrics)

### 🔮 Q2 2026 - Enhancement ✅
- [x] AI-powered fraud detection (smart contract audit)
- [ ] Multi-language support
- [x] Advanced analytics (performance monitoring)
- [ ] University partnerships
- [ ] Community events

### 🌟 Q3 2026 - Scale & Partnership ✅
- [ ] ASEAN expansion
- [x] Advanced DeFi integration (DAO governance, smart contracts)
- [x] Enterprise solutions (compliance systems)
- [ ] Government partnerships
- [ ] Global recognition

Lihat [ROADMAP.md](ROADMAP.md) untuk detail roadmap.

## 📊 Status Proyek

![GitHub commit activity](https://img.shields.io/github/commit-activity/m/sangkuriang/sangkuriang)
![GitHub issues](https://img.shields.io/github/issues/sangkuriang/sangkuriang)
![GitHub pull requests](https://img.shields.io/github/issues-pr/sangkuriang/sangkuriang)
![GitHub contributors](https://img.shields.io/github/contributors/sangkuriang/sangkuriang)

## 📞 Kontak

### 📧 Email
- **General**: hello@sangkuriang.xyz
- **Support**: support@sangkuriang.xyz
- **Partnership**: partnership@sangkuriang.xyz
- **Security**: security@sangkuriang.xyz

### 💬 Social Media
- [Discord](https://discord.gg/sangkuriang)
- [Telegram](https://t.me/sangkuriang_id)
- [Twitter](https://twitter.com/sangkuriang_id)
- [LinkedIn](https://linkedin.com/company/sangkuriang)
- [Instagram](https://instagram.com/sangkuriang.id)

### 🌐 Website
- **Main**: https://sangkuriang.id
- **Docs**: https://docs.sangkuriang.id
- **API**: https://api.sangkuriang.id
- **Status**: https://status.sangkuriang.id

## 🔒 Security

### 🐛 Reporting Security Issues
Jika Anda menemukan kerentanan keamanan, silakan email ke [security@sangkuriang.id](mailto:security@sangkuriang.id) dengan:
- Deskripsi detail masalah
- Langkah reproduksi
- Informasi kontak Anda
- Gunakan PGP jika memungkinkan

### 🔐 PGP Key
```
-----BEGIN PGP PUBLIC KEY BLOCK-----
[menggunakan kunci PGP publik]
-----END PGP PUBLIC KEY BLOCK-----
```

## 📄 Lisensi

Proyek ini dilisensikan di bawah [MIT License](LICENSE) - lihat file [LICENSE](LICENSE) untuk detail.

```
MIT License

Copyright (c) 2024 SANGKURIANG

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🙏 Acknowledgments

- **Komunitas Developer Indonesia** - Untuk semangat dan kontribusinya
- **Open Source Community** - Untuk tools dan library yang digunakan
- **FastAPI Team** - Untuk framework backend yang luar biasa
- **Flutter Team** - Untuk cross-platform development toolkit
- **Semua Kontributor** - Yang telah berkontribusi pada proyek ini

---

<div align="center">

### ⭐ Jika Anda menyukai proyek ini, berikan bintang di GitHub! ⭐

**[⭐ Star this repo](https://github.com/sangkuriang/sangkuriang)** | **[🚀 Try the demo](https://demo.sangkuriang.id)** | **[📖 Read the docs](https://docs.sangkuriang.id)**

</div>

---

**Made with ❤️ by the SANGKURIANG Team**  
**Building the future of Indonesian cryptography, one line of code at a time.**