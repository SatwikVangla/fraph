import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { apiRequest } from "../utils/api";

export default function DashboardPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const [analysis, setAnalysis] = useState(null);
  const [dataset, setDataset] = useState(location.state?.dataset ?? null);
  const [datasets, setDatasets] = useState([]);
  const [preprocessingJob, setPreprocessingJob] = useState(null);
  const [selectedTransactionId, setSelectedTransactionId] = useState(null);
  const [latestGnnArtifact, setLatestGnnArtifact] = useState(null);
  const [deviceStatus, setDeviceStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const hasDatasets = datasets.length > 0;
  const transactionRowRefs = useRef(new Map());

  useEffect(() => {
    let active = true;

    async function loadDatasets() {
      try {
        const availableDatasets = await apiRequest("/upload/datasets");
        if (!active) {
          return;
        }
        setDatasets(availableDatasets);
        if (!dataset && availableDatasets.length) {
          setDataset(availableDatasets[0]);
        }
      } catch {
        // Dataset loading is best-effort here. Analysis requests surface their own errors.
      }
    }

    async function loadAnalysis() {
      try {
        setLoading(true);
        setError("");
        setAnalysis(null);
        setLatestGnnArtifact(null);

        let activeDataset = dataset;
        if (!activeDataset) {
          const datasets = await apiRequest("/upload/datasets");
          if (!datasets.length) {
            throw new Error("No datasets available. Upload a CSV first.");
          }
          activeDataset = datasets[0];
          if (active) {
            setDataset(activeDataset);
          }
        }

        try {
          const deviceResponse = await apiRequest("/train/device");
          if (active) {
            setDeviceStatus(deviceResponse.device ?? null);
          }
        } catch {
          if (active) {
            setDeviceStatus(null);
          }
        }

        try {
          const artifacts = await apiRequest(`/train/artifacts/${activeDataset.id}`);
          if (active) {
            setLatestGnnArtifact(
              artifacts.find((artifact) => artifact.model_name === "gnn") ?? null,
            );
          }
        } catch {
          if (active) {
            setLatestGnnArtifact(null);
          }
        }

        if (activeDataset.large_dataset) {
          const jobStatus = await apiRequest(
            `/upload/preprocessing-status/${activeDataset.id}`,
          );
          if (!active) {
            return;
          }
          setPreprocessingJob(jobStatus);
          if (jobStatus.status !== "completed") {
            return;
          }
        } else if (active) {
          setPreprocessingJob(null);
        }

        const response = await apiRequest("/fraud/detect", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            dataset_id: activeDataset.id,
            threshold: 0.65,
            limit: 8,
          }),
        });

        if (active) {
          setAnalysis(response);
          setSelectedTransactionId(
            response.suspicious_transactions?.[0]?.transaction_id ?? null,
          );
        }
      } catch (requestError) {
        if (active) {
          setError(
            requestError instanceof Error
              ? requestError.message
              : "Failed to load fraud analysis.",
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadDatasets();
    loadAnalysis();
    return () => {
      active = false;
    };
  }, [dataset]);

  useEffect(() => {
    if (!dataset?.large_dataset || !preprocessingJob || preprocessingJob.status === "completed" || preprocessingJob.status === "failed") {
      return undefined;
    }

    const intervalId = window.setInterval(async () => {
      try {
        const nextJob = await apiRequest(
          `/upload/preprocessing-status/${dataset.id}`,
        );
        setPreprocessingJob(nextJob);
        if (nextJob.status === "completed") {
          const response = await apiRequest("/fraud/detect", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              dataset_id: dataset.id,
              threshold: 0.65,
              limit: 8,
            }),
          });
          setAnalysis(response);
          setSelectedTransactionId(
            response.suspicious_transactions?.[0]?.transaction_id ?? null,
          );
        }
      } catch (requestError) {
        setError(
          requestError instanceof Error
            ? requestError.message
            : "Failed to load large dataset preparation status.",
        );
      }
    }, 2000);

    return () => window.clearInterval(intervalId);
  }, [dataset, preprocessingJob]);

  useEffect(() => {
    if (!selectedTransactionId) {
      return;
    }

    const row = transactionRowRefs.current.get(selectedTransactionId);
    row?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [selectedTransactionId]);

  return (
    <div className="min-h-screen bg-black px-6 py-10 text-white md:px-12">
      <div className="mx-auto max-w-7xl">
        <div className="mb-12 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="mb-3 text-sm uppercase tracking-[0.35em] text-red-500">
              Live Graph Fraud Analysis
            </p>
            <h1 className="text-4xl md:text-5xl font-black tracking-wide">
              Fraud Intelligence Dashboard
            </h1>
            <p className="mt-3 text-neutral-400">
              Dataset: {dataset?.name ?? "--"}
            </p>
            <p className="mt-2 max-w-2xl text-sm text-neutral-500">
              Analyze suspicious flows, review the fraud snapshot, and open the dedicated
              graph explorer to evaluate transaction relationships in a larger workspace.
            </p>
            {datasets.length ? (
              <div className="mt-5 max-w-sm">
                <label
                  htmlFor="dashboard-dataset"
                  className="mb-2 block text-xs font-bold uppercase tracking-[0.25em] text-neutral-500"
                >
                  Switch Dataset
                </label>
                <select
                  id="dashboard-dataset"
                  value={dataset?.id ?? ""}
                  onChange={(event) => {
                    const nextDataset = datasets.find(
                      (item) => item.id === Number(event.target.value),
                    );
                    if (nextDataset) {
                      setDataset(nextDataset);
                    }
                  }}
                  className="w-full border border-neutral-700 bg-neutral-950 px-4 py-3 text-sm text-white outline-none transition focus:border-red-600"
                >
                  {datasets.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </div>
            ) : null}
          </div>

          <div className="flex flex-wrap gap-3">
            {analysis?.dataset ? (
              <Link
                to={`/graph/${analysis.dataset.id}`}
                state={{ dataset: analysis.dataset }}
                className="inline-flex w-fit items-center border border-red-600 px-5 py-3 text-sm font-bold uppercase tracking-[0.25em] text-white transition hover:bg-red-600"
              >
                Open Graph Explorer
              </Link>
            ) : null}
            {analysis?.dataset ? (
              <Link
                to={`/compare/${analysis.dataset.id}`}
                state={{ dataset: analysis.dataset }}
                className="inline-flex w-fit items-center border border-neutral-700 px-5 py-3 text-sm font-bold uppercase tracking-[0.25em] text-white transition hover:border-neutral-500"
              >
                Open GNN Comparison
              </Link>
            ) : null}
          </div>
        </div>

        {loading ? (
          <div className="rounded-2xl border border-neutral-800 bg-neutral-950 p-10 text-neutral-300">
            Running fraud analysis...
          </div>
        ) : null}

        {!loading && dataset?.large_dataset && preprocessingJob && preprocessingJob.status !== "completed" ? (
          <div className="mb-10 rounded-2xl border border-amber-700/60 bg-amber-950/20 p-6 text-amber-100">
            <p className="text-sm font-bold uppercase tracking-[0.24em] text-amber-300">
              Large Dataset Preparation
            </p>
            <p className="mt-3 text-sm">
              {preprocessingJob.message}
            </p>
            <p className="mt-2 text-xs uppercase tracking-[0.18em] text-amber-200/80">
              Status: {preprocessingJob.status} | Progress: {preprocessingJob.progress}%
            </p>
            <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-black/40">
              <div
                className="h-full bg-amber-400 transition-all duration-300"
                style={{ width: `${preprocessingJob.progress}%` }}
              />
            </div>
            <p className="mt-4 text-sm text-amber-50/80">
              The dashboard will load sampled graph artifacts after preprocessing completes.
            </p>
          </div>
        ) : null}

        {!loading && deviceStatus && !deviceStatus.cuda_available && !deviceStatus.mps_available ? (
          <div className="mb-10 rounded-2xl border border-amber-700/60 bg-amber-950/20 p-6 text-amber-100">
            GPU acceleration is not currently available to the backend. Analysis and GNN training
            will run on <span className="font-semibold text-white">{deviceStatus.selected_device}</span>.
            {deviceStatus.cuda_version ? ` PyTorch was built with CUDA ${deviceStatus.cuda_version}, but no usable GPU was detected.` : ""}
          </div>
        ) : null}

        {error ? (
          <div className="rounded-2xl border border-red-800 bg-red-950/20 p-6 text-red-300">
            {error}
          </div>
        ) : null}

        {!loading && !error && !hasDatasets ? (
          <div className="rounded-2xl border border-amber-800 bg-amber-950/20 p-6 text-amber-100">
            No datasets are available yet. Upload a labeled CSV to populate the dashboard.
          </div>
        ) : null}

        {!loading && !error && analysis ? (
          <>
            <div className="mb-12 grid gap-6 md:grid-cols-3">
              <MetricCard
                label="Transactions Analyzed"
                value={analysis.summary.transactions_analyzed}
              />
              <MetricCard
                label="Suspicious Transactions"
                value={analysis.summary.suspicious_transactions}
                accent="text-red-500"
              />
              <MetricCard
                label="Average Risk Score"
                value={analysis.summary.average_risk_score}
              />
            </div>

            {latestGnnArtifact ? (
              <GnnInsightsCard artifact={latestGnnArtifact} />
            ) : null}

            <div className="mb-12 grid items-start gap-6 lg:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)]">
              <div className="rounded-2xl border border-red-900/60 bg-neutral-950 p-6">
                <p className="text-sm uppercase tracking-[0.3em] text-red-400">Relationship Explorer</p>
                <h2 className="mt-2 text-2xl font-bold text-white">Open The Graph In A Dedicated Workspace</h2>
                <p className="mt-3 max-w-2xl text-sm text-neutral-400">
                  The transaction graph now lives on its own page so you can inspect suspicious paths,
                  linked accounts, and focused transactions without compressing the dashboard layout.
                </p>
                <div className="mt-6 grid gap-4 md:grid-cols-3">
                  <SnapshotRow label="Nodes" value={analysis.graph.node_count} />
                  <SnapshotRow label="Edges" value={analysis.graph.edge_count} />
                  <SnapshotRow label="Components" value={analysis.graph.connected_components} />
                </div>
                {analysis.dataset ? (
                  <Link
                    to={`/graph/${analysis.dataset.id}`}
                    state={{ dataset: analysis.dataset }}
                    className="mt-6 inline-flex items-center border border-red-600 px-5 py-3 text-sm font-bold uppercase tracking-[0.25em] text-white transition hover:bg-red-600"
                  >
                    Launch Graph Explorer
                  </Link>
                ) : null}
              </div>

              <div className="rounded-2xl border border-neutral-800 bg-neutral-950 p-6">
                <h2 className="text-2xl font-bold">Risk Snapshot</h2>
                <div className="mt-6 space-y-5 text-sm text-neutral-300">
                  <SnapshotRow label="Fraud Rate" value={analysis.summary.fraud_rate} />
                  <SnapshotRow label="Total Amount" value={analysis.summary.total_amount} />
                  <SnapshotRow label="Top Nodes" value={analysis.graph.top_nodes.length} />
                  <SnapshotRow label="Top Edges" value={analysis.graph.top_edges.length} />
                </div>
              </div>
            </div>

            <div className="relative z-10 overflow-hidden rounded-2xl border border-neutral-800 bg-neutral-950">
              <div className="border-b border-neutral-800 px-6 py-5">
                <h2 className="text-2xl font-bold">Suspicious Transactions</h2>
                <p className="mt-2 text-sm text-neutral-500">
                  Open any suspicious transaction in the dedicated graph explorer to inspect its relationship path.
                </p>
              </div>

              <div className="overflow-x-auto">
                <table className="min-w-full text-left text-sm">
                  <thead className="border-b border-neutral-800 text-xs uppercase tracking-[0.25em] text-neutral-500">
                    <tr>
                      <th className="px-6 py-4">Transaction</th>
                      <th className="px-6 py-4">Sender</th>
                      <th className="px-6 py-4">Receiver</th>
                      <th className="px-6 py-4">Amount</th>
                      <th className="px-6 py-4">Risk Score</th>
                    </tr>
                  </thead>
                  <tbody className="text-neutral-200">
                    {analysis.suspicious_transactions.length ? analysis.suspicious_transactions.map((transaction) => (
                      <tr
                        key={transaction.transaction_id}
                        ref={(element) => {
                          if (!element) {
                            transactionRowRefs.current.delete(transaction.transaction_id);
                            return;
                          }
                          transactionRowRefs.current.set(transaction.transaction_id, element);
                        }}
                        onClick={() => {
                          setSelectedTransactionId(transaction.transaction_id);
                          if (analysis?.dataset) {
                            navigate(`/graph/${analysis.dataset.id}`, {
                              state: {
                                dataset: analysis.dataset,
                                transactionId: transaction.transaction_id,
                              },
                            });
                          }
                        }}
                        className={`cursor-pointer border-b border-neutral-900 transition last:border-b-0 ${
                          selectedTransactionId === transaction.transaction_id
                            ? "bg-red-950/30"
                            : "hover:bg-white/5"
                        }`}
                      >
                        <td className="px-6 py-4 font-medium">
                          {transaction.transaction_id}
                        </td>
                        <td className="px-6 py-4">{transaction.sender}</td>
                        <td className="px-6 py-4">{transaction.receiver}</td>
                        <td className="px-6 py-4">
                          {transaction.amount.toLocaleString()}
                        </td>
                        <td className="px-6 py-4 text-red-400">
                          {transaction.risk_score}
                        </td>
                      </tr>
                    )) : (
                      <tr>
                        <td colSpan={5} className="px-6 py-8 text-center text-neutral-500">
                          No suspicious transactions matched the current threshold.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
}

function formatDashboardEvaluation(strategy) {
  if (!strategy) {
    return "No saved evaluation metadata";
  }

  const trainRange = `${strategy.train_step_min ?? "--"}-${strategy.train_step_max ?? "--"}`;
  const testRange = `${strategy.test_step_min ?? "--"}-${strategy.test_step_max ?? "--"}`;
  return `Chronological holdout | train ${trainRange} | test ${testRange}`;
}

function GnnInsightsCard({ artifact }) {
  const config = artifact?.selected_config ?? {};
  const graphSummary = artifact?.explainability?.graph_summary ?? {};
  const ablationSummary = (artifact?.explainability?.ablation_summary ?? []).slice(0, 3);

  return (
    <div className="mb-12 rounded-2xl border border-red-900/60 bg-neutral-950 p-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-red-400">Saved GNN Insight</p>
          <h2 className="mt-2 text-2xl font-bold text-white">Latest Relationship-Aware Model</h2>
          <p className="mt-2 max-w-3xl text-sm text-neutral-400">
            The dashboard is showing the latest persisted graph model for this dataset, including graph scale, device, evaluation strategy, and the strongest ablation takeaways.
          </p>
        </div>
        <div className="rounded-xl border border-neutral-800 bg-black/40 px-4 py-3 text-xs uppercase tracking-[0.22em] text-neutral-300">
          {String(config.model_architecture ?? "--").toUpperCase()} | F1 {artifact?.f1_score ?? "--"}
        </div>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-5">
        <MetricCard label="Device" value={graphSummary.device ?? "--"} />
        <MetricCard label="Nodes" value={graphSummary.total_nodes ?? "--"} />
        <MetricCard label="Edges" value={graphSummary.edge_count ?? "--"} />
        <MetricCard label="Edge Features" value={graphSummary.edge_feature_count ?? "--"} />
        <MetricCard label="PR AUC" value={artifact?.pr_auc ?? "--"} />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="rounded-2xl border border-neutral-800 bg-black/30 p-5">
          <p className="text-xs font-bold uppercase tracking-[0.24em] text-neutral-500">Evaluation</p>
          <p className="mt-3 text-sm text-white">{formatDashboardEvaluation(config.evaluation_strategy)}</p>
          <div className="mt-4 flex flex-wrap gap-2 text-xs uppercase tracking-[0.18em] text-neutral-200">
            <span className="rounded-full border border-red-900/70 px-3 py-2">Similarity {config.use_similarity_edges ? "On" : "Off"}</span>
            <span className="rounded-full border border-red-900/70 px-3 py-2">Party {config.use_party_edges ? "On" : "Off"}</span>
            <span className="rounded-full border border-red-900/70 px-3 py-2">Temporal {config.use_temporal_edges ? "On" : "Off"}</span>
            <span className="rounded-full border border-red-900/70 px-3 py-2">Accounts {config.include_account_nodes ? "On" : "Off"}</span>
          </div>
        </div>

        <div className="rounded-2xl border border-neutral-800 bg-black/30 p-5">
          <p className="text-xs font-bold uppercase tracking-[0.24em] text-neutral-500">Top Ablation Takeaways</p>
          <div className="mt-4 space-y-3 text-sm text-neutral-300">
            {ablationSummary.length ? ablationSummary.map((item) => (
              <div key={item.name} className="rounded-xl border border-neutral-800 bg-neutral-950/70 p-4">
                <p className="font-semibold text-white">{item.label}</p>
                <p className="mt-2 text-xs uppercase tracking-[0.18em] text-neutral-500">
                  {String(item.architecture ?? "--").toUpperCase()} | F1 {item.f1_score ?? "--"} | PR AUC {item.pr_auc ?? "--"}
                </p>
              </div>
            )) : (
              <div className="rounded-xl border border-neutral-800 bg-neutral-950/70 p-4 text-neutral-400">
                No saved ablation results are available yet for this dataset.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ label, value, accent = "" }) {
  return (
    <div className="rounded-2xl border border-neutral-800 bg-neutral-950 p-6">
      <p className="text-sm uppercase tracking-[0.25em] text-neutral-500">{label}</p>
      <p className={`mt-4 text-4xl font-black ${accent}`}>{value}</p>
    </div>
  );
}

function SnapshotRow({ label, value }) {
  return (
    <div className="flex items-center justify-between border-b border-neutral-900 pb-3 last:border-b-0">
      <span className="uppercase tracking-[0.2em] text-neutral-500">{label}</span>
      <span className="text-lg font-semibold text-white">{value}</span>
    </div>
  );
}
