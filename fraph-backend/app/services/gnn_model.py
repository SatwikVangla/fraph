from dataclasses import dataclass

import pandas as pd
import torch
from torch import nn
from torch.nn import functional as F

from app.services.evaluation import compute_binary_classification_metrics
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
    def __init__(self, input_dim: int, hidden_dim: int, dropout: float = 0.2):
        super().__init__()
        self.conv1 = GraphConvolution(input_dim, hidden_dim)
        self.conv2 = GraphConvolution(hidden_dim, hidden_dim)
        self.conv3 = GraphConvolution(hidden_dim, 2)
        self.norm1 = nn.BatchNorm1d(hidden_dim)
        self.norm2 = nn.BatchNorm1d(hidden_dim)
        self.dropout = dropout

    def forward(self, inputs: torch.Tensor, adjacency: torch.Tensor) -> torch.Tensor:
        hidden = self.conv1(inputs, adjacency)
        hidden = self.norm1(hidden)
        hidden = F.relu(hidden)
        hidden = F.dropout(hidden, p=self.dropout, training=self.training)
        hidden = self.conv2(hidden, adjacency)
        hidden = self.norm2(hidden)
        hidden = F.relu(hidden)
        hidden = F.dropout(hidden, p=self.dropout, training=self.training)
        return self.conv3(hidden, adjacency)


def build_transaction_graph_from_prepared(
    prepared: pd.DataFrame,
    train_indices: list[int] | None = None,
    test_indices: list[int] | None = None,
    max_nodes: int = 4096,
    random_state: int = 42,
    use_similarity_edges: bool = True,
    use_party_edges: bool = True,
) -> GraphData:
    if "label" not in prepared.columns or prepared["label"].dropna().empty:
        raise ValueError("GNN training requires a labeled fraud column.")

    labeled = prepared.dropna(subset=["label"]).copy()
    labeled["original_index"] = labeled.index
    labeled["label"] = labeled["label"].astype(int)
    if labeled["label"].nunique() < 2 or len(labeled) < 20:
        raise ValueError(
            "Need at least 20 labeled rows with both fraud and non-fraud classes."
        )

    if len(labeled) > max_nodes:
        fraud_rows = labeled[labeled["label"] == 1]
        legit_rows = labeled[labeled["label"] == 0]
        legit_target = max(max_nodes - len(fraud_rows), 0)
        if legit_target > 0:
            legit_rows = legit_rows.sample(
                n=min(legit_target, len(legit_rows)),
                random_state=random_state,
            )
        labeled = fraud_rows if legit_target == 0 else pd.concat(
            [fraud_rows, legit_rows],
            ignore_index=True,
        )
        labeled = labeled.sample(frac=1.0, random_state=random_state).reset_index(drop=True)

    features_frame = get_numeric_feature_frame(labeled)
    features_frame = (features_frame - features_frame.mean()) / (
        features_frame.std(ddof=0).replace(0, 1.0)
    )
    features_frame = features_frame.fillna(0.0)
    feature_tensor = torch.tensor(features_frame.values, dtype=torch.float32)
    label_tensor = torch.tensor(labeled["label"].values, dtype=torch.long)

    node_count = len(labeled)
    adjacency = torch.eye(node_count, dtype=torch.float32)

    if use_similarity_edges:
        normalized_features = F.normalize(feature_tensor, p=2, dim=1)
        similarity = normalized_features @ normalized_features.T
        k_neighbors = min(16, max(node_count - 1, 1))
        neighbor_indices = torch.topk(similarity, k=k_neighbors + 1, dim=1).indices
        for source in range(node_count):
            for target in neighbor_indices[source].tolist():
                if target == source:
                    continue
                adjacency[source, target] = 1.0
                adjacency[target, source] = 1.0

    if use_party_edges:
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

    train_mask = torch.zeros(node_count, dtype=torch.bool)
    test_mask = torch.zeros(node_count, dtype=torch.bool)
    if train_indices is not None and test_indices is not None:
        original_to_current = {
            int(original_index): current_index
            for current_index, original_index in enumerate(labeled["original_index"].tolist())
        }
        mapped_train_indices = [
            original_to_current[index]
            for index in train_indices
            if index in original_to_current
        ]
        mapped_test_indices = [
            original_to_current[index]
            for index in test_indices
            if index in original_to_current
        ]
        if not mapped_train_indices or not mapped_test_indices:
            raise ValueError(
                "GNN graph sampling removed an entire fold split. Reduce folds or increase max_nodes."
            )
        train_mask[mapped_train_indices] = True
        test_mask[mapped_test_indices] = True
    else:
        generator = torch.Generator().manual_seed(random_state)
        indices = torch.randperm(node_count, generator=generator)
        train_cutoff = max(int(node_count * 0.8), 1)
        shuffled_train_indices = indices[:train_cutoff]
        shuffled_test_indices = indices[train_cutoff:]
        if len(shuffled_test_indices) == 0:
            shuffled_test_indices = shuffled_train_indices[-1:].clone()
            shuffled_train_indices = shuffled_train_indices[:-1]
        train_mask[shuffled_train_indices] = True
        test_mask[shuffled_test_indices] = True

    return GraphData(
        features=feature_tensor,
        labels=label_tensor,
        adjacency=normalized_adjacency,
        train_mask=train_mask,
        test_mask=test_mask,
    )


