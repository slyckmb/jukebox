# Jukebox Roadmap

**Version**: 0.5.0 → 0.6.0
**Status**: Search & UX Improvements Sprint

---

## What's Done (v0.5.0)

- ✅ Complete user journey (request → progress → listen now)
- ✅ Fuzzy autocomplete (80% fewer failed requests)
- ✅ Download progress tracking with Lidarr sync
- ✅ Listen Now buttons (Plex/Jellyfin/Navidrome)
- ✅ Duplicate detection & error handling
- ✅ Mobile-first responsive UI
- ✅ Extracted to standalone repo with clean git history
- ✅ Database restored from backup after migration

---

## Current Sprint (v0.6.0): Search & UX Improvements

**Focus**: Fix search bugs, improve MusicBrainz integration, better UX

**Quick Wins** (⚡ 1-2 hours total):
1. Remove "Check Plex, Jellyfin..." message
2. Fix unmonitored album handling (flip to monitored instead of "already exists")

**Bug Fixes** (🐛 2-3 hours):
3. Frank Sinatra search flicker (results appear then disappear)
4. Taylor Swift album search (top album not found)

**Features** (🎯 4-6 hours):
5. Album dropdown after artist validation
6. Fuzzy search for MusicBrainz input normalization

**Strategic** (🏗️ 8-12 hours):
7. Build local MusicBrainz cache (reduce API hits)
8. Debounce search UX with local cache + "Search MB" button

**Result**: Reliable search, better UX, lower MusicBrainz API usage

---

## Future Ideas

See `ALL-PROPOSED-FEATURES.md` for 47 ranked feature ideas.

Don't implement these unless explicitly needed:
- PWA features
- Push notifications
- Analytics dashboard
- Background workers
- Multi-library support

---

## For Agents

**What to read**:
- `README.md` - Overview and architecture
- `TODO.md` - Current tasks (TASKS ONLY, not guidance!)
- `ALL-PROPOSED-FEATURES.md` - Feature ideas if user requests them

**What NOT to do**:
- ❌ Don't create new planning docs
- ❌ Don't create completion/status docs
- ❌ Don't create handoff/session docs
- ❌ Update TODO.md with tasks, not this file

**Simple rule**: If user wants a feature, check ALL-PROPOSED-FEATURES.md first, then implement it. Don't document the journey.
