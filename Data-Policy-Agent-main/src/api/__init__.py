"""
API Module - REST API endpoints for the Data Policy Agent.
"""
from .routes import create_app, router

__all__ = ["create_app", "router"]
