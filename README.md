# FRAPH

FRAPH is a fraud-analysis workspace with a React frontend and a FastAPI backend. It accepts transaction CSV files, builds graph summaries, runs fraud scoring, and compares simpler non-graph baselines against a relationship-aware GNN that models users, counterparties, and transactions as a connected system. It also includes async training jobs, experiment history, downloadable reports, diagnostics, and richer model evaluation.

The repo is intended to run on both Linux and Windows. The application code avoids OS-specific paths, and the benchmark runner now uses the system temp directory instead of a Linux-only `/tmp` path.

## Current Capabilities

- Upload transaction CSV datasets and store them in SQLite-backed project state
- Accept broader CSV formats through delimiter sniffing and flexible column inference
- Let you override sender, receiver, amount, label, type, and time mappings at upload time
- Show upload validation before analysis:
  - mapping confidence
  - graph-readiness assessment
  - required versus optional field coverage
- Run fraud analysis with graph summaries and suspicious-transaction scoring
- Compare `KNN`, `Logistic Regression`, `Linear SVC`, `Gaussian Naive Bayes`, and `GNN`
- Emphasize graph-based fraud learning through user-to-user and user-to-transaction relationships rather than row-wise scoring alone
- Show richer evaluation metrics:
  - Accuracy
  - Precision
  - Recall
  - F1-score
  - ROC-AUC
  - PR-AUC
  - MCC
  - Confusion matrix values: `TN`, `FP`, `FN`, `TP`
  - GNN threshold and validation score
- Surface dataset diagnostics:
  - class imbalance
  - duplicate transaction IDs
  - missing values
  - self-loop volume
  - warning messages
- Persist model artifacts and training history
- Run async training jobs with progress polling
- Download markdown model reports generated after training
- Cache comparison results so the comparison page loads more reliably
- Show explainability payloads for classical baselines and GNN variants

## Stack

Frontend
- React
- Vite
- Tailwind CSS
- tsParticles

Backend
- FastAPI
- SQLAlchemy
- pandas
- scikit-learn
- NetworkX
- PyTorch
- torch-geometric
- matplotlib

## Repository Layout

```text
fraph/
├── fraph-backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routes/
│   │   ├── services/
│   │   ├── schemas/
│   │   ├── database/
│   │   └── utils/
│   ├── datasets/
│   ├── trained_models/
│   ├── requirements-base.txt
│   ├── requirements-cpu.txt
│   └── run_backend.py
├── src/
│   ├── components/
│   ├── pages/
│   └── utils/
├── public/
├── package.json
└── README.md
```

## Setup

Use:

- Node.js 20+
- Python 3.11 or 3.12

### Frontend

```bash
npm install
```

Windows PowerShell is also fine here:

```powershell
npm install
```

Create `.env` from `.env.example`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

### Backend

Linux:

```bash
cd fraph-backend
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
cd fraph-backend
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements-base.txt
pip install --index-url https://download.pytorch.org/whl/cpu -r requirements-cpu.txt
```

Windows PowerShell uses the same commands after activating the virtual environment.

Optional backend `.env`:

```env
FRAPH_APP_NAME=Fraph Backend
FRAPH_DATABASE_URL=sqlite:///./fraph.db
```

## Run

Backend:

```bash
cd fraph-backend
python run_backend.py
```

Frontend:

```bash
npm run dev
```

Windows PowerShell:

```powershell
npm run dev
```

## API Surfaces

Core routes:

- `POST /upload/`
- `GET /upload/datasets`
- `POST /fraud/detect`
- `POST /compare/`
- `POST /train/`
- `POST /train/jobs`
- `GET /train/jobs/{job_id}`
- `GET /train/artifacts/{dataset_id}`
- `GET /train/reports/{artifact_id}`
- `POST /benchmark/jobs`
- `GET /benchmark/jobs/{job_id}`
- `GET /benchmark/runs/{dataset_id}`

### Compare Behavior

`/compare/` now prefers:

