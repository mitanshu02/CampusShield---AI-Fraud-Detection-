// frontend/src/components/HeatmapViewer.jsx

import { useState } from "react"

const BASE = "http://localhost:8000"

function VisualNotTriggered() {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="rounded-2xl border border-gray-800 bg-gray-900/40 p-5
                    animate-fadeInUp">
      <h2 className="text-sm font-semibold text-gray-400 uppercase
                     tracking-widest mb-4">
        Visual Brand Spoofing Analysis
      </h2>

      <div className="flex items-start gap-4 mb-4">
        <div className="w-12 h-12 rounded-xl bg-gray-800 border border-gray-700
                        flex items-center justify-center flex-shrink-0">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none"
               className="text-gray-500">
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"
                  stroke="currentColor" strokeWidth="1.5"
                  strokeLinecap="round"/>
            <circle cx="12" cy="12" r="3" stroke="currentColor"
                    strokeWidth="1.5"/>
            <path d="M3 3l18 18" stroke="currentColor" strokeWidth="1.5"
                  strokeLinecap="round"/>
          </svg>
        </div>
        <div className="flex-1">
          <p className="text-sm font-semibold text-gray-300 mb-1">
            Visual scan not triggered for this URL
          </p>
          <p className="text-xs text-gray-500 leading-relaxed">
            Visual brand comparison only activates when a URL is detected
            as potentially impersonating a known brand or institution.
            This URL passed the typosquatting check cleanly.
          </p>
        </div>
      </div>

      {/* How it works explainer */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-4 py-3
                   bg-gray-800/60 hover:bg-gray-800 rounded-xl border
                   border-gray-700 transition-all duration-200 group"
      >
        <span className="text-xs font-medium text-gray-400
                         group-hover:text-white transition-colors">
          How does visual brand spoofing detection work?
        </span>
        <svg
          width="14" height="14" viewBox="0 0 24 24" fill="none"
          className={`text-gray-500 transition-transform duration-200
                      ${expanded ? "rotate-180" : ""}`}
        >
          <path d="M6 9l6 6 6-6" stroke="currentColor" strokeWidth="2"
                strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </button>

      {expanded && (
        <div className="mt-3 space-y-3 animate-fadeInUp">

          {/* Step by step */}
          {[
            {
              num: "1",
              color: "bg-indigo-500/20 border-indigo-500/40 text-indigo-400",
              title: "Typosquatting trigger",
              desc: "When a URL closely resembles a known institution's domain — for example fees-nitbhopal-edu.in vs nitbhopal.ac.in — visual analysis is triggered automatically."
            },
            {
              num: "2",
              color: "bg-purple-500/20 border-purple-500/40 text-purple-400",
              title: "Screenshot capture",
              desc: "CampusShield uses a headless browser to capture a pixel-perfect 1280×720 screenshot of the suspicious page, hiding cookie banners and popups for a clean comparison."
            },
            {
              num: "3",
              color: "bg-blue-500/20 border-blue-500/40 text-blue-400",
              title: "Perceptual hash comparison",
              desc: "The screenshot is compared against stored templates of known brands using perceptual hashing — detecting visual similarity even when HTML is completely different."
            },
            {
              num: "4",
              color: "bg-red-500/20 border-red-500/40 text-red-400",
              title: "OpenCV heatmap generation",
              desc: "When similarity exceeds 60%, OpenCV performs a pixel-level diff and highlights tampered regions in red — showing judges exactly where a scammer modified the real page."
            },
          ].map((step, i) => (
            <div key={i}
                 className="flex gap-3 p-3 bg-gray-800/40 rounded-xl
                            border border-gray-700/50">
              <div className={`w-7 h-7 rounded-lg border flex items-center
                               justify-center flex-shrink-0 text-xs font-bold
                               ${step.color}`}>
                {step.num}
              </div>
              <div>
                <p className="text-xs font-semibold text-gray-300 mb-0.5">
                  {step.title}
                </p>
                <p className="text-xs text-gray-500 leading-relaxed">
                  {step.desc}
                </p>
              </div>
            </div>
          ))}

          {/* Demo hint */}
          <div className="flex items-center gap-2 px-3 py-2.5 bg-indigo-500/10
                          border border-indigo-500/20 rounded-xl">
            <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full
                            animate-pulse flex-shrink-0"/>
            <p className="text-xs text-indigo-400">
              Try scanning a typosquatted URL like{" "}
              <span className="font-mono font-semibold">
                fees-nitbhopal-edu.in
              </span>{" "}
              to see the heatmap in action.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

export default function HeatmapViewer({ visualScan }) {
  const [activePanel, setActivePanel] = useState("heatmap")

  // visual scan not triggered — show educational explainer
  if (!visualScan || !visualScan.available) {
    return <VisualNotTriggered />
  }

  // visual scan ran but no brand match found
  if (!visualScan.heatmap_url) {
    return (
      <div className="rounded-2xl border border-gray-800 bg-gray-900/40
                      p-5 animate-fadeInUp">
        <h2 className="text-sm font-semibold text-gray-400 uppercase
                       tracking-widest mb-4">
          Visual Brand Spoofing Analysis
        </h2>
        <div className="flex items-center gap-3 py-3">
          <div className="w-8 h-8 rounded-lg bg-green-500/10 border
                          border-green-500/30 flex items-center
                          justify-center flex-shrink-0">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
                 className="text-green-400">
              <path d="M5 13l4 4L19 7" stroke="currentColor"
                    strokeWidth="2" strokeLinecap="round"
                    strokeLinejoin="round"/>
            </svg>
          </div>
          <div>
            <p className="text-sm text-green-400 font-medium">
              No visual brand impersonation detected
            </p>
            <p className="text-xs text-gray-600 mt-0.5">
              Similarity score: {visualScan.visual_similarity}% —
              below threshold for brand impersonation.
            </p>
          </div>
        </div>
      </div>
    )
  }

  // full heatmap display
  const similarity = visualScan.visual_similarity
  const brand      = visualScan.detected_brand
  const isHighRisk = similarity >= 80
  const isMedRisk  = similarity >= 65 && similarity < 80

  const riskColor = isHighRisk ? {
    badge:  "bg-red-950/50 border-red-700 text-red-300",
    border: "border-red-800/60",
    bg:     "bg-red-950/20",
    bar:    "bg-red-500",
    dot:    "bg-red-400",
  } : isMedRisk ? {
    badge:  "bg-amber-950/50 border-amber-700 text-amber-300",
    border: "border-amber-800/60",
    bg:     "bg-amber-950/20",
    bar:    "bg-amber-500",
    dot:    "bg-amber-400",
  } : {
    badge:  "bg-gray-800 border-gray-700 text-gray-300",
    border: "border-gray-700",
    bg:     "bg-gray-900/40",
    bar:    "bg-gray-500",
    dot:    "bg-gray-400",
  }

  const panels = [
    { id: "heatmap",    label: "Heatmap",    url: visualScan.heatmap_url    },
    { id: "suspicious", label: "Suspicious", url: visualScan.suspicious_url },
    { id: "real",       label: "Real page",  url: visualScan.template_url   },
  ].filter(p => p.url)

  return (
    <div className={`rounded-2xl border ${riskColor.border}
                     ${riskColor.bg} p-5 animate-fadeInUp`}>

      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${riskColor.dot}
                           animate-pulse`}/>
          <h2 className="text-sm font-semibold text-gray-300 uppercase
                         tracking-widest">
            Visual Brand Spoofing Analysis
          </h2>
        </div>
        <span className={`text-xs font-bold px-2.5 py-1 rounded-full
                          border ${riskColor.badge}`}>
          {similarity}% match{brand ? ` to ${brand}` : ""}
        </span>
      </div>

      {/* Similarity bar */}
      <div className="mb-5">
        <div className="flex justify-between text-xs text-gray-500 mb-1.5">
          <span>Visual similarity to known brand</span>
          <span className={isHighRisk ? "text-red-400" :
                           isMedRisk  ? "text-amber-400" : "text-gray-400"}>
            {similarity}%
          </span>
        </div>
        <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
          <div
            className={`h-full ${riskColor.bar} rounded-full
                        transition-all duration-1000 ease-out`}
            style={{ width: `${similarity}%` }}
          />
        </div>
      </div>

      {/* Panel switcher */}
      {panels.length > 1 && (
        <div className="flex gap-1 p-1 bg-gray-900/60 rounded-xl
                        border border-gray-800 mb-4">
          {panels.map(panel => (
            <button
              key={panel.id}
              onClick={() => setActivePanel(panel.id)}
              className={`flex-1 py-2 px-3 rounded-lg text-xs font-medium
                          transition-all duration-200
                          ${activePanel === panel.id
                            ? "bg-indigo-600 text-white"
                            : "text-gray-400 hover:text-white hover:bg-gray-800"
                          }`}
            >
              {panel.label}
            </button>
          ))}
        </div>
      )}

      {/* Image display */}
      {panels.map(panel =>
        activePanel === panel.id ? (
          <div key={panel.id}
               className="rounded-xl overflow-hidden border border-gray-700
                          animate-fadeIn">
            <div className="flex items-center justify-between px-3 py-2
                            bg-gray-800/80 border-b border-gray-700">
              <span className="text-xs text-gray-400 font-medium">
                {panel.id === "heatmap"    &&
                  "Difference heatmap — red zones = tampered regions"}
                {panel.id === "suspicious" &&
                  "Suspicious page — what the user sees"}
                {panel.id === "real"       &&
                  `Real ${brand} page — the legitimate original`}
              </span>
              {panel.id === "heatmap" && visualScan.diff_percentage && (
                <span className="text-xs text-red-400 font-medium">
                  {visualScan.diff_percentage}% pixels differ
                </span>
              )}
            </div>
            <img
              src={`${BASE}${panel.url}`}
              alt={panel.label}
              className="w-full object-cover"
              style={{ maxHeight: "400px" }}
            />
          </div>
        ) : null
      )}

      {/* Three panel thumbnails */}
      {panels.length > 1 && (
        <div className="mt-4 grid grid-cols-3 gap-2">
          {panels.map(panel => (
            <button
              key={panel.id}
              onClick={() => setActivePanel(panel.id)}
              className={`rounded-lg overflow-hidden border transition-all
                          duration-200 cursor-pointer
                          ${activePanel === panel.id
                            ? "border-indigo-500 ring-1 ring-indigo-500/50"
                            : "border-gray-700 hover:border-gray-600"
                          }`}
            >
              <img
                src={`${BASE}${panel.url}`}
                alt={panel.label}
                className="w-full object-cover"
                style={{ height: "60px" }}
              />
              <div className="py-1 px-2 bg-gray-900 text-center">
                <span className="text-xs text-gray-500">{panel.label}</span>
              </div>
            </button>
          ))}
        </div>
      )}

      <p className="text-xs text-gray-600 mt-3 text-center">
        Red zones show where this page differs from the legitimate brand page
      </p>
    </div>
  )
}