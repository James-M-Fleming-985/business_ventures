import React, { useState, useEffect } from 'react';
import './RegressionResults.css';

const RegressionResults = ({ datasetId, xVariable, yVariable }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [regressionData, setRegressionData] = useState(null);

  useEffect(() => {
    const fetchRegressionData = async () => {
      if (!datasetId || !xVariable || !yVariable) {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);
        
        const response = await fetch(`/api/regression/${datasetId}?x=${xVariable}&y=${yVariable}`);
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        setRegressionData(data);
      } catch (err) {
        setError(err.message || 'Failed to fetch regression data');
      } finally {
        setLoading(false);
      }
    };

    fetchRegressionData();
  }, [datasetId, xVariable, yVariable]);

  const formatPValue = (pValue) => {
    if (!pValue && pValue !== 0) return 'N/A';
    
    let stars = '';
    if (pValue < 0.001) {
      stars = '***';
    } else if (pValue < 0.01) {
      stars = '**';
    } else if (pValue < 0.05) {
      stars = '*';
    }
    
    return `${pValue.toFixed(4)}${stars}`;
  };

  if (loading) {
    return (
      <div className="regression-results-loading">
        <div className="spinner"></div>
        <p>Loading regression analysis...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="regression-results-error">
        <p>Error: {error}</p>
      </div>
    );
  }

  if (!regressionData) {
    return null;
  }

  return (
    <div className="regression-results">
      <div className="beta-display">
        <h2>β₁ = {regressionData.beta_1?.toFixed(4) || 'N/A'}</h2>
      </div>
      
      <div className="regression-formula">
        <p>
          {yVariable} = {regressionData.beta_0?.toFixed(4) || 'N/A'} + 
          {regressionData.beta_1?.toFixed(4) || 'N/A'} × {xVariable}
        </p>
      </div>
      
      <div className="metrics-grid">
        <div className="metric-item">
          <span className="metric-label">R²</span>
          <span className="metric-value">
            {regressionData.r_squared?.toFixed(4) || 'N/A'}
          </span>
        </div>
        
        <div className="metric-item">
          <span className="metric-label">p-value</span>
          <span className="metric-value">
            {formatPValue(regressionData.p_value)}
          </span>
        </div>
        
        <div className="metric-item">
          <span className="metric-label">95% CI</span>
          <span className="metric-value">
            [{regressionData.confidence_interval?.[0]?.toFixed(4) || 'N/A'}, 
             {regressionData.confidence_interval?.[1]?.toFixed(4) || 'N/A'}]
          </span>
        </div>
      </div>
    </div>
  );
};

export default RegressionResults;