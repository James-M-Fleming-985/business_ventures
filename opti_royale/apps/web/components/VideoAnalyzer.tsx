import React, { useState, useRef, useEffect } from 'react';
import { 
  Play, 
  Pause, 
  RotateCcw, 
  Zap, 
  Save, 
  Share2, 
  Target, 
  Trophy,
  Users,
  Crown,
  Star,
  Shield,
  Swords,
  Clock,
  Upload
} from 'lucide-react';

interface Card {
  id: string;
  name: string;
  level: number;
  elixir: number;
  type: 'troop' | 'spell' | 'building';
  rarity: 'common' | 'rare' | 'epic' | 'legendary';
  image: string;
}

interface PlayerInfo {
  tag: string;
  name: string;
  level: number;
  trophies: number;
  clan?: {
    tag: string;
    name: string;
    badge: string;
  };
  deck: Card[];
}

interface MatchData {
  battleTime: string;
  type: string;
  arena: {
    id: number;
    name: string;
  };
  player: PlayerInfo;
  opponent: PlayerInfo;
  crowns: {
    player: number;
    opponent: number;
  };
  duration: number; // in seconds
}

interface AnalysisResult {
  timestamp: number;
  recommendation: {
    cardToPlace: Card;
    position: { x: number; y: number };
    confidence: number;
    reasoning: string;
  };
  currentSituation: {
    playerElixir: number;
    opponentElixir: number;
    playerTowers: number;
    opponentTowers: number;
  };
}

interface VideoAnalyzerProps {
  videoUrl: string;
  matchData?: MatchData;
  onAnalysisComplete?: (result: AnalysisResult) => void;
}

