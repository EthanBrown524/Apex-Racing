export const TEAM_COLORS = {
  red_bull:     { primary: "#3671C6", accent: "#fcd700" },
  ferrari:      { primary: "#dc0000", accent: "#ffffff" },
  mercedes:     { primary: "#00d2be", accent: "#ffffff" },
  aston_martin: { primary: "#006f62", accent: "#cedc00" },
  racing_point: { primary: "#f596c8", accent: "#ffffff" },
  mclaren:      { primary: "#ff8700", accent: "#ffffff" },
  alpine:       { primary: "#0090ff", accent: "#fe86bc" },
  renault:      { primary: "#fff500", accent: "#000000" },
  alphatauri:   { primary: "#1634cb", accent: "#ffffff" },
  toro_rosso:   { primary: "#469bff", accent: "#ffffff" },
  alfa:         { primary: "#b12335", accent: "#ffffff" },
  haas:         { primary: "#cccccc", accent: "#e8002d" },
  williams:     { primary: "#00a0dd", accent: "#ffffff" },
  rb:           { primary: "#1634cb", accent: "#ffffff" },
  kick_sauber:  { primary: "#00e701", accent: "#ffffff" },
  unknown:      { primary: "#888888", accent: "#ffffff" },
};

export const DRIVER_TEAMS_BY_YEAR = {
  2019: {
    HAM: "mercedes",    BOT: "mercedes",
    VER: "red_bull",    GAS: "red_bull",   ALB: "red_bull",
    LEC: "ferrari",     VET: "ferrari",
    NOR: "mclaren",     SAI: "mclaren",
    RIC: "renault",     HUL: "renault",
    PER: "racing_point", STR: "racing_point",
    KVY: "toro_rosso",  ALB_T: "toro_rosso",
    KMG: "haas",        GRO: "haas", MAG: "haas",
    KUB: "williams",    RUS: "williams",
    RAI: "alfa",        GIO: "alfa",
  },
  2020: {
    HAM: "mercedes",    BOT: "mercedes",   RUS: "mercedes",
    VER: "red_bull",    ALB: "red_bull",
    LEC: "ferrari",     VET: "ferrari",
    NOR: "mclaren",     SAI: "mclaren",
    RIC: "renault",     OCO: "renault",
    PER: "racing_point", STR: "racing_point",
    HUL: "racing_point",
    GAS: "alphatauri",  KVY: "alphatauri",
    MAG: "haas",        GRO: "haas", FIT: "haas",
    LAT: "williams",    RUS_2: "williams", AIT: "williams",
    RAI: "alfa",        GIO: "alfa", KUB: "alfa",
  },
  2021: {
    HAM: "mercedes",    BOT: "mercedes",
    VER: "red_bull",    PER: "red_bull",
    LEC: "ferrari",     SAI: "ferrari",
    NOR: "mclaren",     RIC: "mclaren",
    ALO: "alpine",      OCO: "alpine",
    VET: "aston_martin", STR: "aston_martin",
    GAS: "alphatauri",  TSU: "alphatauri",
    MAZ: "haas",        MSC: "haas",
    LAT: "williams",    RUS: "williams",
    RAI: "alfa",        GIO: "alfa", KUB: "alfa",
  },
  2022: {
    HAM: "mercedes",    RUS: "mercedes",
    VER: "red_bull",    PER: "red_bull",
    LEC: "ferrari",     SAI: "ferrari",
    NOR: "mclaren",     RIC: "mclaren",
    ALO: "alpine",      OCO: "alpine",
    VET: "aston_martin", STR: "aston_martin", HUL: "aston_martin",
    GAS: "alphatauri",  TSU: "alphatauri",
    MAG: "haas",        MSC: "haas",
    LAT: "williams",    ALB: "williams", DEV: "williams",
    BOT: "alfa",        ZHO: "alfa",
  },
  2023: {
    VER: "red_bull",    PER: "red_bull",
    LEC: "ferrari",     SAI: "ferrari",
    HAM: "mercedes",    RUS: "mercedes",
    ALO: "aston_martin", STR: "aston_martin",
    NOR: "mclaren",     PIA: "mclaren",
    OCO: "alpine",      GAS: "alpine",
    TSU: "alphatauri",  DEV: "alphatauri", RIC: "alphatauri", LAW: "alphatauri",
    BOT: "alfa",        ZHO: "alfa",
    MAG: "haas",        HUL: "haas",
    ALB: "williams",    SAR: "williams",
  },
  2024: {
    VER: "red_bull",    PER: "red_bull",
    LEC: "ferrari",     SAI: "ferrari",   BEA: "ferrari",
    HAM: "mercedes",    RUS: "mercedes",
    ALO: "aston_martin", STR: "aston_martin",
    NOR: "mclaren",     PIA: "mclaren",
    OCO: "alpine",      GAS: "alpine", DOO: "alpine",
    TSU: "rb",          RIC: "rb", LAW: "rb",
    BOT: "kick_sauber", ZHO: "kick_sauber",
    MAG: "haas",        HUL: "haas", BEA_H: "haas",
    ALB: "williams",    SAR: "williams", COL: "williams",
  },
};

export const DRIVER_TEAM_2023 = DRIVER_TEAMS_BY_YEAR[2023];

export function getDriverColor(code, year = 2023) {
  const teamMap = DRIVER_TEAMS_BY_YEAR[year] ?? DRIVER_TEAMS_BY_YEAR[2023];
  const teamRef = teamMap[code?.toUpperCase()] ?? "unknown";
  return TEAM_COLORS[teamRef] ?? TEAM_COLORS.unknown;
}

export function getDriverPrimary(code, year = 2023) {
  return getDriverColor(code, year).primary;
}
