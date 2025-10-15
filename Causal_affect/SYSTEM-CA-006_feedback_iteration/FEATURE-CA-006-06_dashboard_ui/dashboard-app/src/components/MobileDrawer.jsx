import React from 'react';
import { Link } from 'react-router-dom';

function MobileDrawer({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="mobile-drawer" data-testid="mobile-drawer">
      <div className="drawer-overlay" onClick={onClose} />
      <div className="drawer-content">
        <button onClick={onClose} className="drawer-close">✕</button>
        <nav>
          <Link to="/portfolio" onClick={onClose}>Portfolio</Link>
          <Link to="/mvp/1" onClick={onClose}>MVP Detail</Link>
        </nav>
      </div>
    </div>
  );
}

export default MobileDrawer;