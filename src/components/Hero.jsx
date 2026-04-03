import { Suspense, lazy, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import ParticleBackground from "./ParticleBackground";

const HomeTitleScene = lazy(() => import("./HomeTitleScene"));

const platformStats = [
  { value: "8.4M", label: "transactions profiled" },
  { value: "24/7", label: "risk surveillance" },
  { value: "97.2%", label: "pattern recall target" },
];

const platformPillars = [
  {
    eyebrow: "Graph Intelligence",
    title: "Connect suspicious accounts before the damage compounds.",
    body: "Turn raw payment logs into a living fraud map that reveals laundering chains, mule clusters, and repeated transfer signatures.",
  },
  {
    eyebrow: "Model Operations",
    title: "Compare simpler non-graph baselines against a relationship-aware GNN.",
    body: "Move from upload to graph construction to evaluation while showing how linked users and transactions change what the model can learn.",
  },
  {
    eyebrow: "Analyst Workflow",
    title: "Keep the interface focused on high-risk movement.",
    body: "Surface hot paths, weak balances, and linked entities through a single command center rather than fragmented charts.",
  },
];

const activityFeed = [
  "Velocity spike detected across linked wallets",
  "Transfer ladder reconstructed in 3 hops",
  "High-risk subnet isolated for review",
];

const controlPanels = [
  { name: "Upload", detail: "Normalize datasets and ingest fraud labels." },
  { name: "Dashboard", detail: "Inspect risk movement and graph structure." },
  { name: "Compare", detail: "Measure GNN gains over simpler non-graph baselines." },
];

function SceneFallback() {
  return (
    <div className="hero-scene-fallback" aria-hidden="true">
      <div className="hero-scene-fallback-grid" />
      <div className="hero-scene-fallback-glow" />
      <div className="hero-scene-fallback-title">FRAPH</div>
    </div>
  );
}

export default function Hero() {
  const navigate = useNavigate();
  const [showScene, setShowScene] = useState(false);

  useEffect(() => {
    const handle = window.setTimeout(() => setShowScene(true), 120);
    return () => window.clearTimeout(handle);
  }, []);

  return (
    <main className="homepage-shell">
      <div className="homepage-backdrop" />
      <div className="homepage-glow homepage-glow-left" />
      <div className="homepage-glow homepage-glow-right" />
      <div className="homepage-grid" />

      <div className="homepage-particles">
        <ParticleBackground />
      </div>

      <section className="hero-frame">
        <header className="hero-topbar">
          <div className="hero-brand">
            <span className="hero-brand-mark" />
            <div>
              <p className="hero-brand-name">FRAPH</p>
              <p className="hero-brand-tag">Fraud graph intelligence platform</p>
            </div>
          </div>

          <nav className="hero-nav" aria-label="Homepage navigation">
            <button type="button" onClick={() => navigate("/upload")}>
              Upload
            </button>
            <button type="button" onClick={() => navigate("/dashboard")}>
              Dashboard
            </button>
          </nav>
        </header>

        <div className="hero-main">
          <div className="hero-copy">
            <p className="hero-kicker">Redline fraud detection system</p>
            <h1>
              See the network.
              <span> Catch the fraud chain before it spreads.</span>
            </h1>
            <p className="hero-summary">
              A rebuilt landing page for FRAPH, designed around transaction graphs,
              user-transaction relationships, and model evaluation. The interface
              stays visible on first paint, then layers motion and particles on top.
            </p>

            <div className="hero-actions">
              <button
                type="button"
                className="hero-button hero-button-primary"
                onClick={() => navigate("/upload")}
              >
                Start Analysis
              </button>
              <button
                type="button"
                className="hero-button hero-button-secondary"
                onClick={() => navigate("/dashboard")}
              >
                Open Dashboard
              </button>
            </div>

            <div className="hero-stats">
              {platformStats.map((item) => (
                <article key={item.label} className="hero-stat-card">
                  <strong>{item.value}</strong>
                  <span>{item.label}</span>
                </article>
              ))}
            </div>
          </div>

          <div className="hero-stage">
            <div className="hero-stage-shell">
              <div className="hero-stage-screen">
                {showScene ? (
                  <Suspense fallback={<SceneFallback />}>
                    <HomeTitleScene />
                  </Suspense>
                ) : (
                  <SceneFallback />
                )}
                <div className="hero-stage-vignette" />

                <div className="stage-panel stage-panel-top">
                  <span>Graph forge sequence</span>
                  <span>FRAPH title assembled from network flow</span>
                </div>

                <div className="stage-panel stage-panel-right">
                  <p>Alert feed</p>
                  <ul>
                    {activityFeed.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>

                <div className="stage-panel stage-panel-bottom">
                  {controlPanels.map((panel) => (
                    <article key={panel.name}>
                      <span>{panel.name}</span>
                      <p>{panel.detail}</p>
                    </article>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="hero-pillars">
          {platformPillars.map((pillar) => (
            <article key={pillar.eyebrow} className="pillar-card">
              <p>{pillar.eyebrow}</p>
              <h2>{pillar.title}</h2>
              <span>{pillar.body}</span>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
