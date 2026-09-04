import React from 'react';
import { X, ArrowRight, ShieldCheck, Zap, Activity } from 'lucide-react';
import { useWatchlist } from '../context/WatchlistContext';

export const ExplainabilityModal = () => {
  const { selectedStockForExplain, setSelectedStockForExplain } = useWatchlist();

  if (!selectedStockForExplain) return null;

  const {
    symbol,
    companyName,
    currentPrice,
    snapshotPrice,
    priceDeltaPct,
    absoluteChange,
    volumeMultiplier,
    volatilityAdjustedMovement,
    openingGapPct,
    attentionScore,
    attentionCategory,
    whyBreakdown,
    snapshotTimestamp
  } = selectedStockForExplain;

  const categoryColor = attentionCategory === 'SIGNIFICANT' ? 'var(--sig-color)' : attentionCategory === 'WORTH CHECKING' ? 'var(--worth-color)' : 'var(--quiet-color)';

  const formatSnapshotDate = (ts) => {
    if (!ts) return 'Baseline Visit';
    try {
      const d = new Date(ts);
      return d.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit', hour12: true });
    } catch (_) {
      return 'Baseline Visit';
    }
  };

  return (
    <div className="modal-backdrop" onClick={() => setSelectedStockForExplain(null)}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <span style={{ fontSize: '0.74rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600 }}>
              Explainability Engine
            </span>
            <h3 className="modal-title">Why am I seeing this?</h3>
          </div>
          <button
            onClick={() => setSelectedStockForExplain(null)}
            className="icon-btn"
            aria-label="Close modal"
          >
            <X size={18} />
          </button>
        </div>

        <div className="modal-body">
          {/* Header Score Card */}
          <div className="score-hero-box">
            <div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
                {symbol} • {companyName}
              </div>
              <div style={{ fontSize: '0.85rem', color: categoryColor, fontWeight: 700, marginTop: '2px' }}>
                {attentionCategory} ATTENTION
              </div>
            </div>

            <div style={{ textAlign: 'right' }}>
              <div className="score-hero-val" style={{ color: categoryColor }}>
                {attentionScore}
              </div>
              <div style={{ fontSize: '0.68rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>
                out of 100
              </div>
            </div>
          </div>

          {/* Primary Signal & Plain English Explanation */}
          <div className="signal-banner">
            <span className="signal-tag">Primary Signal: {whyBreakdown.primarySignal}</span>
            <p className="signal-desc">{whyBreakdown.plainEnglishExplanation}</p>
          </div>

          {/* 3-Factor Score Breakdown */}
          <div className="score-progress-group">
            <span style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.05em' }}>
              Score Weight Breakdown
            </span>

            {/* Price Movement (40%) */}
            <div className="progress-row">
              <div className="progress-label-row">
                <span>Price Movement (40% weight)</span>
                <span>{whyBreakdown.priceContribution} / 40 pts</span>
              </div>
              <div className="progress-bar-bg">
                <div
                  className="progress-bar-fill"
                  style={{
                    width: `${(whyBreakdown.priceContribution / 40) * 100}%`,
                    backgroundColor: 'var(--accent-primary)'
                  }}
                />
              </div>
              <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                Actual: <strong>{priceDeltaPct >= 0 ? `+${priceDeltaPct.toFixed(2)}%` : `${priceDeltaPct.toFixed(2)}%`}</strong> ({priceDeltaPct >= 0 ? `+₹${absoluteChange.toFixed(2)}` : `-₹${Math.abs(absoluteChange).toFixed(2)}`}) since baseline
              </div>
            </div>

            {/* Volume Anomaly (30%) */}
            <div className="progress-row">
              <div className="progress-label-row">
                <span>Volume Anomaly (30% weight)</span>
                <span>{whyBreakdown.volumeContribution} / 30 pts</span>
              </div>
              <div className="progress-bar-bg">
                <div
                  className="progress-bar-fill"
                  style={{
                    width: `${(whyBreakdown.volumeContribution / 30) * 100}%`,
                    backgroundColor: 'var(--info-color)'
                  }}
                />
              </div>
              <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                Actual: <strong>{volumeMultiplier}×</strong> 20-day average volume
              </div>
            </div>

            {/* Volatility Adjusted (30%) */}
            <div className="progress-row">
              <div className="progress-label-row">
                <span>Volatility Context (30% weight)</span>
                <span>{whyBreakdown.volatilityContribution} / 30 pts</span>
              </div>
              <div className="progress-bar-bg">
                <div
                  className="progress-bar-fill"
                  style={{
                    width: `${(whyBreakdown.volatilityContribution / 30) * 100}%`,
                    backgroundColor: 'var(--worth-color)'
                  }}
                />
              </div>
              <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                Actual: <strong>{volatilityAdjustedMovement}×</strong> typical daily movement standard
              </div>
            </div>
          </div>

          {/* Baseline Timeline */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.05em' }}>
              Since Last Checked Timeline
            </span>

            <div className="timeline-card">
              <div className="timeline-step">
                <span className="timeline-step-label">Baseline Snapshot</span>
                <span className="timeline-step-val">₹{snapshotPrice.toFixed(2)}</span>
                <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>{formatSnapshotDate(snapshotTimestamp)}</span>
              </div>

              <ArrowRight size={16} color="var(--text-muted)" />

              <div className="timeline-step" style={{ alignItems: 'flex-end' }}>
                <span className="timeline-step-label">Current Market</span>
                <span className="timeline-step-val" style={{ color: priceDeltaPct >= 0 ? 'var(--positive-color)' : 'var(--negative-color)' }}>
                  ₹{currentPrice.toFixed(2)}
                </span>
                <span style={{ fontSize: '0.68rem', color: priceDeltaPct >= 0 ? 'var(--positive-color)' : 'var(--negative-color)' }}>
                  {priceDeltaPct >= 0 ? `+${priceDeltaPct.toFixed(2)}%` : `${priceDeltaPct.toFixed(2)}%`}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="modal-footer">
          <button
            onClick={() => setSelectedStockForExplain(null)}
            className="btn-secondary"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
