import React from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, TrendingUp, DollarSign, Users, Activity } from 'lucide-react'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export default function MVPDetail() {
  const { id } = useParams()
  
  // Sample data for the selected MVP
  const mvp = {
    id,
    name: id === '1' ? 'TaskFlow Pro' : id === '2' ? 'MealPlan AI' : 'FitTracker Plus',
    score: id === '1' ? 92 : id === '2' ? 88 : 84,
    dau: id === '1' ? 1247 : id === '2' ? 892 : 1891,
    revenue: id === '1' ? 4231 : id === '2' ? 3102 : 2847,
  }
  
  const metrics = [
    { label: 'DAU', value: mvp.dau.toLocaleString(), icon: Users, change: '+12%', color: 'blue' },
    { label: 'Revenue/Day', value: `$${mvp.revenue}`, icon: DollarSign, change: '+18%', color: 'green' },
    { label: 'Priority Score', value: mvp.score, icon: TrendingUp, change: '+3 pts', color: 'purple' },
    { label: 'Active Sessions', value: '3,421', icon: Activity, change: '+8%', color: 'orange' },
  ]
  
  const scoreBreakdown = [
    { dimension: 'Engagement', score: 94, weight: 30, color: '#3B82F6' },
    { dimension: 'Revenue', score: 88, weight: 35, color: '#10B981' },
    { dimension: 'Growth', score: 92, weight: 25, color: '#F59E0B' },
    { dimension: 'Potential', score: 85, weight: 10, color: '#8B5CF6' },
  ]
  
  const engagementData = Array.from({ length: 30 }, (_, i) => ({
    date: `Day ${i + 1}`,
    value: 800 + Math.random() * 400 + i * 15,
  }))
  
  return (
    <div>
      {/* Breadcrumb */}
      <div className="mb-6">
        <Link to="/" className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Portfolio
        </Link>
      </div>
      
      {/* MVP Header */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">{mvp.name}</h1>
        <p className="text-gray-600">Detailed analytics and performance metrics</p>
      </div>
      
      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        {metrics.map((metric, index) => {
          const Icon = metric.icon
          return (
            <div key={index} className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">{metric.label}</span>
                <Icon className={`w-5 h-5 text-${metric.color}-600`} />
              </div>
              <div className="text-2xl font-bold text-gray-900 mb-1">{metric.value}</div>
              <div className="text-sm text-green-600">{metric.change}</div>
            </div>
          )
        })}
      </div>
      
      {/* Score Breakdown */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Priority Score Breakdown</h2>
        <div className="space-y-4">
          {scoreBreakdown.map((item, index) => (
            <div key={index}>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-700">{item.dimension}</span>
                  <span className="text-xs text-gray-500">({item.weight}% weight)</span>
                </div>
                <span className="text-sm font-semibold text-gray-900">{item.score}/100</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="h-2 rounded-full"
                  style={{ width: `${item.score}%`, backgroundColor: item.color }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Engagement Trend */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Engagement Trend (30 Days)</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={engagementData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" fontSize={12} />
            <YAxis fontSize={12} />
            <Tooltip />
            <Line type="monotone" dataKey="value" stroke="#3B82F6" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      
      {/* Revenue Metrics */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">💰 Revenue Metrics</h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {[
            { label: 'Revenue/Day', value: `$${mvp.revenue}`, change: '+23.4%' },
            { label: 'Conv Rate', value: '4.2%', change: '+0.8%' },
            { label: 'AOV', value: '$29.99', change: '+2.1%' },
            { label: 'LTV:CAC', value: '3.2:1', change: '+0.3' },
            { label: 'MRR', value: '$89,234', change: '+18.2%' },
          ].map((metric, index) => (
            <div key={index} className="text-center">
              <div className="text-sm text-gray-600 mb-1">{metric.label}</div>
              <div className="text-xl font-bold text-gray-900">{metric.value}</div>
              <div className="text-xs text-green-600">{metric.change} ↗️</div>
            </div>
          ))}
        </div>
      </div>

      {/* Traffic Sources */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">📍 Traffic Sources</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left py-2 text-sm font-medium text-gray-700">Source</th>
                <th className="text-right py-2 text-sm font-medium text-gray-700">Users</th>
                <th className="text-right py-2 text-sm font-medium text-gray-700">Conv Rate</th>
                <th className="text-right py-2 text-sm font-medium text-gray-700">Revenue</th>
                <th className="text-right py-2 text-sm font-medium text-gray-700">ROI</th>
              </tr>
            </thead>
            <tbody>
              {[
                { source: 'Google Ads', users: 547, convRate: '5.2%', revenue: '$1,847/d', roi: '4.8x' },
                { source: 'Facebook', users: 412, convRate: '3.8%', revenue: '$1,234/d', roi: '2.1x' },
                { source: 'Organic', users: 188, convRate: '6.1%', revenue: '$892/d', roi: '∞' },
                { source: 'Reddit', users: 78, convRate: '2.9%', revenue: '$189/d', roi: '3.1x' },
                { source: 'Direct', users: 22, convRate: '4.5%', revenue: '$69/d', roi: '∞' },
              ].map((row, index) => (
                <tr key={index} className="border-b hover:bg-gray-50">
                  <td className="py-3 text-sm font-medium text-gray-900">{row.source}</td>
                  <td className="py-3 text-sm text-right text-gray-700">{row.users}</td>
                  <td className="py-3 text-sm text-right text-gray-700">{row.convRate}</td>
                  <td className="py-3 text-sm text-right text-gray-700">{row.revenue}</td>
                  <td className="py-3 text-sm text-right font-medium text-green-600">{row.roi}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Conversion Funnel */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">🎯 Conversion Funnel</h2>
        <div className="space-y-2">
          {[
            { stage: 'Impressions', value: 10000, percent: 100 },
            { stage: 'Clicks', value: 2000, percent: 20 },
            { stage: 'Signups', value: 500, percent: 5 },
            { stage: 'Active Users', value: 250, percent: 2.5 },
            { stage: 'Paying Users', value: 100, percent: 1 },
          ].map((stage, index) => (
            <div key={index}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium text-gray-700">{stage.stage}</span>
                <span className="text-sm text-gray-900">
                  {stage.value.toLocaleString()} ({stage.percent}%)
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-6">
                <div
                  className="h-6 rounded-full bg-blue-600 flex items-center justify-end pr-2"
                  style={{ width: `${Math.min(stage.percent, 100)}%` }}
                >
                  {stage.percent >= 5 && (
                    <span className="text-xs text-white font-medium">{stage.percent}%</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
          <p className="text-sm text-yellow-800">
            <span className="font-semibold">⚠️ Drop-off Analysis:</span> Click to Visit: 77% drop (expected 50-70%, needs improvement)
          </p>
        </div>
      </div>

      {/* Recent Events */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">🎬 Recent Events (Live Feed)</h2>
        <div className="space-y-2">
          {[
            { time: '15s ago', event: 'New signup from Google Ads (San Francisco, CA)', color: 'green' },
            { time: '42s ago', event: 'Purchase completed - $29.99 (Returning customer)', color: 'blue' },
            { time: '1m ago', event: 'Session started (Mobile, iOS 17, Chrome)', color: 'gray' },
            { time: '2m ago', event: 'Trial started (Email: user***@gmail.com)', color: 'purple' },
            { time: '3m ago', event: 'Page view: /pricing (Desktop, Chrome, USA)', color: 'gray' },
          ].map((item, index) => (
            <div key={index} className="flex items-start gap-3 p-2 hover:bg-gray-50 rounded">
              <span className={`text-xs font-medium text-${item.color}-600 mt-0.5`}>{item.time}</span>
              <span className="text-sm text-gray-700 flex-1">{item.event}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">🔧 Actions</h2>
        <div className="flex flex-wrap gap-3">
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
            🚀 Prioritize for Iteration
          </button>
          <button className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition">
            📊 View Full Analytics
          </button>
          <button className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition">
            ⚙️ MVP Settings
          </button>
          <button className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition">
            📦 Archive MVP
          </button>
        </div>
      </div>
    </div>
  )
}