1. cached comparison results for the dataset
2. persisted artifacts for the dataset
3. fresh computation only for missing models

That makes the comparison page less likely to stall or fail because one model is slow.
The intended project framing is GNN versus simpler non-graph baselines, not GNN versus every possible strongest tabular ensemble.

### Async Training Behavior

`POST /train/jobs` creates a background training job and returns a `job_id`.

Poll it with:

```bash
GET /train/jobs/{job_id}
```

The frontend comparison page uses this job flow automatically.

### Benchmark And Experiment History

`POST /benchmark/jobs` runs a repeated-stratified benchmark in the background and persists an experiment run record in SQLite.

The benchmark history for a dataset is available from:

```bash
GET /benchmark/runs/{dataset_id}
```

Each benchmark run stores:

- output root path
- summary table payload
- benchmark config
- run status

## Training Outputs

Saved under:

```text
fraph-backend/trained_models/<dataset-name>/
```

Outputs include:

- `.joblib` files for classical models
- `.pt` file for GNN artifacts
- `.md` report files
- `.json` report payloads
- `.png` metrics charts

## GNN Notes

The current GNN stack includes:

- transaction-account graph construction
- relationship-aware modeling across senders, receivers, counterparties, and transaction nodes
- richer graph-aware engineered features
- residual GraphSAGE layers
- GAT as a second graph architecture for benchmark comparisons
- threshold selection on validation data
- graph-structure and hyperparameter tuning
- temporal graph edges between nearby sender/receiver events
- multi-seed selection for more stable GNN runs
- configurable sampling presets:
  - `small`
  - `medium`
  - `large`
  - `full`

The training API accepts `sampling_preset` in `TrainingRequest`.

## Frontend Notes

The comparison page now shows:

- dataset diagnostics
- async training progress
- extended comparison metrics
- confusion matrix values
- selected config for tuned GNN runs
- top explainability features
- report download links for persisted runs

The backend diagnostics also include a leakage audit so you can inspect unusually label-correlated raw fields when a tabular model looks too good to trust blindly.

The upload page now also supports:

- CSV delimiter detection for preview
- manual column mapping
- upload-time graph-readiness validation
- transaction-table and graph bidirectional focus on the dashboard

## Recommended Dataset

PaySim still fits the pipeline best. Useful columns include:

- `step`
- `type`
- `amount`
- `nameOrig`
- `oldbalanceOrg`
- `newbalanceOrig`
- `nameDest`
- `oldbalanceDest`
- `newbalanceDest`
- `isFraud`

Public mirror used during testing:

- `https://storage.googleapis.com/ml-design-patterns/fraud_data_kaggle.csv`

Other useful datasets to test:

- `BankSim`: another transaction-oriented fraud dataset that is a reasonable fit for sender/receiver and merchant behavior
- `Elliptic Bitcoin Dataset`: stronger graph-native structure if you want a more relationship-heavy fraud story
- `IEEE-CIS Fraud Detection`: useful for broader fraud benchmarking, though less graph-centric
- `Credit Card Fraud Detection`: useful for baseline model checks, but weak for graph claims because sender/receiver structure is limited

Best-fit CSV shape for FRAPH:

- one source/sender entity column
- one destination/receiver entity column
- amount/value column
- time or event-order column
- optional fraud label column

If a CSV is purely generic tabular data with no entity relationship fields, FRAPH can still ingest it, but the graph and GNN become much less meaningful.

## Verification

Current verification run for this repo:

- `python3 -m compileall fraph-backend/app`
- `python3 -m compileall fraph-backend/experiments`
- `npm run build`

Both passed after the latest frontend and backend changes.

## Next Good Additions

If you want to take the project further, the highest-value next steps are:

- move background jobs from in-memory threads to a durable queue
- add SHAP-style explainability for the tabular models
- add node/subgraph attribution for the GNN
- export PDF reports in addition to markdown
- add seeded GNN ensembling for more stable metrics
- store experiment runs in first-class database tables instead of only artifact JSON
- add pagination and filtering to suspicious transactions and training history
