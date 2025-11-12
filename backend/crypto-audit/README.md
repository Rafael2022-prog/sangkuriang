# 🏔️ SANGKURIANG

> **Membangun Kriptografi Nusantara, Satu Baris Kode Sekaligus.**

SANGKURIANG adalah ekosistem pendanaan terdesentralisasi khusus untuk proyek kriptografi berbasis Indonesia. Platform ini memungkinkan developer lokal untuk mendapatkan pendanaan, verifikasi teknis otomatis, dan pengembangan proyek tanpa bergantung pada platform asing.

## 🌟 Fitur Utama

### ✅ Sudah Tersedia

#### 1. 🔐 Multi-Signature Wallet System
- Wallet dengan multi-signature support untuk keamanan tingkat tinggi
- Transaction management dengan approval threshold
- Audit logs lengkap untuk semua aktivitas
- Status reporting real-time

#### 2. 💾 Decentralized Storage System
- Penyimpanan terdesentralisasi untuk audit logs dan hasil verifikasi
- Data integrity verification dengan SHA256
- Automatic node selection dan replication
- Concurrent operations support

#### 3. 🏆 Reputation System
- Developer reputation tracking dengan 6 kategori penilaian
- Project reputation dengan scoring transparan
- Level system (Novice → Developer → Expert → Master → Legend)
- Personalized recommendations untuk improvement
- Leaderboard dan top rankings

### 🚧 Dalam Pengembangan

#### 4. 🔍 Crypto Audit Engine
- Automated security analysis untuk kode kriptografi
- Quantum resistance checking
- NIST/ISO compliance verification
- Performance benchmarking
- Backdoor dan plagiarism detection

#### 5. 📱 Mobile Flutter Interface
- UI dengan tema budaya Indonesia (batik, merah-putih)
- Support e-wallet lokal (OVO, GoPay, Dana)
- Push notifications dan offline capabilities

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- pip package manager

### Installation
```bash
# Clone repository
git clone https://github.com/Rafael2022-prog/SANGKURIANG.git
cd SANGKURIANG/backend/crypto-audit

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest test_multi_sig_wallet_final.py -v
python -m pytest test_decentralized_storage.py -v
python -m pytest test_reputation_system.py -v
```

### Usage Examples

#### Multi-Signature Wallet
```python
import asyncio
from multi_sig_wallet import MultiSigWallet

async def create_wallet():
    # Create wallet with 2-of-3 signature requirement
    wallet = MultiSigWallet(
        wallet_id="wallet_001",
        owners=["owner1", "owner2", "owner3"],
        required_signatures=2
    )
    
    # Create transaction
    tx_id = await wallet.create_transaction(
        destination="recipient_1",
        amount=100.0,
        description="Funding untuk proyek kripto"
    )
    
    # Sign transaction
    await wallet.sign_transaction(tx_id, "owner1", "signature_data")
    await wallet.sign_transaction(tx_id, "owner2", "signature_data")
    
    # Execute transaction
    success = await wallet.execute_transaction(tx_id, "owner1")
    print(f"Transaction executed: {success}")
```

#### Decentralized Storage
```python
import asyncio
from decentralized_storage import DecentralizedStorage

async def store_data():
    storage = DecentralizedStorage()
    
    # Store audit log
    audit_log = {
        "action": "WALLET_CREATED",
        "wallet_id": "wallet_001",
        "timestamp": "2024-01-01T00:00:00Z"
    }
    
    data_id = await storage.store_audit_log(audit_log)
    print(f"Data stored with ID: {data_id}")
    
    # Retrieve data
    retrieved_data = await storage.retrieve_data(data_id)
    print(f"Retrieved data: {retrieved_data}")
```

#### Reputation System
```python
import asyncio
from reputation_system import ReputationEngine, ReputationCategory

async def manage_reputation():
    engine = ReputationEngine()
    
    # Register developer
    dev = await engine.register_developer(
        developer_id="dev_001",
        name="Budi Santoso",
        email="budi@example.com",
        github_username="budisantoso"
    )
    
    # Update reputation
    await engine.update_developer_reputation(
        developer_id="dev_001",
        category=ReputationCategory.SECURITY,
        score=90.0,
        context={
            "type": "audit",
            "description": "Excellent security audit",
            "score": 90.0
        }
    )
    
    # Get reputation insights
    insights = engine.calculate_reputation_insights("dev_001")
    print(f"Reputation level: {insights['developer']['current_level']}")
    print(f"Recommendations: {insights['developer']['recommendations']}")
```

## 🏗️ Architecture

