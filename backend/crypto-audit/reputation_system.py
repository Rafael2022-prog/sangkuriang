"""
Reputation System for Sangkuriang Platform

Sistem reputasi yang transparan dan terdesentralisasi untuk:
- Developer: Track record, kualitas kode, kepatuhan terhadap standar
- Proyek: Keamanan, performa, adopsi komunitas, transparansi
"""

import json
import hashlib
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from enum import Enum
import asyncio
from pathlib import Path


class ReputationCategory(Enum):
    """Kategori reputasi untuk developer dan proyek"""
    SECURITY = "security"
    PERFORMANCE = "performance"
    COMPLIANCE = "compliance"
    COMMUNITY = "community"
    TRANSPARENCY = "transparency"
    INNOVATION = "innovation"


class ReputationLevel(Enum):
    """Level reputasi berdasarkan skor"""
    NOVICE = (0, 25, "Novice", "🌱")
    DEVELOPER = (25, 50, "Developer", "🌿")
    EXPERT = (50, 75, "Expert", "🌳")
    MASTER = (75, 90, "Master", "⭐")
    LEGEND = (90, 100, "Legend", "👑")
    
    def __init__(self, min_score: int, max_score: int, title: str, emoji: str):
        self.min_score = min_score
        self.max_score = max_score
        self.title = title
        self.emoji = emoji
    
    @classmethod
    def get_level(cls, score: float) -> 'ReputationLevel':
        """Get reputation level based on score"""
        for level in cls:
            if level.min_score <= score < level.max_score:
                return level
        return cls.LEGEND  # Default to highest level


@dataclass
class ReputationScore:
    """Individual reputation score component"""
    category: ReputationCategory
    score: float  # 0-100
    weight: float  # Weight for this category
    last_updated: datetime
    evidence: List[Dict[str, Any]]  # Supporting evidence
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'category': self.category.value,
            'score': self.score,
            'weight': self.weight,
            'last_updated': self.last_updated.isoformat(),
            'evidence': self.evidence
        }


@dataclass
class DeveloperReputation:
    """Developer reputation profile"""
    developer_id: str
    name: str
    email: str
    github_username: str
    total_score: float
    level: ReputationLevel
    category_scores: Dict[ReputationCategory, ReputationScore]
    badges: Set[str]
    projects_contributed: List[str]
    reputation_history: List[Dict[str, Any]]
    created_at: datetime
    last_updated: datetime
    
    def get_weighted_score(self) -> float:
        """Calculate weighted reputation score"""
        if not self.category_scores:
            return 0.0
        
        weighted_sum = sum(
            score.score * score.weight 
            for score in self.category_scores.values()
        )
        total_weight = sum(score.weight for score in self.category_scores.values())
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def update_level(self):
        """Update reputation level based on current score"""
        self.total_score = self.get_weighted_score()
        self.level = ReputationLevel.get_level(self.total_score)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'developer_id': self.developer_id,
            'name': self.name,
            'email': self.email,
            'github_username': self.github_username,
            'total_score': self.total_score,
            'level': self.level.title,
            'level_emoji': self.level.emoji,
            'category_scores': {
                cat.value: score.to_dict() 
                for cat, score in self.category_scores.items()
            },
            'badges': list(self.badges),
            'projects_contributed': self.projects_contributed,
            'reputation_history': self.reputation_history,
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat()
        }


