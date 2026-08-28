"""
Dataset Initialization Script for HackFest 2.0 Integration.

This script sets up the sample datasets and demo environment for testing
the Data Policy Compliance Agent with the recommended HackFest 2.0 datasets.

Usage:
    python -m src.datasets.init_datasets [--download] [--sample-only]

Options:
    --download      Download actual datasets from Kaggle (requires API key)
    --sample-only   Only generate synthetic sample data (default)
    --all           Both download and generate sample data
"""
import sys
import argparse
import json
from pathlib import Path
from loguru import logger

# Add parent to path if running as script
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.datasets.loader import DatasetLoader, AMLDatasetAnalyzer, PaySimAnalyzer
from src.datasets.sample_data import SampleDataGenerator, create_demo_database


def setup_directories():
    """Create necessary directories for datasets."""
    base_dir = Path(__file__).parent.parent.parent
    
    directories = [
        base_dir / "data" / "datasets",
        base_dir / "data" / "sample",
        base_dir / "data" / "policies",
        base_dir / "data" / "rules",
        base_dir / "data" / "reports",
    ]
    
    for dir_path in directories:
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {dir_path}")
    
    return base_dir


def download_kaggle_datasets():
    """Download datasets from Kaggle (requires kaggle API key configuration)."""
    loader = DatasetLoader()
    
    print("\n" + "="*60)
    print("DOWNLOADING HACKFEST 2.0 RECOMMENDED DATASETS")
    print("="*60)
    
    print("\nNote: Kaggle API requires authentication.")
    print("Set up your kaggle.json file from https://www.kaggle.com/account")
    print("Place it in ~/.kaggle/kaggle.json (Linux/Mac) or %USERPROFILE%\\.kaggle\\kaggle.json (Windows)\n")
    
    results = loader.download_all_datasets()
    
    print("\nDownload Results:")
    print("-" * 40)
    for dataset, success in results.items():
        status = "✓ Downloaded" if success else "✗ Manual download required"
        info = loader.get_dataset_info(dataset)
        print(f"  {info['name']}: {status}")
        if not success:
            print(f"    → https://www.kaggle.com/datasets/{info['kaggle_id']}")
    
    return results


def generate_sample_data():
    """Generate synthetic sample data for testing."""
    print("\n" + "="*60)
    print("GENERATING SYNTHETIC SAMPLE DATA")
    print("="*60)
    
    generator = SampleDataGenerator()
    
    # Generate AML transactions
    print("\n1. Generating AML Transaction Data...")
    aml_data = generator.generate_aml_transactions(num_records=5000, laundering_rate=0.03)
    generator.save_to_csv(aml_data, "aml_transactions.csv")
    
    # Generate PaySim transactions
    print("\n2. Generating PaySim Transaction Data...")
    paysim_data = generator.generate_paysim_transactions(num_records=5000, fraud_rate=0.02)
    generator.save_to_csv(paysim_data, "paysim_transactions.csv")
    
    # Generate employee compliance data
    print("\n3. Generating Employee Compliance Data...")
    employee_data = generator.generate_employee_compliance(num_employees=200, violation_rate=0.12)
    generator.save_to_csv(employee_data, "employee_compliance.csv")
    
    # Create combined SQLite database
    print("\n4. Creating SQLite Database...")
    results = generator.generate_all_sample_data(db_name="hackfest_compliance.db")
    
    print("\n" + "-"*40)
    print(f"Sample data saved to: {results['database_path']}")
    
    return results


def analyze_sample_data(db_path: str):
    """Analyze the generated sample data for compliance issues."""
    print("\n" + "="*60)
    print("ANALYZING SAMPLE DATA FOR COMPLIANCE ISSUES")
    print("="*60)
    
    try:
        import pandas as pd
        import sqlite3
        
        conn = sqlite3.connect(db_path)
        
        # Analyze AML transactions
        print("\n1. AML Transaction Analysis:")
        print("-" * 40)
        aml_df = pd.read_sql("SELECT * FROM aml_transactions", conn)
        aml_results = AMLDatasetAnalyzer.analyze_transactions(aml_df)
        
        print(f"   Total transactions: {aml_results['total_transactions']}")
        if 'statistics' in aml_results:
            stats = aml_results['statistics']
            if 'amount' in stats:
                print(f"   Amount range: ${stats['amount']['min']:.2f} - ${stats['amount']['max']:.2f}")
            if 'laundering_rate' in stats:
                print(f"   Laundering rate: {stats['laundering_rate']*100:.2f}%")
        
        print(f"\n   Potential Violations Found:")
        for v in aml_results.get('potential_violations', []):
            print(f"   - {v['description']}")
        
        # Analyze PaySim transactions
        print("\n2. PaySim Fraud Analysis:")
        print("-" * 40)
        paysim_df = pd.read_sql("SELECT * FROM paysim_transactions", conn)
        paysim_results = PaySimAnalyzer.analyze_transactions(paysim_df)
        
        print(f"   Total transactions: {paysim_results['total_transactions']}")
        if 'statistics' in paysim_results:
            stats = paysim_results['statistics']
            if 'fraud_rate' in stats:
                print(f"   Fraud rate: {stats['fraud_rate']*100:.2f}%")
        
        print(f"\n   Potential Violations Found:")
        for v in paysim_results.get('potential_violations', []):
            print(f"   - {v['description']}")
        
        # Analyze Employee Compliance
        print("\n3. Employee Compliance Analysis:")
        print("-" * 40)
        emp_df = pd.read_sql("SELECT * FROM employee_compliance", conn)
        
        compliance_issues = {
            "low_attendance": len(emp_df[emp_df['attendance_rate'] < 0.85]),
            "training_incomplete": len(emp_df[emp_df['mandatory_training_completed'] == False]),
            "leave_violations": len(emp_df[emp_df['leave_policy_violation'] == True]),
            "invalid_clearance": len(emp_df[emp_df['security_clearance_valid'] == False]),
            "missing_nda": len(emp_df[emp_df['nda_signed'] == False]),
            "low_compliance_score": len(emp_df[emp_df['compliance_score'] < 0.70])
        }
        
        print(f"   Total employees: {len(emp_df)}")
        print(f"   Employees with violations: {emp_df['has_violation'].sum()}")
        print(f"\n   Issue Breakdown:")
        for issue, count in compliance_issues.items():
            if count > 0:
                print(f"   - {issue.replace('_', ' ').title()}: {count} employees")
        
        conn.close()
        
    except ImportError:
        print("pandas required for analysis. Install with: pip install pandas")
    except Exception as e:
        print(f"Error analyzing data: {e}")


