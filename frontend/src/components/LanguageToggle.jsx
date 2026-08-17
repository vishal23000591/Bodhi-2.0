const OPTIONS = [
  { code: "en", label: "EN" },
  { code: "ta", label: "தமிழ்" },
  { code: "tanglish", label: "Tanglish" },
];

export default function LanguageToggle({ language, onChange }) {
  return (
    <div className="lang-toggle" role="group" aria-label="Answer language">
      {OPTIONS.map((opt) => (
        <button
          key={opt.code}
          type="button"
          className={`lang-toggle-option ${language === opt.code ? "active" : ""}`}
          onClick={() => onChange(opt.code)}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}
