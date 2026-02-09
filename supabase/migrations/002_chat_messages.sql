-- ORACLE-X CHAT MESSAGES TABLE
-- Bu SQL'i Supabase Dashboard > SQL Editor'da çalıştır

-- 1. TABLO OLUŞTUR
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    thinking_time FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. RLS AKTİFLEŞTİR
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;

-- 3. POLİCY'LER (Eğer zaten varsa hata verir, normal)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Users can view own chat messages' AND tablename = 'chat_messages') THEN
        CREATE POLICY "Users can view own chat messages" ON chat_messages FOR SELECT USING (auth.uid() = user_id);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Users can insert own chat messages' AND tablename = 'chat_messages') THEN
        CREATE POLICY "Users can insert own chat messages" ON chat_messages FOR INSERT WITH CHECK (auth.uid() = user_id);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Users can delete own chat messages' AND tablename = 'chat_messages') THEN
        CREATE POLICY "Users can delete own chat messages" ON chat_messages FOR DELETE USING (auth.uid() = user_id);
    END IF;
END $$;

-- 4. INDEX
CREATE INDEX IF NOT EXISTS idx_chat_messages_user_created ON chat_messages(user_id, created_at DESC);
