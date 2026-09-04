import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || '';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || '';

// Safe diagnostic logging (host only, never expose keys)
const projectHost = supabaseUrl ? (() => {
  try {
    return new URL(supabaseUrl).host;
  } catch (_) {
    return 'invalid-url';
  }
})() : 'not-configured';

if (supabaseUrl && supabaseAnonKey) {
  console.log(`[GrowwPulse Supabase] Client initialized for host: ${projectHost}`);
} else {
  console.warn('[GrowwPulse Supabase] Missing VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY in frontend/.env');
}

export const isSupabaseConfigured = Boolean(supabaseUrl && supabaseAnonKey);

export const supabase = isSupabaseConfigured
  ? createClient(supabaseUrl, supabaseAnonKey, {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: true,
      },
    })
  : null;

