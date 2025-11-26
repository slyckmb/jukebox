# Jukebox TODO

**Current Version**: v0.6.10
**Last Updated**: 2025-11-26
**Status**: Production-ready, housekeeping complete

---

## 📋 Active Development Queue

Work in priority order from top to bottom. Mark items complete [x] as you finish them.

### 🚨 P0: Critical - Fix Immediately

#### BUG v0.6.10-1: Stale Album ID in Database (Request 23, Album 2131)
- [ ] **Issue**: Jukebox trying to fetch non-existent album 2131 for request 23
- [ ] **Evidence**: Repeated "Could not fetch album 2131" warnings + Lidarr ModelNotFoundException
- [ ] **Impact**: Log noise, incorrect status display, user confusion
- [ ] **Priority**: P0 - Data integrity + user experience
- [ ] **Solution Options**:
  1. Add cleanup script to detect and mark orphaned requests as "failed" with error message
  2. Enhance sync_request_status() to detect 404 errors and update status
  3. Add admin page to view/clean stale requests
- [ ] **Effort**: 2-3 hours (script + error handling + testing)
- [ ] **Location**: app.py:303-464 (sync_request_status)

---

### 🔥 P1: High Priority - Next Sprint

#### FEATURE: User Onboarding Process (Prevents BUG v0.6.10-3)
- [ ] **Purpose**: Automate root folder setup when creating new users
- [ ] **Problem**: Missing lidarr_admin root folder caused staging workflow failures
- [ ] **Solution**: When admin creates user → auto-create `/data/media/music/lidarr_<username>` + add to Lidarr via API
- [ ] **Benefits**: Prevents critical bugs, reduces manual admin work, ensures consistency
- [ ] **Effort**: 3-4 hours (Lidarr API research, implementation, error handling)
- [ ] **Priority**: P1 - Prevents recurrence of critical workflow bugs
- [ ] **API**: Check `/api/v1/rootfolder` endpoint

#### BUG v0.6.10-2: Python datetime.utcnow() Deprecation Warnings
- [ ] **Issue**: 7+ locations using deprecated datetime.utcnow()
- [ ] **Impact**: Will break in future Python versions, log clutter
- [ ] **Solution**: Replace all `datetime.utcnow()` with `datetime.now(datetime.UTC)`
- [ ] **Locations**: app.py:388, 461, 736, 1167, 1168, 1286, 1962
- [ ] **Effort**: 15-30 minutes (find/replace + testing)
- [ ] **Priority**: P1 - Technical debt, easy win

#### FEATURE: "Ready to Listen!" as Direct Album Link
- [ ] **Request**: Make "Ready to Listen!" header clickable to open album on Navidrome
- [ ] **Current**: Text header with separate service buttons
- [ ] **Impact**: HIGH - Faster access to music, fewer clicks
- [ ] **Effort**: 30 minutes (update template, add album search link)
- [ ] **Location**: app/templates/components/request_card.html
- [ ] **Priority**: P1 - Quick win, user requested

---

### 📋 P2: Medium Priority - Planned Work

#### Partial Album Download Visibility
- [ ] **Question**: Does v0.6.9+ show "11 of 14 tracks (79%)" for partial downloads?
- [ ] **Test**: Partially downloaded album handling
- [ ] **Enhancement**: Add quality/source info if needed
- [ ] **Effort**: 2-3 hours (investigation + potential UI changes)

#### Real-Time Download Status from qBit/SABnzbd
- [ ] **Goal**: Show download progress, speed, ETA while downloading
- [ ] **APIs**: Lidarr queue, qBittorrent WebUI, SABnzbd
- [ ] **Data**: Progress %, speed, ETA, indexer, quality
- [ ] **Effort**: 4-6 hours (API research + implementation + UI)
- [ ] **Risk**: Medium (multiple API integrations)

#### Add Cloudflared to System Log Review
- [ ] **Purpose**: Monitor tunnel health, connectivity issues, DNS failures
- [ ] **Tasks**:
  - Add cloudflared to AGENT-HANDOFF.md log review section
  - Add to STAGE-TEST-PLAN.md systemic log review command
  - Document what to look for (tunnel status, errors, restarts)
- [ ] **Effort**: 30 minutes
- [ ] **Priority**: P2 - Monitoring enhancement

#### API Health Check Button
- [ ] **Use Case**: Ping MusicBrainz and Lidarr to verify connections
- [ ] **Location**: Requests page or admin page
- [ ] **Effort**: 1-2 hours (endpoint + UI button)

#### Media Server Buttons Testing & Polish
- [ ] **Status**: Already implemented, needs testing
- [ ] **Test**: Verify links work for completed albums
- [ ] **Investigate**: Plex direct link options (plex.bjy.com subdomain?)
- [ ] **Verify**: Jellyfin search works with jellyfin.bikejeepyoga.com
- [ ] **Effort**: 1 hour (testing + optional Plex subdomain)

---

### 🧹 P3: Low Priority - Housekeeping & Nice-to-Haves

#### Archive Cloudflared Docs and Tools
- [ ] **Request**: Clean up outdated cloudflared documentation and binaries
- [ ] **Tasks**:
  - Archive docs to `cloudflared/docs/`
  - Archive binaries to `cloudflared/bin/`
  - Update pointers/symlinks
  - Document archive structure
