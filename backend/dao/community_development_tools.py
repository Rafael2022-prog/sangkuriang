"""
SANGKURIANG Community-Driven Development Tools
Alat pengembangan berbasis komunitas untuk ekosistem terdesentralisasi
"""

import asyncio
import json
import hashlib
import time
import os
import sys
import subprocess
import tempfile
import shutil
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import redis.asyncio as redis
from web3 import Web3
from eth_account import Account
import aiofiles
import git
import requests
from pathlib import Path
import base64
import pickle
import threading
import uuid
import re
import random
import string
from urllib.parse import urlparse


class CommunityRole(Enum):
    """Peran dalam komunitas"""
    DEVELOPER = "developer"
    DESIGNER = "designer"
    TESTER = "tester"
    DOCUMENTER = "documenter"
    TRANSLATOR = "translator"
    COMMUNITY_MANAGER = "community_manager"
    MODERATOR = "moderator"
    CONTRIBUTOR = "contributor"
    MENTOR = "mentor"
    MAINTAINER = "maintainer"
    REVIEWER = "reviewer"
    AMBASSADOR = "ambassador"
    ADVOCATE = "advocate"
    RESEARCHER = "researcher"
    ANALYST = "analyst"


class ProjectType(Enum):
    """Jenis proyek komunitas"""
    SMART_CONTRACT = "smart_contract"
    DAPP = "dapp"
    TOOL = "tool"
    LIBRARY = "library"
    FRAMEWORK = "framework"
    DOCUMENTATION = "documentation"
    TUTORIAL = "tutorial"
    VIDEO = "video"
    ARTICLE = "article"
    TRANSLATION = "translation"
    DESIGN = "design"
    COMMUNITY = "community"
    RESEARCH = "research"
    SECURITY_AUDIT = "security_audit"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"


class ProjectStatus(Enum):
    """Status proyek komunitas"""
    IDEA = "idea"
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    TESTING = "testing"
    REVIEW = "review"
    COMPLETED = "completed"
    MAINTAINED = "maintained"
    ARCHIVED = "archived"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"
    NEEDS_HELP = "needs_help"
    SEEKING_CONTRIBUTORS = "seeking_contributors"


class TaskType(Enum):
    """Jenis tugas komunitas"""
    CODING = "coding"
    DESIGN = "design"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    REVIEW = "review"
    TRANSLATION = "translation"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    COMMUNITY_BUILDING = "community_building"
    MARKETING = "marketing"
    EVENT_ORGANIZATION = "event_organization"
    MENTORING = "mentoring"
    BUG_FIX = "bug_fix"
    FEATURE_IMPLEMENTATION = "feature_implementation"
    SECURITY_AUDIT = "security_audit"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"


class TaskStatus(Enum):
    """Status tugas komunitas"""
    OPEN = "open"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    UNDER_REVIEW = "under_review"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"
    NEEDS_CLARIFICATION = "needs_clarification"
    PRIORITY_CHANGED = "priority_changed"


