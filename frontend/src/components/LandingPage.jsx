import React from 'react';
import { 
  Activity, 
  ArrowRight, 
  TrendingUp, 
  Sparkles, 
  ShieldCheck, 
  Zap, 
  Eye, 
  Sliders, 
  BarChart3, 
  UserPlus, 
  LogIn,
  CheckCircle2,
  Clock,
  Layers
} from 'lucide-react';
import { useWatchlist } from '../context/WatchlistContext';

export const LandingPage = () => {
  const { openAuth } = useWatchlist();

  return (
    <div className="landing-page">
      {/* Hero Section */}
      <section className="landing-hero">
        <div className="landing-hero-content">
          <h1 className="landing-title">
            Stop checking 50 tickers.<br />
            <span className="gradient-text">See what changed since you last looked.</span>
          </h1>

          <p className="landing-subtitle">
            GrowwPulse maintains a personal market snapshot and lets you explicitly mark the current market state as seen. 
            Track real movements from your personal baseline, powered by live NSE data, algorithmic attention scoring, and explainable insights.
          </p>

          <div className="landing-cta-group">
            <button
              onClick={() => openAuth('register')}
              className="btn-primary landing-btn-primary"
            >
              <UserPlus size={18} />
              <span>Create Account — It's Free</span>
              <ArrowRight size={16} />
            </button>

            <button
              onClick={() => openAuth('login')}
              className="btn-secondary landing-btn-secondary"
            >
              <LogIn size={18} />
              <span>Sign In to Dashboard</span>
            </button>
          </div>

          <div className="landing-stats-row">
            <div className="landing-stat-item">
              <span className="stat-value">100+</span>
              <span className="stat-label">NSE Indian Equities</span>
            </div>
            <div className="stat-divider" />
            <div className="landing-stat-item">
              <span className="stat-value">3-Factor</span>
              <span className="stat-label">Attention Algorithm</span>
            </div>
            <div className="stat-divider" />
            <div className="landing-stat-item">
              <span className="stat-value">Live NSE</span>
              <span className="stat-label">Real-Time Quotes</span>
            </div>
            <div className="stat-divider" />
            <div className="landing-stat-item">
              <span className="stat-value">100%</span>
              <span className="stat-label">Private Baselines</span>
            </div>
          </div>
        </div>

        {/* Hero Interactive Preview Card */}
        <div className="landing-preview-container">
          <div className="landing-preview-card">
            <div className="preview-card-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div className="brand-icon" style={{ width: '28px', height: '28px' }}>
                  <Activity size={16} />
                </div>
                <div>
                  <h4 style={{ fontSize: '0.92rem', fontWeight: 700 }}>RELIANCE</h4>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>Reliance Industries Ltd • Energy</span>
                </div>
              </div>
              <div className="attention-badge significant">
                <span>Attention Score: 88</span>
              </div>
            </div>

            <div className="preview-card-body">
              <div className="preview-price-row">
                <div>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Current Price</span>
                  <div style={{ fontSize: '1.45rem', fontWeight: 800, fontFamily: 'var(--font-heading)' }}>₹1,412.50</div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Change Since Last Check</span>
                  <div style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--accent-primary)' }}>+1.62% (₹22.50)</div>
                </div>
              </div>

              <div className="preview-breakdown">
                <div className="breakdown-item">
                  <span className="breakdown-label">Volume Anomaly</span>
                  <span className="breakdown-value" style={{ color: 'var(--worth-color)' }}>2.4x 20D Avg</span>
                </div>
                <div className="breakdown-item">
                  <span className="breakdown-label">Opening Gap</span>
                  <span className="breakdown-value">+0.85% Gap Up</span>
                </div>
                <div className="breakdown-item">
                  <span className="breakdown-label">Volatility Movement</span>
                  <span className="breakdown-value">1.8σ Above Normal</span>
                </div>
              </div>

              <div className="preview-explanation">
                <Sparkles size={14} style={{ color: 'var(--accent-primary)', flexShrink: 0, marginTop: '2px' }} />
                <p>
                  <strong>Why it matters:</strong> Strong breakout on 2.4x abnormal institutional volume, crossing yesterday's high with expanding volatility.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Value Pillars Grid */}
      <section className="landing-pillars-section">
        <div className="section-header-center">
          <span className="section-eyebrow">WHAT MAKES GROWWPULSE DIFFERENT</span>
          <h2 className="section-heading">Engineered for Indian stock market investors</h2>
          <p className="section-desc">
            Traditional watchlists show green/red numbers from 9:15 AM market open. GrowwPulse shows you what actually happened between your visits.
          </p>
        </div>

        <div className="landing-grid-3">
          <div className="pillar-card">
            <div className="pillar-icon-wrap" style={{ color: 'var(--accent-primary)' }}>
              <Clock size={24} />
            </div>
            <h3>Change-First Snapshot Baseline</h3>
            <p>
              Every time you check your watchlist, GrowwPulse remembers the prices. When you return 2 hours or 2 days later, it highlights the exact difference since that visit.
            </p>
          </div>

          <div className="pillar-card">
            <div className="pillar-icon-wrap" style={{ color: 'var(--sig-color)' }}>
              <Zap size={24} />
            </div>
            <h3>Smart Attention Scoring</h3>
            <p>
              We calculate an algorithmic 0–100 Attention Score based on price movement (40%), volume anomalies (30%), and volatility (30%), putting the biggest movers on top.
            </p>
          </div>

          <div className="pillar-card">
            <div className="pillar-icon-wrap" style={{ color: 'var(--worth-color)' }}>
              <Sparkles size={24} />
            </div>
            <h3>Plain-English Explainability</h3>
            <p>
              No guesswork. Click any stock card to see a breakdown explaining why the stock moved and what the volume surge indicates in plain English.
            </p>
          </div>

          <div className="pillar-card">
            <div className="pillar-icon-wrap" style={{ color: 'var(--info-color)' }}>
              <Layers size={24} />
            </div>
            <h3>100+ Top Indian Companies</h3>
            <p>
              Explore and search top equities across Nifty 50, IT, Banking, FMCG, Auto, Energy, Metals, Defence, and Consumer Tech with instant one-click addition.
            </p>
          </div>

          <div className="pillar-card">
            <div className="pillar-icon-wrap" style={{ color: 'var(--accent-primary)' }}>
              <BarChart3 size={24} />
            </div>
            <h3>Market Pulse & Anomaly Detection</h3>
            <p>
              Live Indian market status (IST market open/close), top market movers, and highest volume surges condensed into a single glanceable summary.
            </p>
          </div>

          <div className="pillar-card">
            <div className="pillar-icon-wrap" style={{ color: '#A855F7' }}>
              <ShieldCheck size={24} />
            </div>
            <h3>Secure Supabase Authentication</h3>
            <p>
              Your watchlist and baseline snapshots are securely persisted and isolated to your personal account so you can track seamlessly across devices.
            </p>
          </div>
        </div>
      </section>

      {/* Call to Action Banner */}
      <section className="landing-cta-banner">
        <div className="cta-banner-card">
          <h2>Ready to track the market smarter?</h2>
          <p>Create your account in seconds to access your personal change-first watchlist.</p>
          <button
            onClick={() => openAuth('register')}
            className="btn-primary landing-btn-primary"
            style={{ margin: '0 auto' }}
          >
            <UserPlus size={18} />
            <span>Create Your Free Account</span>
            <ArrowRight size={16} />
          </button>
        </div>
      </section>
    </div>
  );
};
