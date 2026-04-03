import { Suspense, lazy } from "react";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";

const Hero = lazy(() => import("./components/Hero"));
const ComparePage = lazy(() => import("./pages/ComparePage"));
const DashboardPage = lazy(() => import("./pages/DashboardPage"));
const UploadPage = lazy(() => import("./pages/UploadPage"));

function RouteLoader() {
  return (
    <div className="min-h-screen bg-black px-6 py-10 text-white md:px-12">
      <div className="mx-auto flex min-h-[70vh] max-w-5xl items-center justify-center rounded-2xl border border-neutral-800 bg-neutral-950 text-sm uppercase tracking-[0.32em] text-neutral-500">
        Loading Interface
      </div>
    </div>
  );
}

export default function App() {
  return (
    <Router>
      <Suspense fallback={<RouteLoader />}>
        <Routes>
          <Route path="/" element={<Hero />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/compare/:datasetId" element={<ComparePage />} />
        </Routes>
      </Suspense>
    </Router>
  );
}
