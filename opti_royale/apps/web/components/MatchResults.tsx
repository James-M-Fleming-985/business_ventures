import React from 'react';
import { 
  Crown, 
  Trophy, 
  Clock, 
  Zap, 
  Target,
  TrendingUp,
  TrendingDown,
  Calendar
} from 'lucide-react';

interface BattleResult {
  type: string;
  battleTime: string;
  arena: {
    id: number;
    name: string;
    iconUrl: string;
  };
  gameMode: {
    id: number;
    name: string;
  };
  deckSelection: string;
  team: Array<{
    tag: string;
    name: string;
    startingTrophies: number;
    trophyChange: number;
    crowns: number;
    kingTowerHitpoints?: number;
    princessTowersHitpoints?: number[];
    clan?: {
      tag: string;
      name: string;
      badgeId: number;
    };
    cards: Array<{
      name: string;
      id: number;
      level: number;
      maxLevel: number;
      iconUrl: string;
      elixirCost: number;
    }>;
  }>;
  opponent: Array<{
    tag: string;
    name: string;
    startingTrophies: number;
    trophyChange: number;
    crowns: number;
    kingTowerHitpoints?: number;
    princessTowersHitpoints?: number[];
    clan?: {
      tag: string;
      name: string;
      badgeId: number;
    };
    cards: Array<{
      name: string;
      id: number;
      level: number;
      maxLevel: number;
      iconUrl: string;
      elixirCost: number;
    }>;
  }>;
}

interface MatchResultsProps {
  battle: BattleResult;
  isExpanded?: boolean;
  onToggleExpand?: () => void;
}

