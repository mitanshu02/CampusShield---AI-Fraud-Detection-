// frontend/src/pages/Home.jsx

import { useState, useEffect } from "react"
import { scanURL } from "../services/api"
import URLInput       from "../components/URLInput"
import RiskMeter      from "../components/RiskMeter"
import SignalCards    from "../components/SignalCards"
import DomainTimeline from "../components/DomainTimeline"
import AttackLabel    from "../components/AttackLabel"
import ExplainerCard  from "../components/ExplainerCard"
import DemoSimulator  from "../components/DemoSimulator"
import UPISignals     from "../components/UPISignals"
import HeatmapViewer  from "../components/HeatmapViewer"
import LiteracyScore, { updateLiteracyScore } from "../components/LiteracyScore"

// ── helpers ───────────────────────────────────────────────────────────────────

function getRiskColour(score) {
  if (score >= 70) return "red"
  if (score >= 40) return "amber"
  return "green"
}

const SCAN_STEPS = [
  { id: 1, label: "Checking domain age and WHOIS record..."        },
  { id: 2, label: "Running typosquatting detection..."             },
  { id: 3, label: "Scanning for UPI payment fraud signals..."      },
  { id: 4, label: "Analysing visual brand similarity..."           },
  { id: 5, label: "Generating AI threat explanation..."            },
]

// ── sub-components ────────────────────────────────────────────────────────────

function Navbar({ showDemo, setShowDemo }) {
  return (
    <header className="sticky top-0 z-50 border-b border-gray-800/80
                       bg-gray-950/90 backdrop-blur-md px-6 py-0">
      <div className="max-w-6xl mx-auto flex items-center h-16 gap-4">

        {/* Logo */}
        <div className="flex items-center gap-3 group">
          <div className="relative">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500
                            to-blue-600 flex items-center justify-center
                            shadow-lg shadow-indigo-500/25 group-hover:shadow-indigo-500/40
                            transition-all duration-300 group-hover:scale-105">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                <path d="M12 2L3 7v5c0 5.25 3.75 10.15 9 11.35C17.25 22.15 21
                         17.25 21 12V7L12 2z"
                      fill="white" fillOpacity="0.9"/>
                <path d="M9 12l2 2 4-4" stroke="white" strokeWidth="2"
                      strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <div className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-green-400
                            rounded-full border-2 border-gray-950 animate-pulse"/>
          </div>
          <div>
            <span className="text-base font-bold text-white tracking-tight">
              CampusShield
            </span>
            <div className="text-xs text-indigo-400 font-medium -mt-0.5">
              AI Fraud Intelligence
            </div>
          </div>
        </div>

        {/* Center nav pills */}
        <div className="hidden md:flex items-center gap-1 mx-auto">
          {["URL Scanner", "Payment Guard", "AI Analysis"].map((item, i) => (
            <div key={i}
                 className="px-3 py-1.5 rounded-lg text-xs font-medium
                            text-gray-400 hover:text-white hover:bg-gray-800
                            transition-all duration-200 cursor-default">
              {item}
            </div>
          ))}
        </div>

        {/* Right side */}
        <div className="flex items-center gap-3 ml-auto">
          <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5
                          rounded-lg bg-green-500/10 border border-green-500/20">
            <div className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse"/>
            <span className="text-xs text-green-400 font-medium">Live</span>
          </div>
          <button
            onClick={() => setShowDemo(!showDemo)}
            className={`text-xs font-medium px-4 py-2 rounded-lg border
                        transition-all duration-200
                        ${showDemo
                          ? "bg-indigo-600 border-indigo-500 text-white shadow-lg shadow-indigo-500/25"
                          : "border-gray-700 text-gray-400 hover:border-gray-600 hover:text-white hover:bg-gray-800"
                        }`}
          >
            {showDemo ? "Hide Demo" : "Demo Mode"}
          </button>
        </div>
      </div>
    </header>
  )
}

