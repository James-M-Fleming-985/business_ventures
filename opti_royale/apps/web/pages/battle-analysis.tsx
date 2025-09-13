import React, { useState, useRef, useCallback } from 'react';
import Head from 'next/head';

export default function BattleAnalysis() {
  const [uploadedVideo, setUploadedVideo] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [isDragActive, setIsDragActive] = useState(false);
  const [processingStatus, setProcessingStatus] = useState({
    videoAnalysis: 'Waiting',
    cardDetection: 'Waiting',
    strategyAnalysis: 'Waiting'
  });
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileUpload(files[0]);
    }
  }, []);

  const validateFile = (file: File): boolean => {
    const validTypes = ['video/mp4', 'video/quicktime', 'video/x-m4v'];
    const maxSize = 500 * 1024 * 1024; // 500MB
    
    if (!validTypes.includes(file.type)) {
      alert('Please upload a valid video file (MP4, MOV, M4V)');
      return false;
    }
    
    if (file.size > maxSize) {
      alert('File size must be less than 500MB');
      return false;
    }
    
    return true;
  };

  const handleFileUpload = async (file: File) => {
    if (!validateFile(file)) return;
    
    setIsUploading(true);
    setUploadProgress(0);
    setProcessingStatus({
      videoAnalysis: 'Processing',
      cardDetection: 'Waiting',
      strategyAnalysis: 'Waiting'
    });
    
    try {
      // Create FormData for file upload
      const formData = new FormData();
      formData.append('file', file);
      
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);
      
      // Upload to API (when API is running)
      try {
        const response = await fetch('http://localhost:3003/api/upload/video', {
          method: 'POST',
          body: formData,
        });
        
        if (response.ok) {
          const result = await response.json();
          console.log('Upload successful:', result);
          clearInterval(progressInterval);
          setUploadProgress(100);
        } else {
          console.log('API not available, using local preview');
        }
      } catch (apiError) {
        console.log('API not available, using local preview mode');
      }
      
      // Create video URL for display (always works)
      const url = URL.createObjectURL(file);
      setVideoUrl(url);
      setUploadedVideo(file);
      
      // Complete progress
      clearInterval(progressInterval);
      setUploadProgress(100);
      
      // Simulate processing completion
      setTimeout(() => {
        setIsUploading(false);
        setProcessingStatus({
          videoAnalysis: 'Complete',
          cardDetection: 'Processing',
          strategyAnalysis: 'Waiting'
        });
        
        setTimeout(() => {
          setProcessingStatus({
            videoAnalysis: 'Complete',
            cardDetection: 'Complete',
            strategyAnalysis: 'Processing'
          });
          
          setTimeout(() => {
            setProcessingStatus({
              videoAnalysis: 'Complete',
              cardDetection: 'Complete',
              strategyAnalysis: 'Complete'
            });
          }, 1500);
        }, 1000);
      }, 2000);
      
    } catch (error) {
      console.error('Upload error:', error);
      setIsUploading(false);
      setUploadProgress(0);
      alert('Upload failed. Please try again.');
    }
  };

  const loadTestVideo = () => {
    // Simulate loading a test video
    setProcessingStatus({
      videoAnalysis: 'Complete',
      cardDetection: 'Complete',
      strategyAnalysis: 'Complete'
    });
    alert('Test video loaded (simulated)');
  };

  return (
    <>
      <Head>
        <title>Battle Analysis - OptiRoyale</title>
        <meta name="description" content="Professional Clash Royale battle analysis tool" />
      </Head>
      
      {/* Enhanced 3-Window Battle Analysis Interface - Direct Implementation */}
      <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 text-white">
        
        {/* DEV BANNER */}
        <div className="bg-yellow-600 text-black text-center py-2 font-bold">
          🔧 DEVELOPMENT VERSION - Video Upload & Analysis Features - 3-WINDOW LAYOUT
        </div>

        {/* Header */}
        <div className="bg-gray-900 shadow-lg">
          <div className="container mx-auto px-4 py-3">
            <div className="flex items-center justify-between">
              <h1 className="text-2xl font-bold bg-gradient-to-r from-yellow-400 to-orange-500 bg-clip-text text-transparent">
                🏆 OptiRoyale Pro - 3-Window Layout
              </h1>
              <div className="text-sm text-gray-300">
                Video Analysis Development
              </div>
            </div>
          </div>
        </div>

        <div className="container mx-auto px-4 py-6">
          
          {/* 3-Window Development Layout */}
          <div className="grid grid-cols-12 gap-6 h-screen max-h-[calc(100vh-120px)]">
            
            {/* Window 1: Enhanced Video Upload (Left) */}
            <div className="col-span-3 bg-gray-800 rounded-lg p-4 overflow-y-auto">
              <h2 className="text-lg font-bold mb-4 flex items-center">
                📁 Video Upload & Processing
              </h2>
              
              {/* Upload Zone */}
              <div 
                className={`border-3 border-dashed ${isDragActive ? 'border-green-400 bg-green-400' : 'border-yellow-400 bg-yellow-400'} bg-opacity-10 rounded-lg p-6 text-center mb-4 hover:border-yellow-500 hover:bg-opacity-20 transition-all cursor-pointer`}
                onDragEnter={handleDragEnter}
                onDragLeave={handleDragLeave}
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <div className="text-4xl mb-2">{isDragActive ? '🎯' : '📹'}</div>
                <div className="font-semibold mb-2">
                  {isDragActive ? 'Drop Video Here' : uploadedVideo ? 'Video Uploaded!' : 'Drop Video Here'}
                </div>
                <div className="text-sm text-gray-400 mb-3">MP4, MOV, M4V up to 500MB</div>
                <input 
                  type="file" 
                  accept="video/mp4,video/quicktime,video/x-m4v" 
                  className="hidden" 
                  ref={fileInputRef}
                  onChange={handleFileSelect}
                />
                <button 
                  className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded font-semibold mb-2"
                  onClick={(e) => {
                    e.stopPropagation();
                    fileInputRef.current?.click();
                  }}
                >
                  Browse Files
                </button>
                <div className="text-xs text-gray-500 mb-2">or</div>
                <div className="text-gray-400">
                  {uploadedVideo ? `Selected: ${uploadedVideo.name}` : 'Drag and drop your Clash Royale gameplay'}
                </div>
              </div>

              {/* Quick Test Files */}
              <div className="bg-gray-700 rounded-lg p-3 mb-4">
                <h3 className="font-semibold mb-2">📋 Quick Test</h3>
                <button 
                  className="w-full bg-green-600 hover:bg-green-700 px-3 py-2 rounded text-sm mb-2"
                  onClick={loadTestVideo}
                >
                  Load clash_test.mp4
                </button>
                <div className="text-xs text-gray-400">Sample battle video for testing</div>
              </div>

              {/* Upload Progress */}
              <div className="bg-gray-700 rounded-lg p-3 mb-4">
                <h3 className="font-semibold mb-2">📊 Upload Progress</h3>
                <div className="bg-gray-600 rounded-full h-2 mb-2">
                  <div 
                    className="bg-yellow-400 h-2 rounded-full transition-all duration-300" 
                    style={{width: `${uploadProgress}%`}}
                  ></div>
                </div>
                <div className="text-xs text-gray-400">
                  {isUploading ? `Uploading... ${uploadProgress}%` : uploadedVideo ? 'Upload complete!' : 'Ready to upload'}
                </div>
              </div>

              {/* Processing Status */}
              <div className="bg-gray-700 rounded-lg p-3">
                <h3 className="font-semibold mb-2">⚙️ Processing Status</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>Video Analysis:</span>
                    <span className={`${processingStatus.videoAnalysis === 'Complete' ? 'text-green-400' : processingStatus.videoAnalysis === 'Processing' ? 'text-yellow-400' : 'text-gray-400'}`}>
                      {processingStatus.videoAnalysis}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Card Detection:</span>
                    <span className={`${processingStatus.cardDetection === 'Complete' ? 'text-green-400' : processingStatus.cardDetection === 'Processing' ? 'text-yellow-400' : 'text-gray-400'}`}>
                      {processingStatus.cardDetection}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Strategy Analysis:</span>
                    <span className={`${processingStatus.strategyAnalysis === 'Complete' ? 'text-green-400' : processingStatus.strategyAnalysis === 'Processing' ? 'text-yellow-400' : 'text-gray-400'}`}>
                      {processingStatus.strategyAnalysis}
                    </span>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Window 2: Video Player (Center) */}
            <div className="col-span-6 bg-gray-800 rounded-lg p-4 relative">
              <h2 className="text-lg font-bold mb-4 flex items-center justify-between">
                <span>🎬 Video Analysis Player</span>
                <div className="text-sm text-gray-400">Ready</div>
              </h2>
              
              {/* Video Player Area */}
              <div className="bg-black rounded-lg h-[70%] mb-4 flex items-center justify-center relative">
                {videoUrl ? (
                  <video
                    ref={videoRef}
                    src={videoUrl}
                    className="w-full h-full object-contain rounded-lg"
                    controls
                    onLoadedMetadata={() => {
                      if (videoRef.current) {
                        console.log('Video loaded:', videoRef.current.duration);
                      }
                    }}
                  />
                ) : (
                  <div className="text-gray-500 text-center">
                    <div className="text-6xl mb-4">📹</div>
                    <div className="text-xl">No video loaded</div>
                    <div className="text-sm mt-2">Upload a battle video to begin analysis</div>
                  </div>
                )}
              </div>
              
              {/* Video Controls */}
              <div className="bg-gray-700 rounded-lg p-3">
                <div className="flex items-center space-x-4 mb-3">
                  <button 
                    className={`px-3 py-1 rounded text-sm ${videoUrl ? 'bg-blue-600 hover:bg-blue-700' : 'bg-gray-600'}`}
                    disabled={!videoUrl}
                    onClick={() => {
                      if (videoRef.current) {
                        if (videoRef.current.paused) {
                          videoRef.current.play();
                        } else {
                          videoRef.current.pause();
                        }
                      }
                    }}
                  >
                    ⏯️ Play/Pause
                  </button>
                  <button 
                    className={`px-3 py-1 rounded text-sm ${videoUrl ? 'bg-gray-600 hover:bg-gray-500' : 'bg-gray-600'}`}
                    disabled={!videoUrl}
                    onClick={() => {
                      if (videoRef.current) {
                        videoRef.current.currentTime = Math.max(0, videoRef.current.currentTime - 10);
                      }
                    }}
                  >
                    ⏮️ -10s
                  </button>
                  <button 
                    className={`px-3 py-1 rounded text-sm ${videoUrl ? 'bg-gray-600 hover:bg-gray-500' : 'bg-gray-600'}`}
                    disabled={!videoUrl}
                    onClick={() => {
                      if (videoRef.current) {
                        videoRef.current.currentTime = Math.min(videoRef.current.duration, videoRef.current.currentTime + 10);
                      }
                    }}
                  >
                    ⏭️ +10s
                  </button>
                  <div className="text-sm text-gray-400">
                    {videoRef.current ? `${Math.floor(videoRef.current.currentTime || 0)}s / ${Math.floor(videoRef.current.duration || 0)}s` : '00:00 / 00:00'}
                  </div>
                </div>
                
                {/* Timeline */}
                <div className="bg-gray-600 rounded-full h-2 mb-2 cursor-pointer"
                  onClick={(e) => {
                    if (videoRef.current) {
                      const rect = e.currentTarget.getBoundingClientRect();
                      const percent = (e.clientX - rect.left) / rect.width;
                      videoRef.current.currentTime = percent * videoRef.current.duration;
                    }
                  }}
                >
                  <div className="bg-blue-400 h-2 rounded-full" style={{width: '0%'}}></div>
                </div>
                
                <div className="flex justify-between text-xs text-gray-400">
                  <span>Analysis Speed: 1x</span>
                  <span>Frame: 0/{videoRef.current?.duration ? Math.floor(videoRef.current.duration * 30) : 0}</span>
                </div>
              </div>
            </div>
            
            {/* Window 3: Analysis Results (Right) */}
            <div className="col-span-3 bg-gray-800 rounded-lg p-4 overflow-y-auto">
              <h2 className="text-lg font-bold mb-4 flex items-center">
                📈 Analysis Results
              </h2>
              
              {/* Real-time Stats */}
              <div className="bg-gray-700 rounded-lg p-3 mb-4">
                <h3 className="font-semibold mb-2">⚡ Real-time Stats</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>Elixir Advantage:</span>
                    <span className="text-green-400">+0</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Tower HP:</span>
                    <span className="text-blue-400">100%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Cards Played:</span>
                    <span className="text-yellow-400">0</span>
                  </div>
                </div>
              </div>

              {/* Detected Cards */}
              <div className="bg-gray-700 rounded-lg p-3 mb-4">
                <h3 className="font-semibold mb-2">🃏 Detected Cards</h3>
                <div className="text-sm text-gray-400">No cards detected yet</div>
              </div>

              {/* Strategy Recommendations */}
              <div className="bg-gray-700 rounded-lg p-3 mb-4">
                <h3 className="font-semibold mb-2">💡 Strategy Tips</h3>
                <div className="text-sm text-gray-400">Upload video to see recommendations</div>
              </div>

              {/* Performance Metrics */}
              <div className="bg-gray-700 rounded-lg p-3">
                <h3 className="font-semibold mb-2">📊 Performance</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>Processing FPS:</span>
                    <span className="text-gray-400">--</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Detection Accuracy:</span>
                    <span className="text-gray-400">--</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Analysis Time:</span>
                    <span className="text-gray-400">--</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
