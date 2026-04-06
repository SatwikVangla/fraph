import { useMemo, useState } from "react";

const SVG_WIDTH = 980;
const SVG_HEIGHT = 560;
const GRAPH_THEMES = [
  {
    name: "Amber Risk",
    panelGlow: "rgba(245, 158, 11, 0.24)",
    secondaryGlow: "rgba(190, 24, 93, 0.18)",
    transactionFill: "#f97316",
    accountFill: "#fde68a",
    suspiciousFill: "#facc15",
    riskyEdge: "rgba(251, 191, 36, 0.95)",
    neutralEdge: "rgba(255, 251, 235, 0.2)",
    activeEdge: "rgba(249, 115, 22, 0.95)",
    halo: "rgba(251, 191, 36, 0.14)",
  },
  {
    name: "Crimson Mesh",
    panelGlow: "rgba(220, 38, 38, 0.24)",
    secondaryGlow: "rgba(239, 68, 68, 0.14)",
    transactionFill: "#dc2626",
    accountFill: "#fecaca",
    suspiciousFill: "#fb7185",
    riskyEdge: "rgba(251, 113, 133, 0.92)",
    neutralEdge: "rgba(255, 228, 230, 0.2)",
    activeEdge: "rgba(248, 113, 113, 0.98)",
    halo: "rgba(248, 113, 113, 0.14)",
  },
  {
    name: "Copper Flow",
    panelGlow: "rgba(249, 115, 22, 0.22)",
    secondaryGlow: "rgba(251, 191, 36, 0.14)",
    transactionFill: "#ea580c",
    accountFill: "#fed7aa",
    suspiciousFill: "#fbbf24",
    riskyEdge: "rgba(251, 191, 36, 0.9)",
    neutralEdge: "rgba(255, 237, 213, 0.18)",
    activeEdge: "rgba(249, 115, 22, 0.95)",
    halo: "rgba(251, 146, 60, 0.13)",
  },
  {
    name: "Rose Cluster",
    panelGlow: "rgba(225, 29, 72, 0.22)",
    secondaryGlow: "rgba(244, 63, 94, 0.14)",
    transactionFill: "#e11d48",
    accountFill: "#fbcfe8",
    suspiciousFill: "#fb7185",
    riskyEdge: "rgba(253, 164, 175, 0.92)",
    neutralEdge: "rgba(255, 241, 242, 0.18)",
    activeEdge: "rgba(244, 63, 94, 0.96)",
    halo: "rgba(244, 114, 182, 0.14)",
  },
];

