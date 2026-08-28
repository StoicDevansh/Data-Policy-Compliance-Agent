"""
Violation Detection Engine - Processes scan results to identify and categorize violations.
"""
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger


class ViolationEngine:
    """
    Process database scan results to detect, categorize, and score violations.
    """
    
    # Severity weights for scoring
    SEVERITY_WEIGHTS = {
        "critical": 100,
        "high": 75,
        "medium": 50,
        "low": 25
    }
    
    # Rule type risk multipliers
    RISK_MULTIPLIERS = {
        "data_encryption": 1.5,
        "data_retention": 1.3,
        "data_access": 1.4,
        "consent": 1.2,
        "age_restriction": 1.5,
        "geographic_restriction": 1.3,
        "audit_logging": 1.0,
        "data_masking": 1.1,
        "notification": 1.2,
        "other": 1.0
    }
    
    def __init__(self):
        """Initialize violation detection engine."""
        self.detected_violations: List[Dict[str, Any]] = []
    
    async def detect(
        self,
        scan_results: Dict[str, Any],
        rules: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Process scan results to detect and categorize violations.
        
        Args:
            scan_results: Results from database scanner
            rules: List of compliance rules
            
        Returns:
            List of detected violations with metadata
        """
        logger.info("Processing scan results for violations...")
        
        potential_violations = scan_results.get("potential_violations", [])
        rules_map = {r['id']: r for r in rules if 'id' in r}
        
        violations = []
        
        for pv in potential_violations:
            # Skip scan errors
            if pv.get('type') == 'scan_error':
                continue
            
            # Get associated rule
            rule_id = pv.get('rule_id')
            rule = rules_map.get(rule_id, {})
            
            # Create violation record
            violation = {
                "id": str(uuid.uuid4()),
                "scan_id": scan_results.get("scan_id"),
                "rule_id": rule_id,
                "rule_type": pv.get('type'),
                "rule_text": pv.get('rule_text') or rule.get('text'),
                "table": pv.get('table'),
                "column": pv.get('column'),
                "columns": pv.get('columns'),
                "violation_count": pv.get('violation_count', 1),
                "details": pv.get('details'),
                "detected_at": datetime.utcnow().isoformat(),
                "status": "open",
                "requires_review": pv.get('requires_review', False)
            }
            
            # Determine severity
            violation['severity'] = self._determine_severity(pv, rule)
            
            # Calculate risk score
            violation['risk_score'] = self._calculate_risk_score(violation)
            
            # Categorize violation
            violation['category'] = self._categorize_violation(violation)
            
            # Add compliance framework mappings
            violation['frameworks'] = self._map_to_frameworks(violation)
            
            violations.append(violation)
        
        # Sort by risk score (highest first)
        violations.sort(key=lambda v: v.get('risk_score', 0), reverse=True)
        
        self.detected_violations.extend(violations)
        
        logger.info(f"Detected {len(violations)} violations")
        
        return violations
    
    def _determine_severity(
        self,
        potential_violation: Dict[str, Any],
        rule: Dict[str, Any]
    ) -> str:
        """Determine violation severity based on type and rule."""
        # Use rule severity if available
        rule_severity = rule.get('severity')
        if rule_severity:
            return rule_severity
        
        # Determine based on violation type
        violation_type = potential_violation.get('type', '')
        
        # Critical violations
        if violation_type in ['data_encryption', 'age_restriction']:
            violation_count = potential_violation.get('violation_count', 1)
            if violation_count > 100:
                return "critical"
            return "high"
        
        # High severity
        if violation_type in ['data_retention', 'data_access', 'geographic_restriction']:
            return "high"
        
        # Medium severity
        if violation_type in ['consent', 'data_masking', 'notification']:
            return "medium"
        
        # Low severity
        if violation_type == 'audit_logging':
            return "low"
        
        return "medium"
    
    def _calculate_risk_score(self, violation: Dict[str, Any]) -> float:
        """Calculate risk score for a violation."""
        base_score = self.SEVERITY_WEIGHTS.get(violation.get('severity', 'medium'), 50)
        
        # Apply type multiplier
        rule_type = violation.get('rule_type', 'other')
        multiplier = self.RISK_MULTIPLIERS.get(rule_type, 1.0)
        
        # Apply count factor (logarithmic scaling)
        count = violation.get('violation_count', 1)
        import math
        count_factor = 1 + math.log10(max(count, 1)) * 0.1
        
        # Calculate final score
        score = base_score * multiplier * count_factor
        
        return round(min(score, 100), 2)  # Cap at 100
    
    def _categorize_violation(self, violation: Dict[str, Any]) -> str:
        """Categorize violation for grouping and reporting."""
        rule_type = violation.get('rule_type', '')
        
        categories = {
            'data_retention': 'Data Lifecycle',
            'data_access': 'Access Control',
            'data_encryption': 'Data Protection',
            'data_masking': 'Data Protection',
            'consent': 'Privacy Rights',
            'age_restriction': 'Privacy Rights',
            'geographic_restriction': 'Data Sovereignty',
            'audit_logging': 'Audit & Compliance',
            'notification': 'Incident Response'
        }
        
        return categories.get(rule_type, 'General Compliance')
    
    def _map_to_frameworks(self, violation: Dict[str, Any]) -> List[str]:
        """Map violation to relevant compliance frameworks."""
        frameworks = []
        rule_type = violation.get('rule_type', '')
        
        # GDPR mappings
        gdpr_types = ['consent', 'data_retention', 'geographic_restriction', 'data_access', 'notification']
        if rule_type in gdpr_types:
            frameworks.append('GDPR')
        
        # HIPAA mappings
        hipaa_types = ['data_encryption', 'data_access', 'audit_logging', 'data_retention']
        if rule_type in hipaa_types:
            frameworks.append('HIPAA')
        
        # CCPA mappings
        ccpa_types = ['consent', 'data_access', 'data_retention']
        if rule_type in ccpa_types:
            frameworks.append('CCPA')
        
        # PCI-DSS mappings
        pci_types = ['data_encryption', 'data_masking', 'data_access', 'audit_logging']
        if rule_type in pci_types:
            frameworks.append('PCI-DSS')
        
        # SOX mappings
        sox_types = ['audit_logging', 'data_access']
        if rule_type in sox_types:
            frameworks.append('SOX')
        
        # COPPA mappings
        if rule_type == 'age_restriction':
            frameworks.append('COPPA')
        
        return frameworks
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics of detected violations."""
        total = len(self.detected_violations)
        
        by_severity = {}
        by_category = {}
        by_type = {}
        by_framework = {}
        
        for v in self.detected_violations:
            # By severity
            sev = v.get('severity', 'unknown')
            by_severity[sev] = by_severity.get(sev, 0) + 1
            
            # By category
            cat = v.get('category', 'Unknown')
            by_category[cat] = by_category.get(cat, 0) + 1
            
            # By type
            typ = v.get('rule_type', 'unknown')
            by_type[typ] = by_type.get(typ, 0) + 1
            
            # By framework
            for fw in v.get('frameworks', []):
                by_framework[fw] = by_framework.get(fw, 0) + 1
        
        # Calculate average risk score
        avg_risk = 0
        if total > 0:
            avg_risk = sum(v.get('risk_score', 0) for v in self.detected_violations) / total
        
        return {
            "total_violations": total,
            "by_severity": by_severity,
            "by_category": by_category,
            "by_type": by_type,
            "by_framework": by_framework,
            "average_risk_score": round(avg_risk, 2),
            "critical_count": by_severity.get('critical', 0),
            "high_count": by_severity.get('high', 0),
            "requires_review": len([v for v in self.detected_violations if v.get('requires_review')])
        }
    
    def filter_violations(
        self,
        severity: Optional[str] = None,
        category: Optional[str] = None,
        rule_type: Optional[str] = None,
        status: Optional[str] = None,
        min_risk_score: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Filter violations based on criteria."""
        filtered = self.detected_violations
        
        if severity:
            filtered = [v for v in filtered if v.get('severity') == severity]
        
        if category:
            filtered = [v for v in filtered if v.get('category') == category]
        
        if rule_type:
            filtered = [v for v in filtered if v.get('rule_type') == rule_type]
        
        if status:
            filtered = [v for v in filtered if v.get('status') == status]
        
        if min_risk_score is not None:
            filtered = [v for v in filtered if v.get('risk_score', 0) >= min_risk_score]
        
        return filtered