@dataclass
class ProjectReputation:
    """Project reputation profile"""
    project_id: str
    project_name: str
    description: str
    developer_id: str
    total_score: float
    level: ReputationLevel
    category_scores: Dict[ReputationCategory, ReputationScore]
    security_score: float
    performance_score: float
    community_score: float
    transparency_score: float
    verification_results: List[Dict[str, Any]]
    audit_history: List[Dict[str, Any]]
    funding_amount: float
    contributor_count: int
    github_stars: int
    github_forks: int
    badges: Set[str]
    reputation_history: List[Dict[str, Any]]
    created_at: datetime
    last_updated: datetime
    
    def get_weighted_score(self) -> float:
        """Calculate weighted reputation score"""
        if not self.category_scores:
            return 0.0
        
        weighted_sum = sum(
            score.score * score.weight 
            for score in self.category_scores.values()
        )
        total_weight = sum(score.weight for score in self.category_scores.values())
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def update_level(self):
        """Update reputation level based on current score"""
        self.total_score = self.get_weighted_score()
        self.level = ReputationLevel.get_level(self.total_score)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'project_id': self.project_id,
            'project_name': self.project_name,
            'description': self.description,
            'developer_id': self.developer_id,
            'total_score': self.total_score,
            'level': self.level.title,
            'level_emoji': self.level.emoji,
            'category_scores': {
                cat.value: score.to_dict() 
                for cat, score in self.category_scores.items()
            },
            'security_score': self.security_score,
            'performance_score': self.performance_score,
            'community_score': self.community_score,
            'transparency_score': self.transparency_score,
            'verification_results': self.verification_results,
            'audit_history': self.audit_history,
            'funding_amount': self.funding_amount,
            'contributor_count': self.contributor_count,
            'github_stars': self.github_stars,
            'github_forks': self.github_forks,
            'badges': list(self.badges),
            'reputation_history': self.reputation_history,
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat()
        }


