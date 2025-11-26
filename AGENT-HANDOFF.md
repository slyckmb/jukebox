# Jukebox Agent Handoff

**Date**: 2025-11-26
**Version**: v0.6.9
**Repo**: /home/michael/dev/work/jukebox
**Production**: https://jukebox.bikejeepyoga.com

---

## Project Status

### Current State: v0.6.9 - Album-Specific Tracking & Bug Fixes ✅

**Recent Accomplishments** (this session):
- ✅ **v0.6.9 Stage 1**: Fixed 3 critical bugs with album-specific status tracking
- ✅ **Root Cause Analysis**: Identified artist-wide vs album-specific stats issue
- ✅ **Database Migration**: Added album-level tracking (migration 004)
- ✅ **Defensive Monitoring**: Auto-detects and re-enables unmonitored albums
- ✅ **Enhanced Logging**: Better visibility into staging and monitoring operations

**Production Status**:
- Deployed: v0.6.9 running at https://jukebox.bikejeepyoga.com
- Database: SQLite with album-specific columns (migration 004 applied)
- Status: Stage 1 complete, ready for field testing
- Backup: Pre-migration backup saved

**What Works Now** (v0.6.9):
- **Album-specific progress**: Shows "X of Y tracks" for individual albums (not artist-wide)
- **Defensive monitoring**: Auto re-enables monitoring if albums become unmonitored
- **Enhanced unmonitoring**: Verification step ensures all albums actually unmonitored
- **Staging safeguards**: Verifies artist exists before using cached staging entry
- Plus all v0.6.8 features (staging workflow, multiple albums from same artist, etc.)

**What's New in v0.6.9**:
- Per-album track count display (fixes "all cards show same progress" bug)
- Monitoring verification and auto-recovery (fixes albums becoming unmonitored)
- Enhanced logging with [STAGING] and [UNMONITOR] prefixes
- Staging workflow verification before use

---

## Recent Session Summary (v0.6.9)

### v0.6.9 - Album-Specific Tracking (2025-11-26)

**Problem**: Three critical bugs reported:
1. Albums becoming unmonitored after initial monitoring
2. Unrequested album auto-downloaded
3. All Caravan Palace cards showing "4 of 5 albums (80%)" - same for every album

**Root Cause**: Status sync tracked artist-wide statistics instead of individual album data

**Solution - 3 Phases**:

**Phase 1: Album-Specific Status Tracking** (2-3 hours)
- Created migration 004: Added `album_total_tracks`, `album_downloaded_tracks`, `album_monitored` columns
- Updated `sync_request_status()` (app.py:303-464) to query specific albums by `lidarr_album_id`
- Modified request card template to display per-album track counts
- Kept artist-wide stats as fallback for backward compatibility

**Phase 2: Defensive Monitoring Verification** (2-3 hours)
- Added auto-detection of unmonitored albums (app.py:351-366)
- Automatically re-enables monitoring when detected
- Triggers album search after re-enabling
- Enhanced `unmonitor_all_albums()` with before/after verification (app.py:833-915)
- Logs albums that remain monitored after unmonitor attempt

**Phase 3: Staging Workflow Safeguards** (1-2 hours)
- Added artist existence check before using staging cache (app.py:1200-1212)
- Auto-removes stale staging entries
- Enhanced logging with [STAGING] and [UNMONITOR] prefixes
- Better visibility into workflow execution

**Testing**: Ready for field testing - Stage 1 complete, Stage 2 (UX polish) planned

---

## Previous Sessions

### Session Summary (v0.6.4 → v0.6.8)

### Field Test Bug Fixes

**v0.6.4** - Critical Staging Workflow Fixes:
1. **Bug #6**: Artist not monitored after staging move → Fixed by setting `monitored=True` in `move_artist_to_user()` (app.py:819)
2. **Bug #7**: All albums monitored instead of just selected → Fixed with `unmonitor_all_albums()` before move (app.py:742-784)

