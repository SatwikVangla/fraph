import { Suspense, lazy, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import ParticleBackground from "./ParticleBackground";

const HomeTitleScene = lazy(() => import("./HomeTitleScene"));

const capabilityCards = [
  {
    label: "Upload",
    text: "Bring in transaction CSV files and map the core fields before analysis starts.",
  },
  {
    label: "Analyze",
    text: "Review suspicious transactions, graph summaries, and dataset diagnostics.",
  },
  {
    label: "Compare",
    text: "Evaluate the GNN against the supported non-graph baselines.",
  },
];

const workflow = [
  "Upload and validate the dataset",
  "Run dashboard fraud analysis",
  "Inspect the transaction graph",
  "Review model comparison metrics",
];

function SceneFallback() {
  return (
    <div className="homev2-scene-fallback" aria-hidden="true">
      <div className="homev2-scene-fallback-grid" />
      <div className="homev2-scene-fallback-glow" />
      <div className="homev2-scene-fallback-title">FRAPH</div>
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
    <main className="homev2-shell">
      <div className="homev2-scene" aria-hidden="true">
        {showScene ? (
          <Suspense fallback={<SceneFallback />}>
            <HomeTitleScene />
          </Suspense>
        ) : (
          <SceneFallback />
        )}
        <div className="homev2-scene-shade" />
      </div>

      <div className="homev2-particles" aria-hidden="true">
        <ParticleBackground />
      </div>

      <div className="homev2-overlay" />

      <section className="homev2-frame">
        <header className="homev2-topbar">
          <div className="homev2-brand">
            <span className="homev2-brand-mark" />
            <div>
              <p className="homev2-brand-name">FRAPH</p>
              <p className="homev2-brand-tag">Fraud relationship analysis workspace</p>
            </div>
          </div>

          <nav className="homev2-nav" aria-label="Homepage navigation">
            <button type="button" onClick={() => navigate("/upload")}>
              Upload
            </button>
            <button type="button" onClick={() => navigate("/dashboard")}>
              Dashboard
            </button>
          </nav>
        </header>

        <section className="homev2-hero">
          <div className="homev2-copy">
            <p className="homev2-kicker">Graph-based fraud analysis</p>
            <h1>Understand transaction relationships before you trust the prediction.</h1>
            <p className="homev2-summary">
              FRAPH is a fraud-analysis workspace for transaction datasets. Upload the CSV,
              inspect suspicious flows, open the graph explorer, and compare the GNN against
              supported non-graph baselines.
            </p>

            <div className="homev2-actions">
              <button
                type="button"
                className="homev2-button homev2-button-primary"
                onClick={() => navigate("/upload")}
              >
                Start With Upload
              </button>
              <button
                type="button"
                className="homev2-button homev2-button-secondary"
                onClick={() => navigate("/dashboard")}
              >
                Open Dashboard
              </button>
            </div>
          </div>

          <aside className="homev2-sidepanel">
            <div className="homev2-panel-block">
              <p className="homev2-panel-label">Core Flow</p>
              <ol className="homev2-workflow-list">
                {workflow.map((item, index) => (
                  <li key={item}>
                    <span>{String(index + 1).padStart(2, "0")}</span>
                    <p>{item}</p>
                  </li>
                ))}
              </ol>
            </div>
          </aside>
        </section>

        <section className="homev2-card-grid">
          {capabilityCards.map((card) => (
            <article key={card.label} className="homev2-card">
              <p className="homev2-card-label">{card.label}</p>
              <span>{card.text}</span>
            </article>
          ))}
        </section>

        <footer className="homev2-footer">
          <p>Copyright © Satwik Vangala</p>
        </footer>
      </section>
    </main>
  );
}
