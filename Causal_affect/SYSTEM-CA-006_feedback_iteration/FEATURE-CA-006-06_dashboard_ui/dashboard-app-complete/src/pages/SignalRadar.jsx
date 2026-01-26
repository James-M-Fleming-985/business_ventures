import React, { useState, useEffect } from 'react';
import GrangerModal from '../components/GrangerModal';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export default function SignalRadar() {
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [matchingMode, setMatchingMode] = useState('simple');
  const [minMomentum, setMinMomentum] = useState(30);
  const [minSources, setMinSources] = useState(2);
  const [expandedCategories, setExpandedCategories] = useState(new Set(['Technology & AI']));
  const [selectedSignal, setSelectedSignal] = useState(null);
  const [showGrangerModal, setShowGrangerModal] = useState(false);

  // Categorize signals by keyword patterns
  const categorizeSignals = (signals) => {
    const categories = {
      'Technology & AI': {
        keywords: ['ai', 'artificial intelligence', 'machine learning', 'neural', 'deep learning', 
                  'chatgpt', 'gpt', 'llm', 'model', 'algorithm', 'data science', 'computer vision'],
        signals: []
      },
      'Business & Economy': {
        keywords: ['layoff', 'hiring', 'job', 'employment', 'economy', 'market', 'stock', 
                  'startup', 'venture', 'funding', 'ipo', 'acquisition', 'merger'],
        signals: []
      },
      'Health & Medical': {
        keywords: ['health', 'medical', 'disease', 'vaccine', 'covid', 'pandemic', 'drug', 
                  'clinical', 'patient', 'hospital', 'treatment'],
        signals: []
      },
      'Science & Research': {
        keywords: ['research', 'study', 'science', 'discovery', 'experiment', 'paper', 
                  'journal', 'physics', 'chemistry', 'biology'],
        signals: []
      },
      'Policy & Regulation': {
        keywords: ['policy', 'regulation', 'law', 'government', 'congress', 'senate', 
                  'legislation', 'legal', 'compliance'],
        signals: []
      },
      'Other': {
        keywords: [],
        signals: []
      }
    };

    signals.forEach(signal => {
      const keyword = signal.keyword.toLowerCase();
      let categorized = false;

      for (const [categoryName, category] of Object.entries(categories)) {
        if (categoryName === 'Other') continue;
        
        if (category.keywords.some(kw => keyword.includes(kw) || kw.includes(keyword))) {
          category.signals.push(signal);
          categorized = true;
          break;
        }
      }

      if (!categorized) {
        categories['Other'].signals.push(signal);
      }
    });

    return categories;
  };

  const fetchSignals = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(
        `${API_BASE}/api/signal-radar/signals/composite?matching_mode=${matchingMode}&min_momentum=${minMomentum}&min_sources=${minSources}`
      );
      
      if (!response.ok) {
        throw new Error('Failed to fetch signals');
      }

      const data = await response.json();
      setSignals(data.composite_signals || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSignals();
    const interval = setInterval(fetchSignals, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [matchingMode, minMomentum, minSources]);

  const toggleCategory = (categoryName) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(categoryName)) {
      newExpanded.delete(categoryName);
    } else {
      newExpanded.add(categoryName);
    }
    setExpandedCategories(newExpanded);
  };

  const handleRunGranger = (signal) => {
    setSelectedSignal(signal);
    setShowGrangerModal(true);
  };

  const getCategoryIcon = (categoryName) => {
    const icons = {
      'Technology & AI': '🤖',
      'Business & Economy': '💼',
      'Health & Medical': '🏥',
      'Science & Research': '🔬',
      'Policy & Regulation': '⚖️',
      'Other': '📊'
    };
    return icons[categoryName] || '📊';
  };

  const categorizedSignals = categorizeSignals(signals);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold flex items-center gap-3">
                <span className="relative flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
                </span>
                SIGNAL RADAR
              </h1>
              <p className="mt-1 text-purple-100">Composite Signals - Aggregated by Keyword</p>
            </div>
            <div className="text-right">
              <div className="text-sm text-purple-100">Total Signals</div>
              <div className="text-3xl font-bold">{signals.length}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white border-b shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex flex-wrap gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Matching Mode
              </label>
              <select
                value={matchingMode}
                onChange={(e) => setMatchingMode(e.target.value)}
                className="rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500"
              >
                <option value="simple">Simple (Exact Match)</option>
                <option value="fuzzy">Fuzzy Matching</option>
                <option value="sophisticated">ML Semantic</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Min Sources
              </label>
              <select
                value={minSources}
                onChange={(e) => setMinSources(Number(e.target.value))}
                className="rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500"
              >
                <option value="1">1+</option>
                <option value="2">2+</option>
                <option value="3">3+</option>
                <option value="4">4+</option>
                <option value="5">5+</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Min Momentum
              </label>
              <input
                type="number"
                value={minMomentum}
                onChange={(e) => setMinMomentum(Number(e.target.value))}
                min="0"
                max="100"
                className="rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500 w-24"
              />
              <span className="ml-1 text-gray-500">%</span>
            </div>

            <div className="flex items-end">
              <button
                onClick={fetchSignals}
                className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition"
              >
                🔄 Refresh
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
            <p className="mt-4 text-gray-600">Loading signals...</p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
            Error: {error}
          </div>
        )}

        {!loading && !error && signals.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            No signals found with current filters
          </div>
        )}

        {!loading && !error && signals.length > 0 && (
          <div className="space-y-6">
            {Object.entries(categorizedSignals).map(([categoryName, category]) => {
              if (category.signals.length === 0) return null;

              const isExpanded = expandedCategories.has(categoryName);

              return (
                <div key={categoryName} className="bg-white rounded-lg shadow-md overflow-hidden">
                  {/* Category Header */}
                  <button
                    onClick={() => toggleCategory(categoryName)}
                    className="w-full px-6 py-4 bg-gradient-to-r from-gray-50 to-gray-100 hover:from-gray-100 hover:to-gray-200 transition flex items-center justify-between border-b border-gray-200"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{getCategoryIcon(categoryName)}</span>
                      <span className="text-lg font-semibold text-gray-900">{categoryName}</span>
                      <span className="text-sm text-gray-500">({category.signals.length} keywords)</span>
                    </div>
                    <span className="text-gray-400">
                      {isExpanded ? '▼' : '▶'}
                    </span>
                  </button>

                  {/* Category Content */}
                  {isExpanded && (
                    <div className="p-6 space-y-4">
                      {category.signals.map((signal) => (
                        <SignalCard
                          key={signal.keyword}
                          signal={signal}
                          onRunGranger={() => handleRunGranger(signal)}
                        />
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Granger Modal */}
      {showGrangerModal && selectedSignal && (
        <GrangerModal
          signal={selectedSignal}
          onClose={() => {
            setShowGrangerModal(false);
            setSelectedSignal(null);
          }}
        />
      )}
    </div>
  );
}

// Signal Card Component
function SignalCard({ signal, onRunGranger }) {
  const [expanded, setExpanded] = useState(false);

  const getTrendIcon = () => {
    if (signal.momentum > 70) return '↗';
    if (signal.momentum > 40) return '→';
    return '↘';
  };

  const getMomentumColor = () => {
    if (signal.momentum > 70) return 'text-green-600';
    if (signal.momentum > 40) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getSourceIcon = (source) => {
    const icons = {
      'wikipedia': '📰',
      'reddit': '🔵',
      'twitter': '🐦',
      'arxiv': '🎓',
      'news': '📰',
      'linkedin': '💼',
      'google_trends': '📊'
    };
    return icons[source.toLowerCase()] || '📊';
  };

  return (
    <div className="border-2 border-gray-200 rounded-lg p-4 hover:border-purple-300 hover:shadow-lg transition">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🔥</span>
            <h3 className="text-xl font-bold text-gray-900">{signal.keyword}</h3>
            <span className={`text-2xl font-bold ${getMomentumColor()}`}>
              {getTrendIcon()} {signal.momentum.toFixed(1)}%
            </span>
          </div>
          <div className="mt-1 flex items-center gap-4 text-sm text-gray-600">
            <span>Sources: <strong>{signal.sources.length}</strong></span>
            <span>•</span>
            <span>Momentum: <strong>{signal.momentum.toFixed(1)}%</strong></span>
            <span>•</span>
            <span>Trend: <strong>{signal.momentum > 70 ? 'Rising' : signal.momentum > 40 ? 'Stable' : 'Falling'}</strong></span>
          </div>
        </div>
      </div>

      {/* Sources Breakdown */}
      <div className="mt-3 pt-3 border-t border-gray-200">
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
          {signal.sources.slice(0, expanded ? signal.sources.length : 4).map((source, idx) => (
            <div key={idx} className="text-sm flex items-center gap-1">
              <span>{getSourceIcon(source.source_name)}</span>
              <span className="font-medium">{source.source_name}:</span>
              <span className="text-gray-600">
                {source.change > 0 && '+'}
                {source.change.toFixed(0)}%
              </span>
            </div>
          ))}
        </div>

        {signal.sources.length > 4 && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="mt-2 text-sm text-purple-600 hover:text-purple-800"
          >
            {expanded ? 'Show less' : `Show ${signal.sources.length - 4} more sources...`}
          </button>
        )}
      </div>

      {/* Actions */}
      <div className="mt-4 flex gap-3">
        <button
          onClick={onRunGranger}
          className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition text-sm font-medium"
        >
          📈 Run Granger Analysis
        </button>
        <button
          onClick={() => setExpanded(!expanded)}
          className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition text-sm font-medium"
        >
          📊 View Details
        </button>
      </div>
    </div>
  );
}
