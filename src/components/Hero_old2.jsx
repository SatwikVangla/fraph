import Spline from '@splinetool/react-spline';
import { useState } from 'react';
import ParticleBackground from "./ParticleBackground";

export default function Hero() {
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

  const handleMouseMove = (e) => {
    // Parallax logic
    const x = (e.clientX / window.innerWidth - 0.5) * 15;
    const y = (e.clientY / window.innerHeight - 0.5) * 15;
    setMousePos({ x, y });
  };

  return (
    <section 
      onMouseMove={handleMouseMove}
      className="relative h-screen w-full bg-black text-white flex items-center justify-center overflow-hidden"
    >
      {/* LAYER 0: 3D Spline Scene (Foundation) */}
      <div className="absolute inset-0 z-0 h-full w-full">
        <Spline scene="https://prod.spline.design/2cc82344-8f3c-4702-92a0-e9276e998ae9/scene.splinecode" />
      </div>

      {/* LAYER 1: Particles (Overlay Atmosphere) */}
      {/* CRITICAL: pointer-events-none ensures you can still click the UI below */}
      <div className="absolute inset-0 z-10 h-full w-full opacity-40 pointer-events-none">
        <ParticleBackground />
      </div>

      {/* LAYER 2: Wavy Texture (PewDiePie Aesthetic) */}
      <div className="wavy-texture z-20" />

      {/* LAYER 3: Focus Vignette */}
      <div className="absolute inset-0 z-30 pointer-events-none bg-[radial-gradient(circle_at_center,_transparent_0%,_rgba(0,0,0,0.5)_80%,_black_100%)]"></div>

      {/* LAYER 4: Content (Highest Layer) */}
      <div className="relative z-40 text-center space-y-8 select-none">
        <div className="relative">
          <h1 
            className="glitch-text text-8xl md:text-[10rem] font-black tracking-tighter leading-none"
            style={{
              transform: `translate3d(${mousePos.x}px, ${mousePos.y}px, 0)`,
              textShadow: `${-mousePos.x}px ${-mousePos.y}px 0px rgba(255, 0, 0, 0.5)`,
              transition: 'transform 0.1s ease-out'
            }}
          >
            FRAPH
          </h1>
        </div>

        <div className="space-y-4 pointer-events-auto">
          <p className="text-lg md:text-xl font-bold tracking-[0.4em] text-red-600 uppercase">
            Fraud Recognition <span className="text-white">/</span> Graph Intelligence
          </p>
          <p className="text-gray-400 max-w-xl mx-auto text-sm md:text-base px-6">
            Detecting financial anomalies through deep relational analysis.
          </p>
          <div className="pt-4">
            <button className="btn-glow px-12 py-4 bg-transparent border-2 border-red-600 text-white font-black uppercase tracking-widest hover:bg-red-600 transition-all duration-300">
              Analyze Network
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
