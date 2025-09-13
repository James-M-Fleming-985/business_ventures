import React from 'react';
import { useRouter } from 'next/router';

function HomePage() {
  const router = useRouter();

  React.useEffect(() => {
    router.push('/dashboard');
  }, [router]);

  return (
    <div style={{ 
      minHeight: '100vh', 
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      color: 'white',
      fontFamily: 'Arial, sans-serif'
    }}>
      <div style={{ textAlign: 'center' }}>
        <h1 style={{ fontSize: '2rem', marginBottom: '1rem' }}>Opti Royale</h1>
        <p>Loading your Clash Royale analysis platform...</p>
      </div>
    </div>
  );
}

export default HomePage;
