import pandas as pd

from app.services.graph_builder import build_graph_from_prepared


def test_build_graph_from_prepared_adds_diverse_focus_edges() -> None:
    dataframe = pd.DataFrame(
        [
            {
                "transaction_id": "t1",
                "sender": "A",
                "receiver": "B",
                "amount": 900.0,
                "label": True,
            },
            {
                "transaction_id": "t2",
                "sender": "A",
                "receiver": "C",
                "amount": 320.0,
                "label": False,
            },
            {
                "transaction_id": "t3",
                "sender": "D",
                "receiver": "B",
                "amount": 280.0,
                "label": False,
            },
            {
                "transaction_id": "t4",
                "sender": "E",
                "receiver": "F",
                "amount": 150.0,
                "label": False,
            },
            {
                "transaction_id": "t5",
                "sender": "A",
                "receiver": "B",
                "amount": 120.0,
                "label": False,
            },
        ]
    )

    graph = build_graph_from_prepared(
        dataframe,
        limit=3,
        suspicious_transaction_ids=["t1"],
    )

    node_ids = {node["id"] for node in graph["top_nodes"]}
    edge_types = {edge["edge_type"] for edge in graph["top_edges"]}
    transfer_edges = [
        edge
        for edge in graph["top_edges"]
        if edge["edge_type"] == "transfers_to"
        and edge["source"] == "account:A"
        and edge["target"] == "account:B"
    ]

    assert "transaction:t1" in node_ids
    assert "transaction:t2" in node_ids
    assert "transaction:t3" in node_ids
    assert "transfers_to" in edge_types
    assert transfer_edges
    assert transfer_edges[0]["count"] == 2
    assert transfer_edges[0]["risk_score"] == 1.0
