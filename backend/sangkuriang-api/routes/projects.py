from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from database import get_db
from models.project import Project, ProjectCategory, ProjectFunding, ProjectUpdate
from models.user import User
from schemas.project import (
    ProjectCreate, ProjectResponse, ProjectUpdate as ProjectUpdateSchema,
    ProjectListResponse, ProjectFundingCreate, ProjectFundingResponse,
    ProjectCategoryResponse, ProjectUpdateCreate, ProjectUpdateResponse
)
from utils.security import get_current_user, validate_github_url
from utils.pagination import paginate_query
import uuid
from datetime import datetime, timedelta

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new project."""
    # Validate GitHub URL if provided
    if project_data.github_url and not validate_github_url(project_data.github_url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid GitHub repository URL"
        )
    
    # Validate deadline
    if project_data.deadline and project_data.deadline <= datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deadline must be in the future"
        )
    
    # Validate funding goal
    if project_data.funding_goal <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Funding goal must be greater than 0"
        )
    
    # Create project
    project = Project(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        title=project_data.title,
        description=project_data.description,
        category=project_data.category,
        funding_goal=project_data.funding_goal,
        deadline=project_data.deadline,
        github_url=project_data.github_url,
        image_url=project_data.image_url,
        tags=project_data.tags or [],
        status="active",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(project)
    db.commit()
    db.refresh(project)
    
    return project

@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("created_at"),
    sort_order: Optional[str] = Query("desc"),
    db: Session = Depends(get_db)
):
    """List all projects with filtering and pagination."""
    query = db.query(Project)
    
    # Apply filters
    if search:
        query = query.filter(
            or_(
                Project.title.ilike(f"%{search}%"),
                Project.description.ilike(f"%{search}%"),
                Project.tags.contains([search])
            )
        )
    
    if category:
        query = query.filter(Project.category == category)
    
    if status:
        query = query.filter(Project.status == status)
    
    # Apply sorting
    if sort_by == "funding_percentage":
        query = query.order_by(
            func.coalesce(Project.current_funding / Project.funding_goal, 0).desc() 
            if sort_order == "desc" else 
            func.coalesce(Project.current_funding / Project.funding_goal, 0).asc()
        )
    elif sort_by == "created_at":
        query = query.order_by(
            Project.created_at.desc() if sort_order == "desc" else Project.created_at.asc()
        )
    elif sort_by == "deadline":
        query = query.order_by(
            Project.deadline.asc() if sort_order == "asc" else Project.deadline.desc()
        )
    
    # Paginate results
    total = query.count()
    projects = paginate_query(query, page, limit).all()
    
    total_pages = (total + limit - 1) // limit
    
    return ProjectListResponse(
        items=projects,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages
    )

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Get project details by ID."""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return project

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_data: ProjectUpdateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update project details."""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check ownership
    if project.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this project"
        )
    
    # Validate GitHub URL if provided
    if project_data.github_url and not validate_github_url(project_data.github_url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid GitHub repository URL"
        )
    
    # Update fields
    update_data = project_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(project)
    
    return project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check ownership
    if project.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this project"
        )
    
    # Soft delete (update status)
    project.status = "deleted"
    project.updated_at = datetime.utcnow()
    db.commit()

@router.get("/{project_id}/funding", response_model=List[ProjectFundingResponse])
async def get_project_funding(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Get funding history for a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    funding = db.query(ProjectFunding).filter(
        ProjectFunding.project_id == project_id
    ).order_by(ProjectFunding.created_at.desc()).all()
    
    return funding

@router.post("/{project_id}/funding", response_model=ProjectFundingResponse)
async def fund_project(
    project_id: str,
    funding_data: ProjectFundingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fund a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if project.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project is not active"
        )
    
    if project.deadline and project.deadline < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project deadline has passed"
        )
    
    if funding_data.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Funding amount must be greater than 0"
        )
    
    # Check if funding would exceed goal
    if project.current_funding + funding_data.amount > project.funding_goal:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Funding would exceed project goal"
        )
    
    # Create funding record
    funding = ProjectFunding(
        id=str(uuid.uuid4()),
        project_id=project_id,
        user_id=current_user.id,
        amount=funding_data.amount,
        payment_method=funding_data.payment_method,
        payment_status="pending",
        notes=funding_data.notes,
        created_at=datetime.utcnow()
    )
    
    db.add(funding)
    
    # Update project funding
    project.current_funding += funding_data.amount
    project.backer_count += 1
    project.updated_at = datetime.utcnow()
    
    # Check if project is fully funded
    if project.current_funding >= project.funding_goal:
        project.status = "funded"
    
    db.commit()
    db.refresh(funding)
    
    return funding

@router.get("/{project_id}/updates", response_model=List[ProjectUpdateResponse])
async def get_project_updates(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Get project updates."""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    updates = db.query(ProjectUpdate).filter(
        ProjectUpdate.project_id == project_id
    ).order_by(ProjectUpdate.created_at.desc()).all()
    
    return updates

@router.post("/{project_id}/updates", response_model=ProjectUpdateResponse)
async def create_project_update(
    project_id: str,
    update_data: ProjectUpdateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a project update."""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check ownership
    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create updates for this project"
        )
    
    update = ProjectUpdate(
        id=str(uuid.uuid4()),
        project_id=project_id,
        title=update_data.title,
        content=update_data.content,
        update_type=update_data.update_type,
        created_at=datetime.utcnow()
    )
    
    db.add(update)
    db.commit()
    db.refresh(update)
    
    return update

@router.get("/categories/list", response_model=List[ProjectCategoryResponse])
async def get_project_categories():
    """Get available project categories."""
    return [
        {"id": "cryptography", "name": "Kriptografi", "description": "Algoritma dan protokol kriptografi"},
        {"id": "blockchain", "name": "Blockchain", "description": "Teknologi blockchain dan distributed ledger"},
        {"id": "security", "name": "Keamanan Siber", "description": "Solusi keamanan digital"},
        {"id": "privacy", "name": "Privasi Data", "description": "Proteksi privasi dan data"},
        {"id": "authentication", "name": "Otentikasi", "description": "Sistem otentikasi dan akses"},
        {"id": "quantum", "name": "Kriptografi Kuantum", "description": "Kriptografi tahan kuantum"},
        {"id": "tools", "name": "Tools & Library", "description": "Tools dan library kriptografi"},
        {"id": "research", "name": "Penelitian", "description": "Penelitian dan pengembangan"}
    ]

@router.get("/featured", response_model=List[ProjectResponse])
async def get_featured_projects(
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """Get featured projects."""
    # Get projects with highest funding percentage or recent activity
    projects = db.query(Project).filter(
        Project.status == "active",
        Project.current_funding > 0
    ).order_by(
        func.coalesce(Project.current_funding / Project.funding_goal, 0).desc()
    ).limit(limit).all()
    
    return projects

@router.get("/trending", response_model=List[ProjectResponse])
async def get_trending_projects(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get trending projects based on recent activity."""
    # Get projects with recent funding or updates
    from datetime import timedelta
    
    recent_date = datetime.utcnow() - timedelta(days=7)
    
    projects = db.query(Project).filter(
        Project.status == "active",
        Project.created_at >= recent_date
    ).order_by(Project.created_at.desc()).limit(limit).all()
    
    return projects