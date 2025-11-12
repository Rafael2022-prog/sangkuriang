"""
Database models for SANGKURIANG API
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, Float, JSON, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from datetime import datetime

Base = declarative_base()

class UserRole(str, enum.Enum):
    USER = "user"
    DEVELOPER = "developer"
    ADMIN = "admin"
    MODERATOR = "moderator"

class ProjectStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FUNDING = "funding"
    FUNDED = "funded"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class FundingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class AuditStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    
    # KYC Information
    kyc_status = Column(String(20), default="pending", nullable=False)
    kyc_verified_at = Column(DateTime, nullable=True)
    identity_document_url = Column(String(500), nullable=True)
    selfie_verification_url = Column(String(500), nullable=True)
    
    # Wallet Information
    wallet_addresses = Column(JSON, default=dict)
    
    # Profile Information
    bio = Column(Text, nullable=True)
    location = Column(String(100), nullable=True)
    website = Column(String(255), nullable=True)
    github_username = Column(String(50), nullable=True)
    
    # Role and Permissions
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    projects = relationship("Project", back_populates="owner")
    fundings = relationship("Funding", back_populates="user")
    audit_requests = relationship("AuditRequest", back_populates="requester")

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Project Information
    title = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)
    short_description = Column(String(500), nullable=False)
    
    # Technical Details
    category = Column(String(50), nullable=False, index=True)  # encryption, hashing, signature, etc.
    programming_language = Column(String(50), nullable=False)
    github_repository = Column(String(500), nullable=False)
    documentation_url = Column(String(500), nullable=True)
    demo_url = Column(String(500), nullable=True)
    
    # Funding Information
    funding_goal = Column(Float, nullable=False)  # IDR
    current_funding = Column(Float, default=0.0, nullable=False)
    min_funding_amount = Column(Float, default=100000.0, nullable=False)  # IDR
    max_funding_amount = Column(Float, nullable=True)  # IDR
    
    # Timeline
    funding_deadline = Column(DateTime(timezone=True), nullable=False)
    estimated_completion_date = Column(DateTime(timezone=True), nullable=True)
    
    # Status and Visibility
    status = Column(Enum(ProjectStatus), default=ProjectStatus.DRAFT, nullable=False, index=True)
    is_featured = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Audit Information
    audit_score = Column(Integer, nullable=True)
    audit_status = Column(Enum(AuditStatus), default=AuditStatus.PENDING, nullable=False)
    last_audit_at = Column(DateTime(timezone=True), nullable=True)
    
    # Media
    cover_image_url = Column(String(500), nullable=True)
    screenshots = Column(JSON, default=list)
    video_url = Column(String(500), nullable=True)
    
    # Statistics
    view_count = Column(Integer, default=0, nullable=False)
    like_count = Column(Integer, default=0, nullable=False)
    share_count = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    owner = relationship("User", back_populates="projects")
    fundings = relationship("Funding", back_populates="project")
    audit_requests = relationship("AuditRequest", back_populates="project")

class Funding(Base):
    __tablename__ = "fundings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Funding Details
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="IDR", nullable=False)
    payment_method = Column(String(50), nullable=False)  # ovo, gopay, dana, bank_transfer, crypto
    
    # Payment Information
    status = Column(Enum(FundingStatus), default=FundingStatus.PENDING, nullable=False, index=True)
    transaction_id = Column(String(255), nullable=True)
    payment_gateway = Column(String(50), nullable=True)  # midtrans, xendit
    payment_proof_url = Column(String(500), nullable=True)
    
    # Refund Information
    refund_reason = Column(Text, nullable=True)
    refunded_at = Column(DateTime(timezone=True), nullable=True)
    refund_amount = Column(Float, nullable=True)
    
    # Anonymous Funding
    is_anonymous = Column(Boolean, default=False, nullable=False)
    display_name = Column(String(100), nullable=True)
    
    # Message from Funder
    message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="fundings")
    user = relationship("User", back_populates="fundings")

class AuditRequest(Base):
    __tablename__ = "audit_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    requester_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Audit Information
    status = Column(Enum(AuditStatus), default=AuditStatus.PENDING, nullable=False, index=True)
    priority = Column(String(20), default="normal", nullable=False)  # low, normal, high, urgent
    
    # Results
    overall_score = Column(Integer, nullable=True)
    security_score = Column(Integer, nullable=True)
    performance_score = Column(Integer, nullable=True)
    compliance_score = Column(Integer, nullable=True)
    
    # Detailed Results
    vulnerabilities = Column(JSON, default=list)
    recommendations = Column(JSON, default=list)
    audit_report_url = Column(String(500), nullable=True)
    badge_url = Column(String(500), nullable=True)
    
    # Processing Information
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    processing_time_seconds = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="audit_requests")
    requester = relationship("User", back_populates="audit_requests")

class AuditBadge(Base):
    __tablename__ = "audit_badges"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    audit_request_id = Column(UUID(as_uuid=True), ForeignKey("audit_requests.id"), nullable=False)
    
    # Badge Information
    badge_type = Column(String(50), nullable=False)  # security, performance, compliance
    score = Column(Integer, nullable=False)
    badge_url = Column(String(500), nullable=False)
    badge_svg = Column(Text, nullable=False)
    
    # Validation
    is_valid = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class PaymentMethod(Base):
    __tablename__ = "payment_methods"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Payment Method Details
    method_type = Column(String(50), nullable=False)  # ovo, gopay, dana, bank_account, crypto_wallet
    provider = Column(String(50), nullable=False)
    account_identifier = Column(String(255), nullable=False)
    account_name = Column(String(255), nullable=True)
    
    # Verification
    is_verified = Column(Boolean, default=False, nullable=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Notification Details
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), nullable=False)  # info, warning, success, error
    
    # Action
    action_url = Column(String(500), nullable=True)
    action_text = Column(String(100), nullable=True)
    
    # Status
    is_read = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())