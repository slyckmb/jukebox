-- Migration 003: Artist Staging Table
-- Created: 2025-11-25
-- Purpose: Support admin staging area for artist validation workflow

-- Create artist_staging table
CREATE TABLE IF NOT EXISTS artist_staging (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,  -- Who first pulled this artist
    artist_name TEXT NOT NULL,
    lidarr_artist_id INTEGER,  -- Lidarr's internal artist ID
    mb_artist_id TEXT NOT NULL UNIQUE,  -- MusicBrainz artist ID (unique constraint prevents duplicates)
    created_at TEXT NOT NULL,
    last_refreshed_at TEXT,  -- Track staleness for auto-refresh
    refresh_count INTEGER DEFAULT 0,  -- Analytics: how often refreshed
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_staging_mb_id ON artist_staging(mb_artist_id);
CREATE INDEX IF NOT EXISTS idx_staging_lidarr_id ON artist_staging(lidarr_artist_id);
CREATE INDEX IF NOT EXISTS idx_staging_last_refresh ON artist_staging(last_refreshed_at);
CREATE INDEX IF NOT EXISTS idx_staging_user ON artist_staging(user_id);

-- Optional: link requests to staging (for analytics/tracking)
-- Note: This column may remain NULL for requests not using staging
ALTER TABLE requests ADD COLUMN artist_staging_id INTEGER REFERENCES artist_staging(id);
