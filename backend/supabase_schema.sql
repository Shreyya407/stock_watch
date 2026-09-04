-- ==============================================================================
-- GrowwPulse Complete Supabase Schema Migration & Realtime Configuration
-- Run this in your Supabase Dashboard -> SQL Editor -> New Query -> Run
-- ==============================================================================

-- 1. Enable UUID Extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==============================================================================
-- 2. Companies Catalog (Master Stock Dictionary & Fundamental Metadata)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.companies (
    symbol TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    sector TEXT,
    industry TEXT,
    exchange TEXT DEFAULT 'NSE',
    market_cap NUMERIC,
    fifty_two_week_high NUMERIC,
    fifty_two_week_low NUMERIC,
    pe_ratio NUMERIC,
    last_price NUMERIC,
    last_volume BIGINT,
    avg_volume_20d NUMERIC,
    historical_volatility NUMERIC,
    created_at TIMESTAMPTZ DEFAULT now(),
    last_updated TIMESTAMPTZ DEFAULT now()
);

-- Index for searching companies by name or sector
CREATE INDEX IF NOT EXISTS idx_companies_name ON public.companies USING gin(to_tsvector('english', company_name));
CREATE INDEX IF NOT EXISTS idx_companies_sector ON public.companies(sector);

-- ==============================================================================
-- 3. User Profiles & Settings Table
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT,
    name TEXT,
    attention_threshold INT DEFAULT 40,
    default_sort TEXT DEFAULT 'attention_score',
    theme TEXT DEFAULT 'dark',
    auto_refresh_interval INT DEFAULT 15,
    notifications_enabled BOOLEAN DEFAULT true,
    last_active_at TIMESTAMPTZ DEFAULT now(),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Trigger to automatically update updated_at
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS on_profile_updated ON public.profiles;
CREATE TRIGGER on_profile_updated
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE PROCEDURE public.handle_updated_at();

-- Auto-create profile trigger whenever a user is created in auth.users
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, name, last_active_at)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'name', split_part(NEW.email, '@', 1)),
        now()
    )
    ON CONFLICT (id) DO UPDATE
    SET 
        email = EXCLUDED.email,
        name = COALESCE(EXCLUDED.name, public.profiles.name),
        last_active_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();

-- Backfill any existing auth.users into public.profiles
INSERT INTO public.profiles (id, email, name, last_active_at)
SELECT 
    id, 
    email, 
    COALESCE(raw_user_meta_data->>'name', split_part(email, '@', 1)),
    now()
FROM auth.users
ON CONFLICT (id) DO NOTHING;

-- ==============================================================================
-- 4. Watchlists Table (User-tracked equities with custom notes & tags)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.watchlists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    notes TEXT,
    target_price NUMERIC,
    tags TEXT[],
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Add optional columns if watchlists already exists
ALTER TABLE public.watchlists ADD COLUMN IF NOT EXISTS notes TEXT;
ALTER TABLE public.watchlists ADD COLUMN IF NOT EXISTS target_price NUMERIC;
ALTER TABLE public.watchlists ADD COLUMN IF NOT EXISTS tags TEXT[];

-- Ensure unique constraint exists for (user_id, symbol)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'unique_user_symbol'
    ) THEN
        ALTER TABLE public.watchlists ADD CONSTRAINT unique_user_symbol UNIQUE (user_id, symbol);
    END IF;
EXCEPTION
    WHEN duplicate_table THEN NULL;
    WHEN others THEN NULL;
END $$;

CREATE INDEX IF NOT EXISTS idx_watchlists_user_id ON public.watchlists(user_id);
CREATE INDEX IF NOT EXISTS idx_watchlists_symbol ON public.watchlists(symbol);

-- ==============================================================================
-- 5. Current Baseline Snapshots Table (Active baseline per user & stock)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    price NUMERIC NOT NULL,
    volume BIGINT NOT NULL,
    attention_score INT,
    attention_category TEXT,
    price_delta_pct NUMERIC,
    timestamp TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Add optional columns if snapshots already exists
ALTER TABLE public.snapshots ADD COLUMN IF NOT EXISTS attention_score INT;
ALTER TABLE public.snapshots ADD COLUMN IF NOT EXISTS attention_category TEXT;
ALTER TABLE public.snapshots ADD COLUMN IF NOT EXISTS price_delta_pct NUMERIC;

-- Ensure unique constraint exists for (user_id, symbol)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'unique_user_snapshot_symbol'
    ) THEN
        ALTER TABLE public.snapshots ADD CONSTRAINT unique_user_snapshot_symbol UNIQUE (user_id, symbol);
    END IF;
EXCEPTION
    WHEN duplicate_table THEN NULL;
    WHEN others THEN NULL;
END $$;

