import React, { useState, lazy, Suspense } from 'react';
import PropTypes from 'prop-types';

// Lazy load components
const LagCurveChart = lazy(() => import('./LagCurveChart'));
const RegressionResults = lazy(() => import('./RegressionResults'));

const ModalTabs = ({ grangerContent }) => {
  const [activeTab, setActiveTab] = useState('Granger');
  const [loadedTabs, setLoadedTabs] = useState(new Set(['Granger']));

  const tabs = ['Granger', 'Lag Curve', 'Regression'];

  const handleTabClick = (tab) => {
    setActiveTab(tab);
    if (!loadedTabs.has(tab)) {
      setLoadedTabs(new Set([...loadedTabs, tab]));
    }
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'Granger':
        return <div className="granger-content">{grangerContent}</div>;
      case 'Lag Curve':
        return loadedTabs.has('Lag Curve') ? (
          <Suspense fallback={<div>Loading...</div>}>
            <LagCurveChart />
          </Suspense>
        ) : null;
      case 'Regression':
        return loadedTabs.has('Regression') ? (
          <Suspense fallback={<div>Loading...</div>}>
            <RegressionResults />
          </Suspense>
        ) : null;
      default:
        return null;
    }
  };

  return (
    <div className="modal-tabs">
      <div className="tab-bar" role="tablist">
        {tabs.map((tab) => (
          <button
            key={tab}
            role="tab"
            className={`tab ${activeTab === tab ? 'active' : ''}`}
            aria-selected={activeTab === tab}
            onClick={() => handleTabClick(tab)}
          >
            {tab}
          </button>
        ))}
      </div>
      <div className="tab-content" role="tabpanel">
        {renderContent()}
      </div>
    </div>
  );
};

ModalTabs.propTypes = {
  grangerContent: PropTypes.node
};

ModalTabs.defaultProps = {
  grangerContent: null
};

export default ModalTabs;