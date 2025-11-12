"""
GitHub Integration Routes for SANGKURIANG
Handles GitHub webhooks and automated audit triggers
"""

from fastapi import APIRouter, HTTPException, Depends, Header, Request
from typing import Dict, Any, Optional
import json
from loguru import logger

from ..services.audit_service import AuditService
from ..services.github_service import GitHubService
from ..database import get_db
from ..models import User, Project
from ..utils.security import get_current_user

router = APIRouter(prefix="/github", tags=["github"])

@router.post("/webhook")
async def github_webhook(
    request: Request,
    x_github_event: Optional[str] = Header(None),
    x_hub_signature_256: Optional[str] = Header(None)
):
    """GitHub webhook endpoint for repository events"""
    try:
        # Get raw payload
        payload = await request.body()
        
        logger.info(f"Received GitHub webhook event: {x_github_event}")
        
        # Handle different GitHub events
        if x_github_event == "push":
            audit_service = AuditService()
            success = await audit_service.handle_webhook(payload, x_hub_signature_256)
            
            if success:
                return {"status": "success", "message": "Webhook processed"}
            else:
                raise HTTPException(status_code=400, detail="Webhook processing failed")
                
        elif x_github_event == "pull_request":
            # Handle pull request events (future enhancement)
            data = json.loads(payload)
            action = data.get("action")
            
            if action in ["opened", "synchronize", "reopened"]:
                # Could trigger audits for PRs
                logger.info(f"Pull request {action} event received")
                
        return {"status": "success", "message": "Event received"}
        
    except Exception as e:
        logger.error(f"GitHub webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/audit/trigger/{project_id}")
async def trigger_automated_audit(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Trigger automated audit for a project"""
    try:
        db = next(get_db())
        
        # Get project
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
            
        # Check if user owns the project or is admin
        if project.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Not authorized")
            
        # Validate GitHub URL
        if not project.github_url:
            raise HTTPException(status_code=400, detail="Project has no GitHub URL")
            
        # Trigger audit
        audit_service = AuditService()
        audit_request_id = await audit_service.trigger_automated_audit(
            project_id, project.github_url, current_user.id
        )
        
        return {
            "status": "success",
            "audit_request_id": audit_request_id,
            "message": "Automated audit triggered successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger audit: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to trigger audit")

@router.get("/audit/results/{audit_request_id}")
async def get_audit_results(
    audit_request_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get audit results for a specific request"""
    try:
        audit_service = AuditService()
        results = await audit_service.get_audit_results(audit_request_id)
        
        if not results:
            raise HTTPException(status_code=404, detail="Audit request not found")
            
        # Check if user owns the project or is admin
        db = next(get_db())
        project = db.query(Project).filter(Project.id == results["project_id"]).first()
        
        if project.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Not authorized")
            
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get audit results: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get audit results")

@router.get("/audit/project/{project_id}")
async def get_project_audits(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all audits for a project"""
    try:
        db = next(get_db())
        
        # Get project
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
            
        # Check if user owns the project or is admin
        if project.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Not authorized")
            
        audit_service = AuditService()
        audits = await audit_service.get_project_audits(project_id)
        
        return {
            "status": "success",
            "project_id": project_id,
            "audits": audits,
            "total": len(audits)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project audits: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get project audits")

@router.get("/repository/info")
async def get_repository_info(
    github_url: str,
    current_user: User = Depends(get_current_user)
):
    """Get repository information from GitHub"""
    try:
        github_service = GitHubService()
        owner, repo = github_service._parse_github_url(github_url)
        
        repo_info = await github_service.get_repository_info(owner, repo)
        languages = await github_service.get_repository_languages(owner, repo)
        
        return {
            "status": "success",
            "repository": {
                "name": repo_info.get("name"),
                "description": repo_info.get("description"),
                "stars": repo_info.get("stargazers_count", 0),
                "forks": repo_info.get("forks_count", 0),
                "language": repo_info.get("language"),
                "languages": languages,
                "topics": repo_info.get("topics", []),
                "license": repo_info.get("license", {}).get("name") if repo_info.get("license") else None,
                "created_at": repo_info.get("created_at"),
                "updated_at": repo_info.get("updated_at"),
                "size": repo_info.get("size", 0),
                "default_branch": repo_info.get("default_branch"),
                "open_issues": repo_info.get("open_issues_count", 0),
                "archived": repo_info.get("archived", False),
                "fork": repo_info.get("fork", False)
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get repository info: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get repository information")

@router.get("/repository/contents")
async def get_repository_contents(
    github_url: str,
    path: str = "",
    current_user: User = Depends(get_current_user)
):
    """Get repository contents from GitHub"""
    try:
        github_service = GitHubService()
        owner, repo = github_service._parse_github_url(github_url)
        
        contents = await github_service.get_repository_contents(owner, repo, path)
        
        return {
            "status": "success",
            "contents": contents
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get repository contents: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get repository contents")