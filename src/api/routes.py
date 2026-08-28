"""
API Routes - FastAPI REST endpoints for Data Policy Agent.
"""
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from pydantic import BaseModel, Field
from loguru import logger

# Import agent and modules
from ..core.agent import DataPolicyAgent
from ..core.config import get_settings
from ..datasets.sample_data import create_demo_database
from ..datasets.loader import DatasetLoader, AMLDatasetAnalyzer, PaySimAnalyzer


# Pydantic Models for request/response
class DatabaseConfig(BaseModel):
    type: str = Field(default="sqlite", description="Database type")
    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    name: str = Field(default="database.db", description="Database name or path")
    user: Optional[str] = None
    password: Optional[str] = None


class ScanRequest(BaseModel):
    tables: Optional[List[str]] = None
    rules: Optional[List[str]] = None
    limit: Optional[int] = None


class ReviewRequest(BaseModel):
    violation_ids: List[str]
    decision: str = Field(..., description="approve, reject, or escalate")
    reviewer: str
    comments: Optional[str] = None


class ReportRequest(BaseModel):
    format: str = Field(default="html", description="json, html, or pdf")
    include_details: bool = True


# Create router
router = APIRouter(prefix="/api", tags=["compliance"])

# Global agent instance (will be initialized on startup)
_agent: Optional[DataPolicyAgent] = None
_demo_db_path: Optional[str] = None


def get_agent() -> DataPolicyAgent:
    """Get or create the agent instance."""
    global _agent
    if _agent is None:
        _agent = DataPolicyAgent()
    return _agent


