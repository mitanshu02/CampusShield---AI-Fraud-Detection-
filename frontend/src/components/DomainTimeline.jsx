// DomainTimeline.jsx

export default function DomainTimeline({ domainAgeSignal }) {
  if (!domainAgeSignal) return null
  if (!domainAgeSignal.legitimate_domain) return null
  if (domainAgeSignal.legitimate_age_days === null) return null

  if (domainAgeSignal.suspicious_domain === domainAgeSignal.legitimate_domain) return null

  const susAge   = domainAgeSignal.suspicious_age_days
  const legAge   = domainAgeSignal.legitimate_age_days
  const susDomain = domainAgeSignal.suspicious_domain
  const legDomain = domainAgeSignal.legitimate_domain

  const formatAge = (days) => {
    if (days === null || days === undefined) return "Age unknown"
    if (days < 30)  return `${days} days old`
    if (days < 365) return `${Math.floor(days / 30)} months old`
    return `${Math.floor(days / 365)} years old`
  }

  // for bar width — if suspicious age unknown use 1% to show minimal bar
  const susBarWidth = susAge === null ? 1 : Math.max((susAge / (susAge + legAge)) * 100, 2)
  const legBarWidth = susAge === null ? 99 : Math.max((legAge / (susAge + legAge)) * 100, 2)

  return (
    <div className="rounded-2xl border border-gray-800 bg-gray-900/50 p-5">
      <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-4">
        Domain Age Comparison
      </h3>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-xs text-gray-400 mb-1 truncate">{susDomain}</p>
          <p className="text-sm font-bold text-red-400 mb-2">
            {formatAge(susAge)}
          </p>
          <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-red-500 rounded-full"
              style={{ width: `${susBarWidth}%` }}
            />
          </div>
          <p className="text-xs text-red-400 mt-2">⚠ Suspicious domain</p>
        </div>

        <div>
          <p className="text-xs text-gray-400 mb-1 truncate">{legDomain}</p>
          <p className="text-sm font-bold text-green-400 mb-2">
            {formatAge(legAge)}
          </p>
          <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-green-500 rounded-full"
              style={{ width: `${legBarWidth}%` }}
            />
          </div>
          <p className="text-xs text-green-400 mt-2">✓ Legitimate domain</p>
        </div>
      </div>

      <p className="text-xs text-gray-600 mt-4 text-center">
        A legitimate institution's domain is never just a few days old
      </p>
    </div>
  )
}