export default function PlaceholderGraph({ graph }) {
  const svgWidth = 540;
  const svgHeight = 360;
  const centerX = svgWidth / 2;
  const centerY = svgHeight / 2;
  const radius = 124;
  const nodes = graph?.top_nodes ?? [];
  const edges = graph?.top_edges ?? [];

  if (!nodes.length) {
    return (
      <div className="flex h-full w-full items-center justify-center text-neutral-500">
        Upload a dataset to render graph activity.
      </div>
    );
  }

  const connectedNodeIds = new Set(
    edges.flatMap((edge) => [edge.source, edge.target]),
  );

  const positionedNodes = nodes.map((node, index) => {
    const angleOffset = nodes.length % 2 === 0 ? Math.PI / nodes.length : 0;
    const angle = (Math.PI * 2 * index) / nodes.length + angleOffset;
    const amountWeight = Math.min(Math.max(node.total_amount, 0), 1_000_000) / 1_000_000;
    const dynamicRadius = radius - amountWeight * 18;
    return {
      ...node,
      x: centerX + Math.cos(angle) * dynamicRadius,
      y: centerY + Math.sin(angle) * dynamicRadius,
    };
  });

  const getNode = (id) => positionedNodes.find((node) => node.id === id);
  const formatLabel = (label) =>
    label.length > 12 ? `${label.slice(0, 6)}...${label.slice(-3)}` : label;

  return (
    <div className="flex h-full w-full items-center justify-center">
      <svg
        viewBox={`0 0 ${svgWidth} ${svgHeight}`}
        className="h-full w-full max-h-[360px]"
      >
        <defs>
          <radialGradient id="graphGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="rgba(255,0,0,0.18)" />
            <stop offset="100%" stopColor="rgba(255,0,0,0)" />
          </radialGradient>
        </defs>

        <circle cx={centerX} cy={centerY} r="110" fill="url(#graphGlow)" />

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
              stroke="rgba(255,255,255,0.28)"
              strokeWidth={Math.max(1, Math.min(edge.count, 4))}
            />
          );
        })}

        {positionedNodes.map((node) => (
          <g key={node.id}>
            <circle
              cx={node.x}
              cy={node.y}
              r={10 + Math.min(node.degree, 10)}
              className={
                connectedNodeIds.has(node.id) ? "fraud-node" : "normal-node"
              }
            />
            <text
              x={node.x}
              y={node.y + 28}
              textAnchor="middle"
              className="fill-neutral-300 text-[10px]"
            >
              {formatLabel(node.label)}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}
