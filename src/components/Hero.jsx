import Spline from "@splinetool/react-spline";
import { useState } from "react";
import ParticleBackground from "./ParticleBackground";

export default function Hero() {
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

  const handleMouseMove = (e) => {
    const x = (e.clientX / window.innerWidth - 0.5) * 15;
    const y = (e.clientY / window.innerHeight - 0.5) * 15;
    setMousePos({ x, y });
  };

  return (
    <section
      onMouseMove={handleMouseMove}
      className="relative h-screen w-full bg-black text-white flex items-center justify-center overflow-hidden"
    >
      {/* 3D BACKGROUND */}
      <div className="absolute inset-0 z-0">
        <Spline
          scene="https://prod.spline.design/2cc82344-8f3c-4702-92a0-e9276e998ae9/scene.splinecode"
          style={{ width: "100%", height: "100%", pointerEvents: "none" }}
        />
      </div>

      {/* PARTICLES */}
      <div className="absolute inset-0 z-10 opacity-40">
        <ParticleBackground />
      </div>

      {/* WAVY TEXTURE */}
      <div className="wavy-texture absolute inset-0 z-20 pointer-events-none" />

      {/* RADIAL FADE */}
      <div
        className="absolute inset-0 pointer-events-none bg-[radial-gradient(circle_at_center,_transparent_0%,_black_90%)]"
        style={{ zIndex: 25 }}
      />

      {/* CONTENT */}
      <div className="relative z-30 text-center space-y-8 select-none">
        <h1
          className="glitch-text text-8xl md:text-[10rem] font-black tracking-tighter"
          style={{
            transform: `translate3d(${mousePos.x}px, ${mousePos.y}px, 0)`,
            textShadow: `${-mousePos.x}px ${-mousePos.y}px 0px rgba(255,0,0,0.5)`,
          }}
        >
          FRAPH
        </h1>

        <div className="space-y-4">
          <p className="text-lg md:text-xl font-bold tracking-[0.4em] text-red-600 uppercase">
            Fraud Recognition <span className="text-white">/</span> Graph Intelligence
          </p>

          <button className="btn-glow mt-8 px-12 py-4 bg-transparent border-2 border-red-600 text-white font-black uppercase tracking-widest hover:bg-red-600 transition-all duration-300">
            Analyze Network
          </button>
        </div>
      </div>
    </section>
  );
}
