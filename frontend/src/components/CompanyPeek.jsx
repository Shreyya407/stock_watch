import React from 'react';
import { X, Building2, TrendingUp, Layers, DollarSign } from 'lucide-react';
import { useWatchlist } from '../context/WatchlistContext';

export const CompanyPeek = () => {
  const { selectedStockForPeek, setSelectedStockForPeek } = useWatchlist();

  if (!selectedStockForPeek) return null;

  const {
    symbol,
    companyName,
    currentPrice,
    details = {},
    source,
    quoteTimestamp
  } = selectedStockForPeek;

  const formatCurrency = (num) => {
    if (!num) return '—';
    return `₹${Number(num).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const formatMarketCap = (num) => {
    if (!num) return '—';
    // Format to Crores
    const inCrores = num / 10000000;
    return `₹${inCrores.toLocaleString('en-IN', { maximumFractionDigits: 0 })} Cr`;
  };

  const formatTimestamp = (ts) => {
    if (!ts) return 'Live';
    try {
      return new Date(ts).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', second: '2-digit', hour12: true });
    } catch (_) {
      return 'Live';
    }
  };

  return (
    <div className="modal-backdrop" onClick={() => setSelectedStockForPeek(null)}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div className="brand-icon" style={{ width: '28px', height: '28px' }}>
              <Building2 size={16} />
            </div>
            <div>
              <h3 className="modal-title">{symbol}</h3>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>{companyName}</span>
            </div>
          </div>

          <button
            onClick={() => setSelectedStockForPeek(null)}
            className="icon-btn"
            aria-label="Close peek"
          >
            <X size={18} />
          </button>
        </div>

        <div className="modal-body">
          <div className="peek-grid">
            <div className="peek-stat">
              <span className="peek-stat-label">Current Price</span>
              <span className="peek-stat-val" style={{ color: 'var(--accent-primary)' }}>
                {formatCurrency(currentPrice)}
              </span>
            </div>

            <div className="peek-stat">
              <span className="peek-stat-label">Previous Close</span>
              <span className="peek-stat-val">{formatCurrency(details.previousClose)}</span>
            </div>

            <div className="peek-stat">
              <span className="peek-stat-label">Day High</span>
              <span className="peek-stat-val">{formatCurrency(details.high)}</span>
            </div>

            <div className="peek-stat">
              <span className="peek-stat-label">Day Low</span>
              <span className="peek-stat-val">{formatCurrency(details.low)}</span>
            </div>

            <div className="peek-stat">
              <span className="peek-stat-label">52 Week High</span>
              <span className="peek-stat-val">{formatCurrency(details.fiftyTwoWeekHigh)}</span>
            </div>

            <div className="peek-stat">
              <span className="peek-stat-label">52 Week Low</span>
              <span className="peek-stat-val">{formatCurrency(details.fiftyTwoWeekLow)}</span>
            </div>

            <div className="peek-stat">
              <span className="peek-stat-label">Sector</span>
              <span className="peek-stat-val" style={{ fontSize: '0.82rem' }}>
                {details.sector || 'Equities'}
              </span>
            </div>

            <div className="peek-stat">
              <span className="peek-stat-label">Market Cap</span>
              <span className="peek-stat-val" style={{ fontSize: '0.82rem' }}>
                {formatMarketCap(details.marketCap)}
              </span>
            </div>
          </div>

          <div style={{
            background: 'var(--surface-secondary)',
            padding: '12px 16px',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-color)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: '0.75rem',
            color: 'var(--text-muted)'
          }}>
            <span>Exchange: <strong>{details.exchange || 'NSE India'}</strong></span>
            <span>As of: <strong>{formatTimestamp(quoteTimestamp)}</strong></span>
          </div>
        </div>

        <div className="modal-footer">
          <button
            onClick={() => setSelectedStockForPeek(null)}
            className="btn-secondary"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};
