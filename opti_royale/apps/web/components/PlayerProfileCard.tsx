import React from 'react';
import { 
  Trophy, 
  Crown, 
  Star, 
  Shield, 
  Users, 
  TrendingUp,
  Award,
  Swords
} from 'lucide-react';
import { clashRoyaleTheme, getTrophyColor } from '../styles/clashRoyaleTheme';

interface ClanInfo {
  tag: string;
  name: string;
  badge: string;
  role: 'member' | 'elder' | 'coLeader' | 'leader';
  donations: number;
  donationsReceived: number;
}

interface PlayerStats {
  level: number;
  expPoints: number;
  expToNextLevel: number;
  trophies: number;
  bestTrophies: number;
  wins: number;
  losses: number;
  threeCrownWins: number;
  challengeCardsWon: number;
  challengeMaxWins: number;
  tournamentCardsWon: number;
  tournamentBattleCount: number;
  role?: string;
  donations: number;
  donationsReceived: number;
  totalDonations: number;
  warDayWins: number;
  clanCardsCollected: number;
  arena: {
    id: number;
    name: string;
    iconUrl: string;
  };
  leagueStatistics?: {
    currentSeason: {
      trophies: number;
      bestTrophies: number;
    };
    previousSeason?: {
      id: string;
      trophies: number;
      bestTrophies: number;
    };
    bestSeason?: {
      id: string;
      trophies: number;
    };
  };
}

interface ClashPlayerProfile {
  tag: string;
  name: string;
  expLevel: number;
  trophies: number;
  bestTrophies: number;
  wins: number;
  losses: number;
  battleCount: number;
  threeCrownWins: number;
  challengeCardsWon: number;
  challengeMaxWins: number;
  tournamentCardsWon: number;
  tournamentBattleCount: number;
  role?: string;
  donations: number;
  donationsReceived: number;
  totalDonations: number;
  warDayWins: number;
  clanCardsCollected: number;
  starPoints: number;
  expPoints: number;
  clan?: ClanInfo;
  arena: {
    id: number;
    name: string;
    iconUrl: string;
  };
  leagueStatistics?: {
    currentSeason: {
      trophies: number;
      bestTrophies: number;
    };
    previousSeason?: {
      id: string;
      trophies: number;
      bestTrophies: number;
    };
    bestSeason?: {
      id: string;
      trophies: number;
    };
  };
}

interface PlayerProfileCardProps {
  player: ClashPlayerProfile;
  isOpponent?: boolean;
  compact?: boolean;
}

