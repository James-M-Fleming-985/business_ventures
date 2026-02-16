import React from 'react';
import { useParams } from 'react-router-dom';
import { usePortfolioStore } from '../stores/portfolioStore';

function MVPDetail() {
  const { id } = useParams();
  const mvps = usePortfolioStore((state) => state.mvps);
  const mvp = mvps.find((m) => m.id === id);

  return (
    <div className="mvp-detail" data-testid="mvp-detail-page">
      <h1>MVP Detail: {id}</h1>
      {mvp ? (
        <>
          <h2>{mvp.name}</h2>
          <p>{mvp.description}</p>
        </>
      ) : (
        <p>MVP not found</p>
      )}
    </div>
  );
}

export default MVPDetail;