function ScanProgress({ steps, currentStep }) {
  return (
    <div className="rounded-2xl border border-gray-800 bg-gray-900/60
                    backdrop-blur-sm p-6 animate-fadeIn">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-8 h-8 rounded-lg bg-indigo-500/20 border border-indigo-500/30
                        flex items-center justify-center">
          <div className="w-3 h-3 border-2 border-indigo-400 border-t-transparent
                          rounded-full animate-spin"/>
        </div>
        <div>
          <p className="text-sm font-semibold text-white">Scanning URL...</p>
          <p className="text-xs text-gray-500">Running {steps.length} security checks</p>
        </div>
        <div className="ml-auto text-xs text-gray-500">
          {Math.min(currentStep, steps.length)}/{steps.length}
        </div>
      </div>

      <div className="space-y-3">
        {steps.map((step, i) => {
          const done    = i < currentStep
          const active  = i === currentStep
          const pending = i > currentStep

          return (
            <div key={step.id}
                 className={`flex items-center gap-3 transition-all duration-300
                             ${pending ? "opacity-30" : "opacity-100"}`}>
              <div className={`w-6 h-6 rounded-full flex items-center justify-center
                               flex-shrink-0 transition-all duration-300
                               ${done    ? "bg-green-500/20 border border-green-500/50"  :
                                 active  ? "bg-indigo-500/20 border border-indigo-500/50" :
                                           "bg-gray-800 border border-gray-700"}`}>
                {done ? (
                  <svg className="w-3 h-3 text-green-400 animate-checkmark"
                       fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round"
                          strokeWidth={2.5} d="M5 13l4 4L19 7"/>
                  </svg>
                ) : active ? (
                  <div className="w-2 h-2 bg-indigo-400 rounded-full animate-pulse"/>
                ) : (
                  <div className="w-1.5 h-1.5 bg-gray-600 rounded-full"/>
                )}
              </div>
              <span className={`text-sm transition-colors duration-300
                                ${done   ? "text-green-400" :
                                  active ? "text-indigo-300" :
                                           "text-gray-600"}`}>
                {step.label}
              </span>
              {done && (
                <span className="ml-auto text-xs text-green-500 font-medium">
                  Done
                </span>
              )}
              {active && (
                <span className="ml-auto text-xs text-indigo-400 animate-pulse">
                  Checking...
                </span>
              )}
            </div>
          )
        })}
      </div>

      {/* Progress bar */}
      <div className="mt-5 h-1 bg-gray-800 rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-indigo-500 to-blue-500
                     rounded-full transition-all duration-500 ease-out"
          style={{ width: `${(Math.min(currentStep, steps.length) / steps.length) * 100}%` }}
        />
      </div>
    </div>
  )
}

