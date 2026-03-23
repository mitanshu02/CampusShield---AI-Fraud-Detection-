// frontend/src/components/RiskMeter.jsx

import { useEffect, useState } from "react";

export default function RiskMeter({ score, colour, label }) {
  const [displayed, setDisplayed] = useState(0);

  useEffect(() => {
    setDisplayed(0);
    let current = 0;
    const step = Math.ceil(score / 40);
    const timer = setInterval(() => {
      current += step;
      if (current >= score) {
        setDisplayed(score);
        clearInterval(timer);
      } else {
        setDisplayed(current);
      }
    }, 30);
    return () => clearInterval(timer);
  }, [score]);

  const c = {
    red: {
      bar: "bg-red-500",
      text: "text-red-400",
      border: "border-red-700",
      bg: "bg-red-950/40",
    },
    amber: {
      bar: "bg-amber-400",
      text: "text-amber-400",
      border: "border-amber-700",
      bg: "bg-amber-950/40",
    },
    green: {
      bar: "bg-green-500",
      text: "text-green-400",
      border: "border-green-700",
      bg: "bg-green-950/40",
    },
  }[colour] || {
    bar: "bg-green-500",
    text: "text-green-400",
    border: "border-green-700",
    bg: "bg-green-950/40",
  };

  return (
    <div className={`rounded-2xl border ${c.border} ${c.bg} p-6`}>
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm font-medium text-gray-300">Risk Score</span>
        <span
          className={`text-xs font-bold px-2.5 py-1 rounded-full border ${c.border} ${c.text}`}
        >
          {label}
        </span>
      </div>

      <div className={`text-7xl font-black tracking-tighter ${c.text} mb-4`}>
        {displayed}
        <span className="text-2xl text-gray-500 font-normal">/100</span>
      </div>

      <div className="h-3 bg-gray-800 rounded-full overflow-hidden">
        <div
          className={`h-full ${c.bar} rounded-full transition-all duration-700 ease-out`}
          style={{ width: `${displayed}%` }}
        />
      </div>

      <p className="text-xs text-gray-500 mt-2">
        {score >= 70
          ? "High risk — do not enter any personal or payment information"
          : score >= 40
            ? "Moderate risk — proceed with caution"
            : "Low risk — no significant threats detected"}
      </p>
    </div>
  );
}
