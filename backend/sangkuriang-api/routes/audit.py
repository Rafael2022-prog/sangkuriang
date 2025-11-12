from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import Optional
from sqlalchemy.orm import Session
from database import get_db
from models.project import Project
from models.audit import AuditRequest, AuditBadge, AuditFinding
from schemas.audit import (
    AuditRequestCreate, AuditRequestResponse, AuditBadgeResponse,
    AuditStatusResponse, AuditFindingResponse
)
from utils.security import get_current_user
from utils.audit_engine import AuditEngine
from utils.github import GitHubAnalyzer
import uuid
from datetime import datetime, timedelta
import asyncio

router = APIRouter(prefix="/audit", tags=["audit"])

@router.post("/request", response_model=AuditRequestResponse, status_code=status.HTTP_201_CREATED)
async def request_audit(
    audit_data: AuditRequestCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Request an audit for a project."""
    # Verify project exists and belongs to user
    project = db.query(Project).filter(Project.id == audit_data.project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if user owns the project or is admin
    if project.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to request audit for this project"
        )
    
    # Check if project has GitHub repository
    if not project.github_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project must have a GitHub repository for audit"
        )
    
    # Check for existing pending or in_progress audits
    existing_audit = db.query(AuditRequest).filter(
        AuditRequest.project_id == audit_data.project_id,
        AuditRequest.status.in_(["pending", "in_progress"])
    ).first()
    
    if existing_audit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project already has an active audit request"
        )
    
    # Create audit request
    audit_request = AuditRequest(
        id=str(uuid.uuid4()),
        project_id=audit_data.project_id,
        user_id=current_user.id,
        audit_type=audit_data.audit_type,
        priority=audit_data.priority,
        notes=audit_data.notes,
        status="pending",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(audit_request)
    db.commit()
    db.refresh(audit_request)
    
    # Start audit process in background
    background_tasks.add_task(process_audit_request, audit_request.id)
    
    return audit_request

@router.get("/request/{request_id}", response_model=AuditRequestResponse)
async def get_audit_request(
    request_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get audit request details."""
    audit_request = db.query(AuditRequest).filter(AuditRequest.id == request_id).first()
    
    if not audit_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit request not found"
        )
    
    # Check authorization
    if audit_request.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this audit request"
        )
    
    return audit_request

@router.get("/project/{project_id}/status", response_model=AuditStatusResponse)
async def get_project_audit_status(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Get audit status for a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Get latest audit request
    latest_audit = db.query(AuditRequest).filter(
        AuditRequest.project_id == project_id
    ).order_by(AuditRequest.created_at.desc()).first()
    
    # Get latest audit badge
    latest_badge = db.query(AuditBadge).filter(
        AuditBadge.project_id == project_id
    ).order_by(AuditBadge.issued_at.desc()).first()
    
    return {
        "project_id": project_id,
        "has_active_audit": latest_audit and latest_audit.status in ["pending", "in_progress"],
        "latest_audit_request": latest_audit,
        "latest_badge": latest_badge,
        "total_audits": db.query(AuditRequest).filter(
            AuditRequest.project_id == project_id
        ).count()
    }

@router.get("/project/{project_id}/badges", response_model=List[AuditBadgeResponse])
async def get_project_badges(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Get all audit badges for a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    badges = db.query(AuditBadge).filter(
        AuditBadge.project_id == project_id
    ).order_by(AuditBadge.issued_at.desc()).all()
    
    return badges

@router.get("/badge/{badge_id}", response_model=AuditBadgeResponse)
async def get_audit_badge(
    badge_id: str,
    db: Session = Depends(get_db)
):
    """Get audit badge details."""
    badge = db.query(AuditBadge).filter(AuditBadge.id == badge_id).first()
    
    if not badge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit badge not found"
        )
    
    return badge

@router.get("/badge/{badge_id}/findings", response_model=List[AuditFindingResponse])
async def get_badge_findings(
    badge_id: str,
    severity: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get findings for an audit badge."""
    badge = db.query(AuditBadge).filter(AuditBadge.id == badge_id).first()
    
    if not badge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit badge not found"
        )
    
    query = db.query(AuditFinding).filter(AuditFinding.audit_badge_id == badge_id)
    
    if severity:
        query = query.filter(AuditFinding.severity == severity)
    
    findings = query.order_by(
        AuditFinding.severity.desc(),
        AuditFinding.created_at.desc()
    ).all()
    
    return findings

@router.get("/queue/stats")
async def get_audit_queue_stats(db: Session = Depends(get_db)):
    """Get audit queue statistics."""
    stats = {
        "pending": db.query(AuditRequest).filter(AuditRequest.status == "pending").count(),
        "in_progress": db.query(AuditRequest).filter(AuditRequest.status == "in_progress").count(),
        "completed": db.query(AuditRequest).filter(AuditRequest.status == "completed").count(),
        "failed": db.query(AuditRequest).filter(AuditRequest.status == "failed").count()
    }
    
    # Get average processing time for completed audits
    completed_audits = db.query(AuditRequest).filter(
        AuditRequest.status == "completed",
        AuditRequest.completed_at.isnot(None)
    ).all()
    
    if completed_audits:
        avg_processing_time = sum(
            (audit.completed_at - audit.created_at).total_seconds() / 3600
            for audit in completed_audits
        ) / len(completed_audits)
        stats["average_processing_hours"] = round(avg_processing_time, 2)
    else:
        stats["average_processing_hours"] = 0
    
    return stats

@router.post("/request/{request_id}/cancel")
async def cancel_audit_request(
    request_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Cancel an audit request."""
    audit_request = db.query(AuditRequest).filter(AuditRequest.id == request_id).first()
    
    if not audit_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit request not found"
        )
    
    # Check authorization
    if audit_request.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to cancel this audit request"
        )
    
    # Check if can be cancelled
    if audit_request.status not in ["pending", "in_progress"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel audit request in current status"
        )
    
    audit_request.status = "cancelled"
    audit_request.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Audit request cancelled successfully"}

