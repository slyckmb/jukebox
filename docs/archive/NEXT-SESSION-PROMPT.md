# Next Session Prompt - Jukebox Project

**Date**: 2025-11-24
**Current Status**: v0.4.0-dev (Stage 3 Complete - THE MONEY SHOT! 🎉)
**Repository**: /home/michael/dev/work/glider/glider-docker/jukebox

---

## Quick Context

You're working on **Jukebox** - a music request portal that integrates with Lidarr to let users request music downloads. The app is mobile-first, uses Flask + SQLite, and is deployed at https://jukebox.bikejeepyoga.com.

**What's Working Right Now**:
- ✅ Complete user journey: Request → See Download Progress → Click "Listen Now" → Music Plays!
- ✅ Lidarr status sync with animated progress bars
- ✅ Listen Now buttons (Plex/Jellyfin/Navidrome deep links)
- ✅ Error handling, duplicate detection, mobile-optimized UI
- ✅ Container rebuilt, deployed, tested (Nov 24, 2025)

**Last Commit**: `f82c91d` - "feat: complete Stage 3 - Lidarr status tracking with download progress (v0.4.0)"

---

## What to Read First

**Essential Documents** (read these in order):
1. `docs/MASTER-ROADMAP.md` - **SINGLE SOURCE OF TRUTH** for priorities and next steps
2. `docs/HANDOFF-JUKEBOX.md` - Project overview, architecture, common operations
3. `docs/STAGE-3-COMPLETION.md` - What was just completed (the money shot!)

**Feature Specs** (if implementing next priority):
- `docs/FEATURE-FUZZY-AUTOCOMPLETE.md` - Detailed spec for Priority 1 (next to implement)
- `docs/ALL-PROPOSED-FEATURES.md` - Complete feature list (47 features ranked)
- `docs/UX-ENHANCEMENTS-FRONTEND.md` - 9 frontend UX improvements

**Reference** (as needed):
- `docs/SECRETS.md` - Secret management documentation
- `docs/CLOUDFLARE-ACCESS-SETUP.md` - Infrastructure setup
- `docs/SECURITY-AUDIT-REPORT.md` - Security audit results

---

## Current Architecture

**File Structure**:
```
jukebox/
├── app/
│   ├── app.py                    # Flask app with sync_request_status(), sync_active_requests()
│   ├── error_parser.py           # Error message parsing
│   ├── templates/
│   │   ├── requests.html         # Main UI with progress bars and Listen Now buttons
│   │   └── components/
│   │       ├── request_card.html # Card with progress/Listen Now (takes media_servers param!)
│   │       └── status_badge.html # Status icons
│   └── static/
│       ├── css/base.css
│       └── js/app.js
├── db/
│   └── migrations/
│       ├── 001_initial_schema.sql
│       ├── 002_add_user_email.sql
│       └── 003_add_download_tracking.sql  # Stage 3: total_albums, downloaded_albums, last_sync_at
└── docs/ (18 files - consolidated, deprecated docs removed)
```

**Key Functions** (app/app.py):
- `sync_request_status(request_id)` - Syncs single request with Lidarr (lines 295-404)
- `sync_active_requests()` - Syncs all active requests, called on page load (line 406+)
- `_render_requests_page(user)` - Renders request list, calls sync first (line 584+)

**Database Schema** (requests table):
```sql
-- Core fields
id, username, artist_name, album_title, note, status, created_at, updated_at
-- Lidarr integration
lidarr_artist_id, last_error
-- Stage 3 additions
total_albums, downloaded_albums, last_sync_at
```

**Status Flow**:
- `new` → `submitted` → `downloading` → `completed`
- Also: `failed`, `existing`

---

## What's Next (Priority Order)

**See `docs/MASTER-ROADMAP.md` for full details**

### Priority 1: Fuzzy Autocomplete ⭐⭐⭐⭐
**Time**: 2-3 hours
**Why**: Reduce failed requests by 80% - users type "beatels" → finds "The Beatles"
**Spec**: `docs/FEATURE-FUZZY-AUTOCOMPLETE.md`

**What to implement**:
- Case-insensitive artist search with fuzzy matching (SequenceMatcher)
- Dropdown with autocomplete suggestions (mobile-friendly)
- Two backend endpoints: `/api/artists/search`, `/api/artists/<id>`
- JavaScript autocomplete class with debouncing
- Update new_request.html with autocomplete input

### Priority 2: UI Cleanup ⭐⭐
**Time**: 2-3 hours (4 small features)

**What to implement**:
1. Show/Hide Failed toggle (20 min)
2. Delete request button (45 min)
3. Status filter pills (40 min)
4. Database indexes (15 min)

