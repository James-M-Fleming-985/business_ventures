import json
import subprocess
import tempfile
import os
from pathlib import Path


def create_react_app_structure():
    """Create the React app structure with all required components."""
    
    # Define the complete React app structure
    files = {
        'package.json': {
            "name": "feedback-dashboard",
            "version": "1.0.0",
            "private": True,
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "react-router-dom": "^6.16.0",
                "zustand": "^4.4.1"
            },
            "devDependencies": {
                "@testing-library/react": "^14.0.0",
                "@testing-library/jest-dom": "^6.1.3",
                "@vitejs/plugin-react": "^4.0.4",
                "vite": "^4.4.9",
                "jsdom": "^22.1.0",
                "vitest": "^0.34.6"
            },
            "scripts": {
                "dev": "vite",
                "build": "vite build",
                "test": "vitest run",
                "preview": "vite preview"
            }
        },
        'vite.config.js': '''
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/setupTests.js',
  },
});
''',
        'index.html': '''
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Feedback Dashboard</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
''',
        'src/main.jsx': '''
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
''',
        'src/App.jsx': '''
import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import ErrorBoundary from './components/ErrorBoundary';
import Layout from './components/Layout';
import Portfolio from './pages/Portfolio';
import MVPDetail from './pages/MVPDetail';

function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Portfolio />} />
            <Route path="/portfolio" element={<Portfolio />} />
            <Route path="/mvp/:id" element={<MVPDetail />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;
''',
        'src/components/ErrorBoundary.jsx': '''
import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '20px', textAlign: 'center' }}>
          <h1>Something went wrong</h1>
          <p>{this.state.error?.message || 'An error occurred'}</p>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
''',
        'src/components/Layout.jsx': '''
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
''',
        'src/components/Header.jsx': '''
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
''',
        'src/components/MobileDrawer.jsx': '''
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
''',
        'src/pages/Portfolio.jsx': '''
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
''',
        'src/pages/MVPDetail.jsx': '''
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
''',
        'src/stores/portfolioStore.js': '''
import { create } from 'zustand';

export const usePortfolioStore = create((set) => ({
  mvps: [
    { id: '1', name: 'MVP 1', description: 'First MVP' },
    { id: '2', name: 'MVP 2', description: 'Second MVP' },
  ],
  addMVP: (mvp) => set((state) => ({ mvps: [...state.mvps, mvp] })),
  removeMVP: (id) => set((state) => ({ mvps: state.mvps.filter((m) => m.id !== id) })),
}));
''',
        'src/stores/notificationStore.js': '''
import { create } from 'zustand';

export const useNotificationStore = create((set) => ({
  notifications: [],
  addNotification: (notification) => 
    set((state) => ({ notifications: [...state.notifications, notification] })),
  removeNotification: (id) => 
    set((state) => ({ notifications: state.notifications.filter((n) => n.id !== id) })),
  clearNotifications: () => set({ notifications: [] }),
}));
''',
        'src/index.css': '''
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
}

.layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 2rem;
  background: #333;
  color: white;
}

.header a {
  color: white;
  text-decoration: none;
}

.menu-toggle {
  background: none;
  border: none;
  color: white;
  font-size: 1.5rem;
  cursor: pointer;
}

.header-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.main-content {
  flex: 1;
  padding: 2rem;
}

.mobile-drawer {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1000;
}

.drawer-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
}

.drawer-content {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 250px;
  background: white;
  padding: 1rem;
}

.drawer-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  margin-bottom: 1rem;
}

.drawer-content nav {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.drawer-content nav a {
  padding: 0.5rem;
  text-decoration: none;
  color: #333;
}

.mvp-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}

.mvp-card {
  border: 1px solid #ddd;
  padding: 1rem;
  border-radius: 4px;
}

.mvp-card h3 {
  margin-bottom: 0.5rem;
}

.mvp-card a {
  color: #0066cc;
  text-decoration: none;
}

@media (min-width: 768px) and (max-width: 1024px) {
  .main-content {
    padding: 1.5rem;
  }
  
  .mvp-list {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1024px) {
  .main-content {
    max-width: 1200px;
    margin: 0 auto;
  }
}

@media (max-width: 767px) {
  .header {
    padding: 1rem;
  }
  
  .main-content {
    padding: 1rem;
  }
  
  .mvp-list {
    grid-template-columns: 1fr;
  }
}
''',
        'src/setupTests.js': '''
import '@testing-library/jest-dom';
'''
    }
    
    return files


def setup_react_project(base_path):
    """Set up the React project structure."""
    base_path = Path(base_path)
    base_path.mkdir(parents=True, exist_ok=True)
    
    files = create_react_app_structure()
    
    for file_path, content in files.items():
        full_path = base_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        if isinstance(content, dict):
            with open(full_path, 'w') as f:
                json.dump(content, f, indent=2)
        else:
            with open(full_path, 'w') as f:
                f.write(content.strip())
    
    return base_path


def install_dependencies(project_path):
    """Install npm dependencies."""
    try:
        subprocess.run(['npm', 'install'], cwd=project_path, check=True, 
                      capture_output=True, timeout=300)
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return False


def build_project(project_path):
    """Build the React project."""
    try:
        subprocess.run(['npm', 'run', 'build'], cwd=project_path, check=True,
                      capture_output=True, timeout=300)
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return False


def run_tests(project_path):
    """Run the test suite."""
    try:
        result = subprocess.run(['npm', 'test'], cwd=project_path, 
                              capture_output=True, timeout=60)
        return result.returncode == 0
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return False