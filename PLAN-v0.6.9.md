# Implementation Plan: v0.6.9 - Album-Specific Status & Bug Fixes

**Date**: 2025-11-26
**Current Version**: v0.6.8
**Target Version**: v0.6.9
**Focus**: Fix critical monitoring bugs + Improve UX with album-specific status

---

## Root Cause Analysis

### Bug v0.6.8-1: Albums Unmonitored After Initial Monitoring

**Current Evidence:**
- Database shows: All Caravan Palace requests have `lidarr_artist_id=157` but different `lidarr_album_id` values (2132, 2134, 2135)
- All show status `downloading` with `downloaded_albums=4, total_albums=5`
- User reports: Albums *were* monitored, but are now unmonitored

**Root Cause Hypothesis:**
The current `sync_request_status()` function (app.py:303-399) calculates status based on **ARTIST-WIDE** statistics:
```python
# Line 344-346: Gets ALL albums for the artist
statistics = artist_data.get("statistics", {})
total_albums = statistics.get("albumCount", 0)

# Line 349-363: Counts ALL downloaded albums for the artist
downloaded_count = 0
for album in albums:
    if track_file_count > 0:
        downloaded_count += 1
```

**The Problem:**
1. User requests album A from Caravan Palace → monitored=True
2. Status sync sees 0/5 albums downloaded for the ARTIST
3. User requests album B from same artist → monitored=True
4. Status sync sees 0/5 albums → **BUT** it's checking the entire artist's album collection
5. Something (possibly Lidarr's auto-refresh or metadata update) may be resetting monitored status

**Additional Issue:**
The staging workflow calls `unmonitor_all_albums()` (app.py:751) before moving the artist. If the artist is ALREADY moved (not in staging), but something triggers the staging logic again, it could unmonitor everything.

### Bug v0.6.8-2: Unrequested Album Downloaded

**Current Evidence:**
- User did NOT request album `<|°_°|>` from Caravan Palace
- Album showed up as completed

**Root Cause Hypothesis:**
1. When artist is added to staging via "Pull Albums", Lidarr does a metadata refresh
2. The metadata refresh might auto-monitor some albums (depending on Lidarr settings)
3. The workflow calls `unmonitor_all_albums()` to reset everything
4. But if there's a race condition or timing issue, Lidarr might have already started downloading before unmonitoring happens
5. Once download completes, it shows as "completed" even though user never requested it

**OR:**
The `unmonitor_all_albums()` function might not be working correctly - it loops through albums but may skip some or fail silently.

### UX Issue: Artist-Wide Progress

**Current Behavior:**
All Caravan Palace request cards show "📥 4 of 5 albums (80%)" because:
- Each request has `total_albums=5` (entire artist)
- Each request has `downloaded_albums=4` (entire artist)
- Frontend displays this as a progress bar

**Expected Behavior:**
Each card should show status for THAT SPECIFIC ALBUM ONLY:
- "Caravan Palace - Panic" → Show if "Panic" album is downloaded (not all 5 albums)
- "Caravan Palace - Chronologic" → Show if "Chronologic" album is downloaded

---

## Implementation Plan

### Phase 1: Album-Specific Status Tracking (P0 - Highest Priority)

**Goal**: Track and display status for individual albums, not entire artist

**Changes Required:**

1. **Database Schema Update** (Migration 004):
   ```sql
   -- Add new columns to requests table
   ALTER TABLE requests ADD COLUMN album_total_tracks INTEGER DEFAULT 0;
   ALTER TABLE requests ADD COLUMN album_downloaded_tracks INTEGER DEFAULT 0;
   ALTER TABLE requests ADD COLUMN album_monitored BOOLEAN DEFAULT NULL;

   -- Keep existing total_albums/downloaded_albums for reference but deprioritize in UI
   ```

2. **Update `sync_request_status()` Function** (app.py:303-399):
   - **Current**: Queries artist statistics (all albums)
   - **New**: Query the SPECIFIC album by `lidarr_album_id`
   - **Logic**:
     ```python
     # Get the specific album for this request
     album_url = f"{LIDARR_URL}/album/{req['lidarr_album_id']}"
     album_resp = requests.get(album_url, ...)
     album_data = album_resp.json()

     # Check THIS album's monitoring status
     is_monitored = album_data.get('monitored', False)

     # Get THIS album's track statistics
     album_stats = album_data.get('statistics', {})
     total_tracks = album_stats.get('trackCount', 0)
     downloaded_tracks = album_stats.get('trackFileCount', 0)

     # Determine status for THIS ALBUM ONLY
     if not is_monitored and downloaded_tracks == 0:
         new_status = "submitted"  # or "pending"
     elif is_monitored and downloaded_tracks == 0:
         new_status = "searching"
     elif downloaded_tracks > 0 and downloaded_tracks < total_tracks:
         new_status = "downloading"
     elif downloaded_tracks == total_tracks:
         new_status = "completed"
     ```

3. **Update Frontend Display** (templates/requests.html):
   - Change progress bar to show `album_downloaded_tracks / album_total_tracks`
   - Add badge showing album monitoring status
   - Keep artist-wide stats as secondary info (optional, in tooltip)

**Estimated Effort**: 2-3 hours
**Impact**: HIGH - Fixes UX issue and provides accurate per-album tracking

---

### Phase 2: Fix Album Monitoring Bugs (P0 - Critical)

**Goal**: Ensure albums stay monitored once set, and only requested albums are monitored

**Changes Required:**

1. **Add Defensive Monitoring Check** (After `set_album_monitored()`):
   ```python
   # After setting album monitored, verify it stuck
   success, err = set_album_monitored(album_id, monitored=True)

   if success:
       # Verify monitoring actually applied (defensive check)
       verify_url = f"{LIDARR_URL}/album/{album_id}"
       verify_resp = requests.get(verify_url, ...)
       verify_data = verify_resp.json()

       if not verify_data.get('monitored', False):
           app.logger.error(f"Album {album_id} monitoring verification FAILED - setting may not have stuck")
           # Retry once
           set_album_monitored(album_id, monitored=True)
   ```

2. **Improve `unmonitor_all_albums()` Error Handling**:
   - Add retry logic for failed PUT requests
   - Log each album's before/after monitoring status
   - Return list of albums that failed to unmonitor

3. **Add Periodic Monitoring Verification** (Optional - for robustness):
   - Every N minutes, check active requests (status=submitted/downloading)
   - Verify their albums are still monitored
   - Re-enable monitoring if it got disabled somehow
   - Log when this happens (helps identify root cause)

**Estimated Effort**: 2-3 hours
**Impact**: CRITICAL - Prevents albums from getting unmonitored

---

### Phase 3: Prevent Unrequested Album Downloads (P0 - Critical)

**Goal**: Ensure only requested albums are monitored/downloaded

**Changes Required:**

1. **Improve `unmonitor_all_albums()` Logging**:
   ```python
   # Before unmonitoring
   app.logger.info(f"BEFORE unmonitor: {len(albums)} albums")
   for album in albums:
       app.logger.info(f"  Album {album['id']} '{album['title']}': monitored={album.get('monitored')}")

   # After unmonitoring
   app.logger.info(f"AFTER unmonitor: verifying...")
   # Re-query and verify all are actually unmonitored
   ```

2. **Add Staging Workflow Safeguards**:
   - Log when staging artist is being used vs when creating new
   - Add explicit check: "Is artist still in staging?" before calling `unmonitor_all_albums()`
   - Current code removes from staging after move (line 1093-1098) - verify this is working

3. **Verify Album Search Trigger Safety**:
   - Review `trigger_album_search()` (app.py:560-585)
   - Ensure it only triggers for the SPECIFIC album, not "search for artist" (all albums)

**Estimated Effort**: 2 hours
**Impact**: CRITICAL - Prevents wasted bandwidth and unwanted downloads

---

## 🛑 STAGE BREAK: Test & Evaluate

**After Phase 3, STOP and test/evaluate before continuing.**

### Testing Checklist

1. **Database Migration Verification**:
   ```bash
   sqlite3 data/requests.db "PRAGMA table_info(requests);"
   # Verify new columns exist: album_total_tracks, album_downloaded_tracks, album_monitored
   ```

2. **Existing Caravan Palace Requests**:
   - Check database: Do they have album-specific data populated?
   - Check Lidarr: Are the requested albums still monitored?
   - Check UI: Does each card show different track counts?

3. **New Request Test**:
   - Request a new album from an artist not yet in Lidarr
   - Verify: Album gets monitored
   - Verify: Only that album is monitored (not all albums)
   - Verify: Card shows track count for that specific album

4. **Multiple Albums from Same Artist Test**:
   - Request album A from Artist X
   - Wait for monitoring to be set
   - Request album B from same Artist X
   - Verify: Both albums A and B remain monitored
   - Verify: Each card shows different track counts

5. **Status Sync Test**:
   - Wait for automatic status sync (or trigger manually)
   - Verify: Album monitoring status is checked and logged
   - Verify: If album becomes unmonitored, it gets re-enabled
   - Check logs for monitoring verification messages

### Evaluation Questions

- ✅ Are the critical bugs (v0.6.8-1 and v0.6.8-2) fixed?
- ✅ Do users see accurate per-album progress?
- ✅ Do albums stay monitored over time?
- ✅ Are only requested albums getting downloaded?
- ❓ Are there any new issues or regressions?
- ❓ Is the logging helpful for debugging?
- ❓ Should we proceed with Phase 4 & 5, or iterate on fixes?

**Decision Point**:
- If tests pass → Proceed to Phase 4 (logging) or Phase 5 (UX)
- If issues found → Fix and re-test before continuing
- Can deploy Phase 1-3 to production as v0.6.9-alpha for field testing

---

### Phase 4: Enhanced Logging & Monitoring (P1 - High)

**Goal**: Better visibility into what's happening with album monitoring

**Changes Required:**

1. **Add Album Monitoring State Change Logging**:
   - Log every time an album's monitored status changes
   - Include: request_id, album_id, album_title, old_state, new_state, trigger reason

2. **Add Status Sync Detailed Logging**:
   - Log what `sync_request_status()` finds vs what it updates
   - Include album monitoring status in sync logs

3. **Create Debug Endpoint** (Optional):
   - `/api/debug/request/<id>` - Shows full state of request + Lidarr data
   - Useful for troubleshooting

**Estimated Effort**: 1-2 hours
**Impact**: HIGH - Makes debugging much easier

---

## Testing Plan

### Test Case 1: Multiple Albums from Same Artist
1. Request "Panic" from Caravan Palace
2. Verify: Only "Panic" is monitored in Lidarr
3. Request "Chronologic" from Caravan Palace
4. Verify: Both "Panic" AND "Chronologic" are monitored
5. Verify: Other Caravan Palace albums remain unmonitored
6. Check database: Each request shows correct `album_monitored=True`
7. Check UI: Each card shows individual album status

### Test Case 2: Album-Specific Download Progress
1. Request an album that's partially downloaded
2. Verify: Card shows tracks for THAT album (not all artist albums)
3. Request another album from same artist
4. Verify: Each card shows different progress percentages

### Test Case 3: Monitoring Persistence
1. Request an album
2. Wait for status sync
3. Manually check Lidarr: Verify album still monitored
4. Trigger another sync
5. Verify: Album stays monitored (doesn't get reset)

---

## Deployment Strategy

1. **Backup Database**:
   ```bash
   cp data/requests.db data/requests.db.backup-v0.6.8
   ```

2. **Test Locally**:
   - Run migration 004
   - Test with multiple requests
   - Verify monitoring status

3. **Deploy to Production**:
   ```bash
   DOCKER_BUILDKIT=0 docker compose build jukebox
   docker compose up -d jukebox
   ```

4. **Post-Deployment Verification**:
   - Check existing Caravan Palace requests
   - Verify album monitoring status in Lidarr
   - Make a test request and verify behavior

---

---

## Phase 5: Quick-Win UX Improvements (P2 - Bonus Features)

**Goal**: Roll in low-effort/high-reward UX improvements while we're already updating the frontend

Since we're already modifying request cards and status display in Phase 1, these additional improvements have minimal marginal cost:

### 5A. Improve Status Badge Clarity (15 min)

**Current Problem**:
- "SUBMITTED" status is ambiguous
- "EXISTING" status unclear (BUG #4 in TODO)

**Improvements**:
```python
# Update status_badge.html
{% if status == 'submitted' %}
  <span class="status-icon">🔍</span>
  <span class="status-text">SEARCHING</span>

{% elif status == 'existing' %}
  <span class="status-icon">✓</span>
  <span class="status-text">AVAILABLE</span>
```

**Benefits**:
- "SEARCHING" is clearer than "SUBMITTED"
- "AVAILABLE" is clearer than "EXISTING"
- Fixes BUG #4 with zero backend changes

### 5B. Add Album Monitoring Status Badge (20 min)

**Addition to Request Cards**:
```html
{% if req.status in ['submitted', 'downloading'] and req.lidarr_album_id %}
  <div class="monitoring-status">
    {% if req.album_monitored %}
      <span class="monitor-badge monitored">👁️ Monitored</span>
    {% else %}
      <span class="monitor-badge unmonitored">⚠️ Not Monitored</span>
    {% endif %}
  </div>
{% endif %}
```

**Benefits**:
- Users can SEE if their album is being monitored
- Makes bug v0.6.8-1 visible to users
- Helps identify when monitoring fails
- Uses new `album_monitored` field from Phase 1

### 5C. Delete Request Button (30 min)

**From ALL-PROPOSED-FEATURES.md Tier 1 #2**:
- Add delete button (trash icon) to each request card
- Soft delete: Set status to 'deleted' rather than hard delete (preserves history)
- Simple DELETE endpoint
- Smooth card removal animation

**Implementation**:
```python
# Add endpoint (app.py)
@app.route("/api/requests/<int:req_id>", methods=["DELETE"])
@login_required
def delete_request(req_id):
    user = current_user()
    with closing(get_db()) as conn:
        # Verify ownership
        req = conn.execute("SELECT user_id FROM requests WHERE id = ?", (req_id,)).fetchone()
        if not req or req['user_id'] != user['id']:
            return jsonify({"error": "Not found"}), 404

        # Soft delete
        conn.execute("UPDATE requests SET status = 'deleted', updated_at = ? WHERE id = ?",
                    (datetime.utcnow().isoformat(), req_id))
        conn.commit()
    return jsonify({"success": True})
```

```javascript
// Frontend: Add delete button to card
async function deleteRequest(reqId) {
  if (!confirm('Delete this request?')) return;

  const resp = await fetch(`/api/requests/${reqId}`, {method: 'DELETE'});
  if (resp.ok) {
    // Animate card out
    const card = document.querySelector(`[data-request-id="${reqId}"]`);
    card.style.opacity = '0';
    setTimeout(() => card.remove(), 300);
  }
}
```

**Benefits**:
- Users can clean up old/failed requests
- No permanent data loss (soft delete)
- Cleaner UI experience

### 5D. Show/Hide Failed Requests Toggle (20 min)

**From ALL-PROPOSED-FEATURES.md Tier 1 #1**:
- Add toggle button at top of page: "Hide Failed Requests"
- Uses localStorage to persist preference
- Pure JavaScript, no backend changes

**Implementation**:
```javascript
// Add to requests page
function toggleFailedRequests() {
  const hidden = localStorage.getItem('hideFailedRequests') === 'true';
  const newState = !hidden;
  localStorage.setItem('hideFailedRequests', newState);

  document.querySelectorAll('.request-card[data-status="failed"]').forEach(card => {
    card.style.display = newState ? 'none' : 'block';
  });

  // Update button text
  document.getElementById('toggle-failed-btn').textContent =
    newState ? 'Show Failed Requests' : 'Hide Failed Requests';
}

// Apply on page load
document.addEventListener('DOMContentLoaded', () => {
  if (localStorage.getItem('hideFailedRequests') === 'true') {
    toggleFailedRequests();
  }
});
```

**Benefits**:
- Declutters view for users with many failed requests
- Preference persists across sessions
- Zero backend work

### 5E. Better Status Text on Cards (10 min)

**Enhancement to status badge display**:
```python
# Update status_badge macro to include helpful subtext
{% if status == 'submitted' %}
  <span class="status-subtext">Lidarr is searching...</span>
{% elif status == 'downloading' %}
  <span class="status-subtext">Download in progress</span>
{% endif %}
```

**Benefits**:
- Users understand what's happening
- Reduces support questions
- Professional polish

### 5F. Status Filter Pills (Optional - 30 min)

**From ALL-PROPOSED-FEATURES.md Tier 1 #4**:
- Add filter buttons at top: [All] [Searching] [Downloading] [Completed] [Failed]
- Pure JavaScript with localStorage
- Shows count in each pill: "Downloading (3)"

**Benefits**:
- Quick filtering without scrolling
- Status overview at a glance
- Mobile-friendly

**Estimated Effort**: 2-2.5 hours total
**Impact**: HIGH - Multiple quality-of-life improvements at low cost
**Risk**: LOW - Mostly frontend changes, soft deletes preserve data

---

## Summary & Implementation Strategy

**Total Estimated Effort**: 9-12.5 hours (across 2 stages)

### ✅ Stage 1: Critical Bug Fixes (COMPLETE)

**Phases 1-3**: 6 hours (actual)
1. ✅ **Phase 1**: Album-specific status tracking - 2-3 hrs
2. ✅ **Phase 2**: Fix monitoring bugs - 2-3 hrs
3. ✅ **Phase 3**: Prevent unrequested downloads - 2 hrs

**Status**: v0.6.9 deployed 2025-11-26, ready for field testing

**Deliverables**:
- ✅ Per-album track counts (not artist-wide)
- ✅ Defensive monitoring verification
- ✅ Verified unmonitoring in staging workflow
- ✅ Better logging for debugging

**Version**: v0.6.9 (deployed to production)

---

### 🎨 Stage 2: UX Polish & Quick Wins (READY TO IMPLEMENT)

**When**: After Stage 1 field testing confirms bugs are fixed
**Total Effort**: 2-2.5 hours for all 6 improvements
**Version**: v0.6.10 or v0.7.0 (depending on scope)

**Prerequisites**:
- Stage 1 field tested and stable
- No critical bugs found in v0.6.9
- User feedback positive

**Implementation Order** (by effort, fastest first):

#### Phase 5A: Better Status Badge Text (15 min) ⚡
```python
# app/templates/components/status_badge.html
{% if status == 'submitted' %}
  <span class="status-icon">🔍</span>
  <span class="status-text">SEARCHING</span>  # Changed from SUBMITTED

{% elif status == 'existing' %}
  <span class="status-icon">✓</span>
  <span class="status-text">AVAILABLE</span>  # Changed from EXISTING
```
**Impact**: Fixes BUG #4 with zero backend changes

#### Phase 5B: Status Subtext (10 min) ⚡
```python
# Add helpful subtext to status badges
{% if status == 'submitted' %}
  <span class="status-subtext">Lidarr is searching...</span>
{% elif status == 'downloading' %}
  <span class="status-subtext">Download in progress</span>
{% endif %}
```
**Impact**: Professional polish, reduces user confusion

#### Phase 5C: Album Monitoring Badge (20 min) ⚡
```html
<!-- app/templates/components/request_card.html -->
{% if req.status in ['submitted', 'downloading'] and req.lidarr_album_id %}
  <div class="monitoring-status">
    {% if req.album_monitored %}
      <span class="monitor-badge monitored">👁️ Monitored</span>
    {% else %}
      <span class="monitor-badge unmonitored">⚠️ Not Monitored</span>
    {% endif %}
  </div>
{% endif %}
```
**Impact**: Makes monitoring status visible, helps identify issues

#### Phase 5D: Hide Failed Requests Toggle (20 min) ⚡
```javascript
// Pure frontend - no backend changes
function toggleFailedRequests() {
  const hidden = localStorage.getItem('hideFailedRequests') === 'true';
  const newState = !hidden;
  localStorage.setItem('hideFailedRequests', newState);

  document.querySelectorAll('.request-card[data-status="failed"]').forEach(card => {
    card.style.display = newState ? 'none' : 'block';
  });
}

// Apply on page load
if (localStorage.getItem('hideFailedRequests') === 'true') {
  toggleFailedRequests();
}
```
**Impact**: Declutters UI, preference persists

#### Phase 5E: Delete Request Button (30 min) ⚡
```python
# Backend: app/app.py
@app.route("/api/requests/<int:req_id>", methods=["DELETE"])
@login_required
def delete_request(req_id):
    user = current_user()
    with closing(get_db()) as conn:
        req = conn.execute("SELECT user_id FROM requests WHERE id = ?", (req_id,)).fetchone()
        if not req or req['user_id'] != user['id']:
            return jsonify({"error": "Not found"}), 404

        # Soft delete
        conn.execute("UPDATE requests SET status = 'deleted', updated_at = ? WHERE id = ?",
                    (datetime.utcnow().isoformat(), req_id))
        conn.commit()
    return jsonify({"success": True})
```
```javascript
// Frontend: request_card.html
async function deleteRequest(reqId) {
  if (!confirm('Delete this request?')) return;
  const resp = await fetch(`/api/requests/${reqId}`, {method: 'DELETE'});
  if (resp.ok) {
    const card = document.querySelector(`[data-request-id="${reqId}"]`);
    card.style.opacity = '0';
    setTimeout(() => card.remove(), 300);
  }
}
```
**Impact**: User-requested feature, cleaner UI

#### Phase 5F: Status Filter Pills (30 min, OPTIONAL) ⚡
```html
<!-- Add to top of requests page -->
<div class="status-filters">
  <button class="filter-pill active" data-filter="all">All (<span id="count-all">0</span>)</button>
  <button class="filter-pill" data-filter="submitted">Searching (<span id="count-submitted">0</span>)</button>
  <button class="filter-pill" data-filter="downloading">Downloading (<span id="count-downloading">0</span>)</button>
  <button class="filter-pill" data-filter="completed">Completed (<span id="count-completed">0</span>)</button>
  <button class="filter-pill" data-filter="failed">Failed (<span id="count-failed">0</span>)</button>
</div>
```
```javascript
// Filter functionality with counts
function filterByStatus(status) {
  document.querySelectorAll('.request-card').forEach(card => {
    card.style.display = (status === 'all' || card.dataset.status === status) ? 'block' : 'none';
  });
  // Update active state
  document.querySelectorAll('.filter-pill').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.filter === status);
  });
}

// Update counts
function updateStatusCounts() {
  const counts = {};
  document.querySelectorAll('.request-card').forEach(card => {
    const status = card.dataset.status;
    counts[status] = (counts[status] || 0) + 1;
  });
  // Update pill counts
  Object.keys(counts).forEach(status => {
    document.getElementById(`count-${status}`).textContent = counts[status];
  });
}
```
**Impact**: Quick filtering, status overview at a glance

---

### Stage 2 Testing Plan

1. **Visual Testing**:
   - Verify "SEARCHING" and "AVAILABLE" status text
   - Check monitoring badge appears on active requests
   - Test delete button animation
   - Verify filter pills work correctly

2. **Functional Testing**:
   - Delete a request and verify soft delete
   - Toggle failed requests on/off
   - Filter by different statuses
   - Refresh page and verify localStorage persists

3. **Cross-Browser Testing**:
   - Test in Chrome, Firefox, Safari
   - Verify mobile responsiveness

---

### Recommended Approach

**✅ Stage 1 Complete**: v0.6.9 deployed, ready for field testing

**Next Steps**:
1. **User tests v0.6.9**: Verify bugs are fixed
2. **Gather feedback**: Check for any regressions
3. **Decision point**: Proceed with Stage 2 if stable
4. **Implement Stage 2**: All 6 features in ~2.5 hours
5. **Deploy v0.6.10**: Quick UX polish release

**Timeline Suggestion**:
- Week 1: Field test v0.6.9
- Week 2: Implement Stage 2 if stable
- Deploy v0.6.10 with UX improvements

**Risk Level**: MEDIUM (LOW with Phase 5 additions)
- Database migration is additive (low risk)
- Changes to sync logic could affect existing requests
- Phase 5 changes are mostly frontend (very low risk)
- Mitigation: Backup database, test thoroughly before deploy

**Expected Outcomes**:
- ✅ Each request card shows status for THAT album only (tracks, not albums)
- ✅ Albums stay monitored once set (defensive re-monitoring)
- ✅ Only requested albums get downloaded (verified unmonitoring)
- ✅ Better visibility into album monitoring state changes (logging)
- ✅ Clearer status badges ("SEARCHING" vs "SUBMITTED")
- ✅ Users can see if albums are monitored (monitoring badge)
- ✅ Users can delete unwanted requests (soft delete)
- ✅ Users can hide failed requests (toggle)
- ✅ Professional status messaging (subtext)
