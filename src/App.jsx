import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

import Hero from "./components/Hero";
import UploadPage from "./pages/UploadPage";
import DashboardPage from "./pages/DashboardPage";

export default function App() {
return ( <Router>


  <Routes>

    <Route path="/" element={<Hero />} />

    <Route path="/upload" element={<UploadPage />} />

    <Route path="/dashboard" element={<DashboardPage />} />

  </Routes>

</Router>


);
}

