"""
Rule Extraction Engine - Uses NLP/LLM to extract actionable compliance rules from policy text.
"""
import json
import re
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None

try:
    import spacy
    NLP_AVAILABLE = True
except ImportError:
    NLP_AVAILABLE = False


class RuleExtractor:
    """
    Extract actionable compliance rules from policy document text.
    Uses a combination of NLP pattern matching and LLM-based extraction.
    """
    
    # Rule type patterns for initial classification
    RULE_PATTERNS = {
        "data_retention": [
            r"(?:retain|keep|store|maintain).*?(?:for|within|no longer than)\s*(\d+)\s*(days?|months?|years?)",
            r"(?:delete|remove|purge|destroy).*?(?:after|within)\s*(\d+)\s*(days?|months?|years?)",
            r"retention\s*(?:period|policy|requirement).*?(\d+)\s*(days?|months?|years?)"
        ],
        "data_access": [
            r"(?:only|must|shall).*?(?:authorized|permitted|approved).*?(?:access|view|read)",
            r"(?:restrict|limit).*?access.*?to",
            r"role-based\s*access",
            r"principle\s*of\s*least\s*privilege"
        ],
        "data_encryption": [
            r"(?:encrypt|encrypted|encryption).*?(?:at rest|in transit|both)",
            r"(?:AES|RSA|TLS|SSL).*?(?:256|128|bit)",
            r"(?:sensitive|personal|PII).*?(?:must be|shall be).*?encrypt"
        ],
        "data_masking": [
            r"(?:mask|redact|anonymize|pseudonymize).*?(?:sensitive|personal|PII)",
            r"(?:display|show).*?(?:last|first)\s*(\d+)\s*(?:digits?|characters?)"
        ],
        "consent": [
            r"(?:explicit|informed)?\s*consent.*?(?:required|must|shall)",
            r"opt-(?:in|out).*?(?:required|must)",
            r"(?:user|customer).*?(?:agreement|permission).*?(?:before|prior)"
        ],
        "audit_logging": [
            r"(?:log|audit|track|record).*?(?:all|every)?\s*(?:access|changes?|modifications?)",
            r"audit\s*trail",
            r"(?:maintain|keep).*?(?:logs?|records?).*?(\d+)\s*(days?|months?|years?)"
        ],
        "geographic_restriction": [
            r"(?:data|information).*?(?:must|shall|should).*?(?:not|never).*?(?:transfer|move|store).*?(?:outside|beyond)",
            r"(?:within|inside).*?(?:jurisdiction|country|region|EU|US|EEA)"
        ],
        "age_restriction": [
            r"(?:minimum|at least)\s*(\d+)\s*(?:years?\s*old|years?\s*of\s*age)",
            r"(?:under|below)\s*(\d+).*?(?:prohibited|not allowed|restricted)"
        ],
        "notification": [
            r"(?:notify|inform|alert).*?(?:within|no later than)\s*(\d+)\s*(hours?|days?)",
            r"(?:breach|incident).*?notification"
        ]
    }
    
    # Severity indicators
    SEVERITY_KEYWORDS = {
        "critical": ["must", "shall", "required", "mandatory", "prohibited", "never", "always"],
        "high": ["should", "important", "recommended", "expected"],
        "medium": ["may", "could", "consider", "advisable"],
        "low": ["optional", "preferred", "suggested"]
    }
    
    def __init__(self, llm_config: Optional[Any] = None):
        """
        Initialize the rule extractor.
        
        Args:
            llm_config: LLM configuration for advanced extraction
        """
        self.llm_config = llm_config
        self.openai_client = None
        
        if llm_config and llm_config.api_key and AsyncOpenAI:
            self.openai_client = AsyncOpenAI(api_key=llm_config.api_key)
        
        # Load spaCy model if available
        self.nlp = None
        if NLP_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                logger.warning("spaCy model not found. Run: python -m spacy download en_core_web_sm")
    
    async def extract_rules(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract compliance rules from policy text.
        
        Args:
            text: Policy document text
            metadata: Optional document metadata
            
        Returns:
            List of extracted rules with metadata
        """
        logger.info("Extracting compliance rules from policy text...")
        
        rules = []
        
        # First, try pattern-based extraction
        pattern_rules = self._extract_pattern_rules(text)
        rules.extend(pattern_rules)
        
        # Then, use LLM for comprehensive extraction
        if self.openai_client:
            llm_rules = await self._extract_llm_rules(text, metadata)
            
            # Merge and deduplicate
            rules = self._merge_rules(rules, llm_rules)
        
        # Enhance rules with additional metadata
        for rule in rules:
            rule['id'] = rule.get('id') or str(uuid.uuid4())
            rule['created_at'] = datetime.utcnow().isoformat()
            rule['status'] = 'active'
            
            # Determine severity if not set
            if 'severity' not in rule:
                rule['severity'] = self._determine_severity(rule.get('text', ''))
            
            # Generate SQL condition if possible
            if 'sql_condition' not in rule:
                rule['sql_condition'] = self._generate_sql_condition(rule)
        
        logger.info(f"Extracted {len(rules)} compliance rules")
        
        return rules
    
    def _extract_pattern_rules(self, text: str) -> List[Dict[str, Any]]:
        """Extract rules using regex patterns."""
        rules = []
        
        # Split text into sentences for better context
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        for rule_type, patterns in self.RULE_PATTERNS.items():
            for pattern in patterns:
                for sentence in sentences:
                    matches = re.finditer(pattern, sentence, re.IGNORECASE)
                    for match in matches:
                        rule = {
                            "type": rule_type,
                            "text": sentence.strip(),
                            "pattern_match": match.group(0),
                            "groups": match.groups(),
                            "extraction_method": "pattern"
                        }
                        
                        # Extract specific values based on rule type
                        if rule_type == "data_retention" and match.groups():
                            groups = match.groups()
                            if len(groups) >= 2:
                                rule['retention_value'] = groups[0]
                                rule['retention_unit'] = groups[1]
                        
                        rules.append(rule)
        
        return rules
    
    async def _extract_llm_rules(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Extract rules using LLM."""
        if not self.openai_client:
            return []
        
        system_prompt = """You are a compliance expert analyzing policy documents.
        
Extract ALL actionable compliance rules from the provided policy text. For each rule, provide:
1. rule_type: Category (data_retention, data_access, data_encryption, data_masking, consent, audit_logging, geographic_restriction, age_restriction, notification, data_quality, security, privacy, other)
2. text: The exact text or summary of the rule
3. severity: critical, high, medium, or low
4. entities: List of database entities/fields this rule applies to (e.g., ["users.email", "transactions.amount"])
5. condition: A description of what constitutes a violation
6. sql_hint: If applicable, a hint for SQL condition to check this rule

Return as JSON array. Be thorough and extract all rules, even implicit ones."""

        user_prompt = f"""Policy Document Metadata:
{json.dumps(metadata or {}, indent=2)}

Policy Text:
{text[:15000]}  # Limit text length for API

Extract all compliance rules as JSON array."""

        try:
            response = await self.openai_client.chat.completions.create(
                model=self.llm_config.model if self.llm_config else "gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=4096,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # Handle different response structures
            rules = result.get('rules', result) if isinstance(result, dict) else result
            
            for rule in rules:
                rule['extraction_method'] = 'llm'
            
            return rules if isinstance(rules, list) else []
            
        except Exception as e:
            logger.error(f"LLM rule extraction failed: {e}")
            return []
    
    def _merge_rules(
        self,
        pattern_rules: List[Dict[str, Any]],
        llm_rules: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Merge and deduplicate rules from different sources."""
        merged = []
        seen_texts = set()
        
        # Prioritize LLM rules as they're usually more comprehensive
        for rule in llm_rules:
            text_key = rule.get('text', '')[:100].lower()
            if text_key not in seen_texts:
                merged.append(rule)
                seen_texts.add(text_key)
        
        # Add pattern rules that aren't duplicates
        for rule in pattern_rules:
            text_key = rule.get('text', '')[:100].lower()
            if text_key not in seen_texts:
                merged.append(rule)
                seen_texts.add(text_key)
        
        return merged
    
    def _determine_severity(self, text: str) -> str:
        """Determine rule severity based on keywords."""
        text_lower = text.lower()
        
        for severity, keywords in self.SEVERITY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return severity
        
        return "medium"  # Default severity
    
    def _generate_sql_condition(self, rule: Dict[str, Any]) -> Optional[str]:
        """Generate a SQL condition hint for the rule."""
        rule_type = rule.get('type', '')
        
        # Generate basic SQL conditions based on rule type
        sql_templates = {
            "data_retention": "created_at < NOW() - INTERVAL '{value} {unit}'",
            "age_restriction": "EXTRACT(YEAR FROM AGE(birthdate)) < {min_age}",
            "data_encryption": "is_encrypted = FALSE",
            "data_masking": "LENGTH(sensitive_field) > {visible_chars}"
        }
        
        if rule_type in sql_templates:
            template = sql_templates[rule_type]
            
            # Fill in values if available
            if rule_type == "data_retention":
                value = rule.get('retention_value', '90')
                unit = rule.get('retention_unit', 'days').upper()
                return template.format(value=value, unit=unit)
            
            return template
        
        return rule.get('sql_hint')
    
    async def validate_rule(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a rule's structure and completeness.
        
        Args:
            rule: Rule to validate
            
        Returns:
            Validation result with any issues
        """
        issues = []
        
        required_fields = ['type', 'text', 'severity']
        for field in required_fields:
            if not rule.get(field):
                issues.append(f"Missing required field: {field}")
        
        valid_types = list(self.RULE_PATTERNS.keys()) + ['data_quality', 'security', 'privacy', 'other']
        if rule.get('type') and rule['type'] not in valid_types:
            issues.append(f"Unknown rule type: {rule['type']}")
        
        valid_severities = ['critical', 'high', 'medium', 'low']
        if rule.get('severity') and rule['severity'] not in valid_severities:
            issues.append(f"Invalid severity: {rule['severity']}")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "rule_id": rule.get('id')
        }
