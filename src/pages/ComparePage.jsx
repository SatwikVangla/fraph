import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";

import ParticleBackground from "../components/ParticleBackground";
import { API_BASE_URL, apiRequest } from "../utils/api";

const MODEL_LABELS = {
  gnn: "GNN",
  knn: "KNN",
  linear_svc: "Linear SVC",
  logistic_regression: "Logistic Regression",
  gaussian_nb: "Gaussian Naive Bayes",
};

export default function ComparePage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { datasetId } = useParams();
  const [comparison, setComparison] = useState(null);
  const [datasets, setDatasets] = useState([]);
  const [trainingResults, setTrainingResults] = useState([]);
  const [job, setJob] = useState(null);
  const [deviceStatus, setDeviceStatus] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [training, setTraining] = useState(false);
  const routeDatasetId = datasetId ? Number(datasetId) : null;
  const activeDatasetId = routeDatasetId ?? comparison?.dataset?.id ?? location.state?.dataset?.id ?? null;
  const activeDatasetName = comparison?.dataset?.name ?? location.state?.dataset?.name ?? null;
  const compareModelNames = [
    "knn",
    "logistic_regression",
    "linear_svc",
    "gaussian_nb",
    "gnn",
  ];
  const gnnComparisonResult = comparison?.model_results?.find((result) => result.model_name === "gnn") ?? null;
  const gnnTrainingResult = trainingResults.find((result) => result.model_name === "gnn") ?? null;

  async function refreshComparison(active = true, preferredDataset = null) {
    try {
      setLoading(true);
      setError("");

      const preferredDatasetId = preferredDataset?.id ?? null;
      const preferredDatasetName = preferredDataset?.name ?? null;
      const payload = activeDatasetId || preferredDatasetId
        ? { dataset_id: activeDatasetId ?? preferredDatasetId }
        : activeDatasetName || preferredDatasetName
          ? { dataset_name: activeDatasetName ?? preferredDatasetName }
          : null;

      if (!payload) {
        if (active) {
          setComparison(null);
          setTrainingResults([]);
        }
        return;
      }

      const response = await apiRequest("/compare/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ...payload,
          model_names: compareModelNames,
        }),
      });

      if (active) {
        setComparison(response);
      }
    } finally {
      setLoading(false);
    }
  }

  async function refreshArtifacts(active = true, preferredDatasetId = null) {
    const artifactDatasetId = activeDatasetId ?? preferredDatasetId;
    if (!artifactDatasetId) {
      if (active) {
        setTrainingResults([]);
      }
      return;
    }
    const artifacts = await apiRequest(`/train/artifacts/${artifactDatasetId}`);
    if (active) {
      setTrainingResults(artifacts);
    }
  }

  useEffect(() => {
    let active = true;

    async function loadPage() {
      try {
        const response = await apiRequest("/upload/datasets");
        if (!active) {
          return;
        }
        setDatasets(response);

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

        const fallbackDataset =
          response.find((item) => item.id === routeDatasetId) ??
          location.state?.dataset ??
          response[0] ??
          null;

        if (!routeDatasetId && !location.state?.dataset?.name && fallbackDataset) {
          navigate(`/compare/${fallbackDataset.id}`, {
            replace: true,
            state: { dataset: fallbackDataset },
          });
          return;
        }

        await refreshComparison(active, fallbackDataset);
        await refreshArtifacts(active, fallbackDataset?.id ?? null);
      } catch (requestError) {
        if (active) {
          setError(
            requestError instanceof Error
              ? requestError.message
              : "Failed to load model comparison.",
          );
          setLoading(false);
        }
      }
    }

    loadPage();
    return () => {
      active = false;
    };
  }, [routeDatasetId, location.state?.dataset?.id, location.state?.dataset?.name, navigate]);

  async function handleTraining() {
    const payload = activeDatasetId
      ? { dataset_id: activeDatasetId }
      : activeDatasetName
        ? { dataset_name: activeDatasetName }
        : null;

    if (!payload) {
      setError("Select or upload a dataset before training models.");
      return;
    }

    try {
      setTraining(true);
      setError("");

      const response = await apiRequest("/train/jobs", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ...payload,
          model_names: compareModelNames,
          epochs: 120,
          hidden_dim: 160,
          learning_rate: 0.003,
          sampling_preset: "large",
        }),
      });
      setJob(response);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Failed to train and persist models.",
      );
    } finally {
      setTraining(false);
    }
  }

  useEffect(() => {
    if (!job || job.status === "completed" || job.status === "failed") {
      return undefined;
    }

    const intervalId = window.setInterval(async () => {
      try {
        const nextJob = await apiRequest(`/train/jobs/${job.job_id}`);
        setJob(nextJob);
        if (nextJob.status === "completed") {
          setTraining(false);
          setTrainingResults(nextJob.result?.training_results ?? []);
          await refreshComparison(true);
          await refreshArtifacts(true);
        }
        if (nextJob.status === "failed") {
          setTraining(false);
          setError(nextJob.error || "Training job failed.");
        }
      } catch (requestError) {
        setTraining(false);
        setError(
          requestError instanceof Error
            ? requestError.message
            : "Failed to poll training job.",
        );
      }
    }, 1500);

    return () => window.clearInterval(intervalId);
  }, [job, activeDatasetId, activeDatasetName]);

  return (
    <div className="relative min-h-screen overflow-hidden bg-black px-6 py-10 text-white md:px-12">
      <div className="absolute inset-0 z-0 opacity-30">
        <ParticleBackground />
      </div>
      <div className="wavy-texture absolute inset-0 z-10 pointer-events-none" />
      <div
        className="absolute inset-0 z-20 pointer-events-none"
        style={{
          background:
            "radial-gradient(circle at center, transparent 0%, black 88%)",
        }}
      />

      <div className="relative z-30 mx-auto max-w-6xl">
        <div className="mb-10 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="mb-3 text-sm uppercase tracking-[0.35em] text-red-500">
              Simpler Baselines vs Relationship-Aware GNN
            </p>
            <h1 className="text-4xl md:text-5xl font-black tracking-wide">
              Model Comparison
            </h1>
            <p className="mt-3 text-neutral-400">
              Dataset: {comparison?.dataset?.name ?? location.state?.dataset?.name ?? "--"}
            </p>
            <p className="mt-2 max-w-2xl text-sm text-neutral-500">
              Compare the relationship-aware GNN against four simpler non-graph baselines:
              KNN, Logistic Regression, Linear SVC, and Gaussian Naive Bayes.
            </p>
            <p className="mt-2 max-w-2xl text-sm text-red-300">
              For this fraud setting, treat <span className="font-semibold text-white">F1</span>,{" "}
              <span className="font-semibold text-white">PR-AUC</span>, and{" "}
              <span className="font-semibold text-white">MCC</span> as the primary metrics.
              Accuracy alone is weak under heavy class imbalance.
            </p>
            {datasets.length ? (
              <div className="mt-5 max-w-sm">
                <label
                  htmlFor="compare-dataset"
                  className="mb-2 block text-xs font-bold uppercase tracking-[0.25em] text-neutral-500"
                >
                  Compare Uploaded Dataset
                </label>
                <select
                  id="compare-dataset"
                  value={activeDatasetId ?? ""}
                  onChange={(event) => {
                    const nextDataset = datasets.find(
                      (item) => item.id === Number(event.target.value),
                    );
                    if (nextDataset) {
                      navigate(`/compare/${nextDataset.id}`, {
                        state: { dataset: nextDataset },
                      });
                    }
                  }}
                  className="w-full border border-neutral-700 bg-neutral-950/80 px-4 py-3 text-sm text-white outline-none transition focus:border-red-600"
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

          <Link
            to="/dashboard"
            state={location.state}
            className="inline-flex w-fit items-center border border-red-600 px-5 py-3 text-sm font-bold uppercase tracking-[0.25em] text-white transition hover:bg-red-600"
          >
            Back To Dashboard
          </Link>
        </div>

        {!datasets.length && !loading ? (
          <div className="mb-8 rounded-2xl border border-amber-800 bg-amber-950/20 p-6 text-amber-100">
            No uploaded datasets are available yet. Upload a labeled CSV before running the
            comparison and GNN training flow.
          </div>
        ) : null}

        <div className="mb-8 flex flex-wrap gap-4">
          <button
            onClick={handleTraining}
            disabled={training || loading || !activeDatasetId}
            className="inline-flex items-center border border-red-600 px-5 py-3 text-sm font-bold uppercase tracking-[0.25em] text-white transition hover:bg-red-600 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {training ? "Training Models..." : "Train And Save Models"}
          </button>
        </div>

        {job ? (
          <div className="mb-8 rounded-2xl border border-neutral-800 bg-neutral-950 p-6">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <p className="text-sm uppercase tracking-[0.28em] text-red-400">
                  Training Job
                </p>
                <p className="mt-2 text-lg font-semibold text-white">
                  {job.message}
                </p>
                <p className="mt-2 text-sm text-neutral-500">
                  Status: {job.status} | Progress: {job.progress}%
                </p>
              </div>
              <div className="h-3 w-full max-w-xs overflow-hidden rounded-full bg-neutral-900">
                <div
                  className="h-full bg-red-600 transition-all duration-300"
                  style={{ width: `${job.progress}%` }}
                />
              </div>
            </div>
          </div>
        ) : null}

        {loading ? (
          <div className="rounded-2xl border border-neutral-800 bg-neutral-950 p-10 text-neutral-300">
            Loading model comparison...
          </div>
        ) : null}

        {!loading && deviceStatus && !deviceStatus.cuda_available && !deviceStatus.mps_available ? (
          <div className="mb-8 rounded-2xl border border-amber-800 bg-amber-950/20 p-6 text-amber-100">
            GPU acceleration is not currently available to the backend. Training will fall back to
            <span className="font-semibold text-white"> {deviceStatus.selected_device}</span>.
            {deviceStatus.cuda_version ? ` PyTorch was built with CUDA ${deviceStatus.cuda_version}, but no usable GPU was detected.` : ""}
          </div>
        ) : null}

        {error ? (
          <div className="rounded-2xl border border-red-800 bg-red-950/20 p-6 text-red-300">
            {error}
          </div>
        ) : null}

        {!loading && !error && comparison ? (
          <>
            <div className="mb-8 grid gap-6 md:grid-cols-4">
              <MetricCard
                label="Fraud Ratio"
                value={comparison.diagnostics?.class_distribution?.fraud_ratio ?? "--"}
              />
              <MetricCard
                label="Fraud Rows"
                value={comparison.diagnostics?.class_distribution?.fraud ?? "--"}
              />
              <MetricCard
                label="Legitimate Rows"
                value={comparison.diagnostics?.class_distribution?.legitimate ?? "--"}
              />
              <MetricCard
                label="Duplicate Transactions"
                value={comparison.diagnostics?.duplicate_transactions ?? "--"}
              />
            </div>

            <div className="mb-8 rounded-2xl border border-neutral-800 bg-neutral-950 p-6">
              <h2 className="text-2xl font-bold">Dataset Diagnostics</h2>
              <div className="mt-5 grid gap-4 md:grid-cols-2">
                {(comparison.diagnostics?.warnings ?? []).length ? (
                  (comparison.diagnostics?.warnings ?? []).map((warning) => (
                    <div
                      key={warning}
                      className="rounded-xl border border-red-900/60 bg-red-950/20 p-4 text-sm text-red-200"
                    >
                      {warning}
                    </div>
                  ))
                ) : (
                  <div className="rounded-xl border border-neutral-800 bg-neutral-900/60 p-4 text-sm text-neutral-300">
                    No major data-quality warnings detected.
                  </div>
                )}
              </div>
            </div>

            <div className="mb-8 rounded-2xl border border-red-900/60 bg-red-950/20 p-6">
              <h2 className="text-2xl font-bold text-white">Primary Fraud Metrics</h2>
              <p className="mt-3 max-w-3xl text-sm leading-6 text-red-100">
                Use <span className="font-semibold text-white">F1</span> to balance precision
                and recall, <span className="font-semibold text-white">PR-AUC</span> to judge
                fraud ranking quality under rare positives, and{" "}
                <span className="font-semibold text-white">MCC</span> to measure balanced
                classification quality even when legitimate transactions dominate.
              </p>
            </div>

            <div className="overflow-hidden rounded-2xl border border-neutral-800 bg-neutral-950">
              <div className="overflow-x-auto">
                <div className="min-w-[1380px]">
                  <div className="grid grid-cols-11 gap-4 border-b border-neutral-800 px-6 py-4 text-xs font-bold uppercase tracking-[0.25em] text-neutral-500">
                    <span>Model</span>
                    <span>Accuracy</span>
                    <span>Precision</span>
                    <span>Recall</span>
                    <span className="text-red-300">F1</span>
                    <span>ROC AUC</span>
                    <span className="text-red-300">PR AUC</span>
                    <span className="text-red-300">MCC</span>
                    <span>Threshold</span>
                    <span>Confusion</span>
                    <span>Explainability</span>
                  </div>

                  {comparison.model_results.map((result) => (
                    <div
                      key={result.model_name}
                      className={`grid grid-cols-11 gap-4 border-b px-6 py-5 text-sm text-neutral-200 last:border-b-0 ${
                        result.model_name === "gnn"
                          ? "border-red-950/70 bg-red-950/10"
                          : "border-neutral-900"
                      }`}
                    >
                      <div>
                        <p className="font-semibold">
                          {MODEL_LABELS[result.model_name] ?? result.model_name}
                        </p>
                        <p className="mt-2 text-xs uppercase tracking-[0.2em] text-neutral-500">
                          {result.status}
                        </p>
                        <p className="mt-2 text-xs text-neutral-500">{result.details}</p>
                        {result.selected_config ? (
                          <div className="mt-2 text-xs text-red-400">
                            <p>Evaluation: {formatEvaluationLabel(result.selected_config?.evaluation_strategy)}</p>
                            {result.model_name === "gnn" ? (
                              <p className="mt-1">
                                {formatArchitectureLabel(result.selected_config?.model_architecture)} | Hidden {result.selected_config?.hidden_dim ?? "--"} | Epochs {result.selected_config?.epochs ?? "--"}
                              </p>
                            ) : null}
                          </div>
                        ) : null}
                        {result.model_name === "gnn" ? (
                          <p className="mt-2 text-xs text-neutral-400">
                            Models linked users, counterparties, and transaction edges instead of
                            scoring rows independently.
                          </p>
                        ) : (
                          <p className="mt-2 text-xs text-neutral-400">
                            Non-graph baseline on transaction features only.
                          </p>
                        )}
                      </div>
                      <MetricCell value={result.accuracy} />
                      <MetricCell value={result.precision} />
                      <MetricCell value={result.recall} />
                      <MetricCell value={result.f1_score} />
                      <MetricCell value={result.roc_auc} />
                      <MetricCell value={result.pr_auc} />
                      <MetricCell value={result.mcc} />
                      <MetricCell value={result.threshold} />
                      <div className="flex items-center text-sm text-neutral-300">
                        {renderConfusion(result)}
                      </div>
                      <div className="text-xs text-neutral-400">
                        {(result.explainability?.top_input_features ?? [])
                          .slice(0, 3)
                          .map((item) => (
                            <p key={`${result.model_name}-${item.feature}`} className="mb-1">
                              {item.feature}: {item.importance}
                            </p>
                          ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {gnnComparisonResult ? (
              <GnnEvidencePanel title="GNN Comparison Evidence" result={gnnComparisonResult} />
            ) : null}
          </>
        ) : null}

        {trainingResults.length ? (
          <>
            <div className="mt-10 overflow-hidden rounded-2xl border border-neutral-800 bg-neutral-950">
            <div className="border-b border-neutral-800 px-6 py-5">
              <h2 className="text-2xl font-bold">Persisted Training Runs</h2>
            </div>
            <div className="overflow-x-auto">
              <div className="min-w-[860px]">
                {trainingResults.map((result) => (
                  <div
                    key={`artifact-${result.model_name}-${result.artifact_path ?? result.status}`}
                    className="border-b border-neutral-900 px-6 py-5 text-sm text-neutral-200 last:border-b-0"
                  >
                    <div className="grid gap-4 md:grid-cols-[1.4fr_repeat(5,minmax(0,1fr))]">
                      <div>
                        <p className="font-semibold">
                          {MODEL_LABELS[result.model_name] ?? result.model_name}
                        </p>
                        <p className="mt-2 text-xs uppercase tracking-[0.2em] text-neutral-500">
                          {result.status}
                        </p>
                        <p className="mt-2 text-xs text-neutral-500">{result.details}</p>
                        <p className="mt-2 break-all text-xs text-red-400">
                          {result.artifact_path ?? "No artifact saved"}
                        </p>
                        {result.artifact_id ? (
                          <a
                            href={`${API_BASE_URL}/train/reports/${result.artifact_id}`}
                            target="_blank"
                            rel="noreferrer"
                            className="mt-3 inline-flex text-xs uppercase tracking-[0.2em] text-red-300"
                          >
                            Download Report
                          </a>
                        ) : null}
                      </div>
                      <MetricCell value={result.accuracy} />
                      <MetricCell value={result.precision} />
                      <MetricCell value={result.recall} />
                      <MetricCell value={result.f1_score} />
                      <MetricCell value={result.roc_auc} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

            {gnnTrainingResult ? (
              <GnnEvidencePanel title="Persisted GNN Training Run" result={gnnTrainingResult} />
            ) : null}
          </>
        ) : null}
      </div>
    </div>
  );
}

function formatArchitectureLabel(value) {
  if (!value) {
    return "Architecture --";
  }

  return `Architecture ${String(value).toUpperCase()}`;
}

function formatEvaluationLabel(strategy) {
  if (!strategy) {
    return "Standard holdout";
  }

  if (strategy.name === "time_aware_holdout") {
    const trainRange = `${strategy.train_step_min ?? "--"}-${strategy.train_step_max ?? "--"}`;
    const testRange = `${strategy.test_step_min ?? "--"}-${strategy.test_step_max ?? "--"}`;
    return `Chronological holdout | train ${trainRange} | test ${testRange}`;
  }

  return strategy.name ?? "Standard holdout";
}

function formatToggleLabel(label, enabled) {
  return `${label}: ${enabled ? "On" : "Off"}`;
}

function GnnEvidencePanel({ title, result }) {
  const config = result?.selected_config ?? {};
  const graphSummary = result?.explainability?.graph_summary ?? {};
  const evaluationStrategy = config.evaluation_strategy ?? {};
  const ablationSummary = result?.explainability?.ablation_summary ?? [];

  return (
    <div className="mt-8 rounded-2xl border border-red-900/60 bg-neutral-950/95 p-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-sm uppercase tracking-[0.28em] text-red-400">Graph Model Evidence</p>
          <h2 className="mt-2 text-2xl font-bold text-white">{title}</h2>
          <p className="mt-2 max-w-3xl text-sm text-neutral-400">
            Architecture, device, graph construction, and chronological evaluation details for the weighted-message-passing GNN.
          </p>
        </div>
        <div className="rounded-xl border border-neutral-800 bg-black/40 px-4 py-3 text-xs uppercase tracking-[0.24em] text-neutral-300">
          {formatArchitectureLabel(config.model_architecture)}
        </div>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-5">
        <MetricCard label="Device" value={graphSummary.device ?? "--"} />
        <MetricCard label="Total Nodes" value={graphSummary.total_nodes ?? "--"} />
        <MetricCard label="Edges" value={graphSummary.edge_count ?? "--"} />
        <MetricCard label="Mean Edge Weight" value={graphSummary.mean_edge_weight ?? "--"} />
        <MetricCard label="Max Edge Weight" value={graphSummary.max_edge_weight ?? "--"} />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="rounded-2xl border border-neutral-800 bg-black/30 p-5">
          <p className="text-xs font-bold uppercase tracking-[0.24em] text-neutral-500">Evaluation Strategy</p>
          <p className="mt-3 text-sm text-white">{formatEvaluationLabel(evaluationStrategy)}</p>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <div className="rounded-xl border border-neutral-800 bg-neutral-950/80 p-4 text-sm text-neutral-300">
              Train rows: {evaluationStrategy.train_rows ?? "--"}
            </div>
            <div className="rounded-xl border border-neutral-800 bg-neutral-950/80 p-4 text-sm text-neutral-300">
              Test rows: {evaluationStrategy.test_rows ?? "--"}
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-neutral-800 bg-black/30 p-5">
          <p className="text-xs font-bold uppercase tracking-[0.24em] text-neutral-500">Graph Construction</p>
          <div className="mt-4 flex flex-wrap gap-2 text-xs uppercase tracking-[0.18em] text-neutral-200">
            <span className="rounded-full border border-red-900/70 px-3 py-2">
              {formatToggleLabel("Similarity", config.use_similarity_edges)}
            </span>
            <span className="rounded-full border border-red-900/70 px-3 py-2">
              {formatToggleLabel("Party", config.use_party_edges)}
            </span>
            <span className="rounded-full border border-red-900/70 px-3 py-2">
              {formatToggleLabel("Temporal", config.use_temporal_edges)}
            </span>
            <span className="rounded-full border border-red-900/70 px-3 py-2">
              {formatToggleLabel("Accounts", config.include_account_nodes)}
            </span>
          </div>
        </div>
      </div>

      {ablationSummary.length ? (
        <div className="mt-6 overflow-hidden rounded-2xl border border-neutral-800 bg-black/30">
          <div className="border-b border-neutral-800 px-5 py-4">
            <h3 className="text-lg font-semibold text-white">Ablation Snapshot</h3>
          </div>
          <div className="overflow-x-auto">
            <div className="min-w-[720px]">
              <div className="grid grid-cols-6 gap-4 border-b border-neutral-800 px-5 py-3 text-xs font-bold uppercase tracking-[0.22em] text-neutral-500">
                <span>Variant</span>
                <span>Arch</span>
                <span>F1</span>
                <span>PR AUC</span>
                <span>ROC AUC</span>
                <span>MCC</span>
              </div>
              {ablationSummary.map((item) => (
                <div
                  key={`${title}-${item.name}`}
                  className="grid grid-cols-6 gap-4 border-b border-neutral-900 px-5 py-4 text-sm text-neutral-200 last:border-b-0"
                >
                  <span>{item.label}</span>
                  <span>{String(item.architecture ?? "--").toUpperCase()}</span>
                  <span>{item.f1_score ?? "--"}</span>
                  <span>{item.pr_auc ?? "--"}</span>
                  <span>{item.roc_auc ?? "--"}</span>
                  <span>{item.mcc ?? "--"}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function MetricCell({ value }) {
  return (
    <div className="flex items-center text-lg font-semibold">
      {value ?? "--"}
    </div>
  );
}

function MetricCard({ label, value }) {
  return (
    <div className="rounded-2xl border border-neutral-800 bg-neutral-950 p-6">
      <p className="text-sm uppercase tracking-[0.25em] text-neutral-500">{label}</p>
      <p className="mt-4 text-3xl font-black text-white">{value}</p>
    </div>
  );
}

function renderConfusion(result) {
  if (
    result.tn == null ||
    result.fp == null ||
    result.fn == null ||
    result.tp == null
  ) {
    return "--";
  }

  return `TN ${result.tn} | FP ${result.fp} | FN ${result.fn} | TP ${result.tp}`;
}
