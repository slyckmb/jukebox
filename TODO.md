# Jukebox TODO

**Current Version**: v0.6.8
**Last Updated**: 2025-11-25

---

## Active Tasks

### Tier 1: Feature Requests

#### New Feature: API Health Check Button 🎯
- [ ] **Request**: Add button to ping MusicBrainz and Lidarr APIs
- [ ] **Use Case**: Debug/dev - verify connections without making requests
- [ ] **Location**: Could add to requests page or new admin page
- [ ] **Priority**: P2 - Nice to have for troubleshooting
- [ ] **Effort**: 1-2 hours (new endpoint + UI button)

---

### Tier 2: Open Bugs - Field Test Issues

#### BUG #1: Artist search requires full exact name
- [ ] **Issue**: Autocomplete doesn't show results until full name is typed
- [ ] **Expected**: Fuzzy search should match partial names like "zach" or "bryan"
- [ ] **Impact**: MEDIUM - Reduces discoverability, frustrates users
- [ ] **Priority**: P1 - Important UX issue
- [ ] **Root Cause**: MusicBrainz API limitation - not our code
- [ ] **Note**: May require local MB cache (Tier 4 feature)
- [ ] **Status**: v0.6.8 - Known limitation, documented

#### BUG #4: Unclear card status - "existing" means artist or album?
- [ ] **Issue**: Request card shows "existing" status - ambiguous
- [ ] **Expected**: Clear distinction - "Artist exists, album monitoring" vs "Album already available"
- [ ] **Impact**: LOW-MEDIUM - Status clarity
- [ ] **Priority**: P2 - UX polish
- [ ] **Location**: Request card rendering logic, status badge

#### BUG #5: Lidarr status updates not syncing to request cards
- [ ] **Issue**: Request card statuses don't update to reflect Lidarr download progress
- [ ] **Expected**: Cards should show "downloading", "completed", progress bars
- [ ] **Impact**: HIGH - Users can't track request progress
- [ ] **Priority**: P1 - Core functionality
- [ ] **Investigation**: Check `sync_active_requests()` and `sync_request_status()` functions
- [ ] **Location**: Status sync logic (app/app.py), possibly page load sync trigger

---

## Completed - v0.6.8 Field Test & Bug Fixes (2025-11-25)

### Critical Staging Workflow Fixes

#### BUG #6: Artist NOT monitored after staging workflow ✅ FIXED (v0.6.4)
- [x] **Issue**: Artist moved from staging to user space is NOT monitored in Lidarr
- [x] **Root Cause**: `move_artist_to_user()` didn't set artist monitored=True
- [x] **Fix**: Added `artist_data["monitored"] = True` in move_artist_to_user() (app.py:819)
- [x] **Status**: v0.6.4 - Fixed and verified

#### BUG #7: ALL albums monitored instead of just selected album ✅ FIXED (v0.6.4)
- [x] **Issue**: When moving artist from staging, ALL albums were being monitored
- [x] **Root Cause**: Lidarr metadata refresh auto-monitors albums, staging didn't reset
- [x] **Fix**: Created `unmonitor_all_albums()` function, called before moving artist (app.py:742-784)
- [x] **Status**: v0.6.4 - Fixed and verified

#### BUG 0.6.4-1: Deleted artist causes "Failed to load albums" ✅ FIXED (v0.6.5)
- [x] **Issue**: Deleted artist in Lidarr still cached in staging, causing load errors
- [x] **Root Cause**: Staging table not checked for deleted artists
- [x] **Fix**: Added artist existence verification before using cached staging entry (app.py:1525-1543)
- [x] **Implementation**: Check Lidarr API, clean up stale staging entries automatically
- [x] **Status**: v0.6.5 - Fixed and verified

#### BUG 0.6.4-2: Multiple artists with same name cause path collision ✅ FIXED (v0.6.5)
- [x] **Issue**: Artists with identical names (e.g., multiple "NF") caused path conflicts
- [x] **Root Cause**: Path generated from name only: `/lidarr_admin/NF`
- [x] **Fix**: Append MusicBrainz ID suffix for uniqueness: `/lidarr_admin/NF-5660a8c7` (app.py:611-614)
- [x] **Status**: v0.6.5 - Fixed and verified

