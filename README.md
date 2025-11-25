# Jukebox - Music Request Portal

**Version**: 0.5.0
**Status**: Production-Ready (95% complete)
**URL**: https://jukebox.bikejeepyoga.com

Flask app that lets users request music downloads via Lidarr with real-time progress tracking.

---

## Quick Start

### Production Deployment

```bash
cd /home/michael/dev/work/jukebox
docker compose build jukebox && docker compose up -d jukebox

# Verify
curl http://localhost:5000/api/health  # Should return {"status":"ok"}

# Logs
docker compose logs --tail=50 jukebox
```

**Requirements**:
- External secrets at `/mnt/config/secrets/jukebox/env`
- External network: `gluetun_network`
- See `docs/SECRETS.md` for configuration details

### Development/Testing Without Infrastructure

If you don't have the external secrets setup:

1. Create a `.env` file with required variables:
```bash
LIDARR_API_KEY=your-api-key
FLASK_SECRET_KEY=your-secret-key
LIDARR_URL=http://lidarr:8686
```

2. Modify `docker-compose.yml` to use `environment:` instead of `env_file:`

3. Remove the `networks:` section if not using gluetun

---

## Features

- ✅ Fuzzy autocomplete artist/album search
- ✅ Download progress tracking
- ✅ Listen Now buttons (Plex/Jellyfin/Navidrome)
- ✅ Mobile-first responsive UI
- ✅ Duplicate detection
- ✅ Cloudflare Zero Trust auth

---

## Architecture

```
app/
├── app.py           # Flask app (main logic)
├── error_parser.py  # User-friendly error messages
├── templates/       # Jinja2 HTML templates
└── static/          # CSS, JS, icons

db/
└── migrations/      # SQL schema migrations

docs/
├── README.md                  # This file
├── TODO.md                    # Current tasks
├── ROADMAP.md                 # What's next
├── ALL-PROPOSED-FEATURES.md   # Future ideas (47 features)
└── archive/                   # Historical docs
```

---

## Key Functions

**app.py**:
- `sync_request_status(req_id)` - Sync single request with Lidarr
- `sync_active_requests()` - Sync all active requests (called on page load)
- `/api/search/artist` - Fuzzy artist search endpoint
- `/api/search/album` - Album search endpoint

---

## Common Operations

**Deploy changes**:
```bash
# Edit files, then rebuild
docker compose build jukebox && docker compose up -d jukebox
```

**Database queries**:
```bash
docker compose exec jukebox sqlite3 /app/data/requests.db \
  "SELECT id, artist_name, status FROM requests ORDER BY id DESC LIMIT 10;"
```

**View requests**:
```bash
curl -s http://localhost:5000/api/requests | jq .
```

---

## Documentation

- **TODO.md** - Current tasks (check this first!)
- **ROADMAP.md** - What's next (1 priority remaining)
- **ALL-PROPOSED-FEATURES.md** - Feature ideas ranked by impact/complexity
- **SECRETS.md** - Secret management
- **CLOUDFLARE-ACCESS-SETUP.md** - Infrastructure setup

Historical docs moved to `docs/archive/`.

---

## Next Priority

**UI Cleanup** (2-3 hours):
1. Show/Hide Failed toggle
2. Delete request button
3. Status filter pills
4. Database indexes

See `ROADMAP.md` for details.
