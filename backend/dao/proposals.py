"""
SANGKURIANG Community Proposals System
Sistem proposal komunitas dengan kategorisasi dan review process
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import hashlib
from urllib.parse import urlparse
from decimal import Decimal
import redis.asyncio as redis


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder untuk menangani Decimal dan tipe khusus lainnya"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)


class ProposalCategory(Enum):
    """Kategori proposal komunitas"""
    TECHNICAL = "technical"
    COMMUNITY = "community"
    FUNDING = "funding"
    GOVERNANCE = "governance"
    MARKETING = "marketing"
    PARTNERSHIP = "partnership"
    EDUCATION = "education"
    RESEARCH = "research"
    EMERGENCY = "emergency"


class ProposalPriority(Enum):
    """Prioritas proposal"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReviewStatus(Enum):
    """Status review proposal"""
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    NEEDS_REVISION = "needs_revision"
    APPROVED_FOR_VOTING = "approved_for_voting"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ProposalStage(Enum):
    """Tahapan proposal"""
    IDEA = "idea"
    DRAFT = "draft"
    COMMUNITY_REVIEW = "community_review"
    EXPERT_REVIEW = "expert_review"
    VOTING = "voting"
    IMPLEMENTATION = "implementation"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class CommunityProposal:
    """Representasi proposal komunitas"""
    id: str
    title: str
    description: str
    category: ProposalCategory
    priority: ProposalPriority
    author: str
    co_authors: List[str]
    review_status: ReviewStatus
    stage: ProposalStage
    created_at: float
    updated_at: float
    review_deadline: Optional[float]
    voting_start: Optional[float]
    voting_end: Optional[float]
    implementation_deadline: Optional[float]
    budget: Optional[Decimal]
    currency: str
    timeline: Dict  # Milestones dan deadlines
    resources: List[str]  # Links ke dokumen, GitHub, dll
    tags: List[str]
    related_proposals: List[str]
    review_notes: List[Dict]  # Catatan dari reviewer
    community_score: float  # Score dari komunitas (0-10)
    expert_score: float  # Score dari expert reviewer (0-10)
    revision_count: int
    views: int
    comments_count: int
    supporters: List[str]
    opposition: List[str]
    is_featured: bool
    language: str  # Bahasa proposal (id, en, dll)
    region: str  # Region target (indonesia, global, dll)


@dataclass
class ProposalReview:
    """Review untuk proposal"""
    id: str
    proposal_id: str
    reviewer: str
    reviewer_type: str  # community, expert, council
    score: float  # 0-10
    comments: str
    technical_feedback: Optional[str]
    economic_feedback: Optional[str]
    risk_assessment: Optional[str]
    recommendation: str  # approve, reject, revise
    created_at: float
    is_public: bool
    helpful_votes: int
    unhelpful_votes: int


@dataclass
class ProposalComment:
    """Komentar pada proposal"""
    id: str
    proposal_id: str
    author: str
    content: str
    parent_comment_id: Optional[str]
    created_at: float
    updated_at: float
    likes: int
    dislikes: int
    is_edited: bool
    language: str


@dataclass
class ProposalMetrics:
    """Metrics untuk proposal system"""
    total_proposals: int
    proposals_by_category: Dict[str, int]
    proposals_by_stage: Dict[str, int]
    proposals_by_priority: Dict[str, int]
    average_review_time: float
    average_community_score: float
    average_expert_score: float
    approval_rate: float
    implementation_rate: float
    community_participation: float