function VerdictHero({ result }) {
  const score   = result.overall_risk
  const verdict = result.verdict
  const isHigh  = score >= 70
  const isMed   = score >= 40 && score < 70
  const isSafe  = score < 40

  const config = isHigh ? {
    bg:        "bg-red-950/40",
    border:    "border-red-800/60",
    glow:      "animate-glow-red",
    iconBg:    "bg-red-500/20 border-red-500/40",
    iconColor: "text-red-400",
    title:     "HIGH RISK — Do not proceed",
    titleColor:"text-red-300",
    subColor:  "text-red-400/80",
    scoreColor:"text-red-400",
    barColor:  "bg-red-500",
  } : isMed ? {
    bg:        "bg-amber-950/40",
    border:    "border-amber-800/60",
    glow:      "",
    iconBg:    "bg-amber-500/20 border-amber-500/40",
    iconColor: "text-amber-400",
    title:     "MEDIUM RISK — Proceed with caution",
    titleColor:"text-amber-300",
    subColor:  "text-amber-400/80",
    scoreColor:"text-amber-400",
    barColor:  "bg-amber-500",
  } : {
    bg:        "bg-green-950/40",
    border:    "border-green-800/60",
    glow:      "animate-glow-green",
    iconBg:    "bg-green-500/20 border-green-500/40",
    iconColor: "text-green-400",
    title:     "SAFE — This URL is legitimate",
    titleColor:"text-green-300",
    subColor:  "text-green-400/80",
    scoreColor:"text-green-400",
    barColor:  "bg-green-500",
  }

  return (
    <div className={`rounded-2xl border ${config.border} ${config.bg}
                     ${config.glow} p-6 animate-fadeInUp`}>
      <div className="flex items-center gap-4">

        {/* Shield icon */}
        <div className={`w-14 h-14 rounded-2xl border ${config.iconBg}
                         flex items-center justify-center flex-shrink-0
                         animate-float`}>
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none"
               className={config.iconColor}>
            {isHigh ? (
              <>
                <path d="M12 2L3 7v5c0 5.25 3.75 10.15 9 11.35C17.25 22.15
                         21 17.25 21 12V7L12 2z"
                      fill="currentColor" fillOpacity="0.2"
                      stroke="currentColor" strokeWidth="1.5"/>
                <path d="M12 8v4M12 16h.01"
                      stroke="currentColor" strokeWidth="2"
                      strokeLinecap="round"/>
              </>
            ) : isSafe ? (
              <>
                <path d="M12 2L3 7v5c0 5.25 3.75 10.15 9 11.35C17.25 22.15
                         21 17.25 21 12V7L12 2z"
                      fill="currentColor" fillOpacity="0.2"
                      stroke="currentColor" strokeWidth="1.5"/>
                <path d="M9 12l2 2 4-4"
                      stroke="currentColor" strokeWidth="2"
                      strokeLinecap="round" strokeLinejoin="round"/>
              </>
            ) : (
              <>
                <path d="M12 2L3 7v5c0 5.25 3.75 10.15 9 11.35C17.25 22.15
                         21 17.25 21 12V7L12 2z"
                      fill="currentColor" fillOpacity="0.2"
                      stroke="currentColor" strokeWidth="1.5"/>
                <path d="M12 8v4M12 16h.01"
                      stroke="currentColor" strokeWidth="2"
                      strokeLinecap="round"/>
              </>
            )}
          </svg>
        </div>

        {/* Text */}
        <div className="flex-1 min-w-0">
          <h2 className={`text-lg font-bold ${config.titleColor} leading-tight`}>
            {config.title}
          </h2>
          <p className={`text-sm mt-1 ${config.subColor} truncate`}>
            {result.impersonation_statement &&
             result.impersonation_statement !== "No specific impersonation target identified."
              ? result.impersonation_statement
              : `Scanned ${result.url}`}
          </p>
          {result.attack_type &&
           !["no threat detected","unknown","safe","no attack","none"]
             .includes(result.attack_type.toLowerCase().trim()) && (
            <div className="mt-2">
              <AttackLabel attackType={result.attack_type} />
            </div>
          )}
        </div>

        {/* Score circle */}
        <div className="flex-shrink-0 text-center">
          <div className={`text-5xl font-black ${config.scoreColor}
                           leading-none tabular-nums`}>
            {score}
          </div>
          <div className="text-xs text-gray-500 mt-1">/ 100</div>
          <div className="mt-2 w-16 h-1.5 bg-gray-800 rounded-full overflow-hidden mx-auto">
            <div className={`h-full ${config.barColor} rounded-full
                             transition-all duration-1000 ease-out`}
                 style={{ width: `${score}%` }}/>
          </div>
        </div>
      </div>
    </div>
  )
}

