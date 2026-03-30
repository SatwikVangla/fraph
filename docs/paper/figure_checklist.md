# Figure Checklist

Use the plots from [`fraph-backend/outputs/20260330121604-fraud_data_kaggle_sample/plots`](/home/satwik/fraph/fraph-backend/outputs/20260330121604-fraud_data_kaggle_sample/plots) as the starting point for the paper figures.

## Recommended Main Figures

1. ROC curves for all models
   - [`random_forest_roc_curve.png`](/home/satwik/fraph/fraph-backend/outputs/20260330121604-fraud_data_kaggle_sample/plots/random_forest_roc_curve.png)
   - [`gnn_roc_curve.png`](/home/satwik/fraph/fraph-backend/outputs/20260330121604-fraud_data_kaggle_sample/plots/gnn_roc_curve.png)
   - [`linear_svc_roc_curve.png`](/home/satwik/fraph/fraph-backend/outputs/20260330121604-fraud_data_kaggle_sample/plots/linear_svc_roc_curve.png)
   - [`logistic_regression_roc_curve.png`](/home/satwik/fraph/fraph-backend/outputs/20260330121604-fraud_data_kaggle_sample/plots/logistic_regression_roc_curve.png)
   - [`knn_roc_curve.png`](/home/satwik/fraph/fraph-backend/outputs/20260330121604-fraud_data_kaggle_sample/plots/knn_roc_curve.png)

2. PR curves for all models
   - [`random_forest_pr_curve.png`](/home/satwik/fraph/fraph-backend/outputs/20260330121604-fraud_data_kaggle_sample/plots/random_forest_pr_curve.png)
   - [`gnn_pr_curve.png`](/home/satwik/fraph/fraph-backend/outputs/20260330121604-fraud_data_kaggle_sample/plots/gnn_pr_curve.png)
   - [`linear_svc_pr_curve.png`](/home/satwik/fraph/fraph-backend/outputs/20260330121604-fraud_data_kaggle_sample/plots/linear_svc_pr_curve.png)
   - [`logistic_regression_pr_curve.png`](/home/satwik/fraph/fraph-backend/outputs/20260330121604-fraud_data_kaggle_sample/plots/logistic_regression_pr_curve.png)
   - [`knn_pr_curve.png`](/home/satwik/fraph/fraph-backend/outputs/20260330121604-fraud_data_kaggle_sample/plots/knn_pr_curve.png)

3. Confusion matrices for the two most important comparisons
   - [`random_forest_confusion_matrix.png`](/home/satwik/fraph/fraph-backend/outputs/20260330121604-fraud_data_kaggle_sample/plots/random_forest_confusion_matrix.png)
   - [`gnn_confusion_matrix.png`](/home/satwik/fraph/fraph-backend/outputs/20260330121604-fraud_data_kaggle_sample/plots/gnn_confusion_matrix.png)

## Recommended Supporting Figures

1. GNN ablation comparison chart
   - build this from [`fraph-backend/outputs/fraud_data_kaggle_sample-gnn-ablation/ablation_results.csv`](/home/satwik/fraph/fraph-backend/outputs/fraud_data_kaggle_sample-gnn-ablation/ablation_results.csv)

2. Hyperparameter sweep summary chart
   - build this from [`fraph-backend/outputs/fraud_data_kaggle_sample-gnn-sweep/sweep_results.csv`](/home/satwik/fraph/fraph-backend/outputs/fraud_data_kaggle_sample-gnn-sweep/sweep_results.csv)

3. Transaction graph illustration from the dashboard
   - use a screenshot from the running app to show how FRAPH presents suspicious network activity

## Suggested Figure Order

1. System workflow diagram
2. ROC comparison
3. PR comparison
4. Random Forest vs GNN confusion matrices
5. GNN ablation chart
6. Dashboard or graph visualization example
