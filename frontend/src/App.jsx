import React from 'react';
import { Navbar } from './components/Navbar';
import { LandingPage } from './components/LandingPage';
import { HeroSummary } from './components/HeroSummary';
import { MarketPulse } from './components/MarketPulse';
import { Watchlist } from './components/Watchlist';
import { ExplainabilityModal } from './components/ExplainabilityModal';
import { CompanyPeek } from './components/CompanyPeek';
import { AddStockModal } from './components/AddStockModal';
import { AuthModal } from './components/AuthModal';
import { useWatchlist } from './context/WatchlistContext';
import { AlertCircle } from 'lucide-react';

export const App = () => {
  const { user, error } = useWatchlist();

  return (
    <div className="app-layout">
      <Navbar />

      {!user ? (
        /* Landing page before logging in with overview & tagline */
        <LandingPage />
      ) : (
        /* Protected Market Watchlist Dashboard: Accessible ONLY after logging in */
        <main className="main-content">
          {error && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              padding: '12px 18px',
              background: 'var(--sig-subtle)',
              border: '1px solid var(--sig-border)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--sig-color)',
              fontSize: '0.88rem'
            }}>
              <AlertCircle size={18} />
              <span>{error}</span>
            </div>
          )}

          <HeroSummary />

          <MarketPulse />

          <Watchlist />
        </main>
      )}

      {/* Interactive Overlays */}
      <ExplainabilityModal />
      <CompanyPeek />
      <AddStockModal />
      <AuthModal />
    </div>
  );
};
export default App;
