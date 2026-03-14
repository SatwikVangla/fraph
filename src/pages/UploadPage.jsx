import { useNavigate } from "react-router-dom";
import { useState } from "react";

export default function UploadPage() {

const navigate = useNavigate();
const [file, setFile] = useState(null);
const [scanning, setScanning] = useState(false);

const runAnalysis = () => {

```
setScanning(true);

setTimeout(() => {
  navigate("/dashboard");
}, 2500);
```

};

return (


<div className="min-h-screen bg-black text-white flex flex-col items-center justify-center">

  <h1 className="text-5xl font-black mb-16 tracking-widest">
    DATASET TERMINAL
  </h1>

  {/* Upload Zone */}

  <div className="border-2 border-red-600 p-16 rounded-xl text-center hover:bg-red-600/10 transition">

    <p className="mb-6 text-lg tracking-wide">
      Drop Transaction Dataset
    </p>

    <input
      type="file"
      onChange={(e) => setFile(e.target.files[0])}
      className="mb-8"
    />

    <button
       onClick={() => navigate("/dashboard")}
       className="px-10 py-3 border border-red-600 hover:bg-red-600 transition font-bold tracking-wider"
    >
      RUN FRAUD ANALYSIS
    </button>

  </div>

  {/* Scanning Animation */}

  {scanning && (

    <div className="mt-16 text-center">

      <p className="animate-pulse text-red-500 mb-4">
        SCANNING TRANSACTIONS...
      </p>

      <div className="w-64 h-1 bg-neutral-800 overflow-hidden">

        <div className="h-full bg-red-600 animate-loading-bar"></div>

      </div>

    </div>

  )}

</div>


);
}

