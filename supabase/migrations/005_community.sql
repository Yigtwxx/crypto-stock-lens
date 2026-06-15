-- Enable pgcrypto for gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- DROP tables if they exist to ensure schema update (WARNING: Deletes data)
DROP TABLE IF EXISTS community_likes;
DROP TABLE IF EXISTS community_comments;
DROP TABLE IF EXISTS community_posts;

-- Community Posts
CREATE TABLE IF NOT EXISTS community_posts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE, 
  content TEXT NOT NULL,
  title TEXT, -- Optional, for Analysis/Thought titles
  type TEXT NOT NULL CHECK (type IN ('question', 'thought', 'analysis')),
  asset_symbol TEXT, -- Optional (e.g., BTC, AAPL)
  image_url TEXT, -- Optional image attachment
  likes_count INTEGER DEFAULT 0,
  comments_count INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Community Comments
CREATE TABLE IF NOT EXISTS community_comments (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  post_id UUID REFERENCES community_posts(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Community Likes (Composite key to prevent duplicate likes)
CREATE TABLE IF NOT EXISTS community_likes (
  post_id UUID REFERENCES community_posts(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (post_id, user_id)
);

-- RLS Policies (Enable if using anon key, but backend uses service_role mostly)
ALTER TABLE community_posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE community_comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE community_likes ENABLE ROW LEVEL SECURITY;

-- Public read access
create policy "Public posts are viewable by everyone"
  on community_posts for select
  using ( true );

create policy "Public comments are viewable by everyone"
  on community_comments for select
  using ( true );

create policy "Public likes are viewable by everyone"
  on community_likes for select
  using ( true );

-- Authenticated create access
create policy "Users can insert their own posts"
  on community_posts for insert
  with check ( auth.uid() = user_id );

create policy "Users can update own posts"
  on community_posts for update
  using ( auth.uid() = user_id );

create policy "Users can delete own posts"
  on community_posts for delete
  using ( auth.uid() = user_id );

create policy "Users can insert their own comments"
  on community_comments for insert
  with check ( auth.uid() = user_id );

create policy "Users can delete own comments"
  on community_comments for delete
  using ( auth.uid() = user_id );

create policy "Users can insert their own likes"
  on community_likes for insert
  with check ( auth.uid() = user_id );

create policy "Users can delete own likes"
  on community_likes for delete
  using ( auth.uid() = user_id );
