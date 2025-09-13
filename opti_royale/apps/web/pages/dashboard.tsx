import React, { useState } from 'react';
import { 
  Trophy, 
  Target, 
  Users, 
  TrendingUp,
  Award,
  Crown,
  BarChart3,
  Zap
} from 'lucide-react';
import { useRouter } from 'next/router';
import Leaderboard from '../components/Leaderboard';
import AchievementsPanel from '../components/AchievementsPanel';
import UserProfile from '../components/UserProfile';
import VideoAnalysisInterface from '../components/VideoAnalysisInterface';

interface DashboardStats {
  totalUsers: number;
  activeUsers: number;
  totalAnalyses: number;
  averageAccuracy: number;
  topPerformers: Array<{
    id: string;
    username: string;
    rating: number;
    accuracy: number;
  }>;
}

const Dashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'overview' | 'analysis' | 'leaderboard' | 'achievements' | 'profile'>('overview');
  const router = useRouter();
  const [stats] = useState<DashboardStats>({
    totalUsers: 15247,
    activeUsers: 3841,
    totalAnalyses: 89523,
    averageAccuracy: 78.4,
    topPerformers: [
      { id: '1', username: 'CardMaster', rating: 2847, accuracy: 94.2 },
      { id: '2', username: 'OptiPro', rating: 2756, accuracy: 91.8 },
      { id: '3', username: 'DeckWizard', rating: 2689, accuracy: 89.5 }
    ]
  });

  const tabConfig = [
    {
      id: 'overview',
      label: 'Overview',
      icon: <BarChart3 className="w-4 h-4" />,
      component: <OverviewTab stats={stats} />
    },
    {
      id: 'analysis',
      label: 'Video Analysis',
      icon: <Zap className="w-4 h-4" />,
      component: null, // Will be handled by direct navigation
      onClick: () => router.push('/battle-analysis')
    },
    {
      id: 'leaderboard',
      label: 'Leaderboard',
      icon: <Trophy className="w-4 h-4" />,
      component: <Leaderboard />
    },
    {
      id: 'achievements',
      label: 'Achievements',
      icon: <Award className="w-4 h-4" />,
      component: <AchievementsPanel />
    },
    {
      id: 'profile',
      label: 'Profile',
      icon: <Users className="w-4 h-4" />,
      component: <UserProfile />
    }
  ];

  return (
    <div style={{ 
      minHeight: '100vh', 
      background: 'linear-gradient(135deg, #1e3a8a, #7c3aed, #1e40af)',
      color: 'white'
    }}>
      {/* Header */}
      <header style={{ 
        background: 'linear-gradient(90deg, #1e40af, #7c3aed)', 
        borderBottom: '2px solid #fbbf24',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
      }}>
        <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '0 16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: '64px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <Crown style={{ width: '32px', height: '32px', color: '#fbbf24' }} />
              <h1 style={{ fontSize: '24px', fontWeight: 'bold', color: 'white', margin: 0 }}>Opti Royale</h1>
              <span style={{ 
                fontSize: '14px', 
                color: '#fde047', 
                background: 'rgba(251, 191, 36, 0.2)', 
                padding: '4px 8px', 
                borderRadius: '4px',
                border: '1px solid #fbbf24'
              }}>
                Clash Royale Analysis Platform
              </span>
            </div>
            
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '14px', color: '#fde047' }}>Welcome back!</div>
                <div style={{ fontWeight: '600', color: 'white' }}>DeckOptimizer</div>
              </div>
              <div style={{ 
                width: '40px', 
                height: '40px', 
                background: 'linear-gradient(135deg, #fbbf24, #f59e0b)', 
                borderRadius: '50%', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center', 
                color: 'black', 
                fontWeight: 'bold' 
              }}>
                D
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav style={{ 
        background: 'linear-gradient(90deg, #1e40af, #7c3aed)', 
        borderBottom: '1px solid rgba(251, 191, 36, 0.3)' 
      }}>
        <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '0 16px' }}>
          <div style={{ display: 'flex', gap: '32px' }}>
            {tabConfig.map(tab => (
              <button
                key={tab.id}
                onClick={() => {
                  if (tab.onClick) {
                    tab.onClick();
                  } else {
                    setActiveTab(tab.id as any);
                  }
                }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '16px 4px',
                  borderBottom: activeTab === tab.id ? '2px solid #fbbf24' : '2px solid transparent',
                  background: 'none',
                  border: 'none',
                  color: activeTab === tab.id ? '#fde047' : '#d1d5db',
                  fontWeight: '500',
                  fontSize: '14px',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main style={{ maxWidth: '1280px', margin: '0 auto', padding: '32px 16px' }}>
        {tabConfig.find(tab => tab.id === activeTab)?.component}
      </main>
    </div>
  );
};

// Overview Tab Component
const OverviewTab: React.FC<{ stats: DashboardStats }> = ({ stats }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      {/* Stats Cards */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', 
        gap: '24px' 
      }}>
        <div style={{ 
          background: 'linear-gradient(135deg, #2563eb, #1d4ed8)', 
          borderRadius: '8px', 
          padding: '24px', 
          border: '2px solid #fbbf24',
          boxShadow: '0 10px 15px rgba(0, 0, 0, 0.1)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <div style={{ 
              padding: '8px', 
              background: 'rgba(251, 191, 36, 0.2)', 
              borderRadius: '8px' 
            }}>
              <Users style={{ width: '24px', height: '24px', color: '#fde047' }} />
            </div>
            <div style={{ marginLeft: '16px' }}>
              <p style={{ fontSize: '14px', color: '#fef3c7', margin: 0 }}>Total Users</p>
              <p style={{ fontSize: '24px', fontWeight: '600', color: 'white', margin: 0 }}>
                {stats.totalUsers.toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        <div style={{ 
          background: 'linear-gradient(135deg, #059669, #047857)', 
          borderRadius: '8px', 
          padding: '24px', 
          border: '2px solid #fbbf24',
          boxShadow: '0 10px 15px rgba(0, 0, 0, 0.1)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <div style={{ 
              padding: '8px', 
              background: 'rgba(251, 191, 36, 0.2)', 
              borderRadius: '8px' 
            }}>
              <Zap style={{ width: '24px', height: '24px', color: '#fde047' }} />
            </div>
            <div style={{ marginLeft: '16px' }}>
              <p style={{ fontSize: '14px', color: '#fef3c7', margin: 0 }}>Active Users</p>
              <p style={{ fontSize: '24px', fontWeight: '600', color: 'white', margin: 0 }}>
                {stats.activeUsers.toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        <div style={{ 
          background: 'linear-gradient(135deg, #7c3aed, #6d28d9)', 
          borderRadius: '8px', 
          padding: '24px', 
          border: '2px solid #fbbf24',
          boxShadow: '0 10px 15px rgba(0, 0, 0, 0.1)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <div style={{ 
              padding: '8px', 
              background: 'rgba(251, 191, 36, 0.2)', 
              borderRadius: '8px' 
            }}>
              <BarChart3 style={{ width: '24px', height: '24px', color: '#fde047' }} />
            </div>
            <div style={{ marginLeft: '16px' }}>
              <p style={{ fontSize: '14px', color: '#fef3c7', margin: 0 }}>Total Analyses</p>
              <p style={{ fontSize: '24px', fontWeight: '600', color: 'white', margin: 0 }}>
                {stats.totalAnalyses.toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        <div style={{ 
          background: 'linear-gradient(135deg, #ea580c, #dc2626)', 
          borderRadius: '8px', 
          padding: '24px', 
          border: '2px solid #fbbf24',
          boxShadow: '0 10px 15px rgba(0, 0, 0, 0.1)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <div style={{ 
              padding: '8px', 
              background: 'rgba(251, 191, 36, 0.2)', 
              borderRadius: '8px' 
            }}>
              <Target style={{ width: '24px', height: '24px', color: '#fde047' }} />
            </div>
            <div style={{ marginLeft: '16px' }}>
              <p style={{ fontSize: '14px', color: '#fef3c7', margin: 0 }}>Avg Accuracy</p>
              <p style={{ fontSize: '24px', fontWeight: '600', color: 'white', margin: 0 }}>
                {stats.averageAccuracy}%
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Features - Quick Actions (Most Prominent) */}
      <div style={{ marginBottom: '32px' }}>
        <h2 style={{ 
          fontSize: '20px', 
          fontWeight: 'bold', 
          color: '#fbbf24', 
          marginBottom: '16px',
          textAlign: 'center' 
        }}>
          🎮 Main Features
        </h2>
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', 
          gap: '16px' 
        }}>
          <button style={{
            background: 'linear-gradient(135deg, #2563eb, #1d4ed8)',
            border: '2px solid #fbbf24',
            borderRadius: '12px',
            padding: '20px',
            color: 'white',
            textAlign: 'left',
            cursor: 'pointer',
            boxShadow: '0 8px 25px rgba(37, 99, 235, 0.3)',
            transition: 'all 0.3s ease',
            display: 'flex',
            alignItems: 'center',
            gap: '16px'
          }}>
            <div style={{ 
              padding: '12px', 
              background: 'rgba(251, 191, 36, 0.2)', 
              borderRadius: '10px' 
            }}>
              <Target style={{ width: '24px', height: '24px', color: '#fbbf24' }} />
            </div>
            <div>
              <div style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '4px' }}>Start New Analysis</div>
              <div style={{ fontSize: '14px', color: '#cbd5e1' }}>Upload gameplay video for AI analysis</div>
            </div>
          </button>

          <button style={{
            background: 'linear-gradient(135deg, #059669, #047857)',
            border: '2px solid #fbbf24',
            borderRadius: '12px',
            padding: '20px',
            color: 'white',
            textAlign: 'left',
            cursor: 'pointer',
            boxShadow: '0 8px 25px rgba(5, 150, 105, 0.3)',
            transition: 'all 0.3s ease',
            display: 'flex',
            alignItems: 'center',
            gap: '16px'
          }}>
            <div style={{ 
              padding: '12px', 
              background: 'rgba(251, 191, 36, 0.2)', 
              borderRadius: '10px' 
            }}>
              <Trophy style={{ width: '24px', height: '24px', color: '#fbbf24' }} />
            </div>
            <div>
              <div style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '4px' }}>View Leaderboard</div>
              <div style={{ fontSize: '14px', color: '#cbd5e1' }}>Check your global ranking</div>
            </div>
          </button>

          <button style={{
            background: 'linear-gradient(135deg, #7c3aed, #6d28d9)',
            border: '2px solid #fbbf24',
            borderRadius: '12px',
            padding: '20px',
            color: 'white',
            textAlign: 'left',
            cursor: 'pointer',
            boxShadow: '0 8px 25px rgba(124, 58, 237, 0.3)',
            transition: 'all 0.3s ease',
            display: 'flex',
            alignItems: 'center',
            gap: '16px'
          }}>
            <div style={{ 
              padding: '12px', 
              background: 'rgba(251, 191, 36, 0.2)', 
              borderRadius: '10px' 
            }}>
              <Award style={{ width: '24px', height: '24px', color: '#fbbf24' }} />
            </div>
            <div>
              <div style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '4px' }}>Check Achievements</div>
              <div style={{ fontSize: '14px', color: '#cbd5e1' }}>View your progress & rewards</div>
            </div>
          </button>

          <button style={{
            background: 'linear-gradient(135deg, #ea580c, #dc2626)',
            border: '2px solid #fbbf24',
            borderRadius: '12px',
            padding: '20px',
            color: 'white',
            textAlign: 'left',
            cursor: 'pointer',
            boxShadow: '0 8px 25px rgba(234, 88, 12, 0.3)',
            transition: 'all 0.3s ease',
            display: 'flex',
            alignItems: 'center',
            gap: '16px'
          }}>
            <div style={{ 
              padding: '12px', 
              background: 'rgba(251, 191, 36, 0.2)', 
              borderRadius: '10px' 
            }}>
              <TrendingUp style={{ width: '24px', height: '24px', color: '#fbbf24' }} />
            </div>
            <div>
              <div style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '4px' }}>View Statistics</div>
              <div style={{ fontSize: '14px', color: '#cbd5e1' }}>Analyze your performance data</div>
            </div>
          </button>
        </div>
      </div>

      {/* Secondary Information - Compact Layout */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', 
        gap: '24px' 
      }}>
        {/* Top Performers - Compact Card */}
        <div style={{ 
          background: 'linear-gradient(135deg, #334155, #1e293b)',
          border: '2px solid #fbbf24',
          borderRadius: '12px',
          overflow: 'hidden',
          boxShadow: '0 8px 25px rgba(0, 0, 0, 0.2)'
        }}>
          <div style={{ 
            padding: '16px 20px', 
            borderBottom: '1px solid rgba(251, 191, 36, 0.3)',
            background: 'rgba(251, 191, 36, 0.1)'
          }}>
            <h3 style={{ 
              fontSize: '16px', 
              fontWeight: 'bold', 
              color: '#fbbf24', 
              margin: 0,
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <Trophy style={{ width: '20px', height: '20px' }} />
              🏆 Top Performers
            </h3>
          </div>
          <div style={{ padding: '16px 20px' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {stats.topPerformers.slice(0, 3).map((performer, index) => (
                <div key={performer.id} style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'space-between',
                  padding: '8px 0'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{
                      width: '32px',
                      height: '32px',
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'black',
                      fontWeight: 'bold',
                      fontSize: '14px',
                      background: index === 0 ? '#fbbf24' : 
                                 index === 1 ? '#9ca3af' : '#ea580c'
                    }}>
                      {index + 1}
                    </div>
                    <div>
                      <div style={{ color: 'white', fontWeight: '600', fontSize: '14px' }}>
                        {performer.username}
                      </div>
                      <div style={{ color: '#94a3b8', fontSize: '12px' }}>
                        {performer.accuracy}% accuracy
                      </div>
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ color: '#fbbf24', fontWeight: 'bold', fontSize: '14px' }}>
                      {performer.rating}
                    </div>
                    <div style={{ color: '#94a3b8', fontSize: '12px' }}>rating</div>
                  </div>
                </div>
              ))}
            </div>
            <button style={{
              width: '100%',
              marginTop: '12px',
              padding: '8px',
              background: 'rgba(251, 191, 36, 0.1)',
              border: '1px solid #fbbf24',
              borderRadius: '6px',
              color: '#fbbf24',
              fontSize: '12px',
              cursor: 'pointer'
            }}>
              View Full Leaderboard →
            </button>
          </div>
        </div>

        {/* Recent Activity - Compact Card */}
        <div style={{ 
          background: 'linear-gradient(135deg, #334155, #1e293b)',
          border: '2px solid #fbbf24',
          borderRadius: '12px',
          overflow: 'hidden',
          boxShadow: '0 8px 25px rgba(0, 0, 0, 0.2)'
        }}>
          <div style={{ 
            padding: '16px 20px', 
            borderBottom: '1px solid rgba(251, 191, 36, 0.3)',
            background: 'rgba(251, 191, 36, 0.1)'
          }}>
            <h3 style={{ 
              fontSize: '16px', 
              fontWeight: 'bold', 
              color: '#fbbf24', 
              margin: 0,
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              ⚡ Recent Activity
            </h3>
          </div>
          <div style={{ padding: '16px 20px' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {[
                { action: 'Completed deck analysis', time: '2 min ago', accuracy: '89.3%' },
                { action: 'Unlocked achievement', time: '1 hr ago', xp: '+50 XP' },
                { action: 'Climbed to rank #1,247', time: '3 hrs ago', change: '+15' }
              ].map((activity, index) => (
                <div key={index} style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'space-between',
                  padding: '8px 0'
                }}>
                  <div>
                    <div style={{ color: 'white', fontSize: '14px', fontWeight: '500' }}>
                      {activity.action}
                    </div>
                    <div style={{ color: '#94a3b8', fontSize: '12px' }}>
                      {activity.time}
                    </div>
                  </div>
                  <div style={{ 
                    color: '#10b981', 
                    fontSize: '12px', 
                    fontWeight: 'bold',
                    background: 'rgba(16, 185, 129, 0.1)',
                    padding: '4px 8px',
                    borderRadius: '4px'
                  }}>
                    {activity.accuracy || activity.xp || activity.change}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
