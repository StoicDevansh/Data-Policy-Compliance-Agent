"""
Dataset Loader - Downloads and manages HackFest 2.0 recommended datasets.

Primary: IBM Transactions for Anti-Money Laundering (AML)
  - URL: https://www.kaggle.com/datasets/ealtman2019/ibm-transactions-for-anti-money-laundering-aml
  - License: CDLA-Sharing-1.0

Secondary: PaySim Financial Dataset
  - URL: https://www.kaggle.com/datasets/ealaxi/paysim1
  - License: CC BY-SA 4.0

Tertiary: Employee Policy Compliance Dataset
  - URL: https://www.kaggle.com/datasets/laraibnadeem2023/employee-policy-compliance-dataset
"""
import os
import asyncio
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class DatasetLoader:
    """
    Manages downloading and loading of HackFest 2.0 recommended datasets.
    """
    
    # Dataset metadata
    DATASETS = {
        "ibm_aml": {
            "name": "IBM Transactions for Anti-Money Laundering",
            "kaggle_id": "ealtman2019/ibm-transactions-for-anti-money-laundering-aml",
            "license": "CDLA-Sharing-1.0",
            "description": "Synthetic financial transaction data with explicit laundering tags",
            "files": ["HI-Small_Trans.csv", "HI-Medium_Trans.csv", "LI-Small_Trans.csv"],
            "primary": True
        },
        "paysim": {
            "name": "PaySim Financial Dataset",
            "kaggle_id": "ealaxi/paysim1",
            "license": "CC BY-SA 4.0",
            "description": "6.3M synthetic mobile money transactions with fraud labels",
            "files": ["PS_20174392719_1491204439457_log.csv"],
            "primary": False
        },
        "employee_compliance": {
            "name": "Employee Policy Compliance Dataset",
            "kaggle_id": "laraibnadeem2023/employee-policy-compliance-dataset",
            "license": "Community",
            "description": "HR/employee policy compliance - attendance, leave, training",
            "files": ["employee_policy_compliance.csv"],
            "primary": False
        }
    }
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize dataset loader.
        
        Args:
            data_dir: Directory to store downloaded datasets
        """
        self.data_dir = data_dir or Path(__file__).parent.parent.parent / "data" / "datasets"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Dataset loader initialized. Data directory: {self.data_dir}")
    
    def download_dataset(self, dataset_key: str, force: bool = False) -> bool:
        """
        Download a dataset from Kaggle.
        
        Args:
            dataset_key: Key from DATASETS dict (ibm_aml, paysim, employee_compliance)
            force: Force re-download even if exists
            
        Returns:
            True if successful
        """
        if dataset_key not in self.DATASETS:
            logger.error(f"Unknown dataset: {dataset_key}")
            return False
        
        dataset = self.DATASETS[dataset_key]
        dataset_dir = self.data_dir / dataset_key
        
        # Check if already downloaded
        if dataset_dir.exists() and not force:
            existing_files = list(dataset_dir.glob("*.csv"))
            if existing_files:
                logger.info(f"Dataset {dataset_key} already exists at {dataset_dir}")
                return True
        
        dataset_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Try kaggle API
            import kaggle
            logger.info(f"Downloading {dataset['name']} from Kaggle...")
            kaggle.api.dataset_download_files(
                dataset['kaggle_id'],
                path=str(dataset_dir),
                unzip=True
            )
            logger.info(f"Successfully downloaded {dataset['name']}")
            return True
            
        except ImportError:
            logger.warning("Kaggle package not installed. Install with: pip install kaggle")
            logger.info(f"Please manually download from: https://www.kaggle.com/datasets/{dataset['kaggle_id']}")
            logger.info(f"And extract to: {dataset_dir}")
            return False
            
        except Exception as e:
            logger.error(f"Failed to download dataset: {e}")
            logger.info(f"Please manually download from: https://www.kaggle.com/datasets/{dataset['kaggle_id']}")
            return False
    
    def download_all_datasets(self, force: bool = False) -> Dict[str, bool]:
        """
        Download all recommended datasets.
        
        Returns:
            Dict mapping dataset_key to download success status
        """
        results = {}
        for dataset_key in self.DATASETS:
            results[dataset_key] = self.download_dataset(dataset_key, force)
        return results
    
    def load_dataset(self, dataset_key: str, sample_size: Optional[int] = None) -> Optional[Any]:
        """
        Load a dataset into a pandas DataFrame.
        
        Args:
            dataset_key: Key from DATASETS dict
            sample_size: Optional number of rows to sample
            
        Returns:
            pandas DataFrame or None if not available
        """
        if not PANDAS_AVAILABLE:
            logger.error("pandas not available. Install with: pip install pandas")
            return None
        
        if dataset_key not in self.DATASETS:
            logger.error(f"Unknown dataset: {dataset_key}")
            return None
        
        dataset = self.DATASETS[dataset_key]
        dataset_dir = self.data_dir / dataset_key
        
        # Find CSV files
        csv_files = list(dataset_dir.glob("*.csv"))
        if not csv_files:
            logger.warning(f"No CSV files found for {dataset_key}. Run download_dataset first.")
            return None
        
        # Load first CSV (or combine)
        try:
            df = pd.read_csv(csv_files[0])
            
            if sample_size and len(df) > sample_size:
                df = df.sample(n=sample_size, random_state=42)
            
            logger.info(f"Loaded {len(df)} rows from {dataset_key}")
            return df
            
        except Exception as e:
            logger.error(f"Failed to load dataset: {e}")
            return None
    
    def load_to_sqlite(
        self,
        dataset_key: str,
        db_path: Optional[Path] = None,
        table_name: Optional[str] = None,
        sample_size: Optional[int] = None
    ) -> Optional[str]:
        """
        Load a dataset into a SQLite database.
        
        Args:
            dataset_key: Key from DATASETS dict
            db_path: Path to SQLite database file
            table_name: Name for the table
            sample_size: Optional number of rows to load
            
        Returns:
            Path to the SQLite database or None
        """
        df = self.load_dataset(dataset_key, sample_size)
        if df is None:
            return None
        
        db_path = db_path or self.data_dir / f"{dataset_key}.db"
        table_name = table_name or dataset_key.replace("-", "_")
        
        try:
            conn = sqlite3.connect(str(db_path))
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            conn.close()
            
            logger.info(f"Loaded {len(df)} rows into {db_path}:{table_name}")
            return str(db_path)
            
        except Exception as e:
            logger.error(f"Failed to load to SQLite: {e}")
            return None
    
    def get_dataset_info(self, dataset_key: str) -> Optional[Dict[str, Any]]:
        """Get metadata about a dataset."""
        if dataset_key not in self.DATASETS:
            return None
        
        dataset = self.DATASETS[dataset_key].copy()
        dataset_dir = self.data_dir / dataset_key
        
        # Check if downloaded
        dataset['downloaded'] = dataset_dir.exists()
        dataset['local_path'] = str(dataset_dir)
        
        if dataset['downloaded']:
            csv_files = list(dataset_dir.glob("*.csv"))
            dataset['local_files'] = [f.name for f in csv_files]
        
        return dataset
    
    def list_datasets(self) -> List[Dict[str, Any]]:
        """List all available datasets with their status."""
        return [self.get_dataset_info(key) for key in self.DATASETS]


class AMLDatasetAnalyzer:
    """
    Analyzer specifically for IBM AML transaction dataset.
    Provides pre-built compliance rule suggestions.
    """
    
    # Pre-defined compliance rules for AML transactions
    AML_COMPLIANCE_RULES = [
        {
            "id": "aml_001",
            "name": "Large Transaction Reporting",
            "description": "Flag any single transaction exceeding $10,000",
            "type": "threshold",
            "column": "Amount",
            "operator": ">",
            "value": 10000,
            "severity": "high",
            "regulation": "Bank Secrecy Act"
        },
        {
            "id": "aml_002",
            "name": "Structuring Detection",
            "description": "Flag accounts with >5 transactions to same beneficiary within 24 hours",
            "type": "frequency",
            "time_window": "24h",
            "threshold": 5,
            "severity": "critical",
            "regulation": "Anti-Structuring Laws"
        },
        {
            "id": "aml_003",
            "name": "Suspicious Multiple Transactions",
            "description": "Flag multiple transactions just below $10,000 threshold",
            "type": "pattern",
            "amount_range": [9000, 9999],
            "count_threshold": 3,
            "severity": "critical",
            "regulation": "Bank Secrecy Act"
        },
        {
            "id": "aml_004",
            "name": "High-Risk Account Activity",
            "description": "Monitor accounts flagged as Is Laundering",
            "type": "flag_check",
            "column": "Is Laundering",
            "value": 1,
            "severity": "critical",
            "regulation": "AML Compliance"
        },
        {
            "id": "aml_005",
            "name": "Cross-Border Transaction Monitoring",
            "description": "Flag international transfers above threshold",
            "type": "cross_border",
            "threshold": 5000,
            "severity": "medium",
            "regulation": "FATF Guidelines"
        }
    ]
    
    @classmethod
    def get_compliance_rules(cls) -> List[Dict[str, Any]]:
        """Get pre-defined AML compliance rules."""
        return cls.AML_COMPLIANCE_RULES
    
    @classmethod
    def analyze_transactions(cls, df: Any) -> Dict[str, Any]:
        """
        Analyze transaction dataset for compliance issues.
        
        Args:
            df: pandas DataFrame with transaction data
            
        Returns:
            Analysis results with potential violations
        """
        if not PANDAS_AVAILABLE:
            return {"error": "pandas not available"}
        
        results = {
            "total_transactions": len(df),
            "potential_violations": [],
            "statistics": {}
        }
        
        # Check for Amount column
        if 'Amount' in df.columns or 'amount' in df.columns:
            amount_col = 'Amount' if 'Amount' in df.columns else 'amount'
            
            # Large transactions
            large_trans = df[df[amount_col] > 10000]
            if len(large_trans) > 0:
                results["potential_violations"].append({
                    "rule_id": "aml_001",
                    "count": len(large_trans),
                    "description": f"Found {len(large_trans)} transactions exceeding $10,000"
                })
            
            # Near-threshold transactions (possible structuring)
            near_threshold = df[(df[amount_col] >= 9000) & (df[amount_col] < 10000)]
            if len(near_threshold) > 0:
                results["potential_violations"].append({
                    "rule_id": "aml_003",
                    "count": len(near_threshold),
                    "description": f"Found {len(near_threshold)} transactions between $9,000-$10,000"
                })
            
            results["statistics"]["amount"] = {
                "mean": float(df[amount_col].mean()),
                "max": float(df[amount_col].max()),
                "min": float(df[amount_col].min())
            }
        
        # Check for laundering flag
        laundering_col = None
        for col in ['Is Laundering', 'is_laundering', 'Is_Laundering']:
            if col in df.columns:
                laundering_col = col
                break
        
        if laundering_col:
            flagged = df[df[laundering_col] == 1]
            if len(flagged) > 0:
                results["potential_violations"].append({
                    "rule_id": "aml_004",
                    "count": len(flagged),
                    "description": f"Found {len(flagged)} transactions flagged as laundering"
                })
            
            results["statistics"]["laundering_rate"] = float(df[laundering_col].mean())
        
        return results


class PaySimAnalyzer:
    """
    Analyzer specifically for PaySim financial fraud dataset.
    """
    
    FRAUD_COMPLIANCE_RULES = [
        {
            "id": "fraud_001",
            "name": "Fraud Transaction Detection",
            "description": "Flag transactions marked as fraudulent",
            "type": "flag_check",
            "column": "isFraud",
            "value": 1,
            "severity": "critical"
        },
        {
            "id": "fraud_002",
            "name": "Large Transfer Monitoring",
            "description": "Monitor large TRANSFER transactions",
            "type": "composite",
            "conditions": [
                {"column": "type", "operator": "==", "value": "TRANSFER"},
                {"column": "amount", "operator": ">", "value": 200000}
            ],
            "severity": "high"
        },
        {
            "id": "fraud_003",
            "name": "Zero Balance Alert",
            "description": "Flag transfers where origin balance drops to zero",
            "type": "balance_check",
            "column": "newbalanceOrig",
            "operator": "==",
            "value": 0,
            "severity": "medium"
        },
        {
            "id": "fraud_004",
            "name": "Cash Out Monitoring",
            "description": "Monitor large CASH_OUT transactions",
            "type": "composite",
            "conditions": [
                {"column": "type", "operator": "==", "value": "CASH_OUT"},
                {"column": "amount", "operator": ">", "value": 100000}
            ],
            "severity": "high"
        }
    ]
    
    @classmethod
    def get_compliance_rules(cls) -> List[Dict[str, Any]]:
        """Get pre-defined fraud compliance rules."""
        return cls.FRAUD_COMPLIANCE_RULES
    
    @classmethod
    def analyze_transactions(cls, df: Any) -> Dict[str, Any]:
        """Analyze PaySim transactions for fraud violations."""
        if not PANDAS_AVAILABLE:
            return {"error": "pandas not available"}
        
        results = {
            "total_transactions": len(df),
            "potential_violations": [],
            "statistics": {}
        }
        
        # Check fraud column
        if 'isFraud' in df.columns:
            fraud_count = df['isFraud'].sum()
            if fraud_count > 0:
                results["potential_violations"].append({
                    "rule_id": "fraud_001",
                    "count": int(fraud_count),
                    "description": f"Found {fraud_count} fraudulent transactions"
                })
            results["statistics"]["fraud_rate"] = float(df['isFraud'].mean())
        
        # Check transaction types
        if 'type' in df.columns:
            results["statistics"]["transaction_types"] = df['type'].value_counts().to_dict()
        
        # Amount statistics
        if 'amount' in df.columns:
            results["statistics"]["amount"] = {
                "mean": float(df['amount'].mean()),
                "max": float(df['amount'].max()),
                "min": float(df['amount'].min())
            }
        
        return results