CREATE INDEX IF NOT EXISTS idx_snapshots_user_id ON public.snapshots(user_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_user_symbol ON public.snapshots(user_id, symbol);

-- ==============================================================================
-- 6. Snapshot History / Time Snapshots (Audit log & timeline of all snapshots)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.snapshot_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    price NUMERIC NOT NULL,
    volume BIGINT,
    attention_score INT,
    attention_category TEXT,
    price_delta_pct NUMERIC,
    trigger_event TEXT DEFAULT 'MANUAL', -- 'INITIAL_ADD', 'MARK_SEEN', 'PERIODIC', 'MANUAL'
    snapshot_timestamp TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_snapshot_history_user ON public.snapshot_history(user_id);
CREATE INDEX IF NOT EXISTS idx_snapshot_history_symbol ON public.snapshot_history(symbol);
CREATE INDEX IF NOT EXISTS idx_snapshot_history_timestamp ON public.snapshot_history(snapshot_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_snapshot_history_user_symbol ON public.snapshot_history(user_id, symbol, snapshot_timestamp DESC);

-- ==============================================================================
-- 7. Row Level Security (RLS) Policies
-- ==============================================================================

-- Enable RLS
ALTER TABLE public.companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.watchlists ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.snapshot_history ENABLE ROW LEVEL SECURITY;

-- Companies: Public Read Access, Service Role Write Access
DROP POLICY IF EXISTS "Allow public read on companies" ON public.companies;
CREATE POLICY "Allow public read on companies" ON public.companies FOR SELECT USING (true);

DROP POLICY IF EXISTS "Allow service role all on companies" ON public.companies;
CREATE POLICY "Allow service role all on companies" ON public.companies FOR ALL TO service_role USING (true);

-- Profiles: Users manage their own profile, Service Role has full access
DROP POLICY IF EXISTS "Users can view own profile" ON public.profiles;
CREATE POLICY "Users can view own profile" ON public.profiles FOR SELECT USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;
CREATE POLICY "Users can update own profile" ON public.profiles FOR UPDATE USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can insert own profile" ON public.profiles;
CREATE POLICY "Users can insert own profile" ON public.profiles FOR INSERT WITH CHECK (auth.uid() = id);

DROP POLICY IF EXISTS "Service role profile all" ON public.profiles;
CREATE POLICY "Service role profile all" ON public.profiles FOR ALL TO service_role USING (true);

-- Watchlists: Users manage their own watchlist
DROP POLICY IF EXISTS "Users can view own watchlists" ON public.watchlists;
CREATE POLICY "Users can view own watchlists" ON public.watchlists FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own watchlists" ON public.watchlists;
CREATE POLICY "Users can insert own watchlists" ON public.watchlists FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own watchlists" ON public.watchlists;
CREATE POLICY "Users can update own watchlists" ON public.watchlists FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own watchlists" ON public.watchlists;
CREATE POLICY "Users can delete own watchlists" ON public.watchlists FOR DELETE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Service role watchlists all" ON public.watchlists;
CREATE POLICY "Service role watchlists all" ON public.watchlists FOR ALL TO service_role USING (true);

-- Snapshots: Users access their own baseline snapshots
DROP POLICY IF EXISTS "Users can view own snapshots" ON public.snapshots;
CREATE POLICY "Users can view own snapshots" ON public.snapshots FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own snapshots" ON public.snapshots;
CREATE POLICY "Users can insert own snapshots" ON public.snapshots FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own snapshots" ON public.snapshots;
CREATE POLICY "Users can update own snapshots" ON public.snapshots FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own snapshots" ON public.snapshots;
CREATE POLICY "Users can delete own snapshots" ON public.snapshots FOR DELETE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Service role snapshots all" ON public.snapshots;
CREATE POLICY "Service role snapshots all" ON public.snapshots FOR ALL TO service_role USING (true);

-- Snapshot History: Users access their own snapshot timeline
DROP POLICY IF EXISTS "Users can view own snapshot history" ON public.snapshot_history;
CREATE POLICY "Users can view own snapshot history" ON public.snapshot_history FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own snapshot history" ON public.snapshot_history;
CREATE POLICY "Users can insert own snapshot history" ON public.snapshot_history FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Service role snapshot_history all" ON public.snapshot_history;
CREATE POLICY "Service role snapshot_history all" ON public.snapshot_history FOR ALL TO service_role USING (true);

-- ==============================================================================
-- 8. Enable Supabase Realtime Replication for Live Updates
-- ==============================================================================
DO $$
BEGIN
    -- Enable full replica identity so updates send complete row state
    ALTER TABLE public.watchlists REPLICA IDENTITY FULL;
    ALTER TABLE public.snapshots REPLICA IDENTITY FULL;
    ALTER TABLE public.snapshot_history REPLICA IDENTITY FULL;
    ALTER TABLE public.profiles REPLICA IDENTITY FULL;
    ALTER TABLE public.companies REPLICA IDENTITY FULL;

    -- Add tables to realtime publication if not already added
    BEGIN
        ALTER PUBLICATION supabase_realtime ADD TABLE public.watchlists;
    EXCEPTION WHEN duplicate_object THEN NULL;
    END;

    BEGIN
        ALTER PUBLICATION supabase_realtime ADD TABLE public.snapshots;
    EXCEPTION WHEN duplicate_object THEN NULL;
    END;

    BEGIN
        ALTER PUBLICATION supabase_realtime ADD TABLE public.snapshot_history;
    EXCEPTION WHEN duplicate_object THEN NULL;
    END;

    BEGIN
        ALTER PUBLICATION supabase_realtime ADD TABLE public.profiles;
    EXCEPTION WHEN duplicate_object THEN NULL;
    END;

    BEGIN
        ALTER PUBLICATION supabase_realtime ADD TABLE public.companies;
    EXCEPTION WHEN duplicate_object THEN NULL;
    END;
END $$;
