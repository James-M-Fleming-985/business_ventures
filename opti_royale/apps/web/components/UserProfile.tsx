import React, { useState, useEffect } from 'react';
import { 
  User, 
  Trophy, 
  Target, 
  TrendingUp, 
  Calendar, 
  Award, 
  Star,
  BarChart3,
  Users,
  Settings,
  Edit3,
  Crown,
  Zap,
  Shield
} from 'lucide-react';

interface UserProfile {
  id: string;
  username: string;
  email: string;
  avatar?: string;
  level: number;
  xp: number;
  xpToNextLevel: number;
  rating: number;
  rank: number;
  tier: string;
  trophies: number;
  totalAnalyses: number;
  averageAccuracy: number;
  winRate: number;
  currentStreak: number;
  longestStreak: number;
  joinedAt: string;
  lastActive: string;
  achievements: {
    total: number;
    unlocked: number;
    recent: Array<{
      id: string;
      name: string;
      icon: string;
      unlockedAt: string;
    }>;
  };
  statistics: {
    totalPlaytime: number;
    favoriteCard: string;
    mostImprovedCard: string;
    weeklyProgress: Array<{
      week: string;
      analyses: number;
      accuracy: number;
    }>;
  };
}

interface UserProfileProps {
  userId?: string;
  isOwnProfile?: boolean;
}