- [ ] **Effort**: 1 hour
- [ ] **Priority**: P3 - Housekeeping

#### BUG #1: Artist Search Requires Full Exact Name
- [ ] **Issue**: Autocomplete doesn't show results until full name typed
- [ ] **Expected**: Fuzzy search for partial names like "zach" or "bryan"
- [ ] **Impact**: MEDIUM - Reduces discoverability
- [ ] **Root Cause**: MusicBrainz API limitation (not our code)
- [ ] **Note**: May require local MB cache (future feature)
- [ ] **Status**: Known limitation, documented

---

## 🔍 Monitoring & Investigation

### BUG v0.6.10-3: Lidarr Root Folder Path Error → POTENTIALLY FIXED
- [x] **Issue**: New artist (Radiohead) added with invalid root path
- [x] **Root Cause**: `/data/media/music/lidarr_admin` folder didn't exist + not in Lidarr config
- [x] **Fix Applied** (2025-11-26):
  - Created folder on disk
  - Added as root folder in Lidarr Media Management
- [ ] **Monitoring**: Watch for similar errors after fix
- [ ] **Testing**: Request new artist via staging, verify Lidarr scans files
- [ ] **Follow-up**: If confirmed fixed, mark as resolved

### ISSUE v0.6.10-4: Plex Server Frequent Crashes (External)
- [ ] **Issue**: Plex crashing repeatedly with dump files
- [ ] **Evidence**: Multiple crash dumps in logs
- [ ] **Impact**: Users can't stream during crashes
- [ ] **Priority**: P0 for user, but external to Jukebox
- [ ] **Version**: 1.43.0.10346-fc911a729
- [ ] **Action**: Document for user, consider downgrade/update
- [ ] **Note**: Does NOT block Jukebox development

---

## 🚀 Future / Strategic

### Build Local MusicBrainz Cache
- [ ] Design database schema for MB data cache
- [ ] Store validated artist/album data from MB API
- [ ] Check cache before hitting MB web API
- [ ] **Impact**: High (performance, API rate limiting)
- [ ] **Effort**: 3-4 hours (schema, migration, caching logic)
- [ ] **Dependency**: Required for fuzzy search improvement

### Debounce Search UX with Local Cache
- [ ] Bounce live text entry against local cache only
- [ ] Add "Search MusicBrainz" button for web API hits
- [ ] **Dependency**: Requires local MB cache
- [ ] **Impact**: Medium (UX refinement)
- [ ] **Effort**: 2 hours

---

## ✅ Recently Completed

### v0.6.10 - Stage 2 UX Polish (2025-11-26)
All features complete and deployed:
1. ✅ Better status badge text ("SEARCHING", "AVAILABLE")
2. ✅ Status subtext (helpful descriptions)
3. ✅ Album monitoring badge (👁️ Monitored / ⚠️ Not Monitored)
4. ✅ Hide failed requests toggle (localStorage)
5. ✅ Delete request button (soft delete)
6. ✅ Status filter pills (with counts)

### v0.6.9 - Album-Specific Tracking & Bug Fixes (2025-11-26)
1. ✅ Phase 1: Album-specific status tracking (migration 004)
2. ✅ Phase 2: Defensive monitoring verification
3. ✅ Phase 3: Staging workflow safeguards
4. ✅ Enhanced logging ([STAGING], [UNMONITOR] prefixes)

### v0.6.8 Field Test & Bug Fixes (2025-11-25)
1. ✅ BUG #6: Artist monitoring after staging move
2. ✅ BUG #7: All albums monitored instead of selected
3. ✅ Bug 0.6.4-1: Deleted artist cache cleanup
4. ✅ Bug 0.6.4-2: Artist name collision (multiple "NF")
5. ✅ Bug 0.6.5-1/0.6.6-1: Multiple albums monitoring reset

### v0.6.0-v0.6.3 - Search & UX Sprint
1. ✅ Stage 3: Artist staging workflow (all 6 phases)
2. ✅ Stage 4: Quick wins (trigger search, status messages, version display)
3. ✅ Bug fixes: Pull Albums, search flicker, album search fallback

---

## 📚 Reference

**Documentation**:
- AGENT-HANDOFF.md - Current status, log locations, how-tos
- PLAN-v0.6.9.md - Detailed v0.6.9 implementation plan
- STAGE-TEST-PLAN.md - Testing workflow for each stage
- HOUSEKEEPING-PLAN.md - Project cleanup procedures
- docs/ALL-PROPOSED-FEATURES.md - Full feature wishlist (archived)
- docs/archive/ - Historical plans and docs

**Key Files**:
- app/app.py - Main Flask application
- app/templates/components/request_card.html - Request card UI
- db/migrations/ - Database schema changes
- utils/debug-scripts/ - Investigation/debugging tools

**Version History**:
- v0.6.0: Stage 3 & 4 (staging workflow, quick wins)
- v0.6.4: Critical staging workflow fixes
- v0.6.5: Edge case fixes (deleted artist, name collision)
- v0.6.6: Multiple album monitoring fix
- v0.6.7-v0.6.8: Enhanced logging and field testing
- v0.6.9: Album-specific tracking, defensive monitoring (2025-11-26)
- v0.6.10: Stage 2 UX polish (2025-11-26)

---

**Work Philosophy**: Start from P0 and work down. Small commits > big commits. Document as you go. Test early and often.
