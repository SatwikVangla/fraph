# Paper Pack

This folder collects the current paper-oriented assets for FRAPH:

- [`abstract.md`](/home/satwik/fraph/docs/paper/abstract.md)
- [`methodology.md`](/home/satwik/fraph/docs/paper/methodology.md)
- [`results.md`](/home/satwik/fraph/docs/paper/results.md)
- [`final_comparison_table.md`](/home/satwik/fraph/docs/paper/final_comparison_table.md)
- [`figure_checklist.md`](/home/satwik/fraph/docs/paper/figure_checklist.md)

## Current Recommended GNN Configuration

Use the current improved GNN configuration below as the main reported FRAPH GNN setup:

- `epochs=5`
- `hidden_dim=32`
- `learning_rate=0.01`
- `dropout=0.2`
- `use_similarity_edges=true`
- `use_party_edges=true`
- `use_class_weights=true`

This is the configuration used in the unified benchmark run stored under [`fraph-backend/outputs/20260330121604-fraud_data_kaggle_sample`](/home/satwik/fraph/fraph-backend/outputs/20260330121604-fraud_data_kaggle_sample). It should be treated as the main comparison source because all models were evaluated under the same split configuration there.

## Reproduce The Main Comparison

From [`fraph-backend`](/home/satwik/fraph/fraph-backend):

```bash
python -m experiments.inspect_dataset --dataset datasets/fraud_data_kaggle_sample.csv
python -m experiments.run_benchmark --dataset datasets/fraud_data_kaggle_sample.csv --folds 3 --repeats 1 --gnn-epochs 5
python -m experiments.generate_paper_report --summary outputs/<run-folder>/summary_metrics.csv --output outputs/paper_report
```

## Run GNN Hyperparameter Checks

```bash
python -m experiments.run_gnn_sweep --dataset datasets/fraud_data_kaggle_sample.csv --folds 3 --repeats 1
```

Use the sweep to compare candidate settings, but keep the architecture version in mind. Earlier saved sweep outputs were generated before the latest GNN upgrade. For a final paper submission, rerun the sweep after any major GNN architecture change.

## Run GNN Ablations

```bash
python -m experiments.run_gnn_ablation --dataset datasets/fraud_data_kaggle_sample.csv --folds 3 --repeats 1 --gnn-epochs 5 --gnn-hidden-dim 32
```

## How To Work With Different Datasets

### Best Fit

Transaction CSVs with:

- sender identifier
- receiver identifier
- transaction amount
- fraud label

Examples:

- PaySim-like mobile money data
- bank-transfer transaction logs with party identifiers
- e-commerce payment graphs with payer and payee ids

### Classical-Only Friendly

Labeled tabular fraud data without sender and receiver fields can still be used for:

- `KNN`
- `Logistic Regression`
- `Linear SVC`
- `Random Forest`

But the graph pipeline will be weaker because it cannot build meaningful entity relationships.

### Better For A Stronger GNN Paper

Graph-native datasets are better if the core paper claim is that the proposed GNN outperforms classical baselines. For FRAPH, the next high-value dataset is:

- Elliptic Bitcoin transaction dataset

That will require a custom loader because it is distributed across multiple files and already encodes graph structure.

## Publication Guidance

Use the current artifacts for:

- a system paper
- an implementation paper
- a baseline comparison paper

Do not yet claim that the proposed GNN is state of the art or stronger than the classical models on PaySim. The current evidence shows the GNN is a meaningful research baseline, but `Random Forest` is still the strongest model on the tested PaySim sample.
