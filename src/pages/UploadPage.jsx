import { useNavigate } from "react-router-dom";
import { useState } from "react";

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

      const response = await fetch(
        `${import.meta.env.VITE_API_BASE_URL || ""}/upload/`,
        {
          method: "POST",
          body: formData,
        },
      );

      if (!response.ok) {
        throw new Error(`Upload failed with status ${response.status}`);
      }

      setTimeout(() => {
        navigate("/dashboard");
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
    <div className="min-h-screen bg-black text-white flex flex-col items-center justify-center px-6">
      <h1 className="text-center text-4xl md:text-5xl font-black mb-16 tracking-widest">
        DATASET TERMINAL
      </h1>

      <div className="w-full max-w-2xl border-2 border-red-600 p-10 md:p-16 rounded-xl text-center hover:bg-red-600/10 transition">
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
          <p className="animate-pulse text-red-500 mb-4">
            SCANNING TRANSACTIONS...
          </p>

          <div className="w-64 h-1 bg-neutral-800 overflow-hidden">
            <div className="h-full bg-red-600 animate-loading-bar"></div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
