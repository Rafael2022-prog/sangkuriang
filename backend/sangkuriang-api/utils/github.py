import aiohttp
import asyncio
import base64
import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
import tempfile
import os
from urllib.parse import urlparse

class GitHubAnalyzer:
    """GitHub repository analyzer for cryptographic projects."""
    
    def __init__(self, github_token: Optional[str] = None):
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"
        self.headers = {}
        
        if self.github_token:
            self.headers["Authorization"] = f"token {self.github_token}"
        
        self.headers["Accept"] = "application/vnd.github.v3+json"
        self.headers["User-Agent"] = "Sangkuriang-Audit-Engine/1.0"
    
    async def analyze_repository(self, github_url: str) -> Dict[str, Any]:
        """Analyze a GitHub repository for cryptographic content."""
        
        # Parse GitHub URL
        repo_info = self.parse_github_url(github_url)
        if not repo_info:
            return {
                "error": "Invalid GitHub URL format",
                "files": [],
                "languages": {},
                "crypto_score": 0
            }
        
        owner = repo_info["owner"]
        repo = repo_info["repo"]
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                # Get repository information
                repo_data = await self.get_repository_info(session, owner, repo)
                
                # Get repository contents
                files = await self.get_repository_files(session, owner, repo)
                
                # Analyze files for cryptographic content
                crypto_files = []
                for file_info in files:
                    if self.is_analyzable_file(file_info["path"]):
                        content = await self.get_file_content(session, owner, repo, file_info["path"])
                        if content:
                            file_analysis = await self.analyze_file_content(
                                content, file_info["path"], file_info["size"]
                            )
                            crypto_files.append(file_analysis)
                
                # Calculate cryptographic score
                crypto_score = self.calculate_crypto_score(crypto_files, repo_data)
                
                # Check for security indicators
                security_indicators = await self.check_security_indicators(session, owner, repo)
                
                return {
                    "repository": repo_data,
                    "files": crypto_files,
                    "languages": repo_data.get("languages", {}),
                    "crypto_score": crypto_score,
                    "security_indicators": security_indicators,
                    "analysis_timestamp": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                return {
                    "error": f"Failed to analyze repository: {str(e)}",
                    "files": [],
                    "languages": {},
                    "crypto_score": 0
                }
    
    def parse_github_url(self, url: str) -> Optional[Dict[str, str]]:
        """Parse GitHub URL to extract owner and repository."""
        patterns = [
            r"github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$",
            r"github\.com/([^/]+)/([^/]+)/.*"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return {
                    "owner": match.group(1),
                    "repo": match.group(2)
                }
        
        return None
    
    async def get_repository_info(self, session: aiohttp.ClientSession, owner: str, repo: str) -> Dict[str, Any]:
        """Get repository information from GitHub API."""
        url = f"{self.base_url}/repos/{owner}/{repo}"
        
        async with session.get(url) as response:
            if response.status != 200:
                raise Exception(f"Failed to get repository info: {response.status}")
            
            repo_data = await response.json()
            
            # Get languages
            languages_url = f"{self.base_url}/repos/{owner}/{repo}/languages"
            async with session.get(languages_url) as lang_response:
                if lang_response.status == 200:
                    repo_data["languages"] = await lang_response.json()
            
            return repo_data
    
    async def get_repository_files(self, session: aiohttp.ClientSession, owner: str, repo: str) -> List[Dict[str, Any]]:
        """Get all files in the repository."""
        files = []
        await self._get_tree_recursive(session, owner, repo, "", files)
        return files
    
    async def _get_tree_recursive(
        self, 
        session: aiohttp.ClientSession, 
        owner: str, 
        repo: str, 
        path: str, 
        files: List[Dict[str, Any]]
    ):
        """Recursively get repository tree."""
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
        
        async with session.get(url) as response:
            if response.status != 200:
                return
            
            contents = await response.json()
            
            if isinstance(contents, list):
                for item in contents:
                    if item["type"] == "file":
                        files.append({
                            "path": item["path"],
                            "size": item["size"],
                            "type": item["type"],
                            "download_url": item["download_url"]
                        })
                    elif item["type"] == "dir" and not self.should_skip_directory(item["path"]):
                        await self._get_tree_recursive(session, owner, repo, item["path"], files)
    
    def should_skip_directory(self, path: str) -> bool:
        """Check if directory should be skipped."""
        skip_dirs = [
            "node_modules", ".git", "__pycache__", "venv", ".venv",
            "build", "dist", "target", "out", "bin", "obj"
        ]
        
        path_parts = path.lower().split("/")
        return any(skip_dir in path_parts for skip_dir in skip_dirs)
    
    def is_analyzable_file(self, file_path: str) -> bool:
        """Check if file should be analyzed."""
        analyzable_extensions = [
            ".py", ".js", ".java", ".cpp", ".c", ".h", ".hpp",
            ".cs", ".go", ".rs", ".ts", ".swift", ".kt", ".scala"
        ]
        
        # Skip test files and documentation
        skip_patterns = [
            "test_", "_test", "spec_", "__tests__", "test/",
            "readme", "license", "changelog", "contributing",
            ".md", ".txt", ".rst", ".pdf", ".doc"
        ]
        
        file_lower = file_path.lower()
        
        # Check if should skip
        if any(pattern in file_lower for pattern in skip_patterns):
            return False
        
        # Check if has analyzable extension
        return any(file_path.endswith(ext) for ext in analyzable_extensions)
    
    async def get_file_content(self, session: aiohttp.ClientSession, owner: str, repo: str, path: str) -> Optional[str]:
        """Get file content from GitHub."""
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
        
        async with session.get(url) as response:
            if response.status != 200:
                return None
            
            data = await response.json()
            
            if data.get("encoding") == "base64":
                content = base64.b64decode(data["content"]).decode("utf-8")
                return content
            
            return data.get("content")
    
    async def analyze_file_content(self, content: str, file_path: str, file_size: int) -> Dict[str, Any]:
        """Analyze file content for cryptographic elements."""
        
        # Skip large files
        if file_size > 100000:  # 100KB limit
            return {
                "path": file_path,
                "size": file_size,
                "crypto_score": 0,
                "crypto_elements": [],
                "security_issues": [],
                "reason": "File too large"
            }
        
        crypto_elements = []
        security_issues = []
        
        # Define cryptographic patterns
        crypto_patterns = {
            "algorithms": [
                r"AES\d*", r"RSA\d*", r"SHA\d*", r"MD5", r"DES\d*", r"3DES",
                r"ChaCha20", r"XSalsa20", r"Poly1305", r"BLAKE\d*", r"Whirlpool"
            ],
            "functions": [
                r"encrypt", r"decrypt", r"hash", r"sign", r"verify", r"generateKey",
                r"deriveKey", r"pbkdf2", r"bcrypt", r"scrypt", r"argon2"
            ],
            "libraries": [
                r"crypto", r"cryptography", r"pycryptodome", r"crypto-js",
                r"bcrypt", r"node-forge", r"jsencrypt", r"tweetnacl"
            ],
            "protocols": [
                r"TLS", r"SSL", r"HTTPS", r"SSH", r"PGP", r"GPG", r"S/MIME"
            ]
        }
        
        # Security issue patterns
        security_patterns = {
            "weak_crypto": [r"MD5", r"SHA1", r"DES", r"RC4"],
            "hardcoded": [
                r"password\s*=\s*['\"][^'\"]{0,20}['\"]",
                r"secret\s*=\s*['\"][^'\"]{0,50}['\"]",
                r"key\s*=\s*['\"][a-fA-F0-9]{16,}['\"]"
            ],
            "weak_random": [r"Math\.random\(", r"random\.random\(", r"rand\(\)"]
        }
        
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Skip comments and empty lines
            if not line_stripped or line_stripped.startswith(('#', '//', '/*', '*', '--')):
                continue
            
            # Check for crypto elements
            for category, patterns in crypto_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        crypto_elements.append({
                            "type": category,
                            "element": pattern.replace('\\', ''),
                            "line": line_num,
                            "code": line_stripped[:100]  # Limit code display
                        })
            
            # Check for security issues
            for issue_type, patterns in security_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        severity = "high" if issue_type == "weak_crypto" else "medium"
                        security_issues.append({
                            "type": issue_type,
                            "severity": severity,
                            "line": line_num,
                            "code": line_stripped[:100],
                            "description": self.get_security_issue_description(issue_type, pattern)
                        })
        
        # Calculate crypto score
        crypto_score = min(100, len(crypto_elements) * 5)
        
        # Reduce score for security issues
        crypto_score -= len(security_issues) * 10
        crypto_score = max(0, crypto_score)
        
        return {
            "path": file_path,
            "size": file_size,
            "crypto_score": crypto_score,
            "crypto_elements": crypto_elements,
            "security_issues": security_issues,
            "lines_analyzed": len(lines)
        }
    
    def get_security_issue_description(self, issue_type: str, pattern: str) -> str:
        """Get description for security issue."""
        descriptions = {
            "weak_crypto": f"Usage of weak cryptographic algorithm detected: {pattern}",
            "hardcoded": "Hardcoded secret or key detected in source code",
            "weak_random": "Weak random number generator used for cryptographic purposes"
        }
        return descriptions.get(issue_type, "Security issue detected")
    
    def calculate_crypto_score(self, crypto_files: List[Dict[str, Any]], repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall cryptographic score for repository."""
        
        if not crypto_files:
            return {
                "overall_score": 0,
                "category_scores": {},
                "assessment": "No cryptographic content found"
            }
        
        # Calculate average file score
        total_score = sum(f.get("crypto_score", 0) for f in crypto_files)
        avg_file_score = total_score / len(crypto_files) if crypto_files else 0
        
        # Language-based scoring
        languages = repo_data.get("languages", {})
        language_bonus = 0
        
        # Bonus for security-focused languages
        if "Python" in languages:
            language_bonus += 10
        if "Rust" in languages:
            language_bonus += 15
        if "Go" in languages:
            language_bonus += 10
        
        # Security issues penalty
        total_issues = sum(len(f.get("security_issues", [])) for f in crypto_files)
        issue_penalty = min(30, total_issues * 5)
        
        # Calculate final score
        final_score = max(0, min(100, avg_file_score + language_bonus - issue_penalty))
        
        # Determine assessment
        if final_score >= 80:
            assessment = "Excellent cryptographic implementation"
        elif final_score >= 60:
            assessment = "Good cryptographic foundation with room for improvement"
        elif final_score >= 40:
            assessment = "Basic cryptographic implementation, needs enhancement"
        else:
            assessment = "Poor cryptographic implementation, requires significant improvement"
        
        return {
            "overall_score": round(final_score, 2),
            "category_scores": {
                "file_analysis": round(avg_file_score, 2),
                "language_bonus": language_bonus,
                "issue_penalty": -issue_penalty
            },
            "total_issues": total_issues,
            "assessment": assessment
        }
    
    async def check_security_indicators(self, session: aiohttp.ClientSession, owner: str, repo: str) -> Dict[str, Any]:
        """Check for security indicators in repository."""
        
        indicators = {
            "has_security_policy": False,
            "has_security_advisories": False,
            "has_dependabot": False,
            "has_codeql": False,
            "recent_commits": 0,
            "contributor_count": 0
        }
        
        try:
            # Check for security policy
            security_url = f"{self.base_url}/repos/{owner}/{repo}/contents/SECURITY.md"
            async with session.get(security_url) as response:
                indicators["has_security_policy"] = response.status == 200
            
            # Check for dependabot alerts
            dependabot_url = f"{self.base_url}/repos/{owner}/{repo}/vulnerability-alerts"
            async with session.get(dependabot_url) as response:
                indicators["has_dependabot"] = response.status == 204
            
            # Get recent commits
            commits_url = f"{self.base_url}/repos/{owner}/{repo}/commits"
            async with session.get(commits_url, params={"per_page": 5}) as response:
                if response.status == 200:
                    commits = await response.json()
                    indicators["recent_commits"] = len(commits)
            
            # Get contributors
            contributors_url = f"{self.base_url}/repos/{owner}/{repo}/contributors"
            async with session.get(contributors_url, params={"per_page": 10}) as response:
                if response.status == 200:
                    contributors = await response.json()
                    indicators["contributor_count"] = len(contributors)
            
            # Check for CodeQL (GitHub Advanced Security)
            codeql_url = f"{self.base_url}/repos/{owner}/{repo}/code-scanning/analyses"
            async with session.get(codeql_url) as response:
                indicators["has_codeql"] = response.status == 200
            
        except Exception as e:
            print(f"Error checking security indicators: {e}")
        
        return indicators
    
    async def get_repository_languages(self, session: aiohttp.ClientSession, owner: str, repo: str) -> Dict[str, int]:
        """Get repository programming languages."""
        url = f"{self.base_url}/repos/{owner}/{repo}/languages"
        
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            return {}
    
    def generate_badge_data(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate badge data from analysis results."""
        
        crypto_score = analysis_result.get("crypto_score", {}).get("overall_score", 0)
        
        # Determine badge level
        if crypto_score >= 90:
            level = "excellent"
            color = "#4CAF50"  # Green
        elif crypto_score >= 70:
            level = "good"
            color = "#FFC107"  # Amber
        elif crypto_score >= 50:
            level = "fair"
            color = "#FF9800"  # Orange
        else:
            level = "poor"
            color = "#F44336"  # Red
        
        # Count security issues
        files = analysis_result.get("files", [])
        total_issues = sum(len(f.get("security_issues", [])) for f in files)
        
        return {
            "score": crypto_score,
            "level": level,
            "color": color,
            "issues_count": total_issues,
            "files_analyzed": len(files),
            "languages": list(analysis_result.get("languages", {}).keys()),
            "badge_url": f"https://img.shields.io/badge/Crypto%20Audit-{level}-{color.replace('#', '')}"
        }