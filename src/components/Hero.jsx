import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import ParticleBackground from "./ParticleBackground";

const SPLINE_SCENE_URL =
  "https://prod.spline.design/2cc82344-8f3c-4702-92a0-e9276e998ae9/scene.splinecode";

const signalCards = [
  {
    value: "Graph-Aware",
    label: "Expose hidden relationships across transaction paths instead of scoring records in isolation.",
  },
  {
    value: "Fraud-Focused",
    label: "Surface suspicious flows, linked entities, and high-risk network regions with a single workflow.",
  },
  {
    value: "Research-Ready",
    label: "Compare classical baselines and graph neural models inside the same fraud analysis workspace.",
  },
];

const workflowSteps = [
  {
    id: "01",
    title: "Upload Transaction Data",
    body: "Start from CSV datasets and normalize sender, receiver, amount, balance, and fraud-label structure.",
  },
  {
    id: "02",
    title: "Construct The Fraud Graph",
    body: "Transform transactions into a connected network that captures relational behavior, transfer flow, and anomaly context.",
  },
  {
    id: "03",
    title: "Compare Detection Models",
    body: "Evaluate graph neural networks alongside traditional fraud classifiers and inspect suspicious transaction clusters.",
  },
];

const metricCards = [
  "Financial fraud detection using graph neural networks",
  "Transaction-level anomaly discovery",
  "Graph-first comparison and training workflow",
];

