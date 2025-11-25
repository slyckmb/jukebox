# Jukebox TODO

**Current Sprint**: Search & UX Improvements (v0.6.0)

---

## Active Tasks (Prioritized: Low Effort → High Reward)

### 1. Add Album Dropdown After Artist Validation 🎯
- [ ] After artist name validated, populate album dropdown
- [ ] New UI component for album selection
- [ ] Improves UX flow for requests

### 2. Add Fuzzy Search for MusicBrainz Input 🎯
- [ ] Normalize/clean text input before MusicBrainz API calls
- [ ] Resolve user input to valid MB search strings
- [ ] Handle common typos and variations

### 3. Build Local MusicBrainz Cache 🏗️ STRATEGIC
- [ ] Design database schema for MB data cache
- [ ] Store validated artist/album data from MB API
- [ ] Check cache before hitting MB web API
- [ ] Reduces API rate and improves response time

### 4. Debounce Search UX with Local Cache 🏗️ STRATEGIC
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