class ReputationEngine:
    """Main reputation system engine"""
    
    def __init__(self, storage_dir: str = "reputation_data"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        # Storage for reputation data
        self.developer_reputations: Dict[str, DeveloperReputation] = {}
        self.project_reputations: Dict[str, ProjectReputation] = {}
        
        # Category weights (can be adjusted based on platform needs)
        self.category_weights = {
            ReputationCategory.SECURITY: 0.30,      # 30% - Very important for crypto
            ReputationCategory.PERFORMANCE: 0.25,     # 25% - Performance matters
            ReputationCategory.COMPLIANCE: 0.20,    # 20% - Regulatory compliance
            ReputationCategory.TRANSPARENCY: 0.15,  # 15% - Open source transparency
            ReputationCategory.COMMUNITY: 0.10,     # 10% - Community engagement
            ReputationCategory.INNOVATION: 0.05    # 5%  - Innovation bonus
        }
        
        # Load existing data
        self._load_reputation_data()
    
    def _load_reputation_data(self):
        """Load reputation data from storage"""
        # Load developer reputations
        dev_file = self.storage_dir / "developer_reputations.json"
        if dev_file.exists():
            try:
                with open(dev_file, 'r') as f:
                    data = json.load(f)
                    # Convert back to objects (simplified)
                    for dev_id, dev_data in data.items():
                        # Basic loading - in production, use proper deserialization
                        self.developer_reputations[dev_id] = self._create_developer_from_dict(dev_data)
            except Exception as e:
                print(f"Error loading developer reputations: {e}")
        
        # Load project reputations
        proj_file = self.storage_dir / "project_reputations.json"
        if proj_file.exists():
            try:
                with open(proj_file, 'r') as f:
                    data = json.load(f)
                    for proj_id, proj_data in data.items():
                        self.project_reputations[proj_id] = self._create_project_from_dict(proj_data)
            except Exception as e:
                print(f"Error loading project reputations: {e}")
    
    def _save_reputation_data(self):
        """Save reputation data to storage"""
        # Save developer reputations
        dev_file = self.storage_dir / "developer_reputations.json"
        try:
            dev_data = {
                dev_id: dev_rep.to_dict() 
                for dev_id, dev_rep in self.developer_reputations.items()
            }
            with open(dev_file, 'w') as f:
                json.dump(dev_data, f, indent=2)
        except Exception as e:
            print(f"Error saving developer reputations: {e}")
        
        # Save project reputations
        proj_file = self.storage_dir / "project_reputations.json"
        try:
            proj_data = {
                proj_id: proj_rep.to_dict() 
                for proj_id, proj_rep in self.project_reputations.items()
            }
            with open(proj_file, 'w') as f:
                json.dump(proj_data, f, indent=2)
        except Exception as e:
            print(f"Error saving project reputations: {e}")
    
    def _create_developer_from_dict(self, data: Dict[str, Any]) -> DeveloperReputation:
        """Create DeveloperReputation from dictionary (simplified)"""
        return DeveloperReputation(
            developer_id=data['developer_id'],
            name=data['name'],
            email=data['email'],
            github_username=data['github_username'],
            total_score=data.get('total_score', 0.0),
            level=ReputationLevel.get_level(data.get('total_score', 0.0)),
            category_scores={},  # Simplified - should be properly deserialized
            badges=set(data.get('badges', [])),
            projects_contributed=data.get('projects_contributed', []),
            reputation_history=data.get('reputation_history', []),
            created_at=datetime.fromisoformat(data['created_at']),
            last_updated=datetime.fromisoformat(data['last_updated'])
        )
    
    def _create_project_from_dict(self, data: Dict[str, Any]) -> ProjectReputation:
        """Create ProjectReputation from dictionary (simplified)"""
        return ProjectReputation(
            project_id=data['project_id'],
            project_name=data['project_name'],
            description=data['description'],
            developer_id=data['developer_id'],
            total_score=data.get('total_score', 0.0),
            level=ReputationLevel.get_level(data.get('total_score', 0.0)),
            category_scores={},  # Simplified
            security_score=data.get('security_score', 0.0),
            performance_score=data.get('performance_score', 0.0),
            community_score=data.get('community_score', 0.0),
            transparency_score=data.get('transparency_score', 0.0),
            verification_results=data.get('verification_results', []),
            audit_history=data.get('audit_history', []),
            funding_amount=data.get('funding_amount', 0.0),
            contributor_count=data.get('contributor_count', 0),
            github_stars=data.get('github_stars', 0),
            github_forks=data.get('github_forks', 0),
            badges=set(data.get('badges', [])),
            reputation_history=data.get('reputation_history', []),
            created_at=datetime.fromisoformat(data['created_at']),
            last_updated=datetime.fromisoformat(data['last_updated'])
        )
    
    async def register_developer(self, developer_id: str, name: str, email: str, 
                               github_username: str) -> DeveloperReputation:
        """Register a new developer"""
        
        if developer_id in self.developer_reputations:
            return self.developer_reputations[developer_id]
        
        # Initialize with neutral scores
        category_scores = {}
        for category in ReputationCategory:
            category_scores[category] = ReputationScore(
                category=category,
                score=50.0,  # Neutral starting score
                weight=self.category_weights[category],
                last_updated=datetime.now(),
                evidence=[{"type": "initial", "description": "Initial registration", "timestamp": datetime.now().isoformat()}]
            )
        
        dev_rep = DeveloperReputation(
            developer_id=developer_id,
            name=name,
            email=email,
            github_username=github_username,
            total_score=50.0,
            level=ReputationLevel.DEVELOPER,
            category_scores=category_scores,
            badges=set(),
            projects_contributed=[],
            reputation_history=[],
            created_at=datetime.now(),
            last_updated=datetime.now()
        )
        
        self.developer_reputations[developer_id] = dev_rep
        self._save_reputation_data()
        
        return dev_rep
    
    async def register_project(self, project_id: str, project_name: str, 
                              description: str, developer_id: str) -> ProjectReputation:
        """Register a new project"""
        
        if project_id in self.project_reputations:
            return self.project_reputations[project_id]
        
        # Initialize with neutral scores
        category_scores = {}
        for category in ReputationCategory:
            category_scores[category] = ReputationScore(
                category=category,
                score=50.0,  # Neutral starting score
                weight=self.category_weights[category],
                last_updated=datetime.now(),
                evidence=[{"type": "initial", "description": "Project registration", "timestamp": datetime.now().isoformat()}]
            )
        
        proj_rep = ProjectReputation(
            project_id=project_id,
            project_name=project_name,
            description=description,
            developer_id=developer_id,
            total_score=50.0,
            level=ReputationLevel.DEVELOPER,
            category_scores=category_scores,
            security_score=50.0,
            performance_score=50.0,
            community_score=50.0,
            transparency_score=50.0,
            verification_results=[],
            audit_history=[],
            funding_amount=0.0,
            contributor_count=0,
            github_stars=0,
            github_forks=0,
            badges=set(),
            reputation_history=[],
            created_at=datetime.now(),
            last_updated=datetime.now()
        )
        
        self.project_reputations[project_id] = proj_rep
        self._save_reputation_data()
        
        return proj_rep
    
    async def update_developer_reputation(self, developer_id: str, category: ReputationCategory,
                                        new_score: float, evidence: Dict[str, Any]):
        """Update developer reputation for a specific category"""
        
        if developer_id not in self.developer_reputations:
            raise ValueError(f"Developer {developer_id} not found")
        
        dev_rep = self.developer_reputations[developer_id]
        
        # Update category score
        if category in dev_rep.category_scores:
            old_score = dev_rep.category_scores[category].score
            dev_rep.category_scores[category].score = new_score
            dev_rep.category_scores[category].last_updated = datetime.now()
            dev_rep.category_scores[category].evidence.append(evidence)
        
        # Update total score and level
        dev_rep.update_level()
        dev_rep.last_updated = datetime.now()
        
        # Add to history
        dev_rep.reputation_history.append({
            'timestamp': datetime.now().isoformat(),
            'action': 'REPUTATION_UPDATED',
            'category': category.value,
            'old_score': old_score if 'old_score' in locals() else 0,
            'new_score': new_score,
            'evidence': evidence
        })
        
        self._save_reputation_data()
    
    async def update_project_reputation(self, project_id: str, category: ReputationCategory,
                                      new_score: float, evidence: Dict[str, Any]):
        """Update project reputation for a specific category"""
        
        if project_id not in self.project_reputations:
            raise ValueError(f"Project {project_id} not found")
        
        proj_rep = self.project_reputations[project_id]
        
        # Update category score
        if category in proj_rep.category_scores:
            old_score = proj_rep.category_scores[category].score
            proj_rep.category_scores[category].score = new_score
            proj_rep.category_scores[category].last_updated = datetime.now()
            proj_rep.category_scores[category].evidence.append(evidence)
        
        # Update specific scores based on category
        if category == ReputationCategory.SECURITY:
            proj_rep.security_score = new_score
        elif category == ReputationCategory.PERFORMANCE:
            proj_rep.performance_score = new_score
        elif category == ReputationCategory.COMMUNITY:
            proj_rep.community_score = new_score
        elif category == ReputationCategory.TRANSPARENCY:
            proj_rep.transparency_score = new_score
        
        # Update total score and level
        proj_rep.update_level()
        proj_rep.last_updated = datetime.now()
        
        # Add to history
        proj_rep.reputation_history.append({
            'timestamp': datetime.now().isoformat(),
            'action': 'REPUTATION_UPDATED',
            'category': category.value,
            'old_score': old_score if 'old_score' in locals() else 0,
            'new_score': new_score,
            'evidence': evidence
        })
        
        self._save_reputation_data()
    
    def get_developer_reputation(self, developer_id: str) -> Optional[DeveloperReputation]:
        """Get developer reputation"""
        return self.developer_reputations.get(developer_id)
    
    def get_project_reputation(self, project_id: str) -> Optional[ProjectReputation]:
        """Get project reputation"""
        return self.project_reputations.get(project_id)
    
    def get_top_developers(self, limit: int = 10) -> List[DeveloperReputation]:
        """Get top developers by reputation"""
        developers = list(self.developer_reputations.values())
        developers.sort(key=lambda x: x.total_score, reverse=True)
        return developers[:limit]
    
    def get_top_projects(self, limit: int = 10) -> List[ProjectReputation]:
        """Get top projects by reputation"""
        projects = list(self.project_reputations.values())
        projects.sort(key=lambda x: x.total_score, reverse=True)
        return projects[:limit]
    
    def get_reputation_leaderboard(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get comprehensive reputation leaderboard"""
        top_developers = self.get_top_developers(10)
        top_projects = self.get_top_projects(10)
        
        return {
            'top_developers': [
                {
                    'rank': i + 1,
                    'developer_id': dev.developer_id,
                    'name': dev.name,
                    'github_username': dev.github_username,
                    'total_score': dev.total_score,
                    'level': dev.level.title,
                    'level_emoji': dev.level.emoji,
                    'badges': list(dev.badges)
                }
                for i, dev in enumerate(top_developers)
            ],
            'top_projects': [
                {
                    'rank': i + 1,
                    'project_id': proj.project_id,
                    'project_name': proj.project_name,
                    'developer_id': proj.developer_id,
                    'total_score': proj.total_score,
                    'level': proj.level.title,
                    'level_emoji': proj.level.emoji,
                    'security_score': proj.security_score,
                    'performance_score': proj.performance_score,
                    'community_score': proj.community_score,
                    'badges': list(proj.badges)
                }
                for i, proj in enumerate(top_projects)
            ]
        }
    
    def calculate_reputation_insights(self, developer_id: str = None, project_id: str = None) -> Dict[str, Any]:
        """Calculate reputation insights and recommendations"""
        insights = {}
        
        if developer_id and developer_id in self.developer_reputations:
            dev_rep = self.developer_reputations[developer_id]
            
            # Find strongest and weakest categories
            strongest_cat = max(dev_rep.category_scores.items(), key=lambda x: x[1].score)
            weakest_cat = min(dev_rep.category_scores.items(), key=lambda x: x[1].score)
            
            insights['developer'] = {
                'current_level': dev_rep.level.title,
                'strongest_category': {
                    'category': strongest_cat[0].value,
                    'score': strongest_cat[1].score
                },
                'weakest_category': {
                    'category': weakest_cat[0].value,
                    'score': weakest_cat[1].score
                },
                'recommendations': self._generate_developer_recommendations(dev_rep)
            }
        
        if project_id and project_id in self.project_reputations:
            proj_rep = self.project_reputations[project_id]
            
            insights['project'] = {
                'current_level': proj_rep.level.title,
                'security_score': proj_rep.security_score,
                'performance_score': proj_rep.performance_score,
                'community_score': proj_rep.community_score,
                'transparency_score': proj_rep.transparency_score,
                'recommendations': self._generate_project_recommendations(proj_rep)
            }
        
        return insights
    
    def _generate_developer_recommendations(self, dev_rep: DeveloperReputation) -> List[str]:
        """Generate personalized recommendations for developer"""
        recommendations = []
        
        for category, score in dev_rep.category_scores.items():
            if score.score < 30:
                if category == ReputationCategory.SECURITY:
                    recommendations.append("🔒 Pelajari best practices keamanan kriptografi")
                elif category == ReputationCategory.PERFORMANCE:
                    recommendations.append("⚡ Optimalkan algoritma kripto untuk performa lebih baik")
                elif category == ReputationCategory.COMPLIANCE:
                    recommendations.append("📋 Pastikan proyek memenuhi standar regulasi")
                elif category == ReputationCategory.TRANSPARENCY:
                    recommendations.append("🔍 Tingkatkan dokumentasi dan transparansi kode")
                elif category == ReputationCategory.COMMUNITY:
                    recommendations.append("🤝 Aktif berkontribusi dalam komunitas kripto Indonesia")
                elif category == ReputationCategory.INNOVATION:
                    recommendations.append("💡 Eksplorasi algoritma kripto inovatif berbasis budaya lokal")
            elif score.score >= 80:
                if category == ReputationCategory.SECURITY:
                    recommendations.append("🌟 Bagikan pengetahuan keamanan Anda dengan komunitas")
                elif category == ReputationCategory.PERFORMANCE:
                    recommendations.append("🏆 Pertahankan performa luar biasa algoritma Anda")
                elif category == ReputationCategory.COMPLIANCE:
                    recommendations.append("✅ Jadikan proyek Anda sebagai standar regulasi")
                elif category == ReputationCategory.TRANSPARENCY:
                    recommendations.append("📖 Bagikan best practices dokumentasi Anda")
                elif category == ReputationCategory.COMMUNITY:
                    recommendations.append("👑 Terus tingkatkan engagement komunitas")
                elif category == ReputationCategory.INNOVATION:
                    recommendations.append("🚀 Eksplorasi inovasi baru di bidang kriptografi")
            else:
                if category == ReputationCategory.SECURITY:
                    recommendations.append("🔐 Tingkatkan keamanan dengan audit berkala")
                elif category == ReputationCategory.PERFORMANCE:
                    recommendations.append("⚙️ Optimalkan performa secara bertahap")
                elif category == ReputationCategory.COMPLIANCE:
                    recommendations.append("📊 Validasi kepatuhan secara berkala")
                elif category == ReputationCategory.TRANSPARENCY:
                    recommendations.append("📝 Perbaiki dokumentasi secara bertahap")
                elif category == ReputationCategory.COMMUNITY:
                    recommendations.append("🌐 Libatkan diri lebih dalam dalam komunitas")
                elif category == ReputationCategory.INNOVATION:
                    recommendations.append("💭 Eksplorasi ide-ide inovatif baru")
        
        return recommendations
    
    def _generate_project_recommendations(self, proj_rep: ProjectReputation) -> List[str]:
        """Generate personalized recommendations for project"""
        recommendations = []
        
        if proj_rep.security_score < 30:
            recommendations.append("🔒 Lakukan security audit menyeluruh")
        
        if proj_rep.performance_score < 30:
            recommendations.append("⚡ Optimalkan performa algoritma")
        
        if proj_rep.community_score < 30:
            recommendations.append("🤝 Tingkatkan engagement dengan komunitas")
        
        if proj_rep.transparency_score < 30:
            recommendations.append("🔍 Perbaiki dokumentasi dan transparansi")
        
        if proj_rep.contributor_count < 5:
            recommendations.append("👥 Dorong kontribusi dari komunitas")
        
        if proj_rep.github_stars < 10:
            recommendations.append("⭐ Promosikan proyek untuk mendapatkan lebih banyak perhatian")
        
        return recommendations


# Example usage and testing
if __name__ == "__main__":
    async def demo():
        engine = ReputationEngine()
        
        # Register developers
        dev1 = await engine.register_developer(
            "dev_001", "Budi Santoso", "budi@example.com", "budisantoso"
        )
        
        dev2 = await engine.register_developer(
            "dev_002", "Siti Nurhaliza", "siti@example.com", "sitinur"
        )
        
        # Register projects
        proj1 = await engine.register_project(
            "proj_001", "FVChain", "Blockchain berbasis algoritma vortex fractal", "dev_001"
        )
        
        proj2 = await engine.register_project(
            "proj_002", "OmegaCrypto", "Algoritma enkripsi kuantum lokal", "dev_002"
        )
        
        # Update reputations with sample data
        await engine.update_developer_reputation(
            "dev_001", ReputationCategory.SECURITY, 85.0,
            {"type": "verification", "description": "Security audit passed", "score": 85.0}
        )
        
        await engine.update_project_reputation(
            "proj_001", ReputationCategory.SECURITY, 90.0,
            {"type": "audit", "description": "Comprehensive security audit", "score": 90.0}
        )
        
        # Get reputation leaderboard
        leaderboard = engine.get_reputation_leaderboard()
        print("🏆 Reputation Leaderboard:")
        print(json.dumps(leaderboard, indent=2))
        
        # Get reputation insights
        insights = engine.calculate_reputation_insights("dev_001", "proj_001")
        print("\n💡 Reputation Insights:")
        print(json.dumps(insights, indent=2))
        
        # Get individual reputations
        dev_rep = engine.get_developer_reputation("dev_001")
        proj_rep = engine.get_project_reputation("proj_001")
        
        if dev_rep:
            print(f"\n👤 Developer {dev_rep.name}:")
            print(f"  Level: {dev_rep.level.title} {dev_rep.level.emoji}")
            print(f"  Total Score: {dev_rep.total_score:.1f}")
        
        if proj_rep:
            print(f"\n📋 Project {proj_rep.project_name}:")
            print(f"  Level: {proj_rep.level.title} {proj_rep.level.emoji}")
            print(f"  Total Score: {proj_rep.total_score:.1f}")
            print(f"  Security Score: {proj_rep.security_score:.1f}")
    
    asyncio.run(demo())