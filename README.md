# FRAPH

FRAPH is a fraud-analysis workspace with a React frontend and a FastAPI backend. It accepts transaction CSV files, builds graph summaries, runs fraud scoring, compares traditional ML models, and trains a first GNN baseline for transaction-network classification.

## What It Does

- Upload a transaction dataset from the browser
- Analyze suspicious transactions and network structure
- Visualize graph activity on the dashboard
- Compare `KNN`, `Logistic Regression`, `Linear SVC`, `Random Forest`, and `GNN`
- Train and persist model artifacts under `fraph-backend/trained_models`

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

## Cross-Platform Setup

The project is structured to work on both Windows and Linux without OS-specific code paths. Use:

- Node.js 20+ for the frontend
- Python 3.11 or 3.12 for the backend
- CPU PyTorch install path by default, so machines without CUDA do not pull GPU wheels

### 1. Clone And Install Frontend

```bash
npm install
```

### 2. Create Frontend Env

Copy [`.env.example`](/home/satwik/fraph/.env.example) to `.env` and adjust only if your backend is not on port `8000`.

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

### 3. Create Backend Virtual Environment

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

### 4. Install Backend Dependencies

Install the base backend stack first:

```bash
pip install -r requirements-base.txt
```

Then install CPU PyTorch:

```bash
pip install --index-url https://download.pytorch.org/whl/cpu -r requirements-cpu.txt
```

This split is intentional. It avoids accidentally downloading CUDA packages on Windows/Linux systems that only need CPU execution.

### 5. Optional Backend Env

Copy [`fraph-backend/.env.example`](/home/satwik/fraph/fraph-backend/.env.example) to `fraph-backend/.env` if you want to customize the backend name or database location.

```env
FRAPH_APP_NAME=Fraph Backend
FRAPH_DATABASE_URL=sqlite:///./fraph.db
```

## Running The Project

### Start Backend

After activating the backend virtual environment:

```bash
cd fraph-backend
python run_backend.py
```

If port `8000` is already used on your machine, run uvicorn manually on another port:

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

If you do that, update `VITE_API_BASE_URL` in your frontend `.env`.

### Start Frontend

From the repo root:

```bash
npm run dev
```

Open the Vite URL shown in the terminal, usually `http://127.0.0.1:5173`.

## Dataset Tutorial

### Recommended Dataset

Use the PaySim transaction fraud dataset for the best current experience in this repo because it contains sender, receiver, amount, balance, and label fields that match the backend pipeline.

Expected useful columns include:

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

### How To Download

You can download PaySim from a public mirror:

- Public mirror used during testing: `https://storage.googleapis.com/ml-design-patterns/fraud_data_kaggle.csv`

Linux:

```bash
curl -L https://storage.googleapis.com/ml-design-patterns/fraud_data_kaggle.csv -o fraph-backend/datasets/fraud_data_kaggle.csv
```

Windows PowerShell:

```powershell
Invoke-WebRequest https://storage.googleapis.com/ml-design-patterns/fraud_data_kaggle.csv -OutFile fraph-backend\datasets\fraud_data_kaggle.csv
```

You can also download a smaller sample yourself if you do not want to upload the full file through the browser.

## How To Use The App

### 1. Upload A Dataset

1. Start the backend and frontend.
2. Open the home page.
3. Click `Analyze Network`.
4. On the upload page, choose a CSV file.
5. Click `RUN FRAUD ANALYSIS`.

The file is sent to `/upload/`, stored under `fraph-backend/datasets`, and indexed in SQLite.

### 2. View Dashboard Results

After upload, the dashboard automatically calls `/fraud/detect` and shows:

- transactions analyzed
- suspicious transaction count
- average risk score
- graph summary
- suspicious transaction table

### 3. Open Model Comparison

From the dashboard, open the comparison page. It calls `/compare/` and displays:

- KNN
- Logistic Regression
- Linear SVC
- Random Forest
- GNN

### 4. Train And Persist Models

On the comparison page, click `Train And Save Models`.

That calls `/train/` and stores artifacts under:

- `fraph-backend/trained_models/<dataset-name>/`

Saved artifacts include:

- `.joblib` files for traditional models
- `.pt` file for the GNN

## Current Backend Endpoints

- `GET /`
- `GET /upload/datasets`
- `POST /upload/`
- `POST /fraud/detect`
- `POST /compare/`
- `POST /train/`
- `GET /train/artifacts/{dataset_id}`

## Notes On Portability

This repo avoids hardcoded OS-specific path logic in the application code. For best portability:

- use `python run_backend.py` or `python -m uvicorn ...` instead of shell-specific wrappers
- keep frontend API configuration in `.env`
- use the CPU PyTorch install path unless you explicitly need GPU support
- do not commit generated datasets, virtual environments, local SQLite DBs, or trained artifacts

## Verification Commands

Frontend:

```bash
npm run lint
npm run build
```

Backend:

```bash
python -m compileall app
```

## Author

Satwik Vangala
