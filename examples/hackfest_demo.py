"""
Example: Using HackFest 2.0 Datasets with Data Policy Agent

This script demonstrates how to use the recommended HackFest 2.0 datasets
(IBM AML, PaySim, Employee Compliance) with the Data Policy Agent.

Run with: python examples/hackfest_demo.py
"""
import asyncio
import json
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.datasets.sample_data import SampleDataGenerator, create_demo_database
from src.datasets.loader import DatasetLoader, AMLDatasetAnalyzer, PaySimAnalyzer


async def demo_with_sample_data():
    """Demonstrate the agent with synthetic sample data."""
    print("\n" + "="*60)
    print("DEMO: Data Policy Agent with HackFest 2.0 Datasets")
    print("="*60)
    
    # Step 1: Generate sample data
    print("\n[1/5] Generating sample data...")
    results = create_demo_database()
    db_path = results['database_path']
    print(f"      Database created: {db_path}")
    
    # Step 2: Load compliance rules
    print("\n[2/5] Loading compliance rules...")
    rules_path = Path(__file__).parent.parent / "data" / "rules" / "compliance_rules.json"
    
    if rules_path.exists():
        with open(rules_path) as f:
            rules_config = json.load(f)
        
        total_rules = sum(len(rs['rules']) for rs in rules_config['rule_sets'].values())
        print(f"      Loaded {total_rules} compliance rules across {len(rules_config['rule_sets'])} rule sets")
    else:
        print("      Rules not found - run init_datasets.py first")
        return
    
    # Step 3: Analyze AML transactions
    print("\n[3/5] Analyzing AML transactions for violations...")
    try:
        import pandas as pd
        import sqlite3
        
        conn = sqlite3.connect(db_path)
        aml_df = pd.read_sql("SELECT * FROM aml_transactions", conn)
        
        aml_analysis = AMLDatasetAnalyzer.analyze_transactions(aml_df)
        print(f"      Total transactions: {aml_analysis['total_transactions']}")
        
        for violation in aml_analysis.get('potential_violations', []):
            print(f"      ⚠ {violation['description']}")
        
        # Apply specific rules
        aml_rules = rules_config['rule_sets']['aml_transactions']['rules']
        
        print("\n      Applying compliance rules:")
        for rule in aml_rules[:3]:  # Show first 3 rules
            condition = rule.get('condition', {})
            col = condition.get('column')
            
            if col and col in aml_df.columns:
                op = condition.get('operator')
                val = condition.get('value')
                
                if op == '>' and val:
                    violations = len(aml_df[aml_df[col] > val])
                elif op == '==' and val is not None:
                    violations = len(aml_df[aml_df[col] == val])
                elif op == 'between':
                    min_val = condition.get('min_value')
                    max_val = condition.get('max_value')
                    violations = len(aml_df[(aml_df[col] >= min_val) & (aml_df[col] <= max_val)])
                else:
                    violations = 0
                
                severity_icon = "🔴" if rule['severity'] == 'critical' else "🟠" if rule['severity'] == 'high' else "🟡"
                print(f"      {severity_icon} {rule['name']}: {violations} violations")
        
    except ImportError:
        print("      pandas required. Install: pip install pandas")
    except Exception as e:
        print(f"      Error: {e}")
    
    # Step 4: Analyze PaySim transactions
    print("\n[4/5] Analyzing PaySim transactions for fraud...")
    try:
        paysim_df = pd.read_sql("SELECT * FROM paysim_transactions", conn)
        
        paysim_analysis = PaySimAnalyzer.analyze_transactions(paysim_df)
        print(f"      Total transactions: {paysim_analysis['total_transactions']}")
        
        for violation in paysim_analysis.get('potential_violations', []):
            print(f"      ⚠ {violation['description']}")
        
        # Apply fraud rules
        fraud_rules = rules_config['rule_sets']['paysim_transactions']['rules']
        
        print("\n      Applying fraud detection rules:")
        for rule in fraud_rules[:3]:
            condition = rule.get('condition', {})
            col = condition.get('column')
            
            if col and col in paysim_df.columns:
                val = condition.get('value')
                op = condition.get('operator')
                
                if op == '==' and val is not None:
                    violations = len(paysim_df[paysim_df[col] == val])
                else:
                    violations = 0
                
                severity_icon = "🔴" if rule['severity'] == 'critical' else "🟠" if rule['severity'] == 'high' else "🟡"
                print(f"      {severity_icon} {rule['name']}: {violations} violations")
        
    except Exception as e:
        print(f"      Error: {e}")
    
    # Step 5: Analyze Employee Compliance
    print("\n[5/5] Analyzing employee compliance...")
    try:
        emp_df = pd.read_sql("SELECT * FROM employee_compliance", conn)
        
        print(f"      Total employees: {len(emp_df)}")
        
        # Apply employee rules
        emp_rules = rules_config['rule_sets']['employee_compliance']['rules']
        
        print("\n      Applying compliance rules:")
        for rule in emp_rules[:4]:
            condition = rule.get('condition', {})
            col = condition.get('column')
            
            if col and col in emp_df.columns:
                val = condition.get('value')
                op = condition.get('operator')
                
                if op == '<' and val:
                    violations = len(emp_df[emp_df[col] < val])
                elif op == '==' and val is not None:
                    violations = len(emp_df[emp_df[col] == val])
                else:
                    violations = 0
                
                severity_icon = "🔴" if rule['severity'] == 'critical' else "🟠" if rule['severity'] == 'high' else "🟡"
                print(f"      {severity_icon} {rule['name']}: {violations} violations")
        
        conn.close()
        
    except Exception as e:
        print(f"      Error: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("DEMO COMPLETE")
    print("="*60)
    print(f"""
Summary:
  ✓ Generated synthetic data matching HackFest 2.0 recommended datasets
  ✓ Applied AML compliance rules (IBM AML dataset structure)
  ✓ Applied fraud detection rules (PaySim dataset structure)
  ✓ Applied employee compliance rules

Database Location: {db_path}

Policy Documents:
  - data/policies/aml_compliance_policy.md
  - data/policies/fraud_detection_policy.md
  - data/policies/employee_compliance_policy.md
  - data/policies/gdpr_data_protection_policy.md

Compliance Rules: data/rules/compliance_rules.json

To download actual Kaggle datasets:
  1. Configure Kaggle API: https://www.kaggle.com/account
  2. Run: python -m src.datasets.init_datasets --download
""")


def demo_dataset_info():
    """Show information about available datasets."""
    print("\n" + "="*60)
    print("HACKFEST 2.0 RECOMMENDED DATASETS")
    print("="*60)
    
    loader = DatasetLoader()
    datasets = loader.list_datasets()
    
    for ds in datasets:
        primary_tag = " [PRIMARY]" if ds.get('primary') else ""
        print(f"\n{ds['name']}{primary_tag}")
        print("-" * 50)
        print(f"  Kaggle: kaggle.com/datasets/{ds['kaggle_id']}")
        print(f"  License: {ds['license']}")
        print(f"  Description: {ds['description']}")
        print(f"  Downloaded: {'Yes' if ds.get('downloaded') else 'No'}")
    
    print("\n" + "-"*60)
    print("""
Download Instructions:
  1. Create Kaggle account: https://www.kaggle.com
  2. Go to Account → Create New API Token
  3. Save kaggle.json to:
     - Windows: %USERPROFILE%\\.kaggle\\kaggle.json
     - Linux/Mac: ~/.kaggle/kaggle.json
  4. Run: python -m src.datasets.init_datasets --download
""")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="HackFest 2.0 Dataset Demo")
    parser.add_argument("--info", action="store_true", help="Show dataset information")
    
    args = parser.parse_args()
    
    if args.info:
        demo_dataset_info()
    else:
        asyncio.run(demo_with_sample_data())
