# Final Comparison Table

Primary source: [`fraph-backend/outputs/20260330121604-fraud_data_kaggle_sample/summary_metrics.csv`](/home/satwik/fraph/fraph-backend/outputs/20260330121604-fraud_data_kaggle_sample/summary_metrics.csv)

Evaluation setting:

- dataset: `fraud_data_kaggle_sample.csv`
- protocol: `3-fold stratified cross-validation`
- repeats: `1`
- seed: `42`
- GNN config: `epochs=5`, `hidden_dim=32`, `learning_rate=0.01`, `dropout=0.2`, similarity edges on, party edges on, class weights on

| Model | Precision | Recall | F1 | ROC-AUC | PR-AUC | MCC |
| --- | --- | --- | --- | --- | --- | --- |
| Random Forest | 0.9864 +- 0.0236 | 0.8980 +- 0.0736 | 0.9385 +- 0.0343 | 0.9823 +- 0.0160 | 0.9515 +- 0.0242 | 0.9401 +- 0.0320 |
| GNN | 0.1856 +- 0.0569 | 0.7211 +- 0.1124 | 0.2906 +- 0.0693 | 0.8476 +- 0.0260 | 0.3185 +- 0.0757 | 0.3184 +- 0.0597 |
| Linear SVC | 0.7612 +- 0.2069 | 0.1565 +- 0.0624 | 0.2506 +- 0.0756 | 0.8910 +- 0.0093 | 0.2050 +- 0.0580 | 0.3331 +- 0.0416 |
| Logistic Regression | 0.8144 +- 0.1875 | 0.1292 +- 0.0472 | 0.2202 +- 0.0693 | 0.8878 +- 0.0130 | 0.2173 +- 0.0529 | 0.3191 +- 0.0676 |
| KNN | 0.7222 +- 0.2546 | 0.1360 +- 0.0965 | 0.2175 +- 0.1277 | 0.8095 +- 0.0357 | 0.2984 +- 0.0191 | 0.2986 +- 0.1158 |

## Ranking Notes

- Best overall model on the current dataset: `Random Forest`
- Best recall among strong non-trivial models: `GNN`
- Best current FRAPH GNN settings: `epochs=5`, `hidden_dim=32`, `learning_rate=0.01`, `dropout=0.2`

## Important Caution

Earlier sweep and ablation artifacts include runs from an older GNN variant. Use the table above as the current main comparison because it comes from the post-upgrade unified benchmark where all models were measured under the same evaluation protocol.