const MatchResults: React.FC<MatchResultsProps> = ({ 
  battle, 
  isExpanded = false, 
  onToggleExpand 
}) => {
  const player = battle.team[0];
  const opponent = battle.opponent[0];
  const isVictory = player.crowns > opponent.crowns;
  const isDraw = player.crowns === opponent.crowns;
  
  const getBattleOutcome = () => {
    if (isDraw) return { text: 'DRAW', color: 'text-yellow-400', bg: 'from-yellow-500 to-orange-500' };
    if (isVictory) return { text: 'VICTORY', color: 'text-green-400', bg: 'from-green-500 to-emerald-600' };
    return { text: 'DEFEAT', color: 'text-red-400', bg: 'from-red-500 to-pink-600' };
  };

  const outcome = getBattleOutcome();
  const timeSince = new Date().getTime() - new Date(battle.battleTime).getTime();
  const timeText = formatTimeSince(timeSince);

  function formatTimeSince(ms: number): string {
    const minutes = Math.floor(ms / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return 'Just now';
  }

  const getTrophyChangeDisplay = (change: number) => {
    if (change > 0) {
      return (
        <div className="flex items-center gap-1 text-green-400">
          <TrendingUp className="w-4 h-4" />
          <span className="font-bold">+{change}</span>
        </div>
      );
    } else if (change < 0) {
      return (
        <div className="flex items-center gap-1 text-red-400">
          <TrendingDown className="w-4 h-4" />
          <span className="font-bold">{change}</span>
        </div>
      );
    }
    return (
      <div className="flex items-center gap-1 text-gray-400">
        <span className="font-bold">0</span>
      </div>
    );
  };

  return (
    <div className="bg-gradient-to-br from-gray-800 via-gray-900 to-black text-white rounded-xl shadow-2xl border-2 border-gray-600 overflow-hidden">
      {/* Header */}
      <div className={`bg-gradient-to-r ${outcome.bg} p-4 border-b-4 border-yellow-400`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img 
              src={battle.arena.iconUrl} 
              alt={battle.arena.name}
              className="w-12 h-12 rounded-full border-2 border-white/40"
            />
            <div>
              <h3 className="text-xl font-bold">{battle.gameMode.name}</h3>
              <p className="text-sm opacity-90">{battle.arena.name}</p>
            </div>
          </div>
          
          <div className="text-right">
            <div className={`text-2xl font-bold ${outcome.color}`}>
              {outcome.text}
            </div>
            <div className="flex items-center gap-1 text-sm opacity-90">
              <Clock className="w-4 h-4" />
              <span>{timeText}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Battle Summary */}
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          {/* Player */}
          <div className="flex-1 text-center">
            <div className="bg-blue-600 rounded-lg p-4 mx-2">
              <h4 className="font-bold text-lg mb-2">{player.name}</h4>
              <p className="text-sm text-blue-200 mb-3">#{player.tag}</p>
              
              <div className="flex items-center justify-center gap-2 mb-2">
                <Trophy className="w-5 h-5 text-yellow-400" />
                <span className="font-bold">{player.startingTrophies}</span>
              </div>
              
              {getTrophyChangeDisplay(player.trophyChange)}
              
              {player.clan && (
                <p className="text-xs text-blue-200 mt-2">{player.clan.name}</p>
              )}
            </div>
          </div>

          {/* VS & Crown Result */}
          <div className="flex-shrink-0 text-center px-6">
            <div className="bg-yellow-500 text-gray-900 font-bold text-xl rounded-full w-16 h-16 flex items-center justify-center mb-4">
              VS
            </div>
            
            <div className="flex items-center justify-center gap-2 text-3xl font-bold">
              <span className={player.crowns > opponent.crowns ? 'text-green-400' : 'text-gray-400'}>
                {player.crowns}
              </span>
              <Crown className="w-8 h-8 text-yellow-400" />
              <span className={opponent.crowns > player.crowns ? 'text-green-400' : 'text-gray-400'}>
                {opponent.crowns}
              </span>
            </div>
            
            <p className="text-xs text-gray-400 mt-2">{battle.type}</p>
          </div>

          {/* Opponent */}
          <div className="flex-1 text-center">
            <div className="bg-red-600 rounded-lg p-4 mx-2">
              <h4 className="font-bold text-lg mb-2">{opponent.name}</h4>
              <p className="text-sm text-red-200 mb-3">#{opponent.tag}</p>
              
              <div className="flex items-center justify-center gap-2 mb-2">
                <Trophy className="w-5 h-5 text-yellow-400" />
                <span className="font-bold">{opponent.startingTrophies}</span>
              </div>
              
              {getTrophyChangeDisplay(opponent.trophyChange)}
              
              {opponent.clan && (
                <p className="text-xs text-red-200 mt-2">{opponent.clan.name}</p>
              )}
            </div>
          </div>
        </div>

        {/* Expand/Collapse Button */}
        <div className="text-center mb-4">
          <button
            onClick={onToggleExpand}
            className="bg-purple-600 hover:bg-purple-700 px-6 py-2 rounded-lg font-medium transition-colors"
          >
            {isExpanded ? 'Hide Details' : 'Show Details'}
          </button>
        </div>

        {/* Expanded Details */}
        {isExpanded && (
          <div className="space-y-6 border-t border-gray-700 pt-6">
            {/* Battle Stats */}
            <div className="grid grid-cols-2 gap-6">
              {/* Player Deck */}
              <div>
                <h5 className="font-bold text-blue-400 mb-3 flex items-center gap-2">
                  <Target className="w-4 h-4" />
                  Your Deck
                </h5>
                <div className="grid grid-cols-4 gap-2">
                  {player.cards.map((card, index) => (
                    <div key={index} className="relative">
                      <img 
                        src={card.iconUrl} 
                        alt={card.name}
                        className="w-full h-16 object-cover rounded border border-blue-500"
                      />
                      <div className="absolute -top-1 -right-1 bg-purple-600 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                        {card.level}
                      </div>
                      <div className="absolute -bottom-1 -left-1 bg-pink-600 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                        {card.elixirCost}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Opponent Deck */}
              <div>
                <h5 className="font-bold text-red-400 mb-3 flex items-center gap-2">
                  <Target className="w-4 h-4" />
                  Opponent Deck
                </h5>
                <div className="grid grid-cols-4 gap-2">
                  {opponent.cards.map((card, index) => (
                    <div key={index} className="relative">
                      <img 
                        src={card.iconUrl} 
                        alt={card.name}
                        className="w-full h-16 object-cover rounded border border-red-500"
                      />
                      <div className="absolute -top-1 -right-1 bg-purple-600 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                        {card.level}
                      </div>
                      <div className="absolute -bottom-1 -left-1 bg-pink-600 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                        {card.elixirCost}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Tower Damage */}
            {(player.kingTowerHitpoints !== undefined || opponent.kingTowerHitpoints !== undefined) && (
              <div>
                <h5 className="font-bold text-yellow-400 mb-3">Tower Status</h5>
                <div className="grid grid-cols-2 gap-6">
                  <div className="bg-blue-600/20 p-4 rounded border border-blue-500/30">
                    <h6 className="font-semibold text-blue-400 mb-2">Your Towers</h6>
                    {player.kingTowerHitpoints !== undefined && (
                      <div className="mb-2">
                        <span className="text-sm text-gray-300">King Tower: </span>
                        <span className="font-bold text-green-400">{player.kingTowerHitpoints} HP</span>
                      </div>
                    )}
                    {player.princessTowersHitpoints && (
                      <div className="space-y-1">
                        {player.princessTowersHitpoints.map((hp, index) => (
                          <div key={index}>
                            <span className="text-sm text-gray-300">Princess Tower {index + 1}: </span>
                            <span className={`font-bold ${hp > 0 ? 'text-green-400' : 'text-red-400'}`}>
                              {hp} HP
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="bg-red-600/20 p-4 rounded border border-red-500/30">
                    <h6 className="font-semibold text-red-400 mb-2">Opponent Towers</h6>
                    {opponent.kingTowerHitpoints !== undefined && (
                      <div className="mb-2">
                        <span className="text-sm text-gray-300">King Tower: </span>
                        <span className="font-bold text-green-400">{opponent.kingTowerHitpoints} HP</span>
                      </div>
                    )}
                    {opponent.princessTowersHitpoints && (
                      <div className="space-y-1">
                        {opponent.princessTowersHitpoints.map((hp, index) => (
                          <div key={index}>
                            <span className="text-sm text-gray-300">Princess Tower {index + 1}: </span>
                            <span className={`font-bold ${hp > 0 ? 'text-green-400' : 'text-red-400'}`}>
                              {hp} HP
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Battle Info */}
            <div className="bg-gray-800 p-4 rounded border border-gray-600">
              <h5 className="font-bold text-purple-400 mb-3 flex items-center gap-2">
                <Calendar className="w-4 h-4" />
                Battle Information
              </h5>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-gray-400">Battle Type:</span>
                  <div className="font-semibold">{battle.type}</div>
                </div>
                <div>
                  <span className="text-gray-400">Game Mode:</span>
                  <div className="font-semibold">{battle.gameMode.name}</div>
                </div>
                <div>
                  <span className="text-gray-400">Arena:</span>
                  <div className="font-semibold">{battle.arena.name}</div>
                </div>
                <div>
                  <span className="text-gray-400">Time:</span>
                  <div className="font-semibold">{new Date(battle.battleTime).toLocaleString()}</div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MatchResults;
