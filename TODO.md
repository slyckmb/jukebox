# Jukebox TODO

**Current Sprint**: Search & UX Improvements (v0.6.0)

---

## Active Tasks (Re-ranked by Impact & Effort)

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
