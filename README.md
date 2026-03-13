# FRAPH

Financial Fraud Detection using Graph Neural Networks.

## Features

- Upload transaction dataset
- Graph visualization of transactions
- Fraud detection using Graph Neural Networks
- Comparison with traditional ML models
- Interactive UI

## Tech Stack

Frontend
- React
- Three.js
- D3.js
- TailwindCSS

Backend
- Python
- PyTorch Geometric
- NetworkX
- FastAPI

## Project Structure
fraph/
│
├── frontend/                      # Website UI
│   ├── public/
│   ├── src/
│   │   ├── components/            # React components
│   │   │   ├── GraphView.jsx
│   │   │   ├── DatasetUpload.jsx
│   │   │   ├── FraudResults.jsx
│   │   │   └── ParticleBackground.jsx
│   │   │
│   │   ├── pages/
│   │   │   ├── Home.jsx
│   │   │   ├── Visualization.jsx
│   │   │   └── CompareModels.jsx
│   │   │
│   │   ├── utils/
│   │   │   └── api.js
│   │   │
│   │   ├── App.jsx
│   │   └── main.jsx
│   │
│   ├── package.json
│   └── vite.config.js
│
│
├── backend/                       # API + ML pipeline
│   │
│   ├── api/
│   │   └── server.py              # FastAPI / Flask API
│   │
│   ├── ml/
│   │   ├── train_gnn.py
│   │   ├── detect_fraud.py
│   │   └── traditional_models.py
│   │
│   ├── graph/
│   │   ├── build_graph.py
│   │   └── graph_features.py
│   │
│   └── utils/
│       ├── preprocess.py
│       └── dataset_loader.py
│
│
├── models/                        # Saved models
│   ├── gnn_model.pth
│   ├── random_forest.pkl
│   └── logistic_regression.pkl
│
│
├── datasets/                      # Fraud datasets
│   ├── raw/
│   └── processed/
│
│
├── notebooks/                     # Experiments
│   ├── data_analysis.ipynb
│   └── gnn_experiments.ipynb
│
│
├── visualizations/                # Graph outputs / screenshots
│   └── fraud_graph_example.png
│
│
├── docs/                          # Documentation
│   ├── architecture.md
│   ├── gnn_explanation.md
│   └── results.md
│
│
├── requirements.txt               # Python dependencies
├── .gitignore
└── README.md
## Author
Satwik Vangala
