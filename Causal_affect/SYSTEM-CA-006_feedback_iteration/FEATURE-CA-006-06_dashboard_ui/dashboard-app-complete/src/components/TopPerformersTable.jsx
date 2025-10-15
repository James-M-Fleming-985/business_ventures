import React from 'react'
import { useNavigate } from 'react-router-dom'
import { TrendingUp } from 'lucide-react'

export default function TopPerformersTable({ mvps }) {
  const navigate = useNavigate()
  
  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600 bg-green-50'
    if (score >= 60) return 'text-blue-600 bg-blue-50'
    return 'text-yellow-600 bg-yellow-50'
  }
  
  const getTrendArrows = (growth) => {
    const count = growth > 100 ? 3 : growth > 50 ? 2 : 1
    return '↗️'.repeat(count)
  }
  
  return (
    <div className="bg-white rounded-lg shadow mb-8">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">
            🎯 Top Performers (Priority Score &gt; 75)
          </h2>
          <button className="text-sm text-blue-600 hover:text-blue-700">
            View All Top 25 →
          </button>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rank</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">MVP Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Score</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">DAU</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Revenue</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Growth</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Trend</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {mvps.map((mvp, index) => (
              <tr 
                key={mvp.id}
                onClick={() => navigate(`/mvp/${mvp.id}`)}
                className="hover:bg-gray-50 cursor-pointer"
              >
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  {index === 0 && '🥇'}
                  {index === 1 && '🥈'}
                  {index === 2 && '🥉'}
                  {index > 2 && (index + 1)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">{mvp.name}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex px-3 py-1 text-sm font-semibold rounded-full ${getScoreColor(mvp.score)}`}>
                    {mvp.score}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {mvp.dau.toLocaleString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  ${mvp.revenue.toLocaleString()}/d
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600">
                  +{mvp.growth}%
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  {getTrendArrows(mvp.growth)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}