**v0.6.5** - Edge Case Fixes:
1. **Bug 0.6.4-1**: Deleted artist caused "Failed to load albums" → Added staging verification, auto-cleanup stale entries (app.py:1525-1543)
2. **Bug 0.6.4-2**: Artist name collision (multiple "NF" artists) → Unique paths with MB ID suffix (app.py:611-614)

**v0.6.6** - Multiple Album Fix:
1. **Bug 0.6.5-1**: 2nd/3rd album unmonitored previous albums → Remove artist from staging after move (app.py:1086-1091)

**v0.6.7-v0.6.8** - Instrumentation & Verification:
1. Added logging to verify staging workflow paths
2. Added explicit print statements for album search triggers
3. Field tested: Multiple albums from same artist work correctly

### Key Code Changes (app.py)

**Staging Verification** (lines 1525-1543):
```python
# Check if staging artist still exists in Lidarr before using cache
resp = requests.get(f"{LIDARR_URL}/artist/{lidarr_artist_id}", ...)
if resp.status_code == 404:
    # Clean up stale staging entry
    conn.execute("DELETE FROM artist_staging WHERE lidarr_artist_id = ?", ...)
```

**Unique Artist Paths** (lines 611-614):
```python
# Prevent name collisions (e.g., multiple "NF" artists)
mb_id_suffix = mb_artist_id[:8] if mb_artist_id else ""
path = f"{root_folder}/{name}-{mb_id_suffix}" if mb_id_suffix else f"{root_folder}/{name}"
```

**Staging Cleanup After Move** (lines 1086-1091):
```python
# Remove from staging after successful move (prevents re-processing)
app.logger.info(f"Removing artist {lidarr_artist_id} from staging after successful move")
conn.execute("DELETE FROM artist_staging WHERE lidarr_artist_id = ?", (lidarr_artist_id,))
```

**Album Search Trigger** (lines 560-585):
```python
def trigger_album_search(album_id: int):
    # Explicit print statements for monitoring
    print(f"[ALBUM SEARCH TRIGGER] Called for album ID {album_id}", flush=True)
    # ... send AlbumSearch command to Lidarr
```

---

## Architecture Overview

**Stack**: Flask + SQLite + Lidarr API + MusicBrainz API
**Main File**: `app/app.py` (~1600 lines as of v0.6.8)
**Database**: `data/requests.db` (users, requests, artist_staging tables)
**Frontend**: Vanilla JS with fuzzy search autocomplete

**Critical Functions**:
- `create_artist_in_staging()` - Add artist to admin staging area (app.py:590-651)
- `move_artist_to_user()` - Move from staging to user space (app.py:786-833)
- `unmonitor_all_albums()` - Reset album monitoring before move (app.py:742-784)
- `set_album_monitored()` - Set album monitored + trigger search (app.py:520-558)
- `trigger_album_search()` - Send AlbumSearch command to Lidarr (app.py:560-585)
- `find_staging_artist()` - Check if artist in staging by MB ID (app.py:652-667)

**Database Schema**:
```sql
-- Artist staging table (added in migration 003)
CREATE TABLE artist_staging (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    artist_name TEXT NOT NULL,
    lidarr_artist_id INTEGER NOT NULL,
    mb_artist_id TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    last_refreshed_at TEXT,
    refresh_count INTEGER DEFAULT 0
);
```

---

## Deployment

```bash
cd /home/michael/dev/work/jukebox

# Build and deploy
DOCKER_BUILDKIT=0 docker compose build jukebox
docker compose up -d jukebox

# Verify
curl http://localhost:5000/api/health  # Should return {"status":"ok","app":"Jukebox"}
docker compose logs --tail=50 jukebox

# Check version (should show v0.6.8)
curl https://jukebox.bikejeepyoga.com/requests | grep version-badge
```

**Requirements**:
- External secrets: `/mnt/config/secrets/jukebox/env`
- External network: `gluetun_network`

