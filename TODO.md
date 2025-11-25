# Jukebox TODO

**Current Sprint**: Search & UX Improvements (v0.6.0)

---

## Active Tasks (Prioritized: Low Effort → High Reward)

### 1. Improve "already monitored" message ⚡ QUICK WIN
- [ ] Change message based on Lidarr album status:
  - If downloading/no tracks: "is already requested"
  - If has tracks: "is already available"
- [ ] Gives user clearer status information upfront
- [ ] Check album statistics in Lidarr response

### 2. Show version number in UI banner 🎯
- [ ] Add version display to page header/banner
- [ ] Read from app.py or environment variable
- [ ] Quick visual indicator of deployed version

### 3. Add Album Dropdown After Artist Validation 🎯
- [ ] After artist name validated, populate album dropdown
- [ ] New UI component for album selection
- [ ] Improves UX flow for requests

### 4. Add Fuzzy Search for MusicBrainz Input 🎯
- [ ] Normalize/clean text input before MusicBrainz API calls
- [ ] Resolve user input to valid MB search strings
- [ ] Handle common typos and variations

### 5. Smart album list workflow 🏗️ STRATEGIC
- [ ] Use MusicBrainz ONLY to validate artist and get MB artist ID
- [ ] If artist exists in Lidarr: query Lidarr API for album list (faster, more accurate)
- [ ] If artist NOT in Lidarr: add artist via API, wait for Lidarr to populate albums
  - Show "Searching for albums..." loading state
  - Poll Lidarr until albums are populated
  - Then show album dropdown
- [ ] Better UX for new vs existing artists

### 6. Handle partial album downloads 🎯
- [ ] Detect when album has incomplete tracks (some missing)
- [ ] Display per-track status or "partial download" indicator
- [ ] Consider: flip monitor bit on individual tracks?
- [ ] Balance: informative but not overly complex UI
- [ ] May need track-level API queries to Lidarr

### 7. Build Local MusicBrainz Cache 🏗️ STRATEGIC
- [ ] Design database schema for MB data cache
- [ ] Store validated artist/album data from MB API
- [ ] Check cache before hitting MB web API
- [ ] Reduces API rate and improves response time

### 8. Debounce Search UX with Local Cache 🏗️ STRATEGIC
- [ ] Bounce live text entry against local cache only
- [ ] Add "Search MusicBrainz" button for web API hits
- [ ] Improves UX and lowers MB API hit rate
- [ ] Depends on #7 (local cache)

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
