export default function PlaceholderGraph() {

const nodes = [
{ id: 1, x: 80, y: 80 },
{ id: 2, x: 300, y: 80 },
{ id: 3, x: 190, y: 180, fraud: true },
{ id: 4, x: 80, y: 280 },
{ id: 5, x: 300, y: 280 }
];

const edges = [
[1,2],
[1,3],
[2,3],
[3,4],
[3,5]
];

const getNode = (id) => nodes.find(n => n.id === id);

return (


<div className="w-full h-full flex items-center justify-center">

  <svg width="400" height="350">

    {/* EDGES */}

    {edges.map(([a,b],i)=>{

      const n1 = getNode(a);
      const n2 = getNode(b);

      return (
        <line
          key={i}
          x1={n1.x}
          y1={n1.y}
          x2={n2.x}
          y2={n2.y}
          stroke="rgba(255,255,255,0.4)"
          strokeWidth="2"
        />
      );
    })}

    {/* NODES */}

    {nodes.map((node,i)=>(
      <circle
        key={i}
        cx={node.x}
        cy={node.y}
        r="8"
        className={node.fraud ? "fraud-node" : "normal-node"}
      />
    ))}

  </svg>

</div>


);
}

