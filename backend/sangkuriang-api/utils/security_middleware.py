"""
Security middleware for SANGKURIANG API
"""

import os
import re
from typing import List, Optional
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import secrets
import logging

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Security headers middleware."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        
    async def dispatch(self, request: Request, call_next):
        """Add security headers to response."""
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Content Security Policy
        csp = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net",
            "font-src 'self' https://fonts.gstatic.com",
            "img-src 'self' data: https:",
            "connect-src 'self' https:",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'"
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp)
        
        return response

class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF protection middleware."""
    
    def __init__(self, app: ASGIApp, secret_key: Optional[str] = None):
        super().__init__(app)
        self.secret_key = secret_key or os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
        
    async def dispatch(self, request: Request, call_next):
        """CSRF protection."""
        # Skip CSRF for safe methods
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return await call_next(request)
        
        # Skip CSRF for API endpoints with proper authentication
        if request.url.path.startswith("/api/"):
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                return await call_next(request)
        
        # Check CSRF token for state-changing requests
        csrf_token = request.headers.get("X-CSRF-Token")
        if not csrf_token:
            csrf_token = request.cookies.get("csrf_token")
        
        if not csrf_token:
            logger.warning(f"CSRF token missing for {request.method} {request.url.path}")
            raise HTTPException(status_code=403, detail="CSRF token required")
        
        # Verify CSRF token (simplified - implement proper verification)
        if not self.verify_csrf_token(csrf_token):
            logger.warning(f"Invalid CSRF token for {request.method} {request.url.path}")
            raise HTTPException(status_code=403, detail="Invalid CSRF token")
        
        return await call_next(request)
    
    def verify_csrf_token(self, token: str) -> bool:
        """Verify CSRF token."""
        # Simplified verification - implement proper token verification
        return len(token) >= 32

class InputValidationMiddleware(BaseHTTPMiddleware):
    """Input validation middleware."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        
    async def dispatch(self, request: Request, call_next):
        """Validate input."""
        # Skip validation for safe methods
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return await call_next(request)
        
        # Validate request size
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                max_size = 10 * 1024 * 1024  # 10MB
                if size > max_size:
                    logger.warning(f"Request too large: {size} bytes")
                    raise HTTPException(status_code=413, detail="Request too large")
            except ValueError:
                pass
        
        # Validate content type for API requests
        if request.url.path.startswith("/api/"):
            content_type = request.headers.get("content-type", "")
            if request.method in ["POST", "PUT", "PATCH"]:
                if not any(ct in content_type for ct in ["application/json", "multipart/form-data"]):
                    logger.warning(f"Invalid content type: {content_type}")
                    raise HTTPException(status_code=400, detail="Invalid content type")
        
        return await call_next(request)

