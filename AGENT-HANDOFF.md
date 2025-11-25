# Jukebox Agent Handoff

**Date**: 2025-11-25
**Context**: Starting v0.6.0 - Search & UX Improvements Sprint
**Repo**: /home/michael/dev/work/jukebox

---

## What You Need to Know

### Project Status
- **v0.6.0 Stage 1-2 Complete**: Quick wins, search fixes, planning done
- **v0.6.0 Stage 3 Ready**: Artist staging workflow (major feature, 4-5 hours)
- **Production**: Running at https://jukebox.bikejeepyoga.com
- **Database**: SQLite at `/home/michael/dev/work/jukebox/data/requests.db` (5 users, 14 requests)
- **Recent Work**: Completed Stage 1 (4 tasks), planned Stage 3 (artist staging with admin pool)

### Current Sprint: v0.6.0 - Search & UX Improvements

**See `TODO.md` for detailed task list** (7 tasks across 4 tiers)

**Completed (Stage 1)**:
1. ✅ Removed "Check Plex, Jellyfin, or Navidrome..." message
2. ✅ Fixed unmonitored album handling (flip to monitored)
3. ✅ Fixed Frank Sinatra search flicker bug (race condition)
4. ✅ Improved album search (fallback generic search)

**Stage 2 (Planning Complete)**:
- Strategy sessions on local cache vs staging area
- Decided: staging area approach (admin pool, no local MB cache yet)
- Requirements documented (see `docs/ARTIST-STAGING-REQUIREMENTS.md`)
- Stage 3 plan ready (see `docs/STAGE-3-PLAN.md`)

**Next (Stage 3 - READY TO START)**:
1. **Artist Staging Workflow** (4-5 hours, highest priority):
   - Database migration (`artist_staging` table)
   - "Pull Albums" button (two-phase commit)
   - Admin staging area (no user clutter)
   - Staging reuse across users (7-day refresh)
   - Move to user space on album commit
   - **Solves**: "wrong artist" and "album not found" problems

**After Stage 3 (Quick Wins)**:
2. Trigger search when monitoring album
3. Improve status messages (requested vs available)
4. Show version in UI banner

---

## Key Architecture

**Stack**: Flask + SQLite + Lidarr API + MusicBrainz API
**Main File**: `app/app.py` (~900 lines)
**Database**: `data/requests.db` (users, requests tables)
**Frontend**: Vanilla JS with fuzzy search autocomplete

**Critical Functions**:
- `sync_request_status(req_id)` - Sync single request with Lidarr
- `sync_active_requests()` - Sync all active requests (called on page load)
- `/api/search/artist` - Fuzzy artist search endpoint
- `/api/search/album` - Album search endpoint

---

## Deployment

```bash
cd /home/michael/dev/work/jukebox
docker compose build jukebox && docker compose up -d jukebox

# Verify
curl http://localhost:5000/api/health  # Should return {"status":"ok"}

# Logs
docker compose logs --tail=50 jukebox
```

**Requirements**:
- External secrets: `/mnt/config/secrets/jukebox/env`
- External network: `gluetun_network`

---

## Common Issues

### Search Problems
- MusicBrainz API rate limits (1 req/sec)
- Fuzzy search happening in frontend JS (`app/static/js/app.js`)
- No local cache (hitting MB API for every keystroke)

### Database
- Users table: 5 users (kim, mike, m2, meeko, admin)
- Requests table: 14 historical requests
- No indexes yet (planned for v0.6.0)

### Testing
```bash
# Run tests in container
docker compose exec jukebox python3 -m unittest tests.test_app -v

# Check syntax
python3 -m py_compile app/app.py
node -c app/static/js/app.js
```

---

## What NOT to Do

- ❌ Don't create new planning/status/session docs
- ❌ Don't modify ROADMAP.md or HANDOFF.md unless project status changes
- ❌ Update TODO.md with tasks, check it off as you complete items
- ❌ Don't add features from ALL-PROPOSED-FEATURES.md unless user explicitly requests

---

## Getting Started

1. Read `TODO.md` for current tasks (already prioritized)
2. Start with Quick Win #1 (remove message - trivial text change)
3. Ask user which task to tackle next if unclear
4. Check `ALL-PROPOSED-FEATURES.md` if user requests a feature

**Simple rule**: Implement tasks from TODO.md in priority order. Don't over-document the journey.

---

## Questions for User

If you need clarification on any search bugs:
- "Can you reproduce the Frank Sinatra search issue? What exactly happens?"
- "For Taylor Swift album - what's the exact album title you searched?"
- "Should the album dropdown replace the text input or appear after artist is selected?"

Otherwise, start with Quick Win #1 and work down the list.
