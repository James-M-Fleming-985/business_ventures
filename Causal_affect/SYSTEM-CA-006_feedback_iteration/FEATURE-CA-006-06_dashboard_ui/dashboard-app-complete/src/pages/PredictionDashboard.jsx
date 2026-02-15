import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  ComposedChart,
} from 'recharts';
import { Calendar, Filter, TrendingUp, AlertCircle } from 'lucide-react';

const PredictionDashboard = () => {
  const [summaryStats, setSummaryStats] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [modelData, setModelData] = useState(null);
  const [loading, setLoading] = useState({
    summary: true,
    chart: true,
    models: true,
  });
  const [error, setError] = useState({
    summary: null,
    chart: null,
    models: null,
  });
  const [filters, setFilters] = useState({
    domain: '',
    variablePair: '',
    dateRange: { start: '', end: '' },
    model: '',
    confidence: '',
  });
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });

  const location = useLocation();

  const fetchData = async () => {
    // Fetch summary stats
    setLoading(prev => ({ ...prev, summary: true }));
    setError(prev => ({ ...prev, summary: null }));
    try {
      const response = await fetch('/api/causality/predictions/accuracy');
      if (!response.ok) throw new Error('Failed to fetch accuracy data');
      const data = await response.json();
      setSummaryStats(data);
    } catch (err) {
      setError(prev => ({ ...prev, summary: err.message }));
    } finally {
      setLoading(prev => ({ ...prev, summary: false }));
    }

    // Fetch chart data
    setLoading(prev => ({ ...prev, chart: true }));
    setError(prev => ({ ...prev, chart: null }));
    try {
      const response = await fetch('/api/causality/predictions/accuracy/timeseries');
      if (!response.ok) throw new Error('Failed to fetch chart data');
      const data = await response.json();
      setChartData(data);
    } catch (err) {
      setError(prev => ({ ...prev, chart: err.message }));
    } finally {
      setLoading(prev => ({ ...prev, chart: false }));
    }

    // Fetch model comparison data
    setLoading(prev => ({ ...prev, models: true }));
    setError(prev => ({ ...prev, models: null }));
    try {
      const response = await fetch('/api/causality/predictions/models/compare');
      if (!response.ok) throw new Error('Failed to fetch model data');
      const data = await response.json();
      setModelData(data);
    } catch (err) {
      setError(prev => ({ ...prev, models: err.message }));
    } finally {
      setLoading(prev => ({ ...prev, models: false }));
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
    }));
  };

  const applyFilters = () => {
    fetchData();
  };

  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const sortedModelData = React.useMemo(() => {
    if (!modelData || !sortConfig.key) return modelData;

    return [...modelData].sort((a, b) => {
      if (a[sortConfig.key] < b[sortConfig.key]) {
        return sortConfig.direction === 'asc' ? -1 : 1;
      }
      if (a[sortConfig.key] > b[sortConfig.key]) {
        return sortConfig.direction === 'asc' ? 1 : -1;
      }
      return 0;
    });
  }, [modelData, sortConfig]);

  const StatCard = ({ title, value, icon: Icon, loading, error }) => (
    <div className="bg-gray-800 rounded-lg p-6 shadow-lg">
      {loading ? (
        <div className="animate-pulse">
          <div className="h-4 bg-gray-700 rounded w-1/2 mb-2"></div>
          <div className="h-8 bg-gray-700 rounded"></div>
        </div>
      ) : error ? (
        <div className="text-red-500 text-sm">{error}</div>
      ) : (
        <>
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-gray-400 text-sm">{title}</h3>
            <Icon className="w-5 h-5 text-gray-500" />
          </div>
          <p className="text-2xl font-bold text-white">{value}</p>
        </>
      )}
    </div>
  );

  const processChartData = () => {
    if (!chartData) return [];
    
    return chartData.map(point => ({
      ...point,
      divergence: point.actual - point.predicted,
    }));
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Navigation Sidebar */}
      <nav className="fixed left-0 top-0 h-full w-64 bg-gray-800 p-4">
        <div className="space-y-2">
          <Link
            to="/predictions"
            className={`flex items-center space-x-2 px-4 py-2 rounded ${
              location.pathname === '/predictions'
                ? 'bg-blue-600 text-white'
                : 'text-gray-300 hover:bg-gray-700'
            }`}
          >
            <span>🎯</span>
            <span>Predictions</span>
          </Link>
        </div>
      </nav>

      {/* Main Content */}
      <div className="ml-64 p-8">
        <h1 className="text-3xl font-bold mb-8">Prediction Dashboard</h1>

        {/* Filter Panel */}
        <div className="bg-gray-800 rounded-lg p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            <Filter className="w-5 h-5 mr-2" />
            Filters
          </h2>
          <div className="grid grid-cols-5 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Domain</label>
              <select
                value={filters.domain}
                onChange={(e) => handleFilterChange('domain', e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
              >
                <option value="">All Domains</option>
                <option value="healthcare">Healthcare</option>
                <option value="finance">Finance</option>
                <option value="retail">Retail</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Variable Pair</label>
              <select
                value={filters.variablePair}
                onChange={(e) => handleFilterChange('variablePair', e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
              >
                <option value="">All Pairs</option>
                <option value="temp-sales">Temperature - Sales</option>
                <option value="price-demand">Price - Demand</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Date Range</label>
              <div className="flex space-x-2">
                <input
                  type="date"
                  value={filters.dateRange.start}
                  onChange={(e) => handleFilterChange('dateRange', { ...filters.dateRange, start: e.target.value })}
                  className="flex-1 bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                />
                <input
                  type="date"
                  value={filters.dateRange.end}
                  onChange={(e) => handleFilterChange('dateRange', { ...filters.dateRange, end: e.target.value })}
                  className="flex-1 bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Model</label>
              <select
                value={filters.model}
                onChange={(e) => handleFilterChange('model', e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
              >
                <option value="">All Models</option>
                <option value="linear">Linear Regression</option>
                <option value="neural">Neural Network</option>
                <option value="ensemble">Ensemble</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Confidence</label>
              <select
                value={filters.confidence}
                onChange={(e) => handleFilterChange('confidence', e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
              >
                <option value="">All Levels</option>
                <option value="high">High (&gt;90%)</option>
                <option value="medium">Medium (70-90%)</option>
                <option value="low">Low (&lt;70%)</option>
              </select>
            </div>
          </div>
          <button
            onClick={applyFilters}
            className="mt-4 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded"
          >
            Apply Filters
          </button>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-4 gap-6 mb-8">
          <StatCard
            title="Mean Absolute Error"
            value={summaryStats?.mae || '0.00'}
            icon={TrendingUp}
            loading={loading.summary}
            error={error.summary}
          />
          <StatCard
            title="R² Score"
            value={summaryStats?.r2 || '0.00'}
            icon={TrendingUp}
            loading={loading.summary}
            error={error.summary}
          />
          <StatCard
            title="RMSE"
            value={summaryStats?.rmse || '0.00'}
            icon={TrendingUp}
            loading={loading.summary}
            error={error.summary}
          />
          <StatCard
            title="Accuracy %"
            value={summaryStats?.accuracy || '0.0%'}
            icon={TrendingUp}
            loading={loading.summary}
            error={error.summary}
          />
        </div>

        {/* Prediction vs Actual Chart */}
        <div className="bg-gray-800 rounded-lg p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Predictions vs Actual Values</h2>
          {loading.chart ? (
            <div className="h-96 flex items-center justify-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          ) : error.chart ? (
            <div className="h-96 flex items-center justify-center text-red-500">
              <AlertCircle className="w-6 h-6 mr-2" />
              {error.chart}
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={400}>
              <ComposedChart data={processChartData()}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="date" stroke="#9CA3AF" />
                <YAxis stroke="#9CA3AF" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1F2937', border: 'none' }}
                  labelStyle={{ color: '#9CA3AF' }}
                />
                <Legend />
                <Area
                  dataKey="divergence"
                  fill={(data) => data.divergence > 0 ? '#10B981' : '#EF4444'}
                  fillOpacity={0.3}
                  stroke="none"
                />
                <Line
                  type="monotone"
                  dataKey="predicted"
                  stroke="#3B82F6"
                  strokeDasharray="5 5"
                  name="Predicted"
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="actual"
                  stroke="#10B981"
                  name="Actual"
                  strokeWidth={2}
                />
              </ComposedChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Model Comparison Table */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Model Performance Comparison</h2>
          {loading.models ? (
            <div className="h-64 flex items-center justify-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          ) : error.models ? (
            <div className="h-64 flex items-center justify-center text-red-500">
              <AlertCircle className="w-6 h-6 mr-2" />
              {error.models}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-700">
                    <th
                      className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider cursor-pointer hover:text-white"
                      onClick={() => handleSort('name')}
                    >
                      Model Name
                    </th>
                    <th
                      className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider cursor-pointer hover:text-white"
                      onClick={() => handleSort('accuracy')}
                    >
                      Accuracy
                    </th>
                    <th
                      className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider cursor-pointer hover:text-white"
                      onClick={() => handleSort('mae')}
                    >
                      MAE
                    </th>
                    <th
                      className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider cursor-pointer hover:text-white"
                      onClick={() => handleSort('rmse')}
                    >
                      RMSE
                    </th>
                    <th
                      className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider cursor-pointer hover:text-white"
                      onClick={() => handleSort('r2')}
                    >
                      R² Score
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {sortedModelData?.map((model, index) => (
                    <tr
                      key={index}
                      className={`border-b border-gray-700 ${
                        model.isBest ? 'bg-blue-900 bg-opacity-20' : ''
                      }`}
                    >
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-white">
                        {model.name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                        {model.accuracy}%
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                        {model.mae}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                        {model.rmse}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                        {model.r2}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PredictionDashboard;
