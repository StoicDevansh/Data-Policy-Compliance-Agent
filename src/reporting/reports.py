"""
Report Generator - Generates compliance reports in various formats.
"""
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from loguru import logger


class ReportGenerator:
    """
    Generates compliance reports in multiple formats (PDF, HTML, JSON, Excel).
    """
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize report generator.
        
        Args:
            output_dir: Directory for saving reports
        """
        self.output_dir = output_dir or Path(__file__).parent.parent.parent / "data" / "reports"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate(
        self,
        violations: List[Dict[str, Any]],
        policies: List[Dict[str, Any]] = None,
        format: str = "json",
        output_path: Optional[str] = None,
        include_details: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a compliance report.
        
        Args:
            violations: List of violations to include
            policies: List of policies (optional)
            format: Output format (json, html, pdf)
            output_path: Custom output path
            include_details: Include detailed violation info
            
        Returns:
            Report metadata including path
        """
        logger.info(f"Generating {format} report with {len(violations)} violations")
        
        report_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        report_data = {
            "report_id": report_id,
            "generated_at": datetime.utcnow().isoformat(),
            "summary": self._generate_summary(violations),
            "violations": violations if include_details else [],
            "policies": policies or [],
            "compliance_score": self._calculate_compliance_score(violations)
        }
        
        if format == "json":
            output = await self._generate_json(report_data, output_path, report_id)
        elif format == "html":
            output = await self._generate_html(report_data, output_path, report_id)
        else:
            output = await self._generate_json(report_data, output_path, report_id)
        
        logger.info(f"Report generated: {output['path']}")
        return output
    
    def _generate_summary(self, violations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate violation summary statistics."""
        if not violations:
            return {
                "total_violations": 0,
                "by_severity": {},
                "by_type": {},
                "by_table": {}
            }
        
        by_severity = {}
        by_type = {}
        by_table = {}
        
        for v in violations:
            # Count by severity
            severity = v.get("severity", "unknown")
            by_severity[severity] = by_severity.get(severity, 0) + 1
            
            # Count by type
            vtype = v.get("rule_type", "unknown")
            by_type[vtype] = by_type.get(vtype, 0) + 1
            
            # Count by table
            table = v.get("table", "unknown")
            by_table[table] = by_table.get(table, 0) + 1
        
        return {
            "total_violations": len(violations),
            "by_severity": by_severity,
            "by_type": by_type,
            "by_table": by_table
        }
    
    def _calculate_compliance_score(self, violations: List[Dict[str, Any]]) -> float:
        """Calculate an overall compliance score (0-100)."""
        if not violations:
            return 100.0
        
        # Weight violations by severity
        severity_weights = {
            "critical": 10,
            "high": 5,
            "medium": 2,
            "low": 1
        }
        
        total_weight = sum(
            severity_weights.get(v.get("severity", "low"), 1)
            for v in violations
        )
        
        # Score decreases with more/worse violations
        # Max deduction is capped at 100
        deduction = min(total_weight, 100)
        
        return max(0, 100 - deduction)
    
    async def _generate_json(
        self,
        report_data: Dict[str, Any],
        output_path: Optional[str],
        report_id: str
    ) -> Dict[str, Any]:
        """Generate JSON report."""
        filename = output_path or f"compliance_report_{report_id}.json"
        if not Path(filename).is_absolute():
            filepath = self.output_dir / filename
        else:
            filepath = Path(filename)
        
        with open(filepath, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        return {
            "format": "json",
            "path": str(filepath),
            "report_id": report_id
        }
    
    async def _generate_html(
        self,
        report_data: Dict[str, Any],
        output_path: Optional[str],
        report_id: str
    ) -> Dict[str, Any]:
        """Generate HTML report."""
        filename = output_path or f"compliance_report_{report_id}.html"
        if not Path(filename).is_absolute():
            filepath = self.output_dir / filename
        else:
            filepath = Path(filename)
        
        html_content = self._render_html_template(report_data)
        
        with open(filepath, 'w') as f:
            f.write(html_content)
        
        return {
            "format": "html",
            "path": str(filepath),
            "report_id": report_id
        }
    
    def _render_html_template(self, report_data: Dict[str, Any]) -> str:
        """Render HTML template for report."""
        summary = report_data.get("summary", {})
        score = report_data.get("compliance_score", 100)
        
        # Determine score color
        if score >= 80:
            score_color = "#22c55e"  # green
        elif score >= 60:
            score_color = "#eab308"  # yellow
        else:
            score_color = "#ef4444"  # red
        
        violations_html = ""
        for v in report_data.get("violations", []):
            severity_class = v.get("severity", "low")
            violations_html += f"""
            <tr class="violation-row {severity_class}">
                <td>{v.get('id', 'N/A')[:8]}</td>
                <td><span class="severity {severity_class}">{severity_class.upper()}</span></td>
                <td>{v.get('table', 'N/A')}</td>
                <td>{v.get('rule_type', 'N/A')}</td>
                <td>{v.get('explanation', v.get('details', 'N/A'))[:100]}...</td>
            </tr>
            """
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Compliance Report - {report_data['report_id']}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f1f5f9; color: #1e293b; line-height: 1.6; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem; }}
        .header {{ background: linear-gradient(135deg, #1e40af, #3b82f6); color: white; padding: 2rem; border-radius: 12px; margin-bottom: 2rem; }}
        .header h1 {{ font-size: 2rem; margin-bottom: 0.5rem; }}
        .header .meta {{ opacity: 0.9; font-size: 0.9rem; }}
        .score-card {{ background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 2rem; text-align: center; }}
        .score {{ font-size: 4rem; font-weight: bold; color: {score_color}; }}
        .score-label {{ color: #64748b; font-size: 1.1rem; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
        .stat-card {{ background: white; padding: 1.5rem; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .stat-value {{ font-size: 2rem; font-weight: bold; color: #1e40af; }}
        .stat-label {{ color: #64748b; font-size: 0.9rem; }}
        .violations-table {{ background: white; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); overflow: hidden; }}
        .violations-table h2 {{ padding: 1.5rem; border-bottom: 1px solid #e2e8f0; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ background: #f8fafc; padding: 1rem; text-align: left; font-weight: 600; color: #475569; }}
        td {{ padding: 1rem; border-bottom: 1px solid #e2e8f0; }}
        .severity {{ padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; }}
        .severity.critical {{ background: #fee2e2; color: #dc2626; }}
        .severity.high {{ background: #ffedd5; color: #ea580c; }}
        .severity.medium {{ background: #fef9c3; color: #ca8a04; }}
        .severity.low {{ background: #dcfce7; color: #16a34a; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Compliance Report</h1>
            <div class="meta">Report ID: {report_data['report_id']} | Generated: {report_data['generated_at']}</div>
        </div>
        
        <div class="score-card">
            <div class="score">{score:.0f}</div>
            <div class="score-label">Compliance Score</div>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{summary.get('total_violations', 0)}</div>
                <div class="stat-label">Total Violations</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary.get('by_severity', {}).get('critical', 0)}</div>
                <div class="stat-label">Critical Issues</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary.get('by_severity', {}).get('high', 0)}</div>
                <div class="stat-label">High Priority</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(summary.get('by_table', {}))}</div>
                <div class="stat-label">Tables Affected</div>
            </div>
        </div>
        
        <div class="violations-table">
            <h2>🚨 Violations Detail</h2>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Severity</th>
                        <th>Table</th>
                        <th>Type</th>
                        <th>Description</th>
                    </tr>
                </thead>
                <tbody>
                    {violations_html if violations_html else '<tr><td colspan="5" style="text-align:center;color:#64748b;">No violations found</td></tr>'}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
        """
        return html
    
    async def generate_dashboard_data(
        self,
        violations: List[Dict[str, Any]],
        policies: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate data for the dashboard API."""
        summary = self._generate_summary(violations)
        
        return {
            "compliance_score": self._calculate_compliance_score(violations),
            "total_violations": summary["total_violations"],
            "violations_by_severity": summary["by_severity"],
            "violations_by_type": summary["by_type"],
            "violations_by_table": summary["by_table"],
            "policies_count": len(policies) if policies else 0,
            "recent_violations": violations[:10] if violations else []
        }