#### BUG 0.6.5-1 / 0.6.6-1: Multiple albums from same artist - only last monitored ✅ FIXED (v0.6.6)
- [x] **Issue**: Requesting 2nd/3rd album from same artist unmonitored previous albums
- [x] **Root Cause**: Artist not removed from staging after move, re-triggered "unmonitor all"
- [x] **Fix**: Remove artist from staging table after successful move to user space (app.py:1086-1091)
- [x] **Status**: v0.6.6 - Fixed, v0.6.7 field tested successfully

### Enhancement & Instrumentation

#### Album Search Trigger Verification ✅ INSTRUMENTED (v0.6.8)
- [x] **Task**: Verify automatic album search is triggered after monitoring
- [x] **Implementation**: Added explicit print statements to trigger_album_search() (app.py:565-585)
- [x] **Logging**: Shows when search triggered, command sent, Lidarr response
- [x] **Status**: v0.6.8 - Instrumented for monitoring, appears to be working

---

## Completed - v0.6.0-v0.6.3 (Search & UX Sprint)

### Stage 3: Artist Staging Workflow ✅ COMPLETE
- [x] **Phase 1**: Database migration (`artist_staging` table)
- [x] **Phase 2**: Backend helper functions (create, find, refresh, move)
- [x] **Phase 3**: API endpoints (`/pull-albums`, `/albums/{id}`)
- [x] **Phase 4**: Configuration (STAGING_REFRESH_DAYS)
- [x] **Phase 5**: Update request submission flow (use staging)
- [x] **Phase 6**: Frontend UI + Polling ("Pull Albums" button, album dropdown, polling)
- [x] **Impact**: Solves "wrong artist" and "album not found" problems
- [x] **Status**: All 6 phases implemented and field tested

**Key Features**:
- Two-phase commit (validate → pull → commit)
- Admin staging area (no user clutter)
- Staging reuse across users (performance)
- Auto-refresh stale artists (7-day threshold)
- Move to user space on commit
- Cleanup on move (prevents duplicate processing)

### Stage 4: Quick Wins ✅ COMPLETE
- [x] Trigger search when flipping album to monitored (immediate downloads)
- [x] Improve status messages ("already requested" vs "already available")
- [x] Show version number in UI banner

### Bug Fixes (Previous Versions)
- [x] Pull Albums fails when artist already exists in Lidarr (v0.6.1)
- [x] Misleading "already available" message for new album (v0.6.2)
- [x] Fix Frank Sinatra search flicker (race condition)
- [x] Improve Taylor Swift album search (fallback generic search)
- [x] Remove "Check Plex, Jellyfin, or Navidrome..." message
- [x] Fix unmonitored album handling (flip to monitored)

---

## Future Features - Lower Priority

### Tier 3: Lower Priority Features

#### Add Fuzzy Search for MusicBrainz Input 🎯
- [ ] Normalize/clean text input before MusicBrainz API calls
- [ ] Resolve user input to valid MB search strings
- [ ] Handle common typos and variations
- [ ] **Impact**: Medium (helps with search accuracy)
- [ ] **Effort**: 1-2 hours

#### Handle partial album downloads 🎯
- [ ] Detect when album has incomplete tracks (some missing)
- [ ] Display per-track status or "partial download" indicator
- [ ] Consider: flip monitor bit on individual tracks?
- [ ] **Impact**: Medium (edge case handling)
- [ ] **Effort**: 2-3 hours (track-level API queries, UI design)

### Tier 4: Strategic/Long-term

#### Build Local MusicBrainz Cache 🏗️ STRATEGIC
- [ ] Design database schema for MB data cache
- [ ] Store validated artist/album data from MB API
- [ ] Check cache before hitting MB web API
- [ ] Reduces API rate and improves response time
- [ ] **Impact**: High (performance, API rate limiting)
- [ ] **Effort**: 3-4 hours (schema, migration, caching logic)

#### Debounce Search UX with Local Cache 🏗️ STRATEGIC
- [ ] Bounce live text entry against local cache only
- [ ] Add "Search MusicBrainz" button for web API hits
- [ ] Improves UX and lowers MB API hit rate
- [ ] **Dependencies**: Requires local MB cache
- [ ] **Impact**: Medium (UX refinement)
- [ ] **Effort**: 2 hours

---

## Backlog

See `docs/ALL-PROPOSED-FEATURES.md` for 47 ranked feature ideas.

When user requests a feature, move it here as a task.
