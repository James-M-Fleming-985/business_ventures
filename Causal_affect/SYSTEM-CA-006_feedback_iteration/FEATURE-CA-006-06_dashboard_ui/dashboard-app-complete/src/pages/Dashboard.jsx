import React from 'react'
import { RefreshCw } from 'lucide-react'
import PortfolioStatsGrid from '../components/PortfolioStatsGrid'
import TopPerformersTable from '../components/TopPerformersTable'
import ArchiveCandidatesTable from '../components/ArchiveCandidatesTable'
import PortfolioTrendsChart from '../components/PortfolioTrendsChart'

// Sample data matching UI_VISUALIZATION.md
const portfolioStats = [
  { label: 'Total MVPs', value: '47', change: 3, changeText: '+3 (7d)' },
  { label: 'Active MVPs', value: '42', change: 2, changeText: '+2 (7d)' },
  { label: 'High Priority', value: '12', change: 1, changeText: '+1 (7d)' },
  { label: 'Archive Queue', value: '3', change: -1, changeText: '-1 (7d)' },
  { label: 'Total Revenue', value: '$127,450', change: 12300, changeText: '+$12.3K (7d)' },
]

const topPerformers = [
  { id: 1, name: 'TaskFlow Pro', score: 92, dau: 1247, revenue: 4231, growth: 127 },
  { id: 2, name: 'MealPlan AI', score: 88, dau: 892, revenue: 3102, growth: 89 },
  { id: 3, name: 'FitTracker Plus', score: 84, dau: 1891, revenue: 2847, growth: 67 },
  { id: 4, name: 'BudgetBuddy', score: 81, dau: 634, revenue: 1923, growth: 52 },
  { id: 5, name: 'LearnPath', score: 78, dau: 421, revenue: 1654, growth: 48 },
]

const archiveCandidates = [
  { id: 101, name: 'QuickNote App', score: 7, dau: 12, revenue: 0, lastActivity: '45 days ago' },
  { id: 102, name: 'EventFinder', score: 5, dau: 8, revenue: 0, lastActivity: '61 days ago' },
  { id: 103, name: 'ColorSchemer', score: 3, dau: 3, revenue: 0, lastActivity: '89 days ago' },
]

// Generate 30 days of trend data
const generateTrendData = () => {
  const data = []
  for (let i = 30; i >= 0; i--) {
    const date = new Date()
    date.setDate(date.getDate() - i)
    data.push({
      date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      dau: 3000 + Math.random() * 2000 + (30 - i) * 50,
      revenue: 8000 + Math.random() * 4000 + (30 - i) * 100,
    })
  }
  return data
}

const trendData = generateTrendData()

export default function Dashboard() {
  const [lastUpdated, setLastUpdated] = React.useState(new Date())
  
  React.useEffect(() => {
    const interval = setInterval(() => {
      setLastUpdated(new Date())
    }, 30000) // 30 seconds
    
    return () => clearInterval(interval)
  }, [])
  
  const secondsAgo = Math.floor((new Date() - lastUpdated) / 1000)
  
  return (
    <div>
      {/* Header with refresh indicator */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">📊 Portfolio Overview</h1>
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <RefreshCw className="w-4 h-4" />
          <span>Last updated: {secondsAgo}s ago</span>
        </div>
      </div>
      
      {/* Portfolio Stats */}
      <PortfolioStatsGrid stats={portfolioStats} />
      
      {/* Top Performers */}
      <TopPerformersTable mvps={topPerformers} />
      
      {/* Archive Candidates */}
      <ArchiveCandidatesTable candidates={archiveCandidates} />
      
      {/* Trends */}
      <PortfolioTrendsChart data={trendData} />
    </div>
  )
}