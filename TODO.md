# Jukebox TODO

**Current Sprint**: Search & UX Improvements (v0.6.0)

---

## Active Tasks (Re-ranked by Impact & Effort)

### Tier 0: Bugs - Field Test Issues (Immediate Priority)

#### BUG #1: Artist search requires full exact name (e.g., 'zach bryan')
- [ ] **Issue**: Autocomplete doesn't show results until full name is typed
- [ ] **Expected**: Fuzzy search should match partial names like "zach" or "bryan"
- [ ] **Impact**: MEDIUM - Reduces discoverability, frustrates users
- [ ] **Priority**: P1 - Important UX issue
- [ ] **Location**: `/api/search/artist` endpoint or MusicBrainz API query
- [ ] **Investigation**: Check if fuzzy matching is working, API query parameters

#### BUG #2: Automatic album search not triggering after monitoring ✅ INSTRUMENTED
- [x] **Investigation Complete**: Code exists and looks correct
- [x] **Fix**: Added comprehensive logging to trace trigger path
- [x] **Logging Added**:
  - When album set to monitored (both paths)
  - AlbumSearch command send to Lidarr
  - Lidarr response status
- [x] **Location**: app/app.py:556-571, 1054-1058, 1137-1141
- [x] **Next**: Watch logs during next request to see if trigger fires
- [x] **Status**: v0.6.2 - Ready for field test verification

#### BUG #3: Misleading "already available" message for new album ✅ FIXED
- [x] **Issue**: Requested new album from existing artist, got confusing message
- [x] **Old Message**: "'Zach Bryan' by Zach Bryan is already available!"
- [x] **New Message**: "Album 'Zach Bryan' is already available! (Artist: Zach Bryan)"
- [x] **Fix**: Changed message to clearly specify ALBUM not artist
- [x] **Also Added**: Logging of album statistics (trackCount) for debugging
- [x] **Location**: app/app.py:1092-1095, 1176-1179
- [x] **Status**: v0.6.2 - Fixed, ready for testing

#### BUG #4: Unclear card status - "existing" means artist or album?
- [ ] **Issue**: Request card shows "existing" status - ambiguous
- [ ] **Context**: Zach Bryan / zachbryan card shows "existing"
- [ ] **Question**: Does this mean artist exists or album exists?
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

### Tier 0: Bugs (Previously Fixed)

#### BUG: Pull Albums fails when artist already exists in Lidarr ✅ FIXED
- [x] **Issue**: Clicking "Pull Albums" for an artist that already exists in Lidarr (any root folder) throws error
- [x] **Error**: Lidarr 400: "This artist has already been added" (ArtistExistsValidator)
- [x] **Root Cause**: `create_artist_in_staging()` doesn't check if artist exists before creating
- [x] **Solution**: Added existence check before creating - now uses existing artist with "ready" state
- [x] **Implementation**: Check `check_artist_exists_in_lidarr()` before `create_artist_in_staging()`
- [x] **Location**: `app/app.py` lines 1482-1500 (pull-albums endpoint)
- [x] **Status**: Fixed, ready for testing

#### TODO: Update requirements documentation
- [ ] **Task**: Clarify in requirements that "Pull Albums" should work for BOTH new and existing artists
- [ ] **Files**: `docs/ARTIST-STAGING-REQUIREMENTS.md` or similar
- [ ] **Context**: Original design assumed staging was only for new artists
- [ ] **Expected behavior**: Pull Albums should:
  1. Check staging first (reuse if found)
  2. Check Lidarr for existing artist (use if found)
  3. Create new artist in staging only if truly new
- [ ] **Priority**: P2 - Documentation update
- [ ] **Effort**: 15 min

---

### Tier 1: Artist Staging Workflow ✅ COMPLETE

#### 1. Artist Staging Workflow 🏗️ (100% Complete)
- [x] **Phase 1**: Database migration (`artist_staging` table)
- [x] **Phase 2**: Backend helper functions (create, find, refresh, move)
- [x] **Phase 3**: API endpoints (`/pull-albums`, `/albums/{id}`)
- [x] **Phase 4**: Configuration (STAGING_REFRESH_DAYS)
- [x] **Phase 5**: Update request submission flow (use staging)
- [x] **Phase 6**: Frontend UI + Polling ("Pull Albums" button, album dropdown, polling)
- [x] **Impact**: Solves "wrong artist" and "album not found" problems
- [x] **Status**: Stage 3 complete - all 6 phases implemented and tested