class SQLInjectionMiddleware(BaseHTTPMiddleware):
    """SQL injection protection middleware."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.sql_patterns = [
            re.compile(r"(\b(union|select|insert|update|delete|drop|create|alter|exec|execute|script|declare)\b.*\b(from|where|and|or|order by|group by|having)\b)", re.IGNORECASE),
            re.compile(r"(\b(and|or)\b.*=.*\b(and|or)\b)", re.IGNORECASE),
            re.compile(r"(\bunion\b.*\bselect\b)", re.IGNORECASE),
            re.compile(r"(\bdrop\b.*\btable\b)", re.IGNORECASE),
            re.compile(r"(\bexec\b.*\b\(.*\))", re.IGNORECASE),
            re.compile(r"(--|#|/\*|\*/)", re.IGNORECASE),
        ]
        
    async def dispatch(self, request: Request, call_next):
        """Check for SQL injection patterns."""
        # Check query parameters
        for key, values in request.query_params.multi_items():
            for value in values:
                if self.contains_sql_injection(value):
                    logger.warning(f"SQL injection detected in query parameter {key}: {value}")
                    raise HTTPException(status_code=400, detail="Invalid input detected")
        
        # Check form data for POST requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
                try:
                    form_data = await request.form()
                    for key, values in form_data.multi_items():
                        for value in values:
                            if self.contains_sql_injection(value):
                                logger.warning(f"SQL injection detected in form data {key}: {value}")
                                raise HTTPException(status_code=400, detail="Invalid input detected")
                except Exception:
                    pass  # Form parsing failed, let the request proceed
        
        return await call_next(request)
    
    def contains_sql_injection(self, value: str) -> bool:
        """Check if value contains SQL injection patterns."""
        if not value or not isinstance(value, str):
            return False
        
        for pattern in self.sql_patterns:
            if pattern.search(value):
                return True
        
        return False

class XSSProtectionMiddleware(BaseHTTPMiddleware):
    """XSS protection middleware."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.xss_patterns = [
            re.compile(r"<script.*?>.*?</script>", re.IGNORECASE | re.DOTALL),
            re.compile(r"<iframe.*?>.*?</iframe>", re.IGNORECASE | re.DOTALL),
            re.compile(r"javascript:", re.IGNORECASE),
            re.compile(r"on\w+\s*=", re.IGNORECASE),
            re.compile(r"<object.*?>.*?</object>", re.IGNORECASE | re.DOTALL),
            re.compile(r"<embed.*?>.*?</embed>", re.IGNORECASE | re.DOTALL),
        ]
        
    async def dispatch(self, request: Request, call_next):
        """Check for XSS patterns."""
        # Check query parameters
        for key, values in request.query_params.multi_items():
            for value in values:
                if self.contains_xss(value):
                    logger.warning(f"XSS detected in query parameter {key}: {value}")
                    raise HTTPException(status_code=400, detail="Invalid input detected")
        
        return await call_next(request)
    
    def contains_xss(self, value: str) -> bool:
        """Check if value contains XSS patterns."""
        if not value or not isinstance(value, str):
            return False
        
        for pattern in self.xss_patterns:
            if pattern.search(value):
                return True
        
        return False

class SecurityLoggerMiddleware(BaseHTTPMiddleware):
    """Security event logging middleware."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        
    async def dispatch(self, request: Request, call_next):
        """Log security events."""
        # Log suspicious requests
        user_agent = request.headers.get("user-agent", "")
        
        # Check for suspicious user agents
        suspicious_ua_patterns = [
            "sqlmap", "nikto", "nessus", "burp", "zap", "acunetix",
            "nmap", "masscan", "shodan", "censys"
        ]
        
        for pattern in suspicious_ua_patterns:
            if pattern.lower() in user_agent.lower():
                logger.warning(f"Suspicious user agent detected: {user_agent}")
                break
        
        # Log requests with suspicious patterns
        if self.is_suspicious_request(request):
            logger.warning(f"Suspicious request from {request.client.host}: {request.method} {request.url.path}")
        
        return await call_next(request)
    
    def is_suspicious_request(self, request: Request) -> bool:
        """Check if request is suspicious."""
        # Check for path traversal
        if ".." in request.url.path:
            return True
        
        # Check for suspicious query parameters
        for key in request.query_params.keys():
            if any(suspicious in key.lower() for suspicious in ["password", "token", "secret", "key"]):
                return True
        
        return False

def setup_security_middleware(app: FastAPI):
    """Setup all security middleware."""
    # Add security headers
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Add input validation
    app.add_middleware(InputValidationMiddleware)
    
    # Add SQL injection protection
    app.add_middleware(SQLInjectionMiddleware)
    
    # Add XSS protection
    app.add_middleware(XSSProtectionMiddleware)
    
    # Add security logging
    app.add_middleware(SecurityLoggerMiddleware)
    
    # Add CSRF protection (optional, can be enabled per endpoint)
    # app.add_middleware(CSRFMiddleware, secret_key=os.getenv("SECRET_KEY"))