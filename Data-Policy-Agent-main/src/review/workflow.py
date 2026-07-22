"""
Human Review Workflow - Manages the human oversight process for violation reviews.
"""
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from loguru import logger


class ReviewStatus(str, Enum):
    """Review workflow statuses"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ESCALATED = "escalated"


class ReviewDecision(str, Enum):
    """Review decision options"""
    APPROVE = "approve"  # Confirm as valid violation
    REJECT = "reject"    # Mark as false positive
    ESCALATE = "escalate"  # Escalate to higher authority


class ReviewWorkflow:
    """
    Manages human review workflow for compliance violations.
    Supports multi-level approvals, escalation, and audit trails.
    """
    
    def __init__(self):
        """Initialize review workflow manager."""
        self.reviews: Dict[str, Dict[str, Any]] = {}
        self.review_history: List[Dict[str, Any]] = []
    
    async def create_review(
        self,
        violations: List[Dict[str, Any]],
        reviewers: Optional[List[str]] = None,
        priority: str = "normal",
        due_date: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new review task for violations.
        
        Args:
            violations: List of violations to review
            reviewers: Optional list of reviewer IDs/emails
            priority: Review priority (low, normal, high, urgent)
            due_date: Optional due date for the review
            notes: Optional notes for reviewers
            
        Returns:
            Review task record
        """
        review_id = str(uuid.uuid4())
        
        # Determine priority based on severity if not specified
        if not reviewers:
            # Auto-assign based on severity
            reviewers = self._auto_assign_reviewers(violations)
        
        review = {
            "id": review_id,
            "violation_ids": [v['id'] for v in violations],
            "violations": violations,
            "reviewers": reviewers,
            "status": ReviewStatus.PENDING.value,
            "priority": priority,
            "due_date": due_date,
            "notes": notes,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "comments": [],
            "decisions": [],
            "audit_trail": [{
                "action": "created",
                "timestamp": datetime.utcnow().isoformat(),
                "details": f"Review created with {len(violations)} violations"
            }]
        }
        
        # Calculate summary stats
        review["summary"] = self._calculate_review_summary(violations)
        
        # Store review
        self.reviews[review_id] = review
        
        logger.info(f"Created review {review_id} for {len(violations)} violations")
        
        return review
    
    async def get_review(self, review_id: str) -> Optional[Dict[str, Any]]:
        """Get a review by ID."""
        return self.reviews.get(review_id)
    
    async def list_reviews(
        self,
        status: Optional[str] = None,
        reviewer: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List reviews with optional filtering.
        
        Args:
            status: Filter by status
            reviewer: Filter by reviewer ID
            
        Returns:
            List of matching reviews
        """
        reviews = list(self.reviews.values())
        
        if status:
            reviews = [r for r in reviews if r['status'] == status]
        
        if reviewer:
            reviews = [r for r in reviews if reviewer in r.get('reviewers', [])]
        
        # Sort by priority and creation date
        priority_order = {'urgent': 0, 'high': 1, 'normal': 2, 'low': 3}
        reviews.sort(key=lambda r: (
            priority_order.get(r.get('priority', 'normal'), 2),
            r.get('created_at', '')
        ))
        
        return reviews
    
    async def assign_reviewer(
        self,
        review_id: str,
        reviewer: str,
        assigned_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Assign a reviewer to a review task.
        
        Args:
            review_id: Review ID
            reviewer: Reviewer ID/email to assign
            assigned_by: Who assigned the reviewer
            
        Returns:
            Updated review record
        """
        review = self.reviews.get(review_id)
        if not review:
            raise ValueError(f"Review {review_id} not found")
        
        if reviewer not in review['reviewers']:
            review['reviewers'].append(reviewer)
        
        review['audit_trail'].append({
            "action": "reviewer_assigned",
            "timestamp": datetime.utcnow().isoformat(),
            "reviewer": reviewer,
            "assigned_by": assigned_by
        })
        
        review['updated_at'] = datetime.utcnow().isoformat()
        
        return review
    
    async def add_comment(
        self,
        review_id: str,
        comment: str,
        author: str,
        violation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a comment to a review.
        
        Args:
            review_id: Review ID
            comment: Comment text
            author: Comment author
            violation_id: Optional specific violation to comment on
            
        Returns:
            Updated review record
        """
        review = self.reviews.get(review_id)
        if not review:
            raise ValueError(f"Review {review_id} not found")
        
        comment_record = {
            "id": str(uuid.uuid4()),
            "text": comment,
            "author": author,
            "violation_id": violation_id,
            "created_at": datetime.utcnow().isoformat()
        }
        
        review['comments'].append(comment_record)
        review['updated_at'] = datetime.utcnow().isoformat()
        
        return review
    
    async def start_review(
        self,
        review_id: str,
        reviewer: str
    ) -> Dict[str, Any]:
        """
        Mark a review as in progress.
        
        Args:
            review_id: Review ID
            reviewer: Reviewer starting the review
            
        Returns:
            Updated review record
        """
        review = self.reviews.get(review_id)
        if not review:
            raise ValueError(f"Review {review_id} not found")
        
        review['status'] = ReviewStatus.IN_PROGRESS.value
        review['started_at'] = datetime.utcnow().isoformat()
        review['started_by'] = reviewer
        review['updated_at'] = datetime.utcnow().isoformat()
        
        review['audit_trail'].append({
            "action": "review_started",
            "timestamp": datetime.utcnow().isoformat(),
            "reviewer": reviewer
        })
        
        return review
    
    async def process_decision(
        self,
        review_id: str,
        decision: str,
        comments: Optional[str] = None,
        reviewer: Optional[str] = None,
        violation_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Process a review decision.
        
        Args:
            review_id: Review ID
            decision: Decision (approve, reject, escalate)
            comments: Optional decision comments
            reviewer: Reviewer making the decision
            violation_ids: Specific violations (if partial decision)
            
        Returns:
            Updated review record
        """
        review = self.reviews.get(review_id)
        if not review:
            raise ValueError(f"Review {review_id} not found")
        
        # Validate decision
        try:
            decision_enum = ReviewDecision(decision.lower())
        except ValueError:
            raise ValueError(f"Invalid decision: {decision}")
        
        # Create decision record
        decision_record = {
            "id": str(uuid.uuid4()),
            "decision": decision_enum.value,
            "comments": comments,
            "reviewer": reviewer,
            "violation_ids": violation_ids or review['violation_ids'],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        review['decisions'].append(decision_record)
        
        # Update violation statuses
        affected_violations = violation_ids or review['violation_ids']
        for v in review['violations']:
            if v['id'] in affected_violations:
                v['review_status'] = decision_enum.value
                v['reviewed_at'] = datetime.utcnow().isoformat()
                v['reviewed_by'] = reviewer
                v['review_comments'] = comments
                
                # Update violation status based on decision
                if decision_enum == ReviewDecision.APPROVE:
                    v['status'] = 'confirmed'
                elif decision_enum == ReviewDecision.REJECT:
                    v['status'] = 'false_positive'
                elif decision_enum == ReviewDecision.ESCALATE:
                    v['status'] = 'escalated'
        
        # Update review status
        if decision_enum == ReviewDecision.ESCALATE:
            review['status'] = ReviewStatus.ESCALATED.value
        elif len(review['decisions']) > 0:
            # Check if all violations have been decided
            decided_ids = set()
            for d in review['decisions']:
                decided_ids.update(d.get('violation_ids', []))
            
            if decided_ids >= set(review['violation_ids']):
                review['status'] = ReviewStatus.COMPLETED.value
                review['completed_at'] = datetime.utcnow().isoformat()
        
        review['updated_at'] = datetime.utcnow().isoformat()
        
        # Add to audit trail
        review['audit_trail'].append({
            "action": f"decision_{decision_enum.value}",
            "timestamp": datetime.utcnow().isoformat(),
            "reviewer": reviewer,
            "violations_affected": len(affected_violations),
            "comments": comments
        })
        
        # Store in history
        self.review_history.append({
            "review_id": review_id,
            "decision": decision_enum.value,
            "timestamp": datetime.utcnow().isoformat(),
            "reviewer": reviewer
        })
        
        logger.info(f"Review {review_id}: {decision_enum.value} decision for {len(affected_violations)} violations")
        
        return review
    
    async def escalate_review(
        self,
        review_id: str,
        escalate_to: List[str],
        reason: str,
        escalated_by: str
    ) -> Dict[str, Any]:
        """
        Escalate a review to higher authority.
        
        Args:
            review_id: Review ID
            escalate_to: List of escalation recipients
            reason: Reason for escalation
            escalated_by: Who escalated
            
        Returns:
            Updated review record
        """
        review = await self.process_decision(
            review_id=review_id,
            decision=ReviewDecision.ESCALATE.value,
            comments=reason,
            reviewer=escalated_by
        )
        
        review['escalated_to'] = escalate_to
        review['escalation_reason'] = reason
        
        review['audit_trail'].append({
            "action": "escalated",
            "timestamp": datetime.utcnow().isoformat(),
            "escalated_by": escalated_by,
            "escalated_to": escalate_to,
            "reason": reason
        })
        
        return review
    
    def _auto_assign_reviewers(
        self,
        violations: List[Dict[str, Any]]
    ) -> List[str]:
        """Auto-assign reviewers based on violation severity."""
        # In a real system, this would look up appropriate reviewers
        # For now, return placeholder
        severities = [v.get('severity') for v in violations]
        
        if 'critical' in severities:
            return ['security-team', 'compliance-officer']
        elif 'high' in severities:
            return ['compliance-team']
        else:
            return ['data-steward']
    
    def _calculate_review_summary(
        self,
        violations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate summary statistics for a review."""
        return {
            "total_violations": len(violations),
            "by_severity": {
                "critical": len([v for v in violations if v.get('severity') == 'critical']),
                "high": len([v for v in violations if v.get('severity') == 'high']),
                "medium": len([v for v in violations if v.get('severity') == 'medium']),
                "low": len([v for v in violations if v.get('severity') == 'low'])
            },
            "tables_affected": list(set(v.get('table') for v in violations if v.get('table'))),
            "rule_types": list(set(v.get('rule_type') for v in violations if v.get('rule_type')))
        }
    
    def get_review_statistics(self) -> Dict[str, Any]:
        """Get overall review statistics."""
        total = len(self.reviews)
        pending = len([r for r in self.reviews.values() if r['status'] == ReviewStatus.PENDING.value])
        in_progress = len([r for r in self.reviews.values() if r['status'] == ReviewStatus.IN_PROGRESS.value])
        completed = len([r for r in self.reviews.values() if r['status'] == ReviewStatus.COMPLETED.value])
        escalated = len([r for r in self.reviews.values() if r['status'] == ReviewStatus.ESCALATED.value])
        
        return {
            "total_reviews": total,
            "pending": pending,
            "in_progress": in_progress,
            "completed": completed,
            "escalated": escalated,
            "completion_rate": round(completed / total * 100, 2) if total > 0 else 0
        }
