# Jukebox TODO

**Current Version**: v0.6.10
**Previous Version**: v0.6.9
**Last Updated**: 2025-11-26

---

## ✅ v0.6.10 - Stage 2 UX Polish DEPLOYED

**Status**: v0.6.10 deployed - All Stage 2 features complete
**Deployment Date**: 2025-11-26

**Completed Features**:
1. ✅ Better status badge text ("SEARCHING" instead of "SUBMITTED", "AVAILABLE" instead of "EXISTING")
2. ✅ Status subtext (helpful descriptions under badges)
3. ✅ Album monitoring badge (shows 👁️ Monitored / ⚠️ Not Monitored)
4. ✅ Hide failed requests toggle (with localStorage persistence)
5. ✅ Delete request button (soft delete with confirmation)
6. ✅ Status filter pills (All, Searching, Downloading, Completed, Available, Failed with counts)

---

## ✅ v0.6.9 - DEPLOYED AND TESTED

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

### 🔍 NEW: Systemic Issues Found in Log Review (2025-11-26)

**Log Review Conducted**: Full system log review across Jukebox → Lidarr → Prowlarr → qBit → Navidrome/Jellyfin/Plex

#### BUG v0.6.10-1: Stale Album ID in Database (Request 23, Album 2131) 🚨 P1
- [ ] **Issue**: Jukebox repeatedly tries to fetch album 2131 for request 23, but Lidarr says it doesn't exist
- [ ] **Evidence**:
  - Jukebox logs: `[2025-11-26 15:58:11,334] WARNING in app: Could not fetch album 2131 for request 23`
  - Lidarr logs: `[Warn] LidarrErrorPipeline: Album with ID 2131 does not exist` with full ModelNotFoundException trace
- [ ] **Impact**: HIGH - Creates log noise, request shows wrong status, user confusion
- [ ] **Priority**: P1 - Data cleanup needed
- [ ] **Root Cause**: Album deleted in Lidarr but request still references old album ID
- [ ] **Solution Options**:
  1. Add cleanup script to detect and mark orphaned requests as "failed" with helpful error message
  2. Enhance sync_request_status() to detect 404 errors and update request status accordingly
  3. Add admin page to view/clean stale requests
- [ ] **Location**: app.py:303-464 (sync_request_status error handling)
- [ ] **Testing**: Query DB for other stale album IDs, verify cleanup doesn't affect valid requests

#### BUG v0.6.10-2: Python datetime.utcnow() Deprecation Warnings 🔧 P2
- [ ] **Issue**: Multiple deprecation warnings throughout Jukebox code
- [ ] **Evidence**: `DeprecationWarning: datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects`
- [ ] **Locations**:
  - app.py:461 (sync status)
  - app.py:388 (another sync call)
  - app.py:1962 (delete request)
  - app.py:736, 1167, 1168, 1286 (various locations)
- [ ] **Impact**: MEDIUM - Will break in future Python versions, log clutter
- [ ] **Priority**: P2 - Technical debt, not urgent
- [ ] **Solution**: Replace all `datetime.utcnow()` with `datetime.now(datetime.UTC)`
- [ ] **Effort**: 15-30 minutes (find/replace + testing)

#### BUG v0.6.10-3: Lidarr Root Folder Path Error for New Artists 🚨 P1 → POTENTIALLY FIXED
- [x] **Issue**: New artist (Radiohead) added with invalid root path - Lidarr can't scan it
- [x] **Evidence**: `[Error] DiskScanService: Not scanning /data/media/music/lidarr_admin/Radiohead-a74b1b7f, it's not a subdirectory of a defined root folder`
- [x] **Impact**: CRITICAL - Artist added but files won't be imported/scanned
- [x] **Priority**: P1 - Blocks workflow for staging-created artists
- [x] **Root Cause**: `/data/media/music/lidarr_admin` folder didn't exist on disk AND wasn't configured in Lidarr Media Management
- [x] **Fix Applied** (2025-11-26):
  - Created `/data/media/music/lidarr_admin` folder on disk
  - Added as root folder in Lidarr Media Management settings
