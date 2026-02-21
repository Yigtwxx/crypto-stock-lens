-- Allow Service Role to Bypass RLS (Implicit, but this makes sure policies are not blocking)
-- Actually, Service Role bypasses everything by default.
-- If the backend is using ANON KEY, we need a policy for anon.
-- BUT backend SHOULD use SERVICE ROLE KEY.

-- OPTION 1: Verify RLS is enabled
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;

-- OPTION 2: Create Policy for Service Role (if not bypassing)
-- This is usually not needed as service_role bypasses RLS.

-- OPTION 3: Allow authenticated users to insert their *own* rows
-- This requires the client to be authenticated (have a JWT).
-- Our backend is NOT sending a user JWT, it sends raw requests.
-- So it acts as ANON or SERVICE_ROLE.

-- IF the backend is using ANON KEY (because Service Role Key is missing/wrong):
-- We must allow anon to insert rows where user_id matches?
-- No, anon doesn't have a user_id in auth.uid().
-- So we must trust the `user_id` column in the payload.

-- DANGEROUS FIX (For Dev Only): Allow Anon to Insert
-- Only run this if secure service role isn't working.
CREATE POLICY "Allow Service Role" ON chat_messages
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

CREATE POLICY "Allow Service Role" ON chat_sessions
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Also Ensure Public can read if needed (for client-side)
CREATE POLICY "Users can see their own messages" ON chat_messages
FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own messages" ON chat_messages
FOR INSERT
WITH CHECK (auth.uid() = user_id);
