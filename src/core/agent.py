"""
Data Policy Agent - Main Agent Orchestrator
Coordinates all components for policy ingestion, violation detection, and monitoring.
"""
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import uuid
from loguru import logger

from .config import get_settings, Settings
from ..ingestion.pdf_parser import PDFParser
from ..ingestion.rule_extractor import RuleExtractor
from ..database.connector import DatabaseConnector
from ..database.scanner import DatabaseScanner
from ..detection.violation_engine import ViolationEngine
from ..detection.explainer import ViolationExplainer
from ..review.workflow import ReviewWorkflow
from ..monitoring.scheduler import MonitoringScheduler
from ..reporting.reports import ReportGenerator


class DataPolicyAgent:
    """
    Main orchestrator for the Data Policy Agent.
    Coordinates policy ingestion, database scanning, violation detection,
    human review, and periodic monitoring.
    """
    
    def __init__(self, settings: Optional[Settings] = None):
        """Initialize the Data Policy Agent with all components."""
        self.settings = settings or get_settings()
        self.session_id = str(uuid.uuid4())
        
        logger.info(f"Initializing Data Policy Agent - Session: {self.session_id}")
        
        # Initialize components
        self.pdf_parser = PDFParser()
        self.rule_extractor = RuleExtractor(self.settings.llm)
        self.db_connector: Optional[DatabaseConnector] = None
        self.db_scanner: Optional[DatabaseScanner] = None
        self.violation_engine = ViolationEngine()
        self.explainer = ViolationExplainer(self.settings.llm)
        self.review_workflow = ReviewWorkflow()
        self.scheduler: Optional[MonitoringScheduler] = None
        self.report_generator = ReportGenerator()
        
        # State
        self.policies: List[Dict[str, Any]] = []
        self.rules: List[Dict[str, Any]] = []
        self.violations: List[Dict[str, Any]] = []
        self.connected_databases: List[Dict[str, Any]] = []
        
        logger.info("Data Policy Agent initialized successfully")
    
    async def ingest_policy(self, pdf_path: str, policy_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Ingest a PDF policy document and extract compliance rules.
        
        Args:
            pdf_path: Path to the PDF policy document
            policy_name: Optional name for the policy
            
        Returns:
            Dictionary containing policy metadata and extracted rules
        """
        logger.info(f"Ingesting policy document: {pdf_path}")
        
        # Parse PDF
        pdf_content = await self.pdf_parser.parse(pdf_path)
        
        # Extract rules using NLP/LLM
        extracted_rules = await self.rule_extractor.extract_rules(
            pdf_content['text'],
            pdf_content.get('metadata', {})
        )
        
        # Create policy record
        policy = {
            "id": str(uuid.uuid4()),
            "name": policy_name or Path(pdf_path).stem,
            "source_path": pdf_path,
            "ingested_at": datetime.utcnow().isoformat(),
            "content_hash": pdf_content.get('hash'),
            "page_count": pdf_content.get('page_count', 0),
            "rules_count": len(extracted_rules),
            "status": "active"
        }
        
        # Store policy and rules
        self.policies.append(policy)
        for rule in extracted_rules:
            rule['policy_id'] = policy['id']
            self.rules.append(rule)
        
        logger.info(f"Successfully extracted {len(extracted_rules)} rules from {policy_name}")
        
        return {
            "policy": policy,
            "rules": extracted_rules
        }
    
    async def connect_database(self, config: Dict[str, Any]) -> bool:
        """
        Connect to a company database for compliance scanning.
        
        Args:
            config: Database connection configuration
            
        Returns:
            True if connection successful
        """
        logger.info(f"Connecting to database: {config.get('type', 'unknown')}")
        
        self.db_connector = DatabaseConnector(config)
        connected = await self.db_connector.connect()
        
        if connected:
            self.db_scanner = DatabaseScanner(self.db_connector)
            self.connected_databases.append({
                "type": config.get('type'),
                "host": config.get('host'),
                "database": config.get('database') or config.get('name'),
                "connected_at": datetime.utcnow().isoformat()
            })
            logger.info("Database connection established successfully")
        else:
            logger.error("Failed to connect to database")
            
        return connected
    
    async def scan_for_violations(
        self,
        tables: Optional[List[str]] = None,
        rules: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Scan the connected database for policy violations.
        
        Args:
            tables: Specific tables to scan (None for all)
            rules: Specific rule IDs to check (None for all)
            limit: Maximum number of violations to return
            
        Returns:
            List of detected violations with explanations
        """
        if not self.db_scanner:
            raise RuntimeError("No database connected. Call connect_database first.")
        
        logger.info("Starting compliance scan...")
        
        # Get rules to check
        rules_to_check = self.rules
        if rules:
            rules_to_check = [r for r in self.rules if r['id'] in rules]
        
        # Scan database
        scan_results = await self.db_scanner.scan(
            rules=rules_to_check,
            tables=tables
        )
        
        # Detect violations
        violations = await self.violation_engine.detect(
            scan_results=scan_results,
            rules=rules_to_check
        )
        
        # Generate explanations
        for violation in violations:
            explanation = await self.explainer.explain(violation)
            violation['explanation'] = explanation
            violation['remediation'] = await self.explainer.suggest_remediation(violation)
        
        # Apply limit if specified
        if limit:
            violations = violations[:limit]
        
        # Store violations
        self.violations.extend(violations)
        
        logger.info(f"Scan complete. Found {len(violations)} violations.")
        
        return violations
    
    async def submit_for_review(
        self,
        violation_ids: List[str],
        reviewers: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Submit violations for human review.
        
        Args:
            violation_ids: IDs of violations to review
            reviewers: Optional list of reviewer emails/IDs
            
        Returns:
            Review workflow status
        """
        violations_to_review = [
            v for v in self.violations if v['id'] in violation_ids
        ]
        
        review_task = await self.review_workflow.create_review(
            violations=violations_to_review,
            reviewers=reviewers
        )
        
        logger.info(f"Created review task {review_task['id']} for {len(violations_to_review)} violations")
        
        return review_task
    
    async def process_review_decision(
        self,
        review_id: str,
        decision: str,
        comments: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a human review decision.
        
        Args:
            review_id: ID of the review task
            decision: 'approve', 'reject', or 'escalate'
            comments: Optional reviewer comments
            
        Returns:
            Updated review status
        """
        result = await self.review_workflow.process_decision(
            review_id=review_id,
            decision=decision,
            comments=comments
        )
        
        # Update violation status based on decision
        if result.get('violations'):
            for v_id in result['violations']:
                for v in self.violations:
                    if v['id'] == v_id:
                        v['review_status'] = decision
                        v['reviewed_at'] = datetime.utcnow().isoformat()
        
        return result
    
    async def start_monitoring(
        self,
        interval_seconds: Optional[int] = None,
        callback: Optional[callable] = None
    ):
        """
        Start periodic monitoring for compliance violations.
        
        Args:
            interval_seconds: Check interval (defaults to settings)
            callback: Optional callback function for new violations
        """
        interval = interval_seconds or self.settings.monitoring.interval_seconds
        
        self.scheduler = MonitoringScheduler(
            agent=self,
            interval_seconds=interval,
            callback=callback
        )
        
        await self.scheduler.start()
        logger.info(f"Started periodic monitoring (interval: {interval}s)")
    
    async def stop_monitoring(self):
        """Stop periodic monitoring."""
        if self.scheduler:
            await self.scheduler.stop()
            logger.info("Stopped periodic monitoring")
    
    async def generate_report(
        self,
        violations: Optional[List[Dict[str, Any]]] = None,
        report_type: str = "compliance",
        output_path: Optional[str] = None,
        format: str = "pdf"
    ) -> str:
        """
        Generate a compliance report.
        
        Args:
            violations: Violations to include (defaults to all)
            report_type: Type of report ('compliance', 'audit', 'summary')
            output_path: Output file path
            format: Output format ('pdf', 'html', 'excel')
            
        Returns:
            Path to generated report
        """
        violations_to_report = violations or self.violations
        
        report_path = await self.report_generator.generate(
            violations=violations_to_report,
            policies=self.policies,
            rules=self.rules,
            report_type=report_type,
            output_path=output_path,
            format=format
        )
        
        logger.info(f"Generated {report_type} report: {report_path}")
        
        return report_path
    
    def get_compliance_status(self) -> Dict[str, Any]:
        """
        Get current compliance status summary.
        
        Returns:
            Dictionary with compliance metrics and trends
        """
        total_violations = len(self.violations)
        critical = len([v for v in self.violations if v.get('severity') == 'critical'])
        high = len([v for v in self.violations if v.get('severity') == 'high'])
        medium = len([v for v in self.violations if v.get('severity') == 'medium'])
        low = len([v for v in self.violations if v.get('severity') == 'low'])
        
        reviewed = len([v for v in self.violations if v.get('review_status')])
        pending_review = total_violations - reviewed
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_policies": len(self.policies),
            "total_rules": len(self.rules),
            "total_violations": total_violations,
            "violations_by_severity": {
                "critical": critical,
                "high": high,
                "medium": medium,
                "low": low
            },
            "review_status": {
                "reviewed": reviewed,
                "pending": pending_review
            },
            "connected_databases": len(self.connected_databases),
            "monitoring_active": self.scheduler is not None and self.scheduler.is_running
        }
    
    async def close(self):
        """Clean up resources and close connections."""
        logger.info("Shutting down Data Policy Agent...")
        
        if self.scheduler:
            await self.stop_monitoring()
        
        if self.db_connector:
            await self.db_connector.close()
        
        logger.info("Data Policy Agent shutdown complete")
