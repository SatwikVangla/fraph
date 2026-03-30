import { useNavigate } from "react-router-dom";
import { useState } from "react";

import ParticleBackground from "../components/ParticleBackground";
import { apiRequest } from "../utils/api";

export default function UploadPage() {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState("");

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

        <div className="w-full max-w-2xl rounded-2xl border-2 border-red-600 bg-black/60 p-10 text-center backdrop-blur-sm transition hover:bg-red-600/10 md:p-16">
          <p className="mb-6 text-lg tracking-wide">Drop Transaction Dataset</p>

          <input
            type="file"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            className="mb-4 block w-full text-sm text-neutral-300 file:mr-4 file:rounded-md file:border file:border-red-600 file:bg-transparent file:px-4 file:py-2 file:text-white hover:file:bg-red-600/10"
          />

          <p className="mb-8 min-h-6 text-sm text-neutral-400">
            {file ? `Selected: ${file.name}` : "No dataset selected"}
          </p>

          <button
            onClick={runAnalysis}
            disabled={scanning}
            className="px-10 py-3 border border-red-600 hover:bg-red-600 transition font-bold tracking-wider disabled:cursor-not-allowed disabled:opacity-60"
          >
            {scanning ? "UPLOADING..." : "RUN FRAUD ANALYSIS"}
          </button>

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
