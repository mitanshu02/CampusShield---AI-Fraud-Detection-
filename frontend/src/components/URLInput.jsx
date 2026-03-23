// frontend/src/components/URLInput.jsx

export default function URLInput({ url, setUrl, onScan, loading }) {
  return (
    <div className="flex gap-3">
      <input
        type="text"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && onScan()}
        placeholder="Paste a URL to scan — e.g. fees-nitbhopal-edu.in/pay"
        className="flex-1 bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 transition"
      />
      <button
        onClick={onScan}
        disabled={loading || !url.trim()}
        className="bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-500 text-white font-semibold px-6 py-3 rounded-xl transition text-sm whitespace-nowrap"
      >
        {loading ? "Scanning..." : "Scan URL"}
      </button>
    </div>
  );
}
