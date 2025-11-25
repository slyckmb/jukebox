# Stage 2 Plan - Quick Wins Round 2

**Target Duration**: 1.5-2 hours (well within 5-hour context window)
**Commit Goal**: Small, focused improvements to existing album workflow
**Status**: Ready to start

---

## Tasks (3 Quick Wins)

### Task 1: Trigger search when flipping album to monitored ⚡
**Priority**: HIGH
**Effort**: 30 min
**Impact**: Downloads start instantly instead of waiting for RSS sync

**Implementation**:
1. Modify `set_album_monitored()` function in `app/app.py` (line ~503)
2. After successful PUT to update album monitoring, add API call:
   ```python
   POST {LIDARR_URL}/command
   {
     "name": "AlbumSearch",
     "albumIds": [album_id]
   }
   ```
3. Handle response (202 Accepted = success)
4. Log command submission for debugging

**Files**: `app/app.py` (~20 lines)

---

### Task 2: Improve "already monitored" message ⚡
**Priority**: MEDIUM
**Effort**: 30 min
**Impact**: Clearer user feedback about album status

**Implementation**:
1. Modify existing album check logic in `new_request()` route (app.py:790-831)
2. When album is already monitored (line ~821), check album statistics:
   ```python
   album_stats = album_data.get("statistics", {})
   track_count = album_stats.get("trackFileCount", 0)
   ```
3. Change message based on track count:
   - `track_count == 0`: "is already requested and downloading"
   - `track_count > 0`: "is already available in your library"

**Files**: `app/app.py` (~10 lines)

---

### Task 3: Show version number in UI banner 🎯
**Priority**: LOW
**Effort**: 20 min
**Impact**: Better visibility of deployed version

**Implementation**:
1. Add version constant to `app/app.py`:
   ```python
   APP_VERSION = "0.6.0-dev"
   ```
2. Pass to base template context in `@app.context_processor`:
   ```python
   @app.context_processor
   def inject_globals():
       return {"app_version": APP_VERSION}
   ```
3. Update `app/templates/base.html` to show version in footer or header:
   ```html
   <span class="version">v{{ app_version }}</span>
   ```
4. Add CSS styling for version display

**Files**:
- `app/app.py` (~10 lines)
- `app/templates/base.html` (~5 lines)
- CSS (inline or in stylesheet)

---

## Testing Plan

### Task 1: Album Search Trigger
- [ ] Request album from existing artist (unmonitored)
- [ ] Verify album flips to monitored
- [ ] Check logs for command submission: "Triggered AlbumSearch for album 123"
- [ ] Verify download starts within seconds (check Lidarr queue)

### Task 2: Status Messages
- [ ] Request unmonitored album (no tracks): see "is already requested"
- [ ] Request monitored album with tracks: see "is already available"
- [ ] Request monitored album without tracks: see "is already requested"

### Task 3: Version Display
- [ ] Check version appears in UI (footer or header)
- [ ] Verify version matches `APP_VERSION` constant
- [ ] Check styling looks good on mobile

### Regression
- [ ] Artist search still works
- [ ] New artist requests still work
- [ ] Existing functionality not broken

---

## Implementation Order

1. **Task 3 first** (simplest, no risk)
   - Quick win to build momentum
   - No dependencies, can't break anything

2. **Task 2 second** (message improvement)
   - Low risk, just text changes
   - Works with existing data

3. **Task 1 last** (search trigger)
   - Highest impact
   - New API call, needs careful testing
   - If time runs short, can defer to Stage 3

---

## Success Criteria

✅ All 3 tasks complete and tested
✅ Container builds and runs
✅ No errors in logs
✅ Manual testing passes
✅ Documentation updated (TODO.md, HANDOFF.md)
✅ Git commit created and pushed

---

## Rollback Plan

If Task 1 (search trigger) causes issues:
- Comment out the command API call
- Keep the monitoring flip working
- Document issue in TODO.md
- Still ship Tasks 2 & 3

---

## Next Stage Preview

**Stage 3** will tackle Task 4 (Smart album list workflow):
- Bigger feature (2-3 hours)
- Solves "Taylor Swift album not found" problem
- Lidarr-first approach for existing artists
- Better UX with loading states
- May split into Stage 3a and 3b if complex
