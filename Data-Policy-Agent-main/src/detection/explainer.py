"""
Violation Explainer - Generates human-readable explanations and remediation suggestions.
"""
import json
from typing import Dict, Any, List, Optional
from loguru import logger

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None


class ViolationExplainer:
    """
    Generate clear, explainable justifications for violations
    and suggest remediation steps.
    """
    
    # Pre-defined explanation templates for offline mode
    EXPLANATION_TEMPLATES = {
        "data_retention": {
            "template": "Data retention violation detected in {table}.{column}. {count} records exceed the maximum retention period of {period}. According to the policy, data should be deleted after this period to comply with data lifecycle requirements.",
            "remediation": [
                "Identify and archive or delete records older than the retention period",
                "Implement automated data purging based on retention rules",
                "Review data retention policies with legal/compliance team",
                "Set up monitoring alerts for aging data"
            ]
        },
        "data_encryption": {
            "template": "Unencrypted sensitive data detected in {table}.{column}. The column appears to contain plaintext sensitive information that should be encrypted according to data protection policies.",
            "remediation": [
                "Encrypt sensitive data at rest using AES-256 or equivalent",
                "Implement column-level encryption for sensitive fields",
                "Review encryption key management practices",
                "Audit all tables for additional unencrypted sensitive data"
            ]
        },
        "data_masking": {
            "template": "Unmasked sensitive data found in {table}.{column}. Personal information is stored in plaintext and should be masked or tokenized to protect privacy.",
            "remediation": [
                "Implement data masking for non-production environments",
                "Use tokenization for sensitive identifiers",
                "Apply dynamic data masking based on user roles",
                "Review access controls for sensitive data"
            ]
        },
        "data_access": {
            "template": "Potential access control violation in {table}. Sensitive columns ({columns}) may lack proper access restrictions as required by the policy.",
            "remediation": [
                "Implement role-based access control (RBAC)",
                "Review and restrict database user permissions",
                "Enable row-level security where applicable",
                "Audit access logs regularly"
            ]
        },
        "age_restriction": {
            "template": "Age restriction violation found in {table}. {count} records indicate users below the minimum required age. This may violate COPPA or similar regulations.",
            "remediation": [
                "Implement age verification at data collection point",
                "Review and remove records of underage users",
                "Update registration forms with age verification",
                "Consult legal team for compliance requirements"
            ]
        },
        "geographic_restriction": {
            "template": "Geographic data restriction concern in {table}.{column}. Data from restricted regions may be stored in violation of data residency requirements.",
            "remediation": [
                "Review data residency requirements for each region",
                "Implement geo-fencing for data storage",
                "Consider regional data centers for compliance",
                "Document data flow and storage locations"
            ]
        },
        "consent": {
            "template": "Consent compliance issue detected. Records may exist without proper consent documentation as required by privacy regulations.",
            "remediation": [
                "Implement consent management platform",
                "Update data collection forms with consent checkboxes",
                "Maintain audit trail of consent records",
                "Provide easy opt-out mechanisms"
            ]
        },
        "audit_logging": {
            "template": "Audit logging deficiency in {table}. The table lacks standard audit columns (created_at, updated_at, modified_by) required for compliance tracking.",
            "remediation": [
                "Add audit columns to track record changes",
                "Implement database triggers for audit logging",
                "Set up centralized audit log collection",
                "Enable change data capture (CDC)"
            ]
        },
        "notification": {
            "template": "Notification compliance issue. The system may not meet required notification timeframes for data breaches or incidents.",
            "remediation": [
                "Document incident response procedures",
                "Implement automated breach notification system",
                "Train staff on notification requirements",
                "Test incident response plans regularly"
            ]
        }
    }
    
    def __init__(self, llm_config: Optional[Any] = None):
        """
        Initialize violation explainer.
        
        Args:
            llm_config: LLM configuration for advanced explanations
        """
        self.llm_config = llm_config
        self.openai_client = None
        
        if llm_config and llm_config.api_key and AsyncOpenAI:
            self.openai_client = AsyncOpenAI(api_key=llm_config.api_key)
    
    async def explain(self, violation: Dict[str, Any]) -> str:
        """
        Generate a human-readable explanation for a violation.
        
        Args:
            violation: Violation record
            
        Returns:
            Clear explanation string
        """
        # Try LLM-based explanation first
        if self.openai_client:
            try:
                return await self._llm_explain(violation)
            except Exception as e:
                logger.warning(f"LLM explanation failed, using template: {e}")
        
        # Fall back to template-based explanation
        return self._template_explain(violation)
    
    async def _llm_explain(self, violation: Dict[str, Any]) -> str:
        """Generate explanation using LLM."""
        system_prompt = """You are a compliance expert explaining policy violations to business stakeholders.
        
Generate a clear, concise explanation of the violation that:
1. Explains what was found in plain language
2. Clarifies why this is a compliance issue
3. Describes the potential risks or impacts
4. Is suitable for both technical and non-technical audiences

Keep the explanation to 2-3 sentences. Be specific about the data involved."""

        user_prompt = f"""Explain this policy violation:

Type: {violation.get('rule_type')}
Table: {violation.get('table')}
Column: {violation.get('column') or violation.get('columns')}
Severity: {violation.get('severity')}
Details: {violation.get('details')}
Policy Rule: {violation.get('rule_text')}
Records Affected: {violation.get('violation_count', 'Unknown')}

Generate a clear explanation."""

        response = await self.openai_client.chat.completions.create(
            model=self.llm_config.model if self.llm_config else "gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=300
        )
        
        return response.choices[0].message.content.strip()
    
    def _template_explain(self, violation: Dict[str, Any]) -> str:
        """Generate explanation using templates."""
        rule_type = violation.get('rule_type', 'other')
        template_data = self.EXPLANATION_TEMPLATES.get(rule_type, {})
        
        template = template_data.get('template', 
            "Compliance violation detected in {table}. {details}")
        
        # Format template with violation data
        explanation = template.format(
            table=violation.get('table', 'unknown table'),
            column=violation.get('column', violation.get('columns', 'multiple columns')),
            columns=', '.join(violation.get('columns', [])) if violation.get('columns') else violation.get('column', ''),
            count=violation.get('violation_count', 'Multiple'),
            period=violation.get('details', ''),
            details=violation.get('details', 'Review needed.')
        )
        
        return explanation
    
    async def suggest_remediation(
        self,
        violation: Dict[str, Any]
    ) -> List[str]:
        """
        Suggest remediation steps for a violation.
        
        Args:
            violation: Violation record
            
        Returns:
            List of remediation steps
        """
        # Try LLM-based suggestions first
        if self.openai_client:
            try:
                return await self._llm_remediation(violation)
            except Exception as e:
                logger.warning(f"LLM remediation failed, using templates: {e}")
        
        # Fall back to template-based suggestions
        return self._template_remediation(violation)
    
    async def _llm_remediation(self, violation: Dict[str, Any]) -> List[str]:
        """Generate remediation suggestions using LLM."""
        system_prompt = """You are a compliance expert providing remediation guidance.
        
Generate 3-5 specific, actionable remediation steps for the policy violation.
Each step should be:
1. Clear and actionable
2. Technical where appropriate
3. Prioritized by importance
4. Feasible to implement

Return as a JSON array of strings."""

        user_prompt = f"""Suggest remediation for this violation:

Type: {violation.get('rule_type')}
Table: {violation.get('table')}
Column: {violation.get('column') or violation.get('columns')}
Severity: {violation.get('severity')}
Details: {violation.get('details')}
Policy Rule: {violation.get('rule_text')}

Return remediation steps as JSON array."""

        response = await self.openai_client.chat.completions.create(
            model=self.llm_config.model if self.llm_config else "gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=500,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        result = json.loads(content)
        
        # Handle different response structures
        if isinstance(result, list):
            return result
        return result.get('steps', result.get('remediation', []))
    
    def _template_remediation(self, violation: Dict[str, Any]) -> List[str]:
        """Get remediation suggestions from templates."""
        rule_type = violation.get('rule_type', 'other')
        template_data = self.EXPLANATION_TEMPLATES.get(rule_type, {})
        
        return template_data.get('remediation', [
            "Review the violation details with your compliance team",
            "Document the violation and create a remediation plan",
            "Implement necessary changes to address the compliance gap",
            "Verify remediation and update compliance documentation"
        ])
    
    async def generate_impact_assessment(
        self,
        violations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate an impact assessment for a group of violations.
        
        Args:
            violations: List of violations to assess
            
        Returns:
            Impact assessment report
        """
        # Count by severity
        severity_counts = {}
        framework_impacts = {}
        total_records = 0
        tables_affected = set()
        
        for v in violations:
            sev = v.get('severity', 'unknown')
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
            
            for fw in v.get('frameworks', []):
                framework_impacts[fw] = framework_impacts.get(fw, 0) + 1
            
            total_records += v.get('violation_count', 0)
            if v.get('table'):
                tables_affected.add(v['table'])
        
        # Determine overall risk level
        critical = severity_counts.get('critical', 0)
        high = severity_counts.get('high', 0)
        
        if critical > 0 or high > 5:
            overall_risk = "CRITICAL"
        elif high > 0:
            overall_risk = "HIGH"
        elif severity_counts.get('medium', 0) > 5:
            overall_risk = "MEDIUM"
        else:
            overall_risk = "LOW"
        
        assessment = {
            "overall_risk_level": overall_risk,
            "total_violations": len(violations),
            "total_records_affected": total_records,
            "tables_affected": list(tables_affected),
            "severity_breakdown": severity_counts,
            "framework_impacts": framework_impacts,
            "immediate_action_required": critical > 0 or high > 3,
            "recommendations": []
        }
        
        # Add recommendations based on risk
        if overall_risk == "CRITICAL":
            assessment["recommendations"].extend([
                "Immediately engage incident response team",
                "Notify compliance officer and legal team",
                "Begin emergency remediation procedures",
                "Document all findings for regulatory reporting"
            ])
        elif overall_risk == "HIGH":
            assessment["recommendations"].extend([
                "Prioritize remediation within 24-48 hours",
                "Brief management on compliance status",
                "Allocate resources for immediate fixes"
            ])
        else:
            assessment["recommendations"].extend([
                "Schedule remediation in next sprint",
                "Add violations to compliance backlog",
                "Review during next compliance review cycle"
            ])
        
        return assessment
