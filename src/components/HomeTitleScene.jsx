import { Canvas, useFrame } from "@react-three/fiber";
import { useEffect, useMemo, useRef } from "react";
import * as THREE from "three";

const NODE_LAYOUT = [
  { id: "n1", position: [-3.6, 1.4, -1.1], scale: 0.18, type: "normal" },
  { id: "n2", position: [-2.2, 2.05, 0.9], scale: 0.12, type: "normal" },
  { id: "n3", position: [-0.85, 1.25, -0.3], scale: 0.14, type: "alert" },
  { id: "n4", position: [1.25, 2.15, 0.85], scale: 0.11, type: "normal" },
  { id: "n5", position: [3.05, 1.1, -0.75], scale: 0.16, type: "normal" },
  { id: "n6", position: [3.9, -0.55, 0.35], scale: 0.14, type: "alert" },
  { id: "n7", position: [2.35, -1.85, -0.65], scale: 0.13, type: "normal" },
  { id: "n8", position: [0.25, -2.2, 0.2], scale: 0.16, type: "normal" },
  { id: "n9", position: [-2.3, -1.7, 0.55], scale: 0.13, type: "normal" },
  { id: "n10", position: [-3.95, -0.15, -0.85], scale: 0.12, type: "alert" },
];

const EDGES = [
  [0, 1],
  [1, 2],
  [2, 3],
  [3, 4],
  [4, 5],
  [5, 6],
  [6, 7],
  [7, 8],
  [8, 9],
  [9, 0],
  [2, 7],
  [1, 8],
  [3, 6],
  [0, 2],
  [4, 7],
];

function createTitleTexture({ title, subtitle, tint }) {
  const canvas = document.createElement("canvas");
  canvas.width = 2048;
  canvas.height = 1024;
  const context = canvas.getContext("2d");

  if (!context) {
    return null;
  }

  context.clearRect(0, 0, canvas.width, canvas.height);
  context.textAlign = "center";
  context.textBaseline = "middle";

  const gradient = context.createLinearGradient(0, 260, 0, 700);
  gradient.addColorStop(0, tint === "primary" ? "rgba(255,243,244,0.98)" : "rgba(255,102,114,0.95)");
  gradient.addColorStop(1, tint === "primary" ? "rgba(255,214,217,0.92)" : "rgba(186,15,27,0.95)");

  context.shadowColor = tint === "primary" ? "rgba(255,110,122,0.28)" : "rgba(120,10,18,0.42)";
  context.shadowBlur = tint === "primary" ? 34 : 22;
  context.fillStyle = gradient;
  context.font = '800 316px "Space Grotesk", "Avenir Next", sans-serif';
  context.letterSpacing = "0.24em";
  context.fillText(title, canvas.width / 2, 420);

  context.shadowBlur = 0;
  context.fillStyle = "rgba(255,180,185,0.9)";
  context.font = '700 56px "Space Grotesk", "Avenir Next", sans-serif';
  context.fillText(subtitle, canvas.width / 2, 650);

  const texture = new THREE.CanvasTexture(canvas);
  texture.needsUpdate = true;
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.minFilter = THREE.LinearFilter;
  texture.magFilter = THREE.LinearFilter;
  return texture;
}

