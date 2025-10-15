import React, { useState, useEffect } from 'react';
import Header from './Header';
import MobileDrawer from './MobileDrawer';

function Layout({ children }) {
  const [isMobile, setIsMobile] = useState(false);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768);
    };
    
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const toggleDrawer = () => {
    setIsDrawerOpen(!isDrawerOpen);
  };

  return (
    <div className="layout">
      <Header onMenuToggle={toggleDrawer} isMobile={isMobile} />
      {isMobile && <MobileDrawer isOpen={isDrawerOpen} onClose={() => setIsDrawerOpen(false)} />}
      <main className="main-content">
        {children}
      </main>
    </div>
  );
}

export default Layout;