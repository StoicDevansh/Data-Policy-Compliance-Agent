"""
Report Generator - Creates compliance reports in multiple formats
"""
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path


class ReportGenerator:
    """
    Generates compliance reports in multiple formats (PDF, HTML, Excel).
    Provides data aggregation, formatting, and template-based reporting.
    """

    def __init__(self):
        """Initialize the report generator."""
        self.report_templates = self._load_report_templates()
        self.reports_dir = Path(__file__).parent.parent.parent / "data" / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.report_counter = 0

    def _load_report_templates(self) -> Dict[str, Any]:
        """Load report templates."""
        return {
            'compliance': {
                'title': 'Compliance Report',
                'sections': ['summary', 'violations', 'trends', 'recommendations']
            },
            'audit': {
                'title': 'Audit Report',
                'sections': ['executive_summary', 'findings', 'methodology', 'appendix']
            },
            'summary': {
                'title': 'Executive Summary',
                'sections': ['overview', 'key_metrics', 'risk_assessment']
            }
        }

    async def generate(
        self,
        violations: List[Dict[str, Any]],
        policies: List[Dict[str, Any]],
        rules: List[Dict[str, Any]],
        report_type: str = 'compliance',
        output_path: Optional[str] = None,
        format: str = 'html',
        include_details: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a compliance report.

        Args:
            violations: List of violations to include
            policies: List of policies to reference
            rules: List of rules to reference
            report_type: Type of report ('compliance', 'audit', 'summary')
            output_path: Optional path to save the report
            format: Output format ('pdf', 'html', 'excel')
            include_details: Whether to include detailed violation information

        Returns:
            Dictionary with report metadata and file path
        """
        report_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()

        # Determine output path
        if not output_path:
            output_path = str(
                self.reports_dir / f"compliance_report_{report_id}.{format}"
            )
        else:
            output_path = str(output_path)

        # Generate report content based on type
        if report_type == 'compliance':
            report_content = await self._generate_compliance_report(
                violations, policies, rules, include_details
            )
        elif report_type == 'audit':
            report_content = await self._generate_audit_report(
                violations, policies, rules, include_details
            )
        else:  # summary
            report_content = await self._generate_summary_report(
                violations, policies, rules, include_details
            )

        # Format and save the report
        saved_path = await self._format_and_save_report(
            report_content, output_path, format, report_type
        )

        # Update report counter
        self.report_counter += 1

        return {
            'report_id': report_id,
            'format': format,
            'path': saved_path,
            'report_type': report_type,
            'generated_at': timestamp.isoformat(),
            'violations_included': len(violations),
            'policies_referenced': len(policies),
            'rules_referenced': len(rules),
            'include_details': include_details,
            'size_bytes': self._get_file_size(saved_path) if saved_path else 0
        }

    async def _generate_compliance_report(
        self,
        violations: List[Dict[str, Any]],
        policies: List[Dict[str, Any]],
        rules: List[Dict[str, Any]],
        include_details: bool
    ) -> Dict[str, Any]:
        """Generate a detailed compliance report."""
        summary = self._generate_summary_statistics(violations, policies, rules)
        details = self._generate_detailed_violations(violations) if include_details else []
        trends = self._generate_trend_analysis(violations)
        recommendations = self._generate_recommendations(violations)

        return {
            'type': 'compliance',
            'summary': summary,
            'details': details,
            'trends': trends,
            'recommendations': recommendations,
            'policies': policies[:10] if policies else [],  # Top 10 policies
            'rules': rules[:20] if rules else []  # Top 20 rules
        }

    async def _generate_audit_report(
        self,
        violations: List[Dict[str, Any]],
        policies: List[Dict[str, Any]],
        rules: List[Dict[str, Any]],
        include_details: bool
    ) -> Dict[str, Any]:
        """Generate an audit report."""
        executive_summary = self._generate_executive_summary(violations, policies, rules)
        findings = self._generate_audit_findings(violations, include_details)
        methodology = self._generate_methodology()
        appendix = self._generate_appendix(policies, rules)

        return {
            'type': 'audit',
            'executive_summary': executive_summary,
            'findings': findings,
            'methodology': methodology,
            'appendix': appendix
        }

    async def _generate_summary_report(
        self,
        violations: List[Dict[str, Any]],
        policies: List[Dict[str, Any]],
        rules: List[Dict[str, Any]],
        include_details: bool
    ) -> Dict[str, Any]:
        """Generate an executive summary report."""
        overview = self._generate_overview(violations)
        key_metrics = self._generate_key_metrics(violations, policies, rules)
        risk_assessment = self._generate_risk_assessment(violations)

        return {
            'type': 'summary',
            'overview': overview,
            'key_metrics': key_metrics,
            'risk_assessment': risk_assessment
        }

    async def _format_and_save_report(
        self,
        content: Dict[str, Any],
        output_path: str,
        format: str,
        report_type: str
    ) -> str:
        """
        Format the report content and save to file.

        Args:
            content: Report content dictionary
            output_path: Path to save the report
            format: Output format ('pdf', 'html', 'excel')
            report_type: Type of report

        Returns:
            Path to the saved report file
        """
        if format == 'html':
            return await self._save_as_html(content, output_path, report_type)
        elif format == 'pdf':
            return await self._save_as_pdf(content, output_path, report_type)
        elif format == 'excel':
            return await self._save_as_excel(content, output_path, report_type)
        else:
            # Default to JSON
            return await self._save_as_json(content, output_path)

    async def _save_as_html(
        self,
        content: Dict[str, Any],
        output_path: str,
        report_type: str
    ) -> str:
        """Save report as HTML file."""
        template = self.report_templates.get(report_type, self.report_templates['compliance'])

        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{template['title']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background-color: #f4f4f4; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; padding: 15px; border-left: 4px solid #007bff; }}
                .violation {{ background-color: #fff8f8; border: 1px solid #ffdddd; padding: 10px; margin: 10px 0; }}
                .high {{ border-left-color: #dc3545; }}
                .medium {{ border-left-color: #ffc107; }}
                .low {{ border-left-color: #28a745; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{template['title']}</h1>
                <p>Generated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            </div>

            {self._format_html_sections(content)}

            <div class="section">
                <h2>Report Information</h2>
                <p>This report was generated by the Data Policy Agent compliance monitoring system.</p>
                <p>For questions, contact your compliance team.</p>
            </div>
        </body>
        </html>
        """

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return output_path

    async def _save_as_json(
        self,
        content: Dict[str, Any],
        output_path: str
    ) -> str:
        """Save report as JSON file."""
        import json

        report_data = {
            'report_metadata': {
                'generated_at': datetime.utcnow().isoformat(),
                'report_type': content.get('type', 'unknown'),
                'version': '1.0'
            },
            'content': content
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=str)

        return output_path

    async def _save_as_pdf(
        self,
        content: Dict[str, Any],
        output_path: str,
        report_type: str
    ) -> str:
        """Save report as PDF file (placeholder implementation)."""
        # In a real implementation, we would use reportlab or weasyprint
        # For now, save as JSON with .pdf extension to indicate the format
        return await self._save_as_json(content, output_path.replace('.pdf', '.json'))

    async def _save_as_excel(
        self,
        content: Dict[str, Any],
        output_path: str,
        report_type: str
    ) -> str:
        """Save report as Excel file (placeholder implementation)."""
        # In a real implementation, we would use openpyxl or pandas
        # For now, save as JSON with .xlsx extension to indicate the format
        return await self._save_as_json(content, output_path.replace('.xlsx', '.json'))

    def _format_html_sections(self, content: Dict[str, Any]) -> str:
        """Format report content as HTML sections."""
        sections_html = ""

        # Add each section from the content
        for key, value in content.items():
            if key in ['summary', 'details', 'trends', 'recommendations', 'policies', 'rules',
                      'executive_summary', 'findings', 'methodology', 'appendix',
                      'overview', 'key_metrics', 'risk_assessment']:
                sections_html += f"""
                <div class="section">
                    <h2>{key.replace('_', ' ').title()}</h2>
                    {self._format_section_content(value)}
                </div>
                """

        return sections_html

    def _format_section_content(self, content: Any) -> str:
        """Format section content for HTML display."""
        if isinstance(content, dict):
            html = "<ul>"
            for k, v in content.items():
                html += f"<li><strong>{k}:</strong> {v}</li>"
            html += "</ul>"
            return html
        elif isinstance(content, list):
            if not content:
                return "<p>No data available.</p>"
            html = "<ul>"
            for item in content:
                if isinstance(item, dict):
                    html += f"<li><strong>{item.get('title', 'Item')}:</strong> {item.get('description', str(item))}</li>"
                else:
                    html += f"<li>{item}</li>"
            html += "</ul>"
            return html
        else:
            return f"<p>{content}</p>"

    def _generate_summary_statistics(
        self,
        violations: List[Dict[str, Any]],
        policies: List[Dict[str, Any]],
        rules: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate summary statistics for the report."""
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for violation in violations:
            severity = violation.get('severity', 'medium').lower()
            if severity in severity_counts:
                severity_counts[severity] += 1

        return {
            'total_violations': len(violations),
            'total_policies': len(policies),
            'total_rules': len(rules),
            'violations_by_severity': severity_counts,
            'generated_at': datetime.utcnow().isoformat()
        }

    def _generate_detailed_violations(
        self,
        violations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate detailed violation information for the report."""
        detailed = []
        for violation in violations[:50]:  # Limit to top 50 for readability
            detailed.append({
                'id': violation.get('id'),
                'type': violation.get('type'),
                'severity': violation.get('severity'),
                'description': violation.get('rule_text', 'No description available'),
                'table': violation.get('table'),
                'column': violation.get('column'),
                'violation_count': violation.get('violation_count', 1),
                'risk_score': violation.get('risk_score', 0),
                'detected_at': violation.get('detected_at'),
                'status': violation.get('status', 'open')
            })

        return detailed

    def _generate_trend_analysis(
        self,
        violations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate trend analysis for the report."""
        # Placeholder for trend analysis - in reality, we would compare with historical data
        return {
            'trend_period': 'Last 24 hours',
            'violations_change': '+5%',  # Placeholder
            'severity_trends': {
                'critical': 'stable',
                'high': 'increasing',
                'medium': 'decreasing',
                'low': 'stable'
            },
            'top_violation_types': [
                {'type': 'data_encryption', 'count': 12},
                {'type': 'access_control', 'count': 8},
                {'type': 'data_retention', 'count': 5}
            ]
        }

    def _generate_recommendations(
        self,
        violations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate remediation recommendations."""
        # Generate recommendations based on violation types found
        violation_types = set(v.get('type') for v in violations)

        recommendations = []
        for vtype in violation_types:
            recommendations.append({
                'violation_type': vtype,
                'priority': 'high' if vtype in ['data_encryption', 'consent', 'age_restriction'] else 'medium',
                'recommendation': f"Address {vtype.replace('_', ' ')} violations through policy updates and technical controls",
                'estimated_effort': 'medium',
                'timeline': '30-60 days'
            })

        return recommendations

    def _generate_executive_summary(
        self,
        violations: List[Dict[str, Any]],
        policies: List[Dict[str, Any]],
        rules: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate executive summary for audit report."""
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for violation in violations:
            severity = violation.get('severity', 'medium').lower()
            if severity in severity_counts:
                severity_counts[severity] += 1

        return {
            'total_violations': len(violations),
            'critical_findings': severity_counts['critical'],
            'high_findings': severity_counts['high'],
            'compliance_score': max(0, 100 - (len(violations) * 2)),  # Simplified scoring
            'assessment_period': 'Last scan cycle',
            'overall_risk': 'High' if severity_counts['critical'] > 0 else 'Medium' if severity_counts['high'] > 5 else 'Low'
        }

    def _generate_audit_findings(
        self,
        violations: List[Dict[str, Any]],
        include_details: bool
    ) -> List[Dict[str, Any]]:
        """Generate audit findings section."""
        findings = []
        for violation in violations[:20]:  # Limit for audit report
            findings.append({
                'finding_id': str(uuid.uuid4()),
                'violation_type': violation.get('type'),
                'severity': violation.get('severity'),
                'description': violation.get('rule_text', ''),
                'location': f"{violation.get('table', 'unknown')}.{violation.get('column', 'unknown')}",
                'impact': self._get_impact_description(violation),
                'recommendation': self._get_recommendation_for_violation(violation),
                'evidence': f"Found {violation.get('violation_count', 1)} instances"
            })

        return findings

    def _generate_methodology(self) -> Dict[str, Any]:
        """Generate methodology section."""
        return {
            'scan_approach': 'Automated compliance scanning using policy rules',
            'data_sources': 'Connected databases and policy documents',
            'tools_used': ['Data Policy Agent', 'Database Scanner', 'Violation Engine'],
            'limitations': ['Scan coverage limited to connected databases', 'Rule-based detection may miss novel violations']
        }

    def _generate_appendix(
        self,
        policies: List[Dict[str, Any]],
        rules: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate appendix section."""
        return {
            'policies_reviewed': [
                {'id': p.get('id'), 'name': p.get('name', 'Unknown Policy')}
                for p in policies[:10]
            ],
            'rules_applied': [
                {'id': r.get('id'), 'type': r.get('type'), 'description': r.get('text', '')[:100]}
                for r in rules[:20]
            ],
            'generated_by': 'Data Policy Agent v1.0',
            'generated_at': datetime.utcnow().isoformat()
        }

    def _generate_overview(
        self,
        violations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate overview section."""
        return {
            'purpose': 'Compliance monitoring and violation detection',
            'scope': 'Database systems and policy documents',
            'findings_summary': f"Found {len(violations)} potential compliance violations",
            'data_sources_scanned': 'All connected database systems'
        }

    def _generate_key_metrics(
        self,
        violations: List[Dict[str, Any]],
        policies: List[Dict[str, Any]],
        rules: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate key metrics section."""
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for violation in violations:
            severity = violation.get('severity', 'medium').lower()
            if severity in severity_counts:
                severity_counts[severity] += 1

        return {
            'total_violations_detected': len(violations),
            'compliance_violation_rate': f"{len(violations)/max(len(policies), 1)*100:.1f}%",
            'average_risk_score': sum(v.get('risk_score', 0) for v in violations) / max(len(violations), 1),
            'policies_in_scope': len(policies),
            'rules_engaged': len(rules)
        }

    def _generate_risk_assessment(
        self,
        violations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate risk assessment section."""
        high_risk = sum(1 for v in violations if v.get('severity') in ['critical', 'high'])
        risk_level = 'Critical' if high_risk > 5 else 'High' if high_risk > 2 else 'Medium' if high_risk > 0 else 'Low'

        return {
            'overall_risk_level': risk_level,
            'high_risk_findings': high_risk,
            'risk_trend': 'Stable',  # Placeholder
            'recommended_actions': [
                'Address critical and high severity violations immediately',
                'Implement preventive controls for recurring violation types',
                'Schedule regular compliance scans'
            ]
        }

    def _get_impact_description(self, violation: Dict[str, Any]) -> str:
        """Get impact description for a violation."""
        impact_map = {
            'data_encryption': 'Risk of data breach and unauthorized access to sensitive information',
            'data_retention': 'Increased storage costs and regulatory non-compliance with data retention laws',
            'data_access': 'Potential for unauthorized data access and privilege escalation',
            'consent': 'Violation of privacy regulations and potential fines',
            'audit_logging': 'Inability to investigate security incidents and compliance issues',
            'age_restriction': 'Violation of children\\'s privacy laws and regulations',
            'geographic_restriction': 'Violation of data sovereignty laws and international transfer restrictions',
            'notification': 'Failure to notify affected parties of data breaches as required by law'
        }
        return impact_map.get(violation.get('type'), 'Potential compliance violation requiring investigation')

    def _get_recommendation_for_violation(self, violation: Dict[str, Any]) -> str:
        """Get recommendation for a specific violation type."""
        recommendation_map = {
            'data_encryption': 'Encrypt sensitive data at rest and in transit using industry-standard algorithms',
            'data_retention': 'Implement automated data retention and deletion policies based on regulatory requirements',
            'data_access': 'Implement role-based access control and principle of least privilege',
            'consent': 'Establish proper consent management systems with audit trails',
            'audit_logging': 'Implement comprehensive logging of all system access and modifications',
            'age_restriction': 'Implement age verification mechanisms and restrict data processing for minors',
            'geographic_restriction': 'Apply geographic access controls and data localization where required',
            'notification': 'Implement breach detection and automated notification systems'
        }
        return recommendation_map.get(violation.get('type'), 'Investigate and remediate according to compliance requirements')

    def _get_file_size(self, file_path: str) -> int:
        """Get the size of a file in bytes."""
        try:
            return Path(file_path).stat().st_size
        except:
            return 0

    async def generate_dashboard_data(
        self,
        violations: List[Dict[str, Any]],
        policies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate data for dashboard display.

        Args:
            violations: List of current violations
            policies: List of current policies

        Returns:
            Dictionary with dashboard data
        """
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for violation in violations:
            severity = violation.get('severity', 'medium').lower()
            if severity in severity_counts:
                severity_counts[severity] += 1

        return {
            'timestamp': datetime.utcnow().isoformat(),
            'total_violations': len(violations),
            'violations_by_severity': severity_counts,
            'total_policies': len(policies),
            'recent_violations': [
                {
                    'id': v.get('id'),
                    'type': v.get('type'),
                    'severity': v.get('severity'),
                    'detected_at': v.get('detected_at')
                }
                for v in sorted(violations, key=lambda x: x.get('detected_at', ''), reverse=True)[:10]
            ],
            'compliance_trend': 'stable',  # Placeholder
            'top_risk_areas': [
                {'area': 'data_encryption', 'count': sum(1 for v in violations if v.get('type') == 'data_encryption')},
                {'area': 'access_control', 'count': sum(1 for v in violations if v.get('type') == 'data_access')},
                {'area': 'data_retention', 'count': sum(1 for v in violations if v.get('type') == 'data_retention')}
            ]
        }