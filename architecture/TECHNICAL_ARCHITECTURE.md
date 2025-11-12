# SANGKURIANG: Technical Architecture

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Mobile Layer                              │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    Flutter App                              │  │
│  │  - Native Android/iOS Support                            │  │
│  │  - Cultural Indonesian UI/UX                              │  │  
│  │  - Offline-first Architecture                             │  │
│  └─────────────────────┬───────────────────────────────────────┘  │
│                        │   HTTPS/WebSocket                        │
└────────────────────────┼──────────────────────────────────────────┘
                         │
┌────────────────────────┼──────────────────────────────────────────┐
│                        ▼   API Gateway                           │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                 Load Balancer                               │  │
│  │  - Rate Limiting                                           │  │
│  │  - SSL Termination                                         │  │
│  │  - DDoS Protection                                         │  │
│  └─────────────────────┬───────────────────────────────────────┘  │
└────────────────────────┼──────────────────────────────────────────┘
                         │
┌────────────────────────┼──────────────────────────────────────────┐
│                        ▼   Backend Services                      │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐  │
│  │   Auth API   │ Project API  │ Funding API  │  Audit API   │  │
│  │              │              │              │              │  │
│  │ FastAPI      │ FastAPI      │ FastAPI      │ FastAPI      │  │
│  │ PostgreSQL   │ PostgreSQL   │ PostgreSQL   │ Python ML    │  │
│  │ Redis        │ Redis        │ Redis        │ Models       │  │
│  └──────┬───────┴──────┬───────┴──────┬───────┴──────┬───────┘  │
│         │              │              │              │         │
└─────────┼──────────────┼──────────────┼──────────────┼─────────┘
          │              │              │              │
┌─────────▼──────────────▼──────────────▼──────────────▼─────────┐
│                    Data Layer                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                 PostgreSQL Cluster                          │ │
│  │  - Project Data                                            │ │
│  │  - User Data                                               │ │
│  │  - Funding Records                                         │ │
│  │  - Audit Results                                           │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                     Redis Cache                             │ │
│  │  - Session Management                                      │ │
│  │  - Real-time Data                                          │ │
│  │  - Rate Limiting Counters                                  │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              File Storage (IPFS/Arweave)                    │ │
│  │  - Project Files                                           │ │
│  │  - Audit Reports                                           │ │
│  │  - Decentralized Backup                                    │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Technology Stack

### Backend Services
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL 14+
- **Cache**: Redis 6+
- **Message Queue**: RabbitMQ / Apache Kafka
- **ML/AI**: TensorFlow, PyTorch, scikit-learn
- **Cryptography**: cryptography.io, PyNaCl, hashlib

### Mobile Application
- **Framework**: Flutter 3.x
- **State Management**: Provider / Bloc
- **Local Storage**: SQLite / Hive
- **Payment Integration**: Midtrans, Xendit
- **Security**: flutter_secure_storage, local_auth

### Infrastructure
- **Container**: Docker & Kubernetes
- **Cloud**: AWS / GCP / Azure
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus, Grafana
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana)

### Security Tools
- **Vulnerability Scanner**: Bandit, Safety
- **SAST**: SonarQube
- **DAST**: OWASP ZAP
- **Dependency Check**: Snyk
- **Secret Scanning**: GitGuardian

## Crypto Audit Engine Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Crypto Audit Engine                            │
│                                                             │
│  ┌─────────────┬──────────────┬──────────────┬────────────┐ │
│  │  Parser     │  Analyzer    │  Evaluator   │  Reporter  │ │
│  │  Module     │  Module      │  Module      │  Module    │ │
│  ├─────────────┼──────────────┼──────────────┼────────────┤ │
│  │ • Language  │ • Crypto     │ • Risk       │ • Report   │ │
│  │   Detection │   Algorithm  │   Assessment │   Generation│ │
│  │ • AST       │   Analysis   │ • Compliance │ • Badge    │ │ │
│  │   Building  │ • Vulnerability│ Check      │   Generation│ │ │
│  │ • Dependency│   Detection  │ • Performance│ • API      │ │ │
│  │   Extraction│ • Quantum    │   Metrics    │   Response   │ │ │
│  │             │   Resistance │              │            │ │ │
│  └─────────────┴──────────────┴──────────────┴────────────┘ │
│                                                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              ML Models                                   │ │
│  │  ┌─────────────┬──────────────┬──────────────┬─────────┐ │ │
│  │  │ Vulnerability│ Crypto       │ Plagiarism │ Code    │ │ │
│  │  │ Detection    │ Algorithm    │ Detection  │ Quality │ │ │
│  │  │ Model        │ Identifier   │ Model      │ Model   │ │ │
│  │  └─────────────┴──────────────┴──────────────┴─────────┘ │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Database Schema (High-Level)

### Users Table
- user_id (UUID, PK)
- email (VARCHAR, UNIQUE)
- password_hash (VARCHAR)
- full_name (VARCHAR)
- phone_number (VARCHAR)
- kyc_status (ENUM)
- wallet_addresses (JSON)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

### Projects Table
- project_id (UUID, PK)
- user_id (UUID, FK)
- title (VARCHAR)
- description (TEXT)
- github_url (VARCHAR)
- category (ENUM)
- funding_goal (DECIMAL)
- current_funding (DECIMAL)
- status (ENUM)
- audit_score (INTEGER)
- audit_report (JSON)
- created_at (TIMESTAMP)

### Funding Table
- funding_id (UUID, PK)
- project_id (UUID, FK)
- user_id (UUID, FK)
- amount (DECIMAL)
- currency (VARCHAR)
- payment_method (ENUM)
- transaction_hash (VARCHAR)
- status (ENUM)
- created_at (TIMESTAMP)

### Audit Results Table
- audit_id (UUID, PK)
- project_id (UUID, FK)
- overall_score (INTEGER)
- security_score (INTEGER)
- performance_score (INTEGER)
- compliance_score (INTEGER)
- vulnerabilities (JSON)
- recommendations (JSON)
- badge_url (VARCHAR)
- created_at (TIMESTAMP)

## Security Architecture

### Multi-Layer Security
1. **Network Security**
   - SSL/TLS encryption
   - Web Application Firewall (WAF)
   - DDoS protection
   - VPN for internal services

2. **Application Security**
   - Input validation & sanitization
   - SQL injection prevention
   - XSS protection
   - CSRF tokens
   - Rate limiting

3. **Data Security**
   - Encryption at rest (AES-256)
   - Encryption in transit (TLS 1.3)
   - Key management (AWS KMS / HashiCorp Vault)
   - Regular security audits

4. **Access Control**
   - OAuth 2.0 / JWT tokens
   - Role-Based Access Control (RBAC)
   - Multi-Factor Authentication (MFA)
   - API key management

### Compliance Standards
- **PCI DSS**: For payment processing
- **GDPR**: For data protection
- **ISO 27001**: For information security
- **SOC 2**: For service organization control
- **OJK Regulations**: For Indonesian financial services

## Scalability Design

### Horizontal Scaling
- Microservices architecture
- Container orchestration (Kubernetes)
- Auto-scaling groups
- Load balancing

### Performance Optimization
- Database indexing
- Query optimization
- Caching strategies
- CDN for static assets
- Asynchronous processing

### Monitoring & Observability
- Application Performance Monitoring (APM)
- Distributed tracing
- Log aggregation
- Real-time alerting
- Health checks