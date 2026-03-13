import Spline from '@splinetool/react-spline';
import { useState } from 'react';
import ParticleBackground from "./ParticleBackground";

export default function Hero() {
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

  const handleMouseMove = (e) => {
    const x = (e.clientX / window.innerWidth - 0.5) * 20;
    const y = (e.clientY / window.innerHeight - 0.5) * 20;
    setMousePos({ x, y });
  };

  return (
	  <section className="relative h-screen w-full bg-black overflow-hidden" onMouseMove={handleMouseMove}>

    {/* LAYER 0: SPLINE (Back) */}
    <div className="absolute inset-0 z-0 h-full w-full">
      <Spline scene="https://prod.spline.design/2cc82344-8f3c-4702-92a0-e9276e998ae9/scene.splinecode" />
    </div>

    {/* LAYER 1: PARTICLES (Middle) */}
    <div className="absolute inset-0 z-10 h-full w-full pointer-events-none opacity-40">
      <ParticleBackground />
    </div>

    {/* LAYER 2: WAVY OVERLAY (Front-Middle) */}
    <div className="wavy-texture absolute inset-0 z-20 pointer-events-none" />

    {/* LAYER 3: TITLE & UI (Front) */}
    <div className="relative z-50 text-center flex flex-col items-center justify-center h-full pointer-events-none">
      <h1 className="glitch-text text-8xl md:text-9xl font-black text-white"
          style={{ transform: `translate3d(${mousePos.x}px, ${mousePos.y}px, 0)` }}>
        FRAPH
      </h1>
      <div className="pointer-events-auto mt-6">
        <button className="px-8 py-3 border-2 border-red-600 text-red-600 font-bold uppercase">
          Analyze Network
        </button>
      </div>
    </div>

  </section>
  );
}
