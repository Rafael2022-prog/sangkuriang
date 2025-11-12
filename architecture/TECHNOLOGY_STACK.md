# SANGKURIANG: Technology Stack

## Backend Stack

### Core Framework
- **FastAPI**: Modern, fast web framework for building APIs with Python 3.7+
  - High performance, on par with NodeJS and Go
  - Automatic API documentation (OpenAPI/Swagger)
  - Type hints and validation with Pydantic
  - Async support for better concurrency

### Database & Storage
- **PostgreSQL**: Advanced open-source relational database
  - ACID compliance for financial transactions
  - JSON support for flexible data structures
  - Full-text search capabilities
  - Row-level security for multi-tenancy

- **Redis**: In-memory data structure store
  - Session management and caching
  - Real-time data processing
  - Pub/Sub for real-time notifications
  - Rate limiting and throttling

### Machine Learning & AI
- **Python ML Libraries**:
  - **scikit-learn**: Classical ML algorithms
  - **TensorFlow/Keras**: Deep learning models
  - **PyTorch**: Research and experimentation
  - **NLTK/spaCy**: Natural language processing
  - **NumPy/Pandas**: Data manipulation and analysis

### Cryptography & Security
- **cryptography.io**: Cryptographic recipes and primitives
- **PyNaCl**: High-level cryptography library
- **hashlib**: Secure hash and message digest algorithms
- **PyJWT**: JSON Web Token implementation
- **bcrypt**: Password hashing library
- **python-jose**: JavaScript Object Signing and Encryption

### API & Integration
- **httpx**: Modern async HTTP client
- **aiohttp**: Async HTTP client/server framework
- **celery**: Distributed task queue
- **dramatiq**: Background task processing
- **pydantic**: Data validation using Python type hints

## Mobile Stack (Flutter)

### Core Framework
- **Flutter 3.x**: Google's UI toolkit for cross-platform development
  - Single codebase for iOS and Android
  - Native performance
  - Hot reload for fast development
  - Rich widget library

### State Management
- **Provider**: Simple state management solution
- **Bloc**: Business Logic Component pattern
- **Riverpod**: Advanced state management
- **GetX**: Lightweight state management

### Local Storage
- **SQLite**: Local database for offline support
- **Hive**: Lightweight key-value database
- **SharedPreferences**: Simple data persistence
- **flutter_secure_storage**: Secure storage for sensitive data

### Payment Integration
- **Midtrans**: Payment gateway Indonesia
- **Xendit**: Fintech API platform
- **flutter_inappwebview**: WebView for payment pages
- **local_auth**: Biometric authentication

### UI/UX Libraries
- **flutter_svg**: SVG rendering support
- **cached_network_image**: Image caching
- **flutter_localizations**: Multi-language support
- **google_fonts**: Custom fonts
- **flutter_icons**: Icon library

## Infrastructure Stack

### Container & Orchestration
- **Docker**: Container platform
- **Kubernetes**: Container orchestration
- **Helm**: Kubernetes package manager
- **Docker Compose**: Multi-container applications

### Cloud Services
- **AWS Services**:
  - **EC2**: Virtual servers
  - **RDS**: Managed PostgreSQL
  - **ElastiCache**: Managed Redis
  - **S3**: Object storage
  - **CloudFront**: CDN
  - **ALB**: Application Load Balancer
  - **Route 53**: DNS management
  - **CloudWatch**: Monitoring and logging

### CI/CD
- **GitHub Actions**: CI/CD automation
- **Jenkins**: Continuous integration server
- **SonarQube**: Code quality analysis
- **Sentry**: Error tracking and monitoring

### Monitoring & Logging
- **Prometheus**: Monitoring and alerting
- **Grafana**: Data visualization
- **ELK Stack**: Elasticsearch, Logstash, Kibana
- **Jaeger**: Distributed tracing
- **New Relic**: Application performance monitoring

## Security Tools

### Static Analysis
- **Bandit**: Security linter for Python
- **Safety**: Dependency vulnerability scanner
- **SonarQube**: Code quality and security analysis
- **Semgrep**: Static analysis engine

### Dynamic Analysis
- **OWASP ZAP**: Web application security scanner
- **sqlmap**: SQL injection testing
- **nikto**: Web server scanner
- **burpsuite**: Web vulnerability scanner

### Dependency Management
- **Snyk**: Vulnerability management
- **pip-audit**: Audit Python packages
- **pip-licenses**: License compliance
- **requirements.txt**: Dependency pinning

## Development Tools

### Version Control
- **Git**: Distributed version control
- **GitHub**: Code hosting and collaboration
- **GitFlow**: Branching model
- **Conventional Commits**: Commit message standard

### Code Quality
- **Black**: Code formatter
- **isort**: Import sorter
- **flake8**: Style guide enforcement
- **mypy**: Static type checker
- **pre-commit**: Git hook framework

### Testing
- **pytest**: Testing framework
- **pytest-asyncio**: Async testing support
- **pytest-cov**: Coverage reporting
- **factory-boy**: Test data generation
- **responses**: HTTP request mocking
- **freezegun**: Time manipulation for testing

### Documentation
- **Sphinx**: Documentation generator
- **MkDocs**: Project documentation
- **Swagger/OpenAPI**: API documentation
- **Redoc**: API reference documentation

## Blockchain Integration

### Web3 Libraries
- **web3.py**: Ethereum Python library
- **eth-account**: Ethereum account management
- **eth-utils**: Ethereum utility functions
- **web3-flashbots**: Flashbots integration

### Smart Contract Tools
- **Brownie**: Python smart contract framework
- **hardhat**: Ethereum development environment
- **truffle**: Smart contract development suite
- **ganache**: Personal blockchain

## Payment Integration

### E-Wallet APIs
- **OVO**: Indonesian digital payment
- **GoPay**: Gojek payment platform
- **DANA**: Digital wallet service
- **LinkAja**: Telkomsel payment platform

### Payment Gateways
- **Midtrans**: Comprehensive payment gateway
- **Xendit**: Fintech API platform
- **DOKU**: Payment solutions
- **iPay88**: Online payment gateway

## Performance Optimization

### Caching
- **Redis**: High-performance caching
- **Memcached**: Distributed memory caching
- **Varnish**: HTTP accelerator
- **CloudFlare**: CDN and caching

### Database Optimization
- **pgbouncer**: PostgreSQL connection pooling
- **pg_stat_statements**: Query performance analysis
- **Redis Cluster**: Distributed caching
- **Read replicas**: Database scaling

### Load Balancing
- **HAProxy**: TCP/HTTP load balancer
- **nginx**: Web server and reverse proxy
- **AWS ALB**: Application load balancer
- **CloudFlare**: Global load balancing

## Compliance & Legal

### Data Privacy
- **GDPR**: General Data Protection Regulation
- **PDP Law**: Indonesian Personal Data Protection
- **CCPA**: California Consumer Privacy Act
- **PIPEDA**: Personal Information Protection Act

### Financial Compliance
- **OJK**: Indonesian Financial Services Authority
- **BI**: Bank Indonesia regulations
- **AML**: Anti-Money Laundering
- **KYC**: Know Your Customer requirements