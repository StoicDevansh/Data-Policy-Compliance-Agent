"""
Approval Management - Tracks review decisions and approval workflows
"""
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional


class ApprovalManager:
    """
    Manages approval workflows for compliance violations.
    Tracks decisions, maintains audit trails, and handles escalations.
    """

    def __init__(self):
        """Initialize the approval manager."""
        self.approvals: Dict[str, Dict[str, Any]] = {}
        self.decision_log: List[Dict[str, Any]] = []

    def record_decision(
        self,
        violation_id: str,
        review_id: str,
        decision: str,
        reviewer: str,
        comments: Optional[str] = None
    ) -> str:
        """
        Record a review decision for a violation.

        Args:
            violation_id: ID of the violation being reviewed
            review_id: ID of the review task
            decision: Decision made ('approve', 'reject', 'escalate')
            reviewer: ID or name of the reviewer
            comments: Optional comments from the reviewer

        Returns:
            Approval record ID
        """
        approval_id = str(uuid.uuid4())

        approval_record = {
            'id': approval_id,
            'violation_id': violation_id,
            'review_id': review_id,
            'decision': decision,
            'reviewer': reviewer,
            'comments': comments,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'approved' if decision == 'approve' else 'pending'
        }

        self.approvals[approval_id] = approval_record

        # Add to decision log
        self.decision_log.append({
            'type': 'decision',
            'approval_id': approval_id,
            'violation_id': violation_id,
            'decision': decision,
            'reviewer': reviewer,
            'timestamp': approval_record['timestamp']
        })

        return approval_id

    def escalate_violation(
        self,
        violation_id: str,
        reason: str,
        escalation_level: str = 'manager'
    ) -> str:
        """
        Escalate a violation to a higher authority.

        Args:
            violation_id: ID of the violation to escalate
            reason: Reason for escalation
            escalation_level: Level of escalation ('manager', 'director', 'legal')

        Returns:
            Escalation record ID
        """
        escalation_id = str(uuid.uuid4())

        escalation_record = {
            'id': escalation_id,
            'violation_id': violation_id,
            'reason': reason,
            'escalation_level': escalation_level,
            'escalated_at': datetime.utcnow().isoformat(),
            'status': 'escalated'
        }

        self.approvals[escalation_id] = escalation_record

        # Add to decision log
        self.decision_log.append({
            'type': 'escalation',
            'escalation_id': escalation_id,
            'violation_id': violation_id,
            'reason': reason,
            'escalation_level': escalation_level,
            'timestamp': escalation_record['escalated_at']
        })

        return escalation_id

    def get_approvals_for_violation(
        self,
        violation_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all approvals related to a specific violation.

        Args:
            violation_id: ID of the violation

        Returns:
            List of approval records
        """
        return [
            approval for approval in self.approvals.values()
            if approval.get('violation_id') == violation_id
        ]

    def get_approval(self
        self,
        approval_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific approval record.

        Args:
            approval_id: ID of the approval

        Returns:
            Approval record if found, None otherwise
        """
        return self.approvals.get(approval_id)

    def update_approval_status(
        self,
        approval_id: str,
        status: str
    ) -> bool:
        """
        Update the status of an approval record.

        Args:
            approval_id: ID of the approval
            status: New status ('approved', 'rejected', 'escalated', 'resolved')

        Returns:
            True if update was successful, False if approval not found
        """
        if approval_id not in self.approvals:
            return False

        self.approvals[approval_id]['status'] = status
        self.approvals[approval_id]['updated_at'] = datetime.utcnow().isoformat()

        return True

    def get_decision_history(
        self,
        violation_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get the decision history for a violation or all violations.

        Args:
            violation_id: Optional violation ID to filter by

        Returns:
            List of decision log entries
        """
        if violation_id:
            return [
                entry for entry in self.decision_log
                if entry.get('violation_id') == violation_id
            ]
        return self.decision_log.copy()

    def get_approval_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about approvals.

        Returns:
            Dictionary with approval statistics
        """
        total_approvals = len(self.approvals)

        decisions = [a for a in self.approvals.values() if 'decision' in a]
        escalations = [a for a in self.approvals.values() if 'escalation_level' in a]

        by_decision = {'approve': 0, 'reject': 0, 'escalate': 0}
        for decision in decisions:
            by_decision[decision['decision']] += 1

        by_status = {'approved': 0, 'pending': 0, 'escalated': 0, 'resolved': 0}
        for approval in self.approvals.values():
            status = approval.get('status', 'pending')
            by_status[status] += 1

        by_level = {'manager': 0, 'director': 0, 'legal': 0}
        for escalation in escalations:
            level = escalation.get('escalation_level', 'manager')
            by_level[level] += 1

        return {
            'total_approvals': total_approvals,
            'by_decision': by_decision,
            'by_status': by_status,
            'by_escalation_level': by_level,
            'total_escalations': len(escalations),
            'recent_decisions': list(reversed(self.decision_log[-10:]))
        }