import networkx as nx

from app.services.preprocessing import preprocess_dataset


def build_graph(dataset_path: str, limit: int = 10) -> dict[str, object]:
    dataframe, _profile = preprocess_dataset(dataset_path)

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

    top_nodes = sorted(
        graph.nodes,
        key=lambda node: (
            graph.degree(node),
            graph.nodes[node].get("total_amount", 0.0),
        ),
        reverse=True,
    )[:limit]

    top_edges = sorted(
        graph.edges(data=True),
        key=lambda edge: edge[2].get("total_amount", 0.0),
        reverse=True,
    )[:limit]

    density = nx.density(graph) if graph.number_of_nodes() > 1 else 0.0
    components = (
        nx.number_weakly_connected_components(graph)
        if graph.number_of_nodes() > 0
        else 0
    )

    return {
        "node_count": graph.number_of_nodes(),
        "edge_count": graph.number_of_edges(),
        "connected_components": components,
        "density": round(float(density), 4),
        "top_nodes": [
            {
                "id": node,
                "label": node,
                "degree": int(graph.degree(node)),
                "total_amount": round(
                    float(graph.nodes[node].get("total_amount", 0.0)),
                    2,
                ),
            }
            for node in top_nodes
        ],
        "top_edges": [
            {
                "source": source,
                "target": target,
                "count": int(data.get("count", 0)),
                "total_amount": round(float(data.get("total_amount", 0.0)), 2),
            }
            for source, target, data in top_edges
        ],
    }
