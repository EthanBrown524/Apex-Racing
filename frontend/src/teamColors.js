export const TEAM_COLORS = {
  red_bull:     { primary: "#3671C6", accent: "#fcd700" },
  ferrari:      { primary: "#dc0000", accent: "#ffffff" },
  mercedes:     { primary: "#00d2be", accent: "#ffffff" },
  aston_martin: { primary: "#006f62", accent: "#cedc00" },
  mclaren:      { primary: "#ff8700", accent: "#ffffff" },
  alpine:       { primary: "#0090ff", accent: "#fe86bc" },
  alphatauri:   { primary: "#1634cb", accent: "#ffffff" },
  alfa:         { primary: "#b12335", accent: "#ffffff" },
  haas:         { primary: "#cccccc", accent: "#e8002d" },
  williams:     { primary: "#00a0dd", accent: "#ffffff" },
  rb:           { primary: "#1634cb", accent: "#ffffff" },
  kick_sauber:  { primary: "#00e701", accent: "#ffffff" },
  unknown:      { primary: "#888888", accent: "#ffffff" },
};

export const DRIVER_TEAM_2023 = {
  VER: "red_bull",    PER: "red_bull",
  LEC: "ferrari",     SAI: "ferrari",
  HAM: "mercedes",    RUS: "mercedes",
  ALO: "aston_martin",STR: "aston_martin",
  NOR: "mclaren",     PIA: "mclaren",
  OCO: "alpine",      GAS: "alpine",
  TSU: "alphatauri",  DEV: "alphatauri",
  BOT: "alfa",        ZHO: "alfa",
  MAG: "haas",        HUL: "haas",
  ALB: "williams",    SAR: "williams",
};

export const DRIVER_TEAMS_BY_YEAR = {
  2023: DRIVER_TEAM_2023,
};

export function getDriverColor(code, year = 2023) {
  const teamMap = DRIVER_TEAMS_BY_YEAR[year] ?? DRIVER_TEAM_2023;
  const teamRef = teamMap[code?.toUpperCase()] ?? "unknown";
  return TEAM_COLORS[teamRef] ?? TEAM_COLORS.unknown;
}

export function getDriverPrimary(code, year = 2023) {
  return getDriverColor(code, year).primary;
}