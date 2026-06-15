-- ═══════════════════════════════════════════════════════════════════════════════
-- ORACLE-X PROFILE FEATURES MIGRATION
-- Adds subscription plans, connected accounts, and user settings
-- ═══════════════════════════════════════════════════════════════════════════════

-- 1. ADD SUBSCRIPTION PLAN TO PROFILES
ALTER TABLE profiles 
ADD COLUMN IF NOT EXISTS subscription_plan TEXT DEFAULT 'free' CHECK (subscription_plan IN ('free', 'pro', 'whale'));

ALTER TABLE profiles
ADD COLUMN IF NOT EXISTS subscription_expires_at TIMESTAMP WITH TIME ZONE;

ALTER TABLE profiles
ADD COLUMN IF NOT EXISTS ai_queries_today INTEGER DEFAULT 0;

ALTER TABLE profiles
ADD COLUMN IF NOT EXISTS ai_queries_reset_at DATE DEFAULT CURRENT_DATE;

-- 2. CONNECTED ACCOUNTS TABLE
CREATE TABLE IF NOT EXISTS connected_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    provider TEXT NOT NULL CHECK (provider IN ('twitter', 'discord', 'telegram')),
    provider_user_id TEXT,
    provider_username TEXT,
    access_token TEXT,
    refresh_token TEXT,
    connected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, provider)
);

-- 3. USER SETTINGS TABLE
CREATE TABLE IF NOT EXISTS user_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL UNIQUE,
    theme TEXT DEFAULT 'dark' CHECK (theme IN ('dark', 'light', 'system')),
    notifications_enabled BOOLEAN DEFAULT TRUE,
    email_alerts BOOLEAN DEFAULT FALSE,
    telegram_alerts BOOLEAN DEFAULT FALSE,
    default_market TEXT DEFAULT 'crypto' CHECK (default_market IN ('crypto', 'nasdaq')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════════════════════════════
-- ROW LEVEL SECURITY
-- ═══════════════════════════════════════════════════════════════════════════════

-- Connected Accounts RLS
ALTER TABLE connected_accounts ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
    CREATE POLICY "Users can view own connected accounts" 
        ON connected_accounts FOR SELECT USING (auth.uid() = user_id);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE POLICY "Users can insert own connected accounts" 
        ON connected_accounts FOR INSERT WITH CHECK (auth.uid() = user_id);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE POLICY "Users can update own connected accounts" 
        ON connected_accounts FOR UPDATE USING (auth.uid() = user_id);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE POLICY "Users can delete own connected accounts" 
        ON connected_accounts FOR DELETE USING (auth.uid() = user_id);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- User Settings RLS
ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
    CREATE POLICY "Users can view own settings" 
        ON user_settings FOR SELECT USING (auth.uid() = user_id);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE POLICY "Users can insert own settings" 
        ON user_settings FOR INSERT WITH CHECK (auth.uid() = user_id);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE POLICY "Users can update own settings" 
        ON user_settings FOR UPDATE USING (auth.uid() = user_id);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- ═══════════════════════════════════════════════════════════════════════════════
-- INDEXES
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE INDEX IF NOT EXISTS idx_connected_accounts_user_id ON connected_accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings(user_id);

-- ═══════════════════════════════════════════════════════════════════════════════
-- HELPER FUNCTIONS
-- ═══════════════════════════════════════════════════════════════════════════════

-- Function to reset daily AI query count
CREATE OR REPLACE FUNCTION reset_daily_ai_queries()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.ai_queries_reset_at < CURRENT_DATE THEN
        NEW.ai_queries_today := 0;
        NEW.ai_queries_reset_at := CURRENT_DATE;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-reset AI queries on profile access
DROP TRIGGER IF EXISTS reset_ai_queries_on_update ON profiles;
CREATE TRIGGER reset_ai_queries_on_update
    BEFORE UPDATE ON profiles
    FOR EACH ROW
    EXECUTE FUNCTION reset_daily_ai_queries();

-- Function to get AI query limit based on plan
CREATE OR REPLACE FUNCTION get_ai_query_limit(plan TEXT)
RETURNS INTEGER AS $$
BEGIN
    CASE plan
        WHEN 'free' THEN RETURN 5;
        WHEN 'pro' THEN RETURN 999999;  -- Unlimited
        WHEN 'whale' THEN RETURN 999999;  -- Unlimited
        ELSE RETURN 5;
    END CASE;
END;
$$ LANGUAGE plpgsql;
