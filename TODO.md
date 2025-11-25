# Jukebox TODO

**Current Sprint**: Search & UX Improvements (v0.6.0)

---

## Active Tasks (Re-ranked by Impact & Effort)

### Tier 1: Quick Wins (Stage 2 - Next!)

#### 1. Trigger search when flipping album to monitored ⚡ HIGH IMPACT
- [ ] After setting album monitored=true, trigger Lidarr album search
- [ ] Use Lidarr API command endpoint: `POST /command {"name":"AlbumSearch","albumIds":[...]}`
- [ ] Ensures download starts immediately instead of waiting for RSS sync
- [ ] **Impact**: Downloads start instantly, better user experience
- [ ] **Effort**: 30 min (modify `set_album_monitored()` function)

#### 2. Improve "already monitored" message ⚡ MEDIUM IMPACT
- [ ] Change message based on Lidarr album status:
  - If downloading/no tracks: "is already requested"
  - If has tracks: "is already available"
- [ ] Check album statistics in Lidarr response
- [ ] **Impact**: Clearer user feedback
- [ ] **Effort**: 30 min (modify message logic in existing album flow)

#### 3. Show version number in UI banner 🎯 LOW IMPACT
- [ ] Add version display to page header/banner
- [ ] Read from app.py or environment variable
- [ ] **Impact**: Better visibility of deployed version
- [ ] **Effort**: 20 min (template + CSS change)

**→ Proposed Stage 2: Tasks 1-3 (1.5 hours total)**

---

### Tier 2: Medium Features (Stage 3)

#### 4. Smart album list workflow (Lidarr-first) 🏗️ HIGH IMPACT
- [ ] Use MusicBrainz ONLY to validate artist and get MB artist ID
- [ ] If artist EXISTS in Lidarr: query Lidarr API for album list (faster, more accurate)
- [ ] If artist NOT in Lidarr: add artist via API, wait for Lidarr to populate albums
  - Show "Searching for albums..." loading state
  - Poll Lidarr until albums are populated
  - Then show album dropdown
- [ ] **Impact**: Solves "Taylor Swift album not found" problem
- [ ] **Effort**: 2-3 hours (backend + frontend changes, polling logic)
- [ ] **Note**: This essentially implements the album dropdown (old task #3) with smarter logic

**→ Proposed Stage 3: Task 4 (2-3 hours)**

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

#### 7. Build Local MusicBrainz Cache 🏗️ STRATEGIC
- [ ] Design database schema for MB data cache
- [ ] Store validated artist/album data from MB API
- [ ] Check cache before hitting MB web API
- [ ] Reduces API rate and improves response time
- [ ] **Impact**: High (performance, API rate limiting)
- [ ] **Effort**: 3-4 hours (schema, migration, caching logic)

#### 8. Debounce Search UX with Local Cache 🏗️ STRATEGIC
- [ ] Bounce live text entry against local cache only
- [ ] Add "Search MusicBrainz" button for web API hits
- [ ] Improves UX and lowers MB API hit rate
- [ ] **Dependencies**: Requires task #7 (local cache)
- [ ] **Impact**: Medium (UX refinement)
- [ ] **Effort**: 2 hours

---

### Removed (Superseded)

~~**3. Add Album Dropdown After Artist Validation**~~ → Superseded by task #4 (Smart album list workflow)

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
