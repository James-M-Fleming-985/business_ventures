import React, { useEffect } from 'react';
import { useRouter } from 'next/router';

const UploadPage: React.FC = () => {
  const router = useRouter();

  useEffect(() => {
    // Redirect to dashboard battle analysis tab
    router.push('/dashboard?tab=battleAnalysis');
  }, [router]);

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-900 via-blue-800 to-purple-900 text-white flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-400 mx-auto mb-4"></div>
        <p className="text-lg text-gray-300">Redirecting to Battle Analysis...</p>
      </div>
    </div>
  );
};

export default UploadPage;
