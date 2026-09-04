import React from 'react';
import { useWatchlist } from '../context/WatchlistContext';

export const MarketStatus = () => {
  const { pulse } = useWatchlist();

  if (!pulse) {
    return (
      <div className="market-status-pill">
        <span className="status-dot closed" />
        <span>NSE • Checking...</span>
      </div>
    );
  }

  const { marketStatus, marketStatusMessage } = pulse;
  const statusClass = marketStatus.toLowerCase();

  return (
    <div className="market-status-pill" title={marketStatusMessage}>
      <span className={`status-dot ${statusClass}`} />
      <span>NSE • {marketStatus === 'OPEN' ? 'Market Open' : marketStatus === 'PRE_MARKET' ? 'Pre-Market' : 'Market Closed'}</span>
    </div>
  );
};
