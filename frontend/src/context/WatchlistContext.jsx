import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';
import { api } from '../services/api';
import { supabase, isSupabaseConfigured } from '../supabase';

const WatchlistContext = createContext();

const STORAGE_KEY_TOKEN = 'growwpulse_auth_token';
const STORAGE_KEY_USER = 'growwpulse_auth_user';

export const WatchlistProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY_USER);
      return saved ? JSON.parse(saved) : null;
    } catch (_) {
      return null;
    }
  });

  const [summary, setSummary] = useState(null);
  const [pulse, setPulse] = useState(null);
  const [stocks, setStocks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [sortBy, setSortBy] = useState('attention'); // 'attention' | 'change' | 'volume' | 'alphabetical'

  // Modals & Navigation state
  const [selectedStockForExplain, setSelectedStockForExplain] = useState(null);
  const [selectedStockForPeek, setSelectedStockForPeek] = useState(null);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState('register'); // 'login' | 'register'

  // Helper to open auth in specific mode
  const openAuth = useCallback((mode = 'register') => {
    setAuthMode(mode);
    setIsAuthModalOpen(true);
  }, []);

  // Initialize stored token on startup
  useEffect(() => {
    const token = localStorage.getItem(STORAGE_KEY_TOKEN);
    if (token) {
      api.setToken(token);
    }
  }, []);

  // Initialize Supabase Auth Listener if configured
  useEffect(() => {
    if (isSupabaseConfigured && supabase) {
      supabase.auth.getSession().then(({ data: { session } }) => {
        if (session && session.user) {
          const u = {
            id: session.user.id,
            email: session.user.email,
            name: session.user.user_metadata?.name || session.user.email?.split('@')[0],
          };
          setUser(u);
          api.setToken(session.access_token);
          localStorage.setItem(STORAGE_KEY_TOKEN, session.access_token);
          localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(u));
        }
      });

      const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
        if (session && session.user) {
          const u = {
            id: session.user.id,
            email: session.user.email,
            name: session.user.user_metadata?.name || session.user.email?.split('@')[0],
          };
          setUser(u);
          api.setToken(session.access_token);
          localStorage.setItem(STORAGE_KEY_TOKEN, session.access_token);
          localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(u));
        } else {
          setUser(null);
          api.setToken(null);
          localStorage.removeItem(STORAGE_KEY_TOKEN);
          localStorage.removeItem(STORAGE_KEY_USER);
        }
      });

      return () => subscription.unsubscribe();
    }
  }, []);

  // Centralized Watchlist Fetcher (Only runs when user is logged in)
  const loadChanges = useCallback(async (isBackground = false) => {
    if (!user) {
      setStocks([]);
      setSummary(null);
      setPulse(null);
      setLoading(false);
      return;
    }

    if (!isBackground) {
      setLoading(true);
    } else {
      setRefreshing(true);
    }
    setError(null);

    try {
      const data = await api.getWatchlistChanges();
      setSummary(data.summary);
      setPulse(data.pulse);
      setStocks(data.stocks || []);
    } catch (err) {
      console.error('Failed to load watchlist changes:', err);
      setError(err.message || 'Market data is temporarily unavailable.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [user]);

  // Fetch watchlist data whenever user state becomes active
  useEffect(() => {
    if (user) {
      loadChanges();
    }
  }, [user, loadChanges]);

  // Supabase Realtime Listener: Subscribes to changes in watchlists, snapshots, snapshot_history
  useEffect(() => {
    if (!isSupabaseConfigured || !supabase || !user?.id) return;

    console.log('[GrowwPulse Realtime] Subscribing to real-time events for user:', user.id);

    const realtimeChannel = supabase
      .channel(`realtime-user-${user.id}`)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'watchlists',
          filter: `user_id=eq.${user.id}`,
        },
        (payload) => {
          console.log('[Realtime] Watchlist modified:', payload.eventType);
          loadChanges(true);
        }
      )
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'snapshots',
          filter: `user_id=eq.${user.id}`,
        },
        (payload) => {
          console.log('[Realtime] Snapshot updated:', payload.eventType);
          loadChanges(true);
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(realtimeChannel);
    };
  }, [user?.id, loadChanges]);

  // Periodic 15-second live quote refresh
  useEffect(() => {
    if (!user) return;
    const interval = setInterval(() => {
      loadChanges(true);
    }, 15000);
    return () => clearInterval(interval);
  }, [user, loadChanges]);

  // Login handler - strictly through Supabase Auth
  const handleLogin = async (email, password) => {
    if (!supabase) {
      throw new Error('Supabase client is not initialized. Please verify frontend/.env configuration.');
    }

    const { data, error } = await supabase.auth.signInWithPassword({ email, password });

    if (error) {
      console.error('[Supabase Auth] Login failed:', error.message);
      throw error;
    }

    if (!data?.user || !data?.session) {
      throw new Error('Sign in succeeded but no active session was returned by Supabase.');
    }

    console.log('[Supabase Auth] Successfully signed in user ID:', data.user.id);
    const u = {
      id: data.user.id,
      email: data.user.email,
      name: data.user.user_metadata?.name || data.user.email?.split('@')[0],
    };
    setUser(u);
    api.setToken(data.session.access_token);
    localStorage.setItem(STORAGE_KEY_TOKEN, data.session.access_token);
    localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(u));
    setIsAuthModalOpen(false);
    setTimeout(() => {
      loadChanges();
    }, 50);
    return data;
  };

  // Register handler - strictly through Supabase Auth
  const handleRegister = async (name, email, password) => {
    if (!supabase) {
      throw new Error('Supabase client is not initialized. Please verify frontend/.env configuration.');
    }

    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          name: name || email.split('@')[0]
        }
      }
    });

    if (error) {
      console.error('[Supabase Auth] Sign up failed:', error.message);
      throw error;
    }

    if (!data?.user) {
      throw new Error('Registration failed: User could not be created in Supabase.');
    }

    console.log('[Supabase Auth] Successfully registered user ID in Supabase:', data.user.id);

    const u = {
      id: data.user.id,
      email: data.user.email,
      name: name || data.user.user_metadata?.name || data.user.email?.split('@')[0],
    };

    if (data.session) {
      setUser(u);
      api.setToken(data.session.access_token);
      localStorage.setItem(STORAGE_KEY_TOKEN, data.session.access_token);
      localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(u));
      setIsAuthModalOpen(false);
      return data;
    } else {
      // Immediate sign-in if email confirmation is turned off in Supabase
      const loginRes = await supabase.auth.signInWithPassword({ email, password });
      if (loginRes.data && loginRes.data.session) {
        setUser(u);
        api.setToken(loginRes.data.session.access_token);
        localStorage.setItem(STORAGE_KEY_TOKEN, loginRes.data.session.access_token);
        localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(u));
        setIsAuthModalOpen(false);
        return loginRes.data;
      }
      return { ...data, requiresEmailConfirmation: true };
    }
  };

  // Logout handler
  const handleLogout = async () => {
    if (supabase) {
      try {
        await supabase.auth.signOut();
      } catch (err) {
        console.warn('[Supabase Auth] Sign out notice:', err.message);
      }
    }
    setUser(null);
    api.setToken(null);
    setStocks([]);
    setSummary(null);
    setPulse(null);
    localStorage.removeItem(STORAGE_KEY_TOKEN);
    localStorage.removeItem(STORAGE_KEY_USER);
  };

  // Add Stock Handler
  const handleAddStock = async (symbol) => {
    try {
      await api.addStock(symbol);
      await loadChanges();
      return { success: true };
    } catch (err) {
      return { success: false, error: err.message || 'Failed to add stock.' };
    }
  };

  // Remove Stock Handler
  const handleRemoveStock = async (symbol) => {
    try {
      await api.removeStock(symbol);
      setStocks(prev => prev.filter(s => s.symbol !== symbol));
      await loadChanges(true);
      return { success: true };
    } catch (err) {
      return { success: false, error: err.message || 'Failed to remove stock.' };
    }
  };

  // Mark Current As Seen Handler (Snapshot update)
  const handleMarkCurrentAsSeen = async () => {
    setRefreshing(true);
    try {
      const data = await api.markCurrentAsSeen();
      setSummary(data.summary);
      setPulse(data.pulse);
      setStocks(data.stocks || []);
      return { success: true };
    } catch (err) {
      setError(err.message || 'Failed to update snapshot baseline.');
      return { success: false, error: err.message };
    } finally {
      setRefreshing(false);
    }
  };

  // Sorted Stocks List
  const sortedStocks = useMemo(() => {
    const list = [...stocks];
    if (sortBy === 'attention') {
      return list.sort((a, b) => b.attentionScore - a.attentionScore);
    }
    if (sortBy === 'change') {
      return list.sort((a, b) => Math.abs(b.priceDeltaPct) - Math.abs(a.priceDeltaPct));
    }
    if (sortBy === 'volume') {
      return list.sort((a, b) => b.volumeMultiplier - a.volumeMultiplier);
    }
    if (sortBy === 'alphabetical') {
      return list.sort((a, b) => a.symbol.localeCompare(b.symbol));
    }
    return list;
  }, [stocks, sortBy]);

  return (
    <WatchlistContext.Provider
      value={{
        user,
        summary,
        pulse,
        stocks: sortedStocks,
        rawStocksCount: stocks.length,
        loading,
        refreshing,
        error,
        sortBy,
        setSortBy,
        loadChanges,
        login: handleLogin,
        register: handleRegister,
        logout: handleLogout,
        authMode,
        setAuthMode,
        openAuth,
        addStock: handleAddStock,
        removeStock: handleRemoveStock,
        markCurrentAsSeen: handleMarkCurrentAsSeen,
        selectedStockForExplain,
        setSelectedStockForExplain,
        selectedStockForPeek,
        setSelectedStockForPeek,
        isAddModalOpen,
        setIsAddModalOpen,
        isAuthModalOpen,
        setIsAuthModalOpen,
      }}
    >
      {children}
    </WatchlistContext.Provider>
  );
};

export const useWatchlist = () => useContext(WatchlistContext);