---

## Common Operations

**Development**:
```bash
# Working directory
cd /home/michael/dev/work/glider/glider-docker/jukebox

# Check syntax
python3 -m py_compile app/app.py
node -c app/static/js/app.js

# View database
sqlite3 data/requests.db 'SELECT id, artist_name, status, downloaded_albums, total_albums FROM requests ORDER BY id DESC LIMIT 10;'
```

**Deployment**:
```bash
# Rebuild container
cd /home/michael/dev/work/glider/glider-docker/jukebox
DOCKER_BUILDKIT=0 docker compose build jukebox
docker compose up -d jukebox

# Check health
curl -s http://localhost:5000/api/health
docker compose logs --tail=20 jukebox
```

**Testing**:
```bash
# Run tests
python -m pytest tests/test_app.py -v

# Manual test
curl -s http://localhost:5000/login
curl -s http://localhost:5000/api/health
```

---

## Recent Bug Fixes

**Template Bug (Fixed Nov 24)**:
- **Issue**: `media_servers` was undefined in `request_card.html` macro
- **Fix**: Updated macro signature to `{% macro request_card(req, media_servers) %}`
- **Fix**: Updated caller in `requests.html` to `{{ request_card(req, media_servers) }}`
- **Status**: Fixed, tested, deployed ✅

---

## Important Notes

1. **Always pass media_servers to request_card macro** - Recent bug fix!

2. **Single repo workflow** - Work directly in `/home/michael/dev/work/glider/glider-docker/jukebox` (no more syncing between repos!)

3. **Sync happens on page load** - `_render_requests_page()` calls `sync_active_requests()` before rendering

4. **Database migration pattern**:
   - Create migration SQL in `db/migrations/00X_description.sql`
   - Run via Python in container: `docker compose exec jukebox python3 -c "..."`
   - sqlite3 command not available in container

5. **Mobile-first CSS** - All UI must work on 320px+ screens, touch targets ≥44px

6. **MASTER-ROADMAP.md is the single source of truth** - Don't create new planning docs, update this one

---

## Git Status

**Last commit**: `f82c91d` - Stage 3 completion
**Branch**: main
**Clean working directory**: Yes (all changes committed)

**Recent commits**:
```
f82c91d - feat: complete Stage 3 - Lidarr status tracking with download progress (v0.4.0)
3dc680e - refactor(config-update): switch to manifest-based stack discovery
eef0a58 - chore: remove legacy script stubs
```

---

## Questions to Ask User

If user says "continue" or "next":
1. Check `docs/MASTER-ROADMAP.md` for recommended priority
2. Ask: "Should I implement Priority 1 (Fuzzy Autocomplete) or Priority 2 (UI Cleanup)?"
3. If user chooses autocomplete, read `docs/FEATURE-FUZZY-AUTOCOMPLETE.md` and implement

If user wants status:
1. Confirm Stage 3 is complete ✅
2. Mention the complete user journey works end-to-end
3. Reference MASTER-ROADMAP.md for next priorities

---

## Success Metrics

**Current Status**:
- ✅ Core user journey complete (80% of value delivered)
- ✅ Download progress visible
- ✅ Listen Now buttons working
- ⚠️ Manual typing (autocomplete will reduce errors by 80%)
- ⚠️ No filters/delete (UI cleanup will add polish)

**After Priority 1 (Autocomplete)**: 95% complete
**After Priority 2 (UI Cleanup)**: Production-ready and awesome!

---

## Prompt for Next Agent

**Copy/paste this to start new session**:

```
I'm continuing work on the Jukebox music request portal (v0.4.0-dev, Stage 3 Complete).

Stage 3 just finished - users can now see download progress and click Listen Now buttons. The core user journey works end-to-end! 🎉

Please read these docs to get up to speed:
1. docs/MASTER-ROADMAP.md (single source of truth for priorities)
2. docs/HANDOFF-JUKEBOX.md (project overview)
3. docs/STAGE-3-COMPLETION.md (what was just completed)

The next priority is implementing Fuzzy Autocomplete (Priority 1) to reduce failed requests by 80%. See docs/FEATURE-FUZZY-AUTOCOMPLETE.md for the full spec.

Working directory: /home/michael/dev/work/glider/glider-docker/jukebox

What should we work on next?
```

---

**End of Next Session Prompt**

**Remember**:
- Read MASTER-ROADMAP.md first - it's the single source of truth
- Stage 3 is COMPLETE and TESTED ✅
- Next up: Fuzzy Autocomplete (2-3 hours) or UI Cleanup (2-3 hours)
