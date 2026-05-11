import { NavLink, Route, Routes } from "react-router-dom";

import ForecastPage from "./pages/ForecastPage.jsx";
import RewindPage from "./pages/RewindPage.jsx";

export default function App() {
  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-badge">APEX</span>
          <span className="brand-name">Racing Records</span>
        </div>
        <nav className="topnav" aria-label="Primary">
          <NavLink to="/" end>Race Rewind</NavLink>
          <NavLink to="/forecast">Forecast</NavLink>
        </nav>
      </header>

      <Routes>
        <Route path="/" element={<RewindPage />} />
        <Route path="/forecast" element={<ForecastPage />} />
      </Routes>
    </div>
  );
}