"""
Database Initialization - Sets up internal SQLite database for storing policies, rules, and violations.
"""
import sqlite3
from pathlib import Path
from loguru import logger

from ..core.config import get_settings


def init_internal_db(db_path: str = None) -> None:
    """
    Initialize the internal database for storing DAP data.
    
    Args:
        db_path: Path to the SQLite database file
    """
    settings = get_settings()
    db_path = db_path or settings.internal_db_path
    
    # Ensure directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Initializing internal database at: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create policies table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS policies (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            source_path TEXT,
            content_hash TEXT,
            page_count INTEGER,
            rules_count INTEGER,
            status TEXT DEFAULT 'active',
            ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create rules table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rules (
            id TEXT PRIMARY KEY,
            policy_id TEXT NOT NULL,
            type TEXT NOT NULL,
            text TEXT NOT NULL,
            severity TEXT DEFAULT 'medium',
            entities TEXT,  -- JSON array
            condition TEXT,
            sql_condition TEXT,
            sql_hint TEXT,
            extraction_method TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (policy_id) REFERENCES policies(id)
        )
    """)
    
    # Create violations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS violations (
            id TEXT PRIMARY KEY,
            rule_id TEXT NOT NULL,
            scan_id TEXT,
            type TEXT NOT NULL,
            table_name TEXT,
            column_name TEXT,
            violation_count INTEGER DEFAULT 1,
            details TEXT,
            explanation TEXT,
            remediation TEXT,
            severity TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'open',  -- open, under_review, resolved, false_positive
            review_status TEXT,
            reviewed_by TEXT,
            reviewed_at TIMESTAMP,
            review_comments TEXT,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP,
            FOREIGN KEY (rule_id) REFERENCES rules(id)
        )
    """)
    
    # Create scans table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id TEXT PRIMARY KEY,
            tables_scanned TEXT,  -- JSON array
            rules_checked INTEGER,
            violations_found INTEGER,
            status TEXT DEFAULT 'completed',
            started_at TIMESTAMP,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create reviews table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id TEXT PRIMARY KEY,
            violation_ids TEXT NOT NULL,  -- JSON array
            reviewers TEXT,  -- JSON array
            status TEXT DEFAULT 'pending',  -- pending, in_progress, completed
            decision TEXT,  -- approve, reject, escalate
            comments TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
    """)
    
    # Create database_connections table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS database_connections (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            host TEXT,
            port INTEGER,
            name TEXT,
            status TEXT DEFAULT 'active',
            connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_scanned_at TIMESTAMP
        )
    """)
    
    # Create reports table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,  -- compliance, audit, summary
            format TEXT DEFAULT 'pdf',
            file_path TEXT,
            violations_included INTEGER,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rules_policy ON rules(policy_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rules_type ON rules(type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_violations_rule ON violations(rule_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_violations_status ON violations(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_violations_scan ON violations(scan_id)")
    
    conn.commit()
    conn.close()
    
    logger.info("Internal database initialized successfully")


def reset_internal_db(db_path: str = None) -> None:
    """
    Reset the internal database (drop all tables and recreate).
    
    Args:
        db_path: Path to the SQLite database file
    """
    settings = get_settings()
    db_path = db_path or settings.internal_db_path
    
    # Remove existing database
    db_file = Path(db_path)
    if db_file.exists():
        db_file.unlink()
        logger.info(f"Removed existing database: {db_path}")
    
    # Reinitialize
    init_internal_db(db_path)


if __name__ == "__main__":
    init_internal_db()
