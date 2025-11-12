import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from typing import Optional, Dict, Any
import re
import secrets
import string

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)

# JWT Token handling
def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    from ..config import settings
    
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify JWT token"""
    from ..config import settings
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None

# Validation functions
def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone: str) -> bool:
    """Validate phone number format (supports international format)"""
    # Remove spaces and common separators
    cleaned_phone = re.sub(r'[\s\-\(\)]', '', phone)
    
    # Check for Indonesian format (+62 or 08)
    indonesian_pattern = r'^(\+62|62|0)8[1-9][0-9]{6,10}$'
    
    # General international format
    international_pattern = r'^\+?[1-9]\d{6,14}$'
    
    return (re.match(indonesian_pattern, cleaned_phone) is not None or
            re.match(international_pattern, cleaned_phone) is not None)

def validate_password_strength(password: str) -> Dict[str, Any]:
    """Validate password strength and return detailed feedback"""
    result = {
        "is_valid": False,
        "score": 0,
        "feedback": []
    }
    
    if len(password) >= 8:
        result["score"] += 1
    else:
        result["feedback"].append("Password must be at least 8 characters long")
    
    if re.search(r'[A-Z]', password):
        result["score"] += 1
    else:
        result["feedback"].append("Password must contain at least one uppercase letter")
    
    if re.search(r'[a-z]', password):
        result["score"] += 1
    else:
        result["feedback"].append("Password must contain at least one lowercase letter")
    
    if re.search(r'\d', password):
        result["score"] += 1
    else:
        result["feedback"].append("Password must contain at least one number")
    
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        result["score"] += 1
    else:
        result["feedback"].append("Password should contain special characters for better security")
    
    result["is_valid"] = result["score"] >= 4
    return result

def validate_github_url(url: str) -> bool:
    """Validate GitHub repository URL"""
    pattern = r'^https?://github\.com/[\w-]+/[\w-]+$'
    return re.match(pattern, url) is not None

def sanitize_input(input_string: str) -> str:
    """Sanitize user input to prevent XSS and injection attacks"""
    # Remove HTML tags
    cleaned = re.sub(r'<[^>]+>', '', input_string)
    # Escape special characters
    cleaned = cleaned.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    cleaned = cleaned.replace('"', '&quot;').replace("'", '&#x27;')
    return cleaned.strip()

# Security utilities
def generate_secure_token(length: int = 32) -> str:
    """Generate cryptographically secure random token"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_otp(length: int = 6) -> str:
    """Generate One-Time Password"""
    return ''.join(secrets.choice(string.digits) for _ in range(length))

def mask_email(email: str) -> str:
    """Mask email address for security"""
    if '@' not in email:
        return email
    
    username, domain = email.split('@')
    if len(username) <= 3:
        masked_username = username[0] + '*' * (len(username) - 1)
    else:
        masked_username = username[:2] + '*' * (len(username) - 3) + username[-1]
    
    return f"{masked_username}@{domain}"

def mask_phone(phone: str) -> str:
    """Mask phone number for security"""
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    if len(cleaned) < 4:
        return '*' * len(cleaned)
    
    return f"{'*' * (len(cleaned) - 4)}{cleaned[-4:]}"

# Rate limiting helpers
def get_client_ip(request) -> str:
    """Extract client IP address from request"""
    # Check for forwarded headers first
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct connection
    if hasattr(request, 'client') and request.client:
        return request.client.host
    
    return "127.0.0.1"

def create_rate_limit_key(ip: str, endpoint: str, user_id: Optional[str] = None) -> str:
    """Create rate limiting key"""
    if user_id:
        return f"rate_limit:user:{user_id}:{endpoint}"
    return f"rate_limit:ip:{ip}:{endpoint}"

# CSRF protection
def generate_csrf_token() -> str:
    """Generate CSRF token"""
    return generate_secure_token(32)

def validate_csrf_token(token: str, session_token: str) -> bool:
    """Validate CSRF token"""
    return secrets.compare_digest(token, session_token)

# File upload security
def validate_file_extension(filename: str, allowed_extensions: set) -> bool:
    """Validate file extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def validate_file_size(file_size: int, max_size_mb: int = 10) -> bool:
    """Validate file size"""
    max_size_bytes = max_size_mb * 1024 * 1024
    return file_size <= max_size_bytes

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for security"""
    # Remove path components
    filename = filename.split('/')[-1].split('\\')[-1]
    
    # Remove special characters
    filename = re.sub(r'[^\w\-\.]', '_', filename)
    
    # Limit length
    if len(filename) > 100:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:95] + (f'.{ext}' if ext else '')
    
    return filename