import React from 'react'
import { TrendingUp, TrendingDown } from 'lucide-react'

export default function PortfolioStatsGrid({ stats }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
      {stats.map((stat, index) => (
        <div key={index} className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600 mb-1">{stat.label}</div>
          <div className="text-3xl font-bold text-gray-900 mb-2">
            {stat.value}
          </div>
          <div className={`flex items-center text-sm ${
            stat.change >= 0 ? 'text-green-600' : 'text-red-600'
          }`}>
            {stat.change >= 0 ? (
              <TrendingUp className="w-4 h-4 mr-1" />
            ) : (
              <TrendingDown className="w-4 h-4 mr-1" />
            )}
            <span>{stat.changeText}</span>
          </div>
        </div>
      ))}
    </div>
  )
}