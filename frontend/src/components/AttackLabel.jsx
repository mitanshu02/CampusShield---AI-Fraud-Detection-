//AttackLabel.jsx

const HIDE_VALUES = [
  "safe",
  "no attack",
  "no threat detected",
  "unknown",
  "none",
]

const HIGH_SEVERITY = [
  "fee portal impersonation",
  "upi collect fraud",
  "visual phishing",
  "semester timing phish",
  "exam result phish",
  "phishing attempt",
  "domain spoofing",
  "scholarship scam",
]

export default function AttackLabel({ attackType }) {
  if (!attackType) return null
  if (HIDE_VALUES.includes(attackType.toLowerCase().trim())) return null

  const isHigh = HIGH_SEVERITY.some((p) =>
    attackType.toLowerCase().includes(p)
  )

  const colour = isHigh
    ? "bg-red-950/50 border-red-700 text-red-300"
    : "bg-amber-950/50 border-amber-700 text-amber-300"

  const dot = isHigh ? "bg-red-500" : "bg-amber-400"

  return (
    <div className="flex items-center gap-2">
      <span className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-semibold ${colour}`}>
        <span className={`w-2 h-2 rounded-full ${dot}`} />
        {attackType}
      </span>
    </div>
  )
}
