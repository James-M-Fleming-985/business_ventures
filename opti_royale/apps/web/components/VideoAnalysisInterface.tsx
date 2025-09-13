import React, { useState } from 'react';
import { Upload, Play, Clock, CheckCircle, AlertCircle, Zap } from 'lucide-react';

interface VideoAnalysisInterfaceProps {
  onAnalysisComplete?: (results: any) => void;
}

interface AnalysisStatus {
  id: string;
  status: 'idle' | 'uploading' | 'processing' | 'completed' | 'error';
  progress: number;
  results?: any;
  error?: string;
}

const VideoAnalysisInterface: React.FC<VideoAnalysisInterfaceProps> = ({ onAnalysisComplete }) => {
  const [analysisStatus, setAnalysisStatus] = useState<AnalysisStatus>({
    id: '',
    status: 'idle',
    progress: 0
  });
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // Validate file type
      const allowedTypes = ['video/mp4', 'video/quicktime', 'video/x-m4v'];
      if (allowedTypes.includes(file.type)) {
        setSelectedFile(file);
        setAnalysisStatus(prev => ({ ...prev, status: 'idle', error: undefined }));
      } else {
        setAnalysisStatus(prev => ({ 
          ...prev, 
          status: 'error', 
          error: 'Please upload a valid video file (MP4, MOV, M4V)' 
        }));
      }
    }
  };

  const startAnalysis = async () => {
    if (!selectedFile) return;

    try {
      setAnalysisStatus(prev => ({ ...prev, status: 'uploading', progress: 0 }));

      // Simulate file upload progress
      for (let i = 0; i <= 100; i += 10) {
        setAnalysisStatus(prev => ({ ...prev, progress: i }));
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      // Simulate processing
      setAnalysisStatus(prev => ({ ...prev, status: 'processing', progress: 0 }));
      
      // Mock analysis results (in production this would call the API)
      const mockResults = await simulateAnalysis();
      
      setAnalysisStatus(prev => ({ 
        ...prev, 
        status: 'completed', 
        progress: 100,
        results: mockResults 
      }));

      onAnalysisComplete?.(mockResults);

    } catch (error) {
      setAnalysisStatus(prev => ({ 
        ...prev, 
        status: 'error', 
        error: 'Analysis failed. Please try again.' 
      }));
    }
  };

  const simulateAnalysis = async (): Promise<any> => {
    // Simulate processing time
    for (let i = 0; i <= 100; i += 5) {
      setAnalysisStatus(prev => ({ ...prev, progress: i }));
      await new Promise(resolve => setTimeout(resolve, 150));
    }

    return {
      overallScore: 87,
      confidence: 0.92,
      recommendations: [
        {
          type: 'placement',
          title: 'Optimize Giant Placement',
          description: 'Place Giant at the bridge for immediate pressure',
          confidence: 0.91
        },
        {
          type: 'timing',
          title: 'Improve Support Timing', 
          description: 'Deploy support troops 2 seconds after Giant',
          confidence: 0.88
        }
      ],
      frameAnalysis: [
        {
          timestamp: 15,
          detectedCards: ['Giant', 'Wizard'],
          placement: {
            recommended: { x: 220, y: 280 },
            confidence: 0.89
          }
        }
      ]
    };
  };

  const resetAnalysis = () => {
    setAnalysisStatus({ id: '', status: 'idle', progress: 0 });
    setSelectedFile(null);
  };

  const getStatusIcon = () => {
    switch (analysisStatus.status) {
      case 'uploading':
      case 'processing':
        return <Clock className="w-5 h-5 animate-spin text-blue-400" />;
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-400" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-400" />;
      default:
        return <Upload className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusMessage = () => {
    switch (analysisStatus.status) {
      case 'uploading':
        return `Uploading video... ${analysisStatus.progress}%`;
      case 'processing':
        return `Analyzing video... ${analysisStatus.progress}%`;
      case 'completed':
        return `Analysis complete! Score: ${analysisStatus.results?.overallScore}/100`;
      case 'error':
        return analysisStatus.error || 'An error occurred';
      default:
        return 'Ready to analyze your Clash Royale gameplay';
    }
  };

  return (
    <div style={{
      background: 'linear-gradient(135deg, #1e3a8a, #7c3aed)',
      borderRadius: '12px',
      padding: '24px',
      border: '2px solid #fbbf24',
      boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)'
    }}>
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ 
          fontSize: '24px', 
          fontWeight: 'bold', 
          color: '#fbbf24',
          marginBottom: '8px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <Zap className="w-6 h-6" />
          Video Analysis
        </h2>
        <p style={{ color: '#e5e7eb', fontSize: '16px' }}>
          Upload your Clash Royale gameplay videos for AI-powered analysis and optimization recommendations
        </p>
      </div>

      {analysisStatus.status === 'idle' && (
        <div>
          <input
            type="file"
            accept="video/mp4,video/quicktime,video/x-m4v"
            onChange={handleFileSelect}
            style={{ display: 'none' }}
            id="video-upload"
          />
          <label
            htmlFor="video-upload"
            style={{
              display: 'block',
              padding: '32px',
              border: '2px dashed #6b7280',
              borderRadius: '8px',
              textAlign: 'center',
              cursor: 'pointer',
              backgroundColor: 'rgba(255, 255, 255, 0.05)',
              transition: 'all 0.3s ease',
              marginBottom: '16px'
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.borderColor = '#fbbf24';
              e.currentTarget.style.backgroundColor = 'rgba(251, 191, 36, 0.1)';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.borderColor = '#6b7280';
              e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
            }}
          >
            <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p style={{ color: '#e5e7eb', fontSize: '18px', marginBottom: '8px' }}>
              {selectedFile ? selectedFile.name : 'Click to upload video'}
            </p>
            <p style={{ color: '#9ca3af', fontSize: '14px' }}>
              Supports MP4, MOV, M4V files • Max 100MB
            </p>
          </label>

          {selectedFile && (
            <button
              onClick={startAnalysis}
              style={{
                width: '100%',
                padding: '12px 24px',
                background: 'linear-gradient(90deg, #fbbf24, #f59e0b)',
                border: 'none',
                borderRadius: '8px',
                color: '#1f2937',
                fontSize: '16px',
                fontWeight: 'bold',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                transition: 'transform 0.2s ease'
              }}
              onMouseOver={(e) => e.currentTarget.style.transform = 'scale(1.02)'}
              onMouseOut={(e) => e.currentTarget.style.transform = 'scale(1)'}
            >
              <Play className="w-5 h-5" />
              Start Analysis
            </button>
          )}
        </div>
      )}

      {(analysisStatus.status === 'uploading' || analysisStatus.status === 'processing') && (
        <div>
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '12px',
            marginBottom: '16px'
          }}>
            {getStatusIcon()}
            <span style={{ color: '#e5e7eb', fontSize: '16px' }}>
              {getStatusMessage()}
            </span>
          </div>
          
          <div style={{
            width: '100%',
            height: '8px',
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
            borderRadius: '4px',
            overflow: 'hidden'
          }}>
            <div style={{
              width: `${analysisStatus.progress}%`,
              height: '100%',
              background: 'linear-gradient(90deg, #fbbf24, #f59e0b)',
              transition: 'width 0.3s ease'
            }} />
          </div>
        </div>
      )}

      {analysisStatus.status === 'completed' && analysisStatus.results && (
        <div>
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '12px',
            marginBottom: '16px'
          }}>
            {getStatusIcon()}
            <span style={{ color: '#10b981', fontSize: '16px', fontWeight: 'bold' }}>
              {getStatusMessage()}
            </span>
          </div>

          <div style={{
            background: 'rgba(16, 185, 129, 0.1)',
            border: '1px solid #10b981',
            borderRadius: '8px',
            padding: '16px',
            marginBottom: '16px'
          }}>
            <h3 style={{ color: '#10b981', fontSize: '18px', fontWeight: 'bold', marginBottom: '8px' }}>
              Analysis Results
            </h3>
            <div style={{ color: '#e5e7eb' }}>
              <p><strong>Overall Score:</strong> {analysisStatus.results.overallScore}/100</p>
              <p><strong>Confidence:</strong> {Math.round(analysisStatus.results.confidence * 100)}%</p>
              <p><strong>Recommendations:</strong> {analysisStatus.results.recommendations.length} found</p>
            </div>
          </div>

          <button
            onClick={resetAnalysis}
            style={{
              width: '100%',
              padding: '12px 24px',
              background: 'linear-gradient(90deg, #6366f1, #8b5cf6)',
              border: 'none',
              borderRadius: '8px',
              color: 'white',
              fontSize: '16px',
              fontWeight: 'bold',
              cursor: 'pointer'
            }}
          >
            Analyze Another Video
          </button>
        </div>
      )}

      {analysisStatus.status === 'error' && (
        <div>
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '12px',
            marginBottom: '16px'
          }}>
            {getStatusIcon()}
            <span style={{ color: '#ef4444', fontSize: '16px' }}>
              {getStatusMessage()}
            </span>
          </div>

          <button
            onClick={resetAnalysis}
            style={{
              width: '100%',
              padding: '12px 24px',
              background: 'linear-gradient(90deg, #6b7280, #4b5563)',
              border: 'none',
              borderRadius: '8px',
              color: 'white',
              fontSize: '16px',
              fontWeight: 'bold',
              cursor: 'pointer'
            }}
          >
            Try Again
          </button>
        </div>
      )}
    </div>
  );
};

export default VideoAnalysisInterface;
