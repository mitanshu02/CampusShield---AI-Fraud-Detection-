// frontend/src/components/UPISignals.jsx

export default function UPISignals({ paymentScan }) {
  if (!paymentScan) return null

  // payment scan ran but browser couldn't load the page
  if (!paymentScan.available) {
    return (
      <div className="rounded-2xl border border-gray-800 bg-gray-900/40 p-5">
        <h2 className="text-sm font-semibold text-gray-400 uppercase
                       tracking-widest mb-3">
          UPI Fraud Signals
        </h2>
        <div className="flex items-center gap-3 py-3">
          <div className="w-8 h-8 rounded-lg bg-gray-800 border border-gray-700
                          flex items-center justify-center flex-shrink-0">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
                 className="text-gray-500">
              <circle cx="12" cy="12" r="10" stroke="currentColor"
                      strokeWidth="1.5"/>
              <path d="M12 8v4M12 16h.01" stroke="currentColor"
                    strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </div>
          <div>
            <p className="text-sm text-gray-400 font-medium">
              No payment content detected
            </p>
            <p className="text-xs text-gray-600 mt-0.5">
              This page does not appear to contain any payment forms,
              UPI fields, or financial transaction elements.
            </p>
          </div>
        </div>
      </div>
    )
  }

  // payment scan ran but found no fraud signals
  if (!paymentScan.upi_signals || paymentScan.upi_signals.length === 0) {
    return (
      <div className="rounded-2xl border border-gray-800 bg-gray-900/40 p-5">
        <h2 className="text-sm font-semibold text-gray-400 uppercase
                       tracking-widest mb-3">
          UPI Fraud Signals
        </h2>
        <div className="flex items-center gap-3 py-3">
          <div className="w-8 h-8 rounded-lg bg-green-500/10 border
                          border-green-500/30 flex items-center justify-center
                          flex-shrink-0">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
                 className="text-green-400">
              <path d="M5 13l4 4L19 7" stroke="currentColor" strokeWidth="2"
                    strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <div>
            <p className="text-sm text-green-400 font-medium">
              No UPI fraud signals detected
            </p>
            <p className="text-xs text-gray-600 mt-0.5">
              Payment risk score: {paymentScan.payment_risk}/100 —
              no suspicious payment patterns found on this page.
            </p>
          </div>
        </div>
      </div>
    )
  }

  const dotStyle = {
    HIGH:   "bg-red-500",
    MEDIUM: "bg-amber-400",
    LOW:    "bg-gray-500",
  }

  const cardStyle = {
    HIGH:   "border-red-800 bg-red-950/30 text-red-300",
    MEDIUM: "border-amber-800 bg-amber-950/30 text-amber-300",
    LOW:    "border-gray-700 bg-gray-900 text-gray-300",
  }

  return (
    <div className="rounded-2xl border border-gray-800 bg-gray-900/40 p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-gray-400 uppercase
                       tracking-widest">
          UPI Fraud Signals
        </h2>
        <span className="text-xs font-bold text-red-300 bg-red-950/50
                         border border-red-800 px-2.5 py-1 rounded-full">
          Payment Risk {paymentScan.payment_risk}/100
        </span>
      </div>

      <div className="space-y-3">
        {paymentScan.upi_signals.map((sig, i) => {
          const sev   = sig.severity || "LOW"
          const style = cardStyle[sev] || cardStyle.LOW
          const dot   = dotStyle[sev]  || dotStyle.LOW

          return (
            <div key={i}
                 className={`rounded-xl border p-4 flex gap-3 items-start
                             ${style}`}>
              <div className={`w-2.5 h-2.5 rounded-full mt-1 flex-shrink-0
                               ${dot}`} />
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold text-white mb-1">
                  {sig.signal}
                </p>
                <p className="text-xs leading-relaxed opacity-80">
                  {sig.detail}
                </p>
              </div>
              <span className={`text-xs font-bold flex-shrink-0 ${
                sev === "HIGH"   ? "text-red-400"   :
                sev === "MEDIUM" ? "text-amber-400" : "text-gray-400"
              }`}>
                {sev}
              </span>
            </div>
          )
        })}
      </div>

      {paymentScan.deep_scan_triggered && paymentScan.deep_scan_note && (
        <div className="mt-4 bg-orange-950/40 border border-orange-800
                        rounded-xl px-4 py-3">
          <p className="text-xs font-semibold text-orange-300 mb-1">
            Deep Scan Finding
          </p>
          <p className="text-xs text-orange-200 leading-relaxed">
            {paymentScan.deep_scan_note}
          </p>
        </div>
      )}
    </div>
  )
}


// // frontend/src/components/UPISignals.jsx

// export default function UPISignals({ paymentScan }) {
//   if (!paymentScan || !paymentScan.available) return null
//   if (!paymentScan.upi_signals || paymentScan.upi_signals.length === 0) return null

//   const dotStyle = {
//     HIGH:   "bg-red-500",
//     MEDIUM: "bg-amber-400",
//     LOW:    "bg-gray-500",
//   }

//   const cardStyle = {
//     HIGH:   "border-red-800 bg-red-950/30 text-red-300",
//     MEDIUM: "border-amber-800 bg-amber-950/30 text-amber-300",
//     LOW:    "border-gray-700 bg-gray-900 text-gray-300",
//   }

//   return (
//     <div className="rounded-2xl border border-gray-800 bg-gray-900/40 p-5">
//       <div className="flex items-center justify-between mb-4">
//         <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-widest">
//           UPI Fraud Signals
//         </h2>
//         <span className="text-xs font-bold text-red-300 bg-red-950/50 border border-red-800 px-2.5 py-1 rounded-full">
//           Payment Risk {paymentScan.payment_risk}/100
//         </span>
//       </div>

//       <div className="space-y-3">
//         {paymentScan.upi_signals.map((sig, i) => {
//           const sev   = sig.severity || "LOW"
//           const style = cardStyle[sev] || cardStyle.LOW
//           const dot   = dotStyle[sev]  || dotStyle.LOW

//           return (
//             <div key={i} className={`rounded-xl border p-4 flex gap-3 items-start ${style}`}>
//               <div className={`w-2.5 h-2.5 rounded-full mt-1 flex-shrink-0 ${dot}`} />
//               <div className="flex-1 min-w-0">
//                 <p className="text-xs font-semibold text-white mb-1">{sig.signal}</p>
//                 <p className="text-xs leading-relaxed opacity-80">{sig.detail}</p>
//               </div>
//               <span className={`text-xs font-bold flex-shrink-0 ${
//                 sev === "HIGH"   ? "text-red-400"   :
//                 sev === "MEDIUM" ? "text-amber-400" : "text-gray-400"
//               }`}>
//                 {sev}
//               </span>
//             </div>
//           )
//         })}
//       </div>

//       {paymentScan.deep_scan_triggered && paymentScan.deep_scan_note && (
//         <div className="mt-4 bg-orange-950/40 border border-orange-800 rounded-xl px-4 py-3">
//           <p className="text-xs font-semibold text-orange-300 mb-1">
//             Deep Scan Finding
//           </p>
//           <p className="text-xs text-orange-200 leading-relaxed">
//             {paymentScan.deep_scan_note}
//           </p>
//         </div>
//       )}
//     </div>
//   )
// }