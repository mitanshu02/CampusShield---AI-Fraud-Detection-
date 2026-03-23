// frontend/src/components/ExplainerCard.jsx

import AttackLabel from "./AttackLabel";

export default function ExplainerCard({
  explanation,
  impersonationStatement,
  attackType,
  riskScore,
}) {
  if (!explanation) return null;

  const getStyles = () => {
    if (riskScore >= 70)
      return {
        card: "border-red-800 bg-red-950/20",
        header: "bg-red-900/40 border-red-800 text-red-200",
        icon: "🚨",
        title: "Threat detected — here is what it is",
      };
    if (riskScore >= 40)
      return {
        card: "border-amber-800 bg-amber-950/20",
        header: "bg-amber-900/40 border-amber-800 text-amber-200",
        icon: "⚠️",
        title: "Suspicious URL — here is what we found",
      };
    return {
      card: "border-green-800 bg-green-950/20",
      header: "bg-green-900/40 border-green-800 text-green-200",
      icon: "✅",
      title: "This URL appears safe",
    };
  };

  const s = getStyles();

  return (
    <div className={`rounded-2xl border ${s.card} overflow-hidden`}>
      {/* Header */}
      <div className={`px-5 py-3 border-b ${s.header} flex items-center gap-2`}>
        <span>{s.icon}</span>
        <span className="text-sm font-semibold">{s.title}</span>
      </div>

      <div className="p-5 space-y-4">
        {/* Impersonation statement — top, highlighted */}
        {impersonationStatement &&
          impersonationStatement !==
            "No specific impersonation target identified." && (
            <div className="bg-gray-800/60 border border-gray-700 rounded-xl px-4 py-3">
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-1">
                Impersonation Target
              </p>
              <p className="text-sm text-white font-medium leading-relaxed">
                {impersonationStatement}
              </p>
            </div>
          )}

        {/* 3-sentence plain English explanation */}
        <p className="text-sm text-gray-300 leading-relaxed">{explanation}</p>

        {/* Attack type badge */}
        <AttackLabel attackType={attackType} />
      </div>
    </div>
  );
}
