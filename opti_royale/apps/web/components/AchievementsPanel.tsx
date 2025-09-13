import React, { useState, useEffect } from 'react';
import { 
  Award, 
  Trophy, 
  Target, 
  TrendingUp, 
  Users, 
  Zap, 
  Star, 
  Crown,
  CheckCircle,
  Lock,
  BarChart3,
  Calendar,
  Flame
} from 'lucide-react';

interface Achievement {
  id: string;
  name: string;
  description: string;
  category: 'accuracy' | 'consistency' | 'social' | 'special' | 'milestone';
  icon: string;
  rarity: 'common' | 'rare' | 'epic' | 'legendary';
  xpReward: number;
  progress: number;
  maxProgress: number;
  isUnlocked: boolean;
  unlockedAt?: string;
  requirements: string[];
}

interface AchievementCategory {
  name: string;
  icon: React.ReactNode;
  color: string;
  achievements: Achievement[];
}

const getAchievementIcon = (iconName: string) => {
  const iconMap: Record<string, React.ReactNode> = {
    'target': <Target className="w-6 h-6" />,
    'trophy': <Trophy className="w-6 h-6" />,
    'trending-up': <TrendingUp className="w-6 h-6" />,
    'users': <Users className="w-6 h-6" />,
    'zap': <Zap className="w-6 h-6" />,
    'star': <Star className="w-6 h-6" />,
    'crown': <Crown className="w-6 h-6" />,
    'chart': <BarChart3 className="w-6 h-6" />,
    'calendar': <Calendar className="w-6 h-6" />,
    'flame': <Flame className="w-6 h-6" />
  };
  return iconMap[iconName] || <Award className="w-6 h-6" />;
};

const getRarityInfo = (rarity: Achievement['rarity']) => {
  switch (rarity) {
    case 'legendary':
      return { color: 'from-purple-500 to-pink-500', textColor: 'text-purple-700', bgColor: 'bg-purple-50' };
    case 'epic':
      return { color: 'from-purple-500 to-blue-500', textColor: 'text-purple-700', bgColor: 'bg-purple-50' };
    case 'rare':
      return { color: 'from-blue-500 to-cyan-500', textColor: 'text-blue-700', bgColor: 'bg-blue-50' };
    default:
      return { color: 'from-gray-400 to-gray-600', textColor: 'text-gray-700', bgColor: 'bg-gray-50' };
  }
};