function hashValue(input) {
  let hash = 0;
  for (let index = 0; index < input.length; index += 1) {
    hash = (hash * 31 + input.charCodeAt(index)) >>> 0;
  }
  return hash;
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function formatCompact(value) {
  if (!Number.isFinite(value)) {
    return "0";
  }
  if (value >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(1)}M`;
  }
  if (value >= 1_000) {
    return `${(value / 1_000).toFixed(1)}K`;
  }
  return `${Math.round(value)}`;
}

function buildGraphProfile(nodes, edges) {
  const suspiciousCount = nodes.filter((node) => node.suspicious).length;
  const transactionCount = nodes.filter((node) => node.node_type === "transaction").length;
  const riskyEdgeCount = edges.filter((edge) => edge.risk_score).length;
  const totalAmount = edges.reduce((sum, edge) => sum + (edge.total_amount ?? 0), 0);
  const edgeTypeCounts = new Map();
  edges.forEach((edge) => {
    edgeTypeCounts.set(edge.edge_type, (edgeTypeCounts.get(edge.edge_type) ?? 0) + 1);
  });
  const dominantEdgeType =
    [...edgeTypeCounts.entries()].sort((left, right) => right[1] - left[1])[0]?.[0] ?? "mixed";
  const density =
    nodes.length > 1 ? edges.length / Math.max(nodes.length * (nodes.length - 1), 1) : 0;
  const signature = [
    nodes.length,
    edges.length,
    suspiciousCount,
    riskyEdgeCount,
    dominantEdgeType,
    nodes.slice(0, 6).map((node) => node.id).join("|"),
  ].join(":");

  return {
    suspiciousCount,
    transactionCount,
    riskyEdgeCount,
    totalAmount,
    dominantEdgeType,
    density,
    signature,
  };
}

function pickGraphTheme(profile) {
  const themeIndex = hashValue(profile.signature) % GRAPH_THEMES.length;
  return GRAPH_THEMES[themeIndex];
}

function buildBackdropBlobs(nodes) {
  return nodes
    .filter((node) => node.node_type === "transaction")
    .slice(0, 6)
    .map((node, index) => ({
      id: node.id,
      x: node.x,
      y: node.y,
      rx: 54 + Math.min(node.degree, 8) * 8 + index * 3,
      ry: 36 + Math.min(node.degree, 6) * 7,
      rotation: ((hashValue(node.id) % 90) - 45),
      opacity: node.suspicious ? 0.95 : 0.55,
    }));
}

function buildFlowPositions(nodes, edges) {
  const transactionNodes = nodes.filter((node) => node.node_type === "transaction");
  const accountNodes = nodes.filter((node) => node.node_type !== "transaction");

  const directionalBalance = new Map();
  edges.forEach((edge) => {
    directionalBalance.set(
      edge.source,
      (directionalBalance.get(edge.source) ?? 0) + 1,
    );
    directionalBalance.set(
      edge.target,
      (directionalBalance.get(edge.target) ?? 0) - 1,
    );
  });

  const senderAccounts = [];
  const receiverAccounts = [];
  const bridgeAccounts = [];

  accountNodes.forEach((node) => {
    const balance = directionalBalance.get(node.id) ?? 0;
    if (balance > 0) {
      senderAccounts.push(node);
      return;
    }
    if (balance < 0) {
      receiverAccounts.push(node);
      return;
    }
    bridgeAccounts.push(node);
  });

  const layoutColumn = (columnNodes, x, startY, spacingY) =>
    columnNodes.map((node, index) => ({
      ...node,
      x,
      y: startY + index * spacingY,
    }));

  const senderSpacing = Math.max(68, 360 / Math.max(senderAccounts.length, 1));
  const receiverSpacing = Math.max(68, 360 / Math.max(receiverAccounts.length, 1));
  const bridgeSpacing = Math.max(72, 240 / Math.max(bridgeAccounts.length, 1));
  const transactionSpacing = Math.max(72, 380 / Math.max(transactionNodes.length, 1));

  const positionedSenders = layoutColumn(senderAccounts, 150, 120, senderSpacing);
  const positionedBridges = layoutColumn(bridgeAccounts, 320, 160, bridgeSpacing);
  const positionedTransactions = layoutColumn(
    transactionNodes,
    SVG_WIDTH * 0.54,
    95,
    transactionSpacing,
  );
  const positionedReceivers = layoutColumn(receiverAccounts, 825, 120, receiverSpacing);

  return [
    ...positionedSenders,
    ...positionedBridges,
    ...positionedTransactions,
    ...positionedReceivers,
  ];
}

function buildNetworkPositions(nodes, edges) {
  const centerX = SVG_WIDTH * 0.52;
  const centerY = SVG_HEIGHT * 0.5;
  const nodeIndex = new Map(nodes.map((node, index) => [node.id, index]));
  const directionalBalance = new Map();
  const neighborsById = new Map(nodes.map((node) => [node.id, new Set()]));

  edges.forEach((edge) => {
    neighborsById.get(edge.source)?.add(edge.target);
    neighborsById.get(edge.target)?.add(edge.source);
    directionalBalance.set(
      edge.source,
      (directionalBalance.get(edge.source) ?? 0) + 1,
    );
    directionalBalance.set(
      edge.target,
      (directionalBalance.get(edge.target) ?? 0) - 1,
    );
  });

  const positions = nodes.map((node) => {
    const seed = hashValue(node.id);
    const angle = ((seed % 360) * Math.PI) / 180;
    const radialBand =
      node.node_type === "transaction"
        ? 90 + (seed % 70)
        : 180 + (seed % 110);
    const directionalOffset = directionalBalance.get(node.id) ?? 0;

    return {
      ...node,
      x: clamp(
        centerX +
          Math.cos(angle) * radialBand +
          (directionalOffset > 0 ? -50 : directionalOffset < 0 ? 50 : 0),
        90,
        SVG_WIDTH - 90,
      ),
      y: clamp(
        centerY +
          Math.sin(angle) * (radialBand * 0.72) +
          (node.suspicious ? -18 : 0),
        80,
        SVG_HEIGHT - 80,
      ),
      vx: 0,
      vy: 0,
    };
  });

  const kRepel = 19000;
  const kLink = 0.011;
  const gravity = 0.02;
  const damping = 0.84;
  const idealLengthBase = 84;
  const iterations = Math.min(140, 70 + nodes.length * 2);

  for (let iteration = 0; iteration < iterations; iteration += 1) {
    for (let index = 0; index < positions.length; index += 1) {
      const node = positions[index];
      let fx = (centerX - node.x) * gravity;
      let fy = (centerY - node.y) * gravity;

      for (let otherIndex = 0; otherIndex < positions.length; otherIndex += 1) {
        if (otherIndex === index) {
          continue;
        }
        const other = positions[otherIndex];
        const dx = node.x - other.x;
        const dy = node.y - other.y;
        const distanceSq = Math.max(dx * dx + dy * dy, 28);
        const distance = Math.sqrt(distanceSq);
        const repel = kRepel / distanceSq;
        fx += (dx / distance) * repel;
        fy += (dy / distance) * repel;
      }

      const neighborIds = neighborsById.get(node.id) ?? new Set();
      neighborIds.forEach((neighborId) => {
        const neighbor = positions[nodeIndex.get(neighborId)];
        if (!neighbor) {
          return;
        }
        const dx = neighbor.x - node.x;
        const dy = neighbor.y - node.y;
        const distance = Math.max(Math.sqrt(dx * dx + dy * dy), 1);
        const idealLength =
          idealLengthBase +
          (node.node_type === "transaction" || neighbor.node_type === "transaction" ? 14 : 32) +
          Math.min((node.degree + neighbor.degree) * 2, 34);
        const pull = (distance - idealLength) * kLink;
        fx += (dx / distance) * pull;
        fy += (dy / distance) * pull;
      });

      if (node.node_type === "transaction") {
        fx += (centerX - node.x) * 0.028;
        fy += (centerY - node.y) * 0.028;
      } else {
        const balance = directionalBalance.get(node.id) ?? 0;
        fx += balance > 0 ? -0.9 : balance < 0 ? 0.9 : 0;
      }

      node.vx = (node.vx + fx) * damping;
      node.vy = (node.vy + fy) * damping;
    }

    positions.forEach((node) => {
      node.x = clamp(node.x + node.vx, 70, SVG_WIDTH - 70);
      node.y = clamp(node.y + node.vy, 70, SVG_HEIGHT - 70);
    });
  }

  return positions.map((node) => {
    const cleanedNode = { ...node };
    delete cleanedNode.vx;
    delete cleanedNode.vy;
    return cleanedNode;
  });
}

function buildNodePositions(nodes, edges, layoutMode) {
  if (layoutMode === "network") {
    return buildNetworkPositions(nodes, edges);
  }
  return buildFlowPositions(nodes, edges);
}

function getConnectedItems(edges, selectedNodeId) {
  if (!selectedNodeId) {
    return { neighborIds: new Set(), selectedEdgeKeys: new Set() };
  }

  const neighborIds = new Set();
  const selectedEdgeKeys = new Set();
  edges.forEach((edge) => {
    if (edge.source === selectedNodeId || edge.target === selectedNodeId) {
      selectedEdgeKeys.add(`${edge.source}-${edge.target}`);
      neighborIds.add(edge.source === selectedNodeId ? edge.target : edge.source);
    }
  });
  return { neighborIds, selectedEdgeKeys };
}

export default function PlaceholderGraph({
  graph,
  focusTransactionId = null,
  onTransactionSelect = null,
}) {
  const [selectedNodeId, setSelectedNodeId] = useState(null);
  const [viewMode, setViewMode] = useState("all");
  const [layoutMode, setLayoutMode] = useState("network");

  const nodes = useMemo(() => graph?.top_nodes ?? [], [graph]);
  const edges = useMemo(() => graph?.top_edges ?? [], [graph]);
  const focusNodeId = focusTransactionId ? `transaction:${focusTransactionId}` : null;

  const baseGraph = useMemo(() => {
    if (viewMode === "all") {
      return { nodes, edges };
    }

    const suspiciousIds = new Set(
      nodes.filter((node) => node.suspicious).map((node) => node.id),
    );
    const suspiciousEdges = edges.filter(
      (edge) =>
        edge.risk_score ||
        suspiciousIds.has(edge.source) ||
        suspiciousIds.has(edge.target),
    );
    suspiciousEdges.forEach((edge) => {
      suspiciousIds.add(edge.source);
      suspiciousIds.add(edge.target);
    });

    return {
      nodes: nodes.filter((node) => suspiciousIds.has(node.id)),
      edges: suspiciousEdges,
    };
  }, [edges, nodes, viewMode]);

  const visibleGraph = useMemo(() => {
    if (!focusNodeId) {
      return baseGraph;
    }

    const focusIds = new Set([focusNodeId]);
    baseGraph.edges.forEach((edge) => {
      if (edge.source === focusNodeId || edge.target === focusNodeId) {
        focusIds.add(edge.source);
        focusIds.add(edge.target);
      }
    });

    const focusedNodes = baseGraph.nodes.filter((node) => focusIds.has(node.id));
    if (!focusedNodes.length) {
      return baseGraph;
    }

    return {
      nodes: focusedNodes,
      edges: baseGraph.edges.filter(
        (edge) => focusIds.has(edge.source) && focusIds.has(edge.target),
      ),
    };
  }, [baseGraph, focusNodeId]);

  const graphProfile = useMemo(
    () => buildGraphProfile(visibleGraph.nodes, visibleGraph.edges),
    [visibleGraph.edges, visibleGraph.nodes],
  );
  const graphTheme = useMemo(() => pickGraphTheme(graphProfile), [graphProfile]);

  if (!visibleGraph.nodes.length) {
    return (
      <div className="flex h-full w-full items-center justify-center text-neutral-500">
        Upload a dataset to render graph activity.
      </div>
    );
  }

  const positionedNodes = buildNodePositions(visibleGraph.nodes, visibleGraph.edges, layoutMode);
  const backdropBlobs = buildBackdropBlobs(positionedNodes);
  const nodeMap = new Map(positionedNodes.map((node) => [node.id, node]));
  const effectiveSelectedNodeId = focusNodeId ?? selectedNodeId;
  const selectedNode = effectiveSelectedNodeId
    ? nodeMap.get(effectiveSelectedNodeId) ?? positionedNodes[0]
    : positionedNodes[0];
  const { neighborIds, selectedEdgeKeys } = getConnectedItems(
    visibleGraph.edges,
    selectedNode?.id ?? null,
  );

  const suspiciousTransactions = visibleGraph.nodes.filter(
    (node) => node.node_type === "transaction" && node.suspicious,
  ).length;
  const accountCount = visibleGraph.nodes.filter(
    (node) => node.node_type === "account",
  ).length;

  const formatAmount = (value) =>
    new Intl.NumberFormat("en-US", {
      maximumFractionDigits: 0,
    }).format(value || 0);

  return (
    <div className="flex w-full min-w-0 flex-col gap-4 p-4">
      <div className="grid gap-3 md:grid-cols-[1.2fr_1fr_1fr_auto_auto]">
        <GraphStat label="Accounts" value={accountCount} tone="neutral" />
        <GraphStat
          label="Transactions"
          value={visibleGraph.nodes.length - accountCount}
          tone="red"
        />
        <GraphStat
          label="Suspicious"
          value={suspiciousTransactions}
          tone="amber"
        />
        <div className="flex items-center justify-end gap-2 rounded-xl border border-neutral-900 bg-neutral-950/90 px-3 py-2">
          <ViewButton
            active={viewMode === "all"}
            label="All"
            onClick={() => setViewMode("all")}
          />
          <ViewButton
            active={viewMode === "suspicious"}
            label="Suspicious"
            onClick={() => setViewMode("suspicious")}
          />
        </div>
        <div className="flex items-center justify-end gap-2 rounded-xl border border-neutral-900 bg-neutral-950/90 px-3 py-2">
          <ViewButton
            active={layoutMode === "network"}
            label="Network"
            onClick={() => setLayoutMode("network")}
          />
          <ViewButton
            active={layoutMode === "flow"}
            label="Flow"
            onClick={() => setLayoutMode("flow")}
          />
        </div>
      </div>

      {focusTransactionId ? (
        <div className="rounded-xl border border-red-900/70 bg-red-950/20 px-4 py-3 text-sm text-red-200">
          Focused transaction path: <span className="font-semibold text-white">{focusTransactionId}</span>
        </div>
      ) : null}

      <div className="grid items-start gap-4 xl:grid-cols-[1.65fr_0.85fr]">
        <div className="overflow-hidden rounded-2xl border border-neutral-900 bg-[radial-gradient(circle_at_50%_50%,rgba(185,28,28,0.28),transparent_32%),linear-gradient(180deg,rgba(18,18,18,0.96),rgba(6,6,6,0.98))]">
          <div
            className="overflow-hidden rounded-2xl border border-neutral-900"
            style={{
              backgroundImage: `radial-gradient(circle at 20% 18%, ${graphTheme.panelGlow}, transparent 28%), radial-gradient(circle at 78% 24%, ${graphTheme.secondaryGlow}, transparent 24%), linear-gradient(180deg, rgba(18,18,18,0.96), rgba(6,6,6,0.98))`,
            }}
          >
          <div className="border-b border-neutral-900 px-5 py-4">
            <p className="text-xs font-bold uppercase tracking-[0.28em] text-red-400">
              Relationship Map
            </p>
            <p className="mt-2 text-sm text-neutral-500">
              {layoutMode === "network"
                ? "Nodes are arranged from their actual transaction links so each dataset forms its own shape."
                : "Sender accounts initiate transactions in the center, which then settle into receiver accounts on the right."}
            </p>
            <div className="mt-3 flex flex-wrap gap-2 text-[11px] uppercase tracking-[0.16em] text-neutral-300">
              <span className="rounded-full border border-neutral-800 bg-black/35 px-3 py-1.5">
                Theme {graphTheme.name}
              </span>
              <span className="rounded-full border border-neutral-800 bg-black/35 px-3 py-1.5">
                Dominant {graphProfile.dominantEdgeType}
              </span>
              <span className="rounded-full border border-neutral-800 bg-black/35 px-3 py-1.5">
                Density {(graphProfile.density * 100).toFixed(1)}%
              </span>
              <span className="rounded-full border border-neutral-800 bg-black/35 px-3 py-1.5">
                Amount {formatCompact(graphProfile.totalAmount)}
              </span>
            </div>
          </div>
          <svg
            viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`}
            className="block h-[400px] w-full md:h-[460px] xl:h-[520px]"
          >
            <defs>
              <marker
                id="arrowHead"
                viewBox="0 0 10 10"
                refX="8"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
              >
                <path d="M 0 0 L 10 5 L 0 10 z" fill={graphTheme.activeEdge} />
              </marker>
            </defs>

            {backdropBlobs.map((blob) => (
              <ellipse
                key={blob.id}
                cx={blob.x}
                cy={blob.y}
                rx={blob.rx}
                ry={blob.ry}
                transform={`rotate(${blob.rotation} ${blob.x} ${blob.y})`}
                fill={graphTheme.halo}
                opacity={blob.opacity}
              />
            ))}

            {layoutMode === "flow" ? (
              <>
                <text x="115" y="44" className="fill-neutral-500 text-[12px] uppercase tracking-[0.28em]">
                  Senders
                </text>
                <text x={SVG_WIDTH * 0.5 - 34} y="44" className="fill-neutral-500 text-[12px] uppercase tracking-[0.28em]">
                  Transactions
                </text>
                <text x="794" y="44" className="fill-neutral-500 text-[12px] uppercase tracking-[0.28em]">
                  Receivers
                </text>
              </>
            ) : null}

            {visibleGraph.edges.map((edge) => {
              const source = nodeMap.get(edge.source);
              const target = nodeMap.get(edge.target);
              if (!source || !target) {
                return null;
              }

              const active = selectedEdgeKeys.has(`${edge.source}-${edge.target}`);
              const isRisky = Boolean(edge.risk_score);
              const stroke = isRisky
                ? graphTheme.riskyEdge
                : active
                  ? graphTheme.activeEdge
                  : graphTheme.neutralEdge;
              const midX = (source.x + target.x) / 2;
              const midY = (source.y + target.y) / 2;
              const curvature = ((hashValue(`${edge.source}:${edge.target}`) % 36) - 18) * 1.8;
              const controlX = midX + (source.y - target.y) * 0.08;
              const controlY = midY + (target.x - source.x) * 0.08 + curvature;
              const path = `M ${source.x} ${source.y} Q ${controlX} ${controlY} ${target.x} ${target.y}`;

              return (
                <g key={`${edge.source}-${edge.target}`}>
                  <path
                    d={path}
                    stroke={stroke}
                    fill="none"
                    strokeWidth={active || isRisky ? 3 : 1.8 + Math.min(edge.count ?? 1, 4) * 0.2}
                    strokeOpacity={layoutMode === "network" ? 0.96 : 0.88}
                    markerEnd={active || isRisky ? "url(#arrowHead)" : undefined}
                  />
                  {layoutMode === "flow" ? (
                    <>
                      <rect
                        x={midX - 28}
                        y={midY - 15}
                        width="56"
                        height="18"
                        rx="9"
                        fill="rgba(10,10,10,0.88)"
                        stroke="rgba(255,255,255,0.08)"
                      />
                      <text
                        x={midX}
                        y={midY - 3}
                        textAnchor="middle"
                        className="fill-neutral-400 text-[10px] uppercase tracking-[0.18em]"
                      >
                        {edge.edge_type}
                      </text>
                    </>
                  ) : null}
                </g>
              );
            })}

            {positionedNodes.map((node) => {
              const isSelected = selectedNode?.id === node.id;
              const isNeighbor = neighborIds.has(node.id);
              const isTransaction = node.node_type === "transaction";
              const radius = isTransaction ? 20 : 11 + Math.min(node.degree, 7);
              const fill = node.suspicious
                ? graphTheme.suspiciousFill
                : isTransaction
                  ? graphTheme.transactionFill
                  : graphTheme.accountFill;
              const stroke = isSelected
                ? "#ffffff"
                : isNeighbor
                  ? "#f87171"
                  : "rgba(255,255,255,0.14)";

              return (
                <g
                  key={node.id}
                  onClick={() => {
                    setSelectedNodeId(node.id);
                    if (node.node_type === "transaction" && onTransactionSelect) {
                      onTransactionSelect(node.id.replace(/^transaction:/, ""));
                    }
                  }}
                  className="cursor-pointer"
                  style={{ opacity: isSelected || isNeighbor || !selectedNode ? 1 : 0.56 }}
                >
                  {isTransaction ? (
                    <rect
                      x={node.x - radius}
                      y={node.y - radius}
                      width={radius * 2}
                      height={radius * 2}
                      rx="10"
                      fill={fill}
                      stroke={stroke}
                      strokeWidth={isSelected ? 3 : 1.6}
                    />
                  ) : (
                    <circle
                      cx={node.x}
                      cy={node.y}
                      r={radius}
                      fill={fill}
                      stroke={stroke}
                      strokeWidth={isSelected ? 3 : 1.6}
                    />
                  )}
                  {node.suspicious ? (
                    <circle
                      cx={node.x + radius - 3}
                      cy={node.y - radius + 3}
                      r="5"
                      fill="#facc15"
                      stroke="#111111"
                      strokeWidth="1.2"
                    />
                  ) : null}
                  <text
                    x={node.x}
                    y={node.y + radius + 16}
                    textAnchor="middle"
                    className="fill-neutral-300 text-[11px]"
                  >
                    {node.label.length > 18
                      ? `${node.label.slice(0, 8)}...${node.label.slice(-4)}`
                      : node.label}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>
        </div>

        <div className="rounded-2xl border border-neutral-900 bg-neutral-950/90 p-5">
          <p className="text-xs font-bold uppercase tracking-[0.28em] text-red-400">
            Relationship Inspector
          </p>
          {selectedNode ? (
            <div className="mt-4 space-y-4">
              <InfoRow label="Label" value={selectedNode.label} />
              <InfoRow label="Node Type" value={selectedNode.node_type} />
              <InfoRow label="Degree" value={selectedNode.degree} />
              <InfoRow
                label="Total Amount"
                value={formatAmount(selectedNode.total_amount)}
              />
              <InfoRow
                label="Activity Count"
                value={selectedNode.activity_count ?? "--"}
              />
              <InfoRow
                label="Suspicious"
                value={selectedNode.suspicious ? "Yes" : "No"}
              />
              <div className="rounded-xl border border-neutral-900 bg-black/40 p-4">
                <p className="text-xs font-bold uppercase tracking-[0.18em] text-neutral-500">
                  Why This Matters
                </p>
                <p className="mt-2 text-sm leading-6 text-neutral-300">
                  The GNN uses these sender, transaction, and receiver connections as
                  message-passing paths. That lets it score a transaction using both its
                  own features and the behavior of neighboring entities.
                </p>
              </div>
              <div className="border-t border-neutral-900 pt-4">
                <p className="text-xs font-bold uppercase tracking-[0.22em] text-neutral-500">
                  Connected Edges
                </p>
                <div className="mt-3 space-y-3">
                  {visibleGraph.edges
                    .filter(
                      (edge) =>
                        edge.source === selectedNode.id || edge.target === selectedNode.id,
                    )
                    .slice(0, 8)
                    .map((edge) => (
                      <div
                        key={`${edge.source}-${edge.target}`}
                        className="rounded-xl border border-neutral-900 bg-black/40 p-3 text-sm text-neutral-300"
                      >
                        <div className="flex items-center justify-between gap-3">
                          <p className="font-semibold text-white">{edge.edge_type}</p>
                          <span className="rounded-full bg-red-950/70 px-2 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-red-300">
                            {edge.risk_score ? "high risk" : "observed"}
                          </span>
                        </div>
                        <p className="mt-1 text-xs text-neutral-500">
                          {edge.source} → {edge.target}
                        </p>
                        <p className="mt-2 text-xs text-red-300">
                          Amount {formatAmount(edge.total_amount)} | Count {edge.count}
                        </p>
                      </div>
                    ))}
                </div>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function GraphStat({ label, value, tone }) {
  const toneClasses = {
    neutral: "text-white",
    red: "text-red-400",
    amber: "text-amber-300",
  };

  return (
    <div className="rounded-xl border border-neutral-900 bg-neutral-950/90 px-4 py-3">
      <p className="text-[11px] uppercase tracking-[0.24em] text-neutral-500">{label}</p>
      <p className={`mt-2 text-2xl font-black ${toneClasses[tone]}`}>{value}</p>
    </div>
  );
}

function ViewButton({ active, label, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`rounded-full px-3 py-2 text-xs font-bold uppercase tracking-[0.18em] transition ${
        active
          ? "bg-red-600 text-white"
          : "border border-neutral-800 bg-black/50 text-neutral-400 hover:border-red-700 hover:text-white"
      }`}
    >
      {label}
    </button>
  );
}

function InfoRow({ label, value }) {
  return (
    <div className="flex items-center justify-between border-b border-neutral-900 pb-3 text-sm last:border-b-0">
      <span className="uppercase tracking-[0.18em] text-neutral-500">{label}</span>
      <span className="max-w-[55%] text-right font-semibold text-white">{value}</span>
    </div>
  );
}