const VideoAnalyzer: React.FC<VideoAnalyzerProps> = ({ 
  videoUrl, 
  matchData,
  onAnalysisComplete 
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [savedAnalyses, setSavedAnalyses] = useState<AnalysisResult[]>([]);
  const [currentVideoUrl, setCurrentVideoUrl] = useState<string>(videoUrl);
  const [uploadedFileName, setUploadedFileName] = useState<string>('');

  const togglePlayPause = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration);
      console.log('Video metadata loaded - Duration:', videoRef.current.duration);
    }
  };

  const handleVideoError = (event: React.SyntheticEvent<HTMLVideoElement, Event>) => {
    console.error('Video error:', event.currentTarget.error);
    const error = event.currentTarget.error;
    if (error) {
      console.error('Error code:', error.code, 'Error message:', error.message);
      
      // Provide user-friendly error messages
      let userMessage = '';
      switch (error.code) {
        case 1:
          userMessage = 'Video loading was aborted.';
          break;
        case 2:
          userMessage = 'Network error occurred while loading the video.';
          break;
        case 3:
          userMessage = 'Video decoding error - the file may be corrupted.';
          break;
        case 4:
          userMessage = 'Video format not supported by your browser. Try converting to a different format.';
          break;
        default:
          userMessage = 'Unknown video error occurred.';
      }
      
      alert(`Video Error: ${userMessage}\n\nTechnical details: ${error.message}`);
      
      // Reset video state on error
      setCurrentVideoUrl('');
      setUploadedFileName('');
      setCurrentTime(0);
      setDuration(0);
      setIsPlaying(false);
    }
  };

  const handleVideoCanPlay = () => {
    console.log('Video can play - ready for playback');
  };

  const seekTo = (time: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = time;
      setCurrentTime(time);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const analyzeCurrentFrame = async () => {
    setIsAnalyzing(true);
    
    // Pause video during analysis
    if (videoRef.current && isPlaying) {
      videoRef.current.pause();
      setIsPlaying(false);
    }

    try {
      // Simulate API call for analysis
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const mockAnalysis: AnalysisResult = {
        timestamp: currentTime,
        recommendation: {
          cardToPlace: {
            id: 'hog_rider',
            name: 'Hog Rider',
            level: 11,
            elixir: 4,
            type: 'troop',
            rarity: 'rare',
            image: '/cards/hog_rider.png'
          },
          position: { x: 0.3, y: 0.7 },
          confidence: 89.5,
          reasoning: 'Opponent has low elixir and no building defenders. Hog Rider can pressure left lane effectively.'
        },
        currentSituation: {
          playerElixir: 6,
          opponentElixir: 2,
          playerTowers: 3,
          opponentTowers: 2
        }
      };

      setAnalysisResult(mockAnalysis);
      onAnalysisComplete?.(mockAnalysis);
    } catch (error) {
      console.error('Analysis failed:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const saveAnalysis = () => {
    if (analysisResult) {
      setSavedAnalyses(prev => [...prev, analysisResult]);
      // TODO: Save to backend
    }
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      console.log('File selected:', file.name, file.type, file.size);
      
      // Validate file type - be more specific about supported formats
      const validTypes = ['video/mp4', 'video/webm', 'video/ogg'];
      const preferredCodecs = ['video/mp4; codecs="avc1.42E01E, mp4a.40.2"', 'video/webm; codecs="vp9, opus"'];
      
      if (!validTypes.includes(file.type)) {
        alert('Please select a supported video file format:\n- MP4 (H.264 codec recommended)\n- WebM (VP9 codec)\n- OGG\n\nNote: Some MP4 files with incompatible codecs may not play.');
        console.error('Unsupported file type:', file.type);
        return;
      }

      // Check file size (max 500MB)
      const maxSize = 500 * 1024 * 1024; // 500MB in bytes
      if (file.size > maxSize) {
        alert('File size too large. Please select a video under 500MB.');
        console.error('File too large:', file.size);
        return;
      }

      // Check if browser can likely play this type
      const video = document.createElement('video');
      const canPlay = video.canPlayType(file.type);
      
      if (canPlay === '') {
        alert('Warning: Your browser may not support this video format. Consider converting to H.264 MP4 or WebM format.');
        console.warn('Browser support uncertain for:', file.type);
      }

      try {
        // Create object URL for local playback
        const objectUrl = URL.createObjectURL(file);
        console.log('Object URL created:', objectUrl);
        
        setCurrentVideoUrl(objectUrl);
        setUploadedFileName(file.name);
        
        // Reset video state
        setCurrentTime(0);
        setDuration(0);
        setIsPlaying(false);
        setAnalysisResult(null);
        
        console.log('Video state updated - URL:', objectUrl, 'Filename:', file.name);
        
        // Reset file input for future uploads
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
      } catch (error) {
        console.error('Error creating object URL:', error);
        alert('Error loading video file. Please try again.');
      }
    }
  };

  const openFileDialog = () => {
    fileInputRef.current?.click();
  };

  const getRarityColor = (rarity: string) => {
    switch (rarity) {
      case 'legendary': return 'from-orange-400 to-yellow-500';
      case 'epic': return 'from-purple-400 to-pink-500';
      case 'rare': return 'from-orange-300 to-orange-500';
      default: return 'from-gray-300 to-gray-400';
    }
  };

  return (
    <div className="bg-gradient-to-b from-blue-900 via-blue-800 to-purple-900 min-h-screen text-white">
      {/* Match Header - Clash Royale Style */}
      {matchData && (
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-4 border-b-4 border-yellow-400">
          <div className="max-w-6xl mx-auto">
            {/* Battle Type & Arena */}
            <div className="text-center mb-4">
              <h2 className="text-2xl font-bold text-yellow-300">{matchData.type}</h2>
              <p className="text-blue-200">{matchData.arena.name}</p>
            </div>

            {/* Players vs */}
            <div className="flex items-center justify-between">
              {/* Player */}
              <div className="flex-1 text-center">
                <div className="bg-blue-500 rounded-lg p-3 mx-2">
                  <h3 className="font-bold text-lg">{matchData.player.name}</h3>
                  <p className="text-sm text-blue-200">#{matchData.player.tag}</p>
                  <div className="flex items-center justify-center gap-2 mt-2">
                    <Trophy className="w-4 h-4 text-yellow-400" />
                    <span>{matchData.player.trophies}</span>
                    <Crown className="w-4 h-4 text-purple-300" />
                    <span>Level {matchData.player.level}</span>
                  </div>
                  {matchData.player.clan && (
                    <p className="text-xs text-blue-200 mt-1">{matchData.player.clan.name}</p>
                  )}
                </div>
              </div>

              {/* VS & Result */}
              <div className="flex-shrink-0 text-center px-4">
                <div className="bg-yellow-500 text-blue-900 font-bold text-xl rounded-full w-16 h-16 flex items-center justify-center mb-2">
                  VS
                </div>
                <div className="flex items-center justify-center gap-1 text-2xl font-bold">
                  <span className={matchData.crowns.player > matchData.crowns.opponent ? 'text-green-400' : 'text-red-400'}>
                    {matchData.crowns.player}
                  </span>
                  <Crown className="w-6 h-6 text-yellow-400" />
                  <span className={matchData.crowns.opponent > matchData.crowns.player ? 'text-green-400' : 'text-red-400'}>
                    {matchData.crowns.opponent}
                  </span>
                </div>
                <p className="text-xs text-blue-200">{formatTime(matchData.duration)}</p>
              </div>

              {/* Opponent */}
              <div className="flex-1 text-center">
                <div className="bg-red-500 rounded-lg p-3 mx-2">
                  <h3 className="font-bold text-lg">{matchData.opponent.name}</h3>
                  <p className="text-sm text-red-200">#{matchData.opponent.tag}</p>
                  <div className="flex items-center justify-center gap-2 mt-2">
                    <Trophy className="w-4 h-4 text-yellow-400" />
                    <span>{matchData.opponent.trophies}</span>
                    <Crown className="w-4 h-4 text-purple-300" />
                    <span>Level {matchData.opponent.level}</span>
                  </div>
                  {matchData.opponent.clan && (
                    <p className="text-xs text-red-200 mt-1">{matchData.opponent.clan.name}</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto p-6">
        {/* DEBUG: 3-Window Layout Version Check */}
        <div className="bg-green-500 text-black text-center p-2 mb-4 rounded font-bold">
          ✅ NEW 3-WINDOW LAYOUT LOADED - v2.0
        </div>
        
        {/* DEBUG: Video State Panel */}
        <div className="bg-yellow-500 text-black text-center p-2 mb-4 rounded text-sm">
          📊 DEBUG: Video URL: {currentVideoUrl ? 'LOADED' : 'NOT LOADED'} | 
          File: {uploadedFileName || 'NONE'} | 
          Duration: {formatTime(duration)} | 
          Playing: {isPlaying ? 'YES' : 'NO'}
        </div>
        
        {/* 3-Window Layout - Updated for better visibility */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 min-h-[600px]">
          
          {/* WINDOW 1: Upload/Video Selection Window (Left) */}
          <div className="bg-gray-800 rounded-lg border-2 border-blue-400 overflow-hidden">
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-3 border-b border-blue-400">
              <h3 className="font-bold text-white flex items-center gap-2">
                <Upload className="w-5 h-5" />
                Video Selection
              </h3>
            </div>
            <div className="p-4 space-y-4">
              {/* Hidden file input */}
              <input
                ref={fileInputRef}
                type="file"
                accept="video/mp4,video/webm,video/ogg"
                onChange={handleFileUpload}
                className="hidden"
              />
              
              {/* Video Info */}
              <div className="bg-gray-700 rounded p-3">
                <h4 className="text-sm font-semibold text-blue-400 mb-2">Current Video</h4>
                <div className="text-sm text-gray-300">
                  <p>📹 {uploadedFileName || 'Clash Royale Gameplay'}</p>
                  <p>⏱️ Duration: {formatTime(duration)}</p>
                  <p>🎮 Battle Analysis Mode</p>
                </div>
              </div>

              {/* Upload New Video */}
              <div className="bg-gray-700 rounded p-3">
                <h4 className="text-sm font-semibold text-green-400 mb-2">Upload New</h4>
                <button 
                  onClick={openFileDialog}
                  className="w-full bg-green-600 hover:bg-green-700 text-white text-sm py-2 px-3 rounded transition-colors flex items-center justify-center gap-2"
                >
                  <Upload className="w-4 h-4" />
                  Select Video File
                </button>
                <p className="text-xs text-gray-400 mt-2">
                  Browser-compatible formats: MP4 (H.264), WebM, OGG
                  <br />
                  Max 500MB • If your video won't play, try converting to H.264 MP4
                </p>
              </div>

              {/* Video Timeline Navigation */}
              <div className="bg-gray-700 rounded p-3">
                <h4 className="text-sm font-semibold text-yellow-400 mb-2">Quick Navigation</h4>
                <div className="space-y-2">
                  <button 
                    onClick={() => seekTo(0)}
                    className="w-full bg-yellow-600 hover:bg-yellow-700 text-white text-xs py-1 px-2 rounded transition-colors"
                  >
                    ⏮️ Start of Match
                  </button>
                  <button 
                    onClick={() => seekTo(duration * 0.5)}
                    className="w-full bg-yellow-600 hover:bg-yellow-700 text-white text-xs py-1 px-2 rounded transition-colors"
                  >
                    ⏭️ Mid Game
                  </button>
                  <button 
                    onClick={() => seekTo(duration * 0.9)}
                    className="w-full bg-yellow-600 hover:bg-yellow-700 text-white text-xs py-1 px-2 rounded transition-colors"
                  >
                    🏁 End Game
                  </button>
                </div>
              </div>

              {/* Analysis History */}
              <div className="bg-gray-700 rounded p-3">
                <h4 className="text-sm font-semibold text-purple-400 mb-2">Analysis History</h4>
                <div className="text-xs text-gray-400">
                  {savedAnalyses.length > 0 ? (
                    <div className="space-y-1 max-h-32 overflow-y-auto">
                      {savedAnalyses.map((analysis, index) => (
                        <div key={index} className="bg-gray-600 p-2 rounded">
                          <div className="flex justify-between">
                            <span>{formatTime(analysis.timestamp)}</span>
                            <span className="text-green-400">{analysis.recommendation.confidence}%</span>
                          </div>
                          <p className="truncate">{analysis.recommendation.cardToPlace.name}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p>No analyses saved yet</p>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* WINDOW 2: Centre Video Player Window (Middle) */}
          <div className="bg-gray-900 rounded-lg border-2 border-yellow-400 overflow-hidden">
            <div className="bg-gradient-to-r from-yellow-500 to-orange-500 p-3 border-b border-yellow-400">
              <h3 className="font-bold text-black flex items-center gap-2">
                <Play className="w-5 h-5" />
                Match Viewer & Controls
              </h3>
            </div>
            
            {/* Video Display */}
            <div className="relative">
              <video
                ref={videoRef}
                src={currentVideoUrl}
                className="w-full h-80 object-cover"
                onTimeUpdate={handleTimeUpdate}
                onLoadedMetadata={handleLoadedMetadata}
                onError={handleVideoError}
                onCanPlay={handleVideoCanPlay}
                controls={false}
                preload="metadata"
              />
              
              {/* Video Upload Overlay - Shows when no video is loaded */}
              {!currentVideoUrl || currentVideoUrl === "data:video/mp4;base64,demo" ? (
                <div className="absolute inset-0 bg-gray-800 bg-opacity-90 flex items-center justify-center">
                  <div className="text-center">
                    <Upload className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-300 mb-2">No video loaded</p>
                    <button
                      onClick={openFileDialog}
                      className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded transition-colors"
                    >
                      Upload Video
                    </button>
                  </div>
                </div>
              ) : null}
              
              {/* Analysis Overlay */}
              {analysisResult && (
                <div className="absolute inset-0 pointer-events-none">
                  <div 
                    className="absolute w-8 h-8 bg-green-500 rounded-full border-4 border-white animate-pulse"
                    style={{
                      left: `${analysisResult.recommendation.position.x * 100}%`,
                      top: `${analysisResult.recommendation.position.y * 100}%`,
                      transform: 'translate(-50%, -50%)'
                    }}
                  >
                    <Target className="w-4 h-4 text-white absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2" />
                  </div>
                </div>
              )}
            </div>

            {/* Video Controls */}
            <div className="p-4 bg-gray-800">
              <div className="flex items-center gap-3 mb-4">
                <button
                  onClick={togglePlayPause}
                  className="bg-blue-600 hover:bg-blue-700 p-2 rounded-full transition-colors"
                >
                  {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                </button>

                <button
                  onClick={() => seekTo(0)}
                  className="bg-gray-600 hover:bg-gray-700 p-2 rounded transition-colors"
                >
                  <RotateCcw className="w-3 h-3" />
                </button>

                <div className="flex-1">
                  <input
                    type="range"
                    min="0"
                    max={duration}
                    value={currentTime}
                    onChange={(e) => seekTo(Number(e.target.value))}
                    className="w-full h-2 bg-gray-600 rounded-lg appearance-none cursor-pointer"
                  />
                </div>

                <span className="text-xs text-gray-300">
                  {formatTime(currentTime)} / {formatTime(duration)}
                </span>
              </div>

              {/* Analysis Button */}
              <button
                onClick={analyzeCurrentFrame}
                disabled={isAnalyzing}
                className="w-full bg-gradient-to-r from-green-500 to-blue-500 hover:from-green-600 hover:to-blue-600 disabled:from-gray-500 disabled:to-gray-600 p-3 rounded-lg font-bold text-white transition-all transform hover:scale-105 disabled:scale-100 flex items-center justify-center gap-2"
              >
                {isAnalyzing ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Zap className="w-4 h-4" />
                    Analyze This Moment
                  </>
                )}
              </button>
            </div>
          </div>

          {/* WINDOW 3: Game Data & Analysis Window (Right) */}
          <div className="bg-gray-800 rounded-lg border-2 border-green-400 overflow-hidden">
            <div className="bg-gradient-to-r from-green-600 to-teal-600 p-3 border-b border-green-400">
              <h3 className="font-bold text-white flex items-center gap-2">
                <Shield className="w-5 h-5" />
                Game Data & Analysis
              </h3>
            </div>
            
            <div className="p-4 space-y-4 max-h-[500px] overflow-y-auto">
              {/* Current Analysis Results */}
              {analysisResult && (
                <div className="bg-green-900/30 border border-green-500 rounded p-3">
                  <h4 className="text-sm font-bold text-green-400 mb-2 flex items-center gap-1">
                    <Target className="w-4 h-4" />
                    Current Analysis
                  </h4>
                  
                  {/* Recommended Card */}
                  <div className="mb-3">
                    <div className={`bg-gradient-to-r ${getRarityColor(analysisResult.recommendation.cardToPlace.rarity)} p-2 rounded text-xs`}>
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-white rounded border">
                          <span className="text-xs">💳</span>
                        </div>
                        <div>
                          <h5 className="font-bold text-white">{analysisResult.recommendation.cardToPlace.name}</h5>
                          <p className="text-white/80">
                            {analysisResult.recommendation.cardToPlace.elixir} Elixir • Level {analysisResult.recommendation.cardToPlace.level}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Confidence & Reasoning */}
                  <div className="mb-3">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-gray-300">Confidence</span>
                      <span className="font-bold text-green-400 text-xs">{analysisResult.recommendation.confidence}%</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-1">
                      <div 
                        className="bg-green-500 h-1 rounded-full"
                        style={{ width: `${analysisResult.recommendation.confidence}%` }}
                      />
                    </div>
                  </div>

                  <div className="mb-3">
                    <h6 className="font-semibold mb-1 text-blue-400 text-xs">Analysis</h6>
                    <p className="text-xs text-gray-300">{analysisResult.recommendation.reasoning}</p>
                  </div>

                  {/* Game State */}
                  <div className="grid grid-cols-2 gap-2 mb-3">
                    <div className="bg-blue-600 p-2 rounded text-center">
                      <p className="text-xs text-blue-200">Your Elixir</p>
                      <p className="text-sm font-bold">{analysisResult.currentSituation.playerElixir}</p>
                    </div>
                    <div className="bg-red-600 p-2 rounded text-center">
                      <p className="text-xs text-red-200">Opponent Elixir</p>
                      <p className="text-sm font-bold">{analysisResult.currentSituation.opponentElixir}</p>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex gap-2">
                    <button
                      onClick={saveAnalysis}
                      className="flex-1 bg-blue-600 hover:bg-blue-700 p-2 rounded font-medium flex items-center justify-center gap-1 transition-colors text-xs"
                    >
                      <Save className="w-3 h-3" />
                      Save
                    </button>
                    <button className="flex-1 bg-purple-600 hover:bg-purple-700 p-2 rounded font-medium flex items-center justify-center gap-1 transition-colors text-xs">
                      <Share2 className="w-3 h-3" />
                      Share
                    </button>
                  </div>
                </div>
              )}

              {/* Deck Information */}
              {matchData && (
                <div className="bg-gray-700 rounded p-3">
                  <h4 className="text-sm font-bold text-blue-400 mb-2 flex items-center gap-1">
                    <Swords className="w-4 h-4" />
                    Battle Decks
                  </h4>

                  {/* Player Deck */}
                  <div className="mb-3">
                    <h5 className="font-semibold mb-2 text-green-400 text-xs">Your Deck</h5>
                    <div className="grid grid-cols-4 gap-1">
                      {matchData.player.deck.map((card, index) => (
                        <div key={index} className={`bg-gradient-to-r ${getRarityColor(card.rarity)} p-1 rounded relative`}>
                          <div className="w-full h-8 bg-white rounded text-xs flex items-center justify-center">💳</div>
                          <div className="absolute -top-1 -right-1 bg-purple-600 text-white text-xs rounded-full w-3 h-3 flex items-center justify-center">
                            {card.level}
                          </div>
                          <div className="absolute -bottom-1 -left-1 bg-pink-600 text-white text-xs rounded-full w-3 h-3 flex items-center justify-center">
                            {card.elixir}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Opponent Deck */}
                  <div>
                    <h5 className="font-semibold mb-2 text-red-400 text-xs">Opponent Deck</h5>
                    <div className="grid grid-cols-4 gap-1">
                      {matchData.opponent.deck.map((card, index) => (
                        <div key={index} className={`bg-gradient-to-r ${getRarityColor(card.rarity)} p-1 rounded relative`}>
                          <div className="w-full h-8 bg-white rounded text-xs flex items-center justify-center">💳</div>
                          <div className="absolute -top-1 -right-1 bg-purple-600 text-white text-xs rounded-full w-3 h-3 flex items-center justify-center">
                            {card.level}
                          </div>
                          <div className="absolute -bottom-1 -left-1 bg-pink-600 text-white text-xs rounded-full w-3 h-3 flex items-center justify-center">
                            {card.elixir}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Development Log */}
              <div className="bg-gray-700 rounded p-3">
                <h4 className="text-sm font-bold text-purple-400 mb-2 flex items-center gap-1">
                  <Clock className="w-4 h-4" />
                  Development Log
                </h4>
                <div className="text-xs text-gray-400 space-y-1">
                  <div className="bg-gray-600 p-2 rounded">
                    <span className="text-green-400">✅</span> VideoAnalyzer: 3-window layout implemented
                  </div>
                  <div className="bg-gray-600 p-2 rounded">
                    <span className="text-blue-400">🔄</span> Analysis engine: Mock data active
                  </div>
                  <div className="bg-gray-600 p-2 rounded">
                    <span className="text-yellow-400">⚠️</span> Backend: API integration pending
                  </div>
                  <div className="bg-gray-600 p-2 rounded">
                    <span className="text-purple-400">📋</span> Features: Upload, analyze, save ready
                  </div>
                </div>
              </div>

              {/* Performance Stats */}
              <div className="bg-gray-700 rounded p-3">
                <h4 className="text-sm font-bold text-orange-400 mb-2">📊 Session Stats</h4>
                <div className="text-xs text-gray-300 space-y-1">
                  <div className="flex justify-between">
                    <span>Analyses Run:</span>
                    <span className="text-green-400">{savedAnalyses.length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Video Duration:</span>
                    <span className="text-blue-400">{formatTime(duration)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Current Time:</span>
                    <span className="text-yellow-400">{formatTime(currentTime)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Progress:</span>
                    <span className="text-purple-400">{duration > 0 ? Math.round((currentTime / duration) * 100) : 0}%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VideoAnalyzer;
