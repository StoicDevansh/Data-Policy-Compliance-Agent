"""
Sample Data Generator - Creates synthetic sample data for testing and demos.

Generates sample data matching the structure of:
- IBM AML Transaction Dataset
- PaySim Financial Dataset
- Employee Policy Compliance Dataset
"""
import random
import string
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from loguru import logger


class SampleDataGenerator:
    """
    Generates synthetic sample data for testing the Data Policy Agent
    without requiring external dataset downloads.
    """
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize sample data generator.
        
        Args:
            output_dir: Directory to save generated data
        """
        self.output_dir = output_dir or Path(__file__).parent.parent.parent / "data" / "sample"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_aml_transactions(
        self,
        num_records: int = 10000,
        laundering_rate: float = 0.02
    ) -> List[Dict[str, Any]]:
        """
        Generate synthetic AML transaction data matching IBM dataset structure.
        
        Args:
            num_records: Number of transactions to generate
            laundering_rate: Fraction of transactions to mark as suspicious
            
        Returns:
            List of transaction dictionaries
        """
        transactions = []
        
        # Generate account IDs
        accounts = [f"ACC_{i:06d}" for i in range(num_records // 10)]
        
        # Transaction types
        tx_types = ['TRANSFER', 'PAYMENT', 'CASH_IN', 'CASH_OUT', 'DEBIT']
        
        # Currencies
        currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CHF']
        
        base_date = datetime(2024, 1, 1)
        
        for i in range(num_records):
            # Determine if this is a laundering transaction
            is_laundering = random.random() < laundering_rate
            
            # Laundering transactions tend to have specific patterns
            if is_laundering:
                # Pattern 1: Just under reporting threshold
                if random.random() < 0.4:
                    amount = random.uniform(9000, 9999)
                # Pattern 2: Large round numbers
                elif random.random() < 0.7:
                    amount = random.choice([10000, 25000, 50000, 100000]) + random.uniform(-100, 100)
                # Pattern 3: Very large amounts
                else:
                    amount = random.uniform(100000, 1000000)
            else:
                # Normal transactions follow a more natural distribution
                amount = random.expovariate(1/5000)  # Average around $5000
                amount = min(amount, 50000)  # Cap normal transactions
            
            tx_date = base_date + timedelta(
                days=random.randint(0, 365),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            transaction = {
                "Transaction_ID": f"TX_{i:08d}",
                "Timestamp": tx_date.isoformat(),
                "From_Account": random.choice(accounts),
                "To_Account": random.choice(accounts),
                "Amount": round(amount, 2),
                "Currency": random.choice(currencies),
                "Transaction_Type": random.choice(tx_types),
                "Is_Laundering": 1 if is_laundering else 0,
                "Payment_Format": random.choice(['Wire', 'ACH', 'Check', 'Cash', 'Crypto']),
                "From_Bank": f"BANK_{random.randint(1, 50):03d}",
                "To_Bank": f"BANK_{random.randint(1, 50):03d}",
                "Account_Age_Days": random.randint(30, 3650),
                "Is_First_Transaction": 1 if random.random() < 0.05 else 0
            }
            
            transactions.append(transaction)
        
        logger.info(f"Generated {num_records} AML transactions ({int(laundering_rate*100)}% laundering rate)")
        return transactions
    
    def generate_paysim_transactions(
        self,
        num_records: int = 10000,
        fraud_rate: float = 0.01
    ) -> List[Dict[str, Any]]:
        """
        Generate synthetic PaySim-style financial transaction data.
        
        Args:
            num_records: Number of transactions to generate
            fraud_rate: Fraction of transactions to mark as fraud
            
        Returns:
            List of transaction dictionaries
        """
        transactions = []
        
        # Transaction types from PaySim
        tx_types = ['PAYMENT', 'TRANSFER', 'CASH_OUT', 'DEBIT', 'CASH_IN']
        
        for i in range(num_records):
            tx_type = random.choice(tx_types)
            is_fraud = random.random() < fraud_rate
            
            # Fraud transactions tend to be larger
            if is_fraud:
                amount = random.uniform(10000, 500000)
            else:
                amount = random.expovariate(1/2000)
                amount = min(amount, 100000)
            
            # Generate balances
            old_balance_orig = random.uniform(0, 100000)
            new_balance_orig = max(0, old_balance_orig - amount)
            old_balance_dest = random.uniform(0, 100000)
            new_balance_dest = old_balance_dest + amount
            
            transaction = {
                "step": i,
                "type": tx_type,
                "amount": round(amount, 2),
                "nameOrig": f"C{random.randint(100000000, 999999999)}",
                "oldbalanceOrg": round(old_balance_orig, 2),
                "newbalanceOrig": round(new_balance_orig, 2),
                "nameDest": f"M{random.randint(100000000, 999999999)}",
                "oldbalanceDest": round(old_balance_dest, 2),
                "newbalanceDest": round(new_balance_dest, 2),
                "isFraud": 1 if is_fraud else 0,
                "isFlaggedFraud": 1 if (is_fraud and random.random() < 0.8) else 0
            }
            
            transactions.append(transaction)
        
        logger.info(f"Generated {num_records} PaySim transactions ({int(fraud_rate*100)}% fraud rate)")
        return transactions
    
    def generate_employee_compliance(
        self,
        num_employees: int = 500,
        violation_rate: float = 0.15
    ) -> List[Dict[str, Any]]:
        """
        Generate synthetic employee policy compliance data.
        
        Args:
            num_employees: Number of employee records
            violation_rate: Fraction with compliance violations
            
        Returns:
            List of employee compliance dictionaries
        """
        records = []
        
        departments = ['Engineering', 'Sales', 'Marketing', 'HR', 'Finance', 'Operations', 'Legal']
        roles = ['Junior', 'Senior', 'Lead', 'Manager', 'Director', 'VP']
        
        for i in range(num_employees):
            has_violation = random.random() < violation_rate
            
            # Attendance compliance
            attendance_rate = random.uniform(0.7, 1.0) if not has_violation else random.uniform(0.5, 0.8)
            
            # Training compliance
            training_completed = not has_violation or random.random() < 0.5
            
            # Leave policy compliance
            leave_days_used = random.randint(0, 30)
            leave_days_allowed = 25
            leave_violation = leave_days_used > leave_days_allowed
            
            record = {
                "employee_id": f"EMP_{i:05d}",
                "name": f"Employee_{i}",
                "department": random.choice(departments),
                "role": random.choice(roles),
                "hire_date": (datetime.now() - timedelta(days=random.randint(30, 3650))).strftime("%Y-%m-%d"),
                "attendance_rate": round(attendance_rate, 2),
                "mandatory_training_completed": training_completed,
                "training_completion_date": datetime.now().strftime("%Y-%m-%d") if training_completed else None,
                "leave_days_used": leave_days_used,
                "leave_days_allowed": leave_days_allowed,
                "leave_policy_violation": leave_violation,
                "security_clearance_valid": random.random() > 0.1,
                "nda_signed": random.random() > 0.05,
                "last_performance_review": (datetime.now() - timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d"),
                "compliance_score": round(random.uniform(0.5, 1.0) if not has_violation else random.uniform(0.3, 0.7), 2),
                "has_violation": has_violation
            }
            
            records.append(record)
        
        logger.info(f"Generated {num_employees} employee compliance records ({int(violation_rate*100)}% violation rate)")
        return records
    
    def save_to_csv(self, data: List[Dict], filename: str) -> str:
        """Save data to CSV file."""
        try:
            import pandas as pd
            df = pd.DataFrame(data)
            filepath = self.output_dir / filename
            df.to_csv(filepath, index=False)
            logger.info(f"Saved {len(data)} records to {filepath}")
            return str(filepath)
        except ImportError:
            logger.error("pandas required for CSV export")
            return ""
    
    def save_to_sqlite(
        self,
        data: List[Dict],
        table_name: str,
        db_name: str = "sample_data.db"
    ) -> str:
        """
        Save data to SQLite database.
        
        Args:
            data: List of dictionaries
            table_name: Name for the database table
            db_name: SQLite database filename
            
        Returns:
            Path to the database
        """
        db_path = self.output_dir / db_name
        
        try:
            import pandas as pd
            df = pd.DataFrame(data)
            
            conn = sqlite3.connect(str(db_path))
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            conn.close()
            
            logger.info(f"Saved {len(data)} records to {db_path}:{table_name}")
            return str(db_path)
            
        except ImportError:
            # Fallback without pandas
            if not data:
                return ""
            
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Create table
            columns = list(data[0].keys())
            create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            cursor.execute(create_sql)
            
            # Insert data
            placeholders = ', '.join(['?' for _ in columns])
            insert_sql = f"INSERT INTO {table_name} VALUES ({placeholders})"
            
            for record in data:
                values = [record.get(col) for col in columns]
                cursor.execute(insert_sql, values)
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved {len(data)} records to {db_path}:{table_name}")
            return str(db_path)
    
    def generate_all_sample_data(self, db_name: str = "compliance_sample.db") -> Dict[str, str]:
        """
        Generate all sample datasets and save to a single SQLite database.
        
        Returns:
            Dict with paths to generated data
        """
        results = {}
        db_path = self.output_dir / db_name
        
        # Generate AML transactions
        aml_data = self.generate_aml_transactions(num_records=5000, laundering_rate=0.03)
        results['aml_transactions'] = self.save_to_sqlite(aml_data, 'aml_transactions', db_name)
        
        # Generate PaySim transactions
        paysim_data = self.generate_paysim_transactions(num_records=5000, fraud_rate=0.02)
        self.save_to_sqlite(paysim_data, 'paysim_transactions', db_name)
        results['paysim_transactions'] = str(db_path)
        
        # Generate employee compliance data
        employee_data = self.generate_employee_compliance(num_employees=200, violation_rate=0.12)
        self.save_to_sqlite(employee_data, 'employee_compliance', db_name)
        results['employee_compliance'] = str(db_path)
        
        logger.info(f"All sample data saved to: {db_path}")
        results['database_path'] = str(db_path)
        
        return results


def create_demo_database():
    """Convenience function to create a demo database with all sample data."""
    generator = SampleDataGenerator()
    return generator.generate_all_sample_data()


if __name__ == "__main__":
    # Generate sample data when run directly
    results = create_demo_database()
    print(f"Demo database created at: {results['database_path']}")
