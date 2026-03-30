from dataclasses import dataclass

import pandas as pd
import torch
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from torch import nn
from torch.nn import functional as F

from app.services.fraud_detection import get_numeric_feature_frame
from app.services.preprocessing import preprocess_dataset
from app.utils.helpers import build_model_storage_path


@dataclass
class GraphData:
    features: torch.Tensor
    labels: torch.Tensor
    adjacency: torch.Tensor
    train_mask: torch.Tensor
    test_mask: torch.Tensor


class GraphConvolution(nn.Module):
    def __init__(self, input_dim: int, output_dim: int):
        super().__init__()
        self.linear = nn.Linear(input_dim, output_dim)

    def forward(self, inputs: torch.Tensor, adjacency: torch.Tensor) -> torch.Tensor:
        return self.linear(adjacency @ inputs)


class TransactionGCN(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int):
        super().__init__()
        self.conv1 = GraphConvolution(input_dim, hidden_dim)
        self.conv2 = GraphConvolution(hidden_dim, 2)

    def forward(self, inputs: torch.Tensor, adjacency: torch.Tensor) -> torch.Tensor:
        hidden = self.conv1(inputs, adjacency)
        hidden = F.relu(hidden)
        hidden = F.dropout(hidden, p=0.2, training=self.training)
        return self.conv2(hidden, adjacency)


def _build_transaction_graph(dataset_path: str) -> GraphData:
    prepared, _profile = preprocess_dataset(dataset_path)
    if "label" not in prepared.columns or prepared["label"].dropna().empty:
        raise ValueError("GNN training requires a labeled fraud column.")

    labeled = prepared.dropna(subset=["label"]).copy()
    labeled["label"] = labeled["label"].astype(int)
    if labeled["label"].nunique() < 2 or len(labeled) < 20:
        raise ValueError(
            "Need at least 20 labeled rows with both fraud and non-fraud classes."
        )

    max_nodes = 4096
    if len(labeled) > max_nodes:
        fraud_rows = labeled[labeled["label"] == 1]
        legit_rows = labeled[labeled["label"] == 0]
        legit_target = max(max_nodes - len(fraud_rows), 0)
        if legit_target > 0:
            legit_rows = legit_rows.sample(
                n=min(legit_target, len(legit_rows)),
                random_state=42,
            )
        labeled = fraud_rows if legit_target == 0 else pd.concat(
            [fraud_rows, legit_rows],
            ignore_index=True,
        )
        labeled = labeled.sample(frac=1.0, random_state=42).reset_index(drop=True)

    features_frame = get_numeric_feature_frame(labeled)
    feature_tensor = torch.tensor(features_frame.values, dtype=torch.float32)
    label_tensor = torch.tensor(labeled["label"].values, dtype=torch.long)

    node_count = len(labeled)
    adjacency = torch.eye(node_count, dtype=torch.float32)

    # Connect nodes that are feature-similar so the GNN has a useful neighborhood
    # even when sender/receiver identities are unique.
    normalized_features = F.normalize(feature_tensor, p=2, dim=1)
    similarity = normalized_features @ normalized_features.T
    k_neighbors = min(8, max(node_count - 1, 1))
    neighbor_indices = torch.topk(similarity, k=k_neighbors + 1, dim=1).indices
    for source in range(node_count):
        for target in neighbor_indices[source].tolist():
            if target == source:
                continue
            adjacency[source, target] = 1.0
            adjacency[target, source] = 1.0

    sender_groups = labeled.groupby("sender").indices
    receiver_groups = labeled.groupby("receiver").indices
    group_collections = [sender_groups, receiver_groups]

    for groups in group_collections:
        for indices in groups.values():
            ordered = sorted(indices)
            for index in range(len(ordered) - 1):
                source = ordered[index]
                target = ordered[index + 1]
                adjacency[source, target] = 1.0
                adjacency[target, source] = 1.0

    degrees = adjacency.sum(dim=1)
    degree_matrix = torch.diag(torch.pow(degrees, -0.5))
    degree_matrix[torch.isinf(degree_matrix)] = 0.0
    normalized_adjacency = degree_matrix @ adjacency @ degree_matrix

    generator = torch.Generator().manual_seed(42)
    indices = torch.randperm(node_count, generator=generator)
    train_cutoff = max(int(node_count * 0.8), 1)
    train_indices = indices[:train_cutoff]
    test_indices = indices[train_cutoff:]
    if len(test_indices) == 0:
        test_indices = train_indices[-1:].clone()
        train_indices = train_indices[:-1]

    train_mask = torch.zeros(node_count, dtype=torch.bool)
    test_mask = torch.zeros(node_count, dtype=torch.bool)
    train_mask[train_indices] = True
    test_mask[test_indices] = True

    return GraphData(
        features=feature_tensor,
        labels=label_tensor,
        adjacency=normalized_adjacency,
        train_mask=train_mask,
        test_mask=test_mask,
    )


def get_gnn_comparison_result() -> dict[str, object]:
    return {
        "model_name": "gnn",
        "status": "pending",
        "details": "GNN training and inference are not implemented yet.",
        "accuracy": None,
        "precision": None,
        "recall": None,
        "f1_score": None,
        "roc_auc": None,
    }


def train_gnn_model(
    dataset_path: str,
    dataset_name: str,
    epochs: int = 40,
    learning_rate: float = 0.01,
    hidden_dim: int = 32,
) -> dict[str, object]:
    graph = _build_transaction_graph(dataset_path)
    model = TransactionGCN(graph.features.shape[1], hidden_dim)
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate, weight_decay=5e-4)
    train_labels = graph.labels[graph.train_mask]
    class_counts = torch.bincount(train_labels, minlength=2).float()
    class_weights = torch.where(
        class_counts > 0,
        train_labels.shape[0] / (2.0 * class_counts),
        torch.ones_like(class_counts),
    )
    criterion = nn.CrossEntropyLoss(weight=class_weights)

    for _epoch in range(epochs):
        model.train()
        optimizer.zero_grad()
        logits = model(graph.features, graph.adjacency)
        loss = criterion(logits[graph.train_mask], graph.labels[graph.train_mask])
        loss.backward()
        optimizer.step()

    model.eval()
    logits = model(graph.features, graph.adjacency)
    probabilities = torch.softmax(logits[graph.test_mask], dim=1)[:, 1]
    predictions = torch.argmax(logits[graph.test_mask], dim=1)
    y_true = graph.labels[graph.test_mask]
    probabilities_np = probabilities.detach().cpu().numpy()
    predictions_np = predictions.detach().cpu().numpy()
    y_true_np = y_true.detach().cpu().numpy()

    artifact_path = build_model_storage_path(dataset_name, "gnn", ".pt")
    torch.save(
        {
            "state_dict": model.state_dict(),
            "input_dim": graph.features.shape[1],
            "hidden_dim": hidden_dim,
        },
        artifact_path,
    )

    return {
        "model_name": "gnn",
        "status": "completed",
        "artifact_path": str(artifact_path),
        "accuracy": round(float(accuracy_score(y_true_np, predictions_np)), 4),
        "precision": round(
            float(precision_score(y_true_np, predictions_np, zero_division=0)),
            4,
        ),
        "recall": round(
            float(recall_score(y_true_np, predictions_np, zero_division=0)),
            4,
        ),
        "f1_score": round(float(f1_score(y_true_np, predictions_np, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_true_np, probabilities_np)), 4),
        "details": "Transaction graph GCN trained and persisted successfully.",
    }


def load_gnn_model(model_path: str) -> dict[str, str]:
    return {
        "status": "completed",
        "message": f"GNN artifact is expected at {model_path}",
    }
