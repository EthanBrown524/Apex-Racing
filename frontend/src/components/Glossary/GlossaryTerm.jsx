const GLOSSARY = {
  undercut: "Pitting one lap earlier than a rival to use fresh tyres for a fast out-lap and emerge ahead.",
  overcut: "Pitting later than a rival, staying out on old tyres while they lose time on cold new ones.",
  drs: "Drag Reduction System - a movable rear-wing flap that opens in designated zones when within 1.0s of the car ahead.",
  vsc: "Virtual Safety Car - drivers must hold a delta time, allowing track marshals to clear debris without bunching the field.",
  sc: "Safety Car - bunches the field at reduced speed behind a lead car. Free 12-15s pit windows for those who hadn't stopped.",
  pole: "Pole position - the front-row grid slot, awarded for the fastest qualifying lap.",
  delta: "Lap-time difference between two stints, drivers, or compounds.",
  stint: "The set of laps between two pit stops on the same set of tyres.",
  "dirty air": "Turbulent airflow trailing a car ahead, which costs aero load and tyre temperature for the chaser.",
};

export default function GlossaryTerm({ term, children }) {
  const key = term?.toLowerCase();
  const def = GLOSSARY[key];
  if (!def) return <>{children ?? term}</>;
  return (
    <span className="gloss" tabIndex={0} aria-label={`${term}: ${def}`}>
      <span className="gloss-underline">{children ?? term}</span>
      <span className="gloss-tooltip" role="tooltip">
        <strong>{term}</strong>
        <span>{def}</span>
      </span>
    </span>
  );
}
