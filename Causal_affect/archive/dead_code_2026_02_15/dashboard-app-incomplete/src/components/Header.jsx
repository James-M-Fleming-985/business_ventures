import React from 'react';
import { Link } from 'react-router-dom';
import { useNotificationStore } from '../stores/notificationStore';

function Header({ onMenuToggle, isMobile }) {
  const notifications = useNotificationStore((state) => state.notifications);

  return (
    <header className="header" data-testid="header">
      {isMobile && (
        <button 
          onClick={onMenuToggle} 
          className="menu-toggle"
          data-testid="menu-toggle"
        >
          ☰
        </button>
      )}
      <div className="logo" data-testid="logo">
        <Link to="/">Dashboard</Link>
      </div>
      <div className="header-actions">
        <div className="notifications" data-testid="notifications">
          🔔 {notifications.length}
        </div>
        <div className="user-menu" data-testid="user-menu">
          👤 User
        </div>
      </div>
    </header>
  );
}

export default Header;