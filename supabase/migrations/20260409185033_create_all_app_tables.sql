/*
  # Create all application tables

  This migration creates the full schema for the art platform app,
  moving from SQLite (ephemeral disk) to persistent Supabase PostgreSQL.

  ## Tables Created
  - `users` - User accounts with profile info and password hashes
  - `artworks` - Artwork posts with image URLs (Cloudinary), title, category
  - `followers` - Follow relationships between users
  - `likes` - Artwork likes by users
  - `comments` - Artwork comments
  - `channels` - Public chat channels
  - `messages` - Channel messages (text + optional image)
  - `collections` - User-curated artwork collections
  - `collection_artworks` - Junction table linking artworks to collections
  - `notifications` - Activity notifications (follow, like, comment, message)
  - `direct_messages` - Private messages between users

  ## Security
  - RLS is enabled on all tables
  - App uses its own auth (Flask/werkzeug password hashing), NOT Supabase auth
  - Service role key is used server-side so policies allow service_role full access
  - anon role is blocked from all tables (no public access)

  ## Notes
  - All image URLs store full Cloudinary HTTPS URLs
  - No data is lost - this is a fresh persistent schema replacing ephemeral SQLite
*/

CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(64) UNIQUE NOT NULL,
  email VARCHAR(120) UNIQUE NOT NULL,
  password_hash VARCHAR(256),
  bio TEXT DEFAULT '',
  profile_image VARCHAR(256) DEFAULT '',
  is_admin BOOLEAN DEFAULT false,
  is_verified BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_users_username ON users (username);
CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);

ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role has full access to users"
  ON users
  FOR SELECT
  TO service_role
  USING (true);

CREATE POLICY "Service role can insert users"
  ON users
  FOR INSERT
  TO service_role
  WITH CHECK (true);

CREATE POLICY "Service role can update users"
  ON users
  FOR UPDATE
  TO service_role
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Service role can delete users"
  ON users
  FOR DELETE
  TO service_role
  USING (true);


