-- Migration 003: Add download tracking fields
-- Date: 2025-11-24
-- Purpose: Track album download progress for status sync

-- Add new columns for tracking download progress
ALTER TABLE requests ADD COLUMN total_albums INTEGER DEFAULT 0;
ALTER TABLE requests ADD COLUMN downloaded_albums INTEGER DEFAULT 0;
ALTER TABLE requests ADD COLUMN last_sync_at TEXT;

-- Update existing 'submitted' requests to trigger sync on next page load
UPDATE requests SET last_sync_at = NULL WHERE status = 'submitted';