def print_compliance_rules():
    """Print summary of available compliance rules."""
    print("\n" + "="*60)
    print("AVAILABLE COMPLIANCE RULES")
    print("="*60)
    
    rules_path = Path(__file__).parent.parent.parent / "data" / "rules" / "compliance_rules.json"
    
    if rules_path.exists():
        with open(rules_path) as f:
            rules_config = json.load(f)
        
        for ruleset_key, ruleset in rules_config['rule_sets'].items():
            print(f"\n{ruleset['name']}")
            print("-" * 40)
            print(f"  Dataset: {ruleset['dataset']}")
            print(f"  Rules: {len(ruleset['rules'])}")
            
            # Count by severity
            severity_count = {}
            for rule in ruleset['rules']:
                sev = rule.get('severity', 'unknown')
                severity_count[sev] = severity_count.get(sev, 0) + 1
            
            print(f"  By Severity: {severity_count}")
    else:
        print("  Rules file not found. Run initialization first.")


def print_usage_example():
    """Print example usage code."""
    print("\n" + "="*60)
    print("EXAMPLE USAGE")
    print("="*60)
    
    example = '''
from src.core.agent import DataPolicyAgent
from src.datasets.loader import DatasetLoader
from src.datasets.sample_data import create_demo_database

# Option 1: Use sample data (no download required)
db_path = create_demo_database()
print(f"Demo database created at: {db_path['database_path']}")

# Option 2: Download actual Kaggle datasets
loader = DatasetLoader()
loader.download_dataset("ibm_aml")  # Requires Kaggle API key

# Initialize agent
agent = DataPolicyAgent()

# Connect to sample database
await agent.connect_database({
    "type": "sqlite",
    "name": db_path['database_path']
})

# Ingest policy documents
await agent.ingest_policy("data/policies/aml_compliance_policy.md")
await agent.ingest_policy("data/policies/fraud_detection_policy.md")

# Scan for violations
violations = await agent.scan_for_violations()

# Generate compliance report
await agent.generate_report(violations, output="compliance_report.pdf")
'''
    print(example)


def main():
    parser = argparse.ArgumentParser(
        description="Initialize HackFest 2.0 datasets for Data Policy Agent"
    )
    parser.add_argument(
        "--download", 
        action="store_true",
        help="Download datasets from Kaggle (requires API key)"
    )
    parser.add_argument(
        "--sample-only", 
        action="store_true",
        help="Only generate synthetic sample data"
    )
    parser.add_argument(
        "--all", 
        action="store_true",
        help="Both download and generate sample data"
    )
    parser.add_argument(
        "--analyze", 
        action="store_true",
        help="Analyze generated data after creation"
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("DATA POLICY AGENT - HACKFEST 2.0 DATASET INITIALIZATION")
    print("="*60)
    print("\nRecommended Datasets:")
    print("  1. IBM AML Transactions (Primary)")
    print("  2. PaySim Financial Dataset (Secondary)")
    print("  3. Employee Compliance Dataset (Tertiary)")
    
    # Setup directories
    base_dir = setup_directories()
    
    db_results = None
    
    if args.download or args.all:
        download_kaggle_datasets()
    
    if args.sample_only or args.all or not (args.download):
        db_results = generate_sample_data()
    
    if args.analyze and db_results:
        analyze_sample_data(db_results['database_path'])
    
    # Print available rules
    print_compliance_rules()
    
    # Print usage example
    print_usage_example()
    
    print("\n" + "="*60)
    print("INITIALIZATION COMPLETE")
    print("="*60)
    print(f"\nData directory: {base_dir / 'data'}")
    print("\nNext steps:")
    print("  1. Review policy documents in data/policies/")
    print("  2. Review compliance rules in data/rules/compliance_rules.json")
    print("  3. Run the agent with sample data or downloaded datasets")


if __name__ == "__main__":
    main()