- [ ] **Monitoring**: Watch for similar errors in logs after fix (need to test with new artist request)
- [ ] **Testing**: Request new artist via staging workflow, verify Lidarr scans files after download
- [ ] **Follow-up**: If confirmed fixed, mark as resolved and close issue

#### ISSUE v0.6.10-4: Plex Server Frequent Crashes 🚨 P0 (External)
- [ ] **Issue**: Plex Media Server crashing repeatedly with dump files
- [ ] **Evidence**: Multiple `****** PLEX MEDIA SERVER CRASHED, CRASH REPORT WRITTEN` in logs
- [ ] **Impact**: CRITICAL - Users can't stream via Plex during crashes
- [ ] **Priority**: P0 - Service availability issue
- [ ] **Note**: This is a Plex issue, not Jukebox, but affects user experience
- [ ] **Action Items**:
  - Document for user awareness
  - Check Plex version (1.43.0.10346-fc911a729)
  - Consider downgrade or update
  - Review crash dumps if accessible
  - Does NOT block Jukebox development

---

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

#### NEW: User Onboarding Process for Jukebox 🎯 (2025-11-26)
- [ ] **Request**: Automate user setup process when new users are created
- [ ] **Problem**: Currently manual - admin must create root folder on disk AND add to Lidarr Media Management
- [ ] **Root Cause of BUG v0.6.10-3**: Missing lidarr_admin root folder caused staging workflow failures
- [ ] **Proposed Solution**: Create onboarding workflow that:
  1. When admin creates new user in Jukebox, automatically create `/data/media/music/lidarr_<username>` folder on disk
  2. Automatically add folder to Lidarr as root folder via API
  3. Verify folder exists and is recognized by Lidarr before completing user creation
  4. Show success/error messages to admin
- [ ] **Benefits**:
  - Prevents BUG v0.6.10-3 from recurring for new users
  - Reduces admin manual work
  - Ensures consistency between Jukebox, filesystem, and Lidarr
- [ ] **Implementation Considerations**:
  - Need Lidarr API endpoint to add root folder (check `/api/v1/rootfolder`)
  - Need proper filesystem permissions for folder creation
  - Handle errors gracefully (folder exists, API fails, etc.)
  - Consider: should this run for existing users retroactively?
- [ ] **Effort**: 3-4 hours (API research, implementation, testing, error handling)
- [ ] **Priority**: P1 - Prevents critical workflow bugs
- [ ] **Location**: app.py user management, new onboarding module

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

#### NEW: Add Cloudflared to System Log Review 🔍 (2025-11-26)
- [ ] **Request**: Include cloudflared container in systemic log analysis workflow
- [ ] **Purpose**: Monitor tunnel health, connectivity issues, DNS failures
- [ ] **Implementation**:
  - Add cloudflared to service list in AGENT-HANDOFF.md log review section
  - Add to STAGE-TEST-PLAN.md systemic log review command
  - Document what to look for in cloudflared logs (tunnel status, errors, restarts)
- [ ] **Effort**: 30 minutes (documentation updates)
- [ ] **Priority**: P2 - Monitoring enhancement
- [ ] **Related**: Part of comprehensive workflow monitoring

#### NEW: Archive/Retire Cloudflared Docs and Tools 📦 (2025-11-26)
- [ ] **Request**: Clean up outdated cloudflared documentation and binaries
- [ ] **Action Items**:
  - Archive old cloudflared docs to `cloudflared/docs/` (if not already there)
  - Archive old cloudflared binaries to `cloudflared/bin/` (if not already there)
  - Update any pointers/symlinks to reference new locations
  - Document archive structure in README or index file
- [ ] **Effort**: 1 hour (organization + documentation)
- [ ] **Priority**: P3 - Housekeeping
- [ ] **Note**: Improves project organization, preserves historical tools

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
