import { useEffect, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";

import PlaceholderGraph from "../components/PlaceholderGraph";
import { apiRequest } from "../utils/api";

export default function DashboardPage() {
  const location = useLocation();
  const [analysis, setAnalysis] = useState(null);
  const [dataset, setDataset] = useState(location.state?.dataset ?? null);
  const [datasets, setDatasets] = useState([]);
  const [selectedTransactionId, setSelectedTransactionId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
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
              Analyze suspicious flows, inspect transaction relationships, and compare the
              relationship-aware GNN against KNN, Logistic Regression, Linear SVC, and
              Gaussian Naive Bayes.
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

          {analysis?.dataset ? (
            <Link
              to={`/compare/${analysis.dataset.id}`}
              state={{ dataset: analysis.dataset }}
              className="inline-flex w-fit items-center border border-red-600 px-5 py-3 text-sm font-bold uppercase tracking-[0.25em] text-white transition hover:bg-red-600"
            >
              Open GNN Comparison
            </Link>
          ) : null}
        </div>

        {loading ? (
          <div className="rounded-2xl border border-neutral-800 bg-neutral-950 p-10 text-neutral-300">
            Running fraud analysis...
          </div>
        ) : null}

        {error ? (
          <div className="rounded-2xl border border-red-800 bg-red-950/20 p-6 text-red-300">
            {error}
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

            <div className="mb-12 grid gap-6 lg:grid-cols-[1.5fr_1fr]">
              <div className="rounded-2xl border border-neutral-800 bg-neutral-950 p-6">
                <div className="mb-6">
                  <h2 className="text-2xl font-bold">Transaction Graph</h2>
                  <p className="mt-2 text-sm text-neutral-500">
                    Nodes: {analysis.graph.node_count} | Edges: {analysis.graph.edge_count} | Components: {analysis.graph.connected_components}
                  </p>
                </div>

                <div className="overflow-hidden rounded-xl border border-neutral-900 bg-black/40">
                  <PlaceholderGraph
                    graph={analysis.graph}
                    focusTransactionId={selectedTransactionId}
                    onTransactionSelect={setSelectedTransactionId}
                  />
                </div>
              </div>

              <div className="rounded-2xl border border-neutral-800 bg-neutral-950 p-6">
                <h2 className="text-2xl font-bold">Risk Snapshot</h2>
                <div className="mt-6 space-y-5 text-sm text-neutral-300">
                  <SnapshotRow label="Fraud Rate" value={analysis.summary.fraud_rate} />
                  <SnapshotRow
                    label="Total Amount"
                    value={analysis.summary.total_amount}
                  />
                  <SnapshotRow label="Top Nodes" value={analysis.graph.top_nodes.length} />
                  <SnapshotRow label="Top Edges" value={analysis.graph.top_edges.length} />
                </div>
              </div>
            </div>

            <div className="overflow-hidden rounded-2xl border border-neutral-800 bg-neutral-950">
              <div className="border-b border-neutral-800 px-6 py-5">
                <h2 className="text-2xl font-bold">Suspicious Transactions</h2>
                <p className="mt-2 text-sm text-neutral-500">
                  Select a transaction to focus its sender-to-receiver path in the graph.
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
                    {analysis.suspicious_transactions.map((transaction) => (
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
                    ))}
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

function SnapshotRow({ label, value }) {
  return (
    <div className="flex items-center justify-between border-b border-neutral-900 pb-3 last:border-b-0">
      <span className="uppercase tracking-[0.2em] text-neutral-500">{label}</span>
      <span className="text-lg font-semibold text-white">{value}</span>
    </div>
  );
}
