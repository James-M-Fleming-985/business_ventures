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
      
      {/* Conversion Funnel */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Conversion Funnel</h2>
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
                  style={{ width: `${stage.percent * 10}%` }}
                >
                  {stage.percent >= 10 && (
                    <span className="text-xs text-white font-medium">{stage.percent}%</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}