import networkx as nx
import pandas as pd

from app.services.preprocessing import preprocess_dataset, recommended_max_rows


def build_graph(
    dataset_path: str,
    limit: int = 10,
    suspicious_transaction_ids: list[str] | None = None,
) -> dict[str, object]:
    dataframe, _profile = preprocess_dataset(
        dataset_path,
        max_rows=recommended_max_rows(dataset_path, purpose="interactive"),
    )
    dataframe = dataframe.copy()
    dataframe["transaction_id"] = dataframe["transaction_id"].astype(str)
    if "label" in dataframe.columns:
        dataframe["label"] = dataframe["label"].fillna(False).astype(bool)
    else:
        dataframe["label"] = False

    graph = nx.DiGraph()
    for row in dataframe.itertuples(index=False):
        sender = str(row.sender)
        receiver = str(row.receiver)
        amount = float(row.amount)

        if graph.has_edge(sender, receiver):
            graph[sender][receiver]["count"] += 1
            graph[sender][receiver]["total_amount"] += amount
        else:
            graph.add_edge(sender, receiver, count=1, total_amount=amount)

    for node in graph.nodes:
        total_amount = 0.0
        for _, _, data in graph.in_edges(node, data=True):
            total_amount += float(data.get("total_amount", 0.0))
        for _, _, data in graph.out_edges(node, data=True):
            total_amount += float(data.get("total_amount", 0.0))
        graph.nodes[node]["total_amount"] = total_amount

    ranked_nodes = sorted(
        graph.nodes,
        key=lambda node: (
            graph.degree(node),
            graph.nodes[node].get("total_amount", 0.0),
        ),
        reverse=True,
    )

    ranked_edges = sorted(
        graph.edges(data=True),
        key=lambda edge: edge[2].get("total_amount", 0.0),
        reverse=True,
    )

    selected_node_ids: list[str] = []
    for source, target, _data in ranked_edges:
        for node_id in (source, target):
            if node_id not in selected_node_ids:
                selected_node_ids.append(node_id)
            if len(selected_node_ids) >= limit:
                break
        if len(selected_node_ids) >= limit:
            break

    if len(selected_node_ids) < limit:
        for node_id in ranked_nodes:
            if node_id not in selected_node_ids:
                selected_node_ids.append(node_id)
            if len(selected_node_ids) >= limit:
                break

    selected_node_set = set(selected_node_ids)
    top_nodes = [node_id for node_id in selected_node_ids if node_id in selected_node_set]
    top_edges = [
        (source, target, data)
        for source, target, data in ranked_edges
        if source in selected_node_set and target in selected_node_set
    ][: max(limit * 2, 1)]

    density = nx.density(graph) if graph.number_of_nodes() > 1 else 0.0
    components = (
        nx.number_weakly_connected_components(graph)
        if graph.number_of_nodes() > 0
        else 0
    )

    focus_ids = set(suspicious_transaction_ids or [])
    if not focus_ids:
        focus_frame = dataframe.sort_values("amount", ascending=False).head(limit)
    else:
        focus_frame = dataframe[dataframe["transaction_id"].isin(focus_ids)].copy()
        if len(focus_frame) < limit:
            remainder = dataframe[~dataframe["transaction_id"].isin(focus_ids)].sort_values(
                "amount",
                ascending=False,
            )
            focus_frame = pd.concat(
                [focus_frame, remainder.head(max(limit - len(focus_frame), 0))],
                ignore_index=True,
            )

    focus_graph = nx.DiGraph()
    for row in focus_frame.itertuples(index=False):
        sender_id = f"account:{row.sender}"
        receiver_id = f"account:{row.receiver}"
        transaction_id = f"transaction:{row.transaction_id}"
        risk_score = 1.0 if bool(getattr(row, "label", False)) else None

        focus_graph.add_node(
            sender_id,
            label=str(row.sender),
            node_type="account",
            total_amount=0.0,
            suspicious=False,
            risk_score=None,
            activity_count=0,
        )
        focus_graph.add_node(
            receiver_id,
            label=str(row.receiver),
            node_type="account",
            total_amount=0.0,
            suspicious=False,
            risk_score=None,
            activity_count=0,
        )
        focus_graph.add_node(
            transaction_id,
            label=str(row.transaction_id),
            node_type="transaction",
            total_amount=float(row.amount),
            suspicious=bool(getattr(row, "label", False)),
            risk_score=risk_score,
            activity_count=1,
        )

        for account_id in (sender_id, receiver_id):
            focus_graph.nodes[account_id]["total_amount"] += float(row.amount)
            focus_graph.nodes[account_id]["activity_count"] += 1

        focus_graph.add_edge(
            sender_id,
            transaction_id,
            count=1,
            total_amount=float(row.amount),
            edge_type="initiates",
            risk_score=risk_score,
        )
        focus_graph.add_edge(
            transaction_id,
            receiver_id,
            count=1,
            total_amount=float(row.amount),
            edge_type="settles_to",
            risk_score=risk_score,
        )

    top_nodes = []
    for node_id, data in focus_graph.nodes(data=True):
        top_nodes.append(
            {
                "id": node_id,
                "label": str(data.get("label", node_id)),
                "degree": int(focus_graph.degree(node_id)),
                "total_amount": round(float(data.get("total_amount", 0.0)), 2),
                "node_type": str(data.get("node_type", "account")),
                "risk_score": data.get("risk_score"),
                "suspicious": bool(data.get("suspicious", False)),
                "activity_count": int(data.get("activity_count", 0)),
            }
        )
    top_nodes.sort(
        key=lambda node: (
            1 if node["node_type"] == "transaction" else 0,
            node["total_amount"],
            node["degree"],
        ),
        reverse=True,
    )

    top_edges = [
        {
            "source": source,
            "target": target,
            "count": int(data.get("count", 0)),
            "total_amount": round(float(data.get("total_amount", 0.0)), 2),
            "edge_type": str(data.get("edge_type", "transfer")),
            "risk_score": data.get("risk_score"),
        }
        for source, target, data in focus_graph.edges(data=True)
    ]

    return {
        "node_count": graph.number_of_nodes(),
        "edge_count": graph.number_of_edges(),
        "connected_components": components,
        "density": round(float(density), 4),
        "top_nodes": top_nodes[: max(limit * 2, 1)],
        "top_edges": top_edges[: max(limit * 4, 1)],
    }
