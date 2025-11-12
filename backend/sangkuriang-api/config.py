"""
Configuration settings for SANGKURIANG API
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "SANGKURIANG Crypto Audit Engine"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-this")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "https://sangkuriang.id",
        "https://app.sangkuriang.id"
    ]
    
    ALLOWED_HOSTS: List[str] = ["*"] if DEBUG else ["sangkuriang.id", "app.sangkuriang.id"]
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://sangkuriang:sangkuriang123@localhost:5432/sangkuriang_db"
    )
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # GitHub Integration
    GITHUB_CLIENT_ID: str = os.getenv("GITHUB_CLIENT_ID", "")
    GITHUB_CLIENT_SECRET: str = os.getenv("GITHUB_CLIENT_SECRET", "")
    GITHUB_WEBHOOK_SECRET: str = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    
    # Payment Integration
    MIDTRANS_SERVER_KEY: str = os.getenv("MIDTRANS_SERVER_KEY", "")
    MIDTRANS_CLIENT_KEY: str = os.getenv("MIDTRANS_CLIENT_KEY", "")
    MIDTRANS_IS_PRODUCTION: bool = os.getenv("MIDTRANS_IS_PRODUCTION", "false").lower() == "true"
    
    XENDIT_SECRET_KEY: str = os.getenv("XENDIT_SECRET_KEY", "")
    XENDIT_WEBHOOK_TOKEN: str = os.getenv("XENDIT_WEBHOOK_TOKEN", "")
    
    # File Storage
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    ALLOWED_FILE_TYPES: List[str] = [".py", ".js", ".ts", ".go", ".rs", ".cpp", ".c"]
    
    # Audit Engine
    AUDIT_ENGINE_TIMEOUT: int = int(os.getenv("AUDIT_ENGINE_TIMEOUT", "300"))  # 5 minutes
    MAX_CONCURRENT_AUDITS: int = int(os.getenv("MAX_CONCURRENT_AUDITS", "5"))
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    RATE_LIMIT_PER_HOUR: int = int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))
    
    # Email
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "noreply@sangkuriang.id")
    
    # Blockchain
    ETHEREUM_RPC_URL: str = os.getenv("ETHEREUM_RPC_URL", "")
    POLYGON_RPC_URL: str = os.getenv("POLYGON_RPC_URL", "")
    BSC_RPC_URL: str = os.getenv("BSC_RPC_URL", "")
    
    # IPFS
    IPFS_API_URL: str = os.getenv("IPFS_API_URL", "http://localhost:5001")
    IPFS_GATEWAY_URL: str = os.getenv("IPFS_GATEWAY_URL", "https://gateway.ipfs.io")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")
    
    # Sentry
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Initialize settings
settings = Settings()

# Create upload directory if it doesn't exist
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)