**Key Features**:
- Two-phase commit (validate → pull → commit)
- Admin staging area (no user clutter)
- Staging reuse across users (performance)
- Auto-refresh stale artists (7-day threshold)
- Move to user space on commit

---

### Tier 2: Quick Wins ✅ COMPLETE (Stage 4)

#### 2. Trigger search when flipping album to monitored ⚡ HIGH IMPACT
- [x] After setting album monitored=true, trigger Lidarr album search
- [x] Use Lidarr API command endpoint: `POST /command {"name":"AlbumSearch","albumIds":[...]}`
- [x] Ensures download starts immediately instead of waiting for RSS sync
- [x] **Impact**: Downloads start instantly, better user experience
- [x] **Effort**: 30 min (modify `set_album_monitored()` function)

#### 3. Improve "already monitored" message ⚡ MEDIUM IMPACT
- [x] Change message based on Lidarr album status:
  - If downloading/no tracks: "is already requested"
  - If has tracks: "is already available"
- [x] Check album statistics in Lidarr response
- [x] **Impact**: Clearer user feedback
- [x] **Effort**: 30 min (modify message logic in existing album flow)

#### 4. Show version number in UI banner 🎯 LOW IMPACT
- [x] Add version display to page header/banner
- [x] Read from app.py or environment variable
- [x] **Impact**: Better visibility of deployed version
- [x] **Effort**: 20 min (template + CSS change)

**Stage 4 Complete**: Tasks 2-4 (1.5 hours total)

---

### Tier 3: Lower Priority Features

#### 5. Add Fuzzy Search for MusicBrainz Input 🎯
- [ ] Normalize/clean text input before MusicBrainz API calls
- [ ] Resolve user input to valid MB search strings
- [ ] Handle common typos and variations
- [ ] **Impact**: Medium (helps with search accuracy)
- [ ] **Effort**: 1-2 hours

#### 6. Handle partial album downloads 🎯
- [ ] Detect when album has incomplete tracks (some missing)
- [ ] Display per-track status or "partial download" indicator
- [ ] Consider: flip monitor bit on individual tracks?
- [ ] Balance: informative but not overly complex UI
- [ ] **Impact**: Medium (edge case handling)
- [ ] **Effort**: 2-3 hours (track-level API queries, UI design)

---

### Tier 4: Strategic/Long-term

#### 6. Build Local MusicBrainz Cache 🏗️ STRATEGIC
- [ ] Design database schema for MB data cache
- [ ] Store validated artist/album data from MB API
- [ ] Check cache before hitting MB web API
- [ ] Reduces API rate and improves response time
- [ ] **Impact**: High (performance, API rate limiting)
- [ ] **Effort**: 3-4 hours (schema, migration, caching logic)

#### 7. Debounce Search UX with Local Cache 🏗️ STRATEGIC
- [ ] Bounce live text entry against local cache only
- [ ] Add "Search MusicBrainz" button for web API hits
- [ ] Improves UX and lowers MB API hit rate
- [ ] **Dependencies**: Requires task #6 (local cache)
- [ ] **Impact**: Medium (UX refinement)
- [ ] **Effort**: 2 hours

---

### Superseded/Merged

~~**Old Task: Add Album Dropdown After Artist Validation**~~ → Merged into Task #1 (Artist Staging Workflow)
~~**Old Task: Smart album list workflow (Lidarr-first)**~~ → Implemented as Task #1 (Artist Staging Workflow)

---

## Backlog

See `docs/ALL-PROPOSED-FEATURES.md` for 47 ranked feature ideas.

When user requests a feature, move it here as a task.

---

## Completed (v0.6.0 - Stage 1)

### Quick Wins
- [x] Remove "Check Plex, Jellyfin, or Navidrome to listen now." message
- [x] Fix unmonitored album handling (flip to monitored instead of "already exists")

### Bug Fixes
- [x] Fix Frank Sinatra search flicker (race condition with stale results)
- [x] Improve Taylor Swift album search (fallback generic search)

---

## Completed (Previous Versions)

- [x] Fuzzy autocomplete for artist search
- [x] Fuzzy autocomplete for album search
- [x] Fix Lidarr API endpoint paths bug
- [x] Add 11 automated tests
- [x] Consolidate documentation (13 docs archived)
