"""
GitHub Service for SANGKURIANG
Handles repository cloning, webhook processing, and GitHub API integration
"""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import httpx
import hmac
import hashlib
import json
import re
from loguru import logger

class GitHubService:
    """Service for GitHub repository operations"""
    
    def __init__(self, github_token: Optional[str] = None, webhook_secret: Optional[str] = None):
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.webhook_secret = webhook_secret or os.getenv("GITHUB_WEBHOOK_SECRET")
        self.base_url = "https://api.github.com"
        self.clone_dir = Path(os.getenv("CLONE_DIR", "/tmp/sangkuriang/repos"))
        self.clone_dir.mkdir(parents=True, exist_ok=True)
        
    async def validate_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Validate GitHub webhook signature"""
        if not self.webhook_secret:
            logger.warning("Webhook secret not configured")
            return True
            
        # GitHub signatures start with 'sha256='
        if not signature.startswith("sha256="):
            return False
            
        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Use hmac.compare_digest for timing attack resistance
        return hmac.compare_digest(signature[7:], expected_signature)
        
    async def get_repository_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get repository information from GitHub API"""
        headers = {}
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
            
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/repos/{owner}/{repo}",
                headers=headers
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to get repository info: {response.status_code}")
                
            return response.json()
            
    async def get_repository_languages(self, owner: str, repo: str) -> Dict[str, int]:
        """Get programming languages used in repository"""
        headers = {}
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
            
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/repos/{owner}/{repo}/languages",
                headers=headers
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to get repository languages: {response.status_code}")
                
            return response.json()
            
    async def get_repository_contents(self, owner: str, repo: str, path: str = "") -> List[Dict[str, Any]]:
        """Get repository contents"""
        headers = {}
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
            
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/repos/{owner}/{repo}/contents/{path}",
                headers=headers
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to get repository contents: {response.status_code}")
                
            return response.json()
            
    async def clone_repository(self, github_url: str, project_id: str) -> str:
        """Clone GitHub repository for audit"""
        try:
            # Parse GitHub URL
            owner, repo = self._parse_github_url(github_url)
            
            # Create project-specific directory
            project_dir = self.clone_dir / project_id
            if project_dir.exists():
                shutil.rmtree(project_dir)
            project_dir.mkdir(parents=True)
            
            # Clone repository
            clone_url = f"https://github.com/{owner}/{repo}.git"
            if self.github_token:
                clone_url = f"https://{self.github_token}@github.com/{owner}/{repo}.git"
                
            logger.info(f"Cloning repository {owner}/{repo} to {project_dir}")
            
            # Use subprocess to clone
            result = subprocess.run([
                "git", "clone", "--depth", "1", clone_url, str(project_dir)
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                raise Exception(f"Failed to clone repository: {result.stderr}")
                
            logger.info(f"Successfully cloned repository to {project_dir}")
            return str(project_dir)
            
        except subprocess.TimeoutExpired:
            raise Exception("Repository cloning timed out")
        except Exception as e:
            logger.error(f"Failed to clone repository: {str(e)}")
            raise
            
    async def update_repository(self, project_id: str, github_url: str) -> str:
        """Update existing cloned repository"""
        try:
            project_dir = self.clone_dir / project_id
            
            if not project_dir.exists():
                return await self.clone_repository(github_url, project_id)
                
            # Parse GitHub URL
            owner, repo = self._parse_github_url(github_url)
            
            logger.info(f"Updating repository {owner}/{repo} in {project_dir}")
            
            # Pull latest changes
            result = subprocess.run([
                "git", "-C", str(project_dir), "pull", "--depth", "1"
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                # If pull fails, re-clone
                shutil.rmtree(project_dir)
                return await self.clone_repository(github_url, project_id)
                
            logger.info(f"Successfully updated repository in {project_dir}")
            return str(project_dir)
            
        except Exception as e:
            logger.error(f"Failed to update repository: {str(e)}")
            raise
            
    def _parse_github_url(self, github_url: str) -> tuple[str, str]:
        """Parse GitHub URL to extract owner and repository name"""
        # Remove trailing .git if present
        github_url = github_url.rstrip('/')
        if github_url.endswith('.git'):
            github_url = github_url[:-4]
            
        # Parse different GitHub URL formats
        patterns = [
            r"github\.com/([^/]+)/([^/]+)",
            r"github\.com:([^/]+)/([^/]+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, github_url)
            if match:
                owner, repo = match.groups()
                return owner, repo
                
        raise ValueError(f"Invalid GitHub URL format: {github_url}")
        
    async def cleanup_repository(self, project_id: str) -> bool:
        """Clean up cloned repository after audit"""
        try:
            project_dir = self.clone_dir / project_id
            if project_dir.exists():
                shutil.rmtree(project_dir)
                logger.info(f"Cleaned up repository for project {project_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to cleanup repository: {str(e)}")
            return False
            
    async def get_commit_info(self, project_path: str) -> Dict[str, Any]:
        """Get latest commit information from cloned repository"""
        try:
            # Get latest commit hash
            result = subprocess.run([
                "git", "-C", project_path, "rev-parse", "HEAD"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                return {}
                
            commit_hash = result.stdout.strip()
            
            # Get commit information
            result = subprocess.run([
                "git", "-C", project_path, "log", "-1", "--format=%H|%an|%ae|%ad|%s"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                return {"commit_hash": commit_hash}
                
            parts = result.stdout.strip().split('|')
            if len(parts) >= 5:
                return {
                    "commit_hash": parts[0],
                    "author_name": parts[1],
                    "author_email": parts[2],
                    "commit_date": parts[3],
                    "commit_message": parts[4]
                }
                
            return {"commit_hash": commit_hash}
            
        except Exception as e:
            logger.error(f"Failed to get commit info: {str(e)}")
            return {}
            
    async def get_file_tree(self, project_path: str, max_depth: int = 3) -> List[Dict[str, Any]]:
        """Get file tree structure of cloned repository"""
        try:
            project_path = Path(project_path)
            file_tree = []
            
            for root, dirs, files in os.walk(project_path):
                # Calculate depth
                depth = len(Path(root).relative_to(project_path).parts)
                if depth > max_depth:
                    continue
                    
                # Add directories
                for dir_name in dirs:
                    dir_path = Path(root) / dir_name
                    relative_path = dir_path.relative_to(project_path)
                    file_tree.append({
                        "type": "directory",
                        "name": dir_name,
                        "path": str(relative_path),
                        "depth": depth
                    })
                    
                # Add files
                for file_name in files:
                    file_path = Path(root) / file_name
                    if file_path.is_file():
                        relative_path = file_path.relative_to(project_path)
                        file_tree.append({
                            "type": "file",
                            "name": file_name,
                            "path": str(relative_path),
                            "size": file_path.stat().st_size,
                            "extension": file_path.suffix.lower(),
                            "depth": depth
                        })
                        
            return file_tree
            
        except Exception as e:
            logger.error(f"Failed to get file tree: {str(e)}")
            return []