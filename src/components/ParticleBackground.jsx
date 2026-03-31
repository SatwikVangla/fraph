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

  if (!init) {
    return null;
  }

  return (
    <div style={{ position: "absolute", inset: 0, pointerEvents: "none", zIndex: 1 }}>
      <Particles
        id="fraud-network"
        style={{ position: "absolute", inset: 0 }}
        options={{
          fullScreen: { enable: false },
          background: { color: "transparent" },
          fpsLimit: 60,
          interactivity: {
            events: {
              onHover: {
                enable: true,
                mode: "grab",
              },
              resize: {
                enable: true,
              },
            },
            modes: {
              grab: {
                distance: 180,
                links: {
                  opacity: 0.35,
                },
              },
            },
          },
          particles: {
            number: {
              density: {
                enable: true,
                area: 900,
              },
              value: 120,
            },
            color: {
              value: ["#671019", "#8a1018", "#d61f2c", "#ff4d5a"],
            },
            opacity: {
              value: { min: 0.18, max: 0.8 },
            },
            shape: {
              type: "circle",
            },
            size: {
              value: { min: 1, max: 4.5 },
            },
            links: {
              enable: true,
              color: "#8a1018",
              distance: 160,
              opacity: 0.22,
              width: 1,
              triangles: {
                enable: false,
              },
            },
            move: {
              enable: true,
              speed: { min: 0.18, max: 0.6 },
              direction: "none",
              random: true,
              straight: false,
              outModes: {
                default: "out",
              },
              attract: {
                enable: true,
                distance: 180,
                rotate: {
                  x: 600,
                  y: 1200,
                },
              },
              trail: {
                enable: false,
              },
            },
            twinkle: {
              particles: {
                enable: true,
                frequency: 0.035,
                opacity: 1,
                color: "#ff8a92",
              },
            },
          },
          detectRetina: true,
        }}
      />
    </div>
  );
}
