import React from 'react';
import { Plus, ShieldAlert } from 'lucide-react';
import { useWatchlist } from '../context/WatchlistContext';

export const EmptyState = () => {
  const { setIsAddModalOpen } = useWatchlist();

  return (
    <div className="empty-state-box">
      <div className="empty-icon">
        <Plus size={24} />
      </div>
      <h3 className="empty-title">Your watchlist is quiet.</h3>
      <p className="empty-desc">
        Add a few NSE stocks to start seeing what meaningfully changed since your baseline visit.
      </p>
      <button
        onClick={() => setIsAddModalOpen(true)}
        className="btn-primary"
        style={{ marginTop: '8px' }}
      >
        <Plus size={16} />
        <span>+ Add your first stock</span>
      </button>
    </div>
  );
};
