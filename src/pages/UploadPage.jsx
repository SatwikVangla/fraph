import { useNavigate } from "react-router-dom";
import { useState } from "react";

import ParticleBackground from "../components/ParticleBackground";
import { apiRequest } from "../utils/api";

const LARGE_DATASET_BYTES = 100 * 1024 * 1024;

export default function UploadPage() {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [mappings, setMappings] = useState({
    sender_column: "",
    receiver_column: "",
    amount_column: "",
    label_column: "",
    transaction_type_column: "",
    step_column: "",
  });
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState("");
  const selectedFileSize = file?.size ?? 0;
  const selectedFileIsLarge = selectedFileSize >= LARGE_DATASET_BYTES;

  const validationSummary = preview
    ? buildValidationSummary({
        headers: preview.headers,
        mappings,
      })
    : null;

  const parsePreviewRows = (content) => {
    const lines = String(content || "").split(/\r?\n/).filter(Boolean);
    const headerLine = lines[0] || "";
    const delimiterCandidates = [",", ";", "\t", "|"];
    const delimiter = delimiterCandidates.reduce((best, candidate) => {
      const parts = headerLine.split(candidate).length;
      const bestParts = headerLine.split(best).length;
      return parts > bestParts ? candidate : best;
    }, ",");

    const headers = headerLine
      .split(delimiter)
      .map((item) => item.trim())
      .slice(0, 12);
    const sampleRows = lines
      .slice(1, 4)
      .map((line) => line.split(delimiter).slice(0, headers.length));
    return { headers, sampleRows };
  };

  const inferMappingDefaults = (headers) => {
    const canonicalize = (value) =>
      String(value || "")
        .toLowerCase()
        .replace(/[^a-z0-9]/g, "");
    const headerMap = new Map(headers.map((header) => [canonicalize(header), header]));
    const pick = (aliases) => {
      for (const alias of aliases) {
        const match = headerMap.get(canonicalize(alias));
        if (match) {
          return match;
        }
      }
      return "";
    };

    return {
      sender_column: pick([
        "sender",
        "source",
        "src",
        "from",
        "from_account",
        "origin",
        "nameOrig",
      ]),
      receiver_column: pick([
        "receiver",
        "target",
        "dst",
        "to",
        "to_account",
        "destination",
        "nameDest",
        "merchant",
      ]),
      amount_column: pick(["amount", "amt", "value", "transaction_amount", "payment_amount"]),
      label_column: pick(["isFraud", "is_fraud", "fraud", "label", "class", "target"]),
      transaction_type_column: pick(["type", "transaction_type", "channel", "payment_type"]),
      step_column: pick(["step", "timestamp", "time", "date", "transaction_time", "event_time"]),
    };
  };

  const handleFile = (nextFile) => {
    setFile(nextFile);
    if (!nextFile) {
      setPreview(null);
      setMappings({
        sender_column: "",
        receiver_column: "",
        amount_column: "",
        label_column: "",
        transaction_type_column: "",
        step_column: "",
      });
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      const parsedPreview = parsePreviewRows(reader.result);
      setPreview(parsedPreview);
      setMappings(inferMappingDefaults(parsedPreview.headers));
    };
    reader.readAsText(nextFile.slice(0, 24 * 1024));
  };

  const runAnalysis = async () => {
    if (!file) {
      setError("Select a dataset before running analysis.");
      return;
    }

    setError("");
    setScanning(true);

    try {
      const formData = new FormData();
      formData.append("file", file);
      Object.entries(mappings).forEach(([key, value]) => {
        if (value) {
          formData.append(key, value);
        }
      });

      const response = await apiRequest("/upload/", {
        method: "POST",
        body: formData,
      });

      setTimeout(() => {
        navigate("/dashboard", {
          state: {
            dataset: response.dataset,
          },
        });
      }, 1200);
    } catch (uploadError) {
      setScanning(false);
      setError(
        uploadError instanceof Error
          ? uploadError.message
          : "Upload failed. Check that the backend is running.",
      );
    }
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-black px-6 text-white">
      <div className="absolute inset-0 z-0 opacity-35">
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

      <div className="relative z-30 flex min-h-screen flex-col items-center justify-center py-10">
        <h1 className="mb-4 text-center text-4xl font-black tracking-[0.35em] md:text-5xl">
          DATASET TERMINAL
        </h1>
        <p className="mb-12 max-w-2xl text-center text-sm uppercase tracking-[0.35em] text-neutral-400">
          Upload PaySim-style transaction data and launch the fraud intelligence
          pipeline
        </p>

        <div className="w-full max-w-4xl rounded-2xl border-2 border-red-600 bg-black/60 p-10 backdrop-blur-sm transition hover:bg-red-600/10 md:p-16">
          <div
            onDragOver={(event) => event.preventDefault()}
            onDrop={(event) => {
              event.preventDefault();
              handleFile(event.dataTransfer.files?.[0] ?? null);
            }}
            className="rounded-2xl border border-dashed border-red-500/70 bg-red-950/10 px-6 py-10 text-center"
          >
            <p className="mb-3 text-lg tracking-wide">Drop Transaction Dataset</p>
            <p className="mb-6 text-sm uppercase tracking-[0.24em] text-neutral-500">
              Drag and drop a CSV or browse from disk
            </p>

            <input
              type="file"
              accept=".csv,text/csv"
              onChange={(event) => handleFile(event.target.files?.[0] ?? null)}
              className="mb-4 block w-full text-sm text-neutral-300 file:mr-4 file:rounded-md file:border file:border-red-600 file:bg-transparent file:px-4 file:py-2 file:text-white hover:file:bg-red-600/10"
            />

            <p className="min-h-6 text-sm text-neutral-400">
              {file ? `Selected: ${file.name}` : "No dataset selected"}
            </p>
            {file ? (
              <p className="mt-2 text-xs uppercase tracking-[0.18em] text-neutral-500">
                Size: {formatFileSize(selectedFileSize)}
              </p>
            ) : null}
          </div>

          {selectedFileIsLarge ? (
            <div className="mt-6 rounded-2xl border border-amber-700/60 bg-amber-950/20 p-5 text-sm text-amber-100">
              Large CSV detected. Upload will stream safely, but the dashboard and compare
              flow will use sampled rows to keep the app responsive. Use async training jobs
              for large datasets.
            </div>
          ) : null}

          {preview ? (
            <div className="mt-8 rounded-2xl border border-neutral-800 bg-neutral-950/80 p-6">
              <div className="flex flex-col gap-2 text-left">
                <p className="text-xs font-bold uppercase tracking-[0.28em] text-red-400">
                  Schema Preview
                </p>
                <p className="text-sm text-neutral-500">
                  First detected columns from the uploaded CSV.
                </p>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                {preview.headers.map((header) => (
                  <span
                    key={header}
                    className="rounded-full border border-neutral-800 bg-black/50 px-3 py-2 text-xs uppercase tracking-[0.18em] text-neutral-300"
                  >
                    {header}
                  </span>
                ))}
              </div>
              <div className="mt-6 grid gap-4 md:grid-cols-2">
                <MappingField
                  label="Sender Column"
                  value={mappings.sender_column}
                  options={preview.headers}
                  onChange={(value) =>
                    setMappings((current) => ({ ...current, sender_column: value }))
                  }
                />
                <MappingField
                  label="Receiver Column"
                  value={mappings.receiver_column}
                  options={preview.headers}
                  onChange={(value) =>
                    setMappings((current) => ({ ...current, receiver_column: value }))
                  }
                />
                <MappingField
                  label="Amount Column"
                  value={mappings.amount_column}
                  options={preview.headers}
                  onChange={(value) =>
                    setMappings((current) => ({ ...current, amount_column: value }))
                  }
                />
                <MappingField
                  label="Label Column"
                  value={mappings.label_column}
                  options={preview.headers}
                  optional
                  onChange={(value) =>
                    setMappings((current) => ({ ...current, label_column: value }))
                  }
                />
                <MappingField
                  label="Type Column"
                  value={mappings.transaction_type_column}
                  options={preview.headers}
                  optional
                  onChange={(value) =>
                    setMappings((current) => ({
                      ...current,
                      transaction_type_column: value,
                    }))
                  }
                />
                <MappingField
                  label="Time Column"
                  value={mappings.step_column}
                  options={preview.headers}
                  optional
                  onChange={(value) =>
                    setMappings((current) => ({ ...current, step_column: value }))
                  }
                />
              </div>
              {validationSummary ? (
                <div className="mt-6 rounded-2xl border border-neutral-800 bg-black/50 p-5">
                  <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                    <div>
                      <p className="text-xs font-bold uppercase tracking-[0.28em] text-red-400">
                        Upload Validation
                      </p>
                      <p className="mt-2 text-sm text-neutral-400">
                        The app checks whether the detected schema is strong enough for
                        graph fraud analysis, not just generic tabular scoring.
                      </p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <StatusBadge
                        label={`Confidence ${validationSummary.confidenceLabel}`}
                        tone={validationSummary.confidenceTone}
                      />
                      <StatusBadge
                        label={validationSummary.readinessLabel}
                        tone={validationSummary.readinessTone}
                      />
                    </div>
                  </div>

                  <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                    <ValidationRow
                      label="Sender"
                      value={mappings.sender_column || "Missing"}
                      valid={Boolean(mappings.sender_column)}
                    />
                    <ValidationRow
                      label="Receiver"
                      value={mappings.receiver_column || "Missing"}
                      valid={Boolean(mappings.receiver_column)}
                    />
                    <ValidationRow
                      label="Amount"
                      value={mappings.amount_column || "Missing"}
                      valid={Boolean(mappings.amount_column)}
                    />
                    <ValidationRow
                      label="Label"
                      value={mappings.label_column || "Optional"}
                      valid={Boolean(mappings.label_column)}
                      optional
                    />
                    <ValidationRow
                      label="Time"
                      value={mappings.step_column || "Optional"}
                      valid={Boolean(mappings.step_column)}
                      optional
                    />
                    <ValidationRow
                      label="Type"
                      value={mappings.transaction_type_column || "Optional"}
                      valid={Boolean(mappings.transaction_type_column)}
                      optional
                    />
                  </div>

                  <div className="mt-5 rounded-xl border border-neutral-900 bg-neutral-950/70 px-4 py-3">
                    <p className="text-xs font-bold uppercase tracking-[0.18em] text-neutral-500">
                      Assessment
                    </p>
                    <p className="mt-2 text-sm leading-6 text-neutral-300">
                      {validationSummary.description}
                    </p>
                  </div>
                </div>
              ) : null}
              <div className="mt-5 overflow-x-auto rounded-xl border border-neutral-900">
                <table className="min-w-full text-left text-xs text-neutral-300">
                  <thead className="bg-black/60 text-neutral-500">
                    <tr>
                      {preview.headers.map((header) => (
                        <th key={header} className="px-3 py-2 font-semibold uppercase tracking-[0.16em]">
                          {header}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {preview.sampleRows.map((row, rowIndex) => (
                      <tr key={`row-${rowIndex}`} className="border-t border-neutral-900">
                        {preview.headers.map((header, columnIndex) => (
                          <td key={`${header}-${rowIndex}`} className="px-3 py-2">
                            {row[columnIndex] ?? "--"}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : null}

          <div className="mt-8 text-center">
            <button
              onClick={runAnalysis}
              disabled={scanning}
              className="px-10 py-3 border border-red-600 hover:bg-red-600 transition font-bold tracking-wider disabled:cursor-not-allowed disabled:opacity-60"
            >
              {scanning ? "UPLOADING..." : "RUN FRAUD ANALYSIS"}
            </button>
          </div>

          {error ? (
            <p className="mt-6 text-sm text-red-400">{error}</p>
          ) : null}
        </div>

        {scanning ? (
          <div className="mt-16 text-center">
            <p className="mb-4 animate-pulse text-red-500">
              SCANNING TRANSACTIONS...
            </p>

            <div className="h-1 w-64 overflow-hidden bg-neutral-800">
              <div className="animate-loading-bar h-full bg-red-600"></div>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}

function formatFileSize(bytes) {
  if (!bytes) {
    return "0 B";
  }
  const units = ["B", "KB", "MB", "GB"];
  let value = bytes;
  let unitIndex = 0;
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }
  return `${value.toFixed(value >= 10 || unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`;
}

function MappingField({ label, value, options, onChange, optional = false }) {
  return (
    <label className="flex flex-col gap-2 text-left">
      <span className="text-[11px] font-bold uppercase tracking-[0.24em] text-neutral-500">
        {label}
      </span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="w-full rounded-xl border border-neutral-800 bg-black/60 px-4 py-3 text-sm text-white outline-none transition focus:border-red-600"
      >
        <option value="">{optional ? "Auto Detect" : "Select Column"}</option>
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}

function buildValidationSummary({ mappings }) {
  const hasSender = Boolean(mappings.sender_column);
  const hasReceiver = Boolean(mappings.receiver_column);
  const hasAmount = Boolean(mappings.amount_column);
  const hasLabel = Boolean(mappings.label_column);
  const hasTime = Boolean(mappings.step_column);
  const hasType = Boolean(mappings.transaction_type_column);

  const requiredCount = [hasSender, hasReceiver, hasAmount].filter(Boolean).length;
  const optionalCount = [hasLabel, hasTime, hasType].filter(Boolean).length;
  const score = requiredCount * 2 + optionalCount;

  let confidenceLabel = "Low";
  let confidenceTone = "neutral";
  if (score >= 8) {
    confidenceLabel = "High";
    confidenceTone = "green";
  } else if (score >= 5) {
    confidenceLabel = "Medium";
    confidenceTone = "amber";
  }

  if (hasSender && hasReceiver && hasAmount && hasLabel) {
    return {
      confidenceLabel,
      confidenceTone,
      readinessLabel: hasTime ? "Graph Ready" : "Graph Ready (No Time)",
      readinessTone: "green",
      description: hasTime
        ? "This CSV has the core relational fields needed for GNN-based fraud analysis, including source, destination, amount, label, and time context."
        : "This CSV has the core relational fields for graph fraud analysis. It is suitable for the GNN, but adding a time column would strengthen temporal transaction patterns.",
    };
  }

  if (hasSender && hasReceiver && hasAmount) {
    return {
      confidenceLabel,
      confidenceTone,
      readinessLabel: "Graph Ready (Unlabeled)",
      readinessTone: "amber",
      description:
        "This CSV has enough relationship structure for graph analysis, but it does not have a confirmed fraud label mapping yet. The dashboard will work, but supervised comparison and training will be limited.",
    };
  }

  if (hasAmount && (hasSender || hasReceiver)) {
    return {
      confidenceLabel,
      confidenceTone,
      readinessLabel: "Baseline Only",
      readinessTone: "amber",
      description:
        "This CSV only partially describes transaction relationships. It may still support limited analysis, but it is weaker for GNN-based fraud learning and better suited to simpler model checks.",
    };
  }

  return {
    confidenceLabel,
    confidenceTone,
    readinessLabel: "Weak Fit",
    readinessTone: "neutral",
    description:
      "This CSV does not expose enough transaction relationship structure yet. Without clear sender, receiver, and amount fields, the graph and GNN pipeline will not be reliable.",
  };
}

function StatusBadge({ label, tone }) {
  const toneClasses = {
    green: "border-emerald-700/70 bg-emerald-950/40 text-emerald-300",
    amber: "border-amber-700/70 bg-amber-950/40 text-amber-300",
    neutral: "border-neutral-700 bg-neutral-900 text-neutral-300",
  };

  return (
    <span
      className={`rounded-full border px-3 py-2 text-[11px] font-bold uppercase tracking-[0.18em] ${
        toneClasses[tone] || toneClasses.neutral
      }`}
    >
      {label}
    </span>
  );
}

function ValidationRow({ label, value, valid, optional = false }) {
  return (
    <div className="rounded-xl border border-neutral-900 bg-neutral-950/70 px-4 py-3">
      <div className="flex items-center justify-between gap-3">
        <span className="text-[11px] font-bold uppercase tracking-[0.18em] text-neutral-500">
          {label}
        </span>
        <span
          className={`text-[10px] font-bold uppercase tracking-[0.16em] ${
            valid
              ? "text-emerald-300"
              : optional
                ? "text-amber-300"
                : "text-red-300"
          }`}
        >
          {valid ? "Mapped" : optional ? "Optional" : "Missing"}
        </span>
      </div>
      <p className="mt-2 truncate text-sm text-white">{value}</p>
    </div>
  );
}
