"""
SANGKURIANG Crypto Audit Engine
Main application entry point
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn
from loguru import logger

# Import with proper path handling
import sys
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from sangkuriang_api.config import settings
    from sangkuriang_api.database import init_db, close_db
    from sangkuriang_api.routers import auth, projects, audit, funding, github
    from sangkuriang_api.middleware import RateLimitMiddleware, SecurityHeadersMiddleware
    from sangkuriang_api.utils.brand_utils import get_brand_config, get_logo_path
except ImportError:
    # Fallback for direct execution
    from config import settings
    from database import init_db, close_db
    from routers import auth, projects, audit, funding, github
    from middleware import RateLimitMiddleware, SecurityHeadersMiddleware
    from utils.brand_utils import get_brand_config, get_logo_path

# Initialize FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting SANGKURIANG Crypto Audit Engine...")
    await init_db()
    logger.info("Database initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down SANGKURIANG...")
    await close_db()
    logger.info("Database connections closed")

app = FastAPI(
    title="SANGKURIANG Crypto Audit Engine",
    description="Decentralized funding platform for Indonesian crypto projects with automated security auditing",
    version="1.0.0",
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# Security middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)

# Include routers
# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["Projects"])
app.include_router(audit.router, prefix="/api/v1/audit", tags=["Audit"])
app.include_router(funding.router, prefix="/api/v1/funding", tags=["Funding"])
app.include_router(github.router, prefix="/api/v1/github", tags=["GitHub Integration"])

# Mount static files for brand assets
app.mount("/static", StaticFiles(directory="../static"), name="static")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to SANGKURIANG Crypto Audit Engine",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "sangkuriang-api",
        "version": "1.0.0"
    }

@app.get("/api/v1/status")
async def system_status():
    """System status endpoint"""
    return {
        "api_status": "operational",
        "database_status": "connected",
        "audit_engine_status": "running",
        "timestamp": "2024-01-01T00:00:00Z"
    }

@app.get("/api/v1/brand/config")
async def brand_config():
    """Get brand configuration"""
    try:
        config = get_brand_config()
        return config
    except Exception as e:
        logger.error(f"Error getting brand config: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/brand/logo/{size:str}")
async def brand_logo(size: str):
    """Get brand logo by size"""
    try:
        logo_path = get_logo_path(size)
        if not logo_path:
            raise HTTPException(status_code=404, detail="Logo size not found")
        
        return {
            "size": size,
            "url": f"/static/images/{logo_path}",
            "path": logo_path
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting brand logo: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning"
    )