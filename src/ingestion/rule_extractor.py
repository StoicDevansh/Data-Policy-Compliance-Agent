"""
Rule Extractor - Extracts compliance rules from policy text using NLP
"""
import re
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional


class RuleExtractor:
    """
    Extracts structured compliance rules from unstructured policy text.
    Uses pattern matching and keyword analysis to identify rule patterns.
    """

    def __init__(self, llm_config: Optional[Dict[str, Any]] = None):
        self.llm_config = llm_config or {}
        self.rule_patterns = self._build_rule_patterns()

    def _build_rule_patterns(self) -> List[Dict[str, Any]]:
        """Build pattern definitions for rule extraction."""
        return [
            {
                'name': 'threshold_rule',
                'patterns': [
                    r'(?:must|shall|should)\s+(?:not\s+)?(?:exceed|be\s+less\s+than|be\s+greater\s+than|be\s+above|be\s+below)\s+\$?(\d+(?:,\d{3})*(?:\.\d+)?)',
                    r'(?:transactions?\s+(?:exceeding|above|over|greater\s+than)\s+\$?)(\d+(?:,\d{3})*(?:\.\d+)?)',
                    r'(?:amounts?\s+(?:over|above|exceeding)\s+\$?)(\d+(?:,\d{3})*(?:\.\d+)?)'
                ],
                'rule_type': 'threshold'
            },
            {
                'name': 'retention_rule',
                'patterns': [
                    r'(?:retain|keep|store)\s+(?:data|records|information)\s+(?:for|for\s+a\s+period\s+of)\s+(\d+)\s+(days?|months?|years?)',
                    r'(?:data\s+retention|retention\s+period)\s*(?:of|:)\s*(\d+)\s+(days?|months?|years?)'
                ],
                'rule_type': 'data_retention'
            },
            {
                'name': 'encryption_rule',
                'patterns': [
                    r'(?:must|shall)\s+(?:encrypt|use\s+encryption\s+for)\s+(?:all\s+)?(?:sensitive|personal|financial|health)\s*(?:data|information|records?)',
                    r'(?:encryption\s+at\s+rest|encrypted\s+at\s+rest|encrypted\s+storage)'
                ],
                'rule_type': 'data_encryption'
            },
            {
                'name': 'access_control_rule',
                'patterns': [
                    r'(?:access\s+to|authorized\s+to\s+access|permitted\s+to\s+access)\s+(?:sensitive|personal|financial|health)\s*(?:data|information|records?)',
                    r'(?:role-based|rbac|least\s+privilege|need-to-know)'
                ],
                'rule_type': 'data_access'
            },
            {
                'name': 'consent_rule',
                'patterns': [
                    r'(?:consent|opt-in|opt-out|permission)\s+(?:must|shall|required)',
                    r'(?:explicit\s+consent|written\s+consent|verbal\s+consent)'
                ],
                'rule_type': 'consent'
            },
            {
                'name': 'audit_logging_rule',
                'patterns': [
                    r'(?:audit|log|track)\s+(?:all\s+)?(?:access|modifications?|changes|activities)',
                    r'(?:logging|audit\s+trail)\s+(?:must|shall|required|mandatory)'
                ],
                'rule_type': 'audit_logging'
            },
            {
                'name': 'data_masking_rule',
                'patterns': [
                    r'(?:mask|redact|anonymize|obfuscate)\s+(?:sensitive|personal|financial|health)\s*(?:data|information|records?)',
                    r'(?:data\s+masking|masking\s+of|masked\s+data)'
                ],
                'rule_type': 'data_masking'
            },
            {
                'name': 'geographic_rule',
                'patterns': [
                    r'(?:restrict|limit|prohibit)\s+(?:transfer|storage|processing)\s+(?:of\s+)?(?:data|information|records?)\s+(?:to|in|from)\s+(?:certain|specific|particular)?\s*(?:countries|regions|jurisdictions)',
                    r'(?:gdpr|eea|european\s+union|eu)\s+(?:compliance|requirements|restrictions)'
                ],
                'rule_type': 'geographic_restriction'
            },
            {
                'name': 'age_restriction_rule',
                'patterns': [
                    r'(?:age|under|below|minimum\s+age)\s*(?:must|shall|required)?\s*(\d+)\s*(?:years?|yrs?)',
                    r'(?:children|minors|under\s+1[3-9]|under\s+18|under\s+21)'
                ],
                'rule_type': 'age_restriction'
            },
            {
                'name': 'notification_rule',
                'patterns': [
                    r'(?:notify|inform|alert)\s+(?:users|individuals|customers|affected\s+parties)\s+(?:of|within|within\s+(\d+)\s+(days?|hours?))',
                    r'(?:breach|incident)\s+(?:notification|disclosure|reporting)'
                ],
                'rule_type': 'notification'
            }
        ]

    async def extract_rules(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Extract compliance rules from policy text.

        Args:
            text: The policy text to analyze
            metadata: Optional metadata about the source document

        Returns:
            List of extracted rules as dictionaries
        """
        rules = []
        metadata = metadata or {}
        policy_name = metadata.get('file_name', 'unknown_policy')

        # Process each rule pattern
        for pattern_def in self.rule_patterns:
            for pattern in pattern_def['patterns']:
                matches = re.finditer(pattern, text, re.IGNORECASE)

                for match in matches:
                    rule = self._create_rule(
                        match=match,
                        pattern_def=pattern_def,
                        text=text,
                        policy_name=policy_name
                    )
                    if rule:
                        rules.append(rule)

        # Deduplicate rules
        rules = self._deduplicate_rules(rules)

        # Assign severity levels
        for rule in rules:
            rule['severity'] = self._determine_severity(rule)

        return rules

    def _create_rule(self, match, pattern_def: Dict[str, Any], text: str, policy_name: str) -> Optional[Dict[str, Any]]:
        """Create a rule dictionary from a regex match."""
        rule_id = f"{pattern_def['rule_type'].upper()}-{uuid.uuid4().hex[:8].upper()}"

        # Extract context around the match
        start = max(0, match.start() - 100)
        end = min(len(text), match.end() + 100)
        context = text[start:end].strip()

        # Clean up the rule text
        rule_text = self._clean_text(match.group(0))

        return {
            'id': rule_id,
            'name': pattern_def['name'].replace('_', ' ').title(),
            'type': pattern_def['rule_type'],
            'text': rule_text,
            'context': context,
            'source_policy': policy_name,
            'extracted_at': datetime.utcnow().isoformat(),
            'confidence': 0.85,  # Confidence score for the extraction
            'entities': self._extract_entities(match, pattern_def)
        }

    def _extract_entities(self, match, pattern_def: Dict[str, Any]) -> List[str]:
        """Extract relevant entities from the match."""
        entities = []
        match_text = match.group(0).lower()

        # Common entity patterns
        entity_keywords = {
            'customer': ['customer', 'client', 'user', 'individual'],
            'employee': ['employee', 'staff', 'worker', 'personnel'],
            'transaction': ['transaction', 'payment', 'transfer', 'amount'],
            'account': ['account', 'profile', 'record'],
            'data': ['data', 'information', 'record', 'document'],
            'password': ['password', 'credential', 'token', 'secret'],
            'email': ['email', 'address', 'contact'],
            'ssn': ['ssn', 'social', 'identification', 'id number'],
            'credit_card': ['credit', 'card', 'payment', 'transaction']
        }

        for entity, keywords in entity_keywords.items():
            if any(kw in match_text for kw in keywords):
                entities.append(entity)

        return entities

    def _determine_severity(self, rule: Dict[str, Any]) -> str:
        """Determine severity level based on rule content."""
        rule_text = rule.get('text', '').lower()
        rule_type = rule.get('type', '')

        # Critical severity for high-risk patterns
        critical_indicators = [
            'must', 'shall', 'required', 'mandatory', 'comply',
            'violation', 'penalty', 'fine', 'illegal', 'prohibited'
        ]

        # Check for critical indicators
        if any(indicator in rule_text for indicator in critical_indicators):
            if rule_type in ['data_encryption', 'age_restriction', 'consent']:
                return 'critical'
            return 'high'

        # Medium severity for standard compliance rules
        if rule_type in ['data_retention', 'data_access', 'audit_logging']:
            return 'medium'

        # Low severity for informational rules
        if rule_type in ['notification', 'data_masking']:
            return 'medium'

        return 'medium'

    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text."""
        # Remove extra whitespace
        text = ' '.join(text.split())
        # Remove leading/trailing punctuation
        text = text.strip('.,;:!?')
        return text

    def _deduplicate_rules(self, rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate rules based on text similarity."""
        seen_texts = set()
        unique_rules = []

        for rule in rules:
            rule_text = rule.get('text', '').lower().strip()
            if rule_text not in seen_texts:
                seen_texts.add(rule_text)
                unique_rules.append(rule)

        return unique_rules