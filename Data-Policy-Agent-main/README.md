# Data Policy Agent (DAP)

A comprehensive software solution that ingests PDF policy documents and monitors company databases for compliance violations.

## 🎯 Features

- **PDF Policy Ingestion**: Extract actionable compliance rules from unstructured policy documents
- **Database Scanning**: Connect to various databases and scan for policy violations
- **Explainable Violations**: Flag violations with clear, detailed justifications
- **Human Review Workflow**: Incorporate human oversight during data analysis
- **Periodic Monitoring**: Schedule automated compliance checks
- **Remediation Suggestions**: AI-powered recommendations for fixing violations
- **Dashboard & Reporting**: Visual compliance status and audit-ready reports

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Data Policy Agent                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │   PDF        │  │   Rule       │  │   Database           │  │
│  │   Ingestion  │──▶│   Extraction │──▶│   Connector         │  │
│  │   Module     │  │   Engine     │  │                      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│         │                  │                    │                │
│         ▼                  ▼                    ▼                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │   Policy     │  │   Compliance │  │   Violation          │  │
│  │   Store      │◀─│   Rules DB   │──▶│   Detection Engine   │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                            │                    │                │
│                            ▼                    ▼                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │   Scheduler  │──▶│   Human      │──▶│   Dashboard &        │  │
│  │   (Periodic) │  │   Review     │  │   Reporting          │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 📦 Installation

```bash
# Clone or navigate to project
cd DAP

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -m src.database.init_db

# Run the application
python -m src.main
```

## 🚀 Quick Start

```python
from src.core.agent import DataPolicyAgent

# Initialize the agent
agent = DataPolicyAgent()

# Ingest a policy document
agent.ingest_policy("policies/privacy_policy.pdf")

# Connect to database
agent.connect_database({
    "type": "postgresql",
    "host": "localhost",
    "database": "company_db",
    "user": "admin",
    "password": "your_password"
})

# Scan for violations
violations = agent.scan_for_violations()

# Generate report
agent.generate_report(violations, output="compliance_report.pdf")
```

## � HackFest 2.0 Dataset Integration

This project integrates the recommended datasets from HackFest 2.0 (GDG Cloud New Delhi × Turgon):

### Recommended Datasets

| Dataset                            | License          | Description                                             |
| ---------------------------------- | ---------------- | ------------------------------------------------------- |
| **IBM AML Transactions** (Primary) | CDLA-Sharing 1.0 | Synthetic financial transactions with laundering labels |
| **PaySim Financial Dataset**       | CC BY-SA 4.0     | 6.3M mobile money transactions with fraud indicators    |
| **Employee Compliance Dataset**    | Community        | HR policy compliance data (attendance, training, leave) |

### Quick Start with Sample Data

```bash
# Generate synthetic sample data (no download required)
python -m src.datasets.init_datasets

# Run analysis demo
python examples/hackfest_demo.py

# Or download actual Kaggle datasets (requires API key)
python -m src.datasets.init_datasets --download
```

### Policy Documents Included

- `data/policies/aml_compliance_policy.md` - Anti-Money Laundering rules
- `data/policies/fraud_detection_policy.md` - Fraud detection policies
- `data/policies/employee_compliance_policy.md` - HR compliance rules
- `data/policies/gdpr_data_protection_policy.md` - GDPR/data protection

### Pre-configured Compliance Rules

Rules in `data/rules/compliance_rules.json`:

- **AML Rules**: Large transaction reporting, structuring detection, velocity monitoring
- **Fraud Rules**: Transaction amount thresholds, balance anomalies, fraud flags
- **Employee Rules**: Attendance monitoring, training compliance, leave policy

## 📁 Project Structure

```
DAP/
├── src/
│   ├── core/
│   │   ├── agent.py           # Main agent orchestrator
│   │   └── config.py          # Configuration management
│   ├── datasets/              # HackFest 2.0 dataset integration
│   │   ├── loader.py          # Dataset downloader/loader
│   │   ├── sample_data.py     # Synthetic data generator
│   │   └── init_datasets.py   # Initialization script
│   ├── ingestion/
│   │   ├── pdf_parser.py      # PDF text extraction
│   │   └── rule_extractor.py  # NLP-based rule extraction
│   ├── database/
│   │   ├── connector.py       # Multi-database connector
│   │   ├── scanner.py         # Database scanning logic
│   │   └── init_db.py         # Database initialization
│   ├── detection/
│   │   ├── violation_engine.py # Violation detection
│   │   └── explainer.py       # Violation explanations
│   ├── review/
│   │   ├── workflow.py        # Human review workflow
│   │   └── approvals.py       # Approval management
│   ├── monitoring/
│   │   ├── scheduler.py       # Periodic monitoring
│   │   └── alerts.py          # Alert notifications
│   ├── reporting/
│   │   ├── dashboard.py       # Web dashboard
│   │   ├── reports.py         # Report generation
│   │   └── templates/         # Report templates
│   ├── api/
│   │   └── routes.py          # REST API endpoints
│   └── main.py                # Application entry point
├── data/
│   ├── policies/              # Policy documents (Markdown/PDF)
│   ├── rules/                 # Compliance rules (JSON)
│   ├── datasets/              # Downloaded Kaggle datasets
│   └── sample/                # Generated sample data
├── examples/
│   └── hackfest_demo.py       # Demo script
├── tests/                     # Unit tests
├── requirements.txt           # Python dependencies
└── README.md
```

## 🔧 Configuration

Create a `.env` file or use `config.yaml`:

```yaml
# config.yaml
database:
  type: postgresql # or mysql, sqlite, mongodb
  host: localhost
  port: 5432
  name: company_db

monitoring:
  enabled: true
  interval: 3600 # seconds

llm:
  provider: openai # or local, anthropic
  model: gpt-4
  api_key: ${OPENAI_API_KEY}

dashboard:
  host: 0.0.0.0
  port: 8080
```

## 📊 API Endpoints

| Endpoint                      | Method | Description                |
| ----------------------------- | ------ | -------------------------- |
| `/api/policies`               | POST   | Upload policy document     |
| `/api/policies`               | GET    | List all policies          |
| `/api/rules`                  | GET    | List extracted rules       |
| `/api/scan`                   | POST   | Trigger compliance scan    |
| `/api/violations`             | GET    | List detected violations   |
| `/api/violations/{id}/review` | POST   | Submit review decision     |
| `/api/reports`                | POST   | Generate compliance report |
| `/api/dashboard`              | GET    | Dashboard metrics          |

## 📜 License

MIT License
