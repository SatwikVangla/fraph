import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import ParticleBackground from "./ParticleBackground";

const SPLINE_SCENE_URL =
  "https://prod.spline.design/2cc82344-8f3c-4702-92a0-e9276e998ae9/scene.splinecode";

function shouldRenderSpline() {
  if (typeof window === "undefined") {
    return false;
  }

  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const compactViewport = window.innerWidth < 1024;
  const saveData = Boolean(navigator.connection?.saveData);

  return !reducedMotion && !compactViewport && !saveData;
}

export default function Hero() {
  const navigate = useNavigate();
  const titleRef = useRef(null);
  const [SplineComponent, setSplineComponent] = useState(null);
  const [showSpline, setShowSpline] = useState(false);
  const [splineFailed, setSplineFailed] = useState(false);

  useEffect(() => {
    if (!shouldRenderSpline()) {
      return undefined;
    }

    let cancelled = false;
    const idleHandle = window.setTimeout(async () => {
      try {
        const module = await import("@splinetool/react-spline");
        if (!cancelled) {
          setSplineComponent(() => module.default);
          setShowSpline(true);
        }
      } catch {
        if (!cancelled) {
          setSplineFailed(true);
        }
      }
    }, 250);

    return () => {
      cancelled = true;
      window.clearTimeout(idleHandle);
    };
  }, []);

  const handleMouseMove = (event) => {
    if (!titleRef.current) {
      return;
    }

    const x = (event.clientX / window.innerWidth - 0.5) * 15;
    const y = (event.clientY / window.innerHeight - 0.5) * 15;

    titleRef.current.style.transform = `translate3d(${x}px, ${y}px, 0)`;
    titleRef.current.style.textShadow = `${-x}px ${-y}px 0 rgba(255,0,0,0.6)`;
  };

  return (
    <section
      onMouseMove={handleMouseMove}
      className="relative isolate flex h-screen w-full items-center justify-center overflow-hidden bg-black text-white"
    >
      <div
        className="absolute inset-0 z-0"
        style={{
          background:
            "radial-gradient(circle at top, rgba(220, 38, 38, 0.28), transparent 38%), linear-gradient(180deg, #080808 0%, #000000 45%, #050505 100%)",
        }}
      />

      <div className="absolute inset-0 z-0 pointer-events-none">
        {showSpline && SplineComponent && !splineFailed ? (
          <SplineComponent
            scene={SPLINE_SCENE_URL}
            style={{
              width: "100%",
              height: "100%",
              pointerEvents: "none",
              opacity: 0.95,
            }}
          />
        ) : null}
      </div>

      <div className="absolute inset-0 z-10 pointer-events-none opacity-40">
        <ParticleBackground />
      </div>

      <div className="wavy-texture absolute inset-0 z-20 pointer-events-none" />

      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(circle at center, transparent 0%, rgba(0, 0, 0, 0.88) 82%, #000 100%)",
          zIndex: 25,
        }}
      />

      <div className="relative z-[100] text-center space-y-8 select-none px-6">
        <h1
          ref={titleRef}
          className="glitch-text text-7xl font-black tracking-tighter transition-transform duration-75 md:text-[10rem]"
        >
          FRAPH
        </h1>

        <div className="space-y-4 pointer-events-auto">
          <p className="text-sm font-bold uppercase tracking-[0.5em] text-red-600 md:text-xl">
            Fraud Recognition <span className="text-white">/</span> Graph Intelligence
          </p>

          <p className="mx-auto max-w-2xl text-sm text-zinc-300 md:text-base">
            Transaction intelligence tuned for dense fraud networks, ranked comparisons,
            and graph-first anomaly analysis.
          </p>

          <button
            onClick={() => navigate("/upload")}
            className="btn-glow mt-8 border-2 border-red-600 bg-transparent px-12 py-4 font-black uppercase tracking-widest text-white transition-all duration-300 hover:bg-red-600"
          >
            Analyze Network
          </button>

          {splineFailed ? (
            <p className="text-xs uppercase tracking-[0.3em] text-zinc-500">
              3D scene disabled. Fallback hero loaded.
            </p>
          ) : null}
        </div>
      </div>
    </section>
  );
}
