-- DİKKAT: Bu kod RLS (Row-Level Security) kısıtlamalarını esnetir.
-- Backend'in "Anonim Anahtar" ile çalışması durumunda hatayı çözer.

-- 1. Önce eski politikaları temizleyelim (varsa)
DROP POLICY IF EXISTS "Public Full Access Messages" ON chat_messages;
DROP POLICY IF EXISTS "Service Role Full Access Messages" ON chat_messages;
DROP POLICY IF EXISTS "Users can insert their own messages" ON chat_messages;

-- 2. Chat Mesajları için HERKESE tam izin ver
CREATE POLICY "Public Full Access Messages"
ON chat_messages
FOR ALL
USING (true)
WITH CHECK (true);

-- 3. Chat Oturumları için de temizleyip izin verelim
DROP POLICY IF EXISTS "Public Full Access Sessions" ON chat_sessions;
DROP POLICY IF EXISTS "Service Role Full Access Sessions" ON chat_sessions;
DROP POLICY IF EXISTS "Users can insert own sessions" ON chat_sessions;

CREATE POLICY "Public Full Access Sessions"
ON chat_sessions
FOR ALL
USING (true)
WITH CHECK (true);