export const UserProfile: React.FC<UserProfileProps> = ({ 
  userId, 
  isOwnProfile = true 
}) => {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'stats' | 'achievements'>('overview');

  useEffect(() => {
    fetchProfile();
  }, [userId]);

  const fetchProfile = async () => {
    try {
      setLoading(true);
      const endpoint = userId ? `/api/users/${userId}` : '/api/profile';
      const response = await fetch(endpoint);
      const data = await response.json();
      setProfile(data.profile);
    } catch (error) {
      console.error('Failed to fetch profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const getTierInfo = (tier: string) => {
    switch (tier.toLowerCase()) {
      case 'legendary':
        return { color: 'text-purple-600', bgColor: 'bg-purple-100', icon: <Crown className="w-5 h-5" /> };
      case 'master':
        return { color: 'text-blue-600', bgColor: 'bg-blue-100', icon: <Star className="w-5 h-5" /> };
      case 'champion':
        return { color: 'text-green-600', bgColor: 'bg-green-100', icon: <Trophy className="w-5 h-5" /> };
      case 'expert':
        return { color: 'text-orange-600', bgColor: 'bg-orange-100', icon: <Target className="w-5 h-5" /> };
      default:
        return { color: 'text-gray-600', bgColor: 'bg-gray-100', icon: <Shield className="w-5 h-5" /> };
    }
  };

  const formatPlaytime = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    if (days > 0) return `${days}d ${hours % 24}h`;
    if (hours > 0) return `${hours}h ${minutes % 60}m`;
    return `${minutes}m`;
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="animate-pulse space-y-6">
          <div className="flex items-center gap-4">
            <div className="w-20 h-20 bg-gray-200 rounded-full"></div>
            <div className="space-y-2">
              <div className="h-6 bg-gray-200 rounded w-32"></div>
              <div className="h-4 bg-gray-200 rounded w-24"></div>
            </div>
          </div>
          <div className="grid grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-16 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-12 text-center">
        <User className="w-16 h-16 mx-auto mb-4 text-gray-300" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Profile not found</h3>
        <p className="text-gray-600">This user profile could not be loaded.</p>
      </div>
    );
  }

  const tierInfo = getTierInfo(profile.tier);
  const xpPercent = ((profile.xp % 1000) / 1000) * 100; // Assuming 1000 XP per level

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Profile Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            {profile.avatar ? (
              <img 
                src={profile.avatar} 
                alt={profile.username}
                className="w-20 h-20 rounded-full border-4 border-white/20"
              />
            ) : (
              <div className="w-20 h-20 bg-white/20 rounded-full flex items-center justify-center border-4 border-white/20">
                <User className="w-10 h-10 text-white" />
              </div>
            )}
            
            <div>
              <div className="flex items-center gap-3 mb-2">
                <h1 className="text-2xl font-bold">{profile.username}</h1>
                {isOwnProfile && (
                  <button className="p-1 hover:bg-white/20 rounded">
                    <Edit3 className="w-4 h-4" />
                  </button>
                )}
              </div>
              
              <div className="flex items-center gap-2 mb-3">
                <div className={`flex items-center gap-1 px-3 py-1 rounded-full ${tierInfo.bgColor} ${tierInfo.color} bg-white/20 text-white`}>
                  {tierInfo.icon}
                  <span className="font-semibold">{profile.tier}</span>
                </div>
                <div className="text-white/80 text-sm">
                  Rank #{profile.rank.toLocaleString()}
                </div>
              </div>

              {/* Level & XP Progress */}
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-white/80">Level {profile.level}</span>
                  <div className="flex-1 bg-white/20 rounded-full h-2 max-w-48">
                    <div 
                      className="bg-white h-2 rounded-full transition-all duration-300"
                      style={{ width: `${xpPercent}%` }}
                    />
                  </div>
                  <span className="text-xs text-white/70">
                    {profile.xp % 1000}/{profile.xpToNextLevel}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {isOwnProfile && (
            <button className="p-2 hover:bg-white/20 rounded-lg transition-colors">
              <Settings className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>

      {/* Stats Overview */}
      <div className="p-6 border-b">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="flex items-center justify-center w-12 h-12 bg-blue-100 rounded-lg mx-auto mb-2">
              <Trophy className="w-6 h-6 text-blue-600" />
            </div>
            <div className="text-2xl font-bold text-gray-900">{profile.rating}</div>
            <div className="text-sm text-gray-600">Rating</div>
          </div>
          
          <div className="text-center">
            <div className="flex items-center justify-center w-12 h-12 bg-green-100 rounded-lg mx-auto mb-2">
              <Target className="w-6 h-6 text-green-600" />
            </div>
            <div className="text-2xl font-bold text-gray-900">{profile.averageAccuracy.toFixed(1)}%</div>
            <div className="text-sm text-gray-600">Accuracy</div>
          </div>
          
          <div className="text-center">
            <div className="flex items-center justify-center w-12 h-12 bg-purple-100 rounded-lg mx-auto mb-2">
              <BarChart3 className="w-6 h-6 text-purple-600" />
            </div>
            <div className="text-2xl font-bold text-gray-900">{profile.totalAnalyses}</div>
            <div className="text-sm text-gray-600">Analyses</div>
          </div>
          
          <div className="text-center">
            <div className="flex items-center justify-center w-12 h-12 bg-orange-100 rounded-lg mx-auto mb-2">
              <Zap className="w-6 h-6 text-orange-600" />
            </div>
            <div className="text-2xl font-bold text-gray-900">{profile.currentStreak}</div>
            <div className="text-sm text-gray-600">Win Streak</div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b">
        <nav className="flex">
          {[
            { id: 'overview', label: 'Overview', icon: <User className="w-4 h-4" /> },
            { id: 'stats', label: 'Statistics', icon: <BarChart3 className="w-4 h-4" /> },
            { id: 'achievements', label: 'Achievements', icon: <Award className="w-4 h-4" /> }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-6 py-3 border-b-2 font-medium text-sm transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="p-6">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Recent Achievements */}
            <div>
              <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                <Award className="w-5 h-5 text-yellow-600" />
                Recent Achievements
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {profile.achievements.recent.map(achievement => (
                  <div key={achievement.id} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                    <div className="w-10 h-10 bg-yellow-100 rounded-lg flex items-center justify-center">
                      <Award className="w-5 h-5 text-yellow-600" />
                    </div>
                    <div>
                      <div className="font-medium text-sm">{achievement.name}</div>
                      <div className="text-xs text-gray-600">
                        {new Date(achievement.unlockedAt).toLocaleDateString()}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Activity Summary */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-lg font-semibold mb-3">Activity</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Total Playtime</span>
                    <span className="font-medium">{formatPlaytime(profile.statistics.totalPlaytime)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Win Rate</span>
                    <span className="font-medium">{profile.winRate.toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Longest Streak</span>
                    <span className="font-medium">{profile.longestStreak} wins</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Joined</span>
                    <span className="font-medium">{new Date(profile.joinedAt).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold mb-3">Preferences</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Favorite Card</span>
                    <span className="font-medium">{profile.statistics.favoriteCard}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Most Improved</span>
                    <span className="font-medium">{profile.statistics.mostImprovedCard}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Achievements</span>
                    <span className="font-medium">{profile.achievements.unlocked}/{profile.achievements.total}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'stats' && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold">Detailed Statistics</h3>
            {/* Add detailed stats charts and graphs here */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium mb-3">Weekly Progress</h4>
                <div className="space-y-2">
                  {profile.statistics.weeklyProgress.map((week, index) => (
                    <div key={index} className="flex justify-between text-sm">
                      <span>{week.week}</span>
                      <span>{week.analyses} analyses • {week.accuracy.toFixed(1)}% accuracy</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium mb-3">Performance Metrics</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>Best Accuracy</span>
                    <span className="font-medium">98.5%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Average Session</span>
                    <span className="font-medium">12 analyses</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Peak Rating</span>
                    <span className="font-medium">{profile.rating + 150}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'achievements' && (
          <div>
            <h3 className="text-lg font-semibold mb-4">Achievement Progress</h3>
            <div className="text-center py-8 text-gray-500">
              <Award className="w-12 h-12 mx-auto mb-3 text-gray-300" />
              <p>Detailed achievements view</p>
              <p className="text-sm">Use the AchievementsPanel component for full view</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default UserProfile;
