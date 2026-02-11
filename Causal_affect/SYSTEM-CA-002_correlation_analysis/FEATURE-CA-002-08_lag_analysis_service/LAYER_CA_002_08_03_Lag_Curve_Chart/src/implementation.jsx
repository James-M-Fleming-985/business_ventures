import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceDot } from 'recharts';

const LagCurveChart = () => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchLagCurveData = async () => {
      try {
        setLoading(true);
        // Simulating API call - replace with actual API endpoint
        const response = await fetch('/api/lag-curve-data');
        
        if (!response.ok) {
          throw new Error('Failed to fetch lag curve data');
        }

        const result = await response.json();
        setData(result);
        setError(null);
      } catch (err) {
        setError(err.message);
        setData(null);
      } finally {
        setLoading(false);
      }
    };

    fetchLagCurveData();
  }, []);

  if (loading) {
    return (
      <div className="loading-spinner-container" style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '400px' 
      }}>
        <div className="loading-spinner" style={{
          border: '4px solid #f3f3f3',
          borderTop: '4px solid #3498db',
          borderRadius: '50%',
          width: '40px',
          height: '40px',
          animation: 'spin 1s linear infinite'
        }}></div>
        <style jsx>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-message" style={{ 
        color: 'red', 
        textAlign: 'center', 
        padding: '20px',
        backgroundColor: '#fee',
        border: '1px solid #fcc',
        borderRadius: '4px',
        margin: '20px'
      }}>
        Error: {error}
      </div>
    );
  }

  if (!data || !data.lagCurveData) {
    return null;
  }

  const { lagCurveData, optimalLag, maxCorrelation } = data;

  return (
    <div className="lag-curve-chart-container">
      <LineChart 
        width={800} 
        height={400} 
        data={lagCurveData}
        margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis 
          dataKey="lag" 
          label={{ value: 'Lag', position: 'insideBottom', offset: -10 }}
        />
        <YAxis 
          label={{ value: 'Correlation', angle: -90, position: 'insideLeft' }}
          domain={[-1, 1]}
        />
        <Tooltip />
        <Legend />
        <Line 
          type="monotone" 
          dataKey="correlation" 
          stroke="#8884d8" 
          strokeWidth={2}
          dot={false}
          name="Correlation"
        />
        {optimalLag !== null && optimalLag !== undefined && (
          <ReferenceDot
            x={optimalLag}
            y={maxCorrelation}
            r={8}
            fill="red"
            stroke="red"
          />
        )}
      </LineChart>
      
      {optimalLag !== null && optimalLag !== undefined && maxCorrelation !== null && maxCorrelation !== undefined && (
        <div className="summary-text" style={{
          marginTop: '20px',
          padding: '15px',
          backgroundColor: '#f0f0f0',
          borderRadius: '4px',
          textAlign: 'center'
        }}>
          <p style={{ margin: '5px 0', fontSize: '16px', fontWeight: 'bold' }}>
            Optimal Lag: {optimalLag}
          </p>
          <p style={{ margin: '5px 0', fontSize: '16px', fontWeight: 'bold' }}>
            Maximum Correlation: {maxCorrelation.toFixed(4)}
          </p>
        </div>
      )}
    </div>
  );
};

export default LagCurveChart;