export const AchievementsPanel: React.FC = () => {
  const [achievements, setAchievements] = useState<Achievement[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [filter, setFilter] = useState<'all' | 'unlocked' | 'locked'>('all');

  useEffect(() => {
    fetchAchievements();
  }, []);

  const fetchAchievements = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/achievements');
      const data = await response.json();
      setAchievements(data.achievements);
    } catch (error) {
      console.error('Failed to fetch achievements:', error);
    } finally {
      setLoading(false);
    }
  };

  const groupedAchievements: AchievementCategory[] = [
    {
      name: 'Accuracy Masters',
      icon: <Target className="w-5 h-5" />,
      color: 'text-green-600',
      achievements: achievements.filter(a => a.category === 'accuracy')
    },
    {
      name: 'Consistency Kings',
      icon: <TrendingUp className="w-5 h-5" />,
      color: 'text-blue-600',
      achievements: achievements.filter(a => a.category === 'consistency')
    },
    {
      name: 'Social Champions',
      icon: <Users className="w-5 h-5" />,
      color: 'text-purple-600',
      achievements: achievements.filter(a => a.category === 'social')
    },
    {
      name: 'Milestones',
      icon: <Trophy className="w-5 h-5" />,
      color: 'text-yellow-600',
      achievements: achievements.filter(a => a.category === 'milestone')
    },
    {
      name: 'Special Events',
      icon: <Crown className="w-5 h-5" />,
      color: 'text-pink-600',
      achievements: achievements.filter(a => a.category === 'special')
    }
  ];

  const filteredAchievements = groupedAchievements.map(category => ({
    ...category,
    achievements: category.achievements.filter(achievement => {
      if (selectedCategory !== 'all' && category.name.toLowerCase() !== selectedCategory) return false;
      if (filter === 'unlocked') return achievement.isUnlocked;
      if (filter === 'locked') return !achievement.isUnlocked;
      return true;
    })
  })).filter(category => category.achievements.length > 0);

  const totalAchievements = achievements.length;
  const unlockedCount = achievements.filter(a => a.isUnlocked).length;
  const totalXP = achievements.filter(a => a.isUnlocked).reduce((sum, a) => sum + a.xpReward, 0);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="animate-pulse space-y-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-20 bg-gray-200 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-600 to-blue-600 text-white p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold flex items-center gap-2">
              <Award className="w-6 h-6" />
              Achievements
            </h2>
            <p className="opacity-90">Unlock rewards by mastering deck optimization</p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold">{unlockedCount}/{totalAchievements}</div>
            <div className="text-sm opacity-90">Unlocked</div>
            <div className="text-sm opacity-75">{totalXP.toLocaleString()} XP Earned</div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="p-4 bg-gray-50 border-b">
        <div className="flex flex-wrap gap-2 mb-3">
          <button
            onClick={() => setSelectedCategory('all')}
            className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
              selectedCategory === 'all' 
                ? 'bg-blue-100 text-blue-700' 
                : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
            }`}
          >
            All Categories
          </button>
          {groupedAchievements.map(category => (
            <button
              key={category.name}
              onClick={() => setSelectedCategory(category.name.toLowerCase())}
              className={`px-3 py-1 rounded-full text-sm font-medium transition-colors flex items-center gap-1 ${
                selectedCategory === category.name.toLowerCase()
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
              }`}
            >
              {category.icon}
              {category.name}
            </button>
          ))}
        </div>
        
        <div className="flex gap-2">
          <button
            onClick={() => setFilter('all')}
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              filter === 'all' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-600'
            }`}
          >
            All
          </button>
          <button
            onClick={() => setFilter('unlocked')}
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              filter === 'unlocked' ? 'bg-green-500 text-white' : 'bg-gray-200 text-gray-600'
            }`}
          >
            Unlocked
          </button>
          <button
            onClick={() => setFilter('locked')}
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              filter === 'locked' ? 'bg-gray-500 text-white' : 'bg-gray-200 text-gray-600'
            }`}
          >
            Locked
          </button>
        </div>
      </div>

      {/* Achievement Categories */}
      <div className="divide-y divide-gray-200">
        {filteredAchievements.map(category => (
          <div key={category.name} className="p-6">
            <h3 className={`text-lg font-bold flex items-center gap-2 mb-4 ${category.color}`}>
              {category.icon}
              {category.name}
              <span className="text-sm font-normal text-gray-500">
                ({category.achievements.filter(a => a.isUnlocked).length}/{category.achievements.length})
              </span>
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {category.achievements.map(achievement => {
                const rarityInfo = getRarityInfo(achievement.rarity);
                const progressPercent = (achievement.progress / achievement.maxProgress) * 100;
                
                return (
                  <div
                    key={achievement.id}
                    className={`relative overflow-hidden rounded-lg border-2 transition-all hover:shadow-md ${
                      achievement.isUnlocked 
                        ? `border-transparent bg-gradient-to-br ${rarityInfo.color} text-white` 
                        : 'border-gray-300 bg-white hover:border-gray-400'
                    }`}
                  >
                    {/* Achievement Content */}
                    <div className={`p-4 ${achievement.isUnlocked ? 'text-white' : ''}`}>
                      <div className="flex items-start gap-3">
                        <div className={`flex-shrink-0 p-2 rounded-lg ${
                          achievement.isUnlocked 
                            ? 'bg-white/20' 
                            : rarityInfo.bgColor
                        }`}>
                          {achievement.isUnlocked ? (
                            <div className="text-white">
                              {getAchievementIcon(achievement.icon)}
                            </div>
                          ) : (
                            <div className="text-gray-400">
                              <Lock className="w-6 h-6" />
                            </div>
                          )}
                        </div>
                        
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <h4 className="font-semibold truncate">{achievement.name}</h4>
                            {achievement.isUnlocked && (
                              <CheckCircle className="w-4 h-4 text-white/80" />
                            )}
                          </div>
                          
                          <p className={`text-sm mb-2 ${
                            achievement.isUnlocked ? 'text-white/90' : 'text-gray-600'
                          }`}>
                            {achievement.description}
                          </p>
                          
                          <div className="flex items-center justify-between text-xs">
                            <span className={`font-medium capitalize px-2 py-1 rounded ${
                              achievement.isUnlocked 
                                ? 'bg-white/20 text-white' 
                                : `${rarityInfo.bgColor} ${rarityInfo.textColor}`
                            }`}>
                              {achievement.rarity}
                            </span>
                            <span className={achievement.isUnlocked ? 'text-white/80' : 'text-gray-500'}>
                              +{achievement.xpReward} XP
                            </span>
                          </div>
                        </div>
                      </div>
                      
                      {/* Progress Bar */}
                      {!achievement.isUnlocked && achievement.maxProgress > 1 && (
                        <div className="mt-3">
                          <div className="flex justify-between text-xs text-gray-600 mb-1">
                            <span>Progress</span>
                            <span>{achievement.progress}/{achievement.maxProgress}</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                              style={{ width: `${Math.min(progressPercent, 100)}%` }}
                            />
                          </div>
                        </div>
                      )}
                      
                      {/* Unlock Date */}
                      {achievement.isUnlocked && achievement.unlockedAt && (
                        <div className="mt-2 text-xs text-white/70">
                          Unlocked {new Date(achievement.unlockedAt).toLocaleDateString()}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {filteredAchievements.length === 0 && (
        <div className="p-12 text-center text-gray-500">
          <Award className="w-16 h-16 mx-auto mb-4 text-gray-300" />
          <h3 className="text-lg font-medium mb-2">No achievements found</h3>
          <p>Try adjusting your filters to see more achievements.</p>
        </div>
      )}
    </div>
  );
};

export default AchievementsPanel;
