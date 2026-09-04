import React, { useState } from 'react';
import { CheckCheck, RefreshCw, Clock, AlertCircle } from 'lucide-react';
import { useWatchlist } from '../context/WatchlistContext';

export const HeroSummary = () => {
  const { summary, markCurrentAsSeen, loadChanges, refreshing } = useWatchlist();
  const [markedFeedback, setMarkedFeedback] = useState(false);

  if (!summary) return null;

  const {
    totalCount,
    changedCount,
    significantCount,
    worthCheckingCount,
    quietCount,
    lastCheckedTimestamp,
    hasMeaningfulChanges,
    summaryText
  } = summary;

  const formatBaselineTime = (ts) => {
    if (!ts) return 'Just now';
    try {
      const date = new Date(ts);
      const now = new Date();
      const isToday = date.toDateString() === now.toDateString();
      const timeStr = date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
      if (isToday) {
        return `Today, ${timeStr}`;
      }
      return `${date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}, ${timeStr}`;
    } catch (_) {
      return 'Recently';
    }
  };

  const handleMarkSeenClick = async () => {
    const res = await markCurrentAsSeen();
    if (res.success) {
      setMarkedFeedback(true);
      setTimeout(() => setMarkedFeedback(false), 2500);
    }
  };

  return (
    <section className="hero-summary">
      <div className="hero-header">
        <div className="hero-titles">
          <span className="hero-label">Intelligent Market Delta</span>
          <h1 className="hero-heading">Since you last checked</h1>
          <p className="hero-subtext">{summaryText}</p>
        </div>

        <div className="hero-actions">
          <button
            onClick={() => loadChanges(true)}
            className="btn-secondary"
            title="Refresh Quotes"
            disabled={refreshing}
          >
            <RefreshCw size={15} className={refreshing ? 'animate-spin' : ''} />
            <span>{refreshing ? 'Updating...' : 'Refresh'}</span>
          </button>

          <button
            onClick={handleMarkSeenClick}
            className="btn-primary"
            title="Reset baseline to current market prices"
          >
            <CheckCheck size={16} />
            <span>{markedFeedback ? 'Baseline Updated!' : 'Mark Current as Seen'}</span>
          </button>
        </div>
      </div>

      <div className="metrics-strip">
        <div className="metric-badge">
          <span className="metric-badge-count">{changedCount}</span>
          <span className="metric-badge-label">Changed</span>
        </div>

        <div className="metric-badge sig">
          <span className="metric-badge-count">{significantCount}</span>
          <span className="metric-badge-label">Significant</span>
        </div>

        <div className="metric-badge worth">
          <span className="metric-badge-count">{worthCheckingCount}</span>
          <span className="metric-badge-label">Worth Checking</span>
        </div>

        <div className="metric-badge quiet">
          <span className="metric-badge-count">{quietCount}</span>
          <span className="metric-badge-label">Quiet</span>
        </div>
      </div>

      <div className="hero-footer-info">
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Clock size={14} />
          <span>Baseline captured: <strong>{formatBaselineTime(lastCheckedTimestamp)}</strong></span>
        </div>
        <span>Total Tracked: {totalCount} Equities</span>
      </div>
    </section>
  );
};
