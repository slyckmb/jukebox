# Jukebox TODO

**Current Version**: v0.6.8
**Next Version**: v0.6.9 (in planning)
**Last Updated**: 2025-11-26

---

## ✅ v0.6.9 - DEPLOYED AND READY FOR TESTING

**Status**: Stage 1 COMPLETE - Ready for field testing
**Plan Document**: See `PLAN-v0.6.9.md` for detailed analysis and implementation steps

**Quick Summary**:
- **Root Cause**: Status sync tracked ARTIST-WIDE stats instead of individual albums
- **Solution**: Added album-specific tracking (tracks, monitoring status) per request
- **Impact**: Fixes 3 critical bugs + foundation for Stage 2 UX features
- **Deployment**: v0.6.9 deployed 2025-11-26

**✅ STAGE 1: Critical Bug Fixes** (COMPLETE - 6 hours)
1. ✅ Phase 0: Root cause analysis
2. ✅ Phase 1: Album-specific status tracking
   - Database migration 004 applied
   - New columns: `album_total_tracks`, `album_downloaded_tracks`, `album_monitored`
   - Updated sync logic to query individual albums
   - Frontend shows per-album track counts
3. ✅ Phase 2: Fix album monitoring bugs
   - Defensive re-monitoring when albums become unmonitored
   - Enhanced unmonitor_all_albums() with verification step
4. ✅ Phase 3: Prevent unrequested downloads
   - Staging workflow safeguards
   - Enhanced logging throughout

**🛑 TESTING PHASE** - Field test v0.6.9 before Stage 2

**Next Steps**:
1. User tests v0.6.9 in production
2. Verify bugs are fixed (Caravan Palace cards show different track counts)
3. Check logs for defensive monitoring warnings
4. Gather feedback and identify any new issues
5. **Decision point**: Proceed to Stage 2 or iterate on fixes

