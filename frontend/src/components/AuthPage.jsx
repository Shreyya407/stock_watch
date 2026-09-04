import React, { useState } from 'react';
import { 
  Activity, 
  Mail, 
  Lock, 
  User, 
  ArrowRight, 
  CheckCircle2, 
  AlertCircle, 
  Loader2, 
  Sparkles, 
  TrendingUp, 
  ShieldCheck, 
  Zap 
} from 'lucide-react';
import { useWatchlist } from '../context/WatchlistContext';

export const AuthPage = ({ initialMode = 'login' }) => {
  const { login, register, demoLogin, setCurrentView } = useWatchlist();
  const [mode, setMode] = useState(initialMode); // 'login' | 'register'
  
  // Form states
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [agreeTerms, setAgreeTerms] = useState(true);
  
  // Status states
  const [loading, setLoading] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

    if (mode === 'register') {
      if (!name.trim()) {
        setErrorMessage('Please enter your full name.');
        return;
      }
      if (!email.trim() || !email.includes('@')) {
        setErrorMessage('Please enter a valid email address.');
        return;
      }
      if (password.length < 6) {
        setErrorMessage('Password must be at least 6 characters.');
        return;
      }
      if (password !== confirmPassword) {
        setErrorMessage('Passwords do not match.');
        return;
      }
      if (!agreeTerms) {
        setErrorMessage('Please accept the terms of service.');
        return;
      }

      setLoading(true);
      try {
        await register(name, email, password);
        setSuccessMessage('Account created successfully! Redirecting...');
      } catch (err) {
        setErrorMessage(err.message || 'Registration failed. Please try again.');
      } finally {
        setLoading(false);
      }
    } else {
      // Login mode
      if (!email.trim()) {
        setErrorMessage('Please enter your email address.');
        return;
      }
      if (!password) {
        setErrorMessage('Please enter your password.');
        return;
      }

      setLoading(true);
      try {
        await login(email, password);
        setSuccessMessage('Signed in successfully! Redirecting...');
      } catch (err) {
        setErrorMessage(err.message || 'Invalid email or password.');
      } finally {
        setLoading(false);
      }
    }
  };

  const handleQuickDemo = async () => {
    setErrorMessage(null);
    setDemoLoading(true);
    try {
      await demoLogin();
      setSuccessMessage('Signed in as Guest Investor! Loading your watchlist...');
    } catch (err) {
      setErrorMessage(err.message || 'Demo sign in failed.');
    } finally {
      setDemoLoading(false);
    }
  };

  return (
    <div className="auth-page-wrapper">
      <div className="auth-container-grid">
        {/* Left: Value Proposition & Visual Brand */}
        <div className="auth-hero-pane">
          <div className="auth-brand-badge">
            <Activity size={20} />
            <span>GrowwPulse Intelligence</span>
          </div>

          <h1 className="auth-hero-title">
            Smart change-first market monitoring for Indian equities.
          </h1>

          <p className="auth-hero-desc">
            Stay focused on what moved since you last looked. Cut through market noise with automated attention scoring and plain-English reasons.
          </p>

          <div className="auth-features-list">
            <div className="auth-feature-item">
              <div className="feature-bullet-icon">
                <Sparkles size={16} />
              </div>
              <div>
                <h4>Baseline Snapshot Tracking</h4>
                <p>Every delta is measured against your personal snapshot, not just daily open.</p>
              </div>
            </div>

            <div className="auth-feature-item">
              <div className="feature-bullet-icon">
                <TrendingUp size={16} />
              </div>
              <div>
                <h4>Smart Attention Ranking</h4>
                <p>Equities ranked dynamically by price volatility, volume anomalies, and gap momentum.</p>
              </div>
            </div>

            <div className="auth-feature-item">
              <div className="feature-bullet-icon">
                <Zap size={16} />
              </div>
              <div>
                <h4>Zero-Latency Live NSE Quotes</h4>
                <p>100+ top Indian companies with real-time updates and interactive explainability.</p>
              </div>
            </div>
          </div>

          <div className="auth-security-footnote">
            <ShieldCheck size={16} />
            <span>Bank-grade encryption • Isolated personal baselines • 100% Free</span>
          </div>
        </div>

        {/* Right: Interactive Form Card */}
        <div className="auth-form-card-pane">
          <div className="auth-form-card">
            {/* Mode Switcher Tabs */}
            <div className="auth-mode-tabs">
              <button
                type="button"
                className={`auth-tab-btn ${mode === 'login' ? 'active' : ''}`}
                onClick={() => { setMode('login'); setErrorMessage(null); setSuccessMessage(null); }}
              >
                Sign In
              </button>
              <button
                type="button"
                className={`auth-tab-btn ${mode === 'register' ? 'active' : ''}`}
                onClick={() => { setMode('register'); setErrorMessage(null); setSuccessMessage(null); }}
              >
                Create Account
              </button>
            </div>

            <div className="auth-form-header">
              <h2>{mode === 'login' ? 'Welcome back to GrowwPulse' : 'Start your smart watchlist'}</h2>
              <p>
                {mode === 'login' 
                  ? 'Enter your credentials to access your personal market snapshot' 
                  : 'Join Indian investors tracking real changes with intelligent attention scores'}
              </p>
            </div>

            {/* Error & Success Alerts */}
            {errorMessage && (
              <div className="auth-alert error">
                <AlertCircle size={16} />
                <span>{errorMessage}</span>
              </div>
            )}

            {successMessage && (
              <div className="auth-alert success">
                <CheckCircle2 size={16} />
                <span>{successMessage}</span>
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} className="auth-form-fields">
              {mode === 'register' && (
                <div className="form-group">
                  <label htmlFor="name-input">Full Name</label>
                  <div className="input-icon-wrap">
                    <User size={17} className="input-icon" />
                    <input
                      id="name-input"
                      type="text"
                      placeholder="e.g. Rahul Sharma"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      required
                    />
                  </div>
                </div>
              )}

              <div className="form-group">
                <label htmlFor="email-input">Email Address</label>
                <div className="input-icon-wrap">
                  <Mail size={17} className="input-icon" />
                  <input
                    id="email-input"
                    type="email"
                    placeholder="name@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="password-input">Password</label>
                <div className="input-icon-wrap">
                  <Lock size={17} className="input-icon" />
                  <input
                    id="password-input"
                    type="password"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                </div>
              </div>

              {mode === 'register' && (
                <div className="form-group">
                  <label htmlFor="confirm-password-input">Confirm Password</label>
                  <div className="input-icon-wrap">
                    <Lock size={17} className="input-icon" />
                    <input
                      id="confirm-password-input"
                      type="password"
                      placeholder="••••••••"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      required
                    />
                  </div>
                </div>
              )}

              {mode === 'register' && (
                <label className="checkbox-label" style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem', color: 'var(--text-secondary)', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={agreeTerms}
                    onChange={(e) => setAgreeTerms(e.target.checked)}
                  />
                  <span>I agree to the Terms of Service & Privacy Policy</span>
                </label>
              )}

              {/* Submit CTA */}
              <button
                type="submit"
                className="btn-primary auth-submit-btn"
                disabled={loading || demoLoading}
              >
                {loading ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    <span>Processing...</span>
                  </>
                ) : (
                  <>
                    <span>{mode === 'login' ? 'Sign In' : 'Create Free Account'}</span>
                    <ArrowRight size={16} />
                  </>
                )}
              </button>
            </form>

            <div className="auth-divider">
              <span>OR</span>
            </div>

            {/* Quick 1-Click Demo Login */}
            <button
              type="button"
              onClick={handleQuickDemo}
              className="btn-secondary auth-demo-btn"
              disabled={loading || demoLoading}
            >
              {demoLoading ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  <span>Loading Demo Account...</span>
                </>
              ) : (
                <>
                  <Sparkles size={16} style={{ color: 'var(--accent-primary)' }} />
                  <span>Explore with One-Click Demo Account</span>
                </>
              )}
            </button>

            {/* Footer switcher */}
            <div className="auth-card-footer">
              {mode === 'login' ? (
                <p>
                  Don't have an account?{' '}
                  <button
                    type="button"
                    onClick={() => { setMode('register'); setErrorMessage(null); }}
                    className="auth-inline-link"
                  >
                    Register now
                  </button>
                </p>
              ) : (
                <p>
                  Already have an account?{' '}
                  <button
                    type="button"
                    onClick={() => { setMode('login'); setErrorMessage(null); }}
                    className="auth-inline-link"
                  >
                    Sign In
                  </button>
                </p>
              )}

              <button
                type="button"
                onClick={() => setCurrentView('dashboard')}
                className="auth-guest-link"
              >
                ← Back to Market Dashboard
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
