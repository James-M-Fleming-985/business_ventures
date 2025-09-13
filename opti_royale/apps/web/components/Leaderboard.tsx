import React, { useState, useEffect } from 'react';
import { Trophy, Medal, Award, TrendingUp, Users, Star } from 'lucide-react';

interface LeaderboardEntry {
  id: string;
  username: string;
  avatar?: string;
  rating: number;
  rank: number;
  accuracy: number;
  totalAnalyses: number;
  winRate: number;
  trophies: number;
  currentStreak: number;
  rankChange: number;
  level: number;
  xp: number;
}

interface LeaderboardProps {
  timeframe?: 'daily' | 'weekly' | 'monthly' | 'allTime';
  category?: 'overall' | 'accuracy' | 'consistency' | 'improvement';
  limit?: number;
}

export const Leaderboard: React.FC<LeaderboardProps> = ({
  timeframe = 'weekly',
  category = 'overall',
  limit = 100
}) => {
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [userRank, setUserRank] = useState<LeaderboardEntry | null>(null);

  useEffect(() => {
    fetchLeaderboard();
  }, [timeframe, category]);

  const fetchLeaderboard = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/leaderboard?timeframe=${timeframe}&category=${category}&limit=${limit}`);
      const data = await response.json();
      setLeaderboard(data.leaderboard);
      setUserRank(data.userRank);
    } catch (error) {
      console.error('Failed to fetch leaderboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const getRankIcon = (rank: number) => {
    if (rank === 1) return <Trophy className="w-6 h-6 text-yellow-500" />;
    if (rank === 2) return <Medal className="w-6 h-6 text-gray-400" />;
    if (rank === 3) return <Award className="w-6 h-6 text-orange-500" />;
    return <span className="w-6 h-6 flex items-center justify-center text-sm font-bold">{rank}</span>;
  };

  const getRankChangeIndicator = (change: number) => {
    if (change > 0) return <TrendingUp className="w-4 h-4 text-green-500" />;
    if (change < 0) return <TrendingUp className="w-4 h-4 text-red-500 transform rotate-180" />;
    return <div className="w-4 h-4" />;
  };

  const formatRating = (rating: number) => {
    if (rating >= 2500) return { tier: 'Legendary', color: 'text-purple-600' };
    if (rating >= 2000) return { tier: 'Master', color: 'text-blue-600' };
    if (rating >= 1500) return { tier: 'Champion', color: 'text-green-600' };
    if (rating >= 1000) return { tier: 'Expert', color: 'text-orange-600' };
    return { tier: 'Beginner', color: 'text-gray-600' };
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="animate-pulse space-y-4">
          {[...Array(10)].map((_, i) => (
            <div key={i} className="h-16 bg-gray-200 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold flex items-center gap-2">
              <Trophy className="w-6 h-6" />
              Leaderboard
            </h2>
            <p className="opacity-90 capitalize">{timeframe} • {category} Rankings</p>
          </div>
          <div className="text-right">
            <div className="text-sm opacity-90">Total Players</div>
            <div className="text-xl font-bold">{leaderboard.length.toLocaleString()}</div>
          </div>
        </div>
      </div>

      {/* User's Current Rank */}
      {userRank && (
        <div className="bg-blue-50 border-b border-blue-200 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center justify-center w-12 h-12 bg-blue-100 rounded-full">
                {getRankIcon(userRank.rank)}
              </div>
              <div>
                <div className="font-semibold text-blue-900">Your Rank: #{userRank.rank}</div>
                <div className="text-sm text-blue-700">
                  {formatRating(userRank.rating).tier} • {userRank.rating} Rating
                </div>
              </div>
            </div>
            <div className="text-right">
              <div className="flex items-center gap-1 text-sm text-blue-700">
                {getRankChangeIndicator(userRank.rankChange)}
                {Math.abs(userRank.rankChange)} from last week
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Leaderboard List */}
      <div className="divide-y divide-gray-200">
        {leaderboard.map((entry, index) => {
          const ratingInfo = formatRating(entry.rating);
          
          return (
            <div
              key={entry.id}
              className={`p-4 hover:bg-gray-50 transition-colors ${
                entry.rank <= 3 ? 'bg-gradient-to-r from-yellow-50 to-orange-50' : ''
              }`}
            >
              <div className="flex items-center justify-between">
                {/* Rank and User Info */}
                <div className="flex items-center gap-4">
                  <div className="flex items-center justify-center w-12 h-12 bg-gray-100 rounded-full">
                    {getRankIcon(entry.rank)}
                  </div>
                  
                  <div className="flex items-center gap-3">
                    {entry.avatar ? (
                      <img src={entry.avatar} alt={entry.username} className="w-10 h-10 rounded-full" />
                    ) : (
                      <div className="w-10 h-10 bg-gradient-to-br from-blue-400 to-purple-600 rounded-full flex items-center justify-center text-white font-bold">
                        {entry.username.charAt(0).toUpperCase()}
                      </div>
                    )}
                    
                    <div>
                      <div className="font-semibold text-gray-900">{entry.username}</div>
                      <div className="flex items-center gap-2 text-sm text-gray-600">
                        <span className={`font-medium ${ratingInfo.color}`}>
                          {ratingInfo.tier}
                        </span>
                        <span>•</span>
                        <span>Level {entry.level}</span>
                        {entry.currentStreak > 0 && (
                          <>
                            <span>•</span>
                            <span className="text-orange-600 flex items-center gap-1">
                              <Star className="w-3 h-3" />
                              {entry.currentStreak} streak
                            </span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Stats */}
                <div className="flex items-center gap-6 text-sm">
                  <div className="text-right">
                    <div className="font-bold text-lg">{entry.rating}</div>
                    <div className="text-gray-600">Rating</div>
                  </div>
                  
                  <div className="text-right">
                    <div className="font-semibold">{entry.accuracy.toFixed(1)}%</div>
                    <div className="text-gray-600">Accuracy</div>
                  </div>
                  
                  <div className="text-right">
                    <div className="font-semibold">{entry.totalAnalyses}</div>
                    <div className="text-gray-600">Analyses</div>
                  </div>
                  
                  <div className="text-right">
                    <div className="font-semibold">{entry.winRate.toFixed(1)}%</div>
                    <div className="text-gray-600">Win Rate</div>
                  </div>

                  <div className="flex items-center gap-1">
                    {getRankChangeIndicator(entry.rankChange)}
                    <span className={`text-xs ${
                      entry.rankChange > 0 ? 'text-green-600' : 
                      entry.rankChange < 0 ? 'text-red-600' : 'text-gray-500'
                    }`}>
                      {entry.rankChange !== 0 && (entry.rankChange > 0 ? '+' : '')}{entry.rankChange}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Load More */}
      {leaderboard.length >= limit && (
        <div className="p-4 text-center bg-gray-50 border-t">
          <button
            onClick={() => {/* Implement load more */}}
            className="text-blue-600 hover:text-blue-800 font-medium"
          >
            Load More Players
          </button>
        </div>
      )}
    </div>
  );
};

export default Leaderboard;