function ConnectionLines({ pointerRef }) {
  const groupRef = useRef(null);
  const pulseRef = useRef(null);

  const segments = useMemo(
    () =>
      EDGES.map(([startIndex, endIndex]) => {
        const start = new THREE.Vector3(...NODE_LAYOUT[startIndex].position);
        const end = new THREE.Vector3(...NODE_LAYOUT[endIndex].position);
        const direction = new THREE.Vector3().subVectors(end, start);
        const length = direction.length();
        const midpoint = new THREE.Vector3().addVectors(start, end).multiplyScalar(0.5);
        const quaternion = new THREE.Quaternion().setFromUnitVectors(
          new THREE.Vector3(0, 1, 0),
          direction.clone().normalize(),
        );

        return {
          key: `${NODE_LAYOUT[startIndex].id}-${NODE_LAYOUT[endIndex].id}`,
          length,
          midpoint,
          quaternion,
        };
      }),
    [],
  );

  useFrame(({ clock }, delta) => {
    const elapsed = clock.getElapsedTime();
    const pointer = pointerRef.current;

    if (groupRef.current) {
      groupRef.current.position.z = -0.1;
      groupRef.current.rotation.z = THREE.MathUtils.lerp(
        groupRef.current.rotation.z,
        Math.sin(elapsed * 0.18) * 0.16 + pointer.x * 0.12,
        delta * 2.4,
      );
      groupRef.current.rotation.x = THREE.MathUtils.lerp(
        groupRef.current.rotation.x,
        Math.cos(elapsed * 0.14) * 0.08 + pointer.y * 0.1,
        delta * 2.4,
      );
      groupRef.current.position.x = THREE.MathUtils.lerp(groupRef.current.position.x, -0.62 + pointer.x * 0.28, delta * 2.2);
      groupRef.current.position.y = THREE.MathUtils.lerp(groupRef.current.position.y, pointer.y * 0.3, delta * 2.2);
    }

    if (pulseRef.current) {
      pulseRef.current.position.x = ((elapsed * 2.2) % 10) - 5;
      pulseRef.current.position.y = pointer.y * 0.22;
      pulseRef.current.material.opacity = 0.16 + Math.sin(elapsed * 2.8) * 0.08;
    }
  });

  return (
    <group ref={groupRef}>
      {segments.map((segment, index) => (
        <mesh key={segment.key} position={segment.midpoint} quaternion={segment.quaternion}>
          <cylinderGeometry args={[0.018, 0.018, segment.length, 10]} />
          <meshStandardMaterial
            color={index % 4 === 0 ? "#ff6b74" : "#8f111b"}
            emissive={index % 4 === 0 ? "#7f0d16" : "#2c0508"}
            transparent
            opacity={0.62}
            roughness={0.24}
            metalness={0.35}
          />
        </mesh>
      ))}

      <mesh ref={pulseRef} position={[-5, 0, 0.18]}>
        <planeGeometry args={[0.34, 6.2]} />
        <meshBasicMaterial color="#ff7a82" transparent opacity={0.2} />
      </mesh>
    </group>
  );
}

function DataNodes({ pointerRef }) {
  const groupRef = useRef(null);
  const nodeRefs = useRef([]);

  useFrame(({ clock }, delta) => {
    const elapsed = clock.getElapsedTime();
    const pointer = pointerRef.current;

    if (groupRef.current) {
      groupRef.current.rotation.y = THREE.MathUtils.lerp(
        groupRef.current.rotation.y,
        Math.sin(elapsed * 0.2) * 0.22 + pointer.x * 0.28,
        delta * 2,
      );
      groupRef.current.rotation.x = THREE.MathUtils.lerp(groupRef.current.rotation.x, pointer.y * 0.14, delta * 2);
      groupRef.current.position.x = THREE.MathUtils.lerp(groupRef.current.position.x, -0.9 + pointer.x * 0.18, delta * 1.8);
      groupRef.current.position.y = THREE.MathUtils.lerp(
        groupRef.current.position.y,
        Math.sin(elapsed * 0.5) * 0.08 + pointer.y * 0.18,
        delta * 1.8,
      );
    }

    nodeRefs.current.forEach((mesh, index) => {
      if (!mesh) {
        return;
      }
      const base = NODE_LAYOUT[index];
      mesh.position.y = base.position[1] + Math.sin(elapsed * (0.8 + index * 0.11)) * 0.12;
      mesh.rotation.x += 0.005 + index * 0.0004;
      mesh.rotation.y += 0.007 + index * 0.0005;
    });
  });

  return (
    <group ref={groupRef}>
      {NODE_LAYOUT.map((node, index) => (
        <mesh
          key={node.id}
          ref={(element) => {
            nodeRefs.current[index] = element;
          }}
          position={node.position}
        >
          <icosahedronGeometry args={[node.scale, 1]} />
          <meshStandardMaterial
            color={node.type === "alert" ? "#ff5b66" : "#f7d6d8"}
            emissive={node.type === "alert" ? "#b60e19" : "#591017"}
            emissiveIntensity={node.type === "alert" ? 1.45 : 0.5}
            roughness={0.18}
            metalness={0.62}
          />
        </mesh>
      ))}
    </group>
  );
}

