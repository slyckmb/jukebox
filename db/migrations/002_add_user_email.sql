-- Migration: Add email column to users table
-- Version: 0.3.0
-- Date: 2025-11-23
-- Author: Claude Code
--
-- Description:
--   Adds email field to users table for Cloudflare Access synchronization.
--   Enables single source of truth for user access management.
--
-- Applied: 2025-11-24

BEGIN TRANSACTION;

-- Add email column (nullable for backward compatibility)
ALTER TABLE users ADD COLUMN email TEXT;

-- Create unique index on email (partial index for non-null values)
CREATE UNIQUE INDEX idx_users_email ON users(email) WHERE email IS NOT NULL;

-- Populate existing users with their email addresses
UPDATE users SET email = 'braband@gmail.com' WHERE username = 'mike';
UPDATE users SET email = 'hansingkc@gmail.com' WHERE username = 'kim';
UPDATE users SET email = 'mramirez9316@gmail.com' WHERE username = 'm2';
UPDATE users SET email = 'm33ko.ramirez@icloud.com' WHERE username = 'meeko';

COMMIT;

-- Verify migration
.schema users
SELECT username, email, is_admin FROM users ORDER BY username;
