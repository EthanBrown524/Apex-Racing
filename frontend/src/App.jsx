import { NavLink, Route, Routes } from "react-router-dom";

import Footer from "./components/Footer/Footer.jsx";
import AboutPage from "./pages/AboutPage.jsx";
import ForecastPage from "./pages/ForecastPage.jsx";
import GloryPathPage from "./pages/GloryPathPage.jsx";
import LibraryPage from "./pages/LibraryPage.jsx";
import RewindPage from "./pages/RewindPage.jsx";
import ShowcasePage from "./pages/ShowcasePage.jsx";
import StatsPage from "./pages/StatsPage.jsx";

export default function App() {
  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-badge">APEX</span>
          <span className="brand-name">
            <strong>Race Director</strong>
            <span className="brand-sub">F1 alternate-history simulator</span>
          </span>
        </div>
        <nav className="topnav" aria-label="Primary">
          <NavLink to="/" end>Library</NavLink>
          <NavLink to="/showcase">Showcase</NavLink>
          <NavLink to="/rewind">Time Machine</NavLink>
          <NavLink to="/glory">Glory Path</NavLink>
          <NavLink to="/forecast">Forecast</NavLink>
          <NavLink to="/stats">Stats</NavLink>
          <NavLink to="/about">About</NavLink>
        </nav>
      </header>

      <Routes>
        <Route path="/" element={<LibraryPage />} />
        <Route path="/showcase" element={<ShowcasePage />} />
        <Route path="/rewind" element={<RewindPage />} />
        <Route path="/rewind/:raceId" element={<RewindPage />} />
        <Route path="/glory" element={<GloryPathPage />} />
        <Route path="/glory/:raceId" element={<GloryPathPage />} />
        <Route path="/forecast" element={<ForecastPage />} />
        <Route path="/forecast/:raceId" element={<ForecastPage />} />
        <Route path="/stats" element={<StatsPage />} />
        <Route path="/about" element={<AboutPage />} />
      </Routes>

      <Footer />
    </div>
  );
}
