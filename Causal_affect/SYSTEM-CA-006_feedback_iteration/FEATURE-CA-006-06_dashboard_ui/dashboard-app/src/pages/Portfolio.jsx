import React from 'react';
import { Link } from 'react-router-dom';
import { usePortfolioStore } from '../stores/portfolioStore';

function Portfolio() {
  const mvps = usePortfolioStore((state) => state.mvps);

  return (
    <div className="portfolio" data-testid="portfolio-page">
      <h1>Portfolio</h1>
      <div className="mvp-list">
        {mvps.map((mvp) => (
          <div key={mvp.id} className="mvp-card">
            <h3>{mvp.name}</h3>
            <p>{mvp.description}</p>
            <Link to={`/mvp/${mvp.id}`}>View Details</Link>
          </div>
        ))}
      </div>
    </div>
  );
}

export default Portfolio;