import { useMemo, useState } from "react";

const NODE_LAYOUT = [
  { id: "n1", x: 16, y: 28, size: 8, type: "normal" },
  { id: "n2", x: 27, y: 19, size: 6, type: "normal" },
  { id: "n3", x: 39, y: 31, size: 7, type: "alert" },
  { id: "n4", x: 53, y: 18, size: 6, type: "normal" },
  { id: "n5", x: 68, y: 29, size: 8, type: "normal" },
  { id: "n6", x: 78, y: 44, size: 7, type: "alert" },
  { id: "n7", x: 63, y: 60, size: 6, type: "normal" },
  { id: "n8", x: 46, y: 66, size: 8, type: "normal" },
  { id: "n9", x: 28, y: 57, size: 6, type: "normal" },
  { id: "n10", x: 17, y: 45, size: 7, type: "alert" },
];

const EDGES = [
  ["n1", "n2"],
  ["n2", "n3"],
  ["n3", "n4"],
  ["n4", "n5"],
  ["n5", "n6"],
  ["n6", "n7"],
  ["n7", "n8"],
  ["n8", "n9"],
  ["n9", "n10"],
  ["n10", "n1"],
  ["n3", "n8"],
  ["n2", "n9"],
  ["n4", "n7"],
  ["n1", "n3"],
  ["n5", "n8"],
];

function buildEdgeMap() {
  return new Map(NODE_LAYOUT.map((node) => [node.id, node]));
}

export default function HomeTitleScene() {
  const [pointer, setPointer] = useState({ x: 0, y: 0 });
  const nodeMap = useMemo(() => buildEdgeMap(), []);

  const handlePointerMove = (event) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = ((event.clientX - rect.left) / rect.width - 0.5) * 2;
    const y = (0.5 - (event.clientY - rect.top) / rect.height) * 2;
    setPointer({ x, y });
  };

  const handlePointerLeave = () => {
    setPointer({ x: 0, y: 0 });
  };

  return (
    <div
      className="homev2-title-scene"
      aria-hidden="true"
      onPointerMove={handlePointerMove}
      onPointerLeave={handlePointerLeave}
      style={{
        "--scene-tilt-x": `${pointer.y * 7}deg`,
        "--scene-tilt-y": `${pointer.x * 9}deg`,
        "--scene-shift-x": `${pointer.x * 18}px`,
        "--scene-shift-y": `${pointer.y * -14}px`,
      }}
    >
      <div className="homev2-title-scene-grid" />
      <div className="homev2-title-scene-glow" />
      <div className="homev2-title-scene-core" />

      <svg
        className="homev2-title-scene-network"
        viewBox="0 0 100 100"
        preserveAspectRatio="xMidYMid slice"
      >
        {EDGES.map(([sourceId, targetId], index) => {
          const source = nodeMap.get(sourceId);
          const target = nodeMap.get(targetId);
          if (!source || !target) {
            return null;
          }
          return (
            <line
              key={`${sourceId}-${targetId}`}
              x1={source.x}
              y1={source.y}
              x2={target.x}
              y2={target.y}
              className={index % 4 === 0 ? "is-hot" : ""}
            />
          );
        })}

        {NODE_LAYOUT.map((node, index) => (
          <g
            key={node.id}
            className={`homev2-title-node ${node.type === "alert" ? "is-alert" : ""}`}
            style={{
              animationDelay: `${index * 0.18}s`,
            }}
          >
            <circle cx={node.x} cy={node.y} r={node.size} className="homev2-title-node-ring" />
            <circle cx={node.x} cy={node.y} r={Math.max(2.5, node.size - 2.5)} className="homev2-title-node-core" />
          </g>
        ))}
      </svg>

      <div className="homev2-title-copy">
        <div className="homev2-title-mark homev2-title-mark-accent">FRAPH</div>
        <div className="homev2-title-mark homev2-title-mark-primary">FRAPH</div>
        <p>Fraud Relationship Analysis Platform Hub</p>
      </div>
    </div>
  );
}
