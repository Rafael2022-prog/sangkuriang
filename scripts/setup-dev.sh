#!/bin/bash

# SANGKURIANG Development Environment Setup Script
# This script sets up the development environment for the SANGKURIANG project

set -e

echo "🚀 Setting up SANGKURIANG Development Environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python version
check_python() {
    log_info "Checking Python installation..."
    
    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        log_success "Python $PYTHON_VERSION found"
        
        # Check if Python version is 3.8 or higher
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
            log_success "Python version is compatible (>= 3.8)"
        else
            log_error "Python 3.8 or higher is required"
            exit 1
        fi
    else
        log_error "Python 3 is not installed. Please install Python 3.8 or higher."
        exit 1
    fi
}

# Check Node.js and npm
check_nodejs() {
    log_info "Checking Node.js installation..."
    
    if command_exists node; then
        NODE_VERSION=$(node --version)
        log_success "Node.js $NODE_VERSION found"
    else
        log_warning "Node.js not found. Flutter development will still work, but some tools may not be available."
    fi
    
    if command_exists npm; then
        NPM_VERSION=$(npm --version)
        log_success "npm $NPM_VERSION found"
    else
        log_warning "npm not found. Some development tools may not be available."
    fi
}

# Check Flutter
check_flutter() {
    log_info "Checking Flutter installation..."
    
    if command_exists flutter; then
        FLUTTER_VERSION=$(flutter --version | head -n1)
        log_success "Flutter found: $FLUTTER_VERSION"
        
        # Check Flutter doctor
        log_info "Running Flutter doctor..."
        flutter doctor
    else
        log_error "Flutter is not installed. Please install Flutter SDK."
        echo "Visit: https://flutter.dev/docs/get-started/install"
        exit 1
    fi
}

# Setup Python virtual environment
setup_python_env() {
    log_info "Setting up Python virtual environment..."
    
    cd backend
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        log_info "Creating virtual environment..."
        python3 -m venv venv
        log_success "Virtual environment created"
    else
        log_info "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    log_info "Activating virtual environment..."
    source venv/bin/activate || . venv/Scripts/activate 2>/dev/null || true
    
    # Upgrade pip
    log_info "Upgrading pip..."
    python -m pip install --upgrade pip
    
    # Install requirements
    log_info "Installing Python dependencies..."
    pip install -r requirements.txt
    
    log_success "Python dependencies installed successfully"
    
    cd ..
}

# Setup Flutter dependencies
setup_flutter_deps() {
    log_info "Setting up Flutter dependencies..."
    
    cd mobile
    
    # Get Flutter dependencies
    log_info "Getting Flutter dependencies..."
    flutter pub get
    
    # Generate code if needed (for build_runner dependencies)
    if grep -q "build_runner" pubspec.yaml; then
        log_info "Running code generation..."
        flutter pub run build_runner build --delete-conflicting-outputs
    fi
    
    log_success "Flutter dependencies installed successfully"
    
    cd ..
}

# Create environment file
setup_env_file() {
    log_info "Setting up environment configuration..."
    
    if [ ! -f ".env" ]; then
        log_info "Creating .env file from template..."
        cp .env.example .env
        log_success "Environment file created. Please edit .env with your actual configuration."
        
        # Generate a random secret key
        SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
        sed -i.bak "s/your-super-secret-key-change-this-in-production/$SECRET_KEY/g" .env
        rm -f .env.bak
        
        log_warning "Remember to update the .env file with your actual API keys and configuration."
    else
        log_info "Environment file already exists"
    fi
}

# Setup database
setup_database() {
    log_info "Setting up database..."
    
    # Check if PostgreSQL is running
    if command_exists pg_isready; then
        if pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
            log_success "PostgreSQL is running"
            
            # Create database if it doesn't exist (requires superuser privileges)
            log_info "Creating database (if not exists)..."
            createdb sangkuriang_db 2>/dev/null || log_warning "Database may already exist or user lacks privileges"
            
            # Run migrations (if alembic is set up)
            if [ -f "backend/alembic.ini" ]; then
                log_info "Running database migrations..."
                cd backend
                source venv/bin/activate || . venv/Scripts/activate 2>/dev/null || true
                alembic upgrade head || log_warning "Migration failed - database may not be properly configured"
                cd ..
            fi
        else
            log_warning "PostgreSQL is not running. Please start PostgreSQL service."
        fi
    else
        log_warning "PostgreSQL client tools not found. Please ensure PostgreSQL is installed and running."
    fi
}

# Setup Redis
setup_redis() {
    log_info "Checking Redis installation..."
    
    if command_exists redis-cli; then
        if redis-cli ping >/dev/null 2>&1; then
            log_success "Redis is running"
        else
            log_warning "Redis is not running. Please start Redis service."
        fi
    else
        log_warning "Redis not found. Caching functionality will not work."
    fi
}

# Create necessary directories
create_directories() {
    log_info "Creating necessary directories..."
    
    mkdir -p backend/uploads
    mkdir -p backend/logs
    mkdir -p mobile/build
    mkdir -p deployment/docker
    mkdir -p deployment/kubernetes
    mkdir -p tests/results
    
    log_success "Directories created"
}

# Install development tools
setup_dev_tools() {
    log_info "Setting up development tools..."
    
    # Install pre-commit hooks (if available)
    if command_exists pre-commit; then
        log_info "Installing pre-commit hooks..."
        pre-commit install || log_warning "Pre-commit installation failed"
    else
        log_info "Installing pre-commit..."
        pip install pre-commit || log_warning "Failed to install pre-commit"
    fi
    
    # Setup git hooks (if in git repository)
    if [ -d ".git" ]; then
        log_info "Setting up git hooks..."
        
        # Create pre-commit hook
        cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Run linting and tests before commit

echo "Running pre-commit checks..."

# Python linting
cd backend
source venv/bin/activate || . venv/Scripts/activate 2>/dev/null || true
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics || exit 1
black --check . || exit 1

# Flutter analysis
cd ../mobile
flutter analyze || exit 1
flutter format --set-exit-if-changed . || exit 1

echo "Pre-commit checks passed!"
EOF
        chmod +x .git/hooks/pre-commit
        log_success "Git hooks configured"
    fi
}

# Main setup function
main() {
    log_info "Starting SANGKURIANG development environment setup..."
    
    # Check prerequisites
    check_python
    check_nodejs
    check_flutter
    
    # Setup components
    create_directories
    setup_env_file
    setup_python_env
    setup_flutter_deps
    setup_database
    setup_redis
    setup_dev_tools
    
    log_success "✅ Development environment setup completed!"
    echo ""
    echo "🎉 SANGKURIANG is ready for development!"
    echo ""
    echo "Next steps:"
    echo "1. Edit the .env file with your actual configuration"
    echo "2. Start the backend server: cd backend && source venv/bin/activate && python sangkuriang-api/main.py"
    echo "3. Run the Flutter app: cd mobile && flutter run"
    echo "4. Visit the API documentation: http://localhost:8000/docs"
    echo ""
    echo "For more information, check the documentation in the docs/ directory."
}

# Run main function
main "$@"