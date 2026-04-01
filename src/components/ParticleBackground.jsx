import { useEffect, useState } from "react";
import Particles, { initParticlesEngine } from "@tsparticles/react";
import { loadSlim } from "@tsparticles/slim";

export default function ParticleBackground() {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;

    initParticlesEngine(async (engine) => {
      await loadSlim(engine);
    }).then(() => {
      if (!cancelled) {
        setReady(true);
      }
    });

    return () => {
      cancelled = true;
    };
  }, []);

  if (!ready) {
    return null;
  }

  return (
    <Particles
      id="homepage-particles"
      className="particle-canvas"
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
                opacity: 0.45,
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
            value: 95,
          },
          color: {
            value: ["#ff2b3a", "#ff5e68", "#9f1018", "#5b070c"],
          },
          links: {
            enable: true,
            color: "#b9131d",
            distance: 145,
            opacity: 0.24,
            width: 1,
          },
          move: {
            attract: {
              enable: true,
              rotate: {
                x: 1000,
                y: 1400,
              },
            },
            direction: "none",
            enable: true,
            outModes: {
              default: "bounce",
            },
            random: true,
            speed: { min: 0.2, max: 0.65 },
            straight: false,
          },
          opacity: {
            value: { min: 0.18, max: 0.7 },
          },
          shape: {
            type: "circle",
          },
          size: {
            value: { min: 1, max: 3.6 },
          },
          twinkle: {
            particles: {
              enable: true,
              color: "#ff9097",
              frequency: 0.02,
              opacity: 1,
            },
          },
        },
        detectRetina: true,
      }}
    />
  );
}
