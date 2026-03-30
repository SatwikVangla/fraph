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

## Paper Evaluation Workflow

If your goal is a paper, do not rely on a single dashboard run. Use the experiment runner in `fraph-backend/experiments` so every model is evaluated on the same repeated stratified splits.

### Recommended Metrics

For fraud datasets, report all of these:

- Accuracy
- Precision
- Recall
- F1-score
- ROC-AUC
- PR-AUC
- MCC
- Confusion matrix values: `TN`, `FP`, `FN`, `TP`

### Run A Full Benchmark

After activating the backend virtual environment:

```bash
cd fraph-backend
python -m experiments.run_benchmark --dataset datasets/fraud_data_kaggle_sample.csv
```

That command runs repeated stratified cross-validation for:

- KNN
- Logistic Regression
- Linear SVC
- Random Forest
- GNN

### Run A GNN Hyperparameter Sweep

Use this when you want to tune the proposed GNN before writing your final comparison table:

```bash
cd fraph-backend
python -m experiments.run_gnn_sweep --dataset datasets/fraud_data_kaggle_sample.csv
```

This evaluates multiple combinations of:

- epochs
- hidden dimension
- learning rate
- dropout

Outputs are written to:

- `fraph-backend/outputs/<dataset>-gnn-sweep/`

Important file:

- `sweep_results.csv`

Use that file to pick the best GNN configuration by `f1_mean`, `pr_auc_mean`, and `roc_auc_mean`.

### Run GNN Ablation Experiments

Use this when you want to justify your GNN design in the paper:

```bash
cd fraph-backend
python -m experiments.run_gnn_ablation --dataset datasets/fraud_data_kaggle_sample.csv
```

The current ablations compare:

- full GNN
- no similarity edges
- no party edges
- no class weighting

Outputs are written to:

- `fraph-backend/outputs/<dataset>-gnn-ablation/`

Important file:

- `ablation_results.csv`

### Generate A Paper-Ready Results Report

After running the benchmark, generate paper-friendly tables:

```bash
cd fraph-backend
python -m experiments.generate_paper_report \
  --summary outputs/<run-folder>/summary_metrics.csv \
  --output outputs/paper_report
```

This produces:

- `ranked_summary.csv`
- `paper_table.csv`
- `paper_table.tex`
- `paper_report.md`

Default experiment settings:

- `5` folds
- `3` repeats
- fixed random seed

### Customize The Benchmark

Example with custom folds, repeats, and GNN settings:

```bash
python -m experiments.run_benchmark \
  --dataset datasets/fraud_data_kaggle_sample.csv \
  --folds 5 \
  --repeats 3 \
  --models knn logistic_regression linear_svc random_forest gnn \
  --gnn-epochs 30 \
  --gnn-hidden-dim 32 \
  --gnn-learning-rate 0.01
```

Windows PowerShell example:

```powershell
python -m experiments.run_benchmark `
  --dataset datasets/fraud_data_kaggle_sample.csv `
  --folds 5 `
  --repeats 3 `
  --models knn logistic_regression linear_svc random_forest gnn `
  --gnn-epochs 30 `
  --gnn-hidden-dim 32 `
  --gnn-learning-rate 0.01
```

### Experiment Outputs

Each run writes a timestamped folder under:

- `fraph-backend/outputs/`

The output folder contains:

- `fold_metrics.csv`
- `fold_metrics.json`
- `summary_metrics.csv`
- `summary_metrics.md`
- `run_config.json`
- `plots/<model>_pr_curve.png`
- `plots/<model>_roc_curve.png`
- `plots/<model>_confusion_matrix.png`

### How To Read The Results

For paper tables, use `summary_metrics.csv` or `summary_metrics.md`.

Interpretation:

- `accuracy_mean` and `accuracy_std`: average accuracy and variability
- `f1_mean`: better than accuracy for imbalanced fraud data
- `pr_auc_mean`: especially important when fraud cases are rare
- `mcc_mean`: balanced signal even under heavy class imbalance

For your paper, the main comparison table should usually report:

- `Precision`
- `Recall`
- `F1`
- `ROC-AUC`
- `PR-AUC`
- `MCC`

Accuracy can still be included, but it should not be your main argument on imbalanced data.

## Working With Different Dataset Types

The current pipeline is strongest on transaction datasets with:

- sender/source account
- receiver/destination account
- transaction amount
- fraud label

### Supported Best

PaySim-style datasets:

- `nameOrig`
- `nameDest`
- `amount`
- `type`
- `step`
- `oldbalanceOrg`
- `newbalanceOrig`
- `oldbalanceDest`
- `newbalanceDest`
- `isFraud`

This is the best option for:

- dashboard graph quality
- classical model comparison
- current GNN baseline

### Also Supported

Generic labeled transaction CSVs can still work if they at least provide:

- sender/source column
- receiver/target column
- amount/value column
- fraud label column

If balances or transaction type are missing, the pipeline still runs, but model quality may drop.

### Weak Fit

Purely tabular fraud datasets with no sender/receiver structure can still be used for classical ML benchmarking, but:

- graph visualization becomes weak
- the GNN becomes much less meaningful
- the paper claim becomes more about tabular fraud detection than graph learning

### Inspect A New Dataset Before Training

Use the dataset inspector first:

```bash
cd fraph-backend
python -m experiments.inspect_dataset --dataset path/to/your_dataset.csv
```

It reports:

- detected columns
- whether the dataset is dashboard-ready
- whether it is comparison-ready
- whether it looks PaySim-like

### Quick Decision Rule For New Datasets

Use these rules before running expensive experiments:

- If the dataset has `sender`, `receiver`, `amount`, and a fraud label:
  good candidate for both classical models and the current GNN
- If the dataset has only tabular features and a label:
  good for classical ML, weak for graph claims
- If the dataset is graph-native but not CSV-shaped:
  useful for future GNN work, but it likely needs a custom loader first

## Suggested Research Setup

If you want publishable results, use this sequence:

1. Run the experiment runner on PaySim and save the summary table.
2. Tune the GNN with ablations:
   - hidden dimension
   - learning rate
   - epochs
   - graph construction strategy
   - class-weighted vs unweighted loss
3. Compare the tuned GNN against the same traditional baselines.
4. Add a second dataset if possible, especially a more graph-native one.
5. Include mean ± std across repeated folds in the paper.

## Practical Advice For Your Paper

- Do not claim superiority from a single split.
- Do not rely on accuracy alone.
- Include PR-AUC and MCC.
- Report the exact dataset size, fraud ratio, and preprocessing assumptions.
- Freeze seeds and experiment settings before writing the final table.
- Keep one final held-out setup if you want a cleaner final result beyond CV summaries.

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
