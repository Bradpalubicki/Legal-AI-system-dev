'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { LegalAIHub } from '@/components/LegalAIHub';
import LandingPage from '@/components/LandingPage';
import { NewFilingModal } from '@/components/notifications/NewFilingModal';

export default function Home() {
  const { isAuthenticated, isLoading } = useAuth();

  // New filing notification state
  const [showNewFilingModal, setShowNewFilingModal] = useState(false);
  const [newFilings, setNewFilings] = useState<any[]>([]);
  const [totalNewDocs, setTotalNewDocs] = useState(0);
  const [filingsSince, setFilingsSince] = useState<string | null>(null);

  // Check for new filings data from login redirect
  useEffect(() => {
    console.log('[HOME DEBUG] useEffect - isAuthenticated:', isAuthenticated, 'isLoading:', isLoading);
    if (isAuthenticated && !isLoading) {
      const storedData = sessionStorage.getItem('newFilingsData');
      console.log('[HOME DEBUG] sessionStorage newFilingsData:', storedData ? 'FOUND' : 'NOT FOUND');
      if (storedData) {
        try {
          const data = JSON.parse(storedData);
          setNewFilings(data.cases || []);
          setTotalNewDocs(data.totalDocs || 0);
          setFilingsSince(data.since || null);
          console.log('[HOME DEBUG] Showing modal with', data.cases?.length, 'cases');
          setShowNewFilingModal(true);
          // Clear the data so it doesn't show again on refresh
          sessionStorage.removeItem('newFilingsData');
        } catch (e) {
          console.error('Failed to parse new filings data:', e);
          sessionStorage.removeItem('newFilingsData');
        }
      }
    }
  }, [isAuthenticated, isLoading]);

  // Handle closing the new filing modal
  const handleNewFilingModalClose = () => {
    setShowNewFilingModal(false);
  };

  // Show loading state while checking authentication
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-navy-900 to-navy-800">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-teal-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-navy-200 text-sm">Loading...</p>
        </div>
      </div>
    );
  }

  // Show landing page for non-authenticated users
  if (!isAuthenticated) {
    return <LandingPage />;
  }

  // Show the main dashboard for authenticated users
  return (
    <>
      <LegalAIHub />
      {/* New Filing Notification Modal */}
      <NewFilingModal
        isOpen={showNewFilingModal}
        onClose={handleNewFilingModalClose}
        filings={newFilings}
        totalDocuments={totalNewDocs}
        since={filingsSince}
      />
    </>
  );
}