const systemStats = [
  { label: "Graph modeling", value: "Active" },
  { label: "Fraud tracing", value: "Live" },
  { label: "Model comparison", value: "Ready" },
];

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

    const x = (event.clientX / window.innerWidth - 0.5) * 18;
    const y = (event.clientY / window.innerHeight - 0.5) * 12;

    titleRef.current.style.transform = `translate3d(${x}px, ${y}px, 0)`;
    titleRef.current.style.textShadow = `${-x * 0.75}px ${-y * 0.75}px 36px rgba(214,31,44,0.45)`;
  };

  return (
    <main
      onMouseMove={handleMouseMove}
      className="homepage-shell relative isolate min-h-screen overflow-hidden bg-[#050505] text-white"
    >
      <div className="absolute inset-0 z-0 bg-[radial-gradient(circle_at_top,rgba(214,31,44,0.24),transparent_32%),linear-gradient(180deg,#170608_0%,#070707_42%,#040404_100%)]" />
      <div className="absolute inset-0 z-0 bg-[radial-gradient(circle_at_80%_18%,rgba(255,77,90,0.16),transparent_22%),radial-gradient(circle_at_24%_62%,rgba(111,9,18,0.22),transparent_28%)]" />

      <div className="absolute inset-0 z-10 pointer-events-none opacity-70">
        <ParticleBackground />
      </div>

      <div className="wavy-texture absolute inset-0 z-20 pointer-events-none opacity-70" />
      <div className="scanlines absolute inset-0 z-20 pointer-events-none" />

      <section className="relative z-30 mx-auto flex min-h-screen w-full max-w-7xl flex-col px-6 pb-16 pt-6 sm:px-8 lg:px-10">
        <header className="flex items-center justify-between border-b border-white/10 pb-4">
          <div className="flex items-center gap-3">
            <span className="h-2.5 w-2.5 rounded-full bg-[#ff4d5a] shadow-[0_0_14px_rgba(255,77,90,0.8)]" />
            <span className="text-xs font-medium uppercase tracking-[0.45em] text-white/70">
              FRAPH
            </span>
          </div>
          <div className="hidden text-xs uppercase tracking-[0.32em] text-white/45 md:block">
            Graph-first financial fraud intelligence
          </div>
        </header>

        <div className="grid flex-1 gap-14 py-10 lg:grid-cols-[1.05fr_0.95fr] lg:items-center lg:gap-10">
          <div className="relative">
            <div className="mb-6 inline-flex items-center gap-3 rounded-full border border-[#7f0f18]/80 bg-[#16080a]/90 px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.32em] text-[#f0b6bb] shadow-[0_0_30px_rgba(127,15,24,0.25)]">
              Financial Fraud Detection Using Graph Neural Networks
            </div>

            <h1
              ref={titleRef}
              className="hero-title max-w-4xl text-5xl font-black uppercase leading-[0.95] tracking-[-0.05em] text-white sm:text-6xl md:text-7xl xl:text-[6.8rem]"
            >
              Detect fraud where transactions become networks.
            </h1>

            <p className="mt-6 max-w-2xl text-base leading-7 text-white/72 sm:text-lg">
              FRAPH is a red-themed fraud analysis workspace built for transaction graphs,
              suspicious flow detection, model comparison, and graph neural network research.
            </p>

            <div className="mt-10 flex flex-col gap-4 sm:flex-row">
              <button
                onClick={() => navigate("/upload")}
                className="btn-glow rounded-full border border-[#ff4d5a] bg-[#d61f2c] px-8 py-4 text-sm font-black uppercase tracking-[0.26em] text-white transition duration-300 hover:-translate-y-0.5 hover:bg-[#ef2b39]"
              >
                Analyze Network
              </button>

              <button
                onClick={() => navigate("/dashboard")}
                className="rounded-full border border-white/15 bg-white/5 px-8 py-4 text-sm font-bold uppercase tracking-[0.22em] text-white transition duration-300 hover:border-[#ff4d5a]/80 hover:bg-[#25090d]"
              >
                Open Dashboard
              </button>
            </div>

            <div className="mt-12 grid gap-4 sm:grid-cols-3">
              {signalCards.map((card) => (
                <article
                  key={card.value}
                  className="rounded-[1.6rem] border border-white/10 bg-[linear-gradient(180deg,rgba(34,8,11,0.92),rgba(12,6,7,0.88))] p-5 shadow-[0_20px_60px_rgba(0,0,0,0.35)] backdrop-blur"
                >
                  <p className="text-sm font-black uppercase tracking-[0.2em] text-[#ff6a75]">
                    {card.value}
                  </p>
                  <p className="mt-3 text-sm leading-6 text-white/62">{card.label}</p>
                </article>
              ))}
            </div>
          </div>

          <div className="relative min-h-[500px] lg:min-h-[700px]">
            <div className="absolute inset-0 rounded-[2rem] border border-[#9f1621]/30 bg-[radial-gradient(circle_at_50%_45%,rgba(214,31,44,0.18),rgba(8,8,8,0.2)_42%,rgba(3,3,3,0.88)_72%)] shadow-[0_0_100px_rgba(173,20,34,0.22)]" />

            <div className="absolute left-5 right-5 top-5 flex justify-between gap-4 rounded-full border border-white/10 bg-black/20 px-4 py-3 text-[10px] uppercase tracking-[0.35em] text-white/40 backdrop-blur">
              <span>Transaction lattice</span>
              <span>3D fraud surface</span>
            </div>

            <div className="absolute inset-5 overflow-hidden rounded-[1.8rem] border border-white/8 bg-[linear-gradient(180deg,rgba(25,8,11,0.72),rgba(5,5,5,0.35))]">
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(255,77,90,0.12),transparent_42%)]" />
              <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(255,255,255,0.02),transparent_22%,transparent_78%,rgba(255,255,255,0.015))]" />

              <div className="hero-orbit hero-orbit-a" />
              <div className="hero-orbit hero-orbit-b" />
              <div className="hero-core" />
              <div className="hero-grid" />

              <div className="absolute inset-x-8 top-20 z-[1] grid gap-3 sm:grid-cols-3">
                {systemStats.map((stat) => (
                  <div
                    key={stat.label}
                    className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3 backdrop-blur"
                  >
                    <p className="text-[10px] uppercase tracking-[0.28em] text-white/35">
                      {stat.label}
                    </p>
                    <p className="mt-2 text-sm font-black uppercase tracking-[0.18em] text-[#ff8a92]">
                      {stat.value}
                    </p>
                  </div>
                ))}
              </div>

              <div className="absolute inset-0 z-[2] pointer-events-none">
                {showSpline && SplineComponent && !splineFailed ? (
                  <SplineComponent
                    scene={SPLINE_SCENE_URL}
                    style={{
                      width: "100%",
                      height: "100%",
                      pointerEvents: "none",
                      opacity: 0.92,
                    }}
                  />
                ) : null}
              </div>

              <div className="absolute right-6 top-28 z-[3] hidden w-44 rounded-[1.25rem] border border-[#f34b57]/20 bg-[linear-gradient(180deg,rgba(41,10,13,0.72),rgba(13,7,8,0.86))] p-4 backdrop-blur lg:block">
                <p className="text-[10px] font-bold uppercase tracking-[0.32em] text-white/35">
                  Signal map
                </p>
                <div className="mt-4 space-y-3">
                  <div className="flex items-center justify-between border-b border-white/8 pb-2 text-[11px] uppercase tracking-[0.2em] text-white/55">
                    <span>Nodes</span>
                    <span className="text-[#ff6a75]">Dense</span>
                  </div>
                  <div className="flex items-center justify-between border-b border-white/8 pb-2 text-[11px] uppercase tracking-[0.2em] text-white/55">
                    <span>Alerts</span>
                    <span className="text-[#ff6a75]">Flagged</span>
                  </div>
                  <div className="flex items-center justify-between text-[11px] uppercase tracking-[0.2em] text-white/55">
                    <span>Risk pulse</span>
                    <span className="text-[#ff6a75]">Active</span>
                  </div>
                </div>
              </div>

              <div className="pointer-events-none absolute inset-x-6 bottom-6 z-[3] rounded-[1.4rem] border border-[#f34b57]/20 bg-[linear-gradient(180deg,rgba(41,10,13,0.84),rgba(13,7,8,0.94))] p-5 backdrop-blur">
                <p className="text-[11px] font-bold uppercase tracking-[0.36em] text-[#ff7f88]">
                  Detection surface
                </p>
                <p className="mt-3 max-w-md text-sm leading-6 text-white/65">
                  A 3D transaction-lattice scene stays in the hero on desktop, while the red
                  network particles preserve motion and graph context across all viewports.
                </p>
                {splineFailed ? (
                  <p className="mt-3 text-[11px] uppercase tracking-[0.3em] text-white/35">
                    3D scene unavailable. Particle fallback active.
                  </p>
                ) : null}
              </div>
            </div>
          </div>
        </div>

        <div className="grid gap-4 border-y border-white/8 py-8 md:grid-cols-3">
          {metricCards.map((item) => (
            <div
              key={item}
              className="rounded-[1.4rem] border border-white/10 bg-white/[0.03] px-5 py-4 text-sm font-medium uppercase tracking-[0.18em] text-white/60"
            >
              {item}
            </div>
          ))}
        </div>

        <div className="grid gap-8 py-12 lg:grid-cols-[0.78fr_1.22fr]">
          <div className="space-y-5">
            <p className="text-xs font-bold uppercase tracking-[0.42em] text-[#ff6a75]">
              Why FRAPH
            </p>
            <h2 className="max-w-lg text-3xl font-black uppercase leading-tight tracking-[-0.04em] text-white sm:text-4xl">
              Built for financial fraud signals hidden inside connected transaction behavior.
            </h2>
            <p className="max-w-xl text-base leading-7 text-white/68">
              The home page should explain the product in one glance: upload data, build a
              transaction graph, analyze suspicious flows, and compare graph neural methods
              against baseline fraud models.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            {workflowSteps.map((step) => (
              <article
                key={step.id}
                className="rounded-[1.7rem] border border-[#6d1018]/70 bg-[linear-gradient(180deg,rgba(31,9,12,0.95),rgba(10,5,6,0.95))] p-6 shadow-[0_18px_45px_rgba(0,0,0,0.28)]"
              >
                <p className="text-xs font-black tracking-[0.32em] text-[#ff5d68]">{step.id}</p>
                <h3 className="mt-4 text-lg font-black uppercase leading-6 text-white">
                  {step.title}
                </h3>
                <p className="mt-4 text-sm leading-6 text-white/62">{step.body}</p>
              </article>
            ))}
          </div>
        </div>

        <footer className="relative mt-auto flex min-h-[8rem] items-end pt-6">
          <div className="bottom-wordmark pointer-events-none absolute inset-x-0 bottom-0 text-center text-[4.25rem] font-black uppercase leading-none tracking-[-0.08em] text-white/[0.06] sm:text-[6.5rem] md:text-[8rem] xl:text-[11rem]">
            FRAPH
          </div>
          <div className="relative z-10 flex w-full items-center justify-between border-t border-white/8 pt-4 text-[11px] uppercase tracking-[0.3em] text-white/40">
            <span>Financial fraud detection using graph neural networks</span>
            <span className="hidden md:block">Transaction intelligence reworked in red</span>
          </div>
        </footer>
      </section>
    </main>
  );
}
