import { useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";

import { apiRequest } from "../utils/api";

const MODEL_LABELS = {
  gnn: "GNN",
  knn: "KNN",
  linear_svc: "Linear SVC",
  logistic_regression: "Logistic Regression",
  random_forest: "Random Forest",
};

export default function ComparePage() {
  const location = useLocation();
  const { datasetId } = useParams();
  const [comparison, setComparison] = useState(null);
  const [trainingResults, setTrainingResults] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [training, setTraining] = useState(false);

  useEffect(() => {
    let active = true;

    async function loadComparison() {
      try {
        setLoading(true);
        setError("");

        const payload = datasetId
          ? { dataset_id: Number(datasetId) }
          : { dataset_name: location.state?.dataset?.name };

        const response = await apiRequest("/compare/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            ...payload,
            model_names: [
              "knn",
              "logistic_regression",
              "linear_svc",
              "random_forest",
              "gnn",
            ],
          }),
        });

        if (active) {
          setComparison(response);
        }
      } catch (requestError) {
        if (active) {
          setError(
            requestError instanceof Error
              ? requestError.message
              : "Failed to load model comparison.",
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    async function loadArtifacts() {
      if (!datasetId) {
        return;
      }
      try {
        const artifacts = await apiRequest(`/train/artifacts/${datasetId}`);
        if (active) {
          setTrainingResults(artifacts);
        }
      } catch {
        // Keep the comparison page usable even if there are no saved artifacts yet.
      }
    }

    loadComparison();
    loadArtifacts();
    return () => {
      active = false;
    };
  }, [datasetId, location.state?.dataset?.name]);

  async function handleTraining() {
    try {
      setTraining(true);
      setError("");

      const payload = datasetId
        ? { dataset_id: Number(datasetId) }
        : { dataset_name: location.state?.dataset?.name };

      const response = await apiRequest("/train/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ...payload,
          model_names: [
            "knn",
            "logistic_regression",
            "linear_svc",
            "random_forest",
            "gnn",
          ],
          epochs: 50,
          hidden_dim: 32,
          learning_rate: 0.01,
        }),
      });

      setTrainingResults(response.training_results);
      const refreshedComparison = await apiRequest("/compare/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ...payload,
          model_names: [
            "knn",
            "logistic_regression",
            "linear_svc",
            "random_forest",
            "gnn",
          ],
        }),
      });
      setComparison(refreshedComparison);
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

  return (
    <div className="min-h-screen bg-black px-6 py-10 text-white md:px-12">
      <div className="mx-auto max-w-6xl">
        <div className="mb-10 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="mb-3 text-sm uppercase tracking-[0.35em] text-red-500">
              Traditional Models vs GNN
            </p>
            <h1 className="text-4xl md:text-5xl font-black tracking-wide">
              Model Comparison
            </h1>
            <p className="mt-3 text-neutral-400">
              Dataset: {comparison?.dataset?.name ?? location.state?.dataset?.name ?? "--"}
            </p>
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
          <div className="overflow-hidden rounded-2xl border border-neutral-800 bg-neutral-950">
            <div className="grid grid-cols-6 gap-4 border-b border-neutral-800 px-6 py-4 text-xs font-bold uppercase tracking-[0.25em] text-neutral-500">
              <span>Model</span>
              <span>Accuracy</span>
              <span>Precision</span>
              <span>Recall</span>
              <span>F1</span>
              <span>ROC AUC</span>
            </div>

            {comparison.model_results.map((result) => (
              <div
                key={result.model_name}
                className="grid grid-cols-6 gap-4 border-b border-neutral-900 px-6 py-5 text-sm text-neutral-200 last:border-b-0"
              >
                <div>
                  <p className="font-semibold">
                    {MODEL_LABELS[result.model_name] ?? result.model_name}
                  </p>
                  <p className="mt-2 text-xs uppercase tracking-[0.2em] text-neutral-500">
                    {result.status}
                  </p>
                  <p className="mt-2 text-xs text-neutral-500">{result.details}</p>
                </div>
                <MetricCell value={result.accuracy} />
                <MetricCell value={result.precision} />
                <MetricCell value={result.recall} />
                <MetricCell value={result.f1_score} />
                <MetricCell value={result.roc_auc} />
              </div>
            ))}
          </div>
        ) : null}

        {trainingResults.length ? (
          <div className="mt-10 overflow-hidden rounded-2xl border border-neutral-800 bg-neutral-950">
            <div className="border-b border-neutral-800 px-6 py-5">
              <h2 className="text-2xl font-bold">Persisted Training Runs</h2>
            </div>
            {trainingResults.map((result) => (
              <div
                key={`artifact-${result.model_name}`}
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
