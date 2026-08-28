"""
Approvals Module - Multi-level approval management for compliance decisions.
"""
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from loguru import logger


class ApprovalLevel(str, Enum):
    """Approval hierarchy levels"""
    L1_DATA_STEWARD = "l1_data_steward"
    L2_COMPLIANCE_TEAM = "l2_compliance_team"
    L3_COMPLIANCE_OFFICER = "l3_compliance_officer"
    L4_EXECUTIVE = "l4_executive"


class ApprovalManager:
    """
    Manages multi-level approval workflows for compliance decisions.
    """
    
    # Approval matrix based on violation severity and type
    APPROVAL_MATRIX = {
        "critical": {
            "required_levels": [ApprovalLevel.L2_COMPLIANCE_TEAM, ApprovalLevel.L3_COMPLIANCE_OFFICER],
            "escalate_to": ApprovalLevel.L4_EXECUTIVE
        },
        "high": {
            "required_levels": [ApprovalLevel.L2_COMPLIANCE_TEAM],
            "escalate_to": ApprovalLevel.L3_COMPLIANCE_OFFICER
        },
        "medium": {
            "required_levels": [ApprovalLevel.L1_DATA_STEWARD],
            "escalate_to": ApprovalLevel.L2_COMPLIANCE_TEAM
        },
        "low": {
            "required_levels": [],
            "escalate_to": ApprovalLevel.L1_DATA_STEWARD
        }
    }
    
    def __init__(self):
        """Initialize approval manager."""
        self.approvals: Dict[str, Dict[str, Any]] = {}
        self.approval_history: List[Dict[str, Any]] = []
    
    async def create_approval_request(
        self,
        review_id: str,
        violations: List[Dict[str, Any]],
        requested_action: str,
        requester: str
    ) -> Dict[str, Any]:
        """
        Create an approval request for a compliance decision.
        
        Args:
            review_id: Associated review ID
            violations: Violations requiring approval
            requested_action: Action requiring approval
            requester: Who is requesting approval
            
        Returns:
            Approval request record
        """
        approval_id = str(uuid.uuid4())
        
        # Determine required approval levels based on severity
        max_severity = self._get_max_severity(violations)
        approval_config = self.APPROVAL_MATRIX.get(max_severity, self.APPROVAL_MATRIX['medium'])
        
        approval = {
            "id": approval_id,
            "review_id": review_id,
            "violation_ids": [v['id'] for v in violations],
            "requested_action": requested_action,
            "requester": requester,
            "max_severity": max_severity,
            "required_levels": [level.value for level in approval_config['required_levels']],
            "escalate_to": approval_config['escalate_to'].value,
            "approvals_received": [],
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        self.approvals[approval_id] = approval
        
        logger.info(f"Created approval request {approval_id} requiring {len(approval_config['required_levels'])} levels")
        
        return approval
    
    async def submit_approval(
        self,
        approval_id: str,
        approver: str,
        approver_level: str,
        approved: bool,
        comments: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Submit an approval decision.
        
        Args:
            approval_id: Approval request ID
            approver: Approver identifier
            approver_level: Approver's authorization level
            approved: Whether approved
            comments: Optional comments
            
        Returns:
            Updated approval record
        """
        approval = self.approvals.get(approval_id)
        if not approval:
            raise ValueError(f"Approval {approval_id} not found")
        
        # Validate approver level
        try:
            level = ApprovalLevel(approver_level)
        except ValueError:
            raise ValueError(f"Invalid approver level: {approver_level}")
        
        # Check if this level is required
        if level.value not in approval['required_levels'] and level.value != approval['escalate_to']:
            logger.warning(f"Approver level {level.value} not in required levels for approval {approval_id}")
        
        # Record approval
        approval_record = {
            "approver": approver,
            "level": level.value,
            "approved": approved,
            "comments": comments,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        approval['approvals_received'].append(approval_record)
        approval['updated_at'] = datetime.utcnow().isoformat()
        
        # Check if approval is complete
        if approved:
            received_levels = set(a['level'] for a in approval['approvals_received'] if a['approved'])
            required_levels = set(approval['required_levels'])
            
            if required_levels <= received_levels:
                approval['status'] = 'approved'
                approval['completed_at'] = datetime.utcnow().isoformat()
        else:
            approval['status'] = 'rejected'
            approval['rejected_by'] = approver
            approval['rejection_reason'] = comments
            approval['completed_at'] = datetime.utcnow().isoformat()
        
        # Store in history
        self.approval_history.append({
            "approval_id": approval_id,
            "action": "approved" if approved else "rejected",
            "approver": approver,
            "level": level.value,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return approval
    
    async def get_pending_approvals(
        self,
        approver_level: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get pending approvals, optionally filtered by level.
        
        Args:
            approver_level: Filter by approval level
            
        Returns:
            List of pending approvals
        """
        pending = [a for a in self.approvals.values() if a['status'] == 'pending']
        
        if approver_level:
            pending = [
                a for a in pending 
                if approver_level in a['required_levels'] 
                or approver_level == a['escalate_to']
            ]
        
        return pending
    
    async def escalate_approval(
        self,
        approval_id: str,
        reason: str,
        escalated_by: str
    ) -> Dict[str, Any]:
        """
        Escalate an approval to the next level.
        
        Args:
            approval_id: Approval to escalate
            reason: Reason for escalation
            escalated_by: Who escalated
            
        Returns:
            Updated approval record
        """
        approval = self.approvals.get(approval_id)
        if not approval:
            raise ValueError(f"Approval {approval_id} not found")
        
        # Add escalation level to required levels
        if approval['escalate_to'] not in approval['required_levels']:
            approval['required_levels'].append(approval['escalate_to'])
        
        approval['escalated'] = True
        approval['escalation_reason'] = reason
        approval['escalated_by'] = escalated_by
        approval['escalated_at'] = datetime.utcnow().isoformat()
        approval['updated_at'] = datetime.utcnow().isoformat()
        
        return approval
    
    def _get_max_severity(self, violations: List[Dict[str, Any]]) -> str:
        """Get the maximum severity from a list of violations."""
        severity_order = ['critical', 'high', 'medium', 'low']
        
        for severity in severity_order:
            if any(v.get('severity') == severity for v in violations):
                return severity
        
        return 'medium'
    
    def get_approval_statistics(self) -> Dict[str, Any]:
        """Get approval statistics."""
        total = len(self.approvals)
        pending = len([a for a in self.approvals.values() if a['status'] == 'pending'])
        approved = len([a for a in self.approvals.values() if a['status'] == 'approved'])
        rejected = len([a for a in self.approvals.values() if a['status'] == 'rejected'])
        
        return {
            "total_requests": total,
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
            "approval_rate": round(approved / (approved + rejected) * 100, 2) if (approved + rejected) > 0 else 0
        }
