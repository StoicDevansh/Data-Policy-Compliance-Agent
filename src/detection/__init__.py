"""Detection module initialization"""
from .violation_engine import ViolationEngine
from .explainer import ViolationExplainer

__all__ = ['ViolationEngine', 'ViolationExplainer']
