// Season metadata used by /seasons and the year-scoped library.
// Champions/taglines are the headline; numbers fall back to /stats when live.

export const SEASONS = [
  {
    year: 2024,
    champion: { code: "VER", name: "Max Verstappen", team: "Red Bull" },
    constructor: "McLaren",
    rounds: 24,
    tagline: "Four in a row, then McLaren strikes back.",
    narrative:
      "Verstappen completes the four-peat, but a resurgent McLaren takes the constructors' title for the first time since 1998 - and Lando Norris emerges as the new generation's lead protagonist.",
    icon: "Q",
    accent: "#3671C6",
    headline_race: { name: "Sao Paulo Grand Prix", note: "Verstappen P17 to P1 in the wet" },
  },
  {
    year: 2023,
    champion: { code: "VER", name: "Max Verstappen", team: "Red Bull" },
    constructor: "Red Bull",
    rounds: 22,
    tagline: "Total dominance. 19 wins. 22 races.",
    narrative:
      "Verstappen and Red Bull post the most lopsided season in F1 history - 19 of 22 wins for the Dutchman. The What-If Lab gets a serious workout asking: who could have stopped him?",
    icon: "T",
    accent: "#e8002d",
    headline_race: { name: "Singapore Grand Prix", note: "The only race Red Bull didn't win" },
  },
  {
    year: 2022,
    champion: { code: "VER", name: "Max Verstappen", team: "Red Bull" },
    constructor: "Red Bull",
    rounds: 22,
    tagline: "Ground effect returns. A dynasty begins.",
    narrative:
      "The biggest regulation overhaul in a generation. Ferrari leads early but Red Bull's reliability and strategy machine claim both titles. Hamilton goes winless for the first time since his debut.",
    icon: "G",
    accent: "#dc0000",
    headline_race: { name: "Monaco Grand Prix", note: "Ferrari's strategy gift to Perez" },
  },
  {
    year: 2021,
    champion: { code: "VER", name: "Max Verstappen", team: "Red Bull" },
    constructor: "Mercedes",
    rounds: 22,
    tagline: "The closest title fight of the century.",
    narrative:
      "Hamilton and Verstappen separated by a single point going into the finale. The safety car at Abu Dhabi changes everything. This is the season the Glory Path was built for.",
    icon: "VS",
    accent: "#ffd24a",
    headline_race: { name: "Abu Dhabi Grand Prix", note: "One lap that rewrote the championship" },
  },
  {
    year: 2020,
    champion: { code: "HAM", name: "Lewis Hamilton", team: "Mercedes" },
    constructor: "Mercedes",
    rounds: 17,
    tagline: "The pandemic season nobody saw coming.",
    narrative:
      "A truncated, geographically chaotic calendar. Hamilton equals Schumacher's record of seven titles. New venues (Mugello, Imola, Portimao) return. Russell almost wins at Sakhir.",
    icon: "VII",
    accent: "#00d2be",
    headline_race: { name: "Sakhir Grand Prix", note: "Russell takes Hamilton's seat - and almost wins" },
  },
  {
    year: 2019,
    champion: { code: "HAM", name: "Lewis Hamilton", team: "Mercedes" },
    constructor: "Mercedes",
    rounds: 21,
    tagline: "The last of the Mercedes dynasty.",
    narrative:
      "Mercedes' sixth consecutive double; the final season before the world stopped. Leclerc emerges at Ferrari, Verstappen wins three times for Red Bull, and Hamilton wins eleven.",
    icon: "VI",
    accent: "#00d2be",
    headline_race: { name: "German Grand Prix", note: "Hamilton's worst race. Verstappen wins from the wet." },
  },
];

export function findSeason(year) {
  return SEASONS.find((s) => s.year === Number(year));
}
