import React, { useState, useEffect } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export default function GrangerModal({ signal, onClose }) {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [maxLag, setMaxLag] = useState(12);

  const runGrangerAnalysis = async () => {
    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const response = await fetch(
        `${API_BASE}/api/signal-radar/signals/${encodeURIComponent(signal.keyword)}/granger`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ max_lag: maxLag })
        }
      );

      if (!response.ok) {
        throw new Error('Failed to run Granger analysis');
      }

      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Auto-run on mount
  useEffect(() => {
    runGrangerAnalysis();
  }, []);

  const getFStatStrength = (fStat) => {
    if (!fStat) return '';
    if (fStat > 10) return '⭐⭐⭐⭐⭐';
    if (fStat > 7) return '⭐⭐⭐⭐';
    if (fStat > 5) return '⭐⭐⭐';
    if (fStat > 3) return '⭐⭐';
    return '⭐';
  };

  const getFStatColor = (fStat) => {
    if (!fStat) return 'text-gray-500';
    if (fStat > 10) return 'text-purple-600';
    if (fStat > 7) return 'text-indigo-600';
    if (fStat > 5) return 'text-blue-600';
    if (fStat > 3) return 'text-cyan-600';
    return 'text-gray-600';
  };

  const getPValueColor = (pValue) => {
    if (!pValue) return 'text-gray-500';
    if (pValue < 0.001) return 'text-green-600';
    if (pValue < 0.01) return 'text-yellow-600';
    if (pValue < 0.05) return 'text-orange-600';
    return 'text-red-600';
  };

  const getSignificanceLabel = (pValue) => {
    if (!pValue) return 'Unknown';
    if (pValue < 0.001) return 'Highly Significant ***';
    if (pValue < 0.01) return 'Very Significant **';
    if (pValue < 0.05) return 'Significant *';
    return 'Not Significant';
  };

  const getInterpretation = (result) => {
    if (!result) return '';

    const { f_statistic, p_value, optimal_lag } = result.granger_results;
    
    if (p_value < 0.05 && f_statistic > 5) {
      return `Strong evidence that "${signal.keyword}" Granger-causes the target variable. 
              The F-statistic of ${f_statistic.toFixed(2)} indicates a robust predictive relationship 
              with ${optimal_lag} period${optimal_lag > 1 ? 's' : ''} lag.`;
    } else if (p_value < 0.05) {
      return `Moderate evidence of Granger causality detected. 
              "${signal.keyword}" may help predict the target variable with ${optimal_lag} period${optimal_lag > 1 ? 's' : ''} lag.`;
    } else {
      return `No significant Granger causality detected. 
              "${signal.keyword}" does not appear to help predict the target variable better than past values alone.`;
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div 
          className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75" 
          onClick={onClose}
        />

        {/* Modal panel */}
        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
          {/* Header */}
          <div className="bg-gradient-to-r from-purple-600 to-indigo-600 px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xl font-bold text-white">
                  📈 Granger Causality Analysis
                </h3>
                <p className="text-purple-100 text-sm mt-1">
                  Keyword: <strong>{signal.keyword}</strong>
                </p>
              </div>
              <button
                onClick={onClose}
                className="text-white hover:text-gray-200 text-2xl font-bold"
              >
                ×
              </button>
            </div>
          </div>

          {/* Body */}
          <div className="px-6 py-6">
            {/* Controls */}
            <div className="mb-6 bg-gray-50 rounded-lg p-4">
              <div className="flex items-center gap-4">
                <label className="block text-sm font-medium text-gray-700">
                  Max Lag Periods
                </label>
                <input
                  type="number"
                  value={maxLag}
                  onChange={(e) => setMaxLag(Number(e.target.value))}
                  min="1"
                  max="30"
                  className="rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500 w-24"
                />
                <button
                  onClick={runGrangerAnalysis}
                  disabled={loading}
                  className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition disabled:bg-gray-400"
                >
                  {loading ? 'Running...' : '🔄 Re-run Analysis'}
                </button>
              </div>
            </div>

            {/* Loading State */}
            {loading && (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
                <p className="mt-4 text-gray-600">Running Granger causality test...</p>
              </div>
            )}

            {/* Error State */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
                Error: {error}
              </div>
            )}

            {/* Results */}
            {!loading && !error && results && (
              <div className="space-y-6">
                {/* F-Statistic Highlight */}
                <div className="bg-gradient-to-br from-purple-50 to-indigo-50 rounded-lg p-6 border-2 border-purple-200">
                  <div className="text-center">
                    <div className="text-sm font-medium text-gray-600 uppercase tracking-wide mb-2">
                      F-Statistic
                    </div>
                    <div className={`text-6xl font-bold ${getFStatColor(results.granger_results.f_statistic)}`}>
                      {results.granger_results.f_statistic.toFixed(3)}
                    </div>
                    <div className="text-3xl mt-2">
                      {getFStatStrength(results.granger_results.f_statistic)}
                    </div>
                    <div className="mt-3 text-sm text-gray-600">
                      {results.granger_results.f_statistic > 10 && 'Extremely Strong Signal'}
                      {results.granger_results.f_statistic > 7 && results.granger_results.f_statistic <= 10 && 'Very Strong Signal'}
                      {results.granger_results.f_statistic > 5 && results.granger_results.f_statistic <= 7 && 'Strong Signal'}
                      {results.granger_results.f_statistic > 3 && results.granger_results.f_statistic <= 5 && 'Moderate Signal'}
                      {results.granger_results.f_statistic <= 3 && 'Weak Signal'}
                    </div>
                  </div>
                </div>

                {/* Key Metrics Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* P-Value */}
                  <div className="bg-white border-2 border-gray-200 rounded-lg p-4">
                    <div className="text-sm font-medium text-gray-600 uppercase tracking-wide mb-2">
                      P-Value
                    </div>
                    <div className={`text-3xl font-bold ${getPValueColor(results.granger_results.p_value)}`}>
                      {results.granger_results.p_value.toExponential(3)}
                    </div>
                    <div className="mt-2 text-sm font-medium text-gray-700">
                      {getSignificanceLabel(results.granger_results.p_value)}
                    </div>
                  </div>

                  {/* Optimal Lag */}
                  <div className="bg-white border-2 border-gray-200 rounded-lg p-4">
                    <div className="text-sm font-medium text-gray-600 uppercase tracking-wide mb-2">
                      Optimal Lag
                    </div>
                    <div className="text-3xl font-bold text-indigo-600">
                      {results.granger_results.optimal_lag}
                    </div>
                    <div className="mt-2 text-sm text-gray-600">
                      Period{results.granger_results.optimal_lag > 1 ? 's' : ''}
                    </div>
                  </div>

                  {/* Correlation */}
                  <div className="bg-white border-2 border-gray-200 rounded-lg p-4">
                    <div className="text-sm font-medium text-gray-600 uppercase tracking-wide mb-2">
                      Correlation (R)
                    </div>
                    <div className="text-3xl font-bold text-blue-600">
                      {results.granger_results.r_value?.toFixed(3) || 'N/A'}
                    </div>
                    <div className="mt-2 text-sm text-gray-600">
                      {results.granger_results.r_value > 0.7 && 'Strong Positive'}
                      {results.granger_results.r_value > 0.3 && results.granger_results.r_value <= 0.7 && 'Moderate Positive'}
                      {results.granger_results.r_value > -0.3 && results.granger_results.r_value <= 0.3 && 'Weak'}
                      {results.granger_results.r_value > -0.7 && results.granger_results.r_value <= -0.3 && 'Moderate Negative'}
                      {results.granger_results.r_value <= -0.7 && 'Strong Negative'}
                    </div>
                  </div>
                </div>

                {/* Interpretation */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <span className="text-2xl">💡</span>
                    <div>
                      <div className="font-semibold text-blue-900 mb-1">Interpretation</div>
                      <p className="text-sm text-blue-800">
                        {getInterpretation(results)}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Additional Details */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-semibold text-gray-900 mb-3">Analysis Details</h4>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <span className="text-gray-600">Signal Sources:</span>
                      <span className="ml-2 font-medium">{signal.sources.length}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Current Momentum:</span>
                      <span className="ml-2 font-medium">{signal.momentum.toFixed(1)}%</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Max Lag Tested:</span>
                      <span className="ml-2 font-medium">{maxLag} periods</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Significance Level:</span>
                      <span className="ml-2 font-medium">α = 0.05</span>
                    </div>
                  </div>
                </div>

                {/* Statistical Notes */}
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <span className="text-xl">ℹ️</span>
                    <div className="text-xs text-yellow-800">
                      <p className="font-semibold mb-1">About Granger Causality:</p>
                      <ul className="list-disc list-inside space-y-1">
                        <li>Tests whether past values of "{signal.keyword}" help predict future values of the target</li>
                        <li>F-statistic measures the strength of predictive power (higher = stronger)</li>
                        <li>P-value &lt; 0.05 indicates statistically significant relationship</li>
                        <li>Optimal lag shows the time delay for maximum predictive effect</li>
                        <li>Granger causality does not imply true causation, only predictive utility</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="bg-gray-50 px-6 py-4 flex justify-end gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