CREATE TABLE IF NOT EXISTS artworks (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  image_url VARCHAR(500) NOT NULL,
  title VARCHAR(200) NOT NULL,
  description TEXT DEFAULT '',
  category VARCHAR(50) DEFAULT 'other',
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_artworks_category ON artworks (category);
CREATE INDEX IF NOT EXISTS ix_artworks_created_at ON artworks (created_at);

ALTER TABLE artworks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role has full access to artworks"
  ON artworks FOR SELECT TO service_role USING (true);
CREATE POLICY "Service role can insert artworks"
  ON artworks FOR INSERT TO service_role WITH CHECK (true);
CREATE POLICY "Service role can update artworks"
  ON artworks FOR UPDATE TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role can delete artworks"
  ON artworks FOR DELETE TO service_role USING (true);


CREATE TABLE IF NOT EXISTS followers (
  id SERIAL PRIMARY KEY,
  follower_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  following_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE (follower_id, following_id)
);

ALTER TABLE followers ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role has full access to followers"
  ON followers FOR SELECT TO service_role USING (true);
CREATE POLICY "Service role can insert followers"
  ON followers FOR INSERT TO service_role WITH CHECK (true);
CREATE POLICY "Service role can update followers"
  ON followers FOR UPDATE TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role can delete followers"
  ON followers FOR DELETE TO service_role USING (true);


CREATE TABLE IF NOT EXISTS likes (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  artwork_id INTEGER NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE (user_id, artwork_id)
);

ALTER TABLE likes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role has full access to likes"
  ON likes FOR SELECT TO service_role USING (true);
CREATE POLICY "Service role can insert likes"
  ON likes FOR INSERT TO service_role WITH CHECK (true);
CREATE POLICY "Service role can update likes"
  ON likes FOR UPDATE TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role can delete likes"
  ON likes FOR DELETE TO service_role USING (true);


CREATE TABLE IF NOT EXISTS comments (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  artwork_id INTEGER NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE comments ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role has full access to comments"
  ON comments FOR SELECT TO service_role USING (true);
CREATE POLICY "Service role can insert comments"
  ON comments FOR INSERT TO service_role WITH CHECK (true);
CREATE POLICY "Service role can update comments"
  ON comments FOR UPDATE TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role can delete comments"
  ON comments FOR DELETE TO service_role USING (true);


CREATE TABLE IF NOT EXISTS channels (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) UNIQUE NOT NULL,
  description TEXT DEFAULT '',
  created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE channels ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role has full access to channels"
  ON channels FOR SELECT TO service_role USING (true);
CREATE POLICY "Service role can insert channels"
  ON channels FOR INSERT TO service_role WITH CHECK (true);
CREATE POLICY "Service role can update channels"
  ON channels FOR UPDATE TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role can delete channels"
  ON channels FOR DELETE TO service_role USING (true);


CREATE TABLE IF NOT EXISTS messages (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  channel_id INTEGER NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
  content TEXT DEFAULT '',
  image_url VARCHAR(500),
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_messages_created_at ON messages (created_at);

ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role has full access to messages"
  ON messages FOR SELECT TO service_role USING (true);
CREATE POLICY "Service role can insert messages"
  ON messages FOR INSERT TO service_role WITH CHECK (true);
CREATE POLICY "Service role can update messages"
  ON messages FOR UPDATE TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role can delete messages"
  ON messages FOR DELETE TO service_role USING (true);


CREATE TABLE IF NOT EXISTS collections (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name VARCHAR(200) NOT NULL,
  description TEXT DEFAULT '',
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE collections ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role has full access to collections"
  ON collections FOR SELECT TO service_role USING (true);
CREATE POLICY "Service role can insert collections"
  ON collections FOR INSERT TO service_role WITH CHECK (true);
CREATE POLICY "Service role can update collections"
  ON collections FOR UPDATE TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role can delete collections"
  ON collections FOR DELETE TO service_role USING (true);


CREATE TABLE IF NOT EXISTS collection_artworks (
  id SERIAL PRIMARY KEY,
  collection_id INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
  artwork_id INTEGER NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
  position INTEGER DEFAULT 0,
  added_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE (collection_id, artwork_id)
);

ALTER TABLE collection_artworks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role has full access to collection_artworks"
  ON collection_artworks FOR SELECT TO service_role USING (true);
CREATE POLICY "Service role can insert collection_artworks"
  ON collection_artworks FOR INSERT TO service_role WITH CHECK (true);
CREATE POLICY "Service role can update collection_artworks"
  ON collection_artworks FOR UPDATE TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role can delete collection_artworks"
  ON collection_artworks FOR DELETE TO service_role USING (true);


CREATE TABLE IF NOT EXISTS notifications (
  id SERIAL PRIMARY KEY,
  recipient_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  sender_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  notif_type VARCHAR(20) NOT NULL,
  artwork_id INTEGER REFERENCES artworks(id) ON DELETE SET NULL,
  read BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_notifications_created_at ON notifications (created_at);

ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role has full access to notifications"
  ON notifications FOR SELECT TO service_role USING (true);
CREATE POLICY "Service role can insert notifications"
  ON notifications FOR INSERT TO service_role WITH CHECK (true);
CREATE POLICY "Service role can update notifications"
  ON notifications FOR UPDATE TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role can delete notifications"
  ON notifications FOR DELETE TO service_role USING (true);


CREATE TABLE IF NOT EXISTS direct_messages (
  id SERIAL PRIMARY KEY,
  sender_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  recipient_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  read BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_direct_messages_created_at ON direct_messages (created_at);

ALTER TABLE direct_messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role has full access to direct_messages"
  ON direct_messages FOR SELECT TO service_role USING (true);
CREATE POLICY "Service role can insert direct_messages"
  ON direct_messages FOR INSERT TO service_role WITH CHECK (true);
CREATE POLICY "Service role can update direct_messages"
  ON direct_messages FOR UPDATE TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role can delete direct_messages"
  ON direct_messages FOR DELETE TO service_role USING (true);