---

## Active Tasks & Priorities

**See `TODO.md` for complete task list**

### High Priority (P1)

1. **BUG #5**: Lidarr status updates not syncing to request cards
   - Issue: Cards don't show download progress
   - Impact: Users can't track request status
   - Investigation needed: `sync_active_requests()` and `sync_request_status()`

### Medium Priority (P2)

2. **Feature Request**: API Health Check Button
   - Add button to ping MB and Lidarr APIs
   - Useful for debugging connection issues
   - Effort: 1-2 hours

3. **BUG #4**: Unclear "existing" status on cards
   - Ambiguous: does it mean artist exists or album exists?
   - UX polish issue

### Lower Priority

4. **BUG #1**: Artist search requires full exact name
   - Root cause: MusicBrainz API limitation (not our code)
   - Potential solution: Local MB cache (Tier 4 strategic feature)

---

## Common Issues & Solutions

### Staging Workflow

**Issue**: Artist shows in staging after being moved to user
- **Cause**: Staging cleanup not happening
- **Check**: `artist_staging` table should be empty or have only unmoved artists
- **Fix**: Added in v0.6.6 (app.py:1086-1091)

**Issue**: Multiple albums from same artist - only last monitored
- **Cause**: Artist still in staging, re-triggering unmonitor all
- **Fix**: Remove from staging after move (v0.6.6)

**Issue**: Path collision for artists with same name
- **Cause**: Path generated from name only
- **Fix**: Append MB ID suffix (v0.6.5)

### Database Cleanup

```bash
# Check staging table
sqlite3 /home/michael/dev/work/jukebox/data/requests.db \
  "SELECT id, artist_name, lidarr_artist_id FROM artist_staging;"

# Clean up stale entries (if needed)
sqlite3 /home/michael/dev/work/jukebox/data/requests.db \
  "DELETE FROM artist_staging WHERE lidarr_artist_id NOT IN (SELECT id FROM ...);"
```

### Testing

```bash
# Check syntax
python3 -m py_compile app/app.py
node -c app/static/js/app.js

# Monitor album search triggers
docker compose logs -f jukebox | grep "ALBUM SEARCH"
```

---

## What NOT to Do

- ❌ Don't create new planning/status/session docs
- ❌ Don't modify ROADMAP.md or HANDOFF.md unless project status significantly changes
- ✅ DO update TODO.md with tasks and mark them as complete
- ❌ Don't add features from ALL-PROPOSED-FEATURES.md unless user explicitly requests
- ✅ DO use the TodoWrite tool to track progress on multi-step tasks

---

## Getting Started (Next Session)

1. **Read `TODO.md`** - Current tasks already prioritized
2. **Check active bugs** - Start with P1 issues (BUG #5 - status sync)
3. **User requests** - Implement specific features as requested
4. **Field testing** - User may report new bugs, add to TODO and fix

**Simple rule**: Work from TODO.md priority order. User will provide specific requests or bug reports. Don't over-document the journey.

---

## Quick Reference

**Version History**:
- v0.6.0: Stage 3 & 4 complete (staging workflow, quick wins)
- v0.6.1: Fix "Pull Albums" for existing artists
- v0.6.2-v0.6.3: Logging and instrumentation
- v0.6.4: Fix artist monitoring and album selection bugs
- v0.6.5: Fix deleted artist cache and name collision
- v0.6.6: Fix multiple album monitoring issue
- v0.6.7-v0.6.8: Enhanced logging and field testing
- v0.6.9: Album-specific tracking, defensive monitoring, staging safeguards (2025-11-26)

**Commits** (most recent):
- d1b4842: fix: prevent album monitoring reset (v0.6.6)
- 4a08673: fix: resolve staging workflow bugs (v0.6.5)
- dd5fcae: feat: implement Stage 4 quick wins (v0.6.0)
- d2d36d5: feat: complete Stage 3 artist staging workflow (v0.6.0)
