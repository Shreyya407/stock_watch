import React from 'react';
import { HelpCircle, Eye, Trash2, ArrowUpRight, ArrowDownRight, Radio } from 'lucide-react';
import { useWatchlist } from '../context/WatchlistContext';

export const StockCard = ({ stock }) => {
  const { setSelectedStockForExplain, setSelectedStockForPeek, removeStock } = useWatchlist();

  const {
    symbol,
    companyName,
    currentPrice,
    snapshotPrice,
    priceDeltaPct,
    absoluteChange,
    volumeMultiplier,
    volatilityAdjustedMovement,
    dayChangePct,
    attentionScore,
    attentionCategory,
    source,
    isStale,
    lastUpdatedSecondsAgo,
    sparkline
  } = stock;

  const isPositive = priceDeltaPct >= 0;
  const categoryClass = attentionCategory === 'SIGNIFICANT' ? 'sig' : attentionCategory === 'WORTH CHECKING' ? 'worth' : 'quiet';

  // Render SVG Sparkline
  const renderSparkline = () => {
    if (!sparkline || sparkline.length < 3) return null;

    const min = Math.min(...sparkline);
    const max = Math.max(...sparkline);
    const range = max - min || 1;
    const width = 280;
    const height = 36;
    const padding = 2;

    const points = sparkline.map((val, idx) => {
      const x = padding + (idx / (sparkline.length - 1)) * (width - 2 * padding);
      const y = height - padding - ((val - min) / range) * (height - 2 * padding);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    }).join(' ');

    const strokeColor = sparkline[sparkline.length - 1] >= sparkline[0] ? 'var(--positive-color)' : 'var(--negative-color)';

    return (
      <div className="sparkline-wrapper" title="Recent Intraday/Daily Trajectory">
        <svg viewBox={`0 0 ${width} ${height}`} className="sparkline-svg" preserveAspectRatio="none">
          <polyline
            fill="none"
            stroke={strokeColor}
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
            points={points}
          />
        </svg>
      </div>
    );
  };

  const formatSource = () => {
    if (isStale) {
      const mins = Math.max(1, Math.round(lastUpdatedSecondsAgo / 60));
      return `STALE • ${mins}m ago`;
    }
    return source;
  };

  return (
    <div className={`stock-card ${categoryClass}`}>
      {/* Top Header */}
      <div className="card-top">
        <div className="card-company-info">
          <span className="ticker-symbol">{symbol}</span>
          <span className="company-name" title={companyName}>{companyName}</span>
        </div>

        <div className={`attention-badge ${categoryClass}`}>
          <span>{attentionScore}</span>
          <span>•</span>
          <span>{attentionCategory}</span>
        </div>
      </div>

      {/* Price & Baseline Delta */}
      <div className="card-price-row">
        <div className="price-current">
          ₹{currentPrice.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </div>

        <div className="price-delta-box">
          <div className={`delta-pct ${isPositive ? 'pos' : 'neg'}`}>
            {isPositive ? <ArrowUpRight size={15} /> : <ArrowDownRight size={15} />}
            <span>{isPositive ? `+${priceDeltaPct.toFixed(2)}%` : `${priceDeltaPct.toFixed(2)}%`}</span>
          </div>
          <span className="delta-rupee">
            {isPositive ? `+₹${absoluteChange.toFixed(2)}` : `-₹${Math.abs(absoluteChange).toFixed(2)}`} since last check
          </span>
        </div>
      </div>

      {/* Sparkline */}
      {renderSparkline()}

      {/* Analytics Breakdown Grid */}
      <div className="card-metrics-grid">
        <div className="sub-metric">
          <span className="sub-metric-label">Volume</span>
          <span className="sub-metric-value">{volumeMultiplier?.toFixed ? `${volumeMultiplier.toFixed(2)}×` : `${volumeMultiplier}×`} avg</span>
        </div>
        <div className="sub-metric">
          <span className="sub-metric-label">Volatility</span>
          <span className="sub-metric-value">
            {volatilityAdjustedMovement > 0 ? `${volatilityAdjustedMovement.toFixed(1)}× typical` : 'Normal'}
          </span>
        </div>
        <div className="sub-metric">
          <span className="sub-metric-label">Day Move</span>
          <span className="sub-metric-value" style={{ color: dayChangePct >= 0 ? 'var(--positive-color)' : 'var(--negative-color)' }}>
            {dayChangePct >= 0 ? `+${dayChangePct.toFixed(2)}%` : `${dayChangePct.toFixed(2)}%`}
          </span>
        </div>
      </div>

      {/* Card Footer Actions */}
      <div className="card-footer">
        <button
          onClick={() => setSelectedStockForExplain(stock)}
          className="btn-explain-chip"
          title="Explain why this score was calculated"
        >
          <HelpCircle size={13} />
          <span>Why this score?</span>
        </button>

        <div className="card-action-links">
          <button
            onClick={() => setSelectedStockForPeek(stock)}
            className="btn-peek-chip"
            title="Quick fundamental research peek"
          >
            <Eye size={13} />
            <span>Company Peek</span>
          </button>

          <button
            onClick={() => removeStock(symbol)}
            className="btn-delete-chip"
            title={`Remove ${symbol} from watchlist`}
            aria-label={`Remove ${symbol}`}
          >
            <Trash2 size={13} />
          </button>
        </div>
      </div>
    </div>
  );
};
