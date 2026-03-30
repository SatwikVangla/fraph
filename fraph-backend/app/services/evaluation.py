import math

from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    matthews_corrcoef,
    precision_score,
    recall_score,
    roc_auc_score,
)


def _safe_metric(value: float, default: float = 0.0) -> float:
    numeric = float(value)
    if math.isnan(numeric) or math.isinf(numeric):
        return default
    return numeric


def compute_binary_classification_metrics(
    y_true,
    probabilities,
    predictions,
) -> dict[str, object]:
    unique_labels = set(y_true)
    tn, fp, fn, tp = confusion_matrix(y_true, predictions, labels=[0, 1]).ravel()
    if len(unique_labels) < 2:
        positive_rate = float(sum(y_true)) / max(len(y_true), 1)
        roc_auc = 0.5
        pr_auc = 1.0 if positive_rate == 1.0 else positive_rate
    else:
        roc_auc = float(roc_auc_score(y_true, probabilities))
        pr_auc = float(average_precision_score(y_true, probabilities))
    return {
        "accuracy": round(_safe_metric(accuracy_score(y_true, predictions)), 4),
        "precision": round(_safe_metric(precision_score(y_true, predictions, zero_division=0)), 4),
        "recall": round(_safe_metric(recall_score(y_true, predictions, zero_division=0)), 4),
        "f1_score": round(_safe_metric(f1_score(y_true, predictions, zero_division=0)), 4),
        "roc_auc": round(_safe_metric(roc_auc, default=0.5), 4),
        "pr_auc": round(_safe_metric(pr_auc), 4),
        "mcc": round(_safe_metric(matthews_corrcoef(y_true, predictions)), 4),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }
