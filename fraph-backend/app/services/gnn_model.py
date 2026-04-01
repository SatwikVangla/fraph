import math
from dataclasses import dataclass

import pandas as pd
import torch
from torch import nn
from torch.nn import functional as F
from torch_geometric.nn import GATConv, LayerNorm, SAGEConv

from app.services.evaluation import compute_binary_classification_metrics
from app.services.fraud_detection import get_numeric_feature_frame
from app.services.preprocessing import preprocess_dataset
from app.utils.helpers import build_model_storage_path


@dataclass
class GraphData:
    features: torch.Tensor
    feature_names: list[str]
    labels: torch.Tensor
    edge_index: torch.Tensor
    transaction_node_count: int
    train_mask: torch.Tensor
    val_mask: torch.Tensor
    test_mask: torch.Tensor


class TransactionGraphSAGE(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int, dropout: float = 0.2):
        super().__init__()
        self.input_encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        self.conv1 = SAGEConv(hidden_dim, hidden_dim)
        self.conv2 = SAGEConv(hidden_dim, hidden_dim)
        self.conv3 = SAGEConv(hidden_dim, hidden_dim)
        self.conv4 = SAGEConv(hidden_dim, hidden_dim)
        self.norm1 = LayerNorm(hidden_dim)
        self.norm2 = LayerNorm(hidden_dim)
        self.norm3 = LayerNorm(hidden_dim)
        self.norm4 = LayerNorm(hidden_dim)
        self.graph_gate = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.Sigmoid(),
        )
        self.output_projection = nn.Sequential(
            nn.Linear(hidden_dim * 4, hidden_dim * 2),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 2),
        )
        self.dropout = dropout

    def forward(self, inputs: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        encoded_inputs = self.input_encoder(inputs)
        hidden = self.conv1(encoded_inputs, edge_index)
        hidden = self.norm1(hidden + encoded_inputs)
        hidden = F.gelu(hidden)
        hidden = F.dropout(hidden, p=self.dropout, training=self.training)
        residual_hidden = hidden
        hidden = self.conv2(hidden, edge_index)
        hidden = self.norm2(hidden + residual_hidden)
        hidden = F.gelu(hidden)
        hidden = F.dropout(hidden, p=self.dropout, training=self.training)
        residual_hidden = hidden
        hidden = self.conv3(hidden, edge_index)
        hidden = self.norm3(hidden + residual_hidden)
        hidden = F.gelu(hidden)
        hidden = F.dropout(hidden, p=self.dropout, training=self.training)
        residual_hidden = hidden
        hidden = self.conv4(hidden, edge_index)
        hidden = self.norm4(hidden + residual_hidden)
        hidden = F.gelu(hidden)
        hidden = F.dropout(hidden, p=self.dropout, training=self.training)
        gate = self.graph_gate(torch.cat([hidden, encoded_inputs], dim=1))
        fused_hidden = gate * hidden + (1.0 - gate) * encoded_inputs
        combined = torch.cat(
            [
                fused_hidden,
                encoded_inputs,
                fused_hidden - encoded_inputs,
                fused_hidden * encoded_inputs,
            ],
            dim=1,
        )
        return self.classifier(self.output_projection(combined))


class TransactionGraphGAT(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int, dropout: float = 0.2):
        super().__init__()
        self.input_encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        self.conv1 = GATConv(hidden_dim, hidden_dim // 4, heads=4, dropout=dropout)
        self.conv2 = GATConv(hidden_dim, hidden_dim // 4, heads=4, dropout=dropout)
        self.norm1 = LayerNorm(hidden_dim)
        self.norm2 = LayerNorm(hidden_dim)
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim * 3, hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 2),
        )
        self.dropout = dropout

    def forward(self, inputs: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        encoded = self.input_encoder(inputs)
        hidden = self.conv1(encoded, edge_index)
        hidden = self.norm1(hidden + encoded)
        hidden = F.gelu(hidden)
        hidden = F.dropout(hidden, p=self.dropout, training=self.training)
        hidden = self.conv2(hidden, edge_index)
        hidden = self.norm2(hidden + encoded)
        hidden = F.gelu(hidden)
        hidden = F.dropout(hidden, p=self.dropout, training=self.training)
        combined = torch.cat([hidden, encoded, hidden * encoded], dim=1)
        return self.classifier(combined)


def _build_transaction_node_features(labeled: pd.DataFrame) -> pd.DataFrame:
    features = get_numeric_feature_frame(labeled).copy()

    sender_group = labeled.groupby("sender", sort=False)
    receiver_group = labeled.groupby("receiver", sort=False)
    pair_group = labeled.groupby(["sender", "receiver"], sort=False)
    amount = pd.to_numeric(labeled["amount"], errors="coerce").fillna(0.0)
    step = pd.to_numeric(labeled["step"], errors="coerce").fillna(0.0)

    sender_counts = sender_group["transaction_id"].transform("count").astype(float)
    receiver_counts = receiver_group["transaction_id"].transform("count").astype(float)
    pair_counts = pair_group["transaction_id"].transform("count").astype(float)
    features["sender_unique_receivers"] = sender_group["receiver"].transform("nunique").astype(float)
    features["receiver_unique_senders"] = receiver_group["sender"].transform("nunique").astype(float)
    features["sender_total_sent_amount"] = sender_group["amount"].transform("sum").astype(float)
    features["receiver_total_received_amount"] = receiver_group["amount"].transform("sum").astype(float)
    features["sender_mean_amount"] = sender_group["amount"].transform("mean").astype(float)
    features["receiver_mean_amount"] = receiver_group["amount"].transform("mean").astype(float)
    features["pair_total_amount"] = pair_group["amount"].transform("sum").astype(float)
    features["pair_mean_amount"] = pair_group["amount"].transform("mean").astype(float)
    features["pair_density"] = pair_counts / sender_counts.clip(lower=1.0)
    features["sender_activity_ratio"] = sender_counts / receiver_counts.clip(lower=1.0)
    features["receiver_activity_ratio"] = receiver_counts / sender_counts.clip(lower=1.0)
    features["amount_vs_sender_mean"] = amount / (
        features["sender_mean_amount"].replace(0.0, 1.0)
    )
    features["amount_vs_receiver_mean"] = amount / (
        features["receiver_mean_amount"].replace(0.0, 1.0)
    )
    features["amount_vs_pair_mean"] = amount / (
        features["pair_mean_amount"].replace(0.0, 1.0)
    )
    features["sender_step_mean"] = sender_group["step"].transform("mean").astype(float)
    features["receiver_step_mean"] = receiver_group["step"].transform("mean").astype(float)
    features["step_from_sender_mean"] = (step - features["sender_step_mean"]).abs()
    features["step_from_receiver_mean"] = (step - features["receiver_step_mean"]).abs()
    features["pair_step_rank"] = pair_group.cumcount().astype(float)
    features["sender_step_rank"] = sender_group.cumcount().astype(float)
    features["receiver_step_rank"] = receiver_group.cumcount().astype(float)
    features["counterparty_diversity"] = (
        features["sender_unique_receivers"] + features["receiver_unique_senders"]
    )
    features["account_net_flow"] = (
        features["sender_total_sent_amount"] - features["receiver_total_received_amount"]
    )
    features["pair_time_gap"] = pair_group["step"].diff().abs().fillna(0.0).astype(float)
    features["sender_time_gap"] = sender_group["step"].diff().abs().fillna(0.0).astype(float)
    features["receiver_time_gap"] = receiver_group["step"].diff().abs().fillna(0.0).astype(float)
    features["pair_is_burst"] = (features["pair_time_gap"] <= 1.0).astype(float)
    features["sender_is_burst"] = (features["sender_time_gap"] <= 1.0).astype(float)
    features["receiver_is_burst"] = (features["receiver_time_gap"] <= 1.0).astype(float)
    features["step_percentile"] = step.rank(method="average", pct=True).astype(float)
    features["amount_step_interaction"] = amount * (1.0 + features["step_percentile"])
    features["node_type_transaction"] = 1.0
    features["node_type_account"] = 0.0

    return features.replace([float("inf"), float("-inf")], 0.0).fillna(0.0)


def _build_account_node_features(
    labeled: pd.DataFrame,
    transaction_feature_columns: list[str],
) -> tuple[pd.DataFrame, list[str]]:
    account_ids = sorted(set(labeled["sender"].astype(str)) | set(labeled["receiver"].astype(str)))
    rows: list[dict[str, float]] = []

    for account_id in account_ids:
        sent = labeled[labeled["sender"].astype(str) == account_id]
        received = labeled[labeled["receiver"].astype(str) == account_id]
        related = pd.concat([sent, received], ignore_index=True)

        total_sent_amount = float(pd.to_numeric(sent["amount"], errors="coerce").fillna(0.0).sum())
        total_received_amount = float(
            pd.to_numeric(received["amount"], errors="coerce").fillna(0.0).sum()
        )
        total_related_amount = total_sent_amount + total_received_amount
        sender_count = float(len(sent))
        receiver_count = float(len(received))
        related_steps = pd.to_numeric(related["step"], errors="coerce").fillna(0.0)
        sender_old_balance = pd.to_numeric(sent["oldbalance_orig"], errors="coerce").fillna(0.0)
        receiver_old_balance = pd.to_numeric(
            received["oldbalance_dest"],
            errors="coerce",
        ).fillna(0.0)

        row = {column: 0.0 for column in transaction_feature_columns}
        row["amount_log"] = float(torch.log1p(torch.tensor(total_related_amount)).item())
        row["sender_tx_count"] = sender_count
        row["receiver_tx_count"] = receiver_count
        row["transaction_type_code"] = -1.0
        row["step_value"] = float(related_steps.mean()) if not related_steps.empty else 0.0
        row["origin_balance_shift"] = float(
            pd.to_numeric(sent["balance_delta_orig"], errors="coerce").fillna(0.0).abs().mean()
        ) if not sent.empty else 0.0
        row["destination_balance_shift"] = float(
            pd.to_numeric(received["balance_delta_dest"], errors="coerce").fillna(0.0).abs().mean()
        ) if not received.empty else 0.0
        row["amount_to_origin_balance"] = total_sent_amount / (float(sender_old_balance.sum()) + 1.0)
        row["amount_to_destination_balance"] = total_received_amount / (
            float(receiver_old_balance.sum()) + 1.0
        )
        row["sender_unique_receivers"] = float(sent["receiver"].nunique())
        row["receiver_unique_senders"] = float(received["sender"].nunique())
        row["sender_total_sent_amount"] = total_sent_amount
        row["receiver_total_received_amount"] = total_received_amount
        row["sender_mean_amount"] = total_sent_amount / max(sender_count, 1.0)
        row["receiver_mean_amount"] = total_received_amount / max(receiver_count, 1.0)
        row["pair_total_amount"] = total_related_amount
        row["pair_mean_amount"] = total_related_amount / max(sender_count + receiver_count, 1.0)
        row["pair_density"] = 0.0
        row["sender_activity_ratio"] = sender_count / max(receiver_count, 1.0)
        row["receiver_activity_ratio"] = receiver_count / max(sender_count, 1.0)
        row["amount_vs_sender_mean"] = 1.0 if sender_count > 0 else 0.0
        row["amount_vs_receiver_mean"] = 1.0 if receiver_count > 0 else 0.0
        row["amount_vs_pair_mean"] = 1.0 if sender_count + receiver_count > 0 else 0.0
        row["sender_step_mean"] = float(
            pd.to_numeric(sent["step"], errors="coerce").fillna(0.0).mean()
        ) if not sent.empty else 0.0
        row["receiver_step_mean"] = float(
            pd.to_numeric(received["step"], errors="coerce").fillna(0.0).mean()
        ) if not received.empty else 0.0
        row["step_from_sender_mean"] = float(related_steps.std(ddof=0)) if len(related_steps) > 1 else 0.0
        row["step_from_receiver_mean"] = float(related_steps.std(ddof=0)) if len(related_steps) > 1 else 0.0
        row["pair_step_rank"] = float(len(related))
        row["sender_step_rank"] = sender_count
        row["receiver_step_rank"] = receiver_count
        row["counterparty_diversity"] = row["sender_unique_receivers"] + row["receiver_unique_senders"]
        row["account_net_flow"] = total_sent_amount - total_received_amount
        row["pair_time_gap"] = float(related_steps.diff().abs().mean()) if len(related_steps) > 1 else 0.0
        row["sender_time_gap"] = float(
            pd.to_numeric(sent["step"], errors="coerce").fillna(0.0).diff().abs().mean()
        ) if len(sent) > 1 else 0.0
        row["receiver_time_gap"] = float(
            pd.to_numeric(received["step"], errors="coerce").fillna(0.0).diff().abs().mean()
        ) if len(received) > 1 else 0.0
        row["pair_is_burst"] = 1.0 if row["pair_time_gap"] <= 1.0 and len(related) > 1 else 0.0
        row["sender_is_burst"] = 1.0 if row["sender_time_gap"] <= 1.0 and len(sent) > 1 else 0.0
        row["receiver_is_burst"] = 1.0 if row["receiver_time_gap"] <= 1.0 and len(received) > 1 else 0.0
        row["step_percentile"] = 0.5
        row["amount_step_interaction"] = total_related_amount * 1.5
        row["node_type_transaction"] = 0.0
        row["node_type_account"] = 1.0
        rows.append(row)

    return pd.DataFrame(rows, columns=transaction_feature_columns), account_ids


def build_transaction_graph_from_prepared(
    prepared: pd.DataFrame,
    train_indices: list[int] | None = None,
    test_indices: list[int] | None = None,
    max_nodes: int | None = None,
    random_state: int = 42,
    use_similarity_edges: bool = True,
    use_party_edges: bool = True,
    use_temporal_edges: bool = True,
    include_account_nodes: bool = True,
) -> GraphData:
    if "label" not in prepared.columns or prepared["label"].dropna().empty:
        raise ValueError("GNN training requires a labeled fraud column.")

    labeled = prepared.dropna(subset=["label"]).copy()
    labeled["original_index"] = labeled.index
    labeled["label"] = labeled["label"].astype(int)
    train_index_set: set[int] = set()
    test_index_set: set[int] = set()
    if labeled["label"].nunique() < 2 or len(labeled) < 20:
        raise ValueError(
            "Need at least 20 labeled rows with both fraud and non-fraud classes."
        )

    if train_indices is not None and test_indices is not None:
        train_index_set = set(train_indices)
        test_index_set = set(test_indices)
        labeled["split_group"] = labeled["original_index"].map(
            lambda index: "train"
            if index in train_index_set
            else "test"
            if index in test_index_set
            else "other"
        )
    else:
        labeled["split_group"] = "all"

    if max_nodes is not None and len(labeled) > max_nodes:
        positive_rows = labeled[labeled["label"] == 1].copy()
        negative_rows = labeled[labeled["label"] == 0].copy()

        if len(positive_rows) >= max_nodes:
            sampled_positive_groups: list[pd.DataFrame] = []
            for _split_group, group in positive_rows.groupby("split_group", sort=False):
                if group.empty:
                    continue
                sample_size = min(
                    len(group),
                    max(
                        1,
                        int(round((len(group) / max(len(positive_rows), 1)) * max_nodes)),
                    ),
                )
                sampled_positive_groups.append(
                    group.sample(n=sample_size, random_state=random_state)
                )
            labeled = pd.concat(sampled_positive_groups, ignore_index=True)
            if len(labeled) > max_nodes:
                labeled = labeled.sample(n=max_nodes, random_state=random_state)
        else:
            sampled_groups = [positive_rows]
            remaining_capacity = max_nodes - len(positive_rows)
            negative_total = max(len(negative_rows), 1)

            for _split_group, group in negative_rows.groupby("split_group", sort=False):
                if group.empty or remaining_capacity <= 0:
                    continue
                sample_size = min(
                    len(group),
                    max(1, int(round((len(group) / negative_total) * remaining_capacity))),
                )
                sampled_groups.append(
                    group.sample(n=sample_size, random_state=random_state)
                )

            labeled = pd.concat(sampled_groups, ignore_index=True)
            if len(labeled) > max_nodes:
                positive_sample = labeled[labeled["label"] == 1]
                negative_sample = labeled[labeled["label"] == 0]
                available_negative_slots = max(max_nodes - len(positive_sample), 0)
                negative_sample = negative_sample.sample(
                    n=min(len(negative_sample), available_negative_slots),
                    random_state=random_state,
                )
                labeled = pd.concat([positive_sample, negative_sample], ignore_index=True)
            elif len(labeled) < max_nodes and len(negative_rows) > 0:
                sampled_indices = set(labeled["original_index"].tolist())
                negative_remainder = negative_rows[
                    ~negative_rows["original_index"].isin(sampled_indices)
                ]
                if not negative_remainder.empty:
                    filler = negative_remainder.sample(
                        n=min(max_nodes - len(labeled), len(negative_remainder)),
                        random_state=random_state,
                    )
                    labeled = pd.concat([labeled, filler], ignore_index=True)

        labeled = labeled.sample(frac=1.0, random_state=random_state).reset_index(drop=True)

    transaction_features = _build_transaction_node_features(labeled)
    transaction_node_count = len(transaction_features)
    if include_account_nodes:
        account_features, account_ids = _build_account_node_features(
            labeled,
            transaction_features.columns.tolist(),
        )
        features_frame = pd.concat(
            [transaction_features, account_features],
            ignore_index=True,
        )
    else:
        account_ids = []
        features_frame = transaction_features
    features_frame = (features_frame - features_frame.mean()) / (
        features_frame.std(ddof=0).replace(0, 1.0)
    )
    features_frame = features_frame.fillna(0.0)
    feature_names = features_frame.columns.tolist()
    feature_tensor = torch.tensor(features_frame.values, dtype=torch.float32)
    all_labels = labeled["label"].astype(int).tolist() + [0] * len(account_ids)
    label_tensor = torch.tensor(all_labels, dtype=torch.long)

    node_count = len(features_frame)
    edge_weights: dict[tuple[int, int], float] = {
        (index, index): 1.0 for index in range(node_count)
    }
    step_values = pd.to_numeric(labeled["step"], errors="coerce").fillna(0.0).tolist()
    amount_values = pd.to_numeric(labeled["amount"], errors="coerce").fillna(0.0).tolist()

    def upsert_edge(source: int, target: int, weight: float) -> None:
        key = (source, target)
        edge_weights[key] = max(edge_weights.get(key, 0.0), float(weight))

    if use_similarity_edges:
        transaction_tensor = feature_tensor[:transaction_node_count]
        normalized_features = F.normalize(transaction_tensor, p=2, dim=1)
        k_neighbors = min(16, max(transaction_node_count - 1, 1))
        chunk_size = 256
        for start in range(0, transaction_node_count, chunk_size):
            stop = min(start + chunk_size, transaction_node_count)
            similarity = normalized_features[start:stop] @ normalized_features.T
            neighbor_values, neighbor_indices = torch.topk(
                similarity,
                k=k_neighbors + 1,
                dim=1,
            )
            for local_source, source in enumerate(range(start, stop)):
                for edge_position, target in enumerate(neighbor_indices[local_source].tolist()):
                    if target == source:
                        continue
                    weight = max(float(neighbor_values[local_source, edge_position].item()), 0.0)
                    if weight <= 0.0:
                        continue
                    upsert_edge(source, target, weight)
                    upsert_edge(target, source, weight)

    if use_party_edges:
        sender_groups = labeled.groupby("sender").indices
        receiver_groups = labeled.groupby("receiver").indices
        pair_groups = labeled.groupby(["sender", "receiver"]).indices
        group_collections = [
            (sender_groups, 1.15),
            (receiver_groups, 1.15),
            (pair_groups, 1.35),
        ]

        for groups, base_weight in group_collections:
            for indices in groups.values():
                ordered = sorted(indices, key=lambda index: (float(step_values[index]), index))
                for index, source in enumerate(ordered):
                    upper_bound = min(index + 5, len(ordered))
                    for neighbor_index in range(index + 1, upper_bound):
                        target = ordered[neighbor_index]
                        step_gap = abs(float(step_values[source]) - float(step_values[target]))
                        temporal_weight = 1.0 / (1.0 + min(step_gap, 25.0))
                        amount_gap = abs(float(amount_values[source]) - float(amount_values[target]))
                        amount_weight = 1.0 / (1.0 + min(amount_gap / 10000.0, 5.0))
                        burst_bonus = 0.35 if step_gap <= 1.0 else 0.0
                        weight = base_weight + temporal_weight + amount_weight * 0.25 + burst_bonus
                        upsert_edge(source, target, weight)
                        upsert_edge(target, source, weight)

    if use_temporal_edges:
        temporal_groups = [
            labeled.groupby("sender").indices,
            labeled.groupby("receiver").indices,
            labeled.groupby(["sender", "receiver"]).indices,
        ]
        for groups in temporal_groups:
            for indices in groups.values():
                ordered = sorted(indices, key=lambda index: (float(step_values[index]), index))
                for source, target in zip(ordered, ordered[1:]):
                    step_gap = abs(float(step_values[source]) - float(step_values[target]))
                    if step_gap > 50:
                        continue
                    temporal_weight = 1.4 + (1.0 / (1.0 + step_gap))
                    upsert_edge(source, target, temporal_weight)
                    upsert_edge(target, source, temporal_weight)

        if include_account_nodes:
            account_offset = transaction_node_count
            account_index_map = {
                account_id: account_offset + index for index, account_id in enumerate(account_ids)
            }
            pair_amounts = (
                labeled.groupby(["sender", "receiver"], sort=False)["amount"]
                .sum()
                .to_dict()
            )

            for transaction_index, row in enumerate(labeled.itertuples(index=False)):
                sender_node = account_index_map[str(row.sender)]
                receiver_node = account_index_map[str(row.receiver)]
                amount_weight = 1.0 + min(float(torch.log1p(torch.tensor(amount_values[transaction_index])).item()) / 5.0, 1.0)
                time_bonus = 0.4 if transaction_index > 0 and abs(step_values[transaction_index] - step_values[max(0, transaction_index - 1)]) <= 1.0 else 0.0
                tx_account_weight = 1.35 + amount_weight + time_bonus
                upsert_edge(transaction_index, sender_node, tx_account_weight)
                upsert_edge(sender_node, transaction_index, tx_account_weight)
                upsert_edge(transaction_index, receiver_node, tx_account_weight)
                upsert_edge(receiver_node, transaction_index, tx_account_weight)

            for (sender, receiver), total_amount in pair_amounts.items():
                sender_node = account_index_map[str(sender)]
                receiver_node = account_index_map[str(receiver)]
                pair_weight = 1.1 + min(float(torch.log1p(torch.tensor(total_amount)).item()) / 6.0, 1.0)
                upsert_edge(sender_node, receiver_node, pair_weight)
                upsert_edge(receiver_node, sender_node, pair_weight)

    edge_indices: list[list[int]] = []
    for (source, target), weight in edge_weights.items():
        repeat_count = max(1, min(int(round(weight)), 4))
        for _ in range(repeat_count):
            edge_indices.append([source, target])

    edge_index = torch.tensor(edge_indices, dtype=torch.long).T.contiguous()

    train_mask = torch.zeros(node_count, dtype=torch.bool)
    val_mask = torch.zeros(node_count, dtype=torch.bool)
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
        fraud_train = [
            index for index in mapped_train_indices if int(label_tensor[index].item()) == 1
        ]
        legit_train = [
            index for index in mapped_train_indices if int(label_tensor[index].item()) == 0
        ]
        val_indices: list[int] = []
        if len(fraud_train) >= 2 and len(legit_train) >= 2:
            fraud_val_count = max(1, int(round(len(fraud_train) * 0.2)))
            legit_val_count = max(1, int(round(len(legit_train) * 0.2)))
            val_indices.extend(sorted(fraud_train)[:fraud_val_count])
            val_indices.extend(sorted(legit_train)[:legit_val_count])
        else:
            validation_size = max(1, int(round(len(mapped_train_indices) * 0.15)))
            val_indices.extend(sorted(mapped_train_indices)[:validation_size])

        train_only_indices = [
            index for index in mapped_train_indices if index not in set(val_indices)
        ]
        if not train_only_indices:
            train_only_indices = mapped_train_indices[:-1]
            val_indices = mapped_train_indices[-1:]

        train_mask[train_only_indices] = True
        val_mask[val_indices] = True
        test_mask[mapped_test_indices] = True
    else:
        generator = torch.Generator().manual_seed(random_state)
        indices = torch.randperm(node_count, generator=generator)
        train_cutoff = max(int(node_count * 0.7), 1)
        val_cutoff = max(int(node_count * 0.85), train_cutoff + 1)
        shuffled_train_indices = indices[:train_cutoff]
        shuffled_val_indices = indices[train_cutoff:val_cutoff]
        shuffled_test_indices = indices[val_cutoff:]
        if len(shuffled_val_indices) == 0:
            shuffled_val_indices = shuffled_train_indices[-1:].clone()
            shuffled_train_indices = shuffled_train_indices[:-1]
        if len(shuffled_test_indices) == 0:
            shuffled_test_indices = shuffled_val_indices[-1:].clone()
            shuffled_val_indices = shuffled_val_indices[:-1]
        train_mask[shuffled_train_indices] = True
        val_mask[shuffled_val_indices] = True
        test_mask[shuffled_test_indices] = True

    return GraphData(
        features=feature_tensor,
        feature_names=feature_names,
        labels=label_tensor,
        edge_index=edge_index,
        transaction_node_count=transaction_node_count,
        train_mask=train_mask,
        val_mask=val_mask,
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


def _default_gnn_trial_configs(
    epochs: int,
    hidden_dim: int,
    learning_rate: float,
    dropout: float,
) -> list[dict[str, object]]:
    return [
        {
            "epochs": min(max(80, int(epochs * 0.7)), 140),
            "hidden_dim": max(hidden_dim, 128),
            "learning_rate": max(learning_rate, 0.0015),
            "dropout": min(max(dropout, 0.08), 0.14),
            "use_similarity_edges": True,
            "use_party_edges": True,
            "use_temporal_edges": True,
            "include_account_nodes": True,
            "model_architecture": "graphsage",
        },
        {
            "epochs": min(max(90, int(epochs * 0.85)), 160),
            "hidden_dim": max(hidden_dim, 160),
            "learning_rate": max(learning_rate * 0.85, 0.0012),
            "dropout": min(max(dropout, 0.08), 0.12),
            "use_similarity_edges": True,
            "use_party_edges": True,
            "use_temporal_edges": True,
            "include_account_nodes": True,
            "model_architecture": "gat",
        },
        {
            "epochs": min(max(100, epochs), 180),
            "hidden_dim": max(hidden_dim, 192),
            "learning_rate": max(learning_rate * 0.65, 0.001),
            "dropout": min(max(dropout + 0.02, 0.1), 0.16),
            "use_similarity_edges": True,
            "use_party_edges": True,
            "use_temporal_edges": True,
            "include_account_nodes": True,
            "model_architecture": "graphsage",
        },
        {
            "epochs": min(max(80, int(epochs * 0.75)), 150),
            "hidden_dim": max(96, hidden_dim),
            "learning_rate": max(learning_rate * 0.9, 0.0013),
            "dropout": min(max(dropout + 0.03, 0.1), 0.18),
            "use_similarity_edges": False,
            "use_party_edges": True,
            "use_temporal_edges": True,
            "include_account_nodes": True,
            "model_architecture": "gat",
        },
        {
            "epochs": min(max(70, int(epochs * 0.65)), 130),
            "hidden_dim": max(96, hidden_dim),
            "learning_rate": max(learning_rate, 0.0015),
            "dropout": min(max(dropout, 0.08), 0.16),
            "use_similarity_edges": True,
            "use_party_edges": True,
            "use_temporal_edges": True,
            "include_account_nodes": False,
            "model_architecture": "graphsage",
        },
        {
            "epochs": min(max(85, int(epochs * 0.8)), 150),
            "hidden_dim": max(128, hidden_dim),
            "learning_rate": max(learning_rate * 0.8, 0.0012),
            "dropout": min(max(dropout + 0.02, 0.1), 0.18),
            "use_similarity_edges": True,
            "use_party_edges": False,
            "use_temporal_edges": True,
            "include_account_nodes": True,
            "model_architecture": "gat",
        },
    ]


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
    random_seed: int = 42,
    model_architecture: str = "graphsage",
) -> dict[str, object]:
    def build_balanced_train_mask() -> torch.Tensor:
        train_indices = torch.nonzero(graph.train_mask, as_tuple=False).view(-1)
        train_targets = graph.labels[train_indices]
        positive_indices = train_indices[train_targets == 1]
        negative_indices = train_indices[train_targets == 0]
        if len(positive_indices) == 0 or len(negative_indices) == 0:
            return graph.train_mask

        negative_sample_size = min(
            len(negative_indices),
            max(len(positive_indices) * 3, len(positive_indices)),
        )
        sampled_negative_order = torch.randperm(len(negative_indices))[:negative_sample_size]
        sampled_indices = torch.cat([positive_indices, negative_indices[sampled_negative_order]])
        balanced_mask = torch.zeros_like(graph.train_mask)
        balanced_mask[sampled_indices] = True
        return balanced_mask

    def select_threshold(
        probabilities_tensor: torch.Tensor,
        targets_tensor: torch.Tensor,
    ) -> tuple[float, float]:
        probabilities_np = probabilities_tensor.detach().cpu().numpy()
        targets_np = targets_tensor.detach().cpu().numpy()
        positive_rate = float(targets_tensor.float().mean().item()) if len(targets_tensor) else 0.0
        positive_count = int(targets_tensor.sum().item()) if len(targets_tensor) else 0
        if len(targets_tensor) < 20 or positive_count < 3:
            fallback_threshold = 0.65 if positive_rate < 0.05 else 0.5
            return fallback_threshold, 0.0
        candidate_thresholds = sorted(
            {
                0.12,
                0.18,
                0.25,
                0.35,
                0.5,
                0.6,
                0.7,
                0.8,
                *[float(value) for value in torch.linspace(0.03, 0.85, steps=24).tolist()],
                *[float(value) for value in probabilities_tensor.detach().cpu().quantile(
                    torch.tensor([0.35, 0.5, 0.65, 0.75, 0.85, 0.9], dtype=torch.float32)
                ).tolist()],
            }
        )

        best_local_score = float("-inf")
        best_local_threshold = 0.5
        for threshold in candidate_thresholds:
            threshold = min(float(threshold), 0.85)
            predictions_np = (probabilities_np >= threshold).astype(int)
            metrics = compute_binary_classification_metrics(
                y_true=targets_np,
                probabilities=probabilities_np,
                predictions=predictions_np,
            )
            predicted_positive_rate = float(predictions_np.mean()) if len(predictions_np) else 0.0
            prevalence_penalty = abs(predicted_positive_rate - positive_rate)
            overshoot_penalty = max(0.0, predicted_positive_rate - max(positive_rate * 4.0, 0.12))
            precision_floor = 0.16 if positive_rate < 0.05 else 0.22
            precision_bonus = 0.08 if float(metrics["precision"]) >= precision_floor else -0.14
            score = (
                float(metrics["f1_score"]) * 0.3
                + float(metrics["pr_auc"]) * 0.24
                + float(metrics["recall"]) * 0.18
                + float(metrics["precision"]) * 0.16
                + float(metrics["mcc"]) * 0.12
                + precision_bonus
                - prevalence_penalty * 0.12
                - overshoot_penalty * 0.32
            )
            if score > best_local_score:
                best_local_score = score
                best_local_threshold = float(threshold)

        return best_local_threshold, best_local_score

    def calibrate_probabilities(
        logits_tensor: torch.Tensor,
        targets_tensor: torch.Tensor,
    ) -> tuple[float, float]:
        if not bool(graph.val_mask.any().item()) or len(targets_tensor) < 20:
            return 1.0, 0.0

        positive_logits = logits_tensor[:, 1] - logits_tensor[:, 0]
        targets = targets_tensor.float()
        best_temperature = 1.0
        best_bias = 0.0
        best_loss = float("inf")

        for temperature in [0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0]:
            scaled_logits = positive_logits / temperature
            for bias in [-2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0]:
                probabilities = torch.sigmoid(scaled_logits + bias)
                loss = F.binary_cross_entropy(probabilities, targets).item()
                if loss < best_loss:
                    best_loss = loss
                    best_temperature = float(temperature)
                    best_bias = float(bias)

        return best_temperature, best_bias

    torch.manual_seed(random_seed)
    if model_architecture == "gat":
        model = TransactionGraphGAT(graph.features.shape[1], hidden_dim, dropout=dropout)
    else:
        model = TransactionGraphSAGE(graph.features.shape[1], hidden_dim, dropout=dropout)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=learning_rate,
        weight_decay=5e-5,
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer,
        T_max=max(epochs, 1),
    )
    train_labels = graph.labels[graph.train_mask]
    if use_class_weights:
        class_counts = torch.bincount(train_labels, minlength=2).float()
        class_weights = torch.where(
            class_counts > 0,
            train_labels.shape[0] / (2.0 * class_counts),
            torch.ones_like(class_counts),
        )
        criterion = nn.CrossEntropyLoss(weight=class_weights, label_smoothing=0.02)
    else:
        criterion = nn.CrossEntropyLoss(label_smoothing=0.02)

    best_state = None
    best_threshold = 0.5
    best_score = float("-inf")
    best_epoch = 0
    patience = max(28, epochs // 4)

    for epoch in range(epochs):
        model.train()
        optimizer.zero_grad()
        logits = model(graph.features, graph.edge_index)
        supervised_train_mask = build_balanced_train_mask()
        train_logits = logits[supervised_train_mask]
        train_targets = graph.labels[supervised_train_mask]
        loss = criterion(train_logits, train_targets)

        probabilities = torch.softmax(train_logits, dim=1)[:, 1]
        positive_targets = train_targets.float()
        focal_factor = torch.pow(
            1.0 - torch.where(positive_targets > 0, probabilities, 1.0 - probabilities),
            2.0,
        )
        loss = loss + (
            F.binary_cross_entropy(probabilities, positive_targets, reduction="none")
            * focal_factor
        ).mean()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=2.0)
        optimizer.step()
        scheduler.step()

        if bool(graph.val_mask.any().item()):
            model.eval()
            with torch.no_grad():
                val_logits = model(graph.features, graph.edge_index)
                val_probabilities = torch.softmax(val_logits[graph.val_mask], dim=1)[:, 1]
                val_y_true = graph.labels[graph.val_mask]
                threshold, score = select_threshold(val_probabilities, val_y_true)
                if score > best_score:
                    best_score = score
                    best_threshold = threshold
                    best_epoch = epoch
                    best_state = {
                        key: value.detach().cpu().clone()
                        for key, value in model.state_dict().items()
                    }
            if epoch - best_epoch >= patience:
                break

    if best_state is not None:
        model.load_state_dict(best_state)
    model.eval()
    logits = model(graph.features, graph.edge_index)
    calibration_temperature = 1.0
    calibration_bias = 0.0
    if bool(graph.val_mask.any().item()):
        with torch.no_grad():
            calibration_temperature, calibration_bias = calibrate_probabilities(
                logits[graph.val_mask],
                graph.labels[graph.val_mask],
            )
            val_margin = (
                (logits[graph.val_mask][:, 1] - logits[graph.val_mask][:, 0])
                / calibration_temperature
            ) + calibration_bias
            recalibration_probabilities = torch.sigmoid(val_margin)
            recalibration_targets = graph.labels[graph.val_mask]
            best_threshold, _ = select_threshold(
                recalibration_probabilities,
                recalibration_targets,
            )
    test_margin = (
        (logits[graph.test_mask][:, 1] - logits[graph.test_mask][:, 0])
        / calibration_temperature
    ) + calibration_bias
    probabilities = torch.sigmoid(test_margin)
    predictions = (probabilities >= best_threshold).long()
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
                "model_type": model_architecture,
            },
            artifact_path,
        )

    metrics = compute_binary_classification_metrics(
        y_true=y_true_np,
        probabilities=probabilities_np,
        predictions=predictions_np,
    )
    encoder_weights = model.input_encoder[0].weight.detach().abs().mean(dim=0).cpu()
    ranked_features = sorted(
        zip(graph.feature_names, encoder_weights.tolist()),
        key=lambda item: item[1],
        reverse=True,
    )[:10]
    result = {
        "model_name": artifact_name,
        "status": "completed",
        "artifact_path": str(artifact_path) if artifact_path else None,
        **metrics,
        "details": f"Transaction-account {model_architecture.upper()} model trained and persisted successfully.",
        "validation_score": round(best_score, 4) if best_score != float("-inf") else None,
        "best_epoch": int(best_epoch),
        "threshold": round(best_threshold, 4),
        "calibration_temperature": round(float(calibration_temperature), 4),
        "calibration_bias": round(float(calibration_bias), 4),
        "explainability": {
            "top_input_features": [
                {"feature": feature_name, "importance": round(float(score), 4)}
                for feature_name, score in ranked_features
            ],
            "graph_summary": {
                "transaction_nodes": int(graph.transaction_node_count),
                "total_nodes": int(graph.features.shape[0]),
                "edge_count": int(graph.edge_index.shape[1]),
            },
        },
    }
    if include_raw_outputs:
        result["raw_outputs"] = {
            "y_true": y_true_np.tolist(),
            "probabilities": probabilities_np.tolist(),
            "predictions": predictions_np.tolist(),
        }
    return result


def tune_and_train_gnn_from_prepared(
    prepared: pd.DataFrame,
    dataset_name: str,
    train_indices: list[int] | None = None,
    test_indices: list[int] | None = None,
    epochs: int = 120,
    learning_rate: float = 0.003,
    hidden_dim: int = 96,
    artifact_name: str = "gnn",
    persist_artifact: bool = True,
    include_raw_outputs: bool = False,
    use_class_weights: bool = True,
    dropout: float = 0.1,
    max_nodes: int | None = None,
    seed_candidates: list[int] | None = None,
    forced_model_architecture: str | None = None,
) -> dict[str, object]:
    best_trial_result: dict[str, object] | None = None
    best_trial_config: dict[str, object] | None = None
    best_trial_score = float("-inf")
    graph_cache: dict[tuple[bool, bool, bool, bool], GraphData] = {}
    trial_configs = _default_gnn_trial_configs(epochs, hidden_dim, learning_rate, dropout)
    if forced_model_architecture is not None:
        filtered = [
            config
            for config in trial_configs
            if str(config.get("model_architecture")) == forced_model_architecture
        ]
        trial_configs = filtered or trial_configs

    for trial_index, trial_config in enumerate(trial_configs, start=1):
        graph_key = (
            bool(trial_config["use_similarity_edges"]),
            bool(trial_config["use_party_edges"]),
            bool(trial_config.get("use_temporal_edges", True)),
            bool(trial_config["include_account_nodes"]),
        )
        graph = graph_cache.get(graph_key)
        if graph is None:
            graph = build_transaction_graph_from_prepared(
                prepared=prepared,
                train_indices=train_indices,
                test_indices=test_indices,
                max_nodes=max_nodes,
                use_similarity_edges=graph_key[0],
                use_party_edges=graph_key[1],
                use_temporal_edges=graph_key[2],
                include_account_nodes=graph_key[3],
            )
            graph_cache[graph_key] = graph
        trial_result = train_gnn_from_graph(
            graph=graph,
            dataset_name=dataset_name,
            epochs=int(trial_config["epochs"]),
            hidden_dim=int(trial_config["hidden_dim"]),
            learning_rate=float(trial_config["learning_rate"]),
            artifact_name=f"{artifact_name}-trial-{trial_index}",
            persist_artifact=False,
            include_raw_outputs=False,
            use_class_weights=use_class_weights,
            dropout=float(trial_config["dropout"]),
            random_seed=42,
            model_architecture=str(trial_config.get("model_architecture", "graphsage")),
        )
        trial_score = float(
            trial_result.get("validation_score")
            or trial_result.get("f1_score")
            or 0.0
        )
        if not math.isfinite(trial_score):
            trial_score = float(trial_result.get("f1_score") or 0.0)
        if trial_score > best_trial_score:
            best_trial_score = trial_score
            best_trial_result = trial_result
            best_trial_config = trial_config

    if best_trial_config is None:
        best_trial_config = trial_configs[0]

    final_graph_key = (
        bool(best_trial_config["use_similarity_edges"]),
        bool(best_trial_config["use_party_edges"]),
        bool(best_trial_config.get("use_temporal_edges", True)),
        bool(best_trial_config["include_account_nodes"]),
    )
    final_graph = graph_cache.get(final_graph_key)
    if final_graph is None:
        final_graph = build_transaction_graph_from_prepared(
            prepared=prepared,
            train_indices=train_indices,
            test_indices=test_indices,
            max_nodes=max_nodes,
            use_similarity_edges=final_graph_key[0],
            use_party_edges=final_graph_key[1],
            use_temporal_edges=final_graph_key[2],
            include_account_nodes=final_graph_key[3],
        )
    final_training_epochs = max(
        int(epochs),
        min(int(best_trial_config.get("epochs", epochs)), 24),
    )
    selected_seeds = seed_candidates or [42, 52, 62]
    best_seed_result: dict[str, object] | None = None
    best_seed = selected_seeds[0]
    best_seed_score = float("-inf")
    for candidate_seed in selected_seeds:
        seed_result = train_gnn_from_graph(
            graph=final_graph,
            dataset_name=dataset_name,
            epochs=final_training_epochs,
            hidden_dim=int(best_trial_config["hidden_dim"]),
            learning_rate=float(best_trial_config["learning_rate"]),
            artifact_name=artifact_name,
            persist_artifact=False,
            include_raw_outputs=include_raw_outputs,
            use_class_weights=use_class_weights,
            dropout=float(best_trial_config["dropout"]),
            random_seed=int(candidate_seed),
            model_architecture=str(best_trial_config.get("model_architecture", "graphsage")),
        )
        seed_score = float(
            seed_result.get("validation_score")
            or seed_result.get("f1_score")
            or 0.0
        )
        if seed_score > best_seed_score:
            best_seed_score = seed_score
            best_seed_result = seed_result
            best_seed = int(candidate_seed)

    if best_seed_result is None:
        best_seed_result = train_gnn_from_graph(
            graph=final_graph,
            dataset_name=dataset_name,
            epochs=final_training_epochs,
            hidden_dim=int(best_trial_config["hidden_dim"]),
            learning_rate=float(best_trial_config["learning_rate"]),
            artifact_name=artifact_name,
            persist_artifact=False,
            include_raw_outputs=include_raw_outputs,
            use_class_weights=use_class_weights,
            dropout=float(best_trial_config["dropout"]),
            random_seed=42,
            model_architecture=str(best_trial_config.get("model_architecture", "graphsage")),
        )

    final_result = best_seed_result
    if persist_artifact:
        persisted_result = train_gnn_from_graph(
            graph=final_graph,
            dataset_name=dataset_name,
            epochs=final_training_epochs,
            hidden_dim=int(best_trial_config["hidden_dim"]),
            learning_rate=float(best_trial_config["learning_rate"]),
            artifact_name=artifact_name,
            persist_artifact=True,
            include_raw_outputs=include_raw_outputs,
            use_class_weights=use_class_weights,
            dropout=float(best_trial_config["dropout"]),
            random_seed=best_seed,
            model_architecture=str(best_trial_config.get("model_architecture", "graphsage")),
        )
        persisted_result["explainability"] = final_result.get("explainability")
        final_result = persisted_result

    final_result["selected_config"] = {
        **best_trial_config,
        "epochs": final_training_epochs,
        "selected_seed": best_seed,
        "candidate_seeds": selected_seeds,
    }
    final_result["details"] = (
        "Transaction-account GraphSAGE trained with automatic tuning over graph structure "
        f"and hyperparameters. Selected config: {final_result['selected_config']}."
    )
    if best_trial_result is not None:
        final_result["tuning_validation_score"] = best_trial_result.get("validation_score")
    return final_result


