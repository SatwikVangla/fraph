export default function PlaceholderGraph({ graph }) {
  const svgWidth = 540;
  const svgHeight = 360;
  const centerX = svgWidth / 2;
  const centerY = svgHeight / 2;
  const radius = 120;
  const nodes = graph?.top_nodes ?? [];
  const edges = graph?.top_edges ?? [];

  if (!nodes.length) {
    return (
      <div className="flex h-full w-full items-center justify-center text-neutral-500">
        Upload a dataset to render graph activity.
      </div>
    );
  }

  const positionedNodes = nodes.map((node, index) => {
    const angle = (Math.PI * 2 * index) / nodes.length;
    return {
      ...node,
      x: centerX + Math.cos(angle) * radius,
      y: centerY + Math.sin(angle) * radius,
    };
  });

  const getNode = (id) => positionedNodes.find((node) => node.id === id);

  return (
    <div className="flex h-full w-full items-center justify-center">
      <svg
        viewBox={`0 0 ${svgWidth} ${svgHeight}`}
        className="h-full w-full max-h-[360px]"
      >
        {edges.map((edge) => {
          const source = getNode(edge.source);
          const target = getNode(edge.target);
          if (!source || !target) {
            return null;
          }

          return (
            <line
              key={`${edge.source}-${edge.target}`}
              x1={source.x}
              y1={source.y}
              x2={target.x}
              y2={target.y}
              stroke="rgba(255,255,255,0.25)"
              strokeWidth={Math.max(1, edge.count)}
            />
          );
        })}

        {positionedNodes.map((node) => (
          <g key={node.id}>
            <circle
              cx={node.x}
              cy={node.y}
              r={10 + Math.min(node.degree, 8)}
              className={node.total_amount > 0 ? "fraud-node" : "normal-node"}
            />
            <text
              x={node.x}
              y={node.y + 28}
              textAnchor="middle"
              className="fill-neutral-300 text-[10px]"
            >
              {node.label}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}
