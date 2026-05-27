import { lazy, Suspense } from "react";
import { NavLink, Route, Routes, useLocation } from "react-router-dom";

import Footer from "./components/Footer/Footer.jsx";

const AboutPage = lazy(() => import("./pages/AboutPage.jsx"));
const ComparePage = lazy(() => import("./pages/ComparePage.jsx"));
const DriverPage = lazy(() => import("./pages/DriverPage.jsx"));
const ForecastPage = lazy(() => import("./pages/ForecastPage.jsx"));
const GloryPathPage = lazy(() => import("./pages/GloryPathPage.jsx"));
const HomePage = lazy(() => import("./pages/HomePage.jsx"));
const LibraryPage = lazy(() => import("./pages/LibraryPage.jsx"));
const RewindPage = lazy(() => import("./pages/RewindPage.jsx"));
const SeasonsPage = lazy(() => import("./pages/SeasonsPage.jsx"));
const ShowcasePage = lazy(() => import("./pages/ShowcasePage.jsx"));
const StandingsPage = lazy(() => import("./pages/StandingsPage.jsx"));
const StatsPage = lazy(() => import("./pages/StatsPage.jsx"));

export default function App() {
  const location = useLocation();
  const isSimulator = location.pathname.startsWith("/rewind");

  return (
    <div className={`app-shell ${isSimulator ? "simulator-shell" : ""}`}>
      <header className="topbar">
        <div className="brand">
          <span className="brand-badge">APEX</span>
          <span className="brand-name">
            <strong>Race Director</strong>
            <span className="brand-sub">F1 alternate-history simulator</span>
          </span>
        </div>
        <nav className="topnav" aria-label="Primary">
          <NavLink to="/" end>Home</NavLink>
          <NavLink to="/seasons">Seasons</NavLink>
          <NavLink to="/library">Library</NavLink>
          <NavLink to="/showcase">Showcase</NavLink>
          <NavLink to="/rewind">Time Machine</NavLink>
          <NavLink to="/glory">Glory Path</NavLink>
          <NavLink to="/forecast">Forecast</NavLink>
          <NavLink to="/compare">Compare</NavLink>
          <NavLink to="/standings">Standings</NavLink>
          <NavLink to="/stats">Stats</NavLink>
          <NavLink to="/about">About</NavLink>
        </nav>
      </header>

      <Suspense fallback={<div className="empty">Loading...</div>}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/seasons" element={<SeasonsPage />} />
          <Route path="/seasons/:year" element={<LibraryPage />} />
          <Route path="/library" element={<LibraryPage />} />
          <Route path="/showcase" element={<ShowcasePage />} />
          <Route path="/rewind" element={<RewindPage />} />
          <Route path="/rewind/:raceId" element={<RewindPage />} />
          <Route path="/glory" element={<GloryPathPage />} />
          <Route path="/glory/:raceId" element={<GloryPathPage />} />
          <Route path="/forecast" element={<ForecastPage />} />
          <Route path="/forecast/:raceId" element={<ForecastPage />} />
          <Route path="/stats" element={<StatsPage />} />
          <Route path="/standings" element={<StandingsPage />} />
          <Route path="/standings/:year" element={<StandingsPage />} />
          <Route path="/driver/:code/:year" element={<DriverPage />} />
          <Route path="/compare" element={<ComparePage />} />
          <Route path="/compare/:raceId" element={<ComparePage />} />
          <Route path="/about" element={<AboutPage />} />
        </Routes>
      </Suspense>

      {!isSimulator && <Footer />}
    </div>
  );
}
