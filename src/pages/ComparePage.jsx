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
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [training, setTraining] = useState(false);
  const selectedDatasetId = datasetId ? Number(datasetId) : null;
  const compareModelNames = [
    "knn",
    "logistic_regression",
    "linear_svc",
    "gaussian_nb",
    "gnn",
  ];

  async function refreshComparison(active = true) {
    try {
      setLoading(true);
      setError("");

      const payload = selectedDatasetId
        ? { dataset_id: selectedDatasetId }
        : { dataset_name: location.state?.dataset?.name };

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

  async function refreshArtifacts(active = true) {
    if (!selectedDatasetId) {
      return;
    }
    const artifacts = await apiRequest(`/train/artifacts/${selectedDatasetId}`);
    if (active) {
      setTrainingResults(artifacts);
    }
  }

  useEffect(() => {
    let active = true;

    async function loadDatasets() {
      try {
        const response = await apiRequest("/upload/datasets");
        if (!active) {
          return;
        }
        setDatasets(response);
      } catch {
        // Keep the page usable even if the selector cannot load.
      }
    }

    async function loadComparison() {
      try {
        await refreshComparison(active);
      } catch (requestError) {
        if (active) {
          setError(
            requestError instanceof Error
              ? requestError.message
              : "Failed to load model comparison.",
          );
        }
      }
    }

    async function loadArtifacts() {
      if (!selectedDatasetId) {
        return;
      }
      try {
        await refreshArtifacts(active);
      } catch {
        // Keep the comparison page usable even if there are no saved artifacts yet.
      }
    }

    loadDatasets();
    loadComparison();
    loadArtifacts();
    return () => {
      active = false;
    };
  }, [selectedDatasetId, location.state?.dataset?.name]);

  async function handleTraining() {
    try {
      setTraining(true);
      setError("");

      const payload = selectedDatasetId
        ? { dataset_id: selectedDatasetId }
        : { dataset_name: location.state?.dataset?.name };

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
  }, [job]);

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
                  value={selectedDatasetId ?? ""}
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

        <div className="mb-8 flex flex-wrap gap-4">
          <button
            onClick={handleTraining}
            disabled={training || loading}
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

            <div className="overflow-hidden rounded-2xl border border-neutral-800 bg-neutral-950">
              <div className="overflow-x-auto">
                <div className="min-w-[1380px]">
                  <div className="grid grid-cols-11 gap-4 border-b border-neutral-800 px-6 py-4 text-xs font-bold uppercase tracking-[0.25em] text-neutral-500">
                    <span>Model</span>
                    <span>Accuracy</span>
                    <span>Precision</span>
                    <span>Recall</span>
                    <span>F1</span>
                    <span>ROC AUC</span>
                    <span>PR AUC</span>
                    <span>MCC</span>
                    <span>Threshold</span>
                    <span>Confusion</span>
                    <span>Explainability</span>
                  </div>

                  {comparison.model_results.map((result) => (
                    <div
                      key={result.model_name}
                      className="grid grid-cols-11 gap-4 border-b border-neutral-900 px-6 py-5 text-sm text-neutral-200 last:border-b-0"
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
                          <p className="mt-2 text-xs text-red-400">
                            Config: {JSON.stringify(result.selected_config)}
                          </p>
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
          </>
        ) : null}

        {trainingResults.length ? (
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
        ) : null}
      </div>
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
