import { useState } from "react";
import DashboardLayout from "../components/DashboardLayout";
import axios from "axios";

const API_BASE = import.meta.env.VITE_AGENT_API_BASE; // Use the same API base as in Generate.jsx

function Optimize() {
  const [currentArch, setCurrentArch] = useState("");
  const [response, setResponse] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setResponse(null);
    setStatus("Starting optimization...");

    try {
      // Step 1: Start optimization
      const startResponse = await axios.post(
        `${API_BASE}/api/architecture/optimize`,
        {
          description: currentArch,
        }
      );

      const { session_id } = startResponse.data;

      // Step 2: Poll for status
      pollStatus(session_id);
    } catch (error) {
      console.error("Error starting optimization:", error);
      setStatus("Failed to start optimization. Please try again.");
      setIsLoading(false);
    }
  };

  const pollStatus = async (sessionId) => {
    try {
      const interval = setInterval(async () => {
        const statusResponse = await axios.get(
          `${API_BASE}/api/architecture/status/${sessionId}`
        );

        const { status, architecture, suggestions } = statusResponse.data;

        if (status === "complete") {
          clearInterval(interval);
          setResponse(architecture);
          setStatus("Optimization complete!");
          setIsLoading(false);
        } else {
          // Handle cases where suggestions might not be an array
          const statusMessage = Array.isArray(suggestions)
            ? suggestions.join(", ")
            : "Processing...";
          setStatus(statusMessage);
        }
      }, 5000); // Poll every 5 seconds
    } catch (error) {
      console.error("Error polling status:", error);
      setStatus("Failed to fetch status. Please try again.");
      setIsLoading(false);
    }
  };

  // Groups suggestions by their 'type' property
  const groupOptimizations = (optimizationData) => {
    // The data arrives as an object with keys like "cost_optimizations", etc.
    // We need to transform it into a structure that the table renderer can use.
    if (!optimizationData || !Array.isArray(optimizationData.OptimizationSuggestions)) {
      return {};
    }

    // Group the array by the "type" property inside each object
    return optimizationData.OptimizationSuggestions.reduce((acc, suggestion) => {
      const { type } = suggestion;
      if (!acc[type]) {
        acc[type] = [];
      }
      acc[type].push(suggestion);
      return acc;
    }, {});
  };

  // Renders a single table for a category of optimizations
  const renderOptimizationTable = (title, optimizations) => {
    if (!optimizations || optimizations.length === 0) return null;

    return (
      <div className="optimization-category mt-8" key={title}>
        <h3 className="text-xl font-bold text-white bg-gradient-to-r from-purple-600 to-pink-600 px-4 py-2 rounded-t-lg shadow-md">
          {title}
        </h3>
        <div className="overflow-x-auto">
          <table className="min-w-full border border-gray-200 shadow-sm rounded-b-lg overflow-hidden">
            <thead className="bg-gray-100 text-gray-700">
              <tr>
                <th className="px-4 py-3 border text-left">Resource Type</th>
                <th className="px-4 py-3 border text-left">Resource ID</th>
                <th className="px-4 py-3 border text-left">Suggestion</th>
                <th className="px-4 py-3 border text-left">
                  Estimated Improvement
                </th>
              </tr>
            </thead>
            <tbody className="bg-white">
              {optimizations.map((item, index) => (
                <tr
                  key={index}
                  className="hover:bg-purple-50 transition-colors duration-200"
                >
                  <td className="px-4 py-3 border font-medium text-gray-800">
                    {item.resourceType}
                  </td>
                  <td className="px-4 py-3 border text-sm text-gray-600">
                    {item.resourceId}
                  </td>
                  <td className="px-4 py-3 border text-gray-700">
                    {item.optimizationSuggestion}
                  </td>
                  <td className="px-4 py-3 border font-semibold text-green-600">
                    {item.estimatedImprovement || "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  const groupedSuggestions = response ? groupOptimizations(response) : {};

  return (
    <DashboardLayout>
      <div className="min-h-screen py-8">
        <div className="max-w-5xl mx-auto px-6 space-y-8">
          {/* Header Section */}
          <div className="bg-white/80 backdrop-blur-sm rounded-3xl shadow-xl p-8 border border-white/50">
            <div className="flex items-center space-x-4 mb-2">
              <div className="p-4 bg-gradient-to-r from-purple-500 to-pink-600 rounded-2xl shadow-lg">
                <svg
                  className="h-8 w-8 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                </svg>
              </div>
              <div>
                <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                  Optimize Architecture
                </h1>
                <p className="text-lg text-gray-600 mt-1">
                  Analyze your current setup and get cost & performance
                  optimization recommendations
                </p>
              </div>
            </div>
          </div>

          {/* Form Section */}
          <div className="bg-white/80 backdrop-blur-sm rounded-3xl shadow-xl border border-white/50 overflow-hidden">
            <div className="p-8">
              <form onSubmit={handleSubmit} className="space-y-8">
                {/* Current Architecture Input */}
                <div className="space-y-4">
                  <label
                    htmlFor="currentArch"
                    className="block text-lg font-bold text-gray-800"
                  >
                    Current Architecture Setup
                  </label>
                  <textarea
                    id="currentArch"
                    rows={8}
                    value={currentArch}
                    onChange={(e) => setCurrentArch(e.target.value)}
                    placeholder="Describe your current AWS architecture in detail..."
                    className="w-full border-2 border-gray-200 rounded-2xl p-4 focus:outline-none focus:ring-4 focus:ring-purple-500/20 focus:border-purple-500 transition-all duration-300 resize-none text-gray-700 placeholder-gray-400 text-lg leading-relaxed"
                    required
                  />
                </div>

                {/* Submit Button */}
                <button
                  type="submit"
                  disabled={isLoading || !currentArch.trim()}
                  className="w-full bg-gradient-to-r from-purple-600 via-purple-700 to-pink-600 text-white px-8 py-5 rounded-2xl hover:from-purple-700 hover:via-purple-800 hover:to-pink-700 transition-all duration-300 font-bold text-xl shadow-xl hover:shadow-2xl disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-3 transform hover:scale-105"
                >
                  {isLoading ? (
                    <>
                      <svg
                        className="animate-spin h-6 w-6"
                        fill="none"
                        viewBox="0 0 24 24"
                      >
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                        ></circle>
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        ></path>
                      </svg>
                      <span>Analyzing & Optimizing Architecture...</span>
                    </>
                  ) : (
                    <>
                      <svg
                        className="h-6 w-6"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                        />
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                        />
                      </svg>
                      <span>Optimize AWS Architecture</span>
                    </>
                  )}
                </button>
              </form>
            </div>
          </div>

          {/* Response Section */}
          {response && (
            <div className="bg-white/80 backdrop-blur-sm rounded-3xl shadow-xl border border-white/50 overflow-hidden">
              <div className="p-8">
                <div className="flex items-center space-x-4 mb-8">
                  <div className="p-3 bg-gradient-to-r from-green-500 to-emerald-500 rounded-2xl shadow-lg">
                    <svg
                      className="h-8 w-8 text-white"
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
                  <div>
                    <h2 className="text-3xl font-bold bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">
                      Optimization Recommendations
                    </h2>
                    <p className="text-gray-600 mt-1">
                      AI-powered cost and performance improvements
                    </p>
                  </div>
                </div>

                <div className="bg-gradient-to-br from-gray-50 to-purple-50 rounded-2xl p-8 border-l-4 border-l-purple-500 shadow-inner space-y-8">
                  {Object.entries(groupedSuggestions).map(
                    ([title, optimizations]) =>
                      renderOptimizationTable(title, optimizations)
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}

export default Optimize;
