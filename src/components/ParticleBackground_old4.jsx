import { useEffect, useState } from "react";
import Particles, { initParticlesEngine } from "@tsparticles/react";
import { loadSlim } from "@tsparticles/slim";

export default function ParticleBackground() {
  const [init, setInit] = useState(false);

  useEffect(() => {
    initParticlesEngine(async (engine) => {
      await loadSlim(engine);
    }).then(() => setInit(true));
  }, []);

  if (!init) return null;

  return (
    <Particles
      id="tsparticles"
      className="h-full w-full"
      options={{
        fullScreen: { enable: false }, // Prevents it from jumping to body tag
        background: { color: "transparent" }, // Allows layers below to show
        particles: {
          number: { value: 100, density: { enable: true, area: 800 } },
          color: { value: "#ffffff" },
          links: { enable: true, color: "#ffffff", distance: 150, opacity: 0.2 },
          move: { enable: true, speed: 1 },
          size: { value: { min: 1, max: 2 } }
        },
        interactivity: {
          events: { onHover: { enable: true, mode: "grab" } }
        },
        detectRetina: true
      }}
    />
  );
}
