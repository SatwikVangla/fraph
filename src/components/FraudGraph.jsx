import ReactFlow, { Background, Controls } from "reactflow";
import "reactflow/dist/style.css";

const nodes = [
{
id: "1",
position: { x: 100, y: 100 },
data: { label: "Account A" }
},
{
id: "2",
position: { x: 400, y: 100 },
data: { label: "Account B" }
},
{
id: "3",
position: { x: 250, y: 300 },
data: { label: "Fraud Account 🔴" },
style: {
background: "#ff0000",
color: "white"
}
}
];

const edges = [
{ id: "e1", source: "1", target: "2", label: "$400" },
{ id: "e2", source: "2", target: "3", label: "$1200" }
];

export default function FraudGraph() {
return (
<div style={{ height: "600px", width: "100%" }}> <ReactFlow nodes={nodes} edges={edges} fitView> <Background /> <Controls /> </ReactFlow> </div>
);
}

