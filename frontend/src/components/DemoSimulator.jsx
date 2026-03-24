//DemoSimulator.jsx

const SCENARIOS = [
  {
    label: "Fake fee portal",
    badge: "HIGH RISK",
    badgeColor: "red",
    url: "https://fees-nitbhopal-edu.in/pay",
    description: "Typosquatted college fee portal registered 2 days ago",
  },
  {
  label: "UPI collect fraud",
  badge: "HIGH RISK",
  badgeColor: "red",
  url: "http://localhost:8080/fake_college_page.html",
  description: "Fake payment portal harvesting UPI PIN — live demo page",
  },
  {
    label: "Fake scholarship",
    badge: "MEDIUM RISK",
    badgeColor: "amber",
    url: "https://scholarship-gov-india.in/apply",
    description: "Government scholarship impersonation collecting Aadhaar",
  },
  {
    label: "Safe — official site",
    badge: "SAFE",
    badgeColor: "green",
    url: "https://www.nitbhopal.ac.in",
    description: "Verified official college domain",
  },
  {
    label: "Exam result phish",
    badge: "HIGH RISK",
    badgeColor: "red",
    url: "https://results-nitp-ac-in.com/btech",
    description: "Fake exam result portal stealing login credentials",
  },
];

const badgeStyles = {
  red: "bg-red-900/60 text-red-300 border-red-700",
  amber: "bg-amber-900/60 text-amber-300 border-amber-700",
  green: "bg-green-900/60 text-green-300 border-green-700",
};

const cardStyles = {
  red: "border-red-900 bg-red-950/20 hover:bg-red-950/40",
  amber: "border-amber-900 bg-amber-950/20 hover:bg-amber-950/40",
  green: "border-green-900 bg-green-950/20 hover:bg-green-950/40",
};

export default function DemoSimulator({ onSelectScenario, onTriggerScan }) {
  const handleClick = (url) => {
    onSelectScenario(url);
    setTimeout(() => onTriggerScan(url), 100);
  };

  return (
    <div className="rounded-2xl border border-gray-800 bg-gray-900/40 p-5">
      <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-4">
        Demo Simulator — Click any scenario to scan
      </h2>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {SCENARIOS.map((s) => (
          <button
            key={s.url}
            onClick={() => handleClick(s.url)}
            className={`rounded-xl border ${cardStyles[s.badgeColor]} p-4 text-left transition cursor-pointer group`}
          >
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="text-sm font-semibold text-white group-hover:text-blue-300 transition">
                  {s.label}
                </p>
                <p className="text-xs text-gray-500 mt-0.5">{s.description}</p>
              </div>
              <span
                className={`text-xs font-bold px-2 py-0.5 rounded-full border flex-shrink-0 ${badgeStyles[s.badgeColor]}`}
              >
                {s.badge}
              </span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
