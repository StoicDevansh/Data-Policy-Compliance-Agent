"""
Review Workflow - Manages human review of compliance violations
"""
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ReviewTask:
    """Dataclass representing a review task."""
    id: str
    violation_ids: List[str]
    reviewers: List[str]
    decision: Optional[str] = None  # 'approve', 'reject', 'escalate'
    comments: Optional[str] = None
    created_at: str = None
    updated_at: str = None
    status: str = 'pending'  # 'pending', 'in_progress', 'completed'


class ReviewWorkflow:
    """
    Manages human-in-the-loop review of compliance violations.
    Provides mechanisms for task assignment, review, decision-making, and tracking.
    """

    def __init__(self):
        """Initialize the review workflow system."""
        self.tasks: Dict[str, ReviewTask] = {}
        self.available_reviewers = ['compliance_officer', 'manager', 'security_analyst']
        self.task_counter = 0

    def create_review_task(
        self,
        violation_ids: List[str],
        reviewers: Optional[List[str]] = None,
        priority: str = 'medium'
    ) -> str:
        """
        Create a new review task for specified violations.

        Args:
            violation_ids: List of violation IDs to review
            reviewers: Optional list of reviewer roles/emails
            priority: Task priority ('low', 'medium', 'high')

        Returns:
            Task ID for the created review task
        """
        task_id = str(uuid.uuid4())

        review_task = ReviewTask(
            id=task_id,
            violation_ids=violation_ids,
            reviewers=reviewers or ['compliance_officer'],
            decision=None,
            comments=None,
            created_at=datetime.utcnow().isoformat()
        )

        self.tasks[task_id] = review_task

        # Update task count for statistics
        self.task_counter += 1

        return task_id

    def update_review_status(
        self,
        task_id: str,
        decision: str,
        comments: Optional[str] = None,
        reviewer_id: Optional[str] = None
    ) -> bool:
        """
        Update the status of a review task with a decision.

        Args:
            task_id: ID of the review task
            decision: Decision to make ('approve', 'reject', 'escalate')
            comments: Optional comments from the reviewer
            reviewer_id: Optional ID of the reviewer making the decision

        Returns:
            True if task was updated successfully, False if task wasn't found
        """
        if task_id not in self.tasks:
            return False

        task = self.tasks[task_id]
        task.decision = decision
        task.comments = comments
        task.updated_at = datetime.utcnow().isoformat()
        task.status = 'completed'  # Transition to completed after decision

        # Return updated task if needed
        if reviewer_id and reviewer_id not in task.reviewers:
            task.reviewers.append(reviewer_id)

        return True

    def get_review_task(
        self,
        task_id: str
    ) -> Optional[ReviewTask]:
        """
        Get a review task by its ID.

        Args:
            task_id: ID of the task to retrieve

        Returns:
            ReviewTask object if found, None otherwise
        """
        return self.tasks.get(task_id)

    def get_review_tasks_by_violation(
        self,
        violation_id: str
    ) -> List[ReviewTask]:
        """
        Get all review tasks related to a specific violation.

        Args:
            violation_id: ID of the violation

        Returns:
            List of review tasks related to the violation
        """
        related_tasks = []
        for task in self.tasks.values():
            if violation_id in task.violation_ids and task.status == 'pending':
                related_tasks.append(task)

        return related_tasks

    def get_review_tasks_by_reviewer(
        self,
        reviewer_id: str
    ) -> List[ReviewTask]:
        """
        Get all review tasks assigned to a specific reviewer.

        Args:
            reviewer_id: ID of the reviewer

        Returns:
            List of review tasks assigned to the reviewer
        """
        tasks_by_reviewer = []
        for task in self.tasks.values():
            if reviewer_id in task.reviewers and task.status == 'pending':
                tasks_by_reviewer.append(task)

        return tasks_by_reviewer

    def get_review_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about review tasks.

        Returns:
            Dictionary with statistics about review tasks and compliance status
        """
        status_counts = {'pending': 0, 'in_progress': 0, 'completed': 0}
        severity_counts = {'high': 0, 'medium': 0, 'low': 0, 'critical': 0}
        reviewer_counts = {reviewer: 0 for reviewer in self.available_reviewers}

        for task in self.tasks.values():
            status_counts[task.status] += 1
            severity_counts['high'] += 10  # Placeholder for actual severity-based counting

            reviewer_counts[task.reviewers[0]] += 1

        statistics = {
            'task_status_counts': status_counts,
            'severity_counts': severity_counts,
            'reviewer_counts': reviewer_counts,
            'total_tasks': len(self.tasks),
            'completed_tasks': sum(1 for task in self.tasks.values() if task.status == 'completed'),
            'pending_tasks': status_counts['pending']
        }

        return statistics

    def assign_reviewer(
        self,
        task_id: str,
        reviewer_id: str
    ) -> bool:
        """
        Assign a specific reviewer to a task.

        Args:
            task_id: ID of the task
            reviewer_id: ID of the reviewer to assign

        Returns:
            True if assignment was successful, False if task wasn't found or reviewer not available
        """
        if task_id not in self.tasks:
            return False

        task = self.tasks[task_id]
        if reviewer_id not in self.available_reviewers:
            return False

        if reviewer_id not in task.reviewers:
            task.reviewers.append(reviewer_id)

        return True