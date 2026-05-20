const ACTION_LABELS = {
  pit: "Pit now",
  stay_out: "Stay out",
  retire: "Retire",
  push: "Push",
  manage: "Manage",
};

const ACTION_TONES = {
  pit: "warn",
  stay_out: "neutral",
  retire: "bad",
  push: "ok",
  manage: "neutral",
};

export default function RaceDirectorNotes({ data }) {
  if (!data) return null;
  const plans = data.plans ?? [];
  const expanded = data.expanded_changes ?? [];

  if (!plans.length && !expanded.length) {
    return (
      <div className="director-panel">
        <div className="director-title">Race Director</div>
        <div className="director-empty">
          AI Race Director ran but produced no strategic responses (Granite may
          be in fallback mode, or the trigger didn't warrant a chain reaction).
        </div>
      </div>
    );
  }

  return (
    <div className="director-panel">
      <div className="director-title">
        Race Director <span className="director-badge">GRANITE</span>
      </div>
      {plans.map((plan, planIndex) => (
        <div className="director-plan" key={planIndex}>
          <div className="director-plan-trigger">{plan.trigger_summary}</div>
          {plan.narrative && (
            <div className="director-plan-narrative">{plan.narrative}</div>
          )}
          {plan.decisions?.length > 0 && (
            <ol className="director-decisions">
              {plan.decisions.map((d, i) => (
                <li key={i} className={`director-decision tone-${ACTION_TONES[d.action] ?? "neutral"}`}>
                  <div className="director-decision-head">
                    <span className="director-driver">{d.driver_code}</span>
                    <span className="director-action">
                      {ACTION_LABELS[d.action] ?? d.action}
                    </span>
                    <span className="director-lap">L{d.lap}</span>
                    <span className="director-confidence" title="AI confidence">
                      {Math.round((d.confidence ?? 0.5) * 100)}%
                    </span>
                  </div>
                  {d.rationale && (
                    <div className="director-rationale">{d.rationale}</div>
                  )}
                </li>
              ))}
            </ol>
          )}
        </div>
      ))}
      {expanded.length > 0 && (
        <div className="director-footer">
          <span className="director-footer-label">Engine changes added</span>
          <span className="director-footer-count">+{expanded.length}</span>
        </div>
      )}
    </div>
  );
}