def quick_train_gnn_from_prepared(
    prepared: pd.DataFrame,
    dataset_name: str,
    train_indices: list[int] | None = None,
    test_indices: list[int] | None = None,
    epochs: int = 24,
    learning_rate: float = 0.0035,
    hidden_dim: int = 64,
    artifact_name: str = "gnn",
    persist_artifact: bool = False,
    include_raw_outputs: bool = False,
    use_class_weights: bool = True,
    dropout: float = 0.15,
    use_similarity_edges: bool = False,
    use_party_edges: bool = True,
    include_account_nodes: bool = True,
    max_nodes: int = 2048,
) -> dict[str, object]:
    graph = build_transaction_graph_from_prepared(
        prepared=prepared,
        train_indices=train_indices,
        test_indices=test_indices,
        max_nodes=max_nodes,
        use_similarity_edges=use_similarity_edges,
        use_party_edges=use_party_edges,
        include_account_nodes=include_account_nodes,
    )
    result = train_gnn_from_graph(
        graph=graph,
        dataset_name=dataset_name,
        epochs=epochs,
        learning_rate=learning_rate,
        hidden_dim=hidden_dim,
        artifact_name=artifact_name,
        persist_artifact=persist_artifact,
        include_raw_outputs=include_raw_outputs,
        use_class_weights=use_class_weights,
        dropout=dropout,
    )
    result["details"] = (
        "Quick GraphSAGE evaluation on a transaction-account graph for interactive comparison."
    )
    result["selected_config"] = {
        "epochs": epochs,
        "hidden_dim": hidden_dim,
        "learning_rate": learning_rate,
        "dropout": dropout,
        "use_similarity_edges": use_similarity_edges,
        "use_party_edges": use_party_edges,
        "include_account_nodes": include_account_nodes,
        "max_nodes": max_nodes,
        "mode": "quick_compare",
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
    sampling_preset: str = "medium",
) -> dict[str, object]:
    sampling_caps = {
        "small": 1536,
        "medium": 4096,
        "large": 8192,
        "full": None,
    }
    prepared = preprocess_dataset(dataset_path)[0]
    return tune_and_train_gnn_from_prepared(
        prepared=prepared,
        dataset_name=dataset_name,
        epochs=epochs,
        learning_rate=learning_rate,
        hidden_dim=hidden_dim,
        artifact_name="gnn",
        persist_artifact=True,
        use_class_weights=use_class_weights,
        dropout=dropout,
        max_nodes=sampling_caps.get(sampling_preset, 4096),
    )


def load_gnn_model(model_path: str) -> dict[str, str]:
    return {
        "status": "completed",
        "message": f"GNN artifact is expected at {model_path}",
    }
