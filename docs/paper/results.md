# Draft Results

## Main Comparison

The current unified benchmark was generated from [`fraph-backend/outputs/20260330121604-fraud_data_kaggle_sample`](/home/satwik/fraph/fraph-backend/outputs/20260330121604-fraud_data_kaggle_sample) using the PaySim-derived sample dataset and a consistent `3-fold` stratified evaluation across all models. The strongest model was `Random Forest`, which achieved an F1-score of `0.9385`, ROC-AUC of `0.9823`, and PR-AUC of `0.9515`. This indicates that the tabular feature space remains highly favorable to tree-based ensembles on the current dataset.

The proposed GNN achieved an F1-score of `0.2906`, ROC-AUC of `0.8476`, and PR-AUC of `0.3185`. Although it does not outperform `Random Forest`, it substantially improves recall over the linear baselines and demonstrates that graph-aware modeling captures fraud-related structure beyond a purely linear decision boundary. The GNN therefore functions as a meaningful research baseline rather than a final dominant model.

Among the classical baselines other than `Random Forest`, `Linear SVC` showed the strongest balance with an F1-score of `0.2506`, while `KNN` achieved a slightly lower F1-score of `0.2175`. `Logistic Regression` remained competitive in ROC-AUC but underperformed on recall and F1 relative to the stronger non-linear models.

## Interpretation

The results suggest three immediate conclusions. First, PaySim remains a strong benchmark for demonstrating the strength of classical fraud classifiers, especially tree-based methods. Second, the FRAPH GNN meaningfully improves sensitivity to fraudulent cases, but its precision remains limited, which suppresses overall F1. Third, the graph construction strategy still requires refinement because the current graph does not yet provide enough discriminative advantage to surpass the strongest classical baseline.

## Ablation Findings

The saved ablation outputs in [`fraph-backend/outputs/fraud_data_kaggle_sample-gnn-ablation/ablation_results.csv`](/home/satwik/fraph/fraph-backend/outputs/fraud_data_kaggle_sample-gnn-ablation/ablation_results.csv) indicate that class weighting is important for the imbalanced setting. Earlier ablation runs also showed that changing the edge design can noticeably shift recall and F1, which supports the claim that graph construction is a central modeling decision in the proposed method.

## Paper Framing Recommendation

The current evidence supports a careful claim: FRAPH provides a reproducible graph-aware fraud analysis framework and a competitive GNN baseline, but on the tested PaySim sample the best overall predictive performance is still achieved by `Random Forest`. For a stronger GNN-centered paper claim, the next steps should be a refreshed post-upgrade sweep, deeper ablation study, and evaluation on a graph-native dataset such as Elliptic.