const PlayerProfileCard: React.FC<PlayerProfileCardProps> = ({ 
  player, 
  isOpponent = false,
  compact = false 
}) => {
  const winRate = player.battleCount > 0 ? (player.wins / player.battleCount * 100).toFixed(1) : '0.0';
  const trophyColor = getTrophyColor(player.trophies);
  
  const getPlayerTitle = () => {
    if (player.trophies >= 7000) return 'Ultimate Champion';
    if (player.trophies >= 6500) return 'Master';
    if (player.trophies >= 6000) return 'Champion';
    if (player.trophies >= 5000) return 'Challenger';
    if (player.trophies >= 4000) return 'Legendary';
    return 'Arena Warrior';
  };

  const getRoleIcon = (role?: string) => {
    switch (role) {
      case 'leader': return <Crown className="w-4 h-4 text-yellow-500" />;
      case 'coLeader': return <Star className="w-4 h-4 text-orange-500" />;
      case 'elder': return <Shield className="w-4 h-4 text-blue-500" />;
      default: return <Users className="w-4 h-4 text-gray-500" />;
    }
  };

  const cardBgColor = isOpponent 
    ? 'from-red-600 via-red-700 to-red-800' 
    : 'from-blue-600 via-blue-700 to-blue-800';

  if (compact) {
    return (
      <div className={`bg-gradient-to-br ${cardBgColor} text-white p-3 rounded-lg border-2 ${isOpponent ? 'border-red-400' : 'border-blue-400'} shadow-lg`}>
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-bold text-lg">{player.name}</h3>
            <p className="text-xs opacity-80">#{player.tag}</p>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-1 justify-end">
              <Trophy className="w-4 h-4" style={{ color: trophyColor }} />
              <span className="font-bold">{player.trophies}</span>
            </div>
            <p className="text-xs opacity-80">Level {player.expLevel}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-gradient-to-br ${cardBgColor} text-white rounded-xl shadow-2xl border-4 ${isOpponent ? 'border-red-400' : 'border-blue-400'} overflow-hidden`}>
      {/* Header */}
      <div className="relative p-6 bg-black/20">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold mb-1">{player.name}</h2>
            <p className="text-sm opacity-80 mb-2">#{player.tag}</p>
            <div className="flex items-center gap-2">
              <span 
                className="px-3 py-1 rounded-full text-xs font-bold border"
                style={{ 
                  backgroundColor: trophyColor,
                  borderColor: 'rgba(255,255,255,0.3)',
                  color: 'white'
                }}
              >
                {getPlayerTitle()}
              </span>
            </div>
          </div>
          
          <div className="text-right">
            <div className="flex items-center gap-2 justify-end mb-2">
              <Trophy className="w-6 h-6" style={{ color: trophyColor }} />
              <span className="text-3xl font-bold">{player.trophies.toLocaleString()}</span>
            </div>
            <p className="text-sm opacity-80">Best: {player.bestTrophies.toLocaleString()}</p>
            <div className="flex items-center gap-1 justify-end mt-1">
              <Crown className="w-4 h-4 text-purple-300" />
              <span className="text-sm">Level {player.expLevel}</span>
            </div>
          </div>
        </div>

        {/* Arena */}
        <div className="flex items-center gap-3 p-3 bg-black/30 rounded-lg border border-white/20">
          <img 
            src={player.arena.iconUrl} 
            alt={player.arena.name}
            className="w-12 h-12 rounded-full border-2 border-white/40"
          />
          <div>
            <h4 className="font-semibold">{player.arena.name}</h4>
            <p className="text-xs opacity-80">Arena {player.arena.id}</p>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="p-6 grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="text-center">
          <div className="bg-green-500/20 p-3 rounded-lg border border-green-500/30">
            <Swords className="w-6 h-6 text-green-400 mx-auto mb-2" />
            <div className="text-2xl font-bold text-green-400">{player.wins.toLocaleString()}</div>
            <div className="text-xs opacity-80">Wins</div>
          </div>
        </div>

        <div className="text-center">
          <div className="bg-red-500/20 p-3 rounded-lg border border-red-500/30">
            <div className="text-2xl font-bold text-red-400">{player.losses.toLocaleString()}</div>
            <div className="text-xs opacity-80">Losses</div>
          </div>
        </div>

        <div className="text-center">
          <div className="bg-purple-500/20 p-3 rounded-lg border border-purple-500/30">
            <div className="text-2xl font-bold text-purple-400">{winRate}%</div>
            <div className="text-xs opacity-80">Win Rate</div>
          </div>
        </div>

        <div className="text-center">
          <div className="bg-yellow-500/20 p-3 rounded-lg border border-yellow-500/30">
            <Crown className="w-6 h-6 text-yellow-400 mx-auto mb-2" />
            <div className="text-2xl font-bold text-yellow-400">{player.threeCrownWins.toLocaleString()}</div>
            <div className="text-xs opacity-80">3-Crown Wins</div>
          </div>
        </div>
      </div>

      {/* Clan Information */}
      {player.clan && (
        <div className="px-6 pb-6">
          <div className="bg-black/30 p-4 rounded-lg border border-white/20">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-bold text-lg flex items-center gap-2">
                <img 
                  src={player.clan.badge} 
                  alt="Clan badge"
                  className="w-8 h-8"
                />
                {player.clan.name}
              </h4>
              <div className="flex items-center gap-1">
                {getRoleIcon(player.clan.role)}
                <span className="text-sm capitalize">{player.clan.role}</span>
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="flex justify-between">
                <span className="opacity-80">Donated:</span>
                <span className="font-semibold text-green-400">{player.clan.donations.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="opacity-80">Received:</span>
                <span className="font-semibold text-blue-400">{player.clan.donationsReceived.toLocaleString()}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* League Statistics */}
      {player.leagueStatistics && (
        <div className="px-6 pb-6">
          <div className="bg-black/30 p-4 rounded-lg border border-white/20">
            <h4 className="font-bold text-lg mb-3 flex items-center gap-2">
              <Award className="w-5 h-5 text-orange-400" />
              League Statistics
            </h4>
            
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="opacity-80">Current Season:</span>
                <span className="font-semibold">{player.leagueStatistics.currentSeason.trophies.toLocaleString()}</span>
              </div>
              
              {player.leagueStatistics.previousSeason && (
                <div className="flex justify-between">
                  <span className="opacity-80">Previous Season:</span>
                  <span className="font-semibold">{player.leagueStatistics.previousSeason.trophies.toLocaleString()}</span>
                </div>
              )}
              
              {player.leagueStatistics.bestSeason && (
                <div className="flex justify-between">
                  <span className="opacity-80">Best Season:</span>
                  <span className="font-semibold text-yellow-400">{player.leagueStatistics.bestSeason.trophies.toLocaleString()}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Additional Stats */}
      <div className="px-6 pb-6">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="bg-black/20 p-3 rounded border border-white/10">
            <div className="flex justify-between">
              <span className="opacity-80">Challenge Max:</span>
              <span className="font-semibold text-orange-400">{player.challengeMaxWins}</span>
            </div>
          </div>
          
          <div className="bg-black/20 p-3 rounded border border-white/10">
            <div className="flex justify-between">
              <span className="opacity-80">War Day Wins:</span>
              <span className="font-semibold text-green-400">{player.warDayWins.toLocaleString()}</span>
            </div>
          </div>
          
          <div className="bg-black/20 p-3 rounded border border-white/10">
            <div className="flex justify-between">
              <span className="opacity-80">Tournament Cards:</span>
              <span className="font-semibold text-purple-400">{player.tournamentCardsWon.toLocaleString()}</span>
            </div>
          </div>
          
          <div className="bg-black/20 p-3 rounded border border-white/10">
            <div className="flex justify-between">
              <span className="opacity-80">Star Points:</span>
              <span className="font-semibold text-yellow-400">{player.starPoints.toLocaleString()}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PlayerProfileCard;
