"""
Data Policy Agent - Main Entry Point

Run with:
    uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

Or:
    python -m src.main
"""
import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

# Configure logging
logger.add(
    "logs/dap_{time}.log",
    rotation="1 day",
    retention="7 days",
    level="INFO"
)


def main():
    """Run the FastAPI application."""
    import uvicorn
    from src.api.routes import create_app
    
    app = create_app()
    
    print("\n" + "="*60)
    print("DATA POLICY AGENT - Starting Server")
    print("="*60)
    print("\nServer Info:")
    print("  URL: http://localhost:8000")
    print("  Docs: http://localhost:8000/docs")
    print("  ReDoc: http://localhost:8000/redoc")
    print("\nQuick Start:")
    print("  1. POST /api/database/demo  - Set up demo database")
    print("  2. POST /api/rules/load     - Load compliance rules")
    print("  3. POST /api/scan           - Run compliance scan")
    print("  4. GET /api/violations      - View violations")
    print("  5. GET /api/dashboard       - View dashboard data")
    print("\n" + "="*60 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


from src.api.routes import create_app
app = create_app()


if __name__ == "__main__":
    main()
