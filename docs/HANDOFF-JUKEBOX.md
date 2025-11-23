# Jukebox Handoff – Debugging Lidarr Failures

**Context**
- Jukebox (Flask + SQLite + Lidarr API), Dockerized, Cloudflare tunnel.
- Live at `https://jukebox.bikejeepyoga.com` on `gluetun_network`; ingress + DNS configured.
- Secrets: `/mnt/config/secrets/jukebox/env` (Flask secret), `/mnt/config/secrets/bash/bash_lidarr-api-key.env` (Lidarr key).
- Recent commits:
  - `app/app.py`: tag lookup/create uses tag IDs; artist lookup populates `foreignArtistId`; `addOptions`/`path`; `_FILE` secrets; `before_request` startup for Flask 3.
  - Offline Docker build with vendored wheels in `jukebox/vendor`.
  - Tests added: `tests/test_app.py` (mocked Lidarr payload/API flow).
  - Cloudflared ingress (`jukebox.bikejeepyoga.com`) routed via `cloudflared tunnel route dns glider-tunnel …`.
- Tests: `python -m pytest tests/test_app.py` passes. Container rebuilt and running.

**Outstanding issue**
- Two failed requests in DB; latest `last_error` shows Lidarr 400: `ForeignArtistId must not be empty`. Prior tag ID error fixed. Need to validate live Lidarr interactions (tag/artist lookup/payload).

**Suggested plan**
1) Inspect current failures:
   - `sqlite3 data/requests.db 'select id, artist_name, status, last_error from requests order by id desc limit 5;'`
   - `docker compose logs --tail=200 jukebox`
2) Verify live Lidarr expectations:
   - Confirm env (`LIDARR_URL`, profile IDs, root folder) matches Lidarr config.
   - Check `/tag` and `/artist/lookup?term=...` responses; ensure `foreignArtistId` is present and payload fields match the running Lidarr version.
3) Expand tests:
   - Mock Lidarr for: existing tag, new tag creation, lookup with no/multiple results, artist POST success/failure, status transitions, per-user access.
4) Fix logic as needed:
   - Adjust `create_artist_in_lidarr` if Lidarr requires different payload (rootFolder/addOptions variants, fallback when `foreignArtistId` missing).
   - Ensure tag endpoints/IDs align with current Lidarr version.
5) Validate:
   - `pytest tests/test_app.py`
   - `DOCKER_BUILDKIT=0 docker compose build jukebox && DOCKER_BUILDKIT=0 docker compose up -d jukebox`
   - Submit a new request in UI/API; verify status = `submitted` (not `failed`), tag applied, root folder derived per user.

**Key files**
- `jukebox/app/app.py`
- `jukebox/tests/test_app.py`
- `jukebox/docker/Dockerfile`, `jukebox/docker-compose.yml`
- `jukebox/docs/SECRETS.md`, `cloudflared/config.yml`

**Target**
- New requests succeed against Lidarr: tag IDs applied, `foreignArtistId` populated, status `submitted`, no 400 errors.