### System Components
```
┌─────────────────────────────────────────────────────────────┐
│                    SANGKURIANG Ecosystem                   │
├─────────────────────────────────────────────────────────────┤
│  📱 Mobile Interface (Flutter)                             │
│  ├─ Native UI dengan tema Indonesia                      │
│  ├─ E-wallet integration                                  │
│  └─ Real-time notifications                               │
├─────────────────────────────────────────────────────────────┤
│  🌐 Backend Services (Python)                              │
│  ├─ 🔐 Multi-Sig Wallet Service                          │
│  ├─ 💾 Decentralized Storage Service                     │
│  ├─ 🏆 Reputation Service                                │
│  ├─ 🔍 Crypto Audit Engine                               │
│  └─ 💰 Funding Service                                    │
├─────────────────────────────────────────────────────────────┤
│  🔗 Blockchain Layer                                       │
│  ├─ Smart Contract untuk funding                          │
│  ├─ IPFS untuk storage terdesentralisasi                 │
│  └─ Web3 integration                                      │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow
1. **Project Registration** → Developer mendaftarkan proyek kripto
2. **Crypto Audit** → Sistem melakukan analisis keamanan otomatis
3. **Reputation Assignment** → Memberikan skor berdasarkan hasil audit
4. **Funding Campaign** → Komunitas dapat memberikan pendanaan
5. **Milestone Tracking** → Progress monitoring dan fund release
6. **Reputation Updates** → Update skor berdasarkan progress

## 🧪 Testing

### Test Coverage
- **Multi-Signature Wallet**: 7/7 tests passed ✅
- **Decentralized Storage**: 10/10 tests passed ✅
- **Reputation System**: 14/14 tests passed ✅

### Running Tests
```bash
# Run all tests
python -m pytest -v

# Run specific test suite
python -m pytest test_multi_sig_wallet_final.py -v
python -m pytest test_decentralized_storage.py -v
python -m pytest test_reputation_system.py -v

# Run with coverage
python -m pytest --cov=. --cov-report=html
```

## 🔒 Security

### Security Features
- **Multi-signature wallets** untuk transaksi aman
- **HMAC-based signatures** untuk data integrity
- **Decentralized storage** untuk menghindari single point of failure
- **Reputation system** untuk trustless verification
- **Automated audits** untuk deteksi dini masalah keamanan

### Best Practices
- Semua kode kriptografi harus open-source
- Audit berkala oleh komunitas
- Transparent reputation scoring
- Multi-party approval untuk transaksi besar

## 🤝 Contributing

Kami menyambut kontribusi dari komunitas! Silakan:

1. **Fork** repository ini
2. **Create branch** untuk fitur Anda (`git checkout -b fitur-baru`)
3. **Commit** perubahan Anda (`git commit -m 'Menambahkan fitur baru'`)
4. **Push** ke branch (`git push origin fitur-baru`)
5. **Buat Pull Request** dengan deskripsi yang jelas

### Development Guidelines
- Tulis tests untuk setiap fitur baru
- Ikuti PEP 8 style guidelines
- Gunakan type hints
- Dokumentasikan kode Anda
- Jaga backward compatibility

## 📋 Roadmap

Lihat [ROADMAP.md](ROADMAP.md) untuk detail roadmap pengembangan dan status implementasi.

## 🏆 Reputation Levels

### Developer Levels
- **Novice** (0-30): Pemula dalam kriptografi
- **Developer** (30-60): Memiliki pengalaman dasar
- **Expert** (60-80): Ahli dalam bidangnya
- **Master** (80-95): Master dengan kontribusi signifikan
- **Legend** (95-100): Legenda dengan reputasi luar biasa

### Project Levels
Sama dengan developer levels, berdasarkan combined score dari:
- Security Score (30%)
- Performance Score (25%)
- Community Score (20%)
- Transparency Score (15%)
- Innovation Score (10%)

## 📞 Support

Jika Anda memiliki pertanyaan atau membutuhkan bantuan:

- 📧 Email: sangkuriang@crypto-indonesia.id
- 💬 Discord: [SANGKURIANG Community](https://discord.gg/sangkuriang)
- 🐛 Issues: Gunakan GitHub Issues untuk bug reports
- 📖 Documentation: Lihat wiki repository ini

## 📄 License

Proyek ini dilisensikan di bawah MIT License - lihat file [LICENSE](LICENSE) untuk detail.

## 🙏 Acknowledgments

- **Komunitas Kripto Indonesia** untuk inspirasi dan support
- **Developer Nusantara** yang telah berkontribusi
- **Open Source Community** untuk tools dan libraries
- **Budaya Indonesia** yang menjadi inspirasi nama dan desain

---

**SANGKURIANG** - *Membangun masa depan kriptografi Indonesia, satu proyek pada satu waktu.*