async def process_audit_request(audit_request_id: str):
    """Process audit request in background."""
    from database import SessionLocal
    
    db = SessionLocal()
    try:
        audit_request = db.query(AuditRequest).filter(
            AuditRequest.id == audit_request_id
        ).first()
        
        if not audit_request or audit_request.status != "pending":
            return
        
        # Update status to in_progress
        audit_request.status = "in_progress"
        audit_request.updated_at = datetime.utcnow()
        db.commit()
        
        # Get project details
        project = db.query(Project).filter(
            Project.id == audit_request.project_id
        ).first()
        
        if not project or not project.github_url:
            audit_request.status = "failed"
            audit_request.error_message = "Project or GitHub URL not found"
            audit_request.updated_at = datetime.utcnow()
            db.commit()
            return
        
        try:
            # Initialize audit engine
            audit_engine = AuditEngine()
            github_analyzer = GitHubAnalyzer()
            
            # Analyze GitHub repository
            repo_analysis = await github_analyzer.analyze_repository(project.github_url)
            
            # Perform security audit
            audit_results = await audit_engine.perform_security_audit(
                repo_analysis=repo_analysis,
                audit_type=audit_request.audit_type
            )
            
            # Create audit badge
            badge = AuditBadge(
                id=str(uuid.uuid4()),
                project_id=audit_request.project_id,
                audit_request_id=audit_request_id,
                badge_type=audit_request.audit_type,
                score=audit_results["overall_score"],
                security_level=audit_results["security_level"],
                issued_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=365),  # 1 year validity
                badge_url=f"/api/audit/badge/{str(uuid.uuid4())}/verify"
            )
            
            db.add(badge)
            
            # Create audit findings
            for finding in audit_results["findings"]:
                audit_finding = AuditFinding(
                    id=str(uuid.uuid4()),
                    audit_badge_id=badge.id,
                    finding_type=finding["type"],
                    severity=finding["severity"],
                    title=finding["title"],
                    description=finding["description"],
                    recommendation=finding.get("recommendation"),
                    file_path=finding.get("file_path"),
                    line_number=finding.get("line_number"),
                    created_at=datetime.utcnow()
                )
                db.add(audit_finding)
            
            # Update audit request
            audit_request.status = "completed"
            audit_request.completed_at = datetime.utcnow()
            audit_request.updated_at = datetime.utcnow()
            
            # Update project audit status
            project.has_audit_badge = True
            project.audit_score = audit_results["overall_score"]
            project.updated_at = datetime.utcnow()
            
            db.commit()
            
        except Exception as e:
            # Update audit request with error
            audit_request.status = "failed"
            audit_request.error_message = str(e)
            audit_request.updated_at = datetime.utcnow()
            db.commit()
            
    finally:
        db.close()