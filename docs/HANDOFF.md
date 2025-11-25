# Jukebox Quick Reference

**Version**: 0.5.0 → 0.6.0 (in progress)
**Repo**: /home/michael/dev/work/jukebox
**URL**: https://jukebox.bikejeepyoga.com

---

## What It Does

Music request portal integrated with Lidarr:
1. User types artist/album (fuzzy autocomplete helps)
2. Submit request → Lidarr downloads music
3. See progress (e.g., "3 of 10 albums downloaded")
4. Click "Listen Now" → Opens in Plex/Jellyfin/Navidrome

---

## Common Commands

```bash
# Rebuild & deploy
docker compose build jukebox && docker compose up -d jukebox

# Check health
curl http://localhost:5000/api/health

# View logs
docker compose logs --tail=50 jukebox

# Check syntax
python3 -m py_compile app/app.py
node -c app/static/js/app.js

# Run tests (in container)
docker compose exec jukebox python3 -m unittest tests.test_app -v
```

---

## Key Files

```
app/app.py          - Main Flask app (900+ lines)
app/templates/      - HTML templates
app/static/         - CSS/JS/icons
db/migrations/      - SQL schema changes
tests/test_app.py   - Automated tests
```

---

## Important Functions

- `sync_request_status(req_id)` - Sync one request with Lidarr
- `sync_active_requests()` - Sync all active requests (runs on page load)
- `/api/search/artist` - Fuzzy artist search
- `/api/search/album` - Album search

---

## Database

```bash
# View recent requests
docker compose exec jukebox sqlite3 /app/data/requests.db \
  "SELECT id, artist_name, status FROM requests ORDER BY id DESC LIMIT 10;"
```

Schema: users, requests (see db/migrations/ for details)

---

## What's Next

See `TODO.md` for current tasks.
See `ROADMAP.md` for priorities.
See `ALL-PROPOSED-FEATURES.md` for feature ideas.

---

## For Agents

1. Read `TODO.md` first
2. Check `ALL-PROPOSED-FEATURES.md` if user wants a feature
3. Don't create new docs - update existing ones
4. Tasks go in `TODO.md`, not in planning docs
