import { useState } from "react";
import DashboardLayout from "../components/DashboardLayout";
import Mermaid from "react-mermaid2";
import jsonToMermaid from "../utils/jsonToMermaid";

const API_BASE = import.meta.env.VITE_AGENT_API_BASE;

function Generate() {
  const [description, setDescription] = useState("");
  const [response, setResponse] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [expectedUsers, setExpectedUsers] = useState("");
  const [concurrentUsers, setConcurrentUsers] = useState("");
  const [usagePattern, setUsagePattern] = useState("steady");
  const [dailyRequests, setDailyRequests] = useState("");
  const [storageGB, setStorageGB] = useState("");
  const [latencyMs, setLatencyMs] = useState("");
  const [criticalFeatures, setCriticalFeatures] = useState("");
  const [region, setRegion] = useState("");
  const [maxCost, setMaxCost] = useState("");

  const [sessionId, setSessionId] = useState(null);
  const [polling, setPolling] = useState(false);
  const [architecture, setArchitecture] = useState(null);
  const [error, setError] = useState("");
  const [mermaidCode, setMermaidCode] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setPolling(true);
    setIsLoading(true);
    setArchitecture(null);
    setMermaidCode("");
    setResponse("");
    setSessionId(null);

    const payload = {
      prompt: description,
      region,
      max_cost: Number(maxCost),
      constraints: criticalFeatures,
      expected_total_users: Number(expectedUsers),
      usage_pattern: usagePattern,
      storage: Number(storageGB),
      concurrent_users: Number(concurrentUsers),
      daily_requests: Number(dailyRequests),
      latency_requirements: Number(latencyMs),
    };

    try {
      const res = await fetch(`${API_BASE}/api/architecture/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();

      if (data.session_id) {
        setSessionId(data.session_id);
        pollForResult(data.session_id, 0);
      } else {
        setError("Failed to start agent session.");
        setPolling(false);
        setIsLoading(false);
      }
    } catch (err) {
      setError("Network error. Please try again.");
      setPolling(false);
      setIsLoading(false);
    }
  };

  const pollForResult = async (id, attempt) => {
    if (attempt > 60) {
      setError("Agent took too long. Please try again later.");
      setPolling(false);
      setIsLoading(false);
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/architecture/status/${id}`);
      const data = await res.json();

      if (data.status === "complete" && data.architecture) {
        setPolling(false);
        setIsLoading(false);
        setArchitecture(data.architecture);
        setResponse(JSON.stringify(data.architecture, null, 2)); // 👈 ensures "Generated Architecture" block displays
        setMermaidCode(jsonToMermaid(data.architecture));
      } else if (data.status === "processing" || data.status === "pending") {
        setTimeout(() => pollForResult(id, attempt + 1), 9000); // 10s interval
      } else {
        setError("Session not found or failed.");
        setPolling(false);
        setIsLoading(false);
      }
    } catch (err) {
      setError("Error polling agent.");
      setPolling(false);
      setIsLoading(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-100">
          <div className="flex items-center space-x-3 mb-4">
            <div className="p-3 bg-blue-100 rounded-lg">
              <svg
                className="h-8 w-8 text-blue-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                />
              </svg>
            </div>
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-gray-900">
                Generate Architecture
              </h1>
              <p className="text-gray-600">
                Provide traffic & usage metrics and our agent will design an
                optimized AWS architecture.
              </p>
            </div>
          </div>
        </div>

        {/* Form */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100">
          <div className="p-8">
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Description */}
              <div>
                <label
                  htmlFor="description"
                  className="block text-sm font-semibold text-gray-700 mb-2"
                >
                  Application Description
                </label>
                <textarea
                  id="description"
                  rows={4}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Briefly describe the application, core functionality and constraints..."
                  className="w-full border-2 border-gray-200 rounded-xl p-4 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 text-gray-700 placeholder-gray-400 resize-none"
                  required
                />
              </div>

              {/* Inputs Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Expected Total Users */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Expected Total Users
                  </label>
                  <input
                    type="number"
                    min={0}
                    value={expectedUsers}
                    onChange={(e) => setExpectedUsers(e.target.value)}
                    placeholder="e.g. 50000"
                    className="w-full border-2 border-gray-200 rounded-xl p-3 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all duration-200 text-gray-700"
                  />
                </div>

                {/* Concurrent Users */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Concurrent Users (peak)
                  </label>
                  <input
                    type="number"
                    min={0}
                    value={concurrentUsers}
                    onChange={(e) => setConcurrentUsers(e.target.value)}
                    placeholder="e.g. 2000"
                    className="w-full border-2 border-gray-200 rounded-xl p-3 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all duration-200 text-gray-700"
                  />
                </div>

                {/* Usage Pattern */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Usage Pattern
                  </label>
                  <select
                    value={usagePattern}
                    onChange={(e) => setUsagePattern(e.target.value)}
                    className="w-full border-2 border-gray-200 rounded-xl p-3 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all duration-200 text-gray-700"
                  >
                    <option value="steady">Steady</option>
                    <option value="burst">Burst / Spiky</option>
                    <option value="diurnal">Diurnal (daily peaks)</option>
                    <option value="seasonal">Seasonal</option>
                  </select>
                </div>

                {/* Daily Requests */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Daily Requests (approx)
                  </label>
                  <input
                    type="number"
                    min={0}
                    value={dailyRequests}
                    onChange={(e) => setDailyRequests(e.target.value)}
                    placeholder="e.g. 1,000,000"
                    className="w-full border-2 border-gray-200 rounded-xl p-3 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all duration-200 text-gray-700"
                  />
                </div>

                {/* Storage */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Storage (GB)
                  </label>
                  <input
                    type="number"
                    min={0}
                    value={storageGB}
                    onChange={(e) => setStorageGB(e.target.value)}
                    placeholder="e.g. 100"
                    className="w-full border-2 border-gray-200 rounded-xl p-3 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all duration-200 text-gray-700"
                  />
                </div>

                {/* Latency */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Latency Requirement (ms)
                  </label>
                  <input
                    type="number"
                    min={0}
                    value={latencyMs}
                    onChange={(e) => setLatencyMs(e.target.value)}
                    placeholder="e.g. 200"
                    className="w-full border-2 border-gray-200 rounded-xl p-3 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all duration-200 text-gray-700"
                  />
                </div>

                {/* Region */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Region
                  </label>
                  <select
                    value={region}
                    onChange={(e) => setRegion(e.target.value)}
                    className="w-full border-2 border-gray-200 rounded-xl p-3 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all duration-200 text-gray-700"
                    required
                  >
                    <option value="">Select region</option>
                    <option value="us-east-1">US East (N. Virginia)</option>
                    <option value="ap-south-1">Asia Pacific (Mumbai)</option>
                    <option value="eu-west-1">EU (Ireland)</option>
                  </select>
                </div>
              </div>

              {/* Critical Features */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Critical Features / Notes
                </label>
                <textarea
                  rows={3}
                  value={criticalFeatures}
                  onChange={(e) => setCriticalFeatures(e.target.value)}
                  placeholder="Authentication, file upload sizes, streaming, regulatory constraints, etc."
                  className="w-full border-2 border-gray-200 rounded-xl p-4 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all duration-200 text-gray-700 placeholder-gray-400 resize-none"
                />
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isLoading || !description.trim()}
                className="w-full bg-gradient-to-r from-blue-600 to-blue-700 text-white px-6 py-3 rounded-xl hover:from-blue-700 hover:to-blue-800 transition-all duration-200 font-semibold text-lg shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-3"
              >
                {isLoading ? (
                  <>
                    <svg
                      className="animate-spin h-5 w-5"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                        className="opacity-25"
                      ></circle>
                      <path
                        fill="currentColor"
                        className="opacity-75"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                      ></path>
                    </svg>
                    <span>Designing Architecture...</span>
                  </>
                ) : (
                  <span>Generate Architecture</span>
                )}
              </button>
            </form>
          </div>
        </div>

        {/* Response */}
        {response && (
          <div className="bg-white rounded-2xl shadow-lg border border-gray-100">
            <div className="p-8">
              <div className="flex items-center space-x-3 mb-6">
                <div className="p-2 bg-green-100 rounded-lg">
                  <svg
                    className="h-6 w-6 text-green-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                </div>
                <h2 className="text-xl font-bold text-gray-900">
                  Generated Architecture
                </h2>
              </div>

              <div className="bg-gray-50 rounded-xl p-6 border-l-4 border-l-blue-500">
                <pre className="whitespace-pre-line text-gray-700 font-mono text-sm leading-relaxed">
                  {response}
                </pre>
              </div>
            </div>
          </div>
        )}

        {polling && (
          <div className="mt-8 text-blue-600 font-semibold">
            Generating architecture... (this may take a few minutes)
          </div>
        )}
        {error && (
          <div className="mt-8 text-red-600 font-semibold">{error}</div>
        )}
        {mermaidCode && (
          <div className="mt-8 bg-white rounded-xl shadow-lg p-6">
            <Mermaid chart={mermaidCode} />
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}

export default Generate;
