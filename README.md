# Data Policy Compliance Agent

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-dashboard-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-frontend-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)

<a href="https://github.com/StoicDevansh/Data-Policy-Compliance-Agent">
  <img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&size=20&pause=1000&color=009688&center=true&vCenter=true&width=650&lines=Ingest+policies;Scan+data+for+violations;Review+and+report+compliance+findings" alt="Data Policy Compliance Agent">
</a>

</div>

Data Policy Compliance Agent ingests policy documents, extracts compliance rules,
scans connected databases, explains violations, and exposes the results through a
FastAPI service and Next.js dashboard.

<div align="center">
  <img src="https://github-readme-stats.vercel.app/api/pin/?username=StoicDevansh&repo=Data-Policy-Compliance-Agent&theme=transparent" alt="Repository statistics">
</div>

## What is included

- PDF and Markdown policy ingestion with rule extraction.
- SQLite, PostgreSQL, MySQL, and MongoDB connection support.
- Rule-based violation detection with explanations and remediation suggestions.
- Human review and approval workflow.
- Scheduled monitoring and compliance reports in JSON or HTML.
- Synthetic AML, PaySim, and employee-compliance datasets for local demos.
- FastAPI endpoints under `/api` and a Next.js dashboard in `frontend/`.

## Project layout

```text
.
├── src/
│   ├── api/          FastAPI routes and request models
│   ├── core/         Agent orchestration and settings
│   ├── database/     Connectors, schema scanning, and initialization
│   ├── datasets/     Sample data and optional Kaggle dataset loading
│   ├── detection/    Violation engine and explanations
│   ├── ingestion/    PDF parsing and rule extraction
│   ├── monitoring/   Scheduled scans
│   ├── reporting/    Compliance report generation
│   └── review/       Human review workflow
├── data/
│   ├── policies/     Included policy examples
│   ├── rules/        Pre-configured compliance rules
│   ├── sample/       Generated sample datasets
│   └── reports/      Generated reports
├── examples/         Local demo scripts
├── frontend/         Next.js dashboard
├── requirements.txt
└── vercel.json
```

## Backend setup

The backend targets Python 3.10. Create and activate a virtual environment, then
install the pinned dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Set `OPENAI_API_KEY` if LLM-backed extraction or explanations are enabled. The
application otherwise uses its configured local/default behavior. Optional
settings can be supplied through `config.yaml` or `DAP_*` environment variables;
do not commit secrets or that file.

Initialize the local database and start the API:

```powershell
python -m src.database.init_db
python -m src.main
```

The API is available at `http://localhost:8000`; interactive documentation is at
`http://localhost:8000/docs`.

## Local demo

Generate the included synthetic datasets and run the analysis demo:

```powershell
python -m src.datasets.init_datasets
python examples/hackfest_demo.py
```

Downloading the optional Kaggle datasets requires a configured Kaggle API token:

```powershell
python -m src.datasets.init_datasets --download
```

## API endpoints

The service is mounted under `/api`. The main workflow is:

1. `POST /api/database/demo` - create and connect the demo database.
2. `POST /api/rules/load` - load the bundled compliance rules.
3. `POST /api/scan` - run a compliance scan.
4. `GET /api/violations` - list detected violations.
5. `POST /api/violations/{violation_id}/review` - record a review decision.
6. `POST /api/reports` - generate a report.
7. `GET /api/dashboard` - retrieve dashboard metrics.

Additional health, policy, database, rule, dataset, and analysis endpoints are
listed in the OpenAPI documentation.

## Dashboard

Install and run the frontend separately:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. The dashboard expects the API at
`http://localhost:8000`; configure the frontend API base URL using the existing
frontend environment configuration when deploying elsewhere.

## Configuration and data

Bundled policy documents are in `data/policies/`, and the rule definitions are
in `data/rules/compliance_rules.json`. Generated databases and reports are local
runtime artifacts. Never add API keys, database passwords, or downloaded private
datasets to version control.

## License

No license file is currently included in this repository. Add a license before
redistributing the project.