**🎨 STAGE 2: Polish & UX** (PLANNED - 3.5-4.5 hours when ready)
- Phase 4: Enhanced logging (1-2 hrs)
- Phase 5: Quick-win UX improvements (2-2.5 hrs):
  - Better status badge text (fixes BUG #4)
  - Album monitoring badge
  - Delete request button
  - Hide failed requests toggle
  - Status subtext
  - Status filter pills

**Stage 2 will be scheduled after Stage 1 field testing is complete**

---

## Active Tasks

### Tier 1: Critical Bugs (P0) - Fix First! 🚨

#### BUG v0.6.8-1: Caravan Palace albums unmonitored after initial monitoring ✅ ROOT CAUSE FOUND
- [x] **Issue**: Albums that were monitored are now unmonitored in Lidarr
- [x] **Root Cause**: Status sync doesn't verify album monitoring status, only checks downloads
  - `sync_request_status()` queries artist statistics (all albums) not individual album
  - No monitoring verification → albums can become unmonitored without detection
  - Possible Lidarr auto-refresh or metadata update resetting monitored status
- [x] **Impact**: CRITICAL - Albums won't download if unmonitored
- [x] **Priority**: P0 - Data integrity issue
- [x] **Solution**: Phase 2 of v0.6.9 plan - Add monitoring verification + re-enable if disabled
- [x] **Location**: app.py:303-399 (sync_request_status)

#### BUG v0.6.8-2: Unrequested album auto-downloaded and marked completed ✅ ROOT CAUSE FOUND
- [x] **Issue**: Album `<|°_°|>` from Caravan Palace was NOT requested but shows as completed
- [x] **Root Cause**: Likely race condition in staging workflow
  - Lidarr metadata refresh auto-monitors some albums (depends on settings)
  - `unmonitor_all_albums()` called but may have timing issue or fail silently
  - Download starts before unmonitoring completes
- [x] **Impact**: CRITICAL - Monitoring/downloading wrong albums
- [x] **Priority**: P0 - Data integrity issue
- [x] **Solution**: Phase 3 of v0.6.9 plan - Better logging + verification in unmonitor workflow
- [x] **Location**: app.py:751-788 (unmonitor_all_albums), staging workflow

---

### Tier 2: High-Impact UX Issues (P1) - Fix Next

#### UX ISSUE: Download progress shows artist-wide stats instead of per-album ✅ SOLUTION DESIGNED
- [x] **Issue**: Request card shows "📥 4 of 5 albums (80%)" for ALL Caravan Palace requests
- [x] **Root Cause**: `sync_request_status()` stores artist-wide `total_albums` and `downloaded_albums`
  - All requests for same artist get same numbers (5 albums total, 4 downloaded)
  - Frontend displays these numbers without knowing which specific album
- [x] **Expected**: Each card should show status for THAT specific album only
  - "Caravan Palace - Panic" → "10/10 tracks" (100% for this album)
  - "Caravan Palace - Chronologic" → "0/12 tracks" (0% for this album)
- [x] **Impact**: HIGH - Users can't track individual album progress
- [x] **Priority**: P1 - Core UX issue
- [x] **Solution**: Phase 1 of v0.6.9 plan - Track `album_total_tracks` and `album_downloaded_tracks` per request
- [x] **Location**: app.py:303-399 (sync_request_status), database schema, frontend templates
- [x] **Effort**: 2-3 hours (migration + backend + frontend)

#### BUG #5: Lidarr status updates not syncing to request cards ✅ LIKELY FIXED in v0.6.9
- [x] **Issue**: Request card statuses don't update to reflect Lidarr download progress
- [x] **Root Cause**: Was showing artist-wide stats, not album-specific progress
- [x] **Solution**: v0.6.9 now queries individual albums and shows per-album track counts
- [x] **Status**: Fixed by v0.6.9 Phase 1 - needs field testing to confirm
- [x] **Testing**: Load requests page and verify cards show correct per-album progress
- [ ] **If still broken**: Investigate page load sync trigger timing
- [x] **Location**: app.py:303-464 (sync_request_status - now album-specific)
- [x] **Note**: This was the same root cause as the UX issue (artist-wide vs album-specific)

---

### 🎯 Stage 2: UX Polish (P1) - PLANNED

**Status**: Ready to implement after v0.6.9 field testing
**Total Effort**: 2-2.5 hours for all 6 improvements
**Priority**: All P1 - Quick wins that complement v0.6.9 changes

See PLAN-v0.6.9.md Phase 5 for detailed implementation specs.

#### 5A. Better Status Badge Text ⚡ (15 min)
- [ ] Change "SUBMITTED" → "SEARCHING"
- [ ] Change "EXISTING" → "AVAILABLE"
- [ ] Fixes BUG #4 with zero backend changes
- [ ] **Files**: status_badge.html

#### 5B. Album Monitoring Status Badge ⚡ (20 min)
- [ ] Add "👁️ Monitored" or "⚠️ Not Monitored" badge to active requests
- [ ] Makes monitoring status visible to users
- [ ] Uses new `album_monitored` field from v0.6.9
- [ ] **Files**: request_card.html

#### 5C. Delete Request Button ⚡ (30 min)
- [ ] Add trash icon to each card with soft delete
- [ ] Allows users to clean up old/failed requests
- [ ] From ALL-PROPOSED-FEATURES.md Tier 1 #2
- [ ] **Files**: app.py (DELETE endpoint), request_card.html, app.js

#### 5D. Hide Failed Requests Toggle ⚡ (20 min)
- [ ] Button to show/hide failed requests (localStorage)
- [ ] Declutters UI for users with many failures
- [ ] Pure frontend, no backend changes
- [ ] From ALL-PROPOSED-FEATURES.md Tier 1 #1
- [ ] **Files**: requests.html, app.js

#### 5E. Status Subtext ⚡ (10 min)
- [ ] Add helpful text under status badges
- [ ] "Lidarr is searching...", "Download in progress"
- [ ] Professional polish, reduces confusion
- [ ] **Files**: status_badge.html

#### 5F. Status Filter Pills (OPTIONAL) ⚡ (30 min)
- [ ] Filter buttons: [All] [Searching (3)] [Downloading (2)] [Completed (5)]
- [ ] Quick filtering with counts
- [ ] From ALL-PROPOSED-FEATURES.md Tier 1 #4
- [ ] **Files**: requests.html, app.js

---

### Tier 2: Quick Win Features (P1) - User Requested ⚡

#### "Ready to Listen!" as Direct Album Link 🎯
- [ ] **Request**: Make "Ready to Listen!" header clickable to open album on Navidrome
- [ ] **Current**: Text header with separate service buttons
- [ ] **Impact**: HIGH - Faster access to music, fewer clicks
- [ ] **Effort**: 30 minutes (update template, add album search link)
- [ ] **Location**: request_card.html

#### Media Server Buttons Testing & Polish 🎯
- [ ] **Status**: ✅ Already implemented! Just needs testing
- [ ] **Test**: Verify links work for completed albums
- [ ] **Investigate**: Plex direct link options (plex.bjy.com subdomain?)
- [ ] **Verify**: Jellyfin search works with jellyfin.bikejeepyoga.com
- [ ] **Effort**: 1 hour (testing + optional Plex subdomain)

---

### Tier 3: Investigation Tasks (P2) 🔍

#### Partial Album Download Visibility
- [ ] **Question**: Does v0.6.9 show "11 of 14 tracks (79%)" for partial downloads?
- [ ] **Test**: Partially downloaded album handling
- [ ] **Enhancement**: Add quality/source info if needed
- [ ] **Effort**: 2-3 hours (investigation + potential enhancement)

#### Real-Time Download Status from qBit/SABnzbd
- [ ] **Goal**: Show download progress, speed, ETA while downloading
- [ ] **APIs**: Lidarr queue, qBittorrent, SABnzbd
- [ ] **Data**: Progress %, speed, ETA, indexer, quality
- [ ] **Effort**: 4-6 hours (research + implementation + UI)
- [ ] **Risk**: Medium (multiple API integrations)

#### API Health Check Button
- [ ] **Use Case**: Ping MusicBrainz and Lidarr to verify connections
- [ ] **Location**: Requests page or admin page
- [ ] **Effort**: 1-2 hours (endpoint + UI button)

---

### Tier 4: Known Limitations (P3)

#### BUG #1: Artist search requires full exact name
- [ ] **Issue**: Autocomplete doesn't show results until full name is typed
- [ ] **Expected**: Fuzzy search should match partial names like "zach" or "bryan"
- [ ] **Impact**: MEDIUM - Reduces discoverability, frustrates users
- [ ] **Priority**: P3 - Known limitation
- [ ] **Root Cause**: MusicBrainz API limitation - not our code
- [ ] **Note**: May require local MB cache (Tier 4 feature)
- [ ] **Status**: v0.6.8 - Known limitation, documented

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
