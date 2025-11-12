from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List
from datetime import datetime
from ..models import UserRole, ProjectStatus, AuditStatus, FundingStatus

# Base schemas
class BaseResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None

# User schemas
class UserBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone_number: Optional[str] = Field(None, regex=r'^\+?\d{10,15}$')
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = Field(None, max_length=500)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)
    referral_code: Optional[str] = None

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in v):
            raise ValueError('Password must contain at least one lowercase letter')
        return v

class UserResponse(UserBase):
    id: str
    role: UserRole
    is_email_verified: bool
    is_phone_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    reputation_score: int = 0
    level: int = 1

    class Config:
        orm_mode = True

# Authentication schemas
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    reset_token: str
    new_password: str

# Project schemas
class ProjectBase(BaseModel):
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=50, max_length=2000)
    category: str = Field(..., regex=r'^[a-zA-Z0-9_-]+$')
    funding_goal: float = Field(..., gt=0)
    deadline: datetime
    github_url: str = Field(..., regex=r'^https?://github\.com/[\w-]+/[\w-]+$')
    image_url: Optional[str] = Field(None, max_length=500)
    tags: Optional[List[str]] = Field(None, max_items=10)

class ProjectCreate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id: str
    user_id: str
    status: ProjectStatus
    current_funding: float = 0.0
    funding_percentage: float = 0.0
    backer_count: int = 0
    audit_score: Optional[float] = None
    security_level: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    user: UserResponse

    class Config:
        orm_mode = True

class ProjectList(BaseModel):
    items: List[ProjectResponse]
    total: int
    page: int
    limit: int
    total_pages: int

# Audit schemas
class AuditRequestBase(BaseModel):
    project_id: str
    notes: Optional[str] = Field(None, max_length=1000)

class AuditRequestCreate(AuditRequestBase):
    pass

class AuditRequestResponse(AuditRequestBase):
    id: str
    user_id: str
    status: AuditStatus
    created_at: datetime
    updated_at: datetime
    project: ProjectResponse

    class Config:
        orm_mode = True

class AuditBadgeResponse(BaseModel):
    id: str
    project_id: str
    project_name: str
    audit_score: float = Field(..., ge=0, le=100)
    security_level: str
    issued_date: datetime
    expiry_date: datetime
    badge_url: str
    findings: Optional[List[dict]] = None
    recommendations: Optional[List[str]] = None
    is_active: bool = True

    class Config:
        orm_mode = True

# Funding schemas
class FundingBase(BaseModel):
    project_id: str
    amount: float = Field(..., gt=0)
    payment_method: str = Field(..., regex=r'^[a-zA-Z0-9_-]+$')
    notes: Optional[str] = Field(None, max_length=500)

class FundingCreate(FundingBase):
    pass

class FundingResponse(FundingBase):
    id: str
    user_id: str
    status: FundingStatus
    transaction_id: Optional[str] = None
    payment_gateway: Optional[str] = None
    paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    user: UserResponse
    project: ProjectResponse

    class Config:
        orm_mode = True

# Payment schemas
class PaymentMethodResponse(BaseModel):
    id: str
    name: str
    type: str
    description: Optional[str]
    is_active: bool
    fees: Optional[dict] = None
    minimum_amount: float = 0
    maximum_amount: float = 999999999

    class Config:
        orm_mode = True

class PaymentProcessRequest(BaseModel):
    funding_id: str
    payment_method: str
    payment_details: Optional[dict] = None

class PaymentProcessResponse(BaseModel):
    success: bool
    message: str
    transaction_id: str
    payment_url: Optional[str] = None
    qr_code: Optional[str] = None
    amount: float
    status: str

# Error schemas
class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    message: str
    details: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Validation schemas
class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    limit: int = Field(10, ge=1, le=100)

class SearchParams(BaseModel):
    search: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = None
    status: Optional[str] = None
    sort_by: Optional[str] = Field(None, regex=r'^[a-zA-Z0-9_-]+$')
    sort_order: Optional[str] = Field("desc", regex=r'^(asc|desc)$')