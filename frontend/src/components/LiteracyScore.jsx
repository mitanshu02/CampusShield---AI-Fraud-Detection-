// frontend/src/components/LiteracyScore.jsx

import { useEffect, useState } from "react"

const KEYS = {
  scamsCaught:        "cs_scams_caught",
  attackTypesLearned: "cs_attack_types",
  totalScans:         "cs_total_scans",
}

export function updateLiteracyScore(riskScore, attackType) {
  const total = parseInt(localStorage.getItem(KEYS.totalScans) || "0")
  localStorage.setItem(KEYS.totalScans, total + 1)

  if (riskScore >= 70) {
    const caught = parseInt(localStorage.getItem(KEYS.scamsCaught) || "0")
    localStorage.setItem(KEYS.scamsCaught, caught + 1)

    if (attackType &&
        attackType !== "No threat detected" &&
        attackType !== "Unknown") {
      const existing = JSON.parse(
        localStorage.getItem(KEYS.attackTypesLearned) || "[]"
      )
      if (!existing.includes(attackType)) {
        existing.push(attackType)
        localStorage.setItem(KEYS.attackTypesLearned, JSON.stringify(existing))
      }
    }
  }

  // dispatch storage event so LiteracyScore component re-reads instantly
  window.dispatchEvent(new Event("storage"))
}

export default function LiteracyScore() {
  const [scores, setScores] = useState({
    scamsCaught:        0,
    attackTypesLearned: 0,
    totalScans:         0,
  })

  const readScores = () => {
    setScores({
      scamsCaught: parseInt(localStorage.getItem(KEYS.scamsCaught) || "0"),
      attackTypesLearned: JSON.parse(
        localStorage.getItem(KEYS.attackTypesLearned) || "[]"
      ).length,
      totalScans: parseInt(localStorage.getItem(KEYS.totalScans) || "0"),
    })
  }

  useEffect(() => {
    readScores()
    window.addEventListener("storage", readScores)
    return () => window.removeEventListener("storage", readScores)
  }, [])

  const stats = [
    { value: scores.scamsCaught,        label: "Scams caught"         },
    { value: scores.attackTypesLearned, label: "Attack types learned" },
    { value: scores.totalScans,         label: "Total scans"          },
  ]

  return (
    <div className="rounded-2xl border border-gray-800 bg-gray-900/40 p-5">
      <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-4">
        Your Security Literacy
      </h2>
      <div className="grid grid-cols-3 gap-3">
        {stats.map((s) => (
          <div
            key={s.label}
            className="bg-gray-800/50 rounded-xl p-4 text-center border border-gray-700"
          >
            <p className="text-3xl font-black text-white">{s.value}</p>
            <p className="text-xs text-gray-400 mt-1 leading-tight">{s.label}</p>
          </div>
        ))}
      </div>
    </div>
  )
}