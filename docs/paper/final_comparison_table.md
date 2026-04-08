# Final Comparison Table

One representative comparison is kept per dataset. For each selected run, the strongest non-GNN baseline and the strongest GNN-family model are shown. For `fraud_data_kaggle_sample.csv`, the selected source is the documented unified benchmark used in the draft paper. For the `tmp` benchmark datasets, the only available comparable run is used.

| Dataset | Run | Protocol | Best Baseline | Best GNN | Baseline F1 | GNN F1 | Baseline PR-AUC | GNN PR-AUC | Baseline Recall | GNN Recall | GNN Threshold |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fraud_data_kaggle_sample.csv | 20260330121604-fraud_data_kaggle_sample | 3-fold, seed 42 | Random Forest | GNN | 0.9385 +- 0.0343 | 0.2906 +- 0.0693 | 0.9515 +- 0.0242 | 0.3185 +- 0.0757 | 0.8980 +- 0.0736 | 0.7211 +- 0.1124 | n/a |
| tmp/fraph_benchmark_slice.csv | 20260330163424-fraph_benchmark_slice | 2-fold, seed 42 | Random Forest | GNN | 0.3000 +- 0.1414 | 0.3126 +- 0.1727 | 0.7556 +- 0.1194 | 0.2690 +- 0.0526 | 0.1805 +- 0.0982 | 0.4236 +- 0.2848 | n/a |
| tmp/fraph_benchmark_tiny.csv | 20260330163953-fraph_benchmark_tiny | 2-fold, seed 42 | Random Forest | GNN | 0.5000 +- 0.7071 | 0.0040 +- 0.0001 | 1.0000 +- 0.0000 | 0.0857 +- 0.1145 | 0.5000 +- 0.7071 | 1.0000 +- 0.0000 | n/a |
