import React, { useState, useEffect } from 'react';
import { X, Mail, Lock, User, AlertCircle, CheckCircle2, Loader2, ArrowRight } from 'lucide-react';
import { useWatchlist } from '../context/WatchlistContext';

export const AuthModal = () => {
  const { 
    isAuthModalOpen, 
    setIsAuthModalOpen, 
    authMode, 
    setAuthMode, 
    login, 
    register 
  } = useWatchlist();

  const [mode, setMode] = useState(authMode || 'register');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  // Sync mode with context
  useEffect(() => {
    if (authMode) {
      setMode(authMode);
      setErrorMessage(null);
      setSuccessMessage(null);
    }
  }, [authMode, isAuthModalOpen]);

  if (!isAuthModalOpen) return null;

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

      setLoading(true);
      try {
        await register(name, email, password);
        setSuccessMessage('Account created successfully!');
        setTimeout(() => {
          setIsAuthModalOpen(false);
        }, 500);
      } catch (err) {
        setErrorMessage(err.message || 'Registration failed.');
      } finally {
        setLoading(false);
      }
    } else {
      // Login
      if (!email.trim()) {
        setErrorMessage('Please enter your email.');
        return;
      }
      if (!password) {
        setErrorMessage('Please enter your password.');
        return;
      }

      setLoading(true);
      try {
        await login(email, password);
        setSuccessMessage('Signed in successfully!');
        setTimeout(() => {
          setIsAuthModalOpen(false);
        }, 400);
      } catch (err) {
        setErrorMessage(err.message || 'Invalid email or password.');
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <div className="modal-backdrop" onClick={() => setIsAuthModalOpen(false)}>
      <div className="modal-card" style={{ maxWidth: '420px', padding: '24px' }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header" style={{ paddingBottom: '8px', borderBottom: 'none' }}>
          <div>
            <h3 className="modal-title" style={{ fontSize: '1.25rem', fontWeight: 800 }}>
              {mode === 'register' ? 'Create Your Account' : 'Sign In to GrowwPulse'}
            </h3>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              {mode === 'register' 
                ? 'Sign up for your personal change-first market watchlist' 
                : 'Enter your credentials to access your watchlist'}
            </span>
          </div>
          <button
            onClick={() => setIsAuthModalOpen(false)}
            className="icon-btn"
            aria-label="Close auth modal"
          >
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ marginTop: '12px' }}>
          <div className="modal-body" style={{ gap: '14px', padding: 0 }}>
            {errorMessage && (
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 14px',
                background: 'var(--sig-subtle)',
                border: '1px solid var(--sig-border)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--sig-color)',
                fontSize: '0.82rem'
              }}>
                <AlertCircle size={15} />
                <span>{errorMessage}</span>
              </div>
            )}

            {successMessage && (
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 14px',
                background: 'var(--quiet-subtle)',
                border: '1px solid var(--accent-border)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--accent-primary)',
                fontSize: '0.82rem'
              }}>
                <CheckCircle2 size={15} />
                <span>{successMessage}</span>
              </div>
            )}

            {mode === 'register' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                <label style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                  Full Name
                </label>
                <div className="search-input-wrap">
                  <User size={16} className="search-icon-pos" />
                  <input
                    type="text"
                    className="search-input"
                    placeholder="e.g. Rahul Sharma"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                  />
                </div>
              </div>
            )}

            <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
              <label style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                Email Address
              </label>
              <div className="search-input-wrap">
                <Mail size={16} className="search-icon-pos" />
                <input
                  type="email"
                  className="search-input"
                  placeholder="name@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
              <label style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                Password
              </label>
              <div className="search-input-wrap">
                <Lock size={16} className="search-icon-pos" />
                <input
                  type="password"
                  className="search-input"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
            </div>

            {mode === 'register' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                <label style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                  Confirm Password
                </label>
                <div className="search-input-wrap">
                  <Lock size={16} className="search-icon-pos" />
                  <input
                    type="password"
                    className="search-input"
                    placeholder="••••••••"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                  />
                </div>
              </div>
            )}

            <button
              type="submit"
              className="btn-primary"
              style={{
                width: '100%',
                padding: '11px 16px',
                marginTop: '8px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                borderRadius: 'var(--radius-md)',
                fontSize: '0.9rem',
                fontWeight: 700,
              }}
              disabled={loading}
            >
              {loading ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  <span>Processing...</span>
                </>
              ) : (
                <>
                  <span>{mode === 'register' ? 'Create Free Account' : 'Sign In'}</span>
                  <ArrowRight size={15} />
                </>
              )}
            </button>
          </div>

          <div className="modal-footer" style={{ justifyContent: 'center', marginTop: '16px', padding: '12px 0 0', borderTop: '1px solid var(--border-subtle)' }}>
            {mode === 'register' ? (
              <span style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                Already have an account?{' '}
                <button
                  type="button"
                  onClick={() => { setMode('login'); setAuthMode('login'); setErrorMessage(null); }}
                  style={{ color: 'var(--accent-primary)', fontWeight: 600, background: 'none', border: 'none', cursor: 'pointer' }}
                >
                  Sign In
                </button>
              </span>
            ) : (
              <span style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                Don't have an account?{' '}
                <button
                  type="button"
                  onClick={() => { setMode('register'); setAuthMode('register'); setErrorMessage(null); }}
                  style={{ color: 'var(--accent-primary)', fontWeight: 600, background: 'none', border: 'none', cursor: 'pointer' }}
                >
                  Create Account
                </button>
              </span>
            )}
          </div>
        </form>
      </div>
    </div>
  );
};
