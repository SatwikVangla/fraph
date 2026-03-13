import { useEffect, useState } from "react";
import Particles, { initParticlesEngine } from "@tsparticles/react";
import { loadSlim } from "@tsparticles/slim";

export default function ParticleBackground() {
  const [init, setInit] = useState(false);

  useEffect(() => {
    initParticlesEngine(async (engine) => {
      await loadSlim(engine);
    }).then(() => {
      setInit(true);
    });
  }, []);

  if (!init) return null;

  return (
    // FIX 1: Wrapper must be position:relative with explicit 100% dimensions
    // so tsParticles has a real bounding box to render into.
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <Particles
        id="tsparticles"
        // FIX 2: Inline style guarantees the canvas fills the wrapper,
        // overriding any Tailwind reset that might zero out h-full.
        style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}
        options={{
          // CRITICAL: Prevents particles from jumping to the <body> tag
          fullScreen: { enable: false },
          background: { color: "transparent" },
          fpsLimit: 120,
          interactivity: {
            events: {
              onHover: { enable: true, mode: "grab" },
            },
            modes: {
              grab: {
                distance: 140,
                links: { opacity: 0.5 },
              },
            },
          },
          particles: {
            color: { value: "#ffffff" },
            links: {
              color: "#ffffff",
              distance: 150,
              enable: true,
              opacity: 0.3,
              width: 1,
            },
            move: {
              direction: "none",
              enable: true,
              outModes: { default: "bounce" },
              random: false,
              speed: 1,
              straight: false,
            },
            number: {
              density: { enable: true },
              value: 100,
            },
            opacity: { value: 0.5 },
            shape: { type: "circle" },
            size: { value: { min: 1, max: 3 } },
          },
          detectRetina: true,
        }}
      />
    </div>
  );
}
