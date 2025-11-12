"""
Audit Service for SANGKURIANG
Handles automated auditing of GitHub repositories
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import json
from loguru import logger

from .github_service import GitHubService
from ..crypto_audit.engine import CryptoAuditEngine, AuditResult
from ..models import AuditRequest, Project, User, AuditStatus
from ..database import get_db

class AuditService:
    """Service for automated code auditing"""
    
    def __init__(self):
        self.github_service = GitHubService()
        self.audit_engine = CryptoAuditEngine()
        
    async def trigger_automated_audit(self, project_id: str, github_url: str, user_id: str) -> str:
        """Trigger automated audit for a project"""
        try:
            logger.info(f"Starting automated audit for project {project_id}")
            
            # Create audit request record
            audit_request = AuditRequest(
                project_id=project_id,
                user_id=user_id,
                github_url=github_url,
                status=AuditStatus.PENDING,
                created_at=datetime.utcnow()
            )
            
            db = next(get_db())
            db.add(audit_request)
            db.commit()
            db.refresh(audit_request)
            
            # Start audit process in background
            asyncio.create_task(self._perform_audit(audit_request.id, project_id, github_url))
            
            return audit_request.id
            
        except Exception as e:
            logger.error(f"Failed to trigger automated audit: {str(e)}")
            raise
            
    async def _perform_audit(self, audit_request_id: str, project_id: str, github_url: str):
        """Perform the actual audit process"""
        db = next(get_db())
        audit_request = None
        
        try:
            # Update status to in_progress
            audit_request = db.query(AuditRequest).filter(AuditRequest.id == audit_request_id).first()
            if audit_request:
                audit_request.status = AuditStatus.IN_PROGRESS
                audit_request.started_at = datetime.utcnow()
                db.commit()
                
            logger.info(f"Cloning repository for audit: {github_url}")
            
            # Clone repository
            repo_path = await self.github_service.clone_repository(github_url, project_id)
            
            # Get repository information
            owner, repo_name = self.github_service._parse_github_url(github_url)
            repo_info = await self.github_service.get_repository_info(owner, repo_name)
            languages = await self.github_service.get_repository_languages(owner, repo_name)
            commit_info = await self.github_service.get_commit_info(repo_path)
            file_tree = await self.github_service.get_file_tree(repo_path)
            
            # Prepare audit metadata
            audit_metadata = {
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
                    "size": repo_info.get("size", 0)
                },
                "commit": commit_info,
                "file_tree": file_tree,
                "audit_timestamp": datetime.utcnow().isoformat()
            }
            
            # Perform crypto audit
            logger.info("Performing crypto audit")
            audit_result = self.audit_engine.audit_project(repo_path, audit_metadata)
            
            # Update audit request with results
            if audit_request:
                audit_request.status = AuditStatus.COMPLETED
                audit_request.completed_at = datetime.utcnow()
                audit_result.audit_request_id = audit_request_id
                audit_request.results = audit_result.to_dict()
                
                # Generate badge URL
                badge_url = self._generate_badge_url(audit_result)
                audit_request.badge_url = badge_url
                
                db.commit()
                
            logger.info(f"Audit completed for project {project_id}")
            
            # Clean up repository
            await self.github_service.cleanup_repository(project_id)
            
        except Exception as e:
            logger.error(f"Audit failed for project {project_id}: {str(e)}")
            
            # Update audit request with error
            if audit_request:
                audit_request.status = AuditStatus.FAILED
                audit_request.error_message = str(e)
                audit_request.completed_at = datetime.utcnow()
                db.commit()
                
            # Clean up repository on error
            try:
                await self.github_service.cleanup_repository(project_id)
            except:
                pass
                
    def _generate_badge_url(self, audit_result: AuditResult) -> str:
        """Generate badge URL based on audit results"""
        # Determine badge color based on score
        if audit_result.overall_score >= 90:
            color = "brightgreen"
            status = "Excellent"
        elif audit_result.overall_score >= 75:
            color = "green"
            status = "Good"
        elif audit_result.overall_score >= 60:
            color = "yellow"
            status = "Fair"
        elif audit_result.overall_score >= 40:
            color = "orange"
            status = "Needs Improvement"
        else:
            color = "red"
            status = "Poor"
            
        # Generate shields.io badge URL
        badge_url = f"https://img.shields.io/badge/SANGKURIANG%20AUDIT-{status}-{color}"
        return badge_url
        
    async def get_audit_results(self, audit_request_id: str) -> Optional[Dict[str, Any]]:
        """Get audit results for a specific request"""
        try:
            db = next(get_db())
            audit_request = db.query(AuditRequest).filter(AuditRequest.id == audit_request_id).first()
            
            if not audit_request:
                return None
                
            return {
                "id": audit_request.id,
                "project_id": audit_request.project_id,
                "status": audit_request.status.value,
                "github_url": audit_request.github_url,
                "created_at": audit_request.created_at.isoformat(),
                "started_at": audit_request.started_at.isoformat() if audit_request.started_at else None,
                "completed_at": audit_request.completed_at.isoformat() if audit_request.completed_at else None,
                "badge_url": audit_request.badge_url,
                "error_message": audit_request.error_message,
                "results": audit_request.results
            }
            
        except Exception as e:
            logger.error(f"Failed to get audit results: {str(e)}")
            return None
            
    async def get_project_audits(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all audit requests for a project"""
        try:
            db = next(get_db())
            audits = db.query(AuditRequest).filter(AuditRequest.project_id == project_id).order_by(AuditRequest.created_at.desc()).all()
            
            return [{
                "id": audit.id,
                "status": audit.status.value,
                "github_url": audit.github_url,
                "created_at": audit.created_at.isoformat(),
                "completed_at": audit.completed_at.isoformat() if audit.completed_at else None,
                "badge_url": audit.badge_url,
                "overall_score": audit.results.get("overall_score") if audit.results else None
            } for audit in audits]
            
        except Exception as e:
            logger.error(f"Failed to get project audits: {str(e)}")
            return []
            
    async def handle_webhook(self, payload: bytes, signature: str) -> bool:
        """Handle GitHub webhook for repository updates"""
        try:
            # Validate webhook signature
            if not await self.github_service.validate_webhook_signature(payload, signature):
                logger.warning("Invalid webhook signature")
                return False
                
            # Parse webhook payload
            data = json.loads(payload)
            
            # Check if it's a push event
            if data.get("action") == "synchronize" or "pusher" in data:
                # Extract repository information
                repository = data.get("repository", {})
                repo_name = repository.get("name")
                repo_owner = repository.get("owner", {}).get("login")
                
                if repo_name and repo_owner:
                    github_url = f"https://github.com/{repo_owner}/{repo_name}"
                    
                    # Find projects with this GitHub URL
                    db = next(get_db())
                    projects = db.query(Project).filter(Project.github_url == github_url).all()
                    
                    # Trigger audits for all matching projects
                    for project in projects:
                        logger.info(f"Triggering audit for project {project.id} due to webhook")
                        await self.trigger_automated_audit(project.id, github_url, project.user_id)
                        
            return True
            
        except Exception as e:
            logger.error(f"Failed to handle webhook: {str(e)}")
            return False