@router.get("/")
async def root():
    """API root endpoint."""
    return {
        "name": "Data Policy Agent API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


# ============== Database Endpoints ==============

@router.post("/database/connect")
async def connect_database(config: DatabaseConfig):
    """Connect to a database for compliance scanning."""
    agent = get_agent()
    
    try:
        connected = await agent.connect_database(config.model_dump())
        
        if connected:
            return {
                "success": True,
                "message": f"Connected to {config.type} database",
                "database": config.name
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to connect to database")
            
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/database/demo")
async def setup_demo_database():
    """Set up demo database with HackFest 2.0 sample data."""
    global _demo_db_path
    agent = get_agent()
    
    try:
        # Generate demo data
        logger.info("Creating demo database...")
        results = create_demo_database()
        _demo_db_path = results['database_path']
        
        # Connect to the demo database
        connected = await agent.connect_database({
            "type": "sqlite",
            "name": _demo_db_path
        })
        
        if connected:
            # Load pre-configured rules
            rules_path = Path(__file__).parent.parent.parent / "data" / "rules" / "compliance_rules.json"
            if rules_path.exists():
                with open(rules_path) as f:
                    rules_config = json.load(f)
                
                # Add rules to agent
                for ruleset in rules_config['rule_sets'].values():
                    for rule in ruleset['rules']:
                        agent.rules.append(rule)
            
            return {
                "success": True,
                "message": "Demo database created and connected",
                "database_path": _demo_db_path,
                "tables": ["aml_transactions", "paysim_transactions", "employee_compliance"],
                "rules_loaded": len(agent.rules)
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to connect to demo database")
            
    except Exception as e:
        logger.error(f"Demo setup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/database/tables")
async def list_tables():
    """List tables in connected database."""
    agent = get_agent()
    
    if not agent.db_connector:
        raise HTTPException(status_code=400, detail="No database connected")
    
    try:
        tables = await agent.db_connector.get_tables()
        return {"tables": tables}
    except Exception as e:
        logger.error(f"Error listing tables: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/database/schema/{table}")
async def get_table_schema(table: str):
    """Get schema for a specific table."""
    agent = get_agent()
    
    if not agent.db_connector:
        raise HTTPException(status_code=400, detail="No database connected")
    
    try:
        schema = await agent.db_connector.get_schema(table)
        return {"table": table, "schema": schema}
    except Exception as e:
        logger.error(f"Error getting schema: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============== Policy Endpoints ==============

@router.post("/policies")
async def upload_policy(file: UploadFile = File(...)):
    """Upload a policy document (PDF or Markdown)."""
    agent = get_agent()
    
    # Save uploaded file
    upload_dir = Path(__file__).parent.parent.parent / "data" / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / file.filename
    
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Process policy
        result = await agent.ingest_policy(str(file_path))
        
        return {
            "success": True,
            "policy": result["policy"],
            "rules_extracted": len(result.get("rules", []))
        }
        
    except Exception as e:
        logger.error(f"Policy upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/policies")
async def list_policies():
    """List all ingested policies."""
    agent = get_agent()
    return {"policies": agent.policies, "count": len(agent.policies)}


@router.get("/rules")
async def list_rules():
    """List all extracted compliance rules."""
    agent = get_agent()
    return {"rules": agent.rules, "count": len(agent.rules)}


@router.post("/rules/load")
async def load_rules_from_file(ruleset: Optional[str] = None):
    """Load pre-configured rules from compliance_rules.json."""
    agent = get_agent()
    
    rules_path = Path(__file__).parent.parent.parent / "data" / "rules" / "compliance_rules.json"
    
    if not rules_path.exists():
        raise HTTPException(status_code=404, detail="Rules file not found")
    
    try:
        with open(rules_path) as f:
            rules_config = json.load(f)
        
        loaded_count = 0
        for key, rs in rules_config['rule_sets'].items():
            if ruleset is None or key == ruleset:
                for rule in rs['rules']:
                    rule['ruleset'] = key
                    agent.rules.append(rule)
                    loaded_count += 1
        
        return {
            "success": True,
            "rules_loaded": loaded_count,
            "total_rules": len(agent.rules)
        }
        
    except Exception as e:
        logger.error(f"Error loading rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============== Scan & Violations Endpoints ==============

@router.post("/scan")
async def run_compliance_scan(request: ScanRequest):
    """Run a compliance scan on the connected database."""
    agent = get_agent()
    
    if not agent.db_connector:
        raise HTTPException(status_code=400, detail="No database connected. Use /database/demo or /database/connect first.")
    
    if not agent.rules:
        raise HTTPException(status_code=400, detail="No rules loaded. Use /rules/load first.")
    
    try:
        violations = await agent.scan_for_violations(
            tables=request.tables,
            rules=request.rules,
            limit=request.limit
        )
        
        return {
            "success": True,
            "violations_found": len(violations),
            "violations": violations
        }
        
    except Exception as e:
        logger.error(f"Scan error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/violations")
async def list_violations(
    severity: Optional[str] = None,
    table: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(default=100, le=1000)
):
    """List detected violations with optional filters."""
    agent = get_agent()
    
    violations = agent.violations
    
    # Apply filters
    if severity:
        violations = [v for v in violations if v.get("severity") == severity]
    if table:
        violations = [v for v in violations if v.get("table") == table]
    if status:
        violations = [v for v in violations if v.get("status") == status]
    
    return {
        "violations": violations[:limit],
        "total": len(violations),
        "filtered": len(agent.violations)
    }


@router.get("/violations/{violation_id}")
async def get_violation(violation_id: str):
    """Get details of a specific violation."""
    agent = get_agent()
    
    violation = next(
        (v for v in agent.violations if v.get("id") == violation_id),
        None
    )
    
    if not violation:
        raise HTTPException(status_code=404, detail="Violation not found")
    
    return violation


@router.post("/violations/{violation_id}/review")
async def review_violation(violation_id: str, request: ReviewRequest):
    """Submit a review decision for a violation."""
    agent = get_agent()
    
    violation = next(
        (v for v in agent.violations if v.get("id") == violation_id),
        None
    )
    
    if not violation:
        raise HTTPException(status_code=404, detail="Violation not found")
    
    # Update violation status
    violation["status"] = request.decision
    violation["reviewed_by"] = request.reviewer
    violation["reviewed_at"] = datetime.utcnow().isoformat()
    violation["review_comments"] = request.comments
    
    return {
        "success": True,
        "violation_id": violation_id,
        "new_status": request.decision
    }


# ============== Reports & Dashboard ==============

@router.post("/reports")
async def generate_report(request: ReportRequest):
    """Generate a compliance report."""
    agent = get_agent()
    
    try:
        report = await agent.report_generator.generate(
            violations=agent.violations,
            policies=agent.policies,
            format=request.format,
            include_details=request.include_details
        )
        
        return {
            "success": True,
            "report_id": report["report_id"],
            "format": report["format"],
            "path": report["path"]
        }
        
    except Exception as e:
        logger.error(f"Report generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/{report_id}")
async def download_report(report_id: str):
    """Download a generated report."""
    reports_dir = Path(__file__).parent.parent.parent / "data" / "reports"
    
    # Look for report files
    for ext in ['json', 'html', 'pdf']:
        report_path = reports_dir / f"compliance_report_{report_id}.{ext}"
        if report_path.exists():
            return FileResponse(
                path=str(report_path),
                filename=report_path.name,
                media_type="application/octet-stream"
            )
    
    raise HTTPException(status_code=404, detail="Report not found")


@router.get("/dashboard")
async def get_dashboard_data():
    """Get dashboard summary data."""
    agent = get_agent()
    
    data = await agent.report_generator.generate_dashboard_data(
        violations=agent.violations,
        policies=agent.policies
    )
    
    data["connected_databases"] = agent.connected_databases
    data["rules_count"] = len(agent.rules)
    
    return data


# ============== Dataset Analysis ==============

@router.get("/datasets")
async def list_available_datasets():
    """List HackFest 2.0 recommended datasets."""
    loader = DatasetLoader()
    datasets = loader.list_datasets()
    return {"datasets": datasets}


@router.post("/analyze/aml")
async def analyze_aml_transactions():
    """Analyze AML transactions in the connected database."""
    agent = get_agent()
    
    if not agent.db_connector:
        raise HTTPException(status_code=400, detail="No database connected")
    
    try:
        import pandas as pd
        import sqlite3
        
        # Get database path
        if hasattr(agent.db_connector.connector, 'config'):
            db_path = agent.db_connector.connector.config.get('name', '')
        else:
            raise HTTPException(status_code=400, detail="Cannot determine database path")
        
        conn = sqlite3.connect(db_path)
        df = pd.read_sql("SELECT * FROM aml_transactions", conn)
        conn.close()
        
        analysis = AMLDatasetAnalyzer.analyze_transactions(df)
        analysis["rules"] = AMLDatasetAnalyzer.get_compliance_rules()
        
        return analysis
        
    except Exception as e:
        logger.error(f"AML analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/paysim")
async def analyze_paysim_transactions():
    """Analyze PaySim fraud transactions in the connected database."""
    agent = get_agent()
    
    if not agent.db_connector:
        raise HTTPException(status_code=400, detail="No database connected")
    
    try:
        import pandas as pd
        import sqlite3
        
        if hasattr(agent.db_connector.connector, 'config'):
            db_path = agent.db_connector.connector.config.get('name', '')
        else:
            raise HTTPException(status_code=400, detail="Cannot determine database path")
        
        conn = sqlite3.connect(db_path)
        df = pd.read_sql("SELECT * FROM paysim_transactions", conn)
        conn.close()
        
        analysis = PaySimAnalyzer.analyze_transactions(df)
        analysis["rules"] = PaySimAnalyzer.get_compliance_rules()
        
        return analysis
        
    except Exception as e:
        logger.error(f"PaySim analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============== FastAPI App Factory ==============

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="Data Policy Agent",
        description="""
        A comprehensive software solution for monitoring database compliance against policy documents.
        
        ## Features
        - PDF Policy Ingestion with rule extraction
        - Multi-database connection support
        - Automated compliance scanning
        - Violation detection with explanations
        - Human review workflow
        - Compliance reporting
        
        ## HackFest 2.0 Integration
        Supports IBM AML, PaySim, and Employee Compliance datasets.
        """,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include router
    app.include_router(router)
    
    # Root: redirect to API docs so users see the real UI, not raw JSON
    @app.get("/", include_in_schema=False)
    async def root_redirect():
        return RedirectResponse(url="/docs", status_code=302)
    
    @app.on_event("startup")
    async def startup_event():
        logger.info("Starting Data Policy Agent API...")
        # Initialize agent
        get_agent()
        logger.info("API ready!")
    
    return app
