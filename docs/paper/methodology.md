# Draft Methodology

## Problem Setting

The task is binary fraud classification on transaction-level data. Each record is classified as either legitimate or fraudulent. Because fraud datasets are highly imbalanced, the evaluation emphasizes threshold-sensitive and imbalance-aware metrics rather than relying on accuracy alone.

## Dataset Preparation

FRAPH currently targets transaction CSV datasets and is especially compatible with PaySim-like data. The preprocessing pipeline standardizes column aliases into a canonical schema with fields for transaction amount, sender, receiver, transaction type, temporal step, balance changes, and fraud label. Missing aliases are resolved where possible, and labeled subsets are extracted for model comparison.

## Feature Engineering

For the traditional machine learning models, the system builds a numeric feature frame from transaction-level attributes such as amount, balance transitions, and derived transaction indicators. These features are used directly by `KNN`, `Logistic Regression`, `Linear SVC`, and `Random Forest`.

For the GNN, the same canonicalized transaction records are transformed into node features and a transaction graph. Each transaction is treated as a node. Graph edges are introduced through two mechanisms:

- feature-similarity edges between numerically similar transactions
- party-based edges linking transactions that share sender or receiver entities

Node features are standardized before graph learning.

## Proposed GNN

The proposed FRAPH GNN is a graph convolutional network with three graph-convolution layers and intermediate batch normalization. ReLU activation and dropout are applied between hidden layers. The model uses class-weighted cross-entropy to mitigate label imbalance during training. The final configuration used for the current main benchmark is:

- `epochs=5`
- `hidden_dim=32`
- `learning_rate=0.01`
- `dropout=0.2`
- similarity edges enabled
- party edges enabled
- class weighting enabled

## Baseline Models

The evaluation includes four traditional machine learning baselines:

- `KNN`
- `Logistic Regression`
- `Linear SVC`
- `Random Forest`

These were selected to cover neighborhood-based, linear, margin-based, and ensemble-tree approaches.

## Evaluation Protocol

All models are evaluated using the same repeated stratified split procedure. For the current unified benchmark used in the draft comparison table, the configuration is:

- `3-fold stratified cross-validation`
- `1 repeat`
- fixed random seed `42`

The framework also supports larger repeated evaluations, hyperparameter sweeps, and GNN ablations through the experiment scripts in [`fraph-backend/experiments`](/home/satwik/fraph/fraph-backend/experiments).

## Metrics

The reported metrics are:

- Accuracy
- Precision
- Recall
- F1-score
- ROC-AUC
- PR-AUC
- Matthews Correlation Coefficient

PR-AUC and MCC are included because they are more informative than raw accuracy for imbalanced fraud data.