class CommunityProposals:
    """Sistem proposal komunitas utama"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.proposal_prefix = "community_proposal:"
        self.review_prefix = "proposal_review:"
        self.comment_prefix = "proposal_comment:"
        self.proposal_counter_key = "community_proposal_counter"
        self.review_counter_key = "proposal_review_counter"
        self.comment_counter_key = "proposal_comment_counter"
        self.active_proposals_key = "active_community_proposals"
        self.featured_proposals_key = "featured_community_proposals"
    
    async def submit_proposal(
        self,
        title: str,
        description: str,
        category: ProposalCategory,
        priority: ProposalPriority,
        author: str,
        co_authors: Optional[List[str]] = None,
        budget: Optional[Decimal] = None,
        currency: str = "IDR",
        timeline: Optional[Dict] = None,
        resources: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        related_proposals: Optional[List[str]] = None,
        language: str = "id",
        region: str = "indonesia"
    ) -> str:
        """Submit proposal komunitas baru"""
        # Validasi input
        if not title or len(title.strip()) < 10:
            raise ValueError("Title must be at least 10 characters")
        
        if not description or len(description.strip()) < 100:
            raise ValueError("Description must be at least 100 characters")
        
        # Validasi resources (URLs)
        if resources:
            for resource in resources:
                if not self._is_valid_url(resource):
                    raise ValueError(f"Invalid resource URL: {resource}")
        
        # Generate proposal ID
        counter = await self.redis.incr(self.proposal_counter_key)
        proposal_id = f"community_proposal_{counter}_{int(time.time())}"
        
        current_time = time.time()
        review_deadline = current_time + (7 * 24 * 3600)  # 7 hari untuk review
        
        # Buat proposal
        proposal = CommunityProposal(
            id=proposal_id,
            title=title.strip(),
            description=description.strip(),
            category=category,
            priority=priority,
            author=author,
            co_authors=co_authors or [],
            review_status=ReviewStatus.SUBMITTED,
            stage=ProposalStage.DRAFT,
            created_at=current_time,
            updated_at=current_time,
            review_deadline=review_deadline,
            voting_start=None,
            voting_end=None,
            implementation_deadline=None,
            budget=budget,
            currency=currency,
            timeline=timeline or {},
            resources=resources or [],
            tags=tags or [],
            related_proposals=related_proposals or [],
            review_notes=[],
            community_score=0.0,
            expert_score=0.0,
            revision_count=0,
            views=0,
            comments_count=0,
            supporters=[],
            opposition=[],
            is_featured=False,
            language=language,
            region=region
        )
        
        # Simpan proposal
        await self._save_proposal(proposal)
        
        # Tambahkan ke active proposals
        await self.redis.sadd(self.active_proposals_key, proposal_id)
        
        return proposal_id
    
    async def add_review(
        self,
        proposal_id: str,
        reviewer: str,
        reviewer_type: str,
        score: float,
        comments: str,
        technical_feedback: Optional[str] = None,
        economic_feedback: Optional[str] = None,
        risk_assessment: Optional[str] = None,
        recommendation: str = "revise",
        is_public: bool = True
    ) -> str:
        """Menambahkan review untuk proposal"""
        # Validasi proposal
        proposal = await self.get_proposal(proposal_id)
        if not proposal:
            raise ValueError("Proposal not found")
        
        # Validasi score
        if not (0 <= score <= 10):
            raise ValueError("Score must be between 0 and 10")
        
        # Validasi recommendation
        valid_recommendations = ["approve", "reject", "revise"]
        if recommendation not in valid_recommendations:
            raise ValueError(f"Recommendation must be one of {valid_recommendations}")
        
        # Generate review ID
        counter = await self.redis.incr(self.review_counter_key)
        review_id = f"proposal_review_{counter}_{int(time.time())}"
        
        # Buat review
        review = ProposalReview(
            id=review_id,
            proposal_id=proposal_id,
            reviewer=reviewer,
            reviewer_type=reviewer_type,
            score=score,
            comments=comments,
            technical_feedback=technical_feedback,
            economic_feedback=economic_feedback,
            risk_assessment=risk_assessment,
            recommendation=recommendation,
            created_at=time.time(),
            is_public=is_public,
            helpful_votes=0,
            unhelpful_votes=0
        )
        
        # Simpan review
        await self._save_review(review)
        
        # Update proposal score dan status
        await self._update_proposal_after_review(proposal_id, review)
        
        return review_id
    
    async def add_comment(
        self,
        proposal_id: str,
        author: str,
        content: str,
        parent_comment_id: Optional[str] = None,
        language: str = "id"
    ) -> str:
        """Menambahkan komentar pada proposal"""
        # Validasi proposal
        proposal = await self.get_proposal(proposal_id)
        if not proposal:
            raise ValueError("Proposal not found")
        
        # Validasi konten
        if not content or len(content.strip()) < 10:
            raise ValueError("Comment must be at least 10 characters")
        
        # Validasi parent comment jika ada
        if parent_comment_id:
            parent_comment = await self.get_comment(parent_comment_id)
            if not parent_comment or parent_comment.proposal_id != proposal_id:
                raise ValueError("Invalid parent comment")
        
        # Generate comment ID
        counter = await self.redis.incr(self.comment_counter_key)
        comment_id = f"proposal_comment_{counter}_{int(time.time())}"
        
        current_time = time.time()
        
        # Buat komentar
        comment = ProposalComment(
            id=comment_id,
            proposal_id=proposal_id,
            author=author,
            content=content.strip(),
            parent_comment_id=parent_comment_id,
            created_at=current_time,
            updated_at=current_time,
            likes=0,
            dislikes=0,
            is_edited=False,
            language=language
        )
        
        # Simpan komentar
        await self._save_comment(comment)
        
        # Update jumlah komentar pada proposal
        await self._update_comment_count(proposal_id)
        
        return comment_id
    
    async def vote_proposal(self, proposal_id: str, voter: str, vote_type: str) -> bool:
        """Vote untuk proposal (support/oppose)"""
        proposal = await self.get_proposal(proposal_id)
        if not proposal:
            raise ValueError("Proposal not found")
        
        # Validasi tipe vote
        if vote_type not in ["support", "oppose"]:
            raise ValueError("Vote type must be 'support' or 'oppose'")
        
        # Hapus vote sebelumnya jika ada
        if voter in proposal.supporters:
            proposal.supporters.remove(voter)
        if voter in proposal.opposition:
            proposal.opposition.remove(voter)
        
        # Tambahkan vote baru
        if vote_type == "support":
            proposal.supporters.append(voter)
        else:
            proposal.opposition.append(voter)
        
        # Update proposal
        proposal.updated_at = time.time()
        await self._save_proposal(proposal)
        
        return True
    
    async def feature_proposal(self, proposal_id: str, featured: bool = True) -> bool:
        """Feature/unfeature proposal"""
        proposal = await self.get_proposal(proposal_id)
        if not proposal:
            raise ValueError("Proposal not found")
        
        proposal.is_featured = featured
        proposal.updated_at = time.time()
        
        await self._save_proposal(proposal)
        
        # Update featured proposals set
        if featured:
            await self.redis.sadd(self.featured_proposals_key, proposal_id)
        else:
            await self.redis.srem(self.featured_proposals_key, proposal_id)
        
        return True
    
    async def get_proposal(self, proposal_id: str) -> Optional[CommunityProposal]:
        """Dapatkan detail proposal"""
        key = f"{self.proposal_prefix}{proposal_id}"
        data = await self.redis.get(key)
        
        if not data:
            return None
        
        proposal_dict = json.loads(data)
        proposal_dict['category'] = ProposalCategory(proposal_dict['category'])
        proposal_dict['priority'] = ProposalPriority(proposal_dict['priority'])
        proposal_dict['review_status'] = ReviewStatus(proposal_dict['review_status'])
        proposal_dict['stage'] = ProposalStage(proposal_dict['stage'])
        
        return CommunityProposal(**proposal_dict)
    
    async def get_comment(self, comment_id: str) -> Optional[ProposalComment]:
        """Dapatkan detail komentar"""
        key = f"{self.comment_prefix}{comment_id}"
        data = await self.redis.get(key)
        
        if not data:
            return None
        
        comment_dict = json.loads(data)
        return ProposalComment(**comment_dict)
    
    async def get_proposals(
        self,
        category: Optional[ProposalCategory] = None,
        stage: Optional[ProposalStage] = None,
        priority: Optional[ProposalPriority] = None,
        status: Optional[ReviewStatus] = None,
        language: Optional[str] = None,
        region: Optional[str] = None,
        featured: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[CommunityProposal]:
        """Dapatkan proposal dengan filter"""
        proposal_keys = await self.redis.keys(f"{self.proposal_prefix}*")
        proposals = []
        
        for key in proposal_keys[offset:offset + limit]:
            data = await self.redis.get(key)
            if data:
                proposal_dict = json.loads(data)
                proposal_dict['category'] = ProposalCategory(proposal_dict['category'])
                proposal_dict['priority'] = ProposalPriority(proposal_dict['priority'])
                proposal_dict['review_status'] = ReviewStatus(proposal_dict['review_status'])
                proposal_dict['stage'] = ProposalStage(proposal_dict['stage'])
                
                proposal = CommunityProposal(**proposal_dict)
                
                # Apply filters
                if category and proposal.category != category:
                    continue
                if stage and proposal.stage != stage:
                    continue
                if priority and proposal.priority != priority:
                    continue
                if status and proposal.review_status != status:
                    continue
                if language and proposal.language != language:
                    continue
                if region and proposal.region != region:
                    continue
                if featured is not None and proposal.is_featured != featured:
                    continue
                
                proposals.append(proposal)
        
        # Sort by created_at (newest first)
        return sorted(proposals, key=lambda x: x.created_at, reverse=True)
    
    async def get_proposal_reviews(self, proposal_id: str, public_only: bool = True) -> List[ProposalReview]:
        """Dapatkan semua review untuk proposal"""
        review_keys = await self.redis.keys(f"{self.review_prefix}*")
        reviews = []
        
        for key in review_keys:
            data = await self.redis.get(key)
            if data:
                review_dict = json.loads(data)
                if review_dict['proposal_id'] == proposal_id:
                    if not public_only or review_dict['is_public']:
                        review = ProposalReview(**review_dict)
                        reviews.append(review)
        
        # Sort by created_at (newest first)
        return sorted(reviews, key=lambda x: x.created_at, reverse=True)
    
    async def get_proposal_comments(self, proposal_id: str, limit: int = 100) -> List[ProposalComment]:
        """Dapatkan komentar untuk proposal"""
        comment_keys = await self.redis.keys(f"{self.comment_prefix}*")
        comments = []
        
        for key in comment_keys[:limit]:
            data = await self.redis.get(key)
            if data:
                comment_dict = json.loads(data)
                if comment_dict['proposal_id'] == proposal_id:
                    comment = ProposalComment(**comment_dict)
                    comments.append(comment)
        
        # Sort by created_at (oldest first for threaded view)
        return sorted(comments, key=lambda x: x.created_at)
    
    async def get_metrics(self) -> ProposalMetrics:
        """Dapatkan metrics untuk proposal system"""
        all_proposals = await self.get_proposals(limit=1000)
        
        total_proposals = len(all_proposals)
        
        # Count by category
        proposals_by_category = {}
        for category in ProposalCategory:
            count = len([p for p in all_proposals if p.category == category])
            proposals_by_category[category.value] = count
        
        # Count by stage
        proposals_by_stage = {}
        for stage in ProposalStage:
            count = len([p for p in all_proposals if p.stage == stage])
            proposals_by_stage[stage.value] = count
        
        # Count by priority
        proposals_by_priority = {}
        for priority in ProposalPriority:
            count = len([p for p in all_proposals if p.priority == priority])
            proposals_by_priority[priority.value] = count
        
        # Calculate averages
        community_scores = [p.community_score for p in all_proposals if p.community_score > 0]
        expert_scores = [p.expert_score for p in all_proposals if p.expert_score > 0]
        
        average_community_score = sum(community_scores) / len(community_scores) if community_scores else 0.0
        average_expert_score = sum(expert_scores) / len(expert_scores) if expert_scores else 0.0
        
        # Calculate rates
        approved_proposals = len([p for p in all_proposals if p.review_status == ReviewStatus.APPROVED_FOR_VOTING])
        implemented_proposals = len([p for p in all_proposals if p.stage == ProposalStage.COMPLETED])
        
        approval_rate = (approved_proposals / total_proposals * 100) if total_proposals > 0 else 0.0
        implementation_rate = (implemented_proposals / total_proposals * 100) if total_proposals > 0 else 0.0
        
        # Calculate community participation (based on supporters + opposition)
        total_participants = sum(len(p.supporters) + len(p.opposition) for p in all_proposals)
        community_participation = (total_participants / total_proposals) if total_proposals > 0 else 0.0
        
        return ProposalMetrics(
            total_proposals=total_proposals,
            proposals_by_category=proposals_by_category,
            proposals_by_stage=proposals_by_stage,
            proposals_by_priority=proposals_by_priority,
            average_review_time=0.0,  # Could be calculated from timestamps
            average_community_score=average_community_score,
            average_expert_score=average_expert_score,
            approval_rate=approval_rate,
            implementation_rate=implementation_rate,
            community_participation=community_participation
        )
    
    # Private methods
    
    async def _save_proposal(self, proposal: CommunityProposal):
        """Simpan proposal ke Redis"""
        key = f"{self.proposal_prefix}{proposal.id}"
        proposal_dict = asdict(proposal)
        proposal_dict['category'] = proposal.category.value
        proposal_dict['priority'] = proposal.priority.value
        proposal_dict['review_status'] = proposal.review_status.value
        proposal_dict['stage'] = proposal.stage.value
        
        await self.redis.set(key, json.dumps(proposal_dict, cls=DecimalEncoder))
    
    async def _save_review(self, review: ProposalReview):
        """Simpan review ke Redis"""
        key = f"{self.review_prefix}{review.id}"
        review_dict = asdict(review)
        await self.redis.set(key, json.dumps(review_dict, cls=DecimalEncoder))
    
    async def _save_comment(self, comment: ProposalComment):
        """Simpan komentar ke Redis"""
        key = f"{self.comment_prefix}{comment.id}"
        comment_dict = asdict(comment)
        await self.redis.set(key, json.dumps(comment_dict, cls=DecimalEncoder))
    
    async def _update_proposal_after_review(self, proposal_id: str, review: ProposalReview):
        """Update proposal setelah review ditambahkan"""
        proposal = await self.get_proposal(proposal_id)
        if not proposal:
            return
        
        # Update score berdasarkan tipe reviewer
        if review.reviewer_type == "community":
            # Update community score (rata-rata dari semua community reviews)
            reviews = await self.get_proposal_reviews(proposal_id, public_only=True)
            community_reviews = [r for r in reviews if r.reviewer_type == "community"]
            if community_reviews:
                proposal.community_score = sum(r.score for r in community_reviews) / len(community_reviews)
        
        elif review.reviewer_type == "expert":
            # Update expert score (rata-rata dari semua expert reviews)
            reviews = await self.get_proposal_reviews(proposal_id, public_only=True)
            expert_reviews = [r for r in reviews if r.reviewer_type == "expert"]
            if expert_reviews:
                proposal.expert_score = sum(r.score for r in expert_reviews) / len(expert_reviews)
        
        # Update status berdasarkan recommendation
        if review.recommendation == "approve":
            proposal.review_status = ReviewStatus.APPROVED_FOR_VOTING
            proposal.stage = ProposalStage.VOTING
        elif review.recommendation == "reject":
            proposal.review_status = ReviewStatus.REJECTED
        elif review.recommendation == "revise":
            proposal.review_status = ReviewStatus.NEEDS_REVISION
            proposal.revision_count += 1
        
        proposal.updated_at = time.time()
        await self._save_proposal(proposal)
    
    async def _update_comment_count(self, proposal_id: str):
        """Update jumlah komentar pada proposal"""
        comments = await self.get_proposal_comments(proposal_id)
        
        proposal = await self.get_proposal(proposal_id)
        if proposal:
            proposal.comments_count = len(comments)
            proposal.updated_at = time.time()
            await self._save_proposal(proposal)
    
    def _is_valid_url(self, url: str) -> bool:
        """Validasi URL"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False