function ForgeTitle({ pointerRef }) {
  const titleRef = useRef(null);
  const haloRef = useRef(null);
  const primaryTexture = useMemo(
    () => createTitleTexture({ title: "FRAPH", subtitle: "FRAUD RELATIONSHIP ANALYSIS PLATFORM HUB", tint: "primary" }),
    [],
  );
  const accentTexture = useMemo(
    () => createTitleTexture({ title: "FRAPH", subtitle: "FRAUD RELATIONSHIP ANALYSIS PLATFORM HUB", tint: "accent" }),
    [],
  );

  useEffect(() => {
    return () => {
      primaryTexture?.dispose();
      accentTexture?.dispose();
    };
  }, [primaryTexture, accentTexture]);

  useFrame(({ clock }, delta) => {
    const elapsed = clock.getElapsedTime();
    const pointer = pointerRef.current;

    if (titleRef.current) {
      titleRef.current.rotation.x = THREE.MathUtils.lerp(
        titleRef.current.rotation.x,
        -0.08 + Math.sin(elapsed * 0.6) * 0.02 + pointer.y * 0.08,
        delta * 2.1,
      );
      titleRef.current.rotation.y = THREE.MathUtils.lerp(
        titleRef.current.rotation.y,
        Math.sin(elapsed * 0.38) * 0.28 + pointer.x * 0.32,
        delta * 2.1,
      );
      titleRef.current.position.x = THREE.MathUtils.lerp(titleRef.current.position.x, -1.1 + pointer.x * 0.18, delta * 1.9);
      titleRef.current.position.y = THREE.MathUtils.lerp(
        titleRef.current.position.y,
        -0.18 + Math.sin(elapsed * 0.75) * 0.09 + pointer.y * 0.18,
        delta * 1.9,
      );
    }

    if (haloRef.current) {
      haloRef.current.scale.x = 1.55 + Math.sin(elapsed * 1.3) * 0.08;
      haloRef.current.scale.y = 0.82 + Math.cos(elapsed * 1.3) * 0.06;
      haloRef.current.position.x = -0.95 + pointer.x * 0.12;
      haloRef.current.position.y = -0.32 + pointer.y * 0.12;
      haloRef.current.material.opacity = 0.24 + Math.sin(elapsed * 1.6) * 0.06;
    }
  });

  return (
    <group>
      <mesh ref={haloRef} position={[-0.95, -0.32, -1.35]} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[2.4, 3.7, 64]} />
        <meshBasicMaterial color="#ff4f5f" transparent opacity={0.26} side={THREE.DoubleSide} />
      </mesh>

      <group ref={titleRef} position={[-1.1, -0.18, 0.28]}>
        <mesh position={[0.05, -0.07, 0]}>
          <planeGeometry args={[6.8, 3.4]} />
          <meshBasicMaterial map={accentTexture} transparent depthWrite={false} />
        </mesh>
        <mesh position={[0, 0, 0.32]}>
          <planeGeometry args={[6.8, 3.4]} />
          <meshBasicMaterial map={primaryTexture} transparent depthWrite={false} />
        </mesh>
      </group>
    </group>
  );
}

function SceneRig({ pointerRef }) {
  const cameraRef = useRef(null);

  useFrame(({ clock }, delta) => {
    const elapsed = clock.getElapsedTime();
    const pointer = pointerRef.current;

    if (cameraRef.current) {
      cameraRef.current.position.x = THREE.MathUtils.lerp(
        cameraRef.current.position.x,
        -0.3 + Math.sin(elapsed * 0.18) * 0.42 + pointer.x * 0.45,
        delta * 1.6,
      );
      cameraRef.current.position.y = THREE.MathUtils.lerp(
        cameraRef.current.position.y,
        0.2 + Math.cos(elapsed * 0.22) * 0.18 + pointer.y * 0.45,
        delta * 1.6,
      );
      cameraRef.current.lookAt(-0.6 + pointer.x * 0.24, pointer.y * 0.22, 0);
    }
  });

  return (
    <>
      <perspectiveCamera ref={cameraRef} makeDefault position={[0, 0.2, 7.6]} fov={32} />
      <color attach="background" args={["#0a0506"]} />
      <fog attach="fog" args={["#0a0506", 7.5, 15]} />
      <ambientLight intensity={0.75} color="#ffe1e4" />
      <directionalLight position={[4, 5, 4]} intensity={1.2} color="#ffe6e8" />
      <pointLight position={[-4, 2, 2]} intensity={22} distance={12} color="#d31320" />
      <pointLight position={[3, -2, 3]} intensity={14} distance={10} color="#ff8f97" />
      <spotLight position={[0, 4.5, 6]} intensity={18} angle={0.36} penumbra={0.8} distance={18} color="#ff6a73" />
      <ConnectionLines pointerRef={pointerRef} />
      <DataNodes pointerRef={pointerRef} />
      <ForgeTitle pointerRef={pointerRef} />
    </>
  );
}

export default function HomeTitleScene() {
  const pointerRef = useRef({ x: 0, y: 0 });

  const handlePointerMove = (event) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = (event.clientX - rect.left) / rect.width;
    const y = (event.clientY - rect.top) / rect.height;

    pointerRef.current = {
      x: (x - 0.5) * 2,
      y: (0.5 - y) * 2,
    };
  };

  const handlePointerLeave = () => {
    pointerRef.current = { x: 0, y: 0 };
  };

  return (
    <div className="hero-canvas-wrap" aria-hidden="true" onPointerMove={handlePointerMove} onPointerLeave={handlePointerLeave}>
      <Canvas dpr={[1, 1.8]} gl={{ antialias: true, alpha: true }}>
        <SceneRig pointerRef={pointerRef} />
      </Canvas>
    </div>
  );
}
