-- Jukebox SQLite Schema v0.1.0 – Last updated: 2025-11-23T12:00:00-05:00

CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    is_admin        INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS requests (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             INTEGER NOT NULL,
    artist_name         TEXT NOT NULL,
    album_title         TEXT,
    note                TEXT,
    status              TEXT NOT NULL DEFAULT 'new',
    tag                 TEXT NOT NULL,
    root_folder_path    TEXT NOT NULL,
    lidarr_artist_id    INTEGER,
    lidarr_album_id     INTEGER,
    last_error          TEXT,
    created_at          TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at          TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_requests_user_id ON requests(user_id);
CREATE INDEX IF NOT EXISTS idx_requests_status ON requests(status);
CREATE INDEX IF NOT EXISTS idx_requests_artist ON requests(artist_name);