def build_transaction_graph(dataset_path: str) -> GraphData:
    prepared, _profile = preprocess_dataset(dataset_path)
    return build_transaction_graph_from_prepared(prepared)


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


def train_gnn_from_graph(
    graph: GraphData,
    dataset_name: str,
    epochs: int = 40,
    learning_rate: float = 0.01,
    hidden_dim: int = 32,
    artifact_name: str = "gnn",
    persist_artifact: bool = True,
    include_raw_outputs: bool = False,
    use_class_weights: bool = True,
    dropout: float = 0.2,
) -> dict[str, object]:
    model = TransactionGCN(graph.features.shape[1], hidden_dim, dropout=dropout)
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate, weight_decay=5e-4)
    train_labels = graph.labels[graph.train_mask]
    if use_class_weights:
        class_counts = torch.bincount(train_labels, minlength=2).float()
        class_weights = torch.where(
            class_counts > 0,
            train_labels.shape[0] / (2.0 * class_counts),
            torch.ones_like(class_counts),
        )
        criterion = nn.CrossEntropyLoss(weight=class_weights)
    else:
        criterion = nn.CrossEntropyLoss()

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

    artifact_path = None
    if persist_artifact:
        artifact_path = build_model_storage_path(dataset_name, artifact_name, ".pt")
        torch.save(
            {
                "state_dict": model.state_dict(),
                "input_dim": graph.features.shape[1],
                "hidden_dim": hidden_dim,
            },
            artifact_path,
        )

    metrics = compute_binary_classification_metrics(
        y_true=y_true_np,
        probabilities=probabilities_np,
        predictions=predictions_np,
    )
    result = {
        "model_name": artifact_name,
        "status": "completed",
        "artifact_path": str(artifact_path) if artifact_path else None,
        **metrics,
        "details": "Transaction graph GCN trained and persisted successfully.",
    }
    if include_raw_outputs:
        result["raw_outputs"] = {
            "y_true": y_true_np.tolist(),
            "probabilities": probabilities_np.tolist(),
            "predictions": predictions_np.tolist(),
        }
    return result


def train_gnn_model(
    dataset_path: str,
    dataset_name: str,
    epochs: int = 40,
    learning_rate: float = 0.01,
    hidden_dim: int = 32,
    use_similarity_edges: bool = True,
    use_party_edges: bool = True,
    use_class_weights: bool = True,
    dropout: float = 0.2,
) -> dict[str, object]:
    graph = build_transaction_graph_from_prepared(
        preprocess_dataset(dataset_path)[0],
        use_similarity_edges=use_similarity_edges,
        use_party_edges=use_party_edges,
    )
    return train_gnn_from_graph(
        graph=graph,
        dataset_name=dataset_name,
        epochs=epochs,
        learning_rate=learning_rate,
        hidden_dim=hidden_dim,
        artifact_name="gnn",
        use_class_weights=use_class_weights,
        dropout=dropout,
    )


def load_gnn_model(model_path: str) -> dict[str, str]:
    return {
        "status": "completed",
        "message": f"GNN artifact is expected at {model_path}",
    }
