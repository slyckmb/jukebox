-- Migration 004: Add album-specific tracking fields
-- Date: 2025-11-26
-- Version: v0.6.9
-- Purpose: Track individual album progress instead of artist-wide statistics
--          Fixes bugs v0.6.8-1 (albums unmonitored) and UX issue (artist-wide progress)

-- Add new columns for album-specific tracking
ALTER TABLE requests ADD COLUMN album_total_tracks INTEGER DEFAULT 0;
ALTER TABLE requests ADD COLUMN album_downloaded_tracks INTEGER DEFAULT 0;
ALTER TABLE requests ADD COLUMN album_monitored BOOLEAN DEFAULT NULL;

-- Note: Keep existing total_albums/downloaded_albums for backward compatibility
-- They will be deprioritized in UI but maintained for reference

-- Trigger re-sync for all active requests to populate new fields
UPDATE requests SET last_sync_at = NULL
WHERE status IN ('submitted', 'downloading')
  AND lidarr_album_id IS NOT NULL;
