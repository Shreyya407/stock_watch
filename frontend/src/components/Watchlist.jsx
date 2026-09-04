import React from 'react';
import { Plus, ArrowUpDown } from 'lucide-react';
import { StockCard } from './StockCard';
import { EmptyState } from './EmptyState';
import { useWatchlist } from '../context/WatchlistContext';

export const Watchlist = () => {
  const { stocks, loading, sortBy, setSortBy, setIsAddModalOpen, rawStocksCount } = useWatchlist();

  return (
    <section className="watchlist-section">
      <div className="watchlist-controls">
        <div className="watchlist-heading-area">
          <h2 className="section-title">Your Watchlist</h2>
          <span className="stock-count-badge">({rawStocksCount} Equities)</span>
        </div>

        <div className="controls-right">
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <ArrowUpDown size={14} color="var(--text-muted)" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="sort-select"
              aria-label="Sort watchlist"
            >
              <option value="attention">Rank by Attention Score</option>
              <option value="change">Rank by % Change</option>
              <option value="volume">Rank by Volume Anomaly</option>
              <option value="alphabetical">Rank Alphabetically</option>
            </select>
          </div>

          <button
            onClick={() => setIsAddModalOpen(true)}
            className="btn-primary"
            style={{ padding: '8px 14px', fontSize: '0.84rem' }}
          >
            <Plus size={15} />
            <span>Add Stock</span>
          </button>
        </div>
      </div>

      {loading ? (
        <div className="stock-grid">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="skeleton skeleton-card" />
          ))}
        </div>
      ) : stocks.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="stock-grid">
          {stocks.map((stock) => (
            <StockCard key={stock.symbol} stock={stock} />
          ))}
        </div>
      )}
    </section>
  );
};
