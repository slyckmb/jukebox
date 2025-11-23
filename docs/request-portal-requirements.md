# Jukebox (Lidarr Request Portal) – Requirements (v0.1.0)

## 1. Purpose

Provide a simple, secure web front end for non-admin users to request music.
Each request is translated into a Lidarr API call so that requested music is downloaded and eventually appears in Jellyfin/Navidrome for streaming and raw-file download.

The app should be:

- Simple (KISS)
- Robust and reliable
- Reasonably secure (per-user accounts, no direct access to Lidarr)

---

## 2. System Context

- **Environment**: Runs as a Docker container on the same Docker network as Lidarr.
- **Upstream service**: Lidarr at `http://lidarr:8686` (reachable as `lidarr` inside the Docker network).
- **Downstream consumers**: Jellyfin and/or Navidrome reading the same music library path as Lidarr.
- **Users**: One account per human user; each user can log in and submit requests.

---

## 3. High-Level Workflow

1. User opens the Request Portal in a browser and logs in with their credentials.
2. User submits a “request” (artist and optional album, plus optional note).
3. Portal stores the request in a local SQLite DB.
4. Portal sends a POST to Lidarr’s API to create/monitor the artist (and optionally specific album).
   - Each request is tagged as `requested_by_<username>`.
   - Each request uses a user-specific root folder, e.g. `/data/media/music/lidarr_<username>` or a shared `lidarr_requests`.
5. The app marks the request status as `submitted`.
6. A background job or periodic task (phase 2) may query Lidarr for progress and update request status to `downloading` / `complete` / `error`.
7. Jellyfin/Navidrome scan the library and make the new music available.

---

## 4. Functional Requirements

### 4.1 Authentication

- R1: The portal SHALL support per-user accounts.
- R2: A user SHALL authenticate with username + password.
- R3: Passwords SHALL be stored as salted hashes (e.g. Werkzeug `generate_password_hash()`).
- R4: Sessions SHALL be cookie-based using Flask’s secure session mechanism.
- R5: There SHALL be an “admin” flag in the user table to differentiate admin vs normal user.
- R6: Admin users MAY list all requests; normal users SHOULD only see their own.

### 4.2 Request Capture

Each request SHOULD capture:

- Request ID
- Requesting user (foreign key to `users`)
- Artist name (required)
- Album title (optional; empty means “all albums”)
- Optional free-text note (e.g. “I own this CD; prefer FLAC”)
- Requested root folder:
  - By default derived from username: `/data/media/music/lidarr_<username>`
- Tag string applied in Lidarr:
  - Format: `requested_by_<username>`
- Status (see §4.3)
- Timestamps: `created_at`, `updated_at`
- Optional `lidarr_artist_id` and `lidarr_album_id` if known.

### 4.3 Request Status

Simple, easy-to-report status states:

- `new` – Created in the portal, not yet sent to Lidarr (e.g. transient error or queue).
- `submitted` – Successfully sent to Lidarr; artist added/monitored.
- `existing` – Lidarr indicated the artist/album already exists (no new monitoring needed).
- `failed` – Attempt to send to Lidarr failed (e.g. network, 4xx/5xx).
- (Phase 2 / optional) `downloading`, `complete` – If you later add Lidarr status polling.

Status changes:

- `new` → `submitted` or `failed` (on Lidarr API call)
- `submitted` → `existing` (if Lidarr says already present)
- `submitted` → `downloading` / `complete` (future enhancement)
- Any → `failed` (on error)

### 4.4 API Forwarding to Lidarr

- R7: The app SHALL call Lidarr using `LIDARR_API_KEY` from environment.
- R8: Base URL SHALL be `http://lidarr:8686/api/v1` (configurable via env `LIDARR_URL`).
- R9: Each new request SHALL POST an artist JSON to `/artist` with:
  - `artistName`
  - `monitored: true`
  - `rootFolderPath` (per-user)
  - `tags: ["requested_by_<username>"]`
  - `qualityProfileId` and `metadataProfileId` from env:
    - `LIDARR_QUALITY_PROFILE_ID`
    - `LIDARR_METADATA_PROFILE_ID`
- R10: On failure (non-2xx), the portal SHALL log the error and set request status to `failed`.

---

## 5. Non-Functional Requirements

- N1: KISS: minimal dependencies (Flask, requests, sqlite3, Werkzeug).
- N2: Dockerized, with environment-based configuration.
- N3: Minimal open endpoints:
  - `/health` for liveness.
  - `/login`, `/logout`.
  - `/request/new`, `/requests`.
- N4: Reasonable security:
  - Use HTTPS via reverse proxy (Caddy/Traefik/NGINX) in front of the container.
  - Do not expose Lidarr API keys in logs or UI.
- N5: Logging:
  - Log request creation and Lidarr API outcomes.

---

## 6. Database Requirements (SQLite)

Two primary tables:

- `users`:
  - `id`, `username`, `password_hash`, `is_admin`, `created_at`
- `requests`:
  - `id`, `user_id`, `artist_name`, `album_title`, `note`,
  - `status`, `tag`, `root_folder_path`,
  - `lidarr_artist_id`, `lidarr_album_id`,
  - `created_at`, `updated_at`, `last_error`

---

## 7. API / UI Endpoints

### 7.1 Web UI

- `GET /login` – Render login form.
- `POST /login` – Authenticate user.
- `POST /logout` – Destroy session.
- `GET /` or `/requests` – List the current user’s requests.
- `GET /request/new` – Render a “new request” form.
- `POST /request/new` – Create a new request and send to Lidarr, updating status.

### 7.2 JSON API (for Postman / programmatic test)

- `GET /api/health` – Return JSON `{ "status": "ok" }`.
- `POST /api/login` – Accept JSON `{ "username", "password" }`, return session cookie or token.
- `POST /api/requests` – Accept JSON `{ "artist_name", "album_title", "note" }`, using authenticated user from session, create request and forward to Lidarr, return request JSON.
- `GET /api/requests` – Return list of authenticated user’s requests.
- `GET /api/requests/<id>` – Return single request data.

---

## 8. Configuration & Deployment

Environment variables:

- `FLASK_SECRET_KEY`
- `LIDARR_URL` (default `http://lidarr:8686/api/v1`)
- `LIDARR_API_KEY`
- `LIDARR_QUALITY_PROFILE_ID`
- `LIDARR_METADATA_PROFILE_ID`
- `MUSIC_ROOT_BASE` (default `/data/media/music`)
- `DB_PATH` (default `/app/data/requests.db`)

Docker:

- Container binds `DB_PATH` to a volume.
- Container is placed on the same Docker network as Lidarr.
- Reverse proxy terminates TLS and forwards to `flask-jukebox:5000`.