class SkillLevel(Enum):
    """Tingkat keahlian"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    MASTER = "master"


class ContributionLevel(Enum):
    """Tingkat kontribusi"""
    FIRST_TIME = "first_time"
    OCCASIONAL = "occasional"
    REGULAR = "regular"
    FREQUENT = "frequent"
    CORE_CONTRIBUTOR = "core_contributor"
    MAINTAINER = "maintainer"


class RecognitionType(Enum):
    """Jenis pengakuan komunitas"""
    CONTRIBUTION_MILESTONE = "contribution_milestone"
    EXCELLENT_WORK = "excellent_work"
    COMMUNITY_HELPER = "community_helper"
    MENTORSHIP = "mentorship"
    INNOVATION = "innovation"
    LEADERSHIP = "leadership"
    CONSISTENCY = "consistency"
    SPECIAL_ACHIEVEMENT = "special_achievement"


@dataclass
class CommunityMember:
    """Anggota komunitas"""
    member_address: str
    member_name: str
    member_email: str
    member_bio: str
    community_roles: List[CommunityRole]
    skills: Dict[str, SkillLevel]  # skill_name -> skill_level
    programming_languages: List[str]
    spoken_languages: List[str]
    location: str
    timezone: str
    availability_hours: int  # hours per week
    contribution_level: ContributionLevel
    join_date: datetime
    last_activity_date: datetime
    reputation_score: float
    contribution_points: int
    badges: List[str]
    projects_participated: List[str]
    tasks_completed: int
    tasks_in_progress: int
    mentoring_students: int
    being_mentored_by: Optional[str] = None
    social_links: Dict[str, str] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)
    custom_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CommunityProject:
    """Proyek komunitas"""
    project_id: str
    project_name: str
    project_description: str
    project_type: ProjectType
    project_status: ProjectStatus
    project_category: str
    project_tags: List[str]
    project_goals: List[str]
    project_requirements: List[str]
    project_technologies: List[str]
    project_difficulty: str  # easy, medium, hard, expert
    estimated_duration_days: int
    current_progress_percentage: float
    project_lead_address: str
    project_lead_name: str
    team_members: List[str]  # member addresses
    required_roles: List[CommunityRole]
    required_skills: Dict[str, SkillLevel]
    project_budget: float
    project_funding_status: str  # funded, partially_funded, seeking_funding, unfunded
    project_rewards: Dict[str, float]  # role -> reward_amount
    project_milestones: List[Dict[str, Any]]
    project_deliverables: List[str]
    project_documentation: str
    project_repository: Optional[str] = None
    project_website: Optional[str] = None
    project_demo: Optional[str] = None
    project_license: str = "MIT"
    project_visibility: str = "public"  # public, private, invite_only
    created_date: datetime = field(default_factory=datetime.now)
    updated_date: datetime = field(default_factory=datetime.now)
    start_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    deadline_date: Optional[datetime] = None
    custom_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CommunityTask:
    """Tugas komunitas"""
    task_id: str
    project_id: str
    task_name: str
    task_description: str
    task_type: TaskType
    task_status: TaskStatus
    task_priority: int  # 1-10
    task_difficulty: str  # easy, medium, hard, expert
    estimated_hours: int
    actual_hours: Optional[int] = None
    assigned_to: Optional[str] = None  # member address
    assigned_by: Optional[str] = None  # member address
    required_skills: List[str]
    required_tools: List[str]
    task_deliverables: List[str]
    task_acceptance_criteria: List[str]
    task_rewards: Dict[str, float]  # type -> reward_amount
    task_dependencies: List[str]  # other task IDs
    task_subtasks: List[str]  # subtask IDs
    task_comments: List[Dict[str, Any]]
    task_progress_percentage: float = 0.0
    created_date: datetime = field(default_factory=datetime.now)
    assigned_date: Optional[datetime] = None
    started_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    deadline_date: Optional[datetime] = None
    custom_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CommunityEvent:
    """Event komunitas"""
    event_id: str
    event_name: str
    event_description: str
    event_type: str  # workshop, hackathon, meetup, conference, webinar, training
    event_status: str  # planned, active, completed, cancelled
    event_format: str  # online, offline, hybrid
    event_location: Optional[str]
    event_url: Optional[str]
    event_start_datetime: datetime
    event_end_datetime: datetime
    event_timezone: str
    event_capacity: int
    event_registration_required: bool
    event_registration_deadline: Optional[datetime]
    event_organizer_address: str
    event_organizer_name: str
    event_co_organizers: List[str]
    event_speakers: List[Dict[str, str]]
    event_participants: List[str]  # member addresses
    event_waitlist: List[str]
    event_topics: List[str]
    event_materials: List[str]
    event_recordings: List[str]
    event_budget: float
    event_sponsors: List[str]
    event_rewards: Dict[str, float]
    event_badges: List[str]
    event_survey_required: bool = True
    created_date: datetime = field(default_factory=datetime.now)
    updated_date: datetime = field(default_factory=datetime.now)
    custom_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MentorshipProgram:
    """Program mentoring komunitas"""
    mentorship_id: str
    mentor_address: str
    mentor_name: str
    mentee_address: str
    mentee_name: str
    mentorship_topic: str
    mentorship_goals: List[str]
    mentorship_duration_weeks: int
    mentorship_status: str  # active, completed, cancelled, on_hold
    mentorship_type: str  # one_on_one, group, project_based, skill_based
    meeting_frequency: str  # weekly, biweekly, monthly
    meeting_duration_minutes: int
    mentorship_materials: List[str]
    mentorship_assignments: List[Dict[str, Any]]
    progress_tracking: List[Dict[str, Any]]
    mentorship_rewards: Dict[str, float]
    start_date: datetime
    end_date: datetime
    created_date: datetime = field(default_factory=datetime.now)
    updated_date: datetime = field(default_factory=datetime.now)
    custom_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecognitionRecord:
    """Record pengakuan komunitas"""
    recognition_id: str
    recognition_type: RecognitionType
    recipient_address: str
    recipient_name: str
    giver_address: str
    giver_name: str
    recognition_title: str
    recognition_description: str
    recognition_reason: str
    recognition_impact: str
    recognition_rewards: Dict[str, float]
    recognition_badges: List[str]
    community_vote_score: float
    community_votes: int
    is_community_approved: bool
    created_date: datetime = field(default_factory=datetime.now)
    custom_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CommunityMetrics:
    """Metrik komunitas"""
    total_members: int = 0
    active_members: int = 0
    new_members_this_month: int = 0
    total_projects: int = 0
    active_projects: int = 0
    completed_projects: int = 0
    total_tasks: int = 0
    open_tasks: int = 0
    completed_tasks: int = 0
    total_events: int = 0
    upcoming_events: int = 0
    total_mentorships: int = 0
    active_mentorships: int = 0
    total_recognitions: int = 0
    this_month_recognitions: int = 0
    average_member_satisfaction: float = 0.0
    average_project_completion_time: float = 0.0
    average_task_completion_time: float = 0.0
    community_growth_rate: float = 0.0
    member_retention_rate: float = 0.0
    project_success_rate: float = 0.0
    task_completion_rate: float = 0.0
    mentorship_success_rate: float = 0.0
    total_community_rewards: float = 0.0
    total_community_points: int = 0
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class CommunityConfiguration:
    """Konfigurasi komunitas"""
    enable_mentorship_programs: bool = True
    enable_recognition_system: bool = True
    enable_project_governance: bool = True
    enable_task_assignment: bool = True
    enable_event_organization: bool = True
    enable_community_voting: bool = True
    enable_skill_matching: bool = True
    enable_reputation_system: bool = True
    enable_community_rewards: bool = True
    enable_project_funding: bool = True
    enable_community_surveys: bool = True
    enable_performance_tracking: bool = True
    enable_communication_tools: bool = True
    enable_collaboration_tools: bool = True
    enable_project_showcase: bool = True
    enable_member_directory: bool = True
    enable_achievement_system: bool = True
    enable_community_challenges: bool = True
    enable_gamification: bool = True
    enable_decentralized_governance: bool = True
    min_reputation_for_mentoring: float = 100.0
    min_reputation_for_project_lead: float = 200.0
    min_reputation_for_reviewing: float = 50.0
    max_tasks_per_member: int = 5
    max_projects_per_member: int = 3
    project_completion_reward_rate: float = 0.1  # tokens per hour
    task_completion_reward_rate: float = 0.05  # tokens per hour
    mentorship_reward_rate: float = 0.02  # tokens per hour
    recognition_reward_rate: float = 0.01  # tokens per recognition
    community_vote_threshold: float = 0.6  # 60% approval required
    custom_settings: Dict[str, Any] = field(default_factory=dict)


class CommunityDevelopmentTools:
    """SANGKURIANG Community-Driven Development Tools"""
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        web3_provider: str = "https://mainnet.infura.io/v3/YOUR_PROJECT_ID",
        enable_monitoring: bool = True
    ):
        # Redis client
        self.redis_client = redis.from_url(redis_url)
        
        # Web3 integration
        self.web3 = Web3(Web3.HTTPProvider(web3_provider))
        
        # System state
        self.community_members: Dict[str, CommunityMember] = {}
        self.community_projects: Dict[str, CommunityProject] = {}
        self.community_tasks: Dict[str, CommunityTask] = {}
        self.community_events: Dict[str, CommunityEvent] = {}
        self.mentorship_programs: Dict[str, MentorshipProgram] = {}
        self.recognition_records: Dict[str, RecognitionRecord] = {}
        self.pending_operations: List[str] = []
        
        # Configuration
        self.config = CommunityConfiguration()
        self.enable_monitoring = enable_monitoring
        
        # Metrics
        self.metrics = CommunityMetrics()
        
        # Monitoring
        self.monitoring_active = True
        self.monitoring_thread = None
        
        # Gamification
        self.achievement_system = self._initialize_achievement_system()
        self.badge_system = self._initialize_badge_system()
        
        # Initialize system
        asyncio.create_task(self._initialize_community_tools())
    
    async def _initialize_community_tools(self) -> None:
        """Inisialisasi community development tools"""
        try:
            # Load existing data from Redis
            await self._load_existing_data()
            
            # Start monitoring
            if self.enable_monitoring:
                self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
                self.monitoring_thread.start()
            
            print("✅ Community development tools initialized")
            
        except Exception as e:
            print(f"❌ Failed to initialize community development tools: {e}")
    
    def _initialize_achievement_system(self) -> Dict[str, Dict[str, Any]]:
        """Inisialisasi sistem achievement"""
        return {
            "first_contribution": {
                "name": "First Steps",
                "description": "Make your first contribution to the community",
                "requirement": 1,
                "type": "contribution",
                "reward_points": 10,
                "reward_tokens": 0.1
            },
            "contributor_10": {
                "name": "Active Contributor",
                "description": "Complete 10 contributions",
                "requirement": 10,
                "type": "contribution",
                "reward_points": 50,
                "reward_tokens": 0.5
            },
            "contributor_50": {
                "name": "Core Contributor",
                "description": "Complete 50 contributions",
                "requirement": 50,
                "type": "contribution",
                "reward_points": 200,
                "reward_tokens": 2.0
            },
            "mentor_first": {
                "name": "Mentor",
                "description": "Complete your first mentorship session",
                "requirement": 1,
                "type": "mentorship",
                "reward_points": 25,
                "reward_tokens": 0.25
            },
            "project_leader": {
                "name": "Project Leader",
                "description": "Successfully lead a community project",
                "requirement": 1,
                "type": "project",
                "reward_points": 100,
                "reward_tokens": 1.0
            },
            "community_helper": {
                "name": "Community Helper",
                "description": "Help 10 community members",
                "requirement": 10,
                "type": "help",
                "reward_points": 75,
                "reward_tokens": 0.75
            },
            "consistent_contributor": {
                "name": "Consistent Contributor",
                "description": "Make contributions for 30 consecutive days",
                "requirement": 30,
                "type": "consistency",
                "reward_points": 150,
                "reward_tokens": 1.5
            },
            "innovation_award": {
                "name": "Innovation Award",
                "description": "Propose an innovative solution that gets implemented",
                "requirement": 1,
                "type": "innovation",
                "reward_points": 300,
                "reward_tokens": 3.0
            }
        }
    
    def _initialize_badge_system(self) -> Dict[str, Dict[str, Any]]:
        """Inisialisasi sistem badge"""
        return {
            "newbie": {
                "name": "Newbie",
                "description": "Welcome to the community!",
                "icon": "🌱",
                "criteria": "Join the community",
                "category": "welcome"
            },
            "coder": {
                "name": "Coder",
                "description": "Contributed code to community projects",
                "icon": "💻",
                "criteria": "Complete 5 coding tasks",
                "category": "contribution"
            },
            "reviewer": {
                "name": "Code Reviewer",
                "description": "Reviewed community code contributions",
                "icon": "👀",
                "criteria": "Complete 10 code reviews",
                "category": "quality"
            },
            "mentor": {
                "name": "Mentor",
                "description": "Mentored community members",
                "icon": "🧑‍🏫",
                "criteria": "Complete 5 mentorship sessions",
                "category": "education"
            },
            "leader": {
                "name": "Community Leader",
                "description": "Led community initiatives",
                "icon": "👑",
                "criteria": "Lead 3 successful projects",
                "category": "leadership"
            },
            "innovator": {
                "name": "Innovator",
                "description": "Proposed innovative solutions",
                "icon": "💡",
                "criteria": "Propose 5 innovative ideas",
                "category": "innovation"
            },
            "helper": {
                "name": "Community Helper",
                "description": "Helped other community members",
                "icon": "🤝",
                "criteria": "Help 20 community members",
                "category": "community"
            },
            "consistent": {
                "name": "Consistent Contributor",
                "description": "Consistently contributed to the community",
                "icon": "📅",
                "criteria": "Contribute for 60 consecutive days",
                "category": "consistency"
            }
        }
    
    async def register_community_member(
        self,
        member_address: str,
        member_name: str,
        member_email: str,
        member_bio: str,
        community_roles: List[CommunityRole],
        skills: Dict[str, SkillLevel],
        programming_languages: List[str],
        spoken_languages: List[str],
        location: str,
        timezone: str,
        availability_hours: int,
        social_links: Optional[Dict[str, str]] = None,
        preferences: Optional[Dict[str, Any]] = None,
        custom_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Register new community member"""
        try:
            # Validate member data
            if not self._validate_member_data(member_address, member_name, member_email):
                return {
                    "success": False,
                    "error": "Invalid member data"
                }
            
            # Check if member already exists
            if member_address in self.community_members:
                return {
                    "success": False,
                    "error": "Member already registered"
                }
            
            # Create community member
            community_member = CommunityMember(
                member_address=member_address,
                member_name=member_name,
                member_email=member_email,
                member_bio=member_bio,
                community_roles=community_roles,
                skills=skills,
                programming_languages=programming_languages,
                spoken_languages=spoken_languages,
                location=location,
                timezone=timezone,
                availability_hours=availability_hours,
                contribution_level=ContributionLevel.FIRST_TIME,
                join_date=datetime.now(),
                last_activity_date=datetime.now(),
                reputation_score=0.0,
                contribution_points=0,
                badges=["newbie"],
                projects_participated=[],
                tasks_completed=0,
                tasks_in_progress=0,
                mentoring_students=0,
                social_links=social_links or {},
                preferences=preferences or {},
                custom_metadata=custom_metadata or {}
            )
            
            # Add to registry
            self.community_members[member_address] = community_member
            
            # Update metrics
            self.metrics.total_members += 1
            self.metrics.new_members_this_month += 1
            
            # Check for achievements
            await self._check_member_achievements(member_address)
            
            print(f"✅ Community member registered: {member_name}")
            return {
                "success": True,
                "member_address": member_address,
                "member_name": member_name,
                "reputation_score": 0.0,
                "badges": ["newbie"],
                "contribution_points": 0
            }
            
        except Exception as e:
            print(f"❌ Failed to register community member: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_community_project(
        self,
        project_name: str,
        project_description: str,
        project_type: ProjectType,
        project_category: str,
        project_tags: List[str],
        project_goals: List[str],
        project_requirements: List[str],
        project_technologies: List[str],
        project_difficulty: str,
        estimated_duration_days: int,
        project_lead_address: str,
        required_roles: List[CommunityRole],
        required_skills: Dict[str, SkillLevel],
        project_budget: float,
        project_license: str = "MIT",
        project_visibility: str = "public",
        project_repository: Optional[str] = None,
        project_website: Optional[str] = None,
        deadline_date: Optional[datetime] = None,
        custom_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create new community project"""
        try:
            # Validate project lead
            if project_lead_address not in self.community_members:
                return {
                    "success": False,
                    "error": "Project lead not found"
                }
            
            # Validate project lead reputation
            lead_member = self.community_members[project_lead_address]
            if lead_member.reputation_score < self.config.min_reputation_for_project_lead:
                return {
                    "success": False,
                    "error": f"Insufficient reputation. Required: {self.config.min_reputation_for_project_lead}, Current: {lead_member.reputation_score}"
                }
            
            # Generate project ID
            project_id = str(uuid.uuid4())
            
            # Create community project
            community_project = CommunityProject(
                project_id=project_id,
                project_name=project_name,
                project_description=project_description,
                project_type=project_type,
                project_status=ProjectStatus.PLANNING,
                project_category=project_category,
                project_tags=project_tags,
                project_goals=project_goals,
                project_requirements=project_requirements,
                project_technologies=project_technologies,
                project_difficulty=project_difficulty,
                estimated_duration_days=estimated_duration_days,
                current_progress_percentage=0.0,
                project_lead_address=project_lead_address,
                project_lead_name=lead_member.member_name,
                team_members=[project_lead_address],
                required_roles=required_roles,
                required_skills=required_skills,
                project_budget=project_budget,
                project_funding_status="seeking_funding",
                project_rewards={},
                project_milestones=[],
                project_deliverables=[],
                project_documentation="",
                project_license=project_license,
                project_visibility=project_visibility,
                project_repository=project_repository,
                project_website=project_website,
                deadline_date=deadline_date,
                custom_metadata=custom_metadata or {}
            )
            
            # Add to registry
            self.community_projects[project_id] = community_project
            
            # Update project lead
            lead_member.projects_participated.append(project_id)
            
            # Update metrics
            self.metrics.total_projects += 1
            if community_project.project_status == ProjectStatus.PLANNING:
                self.metrics.active_projects += 1
            
            print(f"✅ Community project created: {project_name}")
            return {
                "success": True,
                "project_id": project_id,
                "project_name": project_name,
                "project_lead": lead_member.member_name,
                "project_status": ProjectStatus.PLANNING.value,
                "team_size": 1
            }
            
        except Exception as e:
            print(f"❌ Failed to create community project: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_community_task(
        self,
        project_id: str,
        task_name: str,
        task_description: str,
        task_type: TaskType,
        task_priority: int,
        task_difficulty: str,
        estimated_hours: int,
        required_skills: List[str],
        required_tools: List[str],
        task_deliverables: List[str],
        task_acceptance_criteria: List[str],
        task_rewards: Dict[str, float],
        deadline_date: Optional[datetime] = None,
        task_dependencies: Optional[List[str]] = None,
        custom_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create new community task"""
        try:
            # Validate project exists
            if project_id not in self.community_projects:
                return {
                    "success": False,
                    "error": "Project not found"
                }
            
            # Generate task ID
            task_id = str(uuid.uuid4())
            
            # Create community task
            community_task = CommunityTask(
                task_id=task_id,
                project_id=project_id,
                task_name=task_name,
                task_description=task_description,
                task_type=task_type,
                task_status=TaskStatus.OPEN,
                task_priority=task_priority,
                task_difficulty=task_difficulty,
                estimated_hours=estimated_hours,
                required_skills=required_skills,
                required_tools=required_tools,
                task_deliverables=task_deliverables,
                task_acceptance_criteria=task_acceptance_criteria,
                task_rewards=task_rewards,
                task_dependencies=task_dependencies or [],
                task_subtasks=[],
                task_comments=[],
                deadline_date=deadline_date,
                custom_metadata=custom_metadata or {}
            )
            
            # Add to registry
            self.community_tasks[task_id] = community_task
            
            # Update project
            project = self.community_projects[project_id]
            project.project_milestones.append({
                "task_id": task_id,
                "task_name": task_name,
                "status": "pending",
                "deadline": deadline_date.isoformat() if deadline_date else None
            })
            
            # Update metrics
            self.metrics.total_tasks += 1
            self.metrics.open_tasks += 1
            
            print(f"✅ Community task created: {task_name}")
            return {
                "success": True,
                "task_id": task_id,
                "task_name": task_name,
                "project_id": project_id,
                "task_status": TaskStatus.OPEN.value,
                "estimated_hours": estimated_hours
            }
            
        except Exception as e:
            print(f"❌ Failed to create community task: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def assign_task_to_member(
        self,
        task_id: str,
        member_address: str,
        assigned_by: str
    ) -> Dict[str, Any]:
        """Assign task to community member"""
        try:
            # Validate task exists
            if task_id not in self.community_tasks:
                return {
                    "success": False,
                    "error": "Task not found"
                }
            
            # Validate member exists
            if member_address not in self.community_members:
                return {
                    "success": False,
                    "error": "Member not found"
                }
            
            # Validate assigner exists
            if assigned_by not in self.community_members:
                return {
                    "success": False,
                    "error": "Assigner not found"
                }
            
            # Get task and member
            task = self.community_tasks[task_id]
            member = self.community_members[member_address]
            
            # Check if task is assignable
            if task.task_status != TaskStatus.OPEN:
                return {
                    "success": False,
                    "error": "Task is not available for assignment"
                }
            
            # Check member capacity
            if member.tasks_in_progress >= self.config.max_tasks_per_member:
                return {
                    "success": False,
                    "error": f"Member has reached maximum task limit: {self.config.max_tasks_per_member}"
                }
            
            # Check skill matching
            if not self._check_skill_compatibility(member, task):
                return {
                    "success": False,
                    "error": "Member does not have required skills for this task"
                }
            
            # Assign task
            task.assigned_to = member_address
            task.assigned_by = assigned_by
            task.task_status = TaskStatus.ASSIGNED
            task.assigned_date = datetime.now()
            
            # Update member
            member.tasks_in_progress += 1
            member.last_activity_date = datetime.now()
            
            # Update metrics
            self.metrics.open_tasks -= 1
            
            print(f"✅ Task assigned: {task.task_name} to {member.member_name}")
            return {
                "success": True,
                "task_id": task_id,
                "task_name": task_name,
                "assigned_to": member.member_name,
                "assigned_by": self.community_members[assigned_by].member_name,
                "assigned_date": task.assigned_date.isoformat()
            }
            
        except Exception as e:
            print(f"❌ Failed to assign task: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_mentorship_program(
        self,
        mentor_address: str,
        mentee_address: str,
        mentorship_topic: str,
        mentorship_goals: List[str],
        mentorship_duration_weeks: int,
        mentorship_type: str,
        meeting_frequency: str,
        meeting_duration_minutes: int,
        start_date: datetime,
        end_date: datetime,
        mentorship_materials: Optional[List[str]] = None,
        custom_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create mentorship program"""
        try:
            # Validate mentor exists
            if mentor_address not in self.community_members:
                return {
                    "success": False,
                    "error": "Mentor not found"
                }
            
            # Validate mentee exists
            if mentee_address not in self.community_members:
                return {
                    "success": False,
                    "error": "Mentee not found"
                }
            
            # Validate mentor reputation
            mentor_member = self.community_members[mentor_address]
            if mentor_member.reputation_score < self.config.min_reputation_for_mentoring:
                return {
                    "success": False,
                    "error": f"Insufficient reputation for mentoring. Required: {self.config.min_reputation_for_mentoring}, Current: {mentor_member.reputation_score}"
                }
            
            # Check mentor capacity
            if mentor_member.mentoring_students >= 5:  # Max 5 mentees per mentor
                return {
                    "success": False,
                    "error": "Mentor has reached maximum mentee capacity"
                }
            
            # Generate mentorship ID
            mentorship_id = str(uuid.uuid4())
            
            # Calculate rewards
            mentorship_rewards = {
                "mentor_tokens": mentorship_duration_weeks * 0.5,
                "mentor_points": mentorship_duration_weeks * 10,
                "mentee_tokens": mentorship_duration_weeks * 0.2,
                "mentee_points": mentorship_duration_weeks * 5
            }
            
            # Create mentorship program
            mentorship_program = MentorshipProgram(
                mentorship_id=mentorship_id,
                mentor_address=mentor_address,
                mentor_name=mentor_member.member_name,
                mentee_address=mentee_address,
                mentee_name=self.community_members[mentee_address].member_name,
                mentorship_topic=mentorship_topic,
                mentorship_goals=mentorship_goals,
                mentorship_duration_weeks=mentorship_duration_weeks,
                mentorship_status="active",
                mentorship_type=mentorship_type,
                meeting_frequency=meeting_frequency,
                meeting_duration_minutes=meeting_duration_minutes,
                mentorship_materials=mentorship_materials or [],
                mentorship_assignments=[],
                progress_tracking=[],
                mentorship_rewards=mentorship_rewards,
                start_date=start_date,
                end_date=end_date,
                custom_metadata=custom_metadata or {}
            )
            
            # Add to registry
            self.mentorship_programs[mentorship_id] = mentorship_program
            
            # Update members
            mentor_member.mentoring_students += 1
            self.community_members[mentee_address].being_mentored_by = mentor_address
            
            # Update metrics
            self.metrics.total_mentorships += 1
            self.metrics.active_mentorships += 1
            
            print(f"✅ Mentorship program created: {mentorship_topic}")
            return {
                "success": True,
                "mentorship_id": mentorship_id,
                "mentor_name": mentor_member.member_name,
                "mentee_name": self.community_members[mentee_address].member_name,
                "mentorship_topic": mentorship_topic,
                "mentorship_rewards": mentorship_rewards
            }
            
        except Exception as e:
            print(f"❌ Failed to create mentorship program: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def give_community_recognition(
        self,
        recognition_type: RecognitionType,
        recipient_address: str,
        giver_address: str,
        recognition_title: str,
        recognition_description: str,
        recognition_reason: str,
        recognition_impact: str,
        community_vote_required: bool = True,
        custom_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Give community recognition"""
        try:
            # Validate recipient exists
            if recipient_address not in self.community_members:
                return {
                    "success": False,
                    "error": "Recipient not found"
                }
            
            # Validate giver exists
            if giver_address not in self.community_members:
                return {
                    "success": False,
                    "error": "Giver not found"
                }
            
            # Generate recognition ID
            recognition_id = str(uuid.uuid4())
            
            # Calculate rewards
            recognition_rewards = {
                "recipient_tokens": self.config.recognition_reward_rate,
                "recipient_points": 10,
                "giver_tokens": self.config.recognition_reward_rate * 0.5,
                "giver_points": 5
            }
            
            # Create recognition record
            recognition_record = RecognitionRecord(
                recognition_id=recognition_id,
                recognition_type=recognition_type,
                recipient_address=recipient_address,
                recipient_name=self.community_members[recipient_address].member_name,
                giver_address=giver_address,
                giver_name=self.community_members[giver_address].member_name,
                recognition_title=recognition_title,
                recognition_description=recognition_description,
                recognition_reason=recognition_reason,
                recognition_impact=recognition_impact,
                recognition_rewards=recognition_rewards,
                recognition_badges=[],
                community_vote_score=0.0,
                community_votes=0,
                is_community_approved=not community_vote_required,
                custom_metadata=custom_metadata or {}
            )
            
            # Add to registry
            self.recognition_records[recognition_id] = recognition_record
            
            # Update member reputation
            recipient_member = self.community_members[recipient_address]
            recipient_member.reputation_score += 5.0
            recipient_member.contribution_points += 10
            
            # Update metrics
            self.metrics.total_recognitions += 1
            self.metrics.this_month_recognitions += 1
            
            print(f"✅ Community recognition given: {recognition_title}")
            return {
                "success": True,
                "recognition_id": recognition_id,
                "recipient_name": recipient_member.member_name,
                "giver_name": self.community_members[giver_address].member_name,
                "recognition_rewards": recognition_rewards,
                "community_vote_required": community_vote_required
            }
            
        except Exception as e:
            print(f"❌ Failed to give community recognition: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_community_event(
        self,
        event_name: str,
        event_description: str,
        event_type: str,
        event_format: str,
        event_start_datetime: datetime,
        event_end_datetime: datetime,
        event_timezone: str,
        event_capacity: int,
        event_organizer_address: str,
        event_topics: List[str],
        event_location: Optional[str] = None,
        event_url: Optional[str] = None,
        event_registration_required: bool = True,
        event_registration_deadline: Optional[datetime] = None,
        event_budget: float = 0.0,
        event_sponsors: Optional[List[str]] = None,
        custom_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create community event"""
        try:
            # Validate organizer exists
            if event_organizer_address not in self.community_members:
                return {
                    "success": False,
                    "error": "Event organizer not found"
                }
            
            # Generate event ID
            event_id = str(uuid.uuid4())
            
            # Calculate rewards
            event_rewards = {
                "organizer_tokens": 2.0,
                "organizer_points": 20,
                "participant_tokens": 0.5,
                "participant_points": 5
            }
            
            # Create community event
            community_event = CommunityEvent(
                event_id=event_id,
                event_name=event_name,
                event_description=event_description,
                event_type=event_type,
                event_status="planned",
                event_format=event_format,
                event_location=event_location,
                event_url=event_url,
                event_start_datetime=event_start_datetime,
                event_end_datetime=event_end_datetime,
                event_timezone=event_timezone,
                event_capacity=event_capacity,
                event_registration_required=event_registration_required,
                event_registration_deadline=event_registration_deadline,
                event_organizer_address=event_organizer_address,
                event_organizer_name=self.community_members[event_organizer_address].member_name,
                event_co_organizers=[],
                event_speakers=[],
                event_participants=[],
                event_waitlist=[],
                event_topics=event_topics,
                event_materials=[],
                event_recordings=[],
                event_budget=event_budget,
                event_sponsors=event_sponsors or [],
                event_rewards=event_rewards,
                event_badges=[],
                event_survey_required=True,
                custom_metadata=custom_metadata or {}
            )
            
            # Add to registry
            self.community_events[event_id] = community_event
            
            # Update metrics
            self.metrics.total_events += 1
            if community_event.event_status == "planned":
                self.metrics.upcoming_events += 1
            
            print(f"✅ Community event created: {event_name}")
            return {
                "success": True,
                "event_id": event_id,
                "event_name": event_name,
                "event_organizer": community_event.event_organizer_name,
                "event_rewards": event_rewards,
                "event_capacity": event_capacity
            }
            
        except Exception as e:
            print(f"❌ Failed to create community event: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_community_member_profile(self, member_address: str) -> Dict[str, Any]:
        """Get community member profile"""
        try:
            if member_address not in self.community_members:
                return {"success": False, "error": "Member not found"}
            
            member = self.community_members[member_address]
            
            return {
                "success": True,
                "member": {
                    "member_address": member.member_address,
                    "member_name": member.member_name,
                    "member_bio": member.member_bio,
                    "community_roles": [role.value for role in member.community_roles],
                    "skills": {skill: level.value for skill, level in member.skills.items()},
                    "programming_languages": member.programming_languages,
                    "spoken_languages": member.spoken_languages,
                    "location": member.location,
                    "timezone": member.timezone,
                    "availability_hours": member.availability_hours,
                    "contribution_level": member.contribution_level.value,
                    "reputation_score": member.reputation_score,
                    "contribution_points": member.contribution_points,
                    "badges": member.badges,
                    "projects_participated": len(member.projects_participated),
                    "tasks_completed": member.tasks_completed,
                    "tasks_in_progress": member.tasks_in_progress,
                    "mentoring_students": member.mentoring_students,
                    "being_mentored_by": member.being_mentored_by,
                    "join_date": member.join_date.isoformat(),
                    "last_activity_date": member.last_activity_date.isoformat()
                }
            }
            
        except Exception as e:
            print(f"❌ Failed to get member profile: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_community_project_info(self, project_id: str) -> Dict[str, Any]:
        """Get community project information"""
        try:
            if project_id not in self.community_projects:
                return {"success": False, "error": "Project not found"}
            
            project = self.community_projects[project_id]
            
            return {
                "success": True,
                "project": {
                    "project_id": project.project_id,
                    "project_name": project.project_name,
                    "project_description": project.project_description,
                    "project_type": project.project_type.value,
                    "project_status": project.project_status.value,
                    "project_category": project.project_category,
                    "project_tags": project.project_tags,
                    "project_goals": project.project_goals,
                    "project_requirements": project.project_requirements,
                    "project_technologies": project.project_technologies,
                    "project_difficulty": project.project_difficulty,
                    "estimated_duration_days": project.estimated_duration_days,
                    "current_progress_percentage": project.current_progress_percentage,
                    "project_lead": project.project_lead_name,
                    "team_size": len(project.team_members),
                    "team_members": project.team_members,
                    "required_roles": [role.value for role in project.required_roles],
                    "project_budget": project.project_budget,
                    "project_funding_status": project.project_funding_status,
                    "project_license": project.project_license,
                    "project_visibility": project.project_visibility,
                    "created_date": project.created_date.isoformat(),
                    "updated_date": project.updated_date.isoformat()
                }
            }
            
        except Exception as e:
            print(f"❌ Failed to get project info: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_community_metrics(self) -> Dict[str, Any]:
        """Get community metrics"""
        try:
            await self._update_community_metrics()
            
            return {
                "success": True,
                "metrics": {
                    "total_members": self.metrics.total_members,
                    "active_members": self.metrics.active_members,
                    "new_members_this_month": self.metrics.new_members_this_month,
                    "total_projects": self.metrics.total_projects,
                    "active_projects": self.metrics.active_projects,
                    "completed_projects": self.metrics.completed_projects,
                    "total_tasks": self.metrics.total_tasks,
                    "open_tasks": self.metrics.open_tasks,
                    "completed_tasks": self.metrics.completed_tasks,
                    "total_events": self.metrics.total_events,
                    "upcoming_events": self.metrics.upcoming_events,
                    "total_mentorships": self.metrics.total_mentorships,
                    "active_mentorships": self.metrics.active_mentorships,
                    "total_recognitions": self.metrics.total_recognitions,
                    "this_month_recognitions": self.metrics.this_month_recognitions,
                    "average_member_satisfaction": self.metrics.average_member_satisfaction,
                    "average_project_completion_time": self.metrics.average_project_completion_time,
                    "average_task_completion_time": self.metrics.average_task_completion_time,
                    "community_growth_rate": self.metrics.community_growth_rate,
                    "member_retention_rate": self.metrics.member_retention_rate,
                    "project_success_rate": self.metrics.project_success_rate,
                    "task_completion_rate": self.metrics.task_completion_rate,
                    "mentorship_success_rate": self.metrics.mentorship_success_rate,
                    "total_community_rewards": self.metrics.total_community_rewards,
                    "total_community_points": self.metrics.total_community_points,
                    "last_updated": self.metrics.last_updated.isoformat()
                }
            }
            
        except Exception as e:
            print(f"❌ Failed to get community metrics: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # Helper methods
    def _validate_member_data(self, member_address: str, member_name: str, member_email: str) -> bool:
        """Validate member data"""
        try:
            if not member_address or len(member_address) < 10:
                return False
            
            if not member_name or len(member_name.strip()) == 0:
                return False
            
            # Simple email validation
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, member_email):
                return False
            
            return True
        except Exception:
            return False
    
    def _check_skill_compatibility(self, member: CommunityMember, task: CommunityTask) -> bool:
        """Check if member has required skills for task"""
        try:
            # Check if member has at least 60% of required skills
            required_skills = set(task.required_skills)
            member_skills = set(member.skills.keys())
            
            if not required_skills:
                return True  # No specific skills required
            
            compatibility_percentage = len(required_skills.intersection(member_skills)) / len(required_skills)
            return compatibility_percentage >= 0.6
            
        except Exception:
            return False
    
    async def _check_member_achievements(self, member_address: str) -> None:
        """Check and award member achievements"""
        try:
            member = self.community_members[member_address]
            
            # Check first contribution
            if member.tasks_completed >= 1 and "first_contribution" not in member.badges:
                await self._award_achievement(member_address, "first_contribution")
            
            # Check contributor milestones
            if member.tasks_completed >= 10 and "contributor_10" not in member.badges:
                await self._award_achievement(member_address, "contributor_10")
            
            if member.tasks_completed >= 50 and "contributor_50" not in member.badges:
                await self._award_achievement(member_address, "contributor_50")
            
            # Check mentorship
            if member.mentoring_students >= 1 and "mentor" not in member.badges:
                await self._award_achievement(member_address, "mentor_first")
            
            # Check project leadership
            if any(p.project_lead_address == member_address for p in self.community_projects.values()):
                if "project_leader" not in member.badges:
                    await self._award_achievement(member_address, "project_leader")
            
        except Exception as e:
            print(f"Error checking member achievements: {e}")
    
    async def _award_achievement(self, member_address: str, achievement_key: str) -> None:
        """Award achievement to member"""
        try:
            if achievement_key in self.achievement_system:
                achievement = self.achievement_system[achievement_key]
                member = self.community_members[member_address]
                
                # Add badge
                member.badges.append(achievement_key)
                
                # Award rewards
                member.contribution_points += achievement["reward_points"]
                member.reputation_score += achievement["reward_points"] / 10
                
                # Update metrics
                self.metrics.total_community_points += achievement["reward_points"]
                self.metrics.total_community_rewards += achievement["reward_tokens"]
                
                print(f"🏆 Achievement awarded to {member.member_name}: {achievement['name']}")
                
        except Exception as e:
            print(f"Error awarding achievement: {e}")
    
    async def _update_community_metrics(self) -> None:
        """Update community metrics"""
        try:
            # Member metrics
            self.metrics.active_members = len([
                m for m in self.community_members.values() 
                if (datetime.now() - m.last_activity_date).days <= 30
            ])
            
            # Project metrics
            self.metrics.active_projects = len([
                p for p in self.community_projects.values() 
                if p.project_status in [ProjectStatus.PLANNING, ProjectStatus.IN_PROGRESS, ProjectStatus.TESTING]
            ])
            
            self.metrics.completed_projects = len([
                p for p in self.community_projects.values() 
                if p.project_status == ProjectStatus.COMPLETED
            ])
            
            # Task metrics
            self.metrics.open_tasks = len([
                t for t in self.community_tasks.values() 
                if t.task_status in [TaskStatus.OPEN, TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS]
            ])
            
            self.metrics.completed_tasks = len([
                t for t in self.community_tasks.values() 
                if t.task_status == TaskStatus.COMPLETED
            ])
            
            # Mentorship metrics
            self.metrics.active_mentorships = len([
                m for m in self.mentorship_programs.values() 
                if m.mentorship_status == "active"
            ])
            
            # Calculate rates
            if self.metrics.total_members > 0:
                self.metrics.member_retention_rate = self.metrics.active_members / self.metrics.total_members
            
            if self.metrics.total_projects > 0:
                self.metrics.project_success_rate = self.metrics.completed_projects / self.metrics.total_projects
            
            if self.metrics.total_tasks > 0:
                self.metrics.task_completion_rate = self.metrics.completed_tasks / self.metrics.total_tasks
            
            self.metrics.last_updated = datetime.now()
            
        except Exception as e:
            print(f"Error updating community metrics: {e}")
    
    def _monitoring_loop(self) -> None:
        """Monitoring loop (runs in separate thread)"""
        while self.monitoring_active:
            try:
                asyncio.run(self._update_community_metrics())
                time.sleep(300)  # Update every 5 minutes
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(60)
    
    async def _load_existing_data(self) -> None:
        """Load existing data from Redis"""
        try:
            # Load community members
            members_data = await self.redis_client.get("community_members")
            if members_data:
                self.community_members = pickle.loads(members_data)
            
            # Load community projects
            projects_data = await self.redis_client.get("community_projects")
            if projects_data:
                self.community_projects = pickle.loads(projects_data)
            
            # Load community tasks
            tasks_data = await self.redis_client.get("community_tasks")
            if tasks_data:
                self.community_tasks = pickle.loads(tasks_data)
            
        except Exception as e:
            print(f"Error loading existing data: {e}")


# Example usage and testing
async def test_community_development_tools():
    """Test SANGKURIANG Community Development Tools"""
    print("🚀 Testing SANGKURIANG Community Development Tools")
    
    # Initialize community tools
    community_tools = CommunityDevelopmentTools(
        enable_monitoring=True
    )
    
    # Wait for initialization
    await asyncio.sleep(2)
    
    # Test member registration
    print("\n👥 Registering community members...")
    member1 = await community_tools.register_community_member(
        member_address="0x1111111111111111111111111111111111111111",
        member_name="Budi Santoso",
        member_email="budi.santoso@example.com",
        member_bio="Blockchain developer and community enthusiast",
        community_roles=[CommunityRole.DEVELOPER, CommunityRole.MENTOR, CommunityRole.REVIEWER],
        skills={
            "Solidity": SkillLevel.EXPERT,
            "Python": SkillLevel.ADVANCED,
            "JavaScript": SkillLevel.INTERMEDIATE,
            "Smart Contracts": SkillLevel.EXPERT,
            "DeFi": SkillLevel.ADVANCED
        },
        programming_languages=["Solidity", "Python", "JavaScript", "TypeScript"],
        spoken_languages=["Indonesian", "English"],
        location="Jakarta, Indonesia",
        timezone="Asia/Jakarta",
        availability_hours=20,
        social_links={
            "github": "https://github.com/budisantoso",
            "twitter": "https://twitter.com/budisantoso",
            "linkedin": "https://linkedin.com/in/budisantoso"
        }
    )
    print(f"Member 1: {member1}")
    
    member2 = await community_tools.register_community_member(
        member_address="0x2222222222222222222222222222222222222222",
        member_name="Siti Nurhaliza",
        member_email="siti.nurhaliza@example.com",
        member_bio="Full-stack developer and UI/UX designer",
        community_roles=[CommunityRole.DEVELOPER, CommunityRole.DESIGNER, CommunityRole.CONTRIBUTOR],
        skills={
            "React": SkillLevel.ADVANCED,
            "Node.js": SkillLevel.ADVANCED,
            "UI/UX Design": SkillLevel.INTERMEDIATE,
            "Python": SkillLevel.INTERMEDIATE,
            "Database Design": SkillLevel.INTERMEDIATE
        },
        programming_languages=["JavaScript", "TypeScript", "Python", "CSS", "HTML"],
        spoken_languages=["Indonesian", "English"],
        location="Bandung, Indonesia",
        timezone="Asia/Jakarta",
        availability_hours=15,
        social_links={
            "github": "https://github.com/sitinurhaliza",
            "twitter": "https://twitter.com/sitinurhaliza",
            "dribbble": "https://dribbble.com/sitinurhaliza"
        }
    )
    print(f"Member 2: {member2}")
    
    # Test project creation
    print("\n📋 Creating community projects...")
    project1 = await community_tools.create_community_project(
        project_name="SANGKURIANG DAO Governance Interface",
        project_description="Build a user-friendly interface for SANGKURIANG DAO governance",
        project_type=ProjectType.DAPP,
        project_category="Governance",
        project_tags=["DAO", "Governance", "Web3", "React"],
        project_goals=[
            "Create intuitive voting interface",
            "Implement proposal creation workflow",
            "Add treasury management dashboard",
            "Integrate with smart contracts"
        ],
        project_requirements=[
            "React.js knowledge required",
            "Web3.js integration needed",
            "Mobile responsive design",
            "Accessibility compliance"
        ],
        project_technologies=["React", "Web3.js", "Material-UI", "IPFS"],
        project_difficulty="medium",
        estimated_duration_days=60,
        project_lead_address="0x1111111111111111111111111111111111111111",
        required_roles=[
            CommunityRole.DEVELOPER,
            CommunityRole.DESIGNER,
            CommunityRole.REVIEWER
        ],
        required_skills={
            "React": SkillLevel.INTERMEDIATE,
            "JavaScript": SkillLevel.INTERMEDIATE,
            "UI/UX Design": SkillLevel.BEGINNER,
            "Web3": SkillLevel.BEGINNER
        },
        project_budget=500.0,
        project_repository="https://github.com/sangkuriang/dao-interface",
        project_website="https://sangkuriang.org"
    )
    print(f"Project 1: {project1}")
    
    # Test task creation
    print("\n✅ Creating community tasks...")
    task1 = await community_tools.create_community_task(
        project_id=project1["project_id"],
        task_name="Design DAO Dashboard Mockups",
        task_description="Create UI/UX mockups for the DAO governance dashboard",
        task_type=TaskType.DESIGN,
        task_priority=8,
        task_difficulty="medium",
        estimated_hours=20,
        required_skills=["UI/UX Design", "Figma", "User Research"],
        required_tools=["Figma", "Adobe XD"],
        task_deliverables=["Dashboard mockups", "User flow diagrams", "Design system"],
        task_acceptance_criteria=[
            "Mobile responsive design",
            "Accessibility compliance",
            "Consistent with brand guidelines",
            "User testing feedback incorporated"
        ],
        task_rewards={
            "tokens": 1.5,
            "points": 15,
            "reputation": 10
        }
    )
    print(f"Task 1: {task1}")
    
    task2 = await community_tools.create_community_task(
        project_id=project1["project_id"],
        task_name="Implement Voting Contract Integration",
        task_description="Integrate smart contract voting functionality into the frontend",
        task_type=TaskType.CODING,
        task_priority=9,
        task_difficulty="hard",
        estimated_hours=40,
        required_skills=["Solidity", "Web3.js", "React", "Smart Contracts"],
        required_tools=["Hardhat", "MetaMask", "VS Code"],
        task_deliverables=["Voting integration code", "Unit tests", "Documentation"],
        task_acceptance_criteria=[
            "All voting functions work correctly",
            "Error handling implemented",
            "Gas optimization applied",
            "Security best practices followed"
        ],
        task_rewards={
            "tokens": 3.0,
            "points": 30,
            "reputation": 20
        }
    )
    print(f"Task 2: {task2}")
    
    # Test task assignment
    print("\n🎯 Assigning tasks to members...")
    assignment1 = await community_tools.assign_task_to_member(
        task_id=task1["task_id"],
        member_address="0x2222222222222222222222222222222222222222",
        assigned_by="0x1111111111111111111111111111111111111111"
    )
    print(f"Assignment 1: {assignment1}")
    
    assignment2 = await community_tools.assign_task_to_member(
        task_id=task2["task_id"],
        member_address="0x1111111111111111111111111111111111111111",
        assigned_by="0x1111111111111111111111111111111111111111"
    )
    print(f"Assignment 2: {assignment2}")
    
    # Test mentorship program
    print("\n🎓 Creating mentorship program...")
    mentorship = await community_tools.create_mentorship_program(
        mentor_address="0x1111111111111111111111111111111111111111",
        mentee_address="0x2222222222222222222222222222222222222222",
        mentorship_topic="Smart Contract Development",
        mentorship_goals=[
            "Learn Solidity basics",
            "Understand smart contract patterns",
            "Build first DeFi contract",
            "Security best practices"
        ],
        mentorship_duration_weeks=8,
        mentorship_type="one_on_one",
        meeting_frequency="weekly",
        meeting_duration_minutes=60,
        start_date=datetime.now(),
        end_date=datetime.now() + timedelta(weeks=8)
    )
    print(f"Mentorship: {mentorship}")
    
    # Test community recognition
    print("\n🏆 Giving community recognition...")
    recognition = await community_tools.give_community_recognition(
        recognition_type=RecognitionType.EXCELLENT_WORK,
        recipient_address="0x2222222222222222222222222222222222222222",
        giver_address="0x1111111111111111111111111111111111111111",
        recognition_title="Outstanding UI/UX Design Work",
        recognition_description="Exceptional design work on the DAO dashboard mockups",
        recognition_reason="Created beautiful and user-friendly designs that exceeded expectations",
        recognition_impact="Improved user experience and increased community engagement"
    )
    print(f"Recognition: {recognition}")
    
    # Test community event
    print("\n🎪 Creating community event...")
    event = await community_tools.create_community_event(
        event_name="SANGKURIANG DAO Workshop",
        event_description="Learn how to participate in SANGKURIANG DAO governance",
        event_type="workshop",
        event_format="online",
        event_start_datetime=datetime.now() + timedelta(days=7),
        event_end_datetime=datetime.now() + timedelta(days=7, hours=2),
        event_timezone="Asia/Jakarta",
        event_capacity=50,
        event_organizer_address="0x1111111111111111111111111111111111111111",
        event_topics=["DAO", "Governance", "Voting", "Treasury"],
        event_url="https://sangkuriang.org/workshop",
        event_budget=100.0
    )
    print(f"Event: {event}")
    
    # Get information
    print("\n📊 Getting community information...")
    
    # Get member profile
    member_profile = await community_tools.get_community_member_profile("0x1111111111111111111111111111111111111111")
    print(f"Member Profile: {member_profile}")
    
    # Get project info
    project_info = await community_tools.get_community_project_info(project1["project_id"])
    print(f"Project Info: {project_info}")
    
    # Get community metrics
    metrics = await community_tools.get_community_metrics()
    print(f"Community Metrics: {metrics}")
    
    print("\n✅ Community Development Tools testing completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_community_development_tools())