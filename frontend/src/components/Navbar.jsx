import React from 'react';
import { Activity, LogIn, UserPlus, LogOut } from 'lucide-react';
import { MarketStatus } from './MarketStatus';
import { ThemeToggle } from './ThemeToggle';
import { useWatchlist } from '../context/WatchlistContext';

export const Navbar = () => {
  const { user, logout, openAuth } = useWatchlist();

  return (
    <header className="navbar">
      <div className="navbar-container">
        <div className="navbar-brand">
          <div className="brand-icon">
            <Activity size={20} />
          </div>
          <span className="brand-name">GrowwPulse</span>
          <span className="brand-badge">Change-First Watchlist</span>
        </div>

        <div className="navbar-actions">
          <MarketStatus />
          
          <ThemeToggle />

          {user ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div className="auth-btn" title={user.email || user.name}>
                <div className="user-avatar">
                  {user.name ? user.name[0].toUpperCase() : (user.email ? user.email[0].toUpperCase() : 'U')}
                </div>
                <span style={{ maxWidth: '130px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontWeight: 600 }}>
                  {user.name || (user.email ? user.email.split('@')[0] : 'User')}
                </span>
              </div>
              <button
                onClick={logout}
                className="icon-btn"
                title="Sign Out"
                aria-label="Sign Out"
              >
                <LogOut size={16} />
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <button
                onClick={() => openAuth('login')}
                className="btn-secondary"
                style={{ padding: '6px 14px', fontSize: '0.82rem', display: 'flex', alignItems: 'center', gap: '6px', borderRadius: 'var(--radius-md)' }}
                title="Sign In to your account"
              >
                <LogIn size={14} />
                <span>Sign In</span>
              </button>
              <button
                onClick={() => openAuth('register')}
                className="btn-primary"
                style={{ padding: '6px 14px', fontSize: '0.82rem', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', gap: '6px' }}
                title="Create a new account"
              >
                <UserPlus size={14} />
                <span>Create Account</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
