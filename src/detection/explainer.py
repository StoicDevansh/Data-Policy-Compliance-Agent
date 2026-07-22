"""
Violation Explainer - Provides explanations and remediation suggestions for violations
"""
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional


class ViolationExplainer:
    """
    Provides clear, actionable explanations for compliance violations
    and suggests remediation steps to address them.
    """

    def __init__(self, llm_config: Optional[Dict[str, Any]] = None):
        self.llm_config = llm_config or {}
        self.explanation_templates = self._load_explanation_templates()

    def _load_explanation_templates(self) -> Dict[str, Any]:
        """Load explanation templates for different violation types."""
        return {
            'data_encryption': {
                'title': 'Data Encryption Violation',
                'explanation': 'Sensitive data is not properly encrypted, creating security risks.',
                'impact': 'Unauthorized access to sensitive information, potential data breaches',
                'urgency': 'High',
                'affected_systems': ['database storage', 'file systems'],
                'technical_description': 'Encryption should be applied to all sensitive data at rest and in transit.'
            },
            'data_retention': {
                'title': 'Data Retention Period Violation',
                'explanation': 'Data is being retained beyond approved time periods.',
                'impact': 'Increased storage costs and regulatory non-compliance',
                'urgency': 'Medium',
                'affected_systems': ['database records', 'backup systems'],
                'technical_description': 'Data must be automatically deleted or anonymized after specified retention periods.'
            },
            'data_access': {
                'title': 'Access Control Violation',
                'explanation': 'Access controls are insufficient or not properly implemented for sensitive data.',
                'impact': 'Unauthorized access to sensitive information',
                'urgency': 'High',
                'affected_systems': ['database systems', 'application access'],
                'technical_description': 'Implement role-based access control and enforce least privilege principles.'
            },
            'data_masking': {
                'title': 'Data Masking Violation',
                'explanation': 'Sensitive data is exposed in unmasked form where it should be protected.',
                'impact': 'Risk of data exposure during development, testing, or analytics',
                'urgency': 'Medium',
                'affected_systems': ['data warehouses', 'reporting systems'],
                'technical_description': 'Apply data masking, tokenization, or anonymization to sensitive data in non-production environments.'
            },
            'consent': {
                'title': 'Consent Management Violation',
                'explanation': 'Individuals have not provided or have not withdrawn consent for data processing.',
                'impact': 'Regulatory non-compliance and loss of customer trust',
                'urgency': 'High',
                'affected_systems': ['customer databases', 'consent management systems'],
                'technical_description': 'Implement proper consent capture, storage, and withdrawal mechanisms.'
            },
            'audit_logging': {
                'title': 'Audit Logging Violation',
                'explanation': 'Required audit trails are not being properly maintained.',
                'impact': 'Inability to investigate security incidents or compliance violations',
                'urgency': 'High',
                'affected_systems': ['system logs', 'event records'],
                'technical_description': 'Implement comprehensive logging of all access, modifications, and system activities.'
            },
            'age_restriction': {
                'title': 'Age Restriction Violation',
                'explanation': 'Data processing involves minors or individuals below required age.',
                'impact': 'Violation of privacy laws and regulations for children','' urgency': 'Critical',
                'affected_systems': ['customer databases', 'registration systems'],
                'technical_description': 'Implement age verification and restrict access to data from minors.'
            },
            'geographic_restriction': {
                'title': 'Geographic Restriction Violation',
                'explanation': 'Data is being transferred to restricted jurisdictions or regions.',
                'impact': 'Violation of data sovereignty laws and international regulations',
                'urgency': 'High',
                'affected_systems': ['data transfer systems', 'cloud services'],
                'technical_description': 'Implement geographic access controls and data localization where required.'
            },
            'notification': {
                'title': 'Notification Violation',
                'explanation': 'Required notifications for data breaches or incidents are not being made.',
                'impact': 'Regulatory penalties and customer trust issues',
                'urgency': 'Critical',
                'affected_systems': ['notification systems', 'alert mechanisms'],
                'technical_description': 'Implement breach detection and automated notification systems.'
            }
        }

    async def explain(self, violation: Dict[str, Any]) -> str:
        """
        Generate a clear explanation for a violation.

        Args:
            violation: The violation to explain

        Returns:
            A human-readable explanation of the violation
        """
        violation_type = violation.get('type', 'generic')
        template = self.explanation_templates.get(violation_type, self._get_generic_template())

        # Generate explanation using template and violation details
        explanation_parts = [
            f"Violation: {template['title']}",
            f"\n\nExplanation: {template['explanation']}",
            f"\nImpact: {template['impact']}",
            f"\nPriority: {template['urgency']}",
            f"\nAffected Systems: {', '.join(template['affected_systems'])}"
        ]

        # Add specific violation details if available
        if violation.get('violation_count', 1) > 1:
            explanation_parts.append(f"\n\nCount: {violation['violation_count']} instances found")

        if violation.get('table'):
            explanation_parts.append(f"\nTable: {violation['table']}")

        if violation.get('column'):
            explanation_parts.append(f"\nColumn: {violation['column']}")

        explanation_parts.append(f"\n\nTechnical Details: {template['technical_description']}")

        return "\n".join(explanation_parts)

    async def suggest_remediation(self, violation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Suggest remediation steps for a violation.

        Args:
            violation: The violation to remediate

        Returns:
            Dictionary with remediation suggestions and details
        """
        violation_type = violation.get('type', 'generic')
        remediation_plan = {
            'immediate_actions': [],
            'short_term_fixes': [],
            'long_term_improvements': [],
            'estimated_effort': 'medium',
            'estimated_timeframe': '30-90 days',
            'priority': 'high'
        }

        # Generate specific remediation based on violation type
        if violation_type == 'data_encryption':
            remediation_plan['immediate_actions'] = [
                'Encrypt sensitive columns in the database using AES-256',
                'Enable HTTPS for all data transmissions',
                'Implement key management system'
            ]
            remediation_plan['short_term_fixes'] = [
                'Apply encryption to PII (Personal Identifiable Information)',
                'Use encrypted backup protocols',
                'Implement encrypted logging'
            ]
            remediation_plan['long_term_improvements'] = [
                'Implement automated encryption key rotation',
                'Add encryption monitoring and alerting',
                'Implement comprehensive data classification system'
            ]
            remediation_plan['estimated_effort'] = 'high'

        elif violation_type == 'data_retention':
            remediation_plan['immediate_actions'] = [
                'Implement data retention policies and procedures',
                'Set up automated data deletion scripts',
                'Create data retention audit trails'
            ]
            remediation_plan['short_term_fixes'] = [
                'Identify and classify data subject to retention policies',
                'Implement data lifecycle management',
                'Set up retention period alerts'
            ]
            remediation_plan['long_term_improvements'] = [
                'Implement automated data purging based on metadata',
                'Create data retention reporting dashboard',
                'Integrate retention policies with data classification systems'
            ]
            remediation_plan['estimated_effort'] = 'medium'

        elif violation_type == 'data_access':
            remediation_plan['immediate_actions'] = [
                'Review and update access control policies',
                'Conduct access rights audit',
                'Implement emergency access procedures'
            ]
            remediation_plan['short_term_fixes'] = [
                'Implement multi-factor authentication for privileged access',
                'Add access logging and monitoring',
                'Create access delegation procedures'
            ]
            remediation_plan['long_term_improvements'] = [
                'Implement privileged access management system',
                'Add just-in-time access provisioning',
                'Create comprehensive access governance framework'
            ]
            remediation_plan['estimated_effort'] = 'high'

        else:
            # Generic remediation plan
            remediation_plan['immediate_actions'] = [
                'Assess the specific violation details',
                'Document current state and requirements',
                'Create action plan for compliance'
            ]
            remediation_plan['short_term_fixes'] = [
                'Implement quick fixes to achieve compliance',
                'Update documentation and procedures',
                'Train staff on new requirements'
            ]
            remediation_plan['long_term_improvements'] = [
                'Implement preventive controls',
                'Create automated compliance monitoring',
                'Establish continuous improvement process'
            ]
            remediation_plan['estimated_effort'] = 'medium'

        remediation_plan['created_at'] = datetime.utcnow().isoformat()

        return remediation_plan

    async def explain(self, violation: Dict[str, Any]) -> str:
        """
        Generate a clear explanation for a violation.

        Args:
            violation: The violation to explain

        Returns:
            A human-readable explanation of the violation
        """
        violation_type = violation.get('type', 'generic')
        template = self.explanation_templates.get(violation_type, self._get_generic_template())

        # Generate explanation using template and violation details
        explanation_parts = [
            f"Violation: {template['title']}",
            f"\n\nExplanation: {template['explanation']}",
            f"\nImpact: {template['impact']}",
            f"\nPriority: {template['urgency']}",
            f"\nAffected Systems: {', '.join(template['affected_systems'])}"
        ]

        # Add specific violation details if available
        if violation.get('violation_count', 1) > 1:
            explanation_parts.append(f"\n\nCount: {violation['violation_count']} instances found")

        if violation.get('table'):
            explanation_parts.append(f"\nTable: {violation['table']}")

        if violation.get('column'):
            explanation_parts.append(f"\nColumn: {violation['column']}")

        explanation_parts.append(f"\n\nTechnical Details: {template['technical_description']}")

        return "\n".join(explanation_parts)

    async def suggest_remediation(self, violation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Suggest remediation steps for a violation.

        Args:
            violation: The violation to remediate

        Returns:
            Dictionary with remediation suggestions and details
        """
        violation_type = violation.get('type', 'generic')
        remediation_plan = {
            'immediate_actions': [],
            'short_term_fixes': [],
            'long_term_improvements': [],
            'estimated_effort': 'medium',
            'estimated_timeframe': '30-90 days',
            'priority': 'high'
        }

        # Generate specific remediation based on violation type
        if violation_type == 'data_encryption':
            remediation_plan['immediate_actions'] = [
                'Encrypt sensitive columns in the database using AES-256',
                'Enable HTTPS for all data transmissions',
                'Implement key management system'
            ]
            remediation_plan['short_term_fixes'] = [
                'Apply encryption to PII (Personal Identifiable Information)',
                'Use encrypted backup protocols',
                'Implement encrypted logging'
            ]
            remediation_plan['long_term_improvements'] = [
                'Implement automated encryption key rotation',
                'Add encryption monitoring and alerting',
                'Implement comprehensive data classification system'
            ]
            remediation_plan['estimated_effort'] = 'high'

        elif violation_type == 'data_retention':
            remediation_plan['immediate_actions'] = [
                'Implement data retention policies and procedures',
                'Set up automated data deletion scripts',
                'Create data retention audit trails'
            ]
            remediation_plan['short_term_fixes'] = [
                'Identify and classify data subject to retention policies',
                'Implement data lifecycle management',
                'Set up retention period alerts'
            ]
            remediation_plan['long_term_improvements'] = [
                'Implement automated data purging based on metadata',
                'Create data retention reporting dashboard',
                'Integrate retention policies with data classification systems'
            ]
            remediation_plan['estimated_effort'] = 'medium'

        elif violation_type == 'data_access':
            remediation_plan['immediate_actions'] = [
                'Review and update access control policies',
                'Conduct access rights audit',
                'Implement emergency access procedures'
            ]
            remediation_plan['short_term_fixes'] = [
                'Implement multi-factor authentication for privileged access',
                'Add access logging and monitoring',
                'Create access delegation procedures'
            ]
            remediation_plan['long_term_improvements'] = [
                'Implement privileged access management system',
                'Add just-in-time access provisioning',
                'Create comprehensive access governance framework'
            ]
            remediation_plan['estimated_effort'] = 'high'

        else:
            # Generic remediation plan
            remediation_plan['immediate_actions'] = [
                'Assess the specific violation details',
                'Document current state and requirements',
                'Create action plan for compliance'
            ]
            remediation_plan['short_term_fixes'] = [
                'Implement quick fixes to achieve compliance',
                'Update documentation and procedures',
                'Train staff on new requirements'
            ]
            remediation_plan['long_term_improvements'] = [
                'Implement preventive controls',
                'Create automated compliance monitoring',
                'Establish continuous improvement process'
            ]
            remediation_plan['estimated_effort'] = 'medium'

        remediation_plan['created_at'] = datetime.utcnow().isoformat()

        return remediation_plan

    def _get_generic_template(self) -> Dict[str, Any]:
        """Get generic explanation template for unknown violation types."""
        return {
            'title': 'Compliance Violation',
            'explanation': 'A compliance violation has been detected that requires attention.',
            'impact': 'Potential regulatory non-compliance and associated risks.',
            'urgency': 'Medium',
            'affected_systems': ['various systems'],
            'technical_description': 'The specific violation requires investigation and remediation.'
        }