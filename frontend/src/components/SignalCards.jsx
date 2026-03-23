// frontend/src/components/SignalCards.jsx

export default function SignalCards({ signals }) {
  if (!signals) return null;

  const SIGNAL_KEYS = ["domain_age", "typosquatting", "phishtank", "keywords"];

  const getColour = (score) => {
    if (score >= 70)
      return {
        dot: "bg-red-500",
        border: "border-red-800",
        bg: "bg-red-950/30",
        text: "text-red-300",
      };
    if (score >= 40)
      return {
        dot: "bg-amber-400",
        border: "border-amber-800",
        bg: "bg-amber-950/30",
        text: "text-amber-300",
      };
    return {
      dot: "bg-green-500",
      border: "border-green-800",
      bg: "bg-green-950/30",
      text: "text-green-300",
    };
  };

  return (
    <div>
      <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-widest mb-3">
        Signal Checks
      </h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {SIGNAL_KEYS.map((key) => {
          const sig = signals[key];
          if (!sig) return null;
          const c = getColour(sig.score);

          return (
            <div
              key={key}
              className={`rounded-xl border ${c.border} ${c.bg} p-4 flex gap-3 items-start`}
            >
              {/* Colour dot indicator */}
              <div
                className={`w-2.5 h-2.5 rounded-full mt-1.5 flex-shrink-0 ${c.dot}`}
              />

              <div className="min-w-0">
                {/* Signal name and weight */}
                <div className="flex items-center justify-between gap-2">
                  <p className="text-xs font-semibold text-gray-300">
                    {sig.name}
                  </p>
                  <p className="text-xs text-gray-600">{sig.weight}</p>
                </div>

                {/* Detail text */}
                <p className={`text-xs mt-1 ${c.text}`}>{sig.detail}</p>

                {/* Score */}
                <p className="text-xs text-gray-600 mt-1">
                  Score: {sig.score}/100
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
