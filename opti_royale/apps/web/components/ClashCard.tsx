import React from 'react';
import { clashRoyaleTheme, getCardRarityStyles, getElixirColor } from '../styles/clashRoyaleTheme';
import { Zap, Star, Shield, Sword } from 'lucide-react';

interface CardData {
  id: string;
  name: string;
  description: string;
  level: number;
  elixir: number;
  type: 'troop' | 'spell' | 'building';
  rarity: 'common' | 'rare' | 'epic' | 'legendary';
  image: string;
  stats?: {
    damage?: number;
    hitpoints?: number;
    speed?: 'slow' | 'medium' | 'fast' | 'very-fast';
    range?: number;
  };
}

interface ClashCardProps {
  card: CardData;
  size?: 'small' | 'medium' | 'large';
  showStats?: boolean;
  onClick?: () => void;
  isSelected?: boolean;
  showLevel?: boolean;
}

const ClashCard: React.FC<ClashCardProps> = ({
  card,
  size = 'medium',
  showStats = false,
  onClick,
  isSelected = false,
  showLevel = true
}) => {
  const rarityStyles = getCardRarityStyles(card.rarity);
  const elixirColor = getElixirColor(card.elixir);

  const sizeClasses = {
    small: 'w-20 h-28',
    medium: 'w-24 h-32',
    large: 'w-32 h-44'
  };

  const getTypeIcon = () => {
    switch (card.type) {
      case 'troop':
        return <Sword className="w-3 h-3" />;
      case 'spell':
        return <Zap className="w-3 h-3" />;
      case 'building':
        return <Shield className="w-3 h-3" />;
      default:
        return null;
    }
  };

  const getRarityStars = () => {
    const stars = {
      common: 1,
      rare: 2,
      epic: 3,
      legendary: 4
    };
    
    return Array.from({ length: stars[card.rarity] }, (_, i) => (
      <Star key={i} className="w-2 h-2 fill-current" />
    ));
  };

  return (
    <div 
      className={`
        ${sizeClasses[size]} 
        relative cursor-pointer transform transition-all duration-300 hover:scale-105 hover:rotate-1
        ${isSelected ? 'ring-4 ring-yellow-400 ring-opacity-80' : ''}
        ${onClick ? 'hover:shadow-2xl' : ''}
      `}
      onClick={onClick}
      style={{ perspective: '1000px' }}
    >
      {/* Card Background with Rarity Gradient */}
      <div 
        className="absolute inset-0 rounded-lg border-2 shadow-lg"
        style={{
          background: rarityStyles.background,
          borderColor: rarityStyles.borderColor,
          boxShadow: `0 8px 25px -8px ${rarityStyles.borderColor}40`
        }}
      >
        {/* Inner Card Content */}
        <div className="relative h-full p-1 rounded-lg overflow-hidden">
          {/* Card Image */}
          <div className="relative h-2/3 mb-1">
            <img 
              src={card.image} 
              alt={card.name}
              className="w-full h-full object-cover rounded border border-white/20"
            />
            
            {/* Elixir Cost */}
            <div 
              className="absolute -top-1 -right-1 w-6 h-6 rounded-full flex items-center justify-center text-white font-bold text-xs border-2 border-white shadow-lg"
              style={{ backgroundColor: elixirColor }}
            >
              {card.elixir}
            </div>

            {/* Card Type Icon */}
            <div 
              className="absolute -top-1 -left-1 w-5 h-5 rounded-full flex items-center justify-center text-white bg-gray-800 border border-white/40"
            >
              {getTypeIcon()}
            </div>

            {/* Level Badge */}
            {showLevel && (
              <div className="absolute bottom-0 right-0 bg-purple-600 text-white text-xs px-2 py-1 rounded-tl border border-white/20 font-bold">
                LV{card.level}
              </div>
            )}
          </div>

          {/* Card Name */}
          <div className="text-center px-1">
            <h3 
              className="text-xs font-bold truncate leading-tight"
              style={{ color: rarityStyles.color }}
            >
              {card.name}
            </h3>
            
            {/* Rarity Stars */}
            <div className="flex justify-center mt-1 gap-1" style={{ color: rarityStyles.color }}>
              {getRarityStars()}
            </div>
          </div>
        </div>

        {/* Shine Effect on Hover */}
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full transition-transform duration-700 hover:translate-x-full" />
      </div>

      {/* Detailed Stats Panel (for large cards or when showStats is true) */}
      {showStats && card.stats && (
        <div 
          className="absolute top-full left-0 right-0 mt-2 bg-gray-900 text-white p-2 rounded border border-gray-600 shadow-xl z-10"
          style={{ minWidth: '200px' }}
        >
          <h4 className="font-bold text-sm mb-2 text-yellow-400">{card.name}</h4>
          <p className="text-xs text-gray-300 mb-2">{card.description}</p>
          
          <div className="grid grid-cols-2 gap-2 text-xs">
            {card.stats.damage && (
              <div className="flex justify-between">
                <span className="text-gray-400">Damage:</span>
                <span className="text-red-400 font-semibold">{card.stats.damage}</span>
              </div>
            )}
            {card.stats.hitpoints && (
              <div className="flex justify-between">
                <span className="text-gray-400">HP:</span>
                <span className="text-green-400 font-semibold">{card.stats.hitpoints}</span>
              </div>
            )}
            {card.stats.speed && (
              <div className="flex justify-between">
                <span className="text-gray-400">Speed:</span>
                <span className="text-blue-400 font-semibold capitalize">{card.stats.speed}</span>
              </div>
            )}
            {card.stats.range && (
              <div className="flex justify-between">
                <span className="text-gray-400">Range:</span>
                <span className="text-purple-400 font-semibold">{card.stats.range}</span>
              </div>
            )}
          </div>
          
          <div className="mt-2 pt-2 border-t border-gray-700">
            <div className="flex justify-between items-center text-xs">
              <span className="text-gray-400 capitalize">{card.rarity} {card.type}</span>
              <span className="text-purple-400">{card.elixir} elixir</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Deck Display Component
interface DeckDisplayProps {
  cards: CardData[];
  title?: string;
  playerName?: string;
  averageElixir?: number;
  onCardClick?: (card: CardData) => void;
  selectedCard?: string;
}

export const DeckDisplay: React.FC<DeckDisplayProps> = ({
  cards,
  title,
  playerName,
  averageElixir,
  onCardClick,
  selectedCard
}) => {
  const calculateAverageElixir = () => {
    if (averageElixir !== undefined) return averageElixir;
    return cards.reduce((sum, card) => sum + card.elixir, 0) / cards.length;
  };

  return (
    <div className="bg-gradient-to-br from-gray-800 to-gray-900 p-4 rounded-lg border-2 border-gray-600 shadow-xl">
      {/* Header */}
      {(title || playerName) && (
        <div className="mb-4 text-center">
          {title && (
            <h3 className="text-lg font-bold text-yellow-400 mb-1">{title}</h3>
          )}
          {playerName && (
            <p className="text-sm text-gray-300">{playerName}</p>
          )}
          <div className="flex justify-center items-center gap-2 mt-2">
            <span className="text-xs text-gray-400">Average Elixir:</span>
            <span 
              className="text-sm font-bold px-2 py-1 rounded"
              style={{ 
                backgroundColor: getElixirColor(calculateAverageElixir()),
                color: 'white'
              }}
            >
              {calculateAverageElixir().toFixed(1)}
            </span>
          </div>
        </div>
      )}

      {/* Deck Grid */}
      <div className="grid grid-cols-4 gap-3 justify-items-center">
        {cards.map((card, index) => (
          <ClashCard
            key={`${card.id}-${index}`}
            card={card}
            size="medium"
            onClick={() => onCardClick?.(card)}
            isSelected={selectedCard === card.id}
            showLevel={true}
          />
        ))}
      </div>

      {/* Deck Statistics */}
      <div className="mt-4 pt-3 border-t border-gray-700">
        <div className="grid grid-cols-4 gap-2 text-xs text-center">
          <div>
            <div className="text-gray-400">Troops</div>
            <div className="text-blue-400 font-semibold">
              {cards.filter(c => c.type === 'troop').length}
            </div>
          </div>
          <div>
            <div className="text-gray-400">Spells</div>
            <div className="text-purple-400 font-semibold">
              {cards.filter(c => c.type === 'spell').length}
            </div>
          </div>
          <div>
            <div className="text-gray-400">Buildings</div>
            <div className="text-green-400 font-semibold">
              {cards.filter(c => c.type === 'building').length}
            </div>
          </div>
          <div>
            <div className="text-gray-400">Legendaries</div>
            <div className="text-orange-400 font-semibold">
              {cards.filter(c => c.rarity === 'legendary').length}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ClashCard;
