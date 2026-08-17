const LABEL = {
  mastered: "Mastered",
  in_progress: "In Progress",
  needs_reteach: "Needs Reteach",
  not_started: "Not Started",
};

const CLASS = {
  mastered: "badge-mastered",
  in_progress: "badge-in-progress",
  needs_reteach: "badge-needs-reteach",
  not_started: "badge-not-started",
};

export default function MasteryBadge({ status }) {
  const key = status && LABEL[status] ? status : "not_started";
  return <span className={`badge ${CLASS[key]}`}>{LABEL[key]}</span>;
}
