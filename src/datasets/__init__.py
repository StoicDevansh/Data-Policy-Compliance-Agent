"""
Datasets Module - HackFest 2.0 Dataset Integration.

Integrates recommended datasets for Data Policy Compliance Agent:
- IBM Transactions for Anti-Money Laundering (AML) - Primary
- PaySim Financial Dataset - Secondary
- Employee Policy Compliance Dataset - Tertiary
"""
from .loader import DatasetLoader
from .sample_data import SampleDataGenerator

__all__ = ["DatasetLoader", "SampleDataGenerator"]
