import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";

import PlaceholderGraph from "../components/PlaceholderGraph";
import { apiRequest } from "../utils/api";

export default function GraphPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { datasetId } = useParams();
  const [analysis, setAnalysis] = useState(null);
  const [datasets, setDatasets] = useState([]);
  const [dataset, setDataset] = useState(location.state?.dataset ?? null);
  const [preprocessingJob, setPreprocessingJob] = useState(null);
  const [selectedTransactionId, setSelectedTransactionId] = useState(location.state?.transactionId ?? null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const transactionRowRefs = useRef(new Map());
  const routeDatasetId = datasetId ? Number(datasetId) : null;

  useEffect(() => {
    let active = true;

    async function loadGraphAnalysis() {
      try {
        setLoading(true);
        setError("");
        setAnalysis(null);

        const availableDatasets = await apiRequest("/upload/datasets");
        if (!active) {
          return;
        }
        setDatasets(availableDatasets);

        const resolvedDataset =
          availableDatasets.find((item) => item.id === routeDatasetId) ??
          dataset ??
          location.state?.dataset ??
          availableDatasets[0] ??
          null;

        if (!resolvedDataset) {
          throw new Error("No datasets available. Upload a CSV first.");
        }

        if ((!routeDatasetId || routeDatasetId !== resolvedDataset.id) && active) {
          navigate(`/graph/${resolvedDataset.id}`, {
            replace: true,
            state: { dataset: resolvedDataset },
          });
          return;
        }

        setDataset(resolvedDataset);

        if (resolvedDataset.large_dataset) {
          const jobStatus = await apiRequest(
            `/upload/preprocessing-status/${resolvedDataset.id}`,
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
            dataset_id: resolvedDataset.id,
            threshold: 0.65,
            limit: 8,
          }),
        });

        if (active) {
          setAnalysis(response);
          setSelectedTransactionId(
            location.state?.transactionId ?? response.suspicious_transactions?.[0]?.transaction_id ?? null,
          );
        }
      } catch (requestError) {
        if (active) {
          setError(
            requestError instanceof Error
              ? requestError.message
              : "Failed to load graph analysis.",
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadGraphAnalysis();
    return () => {
      active = false;
    };
  }, [routeDatasetId, location.state?.dataset?.id, navigate]);

  useEffect(() => {
    if (!dataset?.large_dataset || !preprocessingJob || preprocessingJob.status === "completed" || preprocessingJob.status === "failed") {
      return undefined;
    }

    const intervalId = window.setInterval(async () => {
      try {
        const nextJob = await apiRequest(`/upload/preprocessing-status/${dataset.id}`);
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
            location.state?.transactionId ?? response.suspicious_transactions?.[0]?.transaction_id ?? null,
          );
        }
      } catch (requestError) {
        setError(
          requestError instanceof Error
            ? requestError.message
            : "Failed to load graph preparation status.",
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
        <div className="mb-12 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="mb-3 text-sm uppercase tracking-[0.35em] text-red-500">
              Dedicated Relationship Explorer
            </p>
            <h1 className="text-4xl font-black tracking-wide md:text-5xl">
              Transaction Graph Analysis
            </h1>
            <p className="mt-3 text-neutral-400">Dataset: {dataset?.name ?? "--"}</p>
            <p className="mt-2 max-w-3xl text-sm text-neutral-500">
              Inspect the graph separately from the dashboard so the relationship structure,
              suspicious paths, and connected entities are easier to evaluate.
            </p>
            {datasets.length ? (
              <div className="mt-5 max-w-sm">
                <label
                  htmlFor="graph-dataset"
                  className="mb-2 block text-xs font-bold uppercase tracking-[0.25em] text-neutral-500"
                >
                  Switch Dataset
                </label>
                <select
                  id="graph-dataset"
                  value={dataset?.id ?? ""}
                  onChange={(event) => {
                    const nextDataset = datasets.find(
                      (item) => item.id === Number(event.target.value),
                    );
                    if (nextDataset) {
                      navigate(`/graph/${nextDataset.id}`, {
                        state: { dataset: nextDataset },
                      });
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
            {dataset ? (
              <Link
                to={`/compare/${dataset.id}`}
                state={{ dataset }}
                className="inline-flex items-center border border-red-600 px-5 py-3 text-sm font-bold uppercase tracking-[0.25em] text-white transition hover:bg-red-600"
              >
                Open GNN Comparison
              </Link>
            ) : null}
            <Link
              to="/dashboard"
              state={dataset ? { dataset } : undefined}
              className="inline-flex items-center border border-neutral-700 px-5 py-3 text-sm font-bold uppercase tracking-[0.25em] text-white transition hover:border-neutral-500"
            >
              Back To Dashboard
            </Link>
          </div>
        </div>

        {loading ? (
          <div className="rounded-2xl border border-neutral-800 bg-neutral-950 p-10 text-neutral-300">
            Loading graph analysis...
          </div>
        ) : null}

        {!loading && dataset?.large_dataset && preprocessingJob && preprocessingJob.status !== "completed" ? (
          <div className="mb-10 rounded-2xl border border-amber-700/60 bg-amber-950/20 p-6 text-amber-100">
            <p className="text-sm font-bold uppercase tracking-[0.24em] text-amber-300">
              Large Dataset Preparation
            </p>
            <p className="mt-3 text-sm">{preprocessingJob.message}</p>
            <p className="mt-2 text-xs uppercase tracking-[0.18em] text-amber-200/80">
              Status: {preprocessingJob.status} | Progress: {preprocessingJob.progress}%
            </p>
            <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-black/40">
              <div
                className="h-full bg-amber-400 transition-all duration-300"
                style={{ width: `${preprocessingJob.progress}%` }}
              />
            </div>
          </div>
        ) : null}

        {error ? (
          <div className="rounded-2xl border border-red-800 bg-red-950/20 p-6 text-red-300">
            {error}
          </div>
        ) : null}

        {!loading && !error && analysis ? (
          <>
            <div className="mb-10 grid gap-6 md:grid-cols-4">
              <MetricCard label="Nodes" value={analysis.graph.node_count} />
              <MetricCard label="Edges" value={analysis.graph.edge_count} />
              <MetricCard label="Components" value={analysis.graph.connected_components} />
              <MetricCard label="Suspicious Transactions" value={analysis.summary.suspicious_transactions} accent="text-red-500" />
            </div>

            <div className="mb-12 overflow-hidden rounded-2xl border border-neutral-800 bg-neutral-950 p-6">
              <div className="mb-6 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
                <div>
                  <h2 className="text-2xl font-bold">Relationship Map</h2>
                  <p className="mt-2 text-sm text-neutral-500">
                    Focus a suspicious transaction to isolate its sender-to-receiver path and inspect how connected accounts shape fraud context.
                  </p>
                </div>
                <div className="rounded-xl border border-neutral-800 bg-black/40 px-4 py-3 text-xs uppercase tracking-[0.22em] text-neutral-300">
                  Fraud rate {analysis.summary.fraud_rate}
                </div>
              </div>

              <div className="min-w-0 overflow-hidden rounded-xl border border-neutral-900 bg-black/40">
                <PlaceholderGraph
                  graph={analysis.graph}
                  focusTransactionId={selectedTransactionId}
                  onTransactionSelect={setSelectedTransactionId}
                />
              </div>
            </div>

            <div className="overflow-hidden rounded-2xl border border-neutral-800 bg-neutral-950">
              <div className="border-b border-neutral-800 px-6 py-5">
                <h2 className="text-2xl font-bold">Suspicious Transactions</h2>
                <p className="mt-2 text-sm text-neutral-500">
                  Select a transaction to focus its local relationship path in the graph.
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
                        onClick={() => setSelectedTransactionId(transaction.transaction_id)}
                        className={`cursor-pointer border-b border-neutral-900 transition last:border-b-0 ${
                          selectedTransactionId === transaction.transaction_id
                            ? "bg-red-950/30"
                            : "hover:bg-white/5"
                        }`}
                      >
                        <td className="px-6 py-4 font-medium">{transaction.transaction_id}</td>
                        <td className="px-6 py-4">{transaction.sender}</td>
                        <td className="px-6 py-4">{transaction.receiver}</td>
                        <td className="px-6 py-4">{transaction.amount.toLocaleString()}</td>
                        <td className="px-6 py-4 text-red-400">{transaction.risk_score}</td>
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

function MetricCard({ label, value, accent = "" }) {
  return (
    <div className="rounded-2xl border border-neutral-800 bg-neutral-950 p-6">
      <p className="text-sm uppercase tracking-[0.25em] text-neutral-500">{label}</p>
      <p className={`mt-4 text-4xl font-black ${accent}`}>{value}</p>
    </div>
  );
}
