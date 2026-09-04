import React from 'react';
import { Zap, TrendingUp, BarChart2, Flame } from 'lucide-react';
import { useWatchlist } from '../context/WatchlistContext';

export const MarketPulse = () => {
  const { pulse } = useWatchlist();

  if (!pulse) return null;

  const { topMover, largestVolumeAnomaly, highestAttention, marketStatusMessage } = pulse;

  return (
    <div className="market-pulse-card">
      <div className="pulse-header">
        <Zap size={16} color="var(--accent-primary)" />
        <span>Market Pulse</span>
      </div>

      <div className="pulse-items-grid">
        {topMover && (
          <div className="pulse-item">
            <span className="pulse-item-label">Top Move</span>
            <div className="pulse-item-value">
              <TrendingUp size={14} color={topMover.changePct >= 0 ? 'var(--positive-color)' : 'var(--negative-color)'} />
              <span>{topMover.symbol}</span>
              <span style={{ color: topMover.changePct >= 0 ? 'var(--positive-color)' : 'var(--negative-color)' }}>
                {topMover.changePct >= 0 ? `+${topMover.changePct}%` : `${topMover.changePct}%`}
              </span>
            </div>
          </div>
        )}

        {largestVolumeAnomaly && (
          <div className="pulse-item">
            <span className="pulse-item-label">Volume Anomaly</span>
            <div className="pulse-item-value">
              <BarChart2 size={14} color="var(--info-color)" />
              <span>{largestVolumeAnomaly.symbol}</span>
              <span style={{ color: 'var(--text-secondary)' }}>
                {largestVolumeAnomaly.multiplier}× normal
              </span>
            </div>
          </div>
        )}

        {highestAttention && (
          <div className="pulse-item">
            <span className="pulse-item-label">Highest Attention</span>
            <div className="pulse-item-value">
              <Flame size={14} color="var(--sig-color)" />
              <span>{highestAttention.symbol}</span>
              <span style={{
                color: highestAttention.score >= 70 ? 'var(--sig-color)' : highestAttention.score >= 40 ? 'var(--worth-color)' : 'var(--quiet-color)',
                fontWeight: 700
              }}>
                {highestAttention.score} / 100
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