function ResultTabs({ result }) {
  const [activeTab, setActiveTab] = useState("url")

  const tabs = [
     { id: "url",     label: "URL Analysis",   icon: "🔍" },
     { id: "payment", label: "Payment Check",  icon: "💳" },
     { id: "visual",  label: "Visual Check",   icon: "👁" },
     { id: "verdict", label: "AI Verdict",     icon: "🤖" },
  ]
  // const tabs = [
  //   { id: "url",     label: "URL Analysis",   icon: "🔍" },
  //   { id: "payment", label: "Payment Check",  icon: "💳" },
  //   { id: "verdict", label: "AI Verdict",     icon: "🤖" },
  // ]

  return (
    <div className="animate-fadeInUp" style={{ animationDelay: "0.2s" }}>
      {/* Tab bar */}
      <div className="flex gap-1 p-1 bg-gray-900 rounded-xl border
                      border-gray-800 mb-4">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 flex items-center justify-center gap-2
                        px-4 py-2.5 rounded-lg text-sm font-medium
                        transition-all duration-200
                        ${activeTab === tab.id
                          ? "bg-indigo-600 text-white shadow-lg shadow-indigo-500/25"
                          : "text-gray-400 hover:text-white hover:bg-gray-800"
                        }`}
          >
            <span style={{ fontSize: "14px" }}>{tab.icon}</span>
            <span className="hidden sm:inline">{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div key={activeTab} className="animate-fadeInUp space-y-4">
        {activeTab === "url" && (
          <>
            <DomainTimeline
              domainAgeSignal={result.url_scan?.signals?.domain_age}
            />
            <SignalCards signals={result.url_scan?.signals} />
          </>
        )}

        {activeTab === "payment" && (
          <UPISignals paymentScan={result.payment_scan} />
        )}

        {activeTab === "visual" && (
          <HeatmapViewer visualScan={result.visual_scan} />
        )}

        {activeTab === "verdict" && (
          <ExplainerCard
            explanation={result.explanation}
            impersonationStatement={result.impersonation_statement}
            attackType={result.attack_type}
            riskScore={result.overall_risk}
          />
        )}
        {/* {activeTab === "url" && (
          <>
            <DomainTimeline
              domainAgeSignal={result.url_scan?.signals?.domain_age}
            />
            <SignalCards signals={result.url_scan?.signals} />
          </>
        )}

        {activeTab === "payment" && (
          <UPISignals paymentScan={result.payment_scan} />
        )}

        {activeTab === "verdict" && (
          <>
            <HeatmapViewer visualScan={result.visual_scan} />
            <ExplainerCard
              explanation={result.explanation}
              impersonationStatement={result.impersonation_statement}
              attackType={result.attack_type}
              riskScore={result.overall_risk}
            />
          </>
        )} */}
      </div>
    </div>
  )
}

// ── main component ────────────────────────────────────────────────────────────

export default function Home() {
  const [url,         setUrl]         = useState("")
  const [loading,     setLoading]     = useState(false)
  const [scanStep,    setScanStep]    = useState(-1)
  const [result,      setResult]      = useState(null)
  const [error,       setError]       = useState(null)
  const [showDemo,    setShowDemo]    = useState(false)

  // animate scan steps while loading
  useEffect(() => {
    if (!loading) { setScanStep(-1); return }
    setScanStep(0)
    const timers = SCAN_STEPS.map((_, i) =>
      setTimeout(() => setScanStep(i + 1), (i + 1) * 500)
    )
    return () => timers.forEach(clearTimeout)
  }, [loading])
  // useEffect(() => {
  //   if (!loading) { setScanStep(-1); return }
  //   setScanStep(0)
  //   const timers = SCAN_STEPS.map((_, i) =>
  //     setTimeout(() => setScanStep(i + 1), (i + 1) * 600)
  //   )
  //   return () => timers.forEach(clearTimeout)
  // }, [loading])

  const handleScan = async (targetUrl) => {
    const scanTarget = (targetUrl || url).trim()
    if (!scanTarget) return

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const data = await scanURL(scanTarget)
      // small delay so last step animation completes
      setTimeout(() => {
        setResult(data)
        setLoading(false)
        updateLiteracyScore(data.overall_risk, data.attack_type)
      }, 400)
    } catch (e) {
      setError("Scan failed — make sure the backend is running on port 8000.")
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">

      {/* Subtle background grid */}
      <div className="fixed inset-0 pointer-events-none"
           style={{
             backgroundImage: `radial-gradient(circle at 1px 1px,
               rgba(255,255,255,0.03) 1px, transparent 0)`,
             backgroundSize: "32px 32px"
           }}/>

      <Navbar showDemo={showDemo} setShowDemo={setShowDemo} />

      <main className="relative max-w-3xl mx-auto px-4 py-12 space-y-8">

        {/* Hero text */}
        <div className="text-center space-y-3 animate-fadeInUp">
          <div className="inline-flex items-center gap-2 px-3 py-1.5
                          rounded-full border border-indigo-500/30
                          bg-indigo-500/10 text-indigo-400 text-xs font-medium
                          mb-2">
            <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-pulse"/>
            Powered by AI — Free to use
          </div>
          <h1 className="text-4xl font-black tracking-tight bg-gradient-to-br
                         from-white to-gray-400 bg-clip-text text-transparent">
            Is this URL safe?
          </h1>
          <p className="text-gray-400 text-sm max-w-md mx-auto leading-relaxed">
            Paste any URL to instantly check for phishing, typosquatting,
            and UPI payment fraud — powered by AI.
          </p>
        </div>

        {/* Demo simulator */}
        {showDemo && (
          <div className="animate-fadeInUp">
            <DemoSimulator
              onSelectScenario={(scenarioUrl) => setUrl(scenarioUrl)}
              onTriggerScan={(scenarioUrl)    => handleScan(scenarioUrl)}
            />
          </div>
        )}

        {/* URL input */}
        <div className="animate-fadeInUp delay-100">
          <URLInput
            url={url}
            setUrl={setUrl}
            onScan={() => handleScan()}
            loading={loading}
          />
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-900/30 border border-red-700 rounded-xl
                          p-4 text-red-300 text-sm animate-fadeInUp">
            {error}
          </div>
        )}

        {/* Scan progress animation */}
        {loading && (
          <ScanProgress steps={SCAN_STEPS} currentStep={scanStep} />
        )}

        {/* Results */}
        {result && !loading && (
          <div className="space-y-5">
            <VerdictHero result={result} />
            <ResultTabs  result={result} />
            <div className="animate-fadeInUp" style={{ animationDelay: "0.4s" }}>
              <LiteracyScore />
            </div>
          </div>
        )}

        {/* Empty state */}
        {!result && !loading && !error && (
          <div className="text-center py-16 animate-fadeIn">
            <div className="w-16 h-16 rounded-2xl bg-gray-900 border
                            border-gray-800 flex items-center justify-center
                            mx-auto mb-4 animate-float">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none"
                   className="text-gray-600">
                <path d="M12 2L3 7v5c0 5.25 3.75 10.15 9 11.35C17.25 22.15
                         21 17.25 21 12V7L12 2z"
                      fill="currentColor" fillOpacity="0.3"
                      stroke="currentColor" strokeWidth="1.5"/>
                <path d="M9 12l2 2 4-4"
                      stroke="currentColor" strokeWidth="2"
                      strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <p className="text-gray-600 text-sm">
              Paste a URL above to begin scanning
            </p>
            <p className="text-gray-700 text-xs mt-1">
              Checks domain age · typosquatting · UPI fraud · AI analysis
            </p>
          </div>
        )}

      </main>
    </div>
  )
}

// // frontend/src/pages/Home.jsx

// import { useState }    from "react"
// import { scanURL }     from "../services/api"
// import URLInput        from "../components/URLInput"
// import RiskMeter       from "../components/RiskMeter"
// import SignalCards     from "../components/SignalCards"
// import DomainTimeline  from "../components/DomainTimeline"
// import AttackLabel     from "../components/AttackLabel"
// import ExplainerCard   from "../components/ExplainerCard"
// import DemoSimulator   from "../components/DemoSimulator"
// import UPISignals      from "../components/UPISignals"
// import HeatmapViewer   from "../components/HeatmapViewer"
// import LiteracyScore, { updateLiteracyScore } from "../components/LiteracyScore"

// function getRiskColour(score) {
//   if (score >= 70) return "red"
//   if (score >= 40) return "amber"
//   return "green"
// }

// export default function Home() {
//   const [url,      setUrl]      = useState("")
//   const [loading,  setLoading]  = useState(false)
//   const [result,   setResult]   = useState(null)
//   const [error,    setError]    = useState(null)
//   const [showDemo, setShowDemo] = useState(false)

//   const handleScan = async (targetUrl) => {
//     const scanTarget = (targetUrl || url).trim()
//     if (!scanTarget) return

//     setLoading(true)
//     setError(null)
//     setResult(null)

//     try {
//       const data = await scanURL(scanTarget)
//       setResult(data)
//       updateLiteracyScore(data.overall_risk, data.attack_type)
//     } catch (e) {
//       setError("Scan failed — make sure the backend is running on port 8000.")
//     } finally {
//       setLoading(false)
//     }
//   }

//   return (
//     <div className="min-h-screen bg-gray-950 text-white">

//       {/* Header */}
//       <header className="border-b border-gray-800 px-6 py-4 flex items-center gap-3">
//         <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-sm font-bold">
//           CS
//         </div>
//         <span className="text-lg font-semibold">CampusShield</span>
//         <span className="text-xs text-gray-500 bg-gray-800 px-2 py-0.5 rounded-full">
//           AI Fraud Intelligence
//         </span>
//         <button
//           onClick={() => setShowDemo(!showDemo)}
//           className="text-xs text-gray-400 border border-gray-700 px-3 py-1.5 rounded-lg hover:bg-gray-800 transition"
//         >
//           {showDemo ? "Hide Demo" : "Demo Mode"}
//         </button>
//       </header>

//       <main className="max-w-3xl mx-auto px-4 py-10 space-y-8">

//         {/* Hero */}
//         <div className="text-center space-y-2">
//           <h1 className="text-3xl font-bold tracking-tight">
//             Is this URL safe?
//           </h1>
//           <p className="text-gray-400 text-sm">
//             Paste any URL to check for phishing, typosquatting, and UPI fraud.
//           </p>
//         </div>

//         {/* Demo simulator */}
//         {showDemo && (
//           <DemoSimulator
//             onSelectScenario={(scenarioUrl) => setUrl(scenarioUrl)}
//             onTriggerScan={(scenarioUrl)    => handleScan(scenarioUrl)}
//           />
//         )}

//         {/* URL input */}
//         <URLInput
//           url={url}
//           setUrl={setUrl}
//           onScan={() => handleScan()}
//           loading={loading}
//         />

//         {/* Error */}
//         {error && (
//           <div className="bg-red-900/30 border border-red-700 rounded-xl p-4 text-red-300 text-sm">
//             {error}
//           </div>
//         )}

//         {/* Results */}
//         {result && (
//           <div className="space-y-6">

//             {/* Attack label — Upgrade 3 */}
//             <AttackLabel attackType={result.attack_type} />

//             {/* Risk meter */}
//             <RiskMeter
//               score={result.overall_risk}
//               colour={getRiskColour(result.overall_risk)}
//               label={result.verdict}
//             />

//             {/* Domain age timeline — Upgrade 1 */}
//             <DomainTimeline
//               domainAgeSignal={result.url_scan?.signals?.domain_age}
//             />

//             {/* 4 URL signal cards */}
//             <SignalCards signals={result.url_scan?.signals} />

//             {/* UPI fraud signals — Feature 3 */}
//             <UPISignals paymentScan={result.payment_scan} />

//             {/* Visual heatmap — Feature 2 — renders only when available */}
//             <HeatmapViewer visualScan={result.visual_scan} />

//             {/* Trust explainer card — Feature 4 */}
//             <ExplainerCard
//               explanation={result.explanation}
//               impersonationStatement={result.impersonation_statement}
//               attackType={result.attack_type}
//               riskScore={result.overall_risk}
//             />

//             {/* Literacy score — Feature 5A */}
//             <LiteracyScore />

//           </div>
//         )}

//       </main>
//     </div>
//   )
// }
