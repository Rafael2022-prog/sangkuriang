"""
Rate limiting middleware for SANGKURIANG API
"""

import time
import asyncio
from typing import Dict, Optional
from collections import defaultdict, deque
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self, rate: int = 60, burst: int = 10):
        """
        Initialize rate limiter.
        
        Args:
            rate: Number of requests per minute
            burst: Maximum burst size
        """
        self.rate = rate
        self.burst = burst
        self.tokens = burst
        self.last_update = time.time()
        self.request_times = deque(maxlen=rate)
    
    def is_allowed(self) -> bool:
        """Check if request is allowed."""
        now = time.time()
        
        # Remove old requests (older than 1 minute)
        while self.request_times and now - self.request_times[0] > 60:
            self.request_times.popleft()
        
        # Check if we can add a new request
        if len(self.request_times) >= self.rate:
            return False
        
        # Add current request
        self.request_times.append(now)
        return True
    
    def get_wait_time(self) -> float:
        """Get wait time until next request is allowed."""
        if not self.request_times:
            return 0
        
        oldest_request = self.request_times[0]
        wait_time = 60 - (time.time() - oldest_request)
        return max(0, wait_time)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.rate_limiters: Dict[str, RateLimiter] = defaultdict(lambda: RateLimiter(rate=60, burst=10))
        self.ip_limiters: Dict[str, RateLimiter] = defaultdict(lambda: RateLimiter(rate=100, burst=20))
        
        # Special rate limits for different endpoints
        self.endpoint_limits = {
            "/api/v1/auth/login": RateLimiter(rate=5, burst=2),
            "/api/v1/auth/register": RateLimiter(rate=5, burst=2),
            "/api/v1/auth/reset-password": RateLimiter(rate=3, burst=1),
            "/api/v1/payments/create": RateLimiter(rate=10, burst=3),
            "/api/v1/audit/request": RateLimiter(rate=5, burst=2),
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        
        # Get client identifier
        client_id = self.get_client_id(request)
        ip_address = request.client.host if request.client else "unknown"
        
        # Get endpoint
        endpoint = request.url.path
        
        # Check if rate limiting should be applied
        if not self.should_rate_limit(request):
            return await call_next(request)
        
        # Get appropriate rate limiter
        rate_limiter = self.get_rate_limiter(endpoint, client_id, ip_address)
        
        # Check if request is allowed
        if not rate_limiter.is_allowed():
            wait_time = rate_limiter.get_wait_time()
            
            logger.warning(
                f"Rate limit exceeded for {client_id} ({ip_address}) "
                f"on endpoint {endpoint}. Wait time: {wait_time:.1f}s"
            )
            
            return Response(
                content=f"Rate limit exceeded. Please wait {wait_time:.1f} seconds.",
                status_code=429,
                headers={
                    "Retry-After": str(int(wait_time) + 1),
                    "X-RateLimit-Limit": str(rate_limiter.rate),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time() + wait_time))
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = rate_limiter.rate - len(rate_limiter.request_times)
        response.headers["X-RateLimit-Limit"] = str(rate_limiter.rate)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        
        return response
    
    def get_client_id(self, request: Request) -> str:
        """Get client identifier from request."""
        # Try to get user ID from auth header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            # In a real implementation, you would decode the JWT token
            # For now, we'll use a hash of the token
            import hashlib
            return hashlib.md5(auth_header.encode()).hexdigest()
        
        # Fallback to IP address
        return request.client.host if request.client else "unknown"
    
    def get_rate_limiter(self, endpoint: str, client_id: str, ip_address: str) -> RateLimiter:
        """Get appropriate rate limiter for the request."""
        # Check for endpoint-specific limits
        for path_prefix, limiter in self.endpoint_limits.items():
            if endpoint.startswith(path_prefix):
                return limiter
        
        # Check for authenticated user limits
        if client_id != "unknown" and not self.is_ip_address(client_id):
            return self.rate_limiters[f"user:{client_id}"]
        
        # Use IP-based limits for unauthenticated requests
        return self.ip_limiters[ip_address]
    
    def is_ip_address(self, identifier: str) -> bool:
        """Check if identifier is an IP address."""
        import re
        ip_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
        return bool(ip_pattern.match(identifier))
    
    def should_rate_limit(self, request: Request) -> bool:
        """Check if request should be rate limited."""
        # Skip rate limiting for health checks and static files
        path = request.url.path
        
        skip_paths = [
            "/health",
            "/static",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]
        
        for skip_path in skip_paths:
            if path.startswith(skip_path):
                return False
        
        # Skip rate limiting for OPTIONS requests
        if request.method == "OPTIONS":
            return False
        
        return True

# Rate limiter for specific use cases
class EndpointRateLimiter:
    """Rate limiter for specific endpoints."""
    
    def __init__(self, requests_per_minute: int = 10, burst: int = 5):
        self.requests_per_minute = requests_per_minute
        self.burst = burst
        self.requests = deque(maxlen=requests_per_minute)
    
    async def is_allowed(self, key: str) -> bool:
        """Check if request with key is allowed."""
        now = time.time()
        
        # Remove old requests
        while self.requests and now - self.requests[0] > 60:
            self.requests.popleft()
        
        # Check if we can add a new request
        if len(self.requests) >= self.requests_per_minute:
            return False
        
        self.requests.append(now)
        return True
    
    def get_remaining_requests(self) -> int:
        """Get remaining requests for current minute."""
        now = time.time()
        
        # Remove old requests
        while self.requests and now - self.requests[0] > 60:
            self.requests.popleft()
        
        return max(0, self.requests_per_minute - len(self.requests))

# Global rate limiters
auth_rate_limiter = EndpointRateLimiter(requests_per_minute=5, burst=2)
payment_rate_limiter = EndpointRateLimiter(requests_per_minute=10, burst=3)
audit_rate_limiter = EndpointRateLimiter(requests_per_minute=5, burst=2)

async def check_rate_limit(limiter: EndpointRateLimiter, key: str) -> tuple[bool, int]:
    """Check rate limit and return (is_allowed, remaining_requests)."""
    is_allowed = await limiter.is_allowed(key)
    remaining = limiter.get_remaining_requests()
    return is_allowed, remaining