import { BrowserRouter as Router, Route, Routes } from "react-router-dom";

import Hero from "./components/Hero";
import ComparePage from "./pages/ComparePage";
import DashboardPage from "./pages/DashboardPage";
import UploadPage from "./pages/UploadPage";

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Hero />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/compare/:datasetId" element={<ComparePage />} />
      </Routes>
    </Router>
  );
}
