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
    <div style={{ position: "absolute", inset: 0,pointerEvents: "none", zIndex: 1 }}>
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
                mode: "connect"
              }
            },
            modes: {
              connect: {
                distance: 170,
                links: {
                  opacity: 0.6
                }
              }
            }
          },

          particles: {
            number: {
              density: {
                enable: true
              },
              value: 140
            },

            color: {
              value: ["#ffffff", "#ffffff", "#ffffff", "#ff0000"]
            },

            shape: {
              type: "circle"
            },

            size: {
              value: { min: 1, max: 3 }
            },

            opacity: {
              value: 0.6
            },

            links: {
              enable: true,
              color: "#ffffff",
              distance: 170,
              opacity: 0.35,
              width: 1
            },

            move: {
              enable: true,
              speed: 0.5,
              direction: "none",
              random: false,
              straight: false,
              outModes: {
                default: "bounce"
              }
            },

            twinkle: {
              particles: {
                enable: true,
                frequency: 0.05,
                opacity: 1
              }
            }
          },

          detectRetina: true
        }}
      />
    </div>
  );
}
