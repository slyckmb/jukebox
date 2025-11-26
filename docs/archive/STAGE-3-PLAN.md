# Stage 3 Plan - Artist Staging Workflow

**Feature**: Admin Staging Area with Album Pull
**Target Duration**: 3-4 hours (within 5-hour context window)
**Priority**: HIGH (Core v0.6.0 feature)
**Status**: Ready to implement

---

## Overview

Implement two-phase commit for artist requests:
1. **Phase 1**: User validates artist → "Pull Albums" → artist added to staging (admin space, unmonitored)
2. **Phase 2**: User selects album → artist moved to user space → album monitored → download starts

**Why**: Prevents wrong artist additions, provides album validation, solves "Taylor Swift album not found" problem

---

## Implementation Tasks (Ordered)

### Task 1: Database Migration (30 min)
**Files**: `db/migrations/003_artist_staging.sql` (new)

Create `artist_staging` table and migration script:

```sql
-- db/migrations/003_artist_staging.sql
CREATE TABLE IF NOT EXISTS artist_staging (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    artist_name TEXT NOT NULL,
    lidarr_artist_id INTEGER,
    mb_artist_id TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    last_refreshed_at TEXT,
    refresh_count INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_staging_mb_id ON artist_staging(mb_artist_id);
CREATE INDEX idx_staging_lidarr_id ON artist_staging(lidarr_artist_id);
CREATE INDEX idx_staging_last_refresh ON artist_staging(last_refreshed_at);

-- Optional: link requests to staging
ALTER TABLE requests ADD COLUMN artist_staging_id INTEGER REFERENCES artist_staging(id);
```

**Testing**:
- Run migration manually
- Verify table exists
- Check indexes created

---

### Task 2: Backend Helper Functions (60 min)
**Files**: `app/app.py`

Add after `set_album_monitored()` function:

#### 2a. `create_artist_in_staging()`
```python
def create_artist_in_staging(artist_name: str, mb_artist_id: str, user_id: int):
    """
    Add artist to Lidarr staging area (admin space, unmonitored).
    Returns (lidarr_artist_id, error)
    """
    # Use admin root folder and staging tag
    # monitored = False
    # addOptions: {"monitor": "none", "searchForMissingAlbums": False}
```

#### 2b. `find_staging_artist()`
```python
def find_staging_artist(mb_artist_id: str):
    """
    Check if artist exists in staging.
    Returns (staging_record, error)
    """
```

#### 2c. `trigger_artist_refresh()`
```python
def trigger_artist_refresh(lidarr_artist_id: int):
    """
    Tell Lidarr to refresh artist metadata from MusicBrainz.
    POST /command {"name": "RefreshArtist", "artistId": 123}
    Returns (success: bool, error)
    """
```

#### 2d. `get_artist_albums()`
```python
def get_artist_albums(lidarr_artist_id: int):
    """
    Get all albums for artist from Lidarr.
    GET /album?artistId={id}
    Returns (albums: list, error)
    """
```

#### 2e. `move_artist_to_user()`
```python
def move_artist_to_user(lidarr_artist_id: int, username: str):
    """
    Move artist from staging to user space.
    - GET /artist/{id}
    - Update rootFolderPath, path, tags
    - PUT /artist/{id}
    Returns (success: bool, error)
    """
```

**Testing**:
- Unit test each function independently
- Mock Lidarr API responses
- Verify DB operations

---

### Task 3: Frontend UI - "Pull Albums" Button (30 min)
**Files**: `app/templates/new_request.html`

Add UI between artist selection and album dropdown:

```html
<!-- After artist validated -->
<div id="artist-validated" style="display:none;">
  <div class="artist-card">
    <h3 id="validated-artist-name"></h3>
    <button id="pull-albums-btn" class="btn btn-primary">
      Pull Albums from Lidarr
    </button>
  </div>
</div>

<!-- Album dropdown (hidden until pulled) -->
<div id="album-dropdown-container" style="display:none;">
  <label for="album-select">Select Album</label>
  <select id="album-select" name="album_title" required>
    <option value="">Choose an album...</option>
  </select>
</div>

<!-- Loading states -->
<div id="loading-albums" style="display:none;">
  <span class="spinner"></span>
  <span id="loading-message">Loading albums...</span>
</div>
```

**JavaScript**:
- Listen for artist selection
- Show "Pull Albums" button
- AJAX call to `/api/artist/pull-albums`
- Poll for album list
- Populate dropdown when ready

**Testing**:
- Click "Pull Albums" → loading spinner shows
- Albums populate → dropdown appears
- Select album → form submits

---

### Task 4: API Endpoints (45 min)
**Files**: `app/app.py`

#### 4a. `/api/artist/pull-albums` (POST)
```python
@app.route("/api/artist/pull-albums", methods=["POST"])
@login_required
def pull_albums():
    """
    Trigger album pull for artist.
    Returns {status, lidarr_artist_id, message}
    """
    # Get artist_name, mb_artist_id from request
    # Check staging (find_staging_artist)
    # If exists and fresh: return immediately
    # If exists and stale: trigger refresh
    # If not exists: create_artist_in_staging
    # Return lidarr_artist_id for polling
```

#### 4b. `/api/artist/albums/<lidarr_id>` (GET)
```python
@app.route("/api/artist/albums/<int:lidarr_id>", methods=["GET"])
@login_required
def get_albums(lidarr_id):
    """
    Get album list for artist.
    Used by frontend for polling.
    Returns {albums: [...], ready: bool}
    """
    # Call get_artist_albums()
    # Return album list if ready
    # Return {ready: false} if still populating
```

**Testing**:
- Postman/curl tests for each endpoint
- Verify JSON responses
- Test error cases (invalid IDs, Lidarr down)

---

### Task 5: Update Request Submission Flow (45 min)
**Files**: `app/app.py` - modify `new_request()` route

Current flow adds artist immediately. New flow:
1. Check if artist in staging
2. If yes: move to user space
3. Then monitor album + trigger download

**Changes**:
```python
@app.route("/request/new", methods=["POST"])
def new_request():
    # ... existing validation ...

    # NEW: Check if artist in staging
    staging_artist = find_staging_artist(mb_artist_id)

    if staging_artist:
        # Move from staging to user
        success, err = move_artist_to_user(
            staging_artist["lidarr_artist_id"],
            user["username"]
        )
        if not success:
            flash(f"Failed to move artist: {err}", "danger")
            return redirect(url_for("list_requests"))

        lidarr_artist_id = staging_artist["lidarr_artist_id"]
    else:
        # Existing flow: check if in user space
        exists, existing_artist, check_error = check_artist_exists_in_lidarr(foreign_artist_id)

        if exists:
            # Use existing user artist
            lidarr_artist_id = existing_artist.get("id")
        else:
            # Add new artist to user space
            data, err = create_artist_in_lidarr(user["username"], artist_name)
            # ... existing error handling ...

    # Continue with album monitoring logic...
```

**Testing**:
- Submit request after "Pull Albums" → moves artist to user space
- Submit request for existing user artist → skips staging
- Submit request for new artist (no pull) → error/prompt to pull

---

### Task 6: Polling Logic (Frontend) (30 min)
**Files**: `app/templates/new_request.html` (JavaScript)

Implement exponential backoff polling:

```javascript
async function pollForAlbums(lidarrArtistId) {
    const maxAttempts = 10;
    const delays = [1000, 2000, 2000, 3000, 3000, 4000, 4000, 5000, 5000, 5000]; // Total: ~30s

    for (let i = 0; i < maxAttempts; i++) {
        await sleep(delays[i]);

        const response = await fetch(`/api/artist/albums/${lidarrArtistId}`);
        const data = await response.json();

        if (data.ready && data.albums.length > 0) {
            return data.albums;
        }

        updateLoadingMessage(`Checking for albums... (${i + 1}/${maxAttempts})`);
    }

    throw new Error("Timeout: Lidarr took too long to populate albums");
}
```

**Testing**:
- New artist → polls until albums appear
- Timeout scenario → shows error message
- Cancellation (user closes tab) → stops polling

---

## Testing Plan

### Integration Tests

#### Test 1: Full Flow (New Artist)
```
1. Type "frank sinatra" → MB validates
2. Click "Pull Albums" → loading spinner
3. Wait 5-10s → albums appear in dropdown
4. Select "In The Wee Small Hours" → submit
5. Verify: artist moved to user space, album monitored
6. Check logs: move operation logged
7. Check Lidarr: artist in user's root folder with user's tag
```

#### Test 2: Reuse Staging (Fresh)
```
1. User A pulls "Taylor Swift" on Day 1
2. User B searches "taylor swift" on Day 2
3. User B clicks "Pull Albums" → instant (< 1s)
4. Verify: same Lidarr artist ID reused
5. User B selects album → gets own copy in own root folder
```

#### Test 3: Refresh Staging (Stale)
```
1. Manually set last_refreshed_at to 10 days ago
2. Search artist → click "Pull Albums"
3. Verify: "Refreshing albums..." message
4. Wait 2-5s → albums appear (updated)
5. Check logs: RefreshArtist command sent
```

#### Test 4: Existing User Artist
```
1. User already has "Beatles" in library
2. Search "beatles" → click "Pull Albums"
3. Verify: skips staging, uses user's existing artist
4. Albums load instantly from user's library
```

### Regression Tests
- [ ] Existing request flow still works (without staging)
- [ ] Status sync still works
- [ ] Request list displays correctly
- [ ] Authentication still required

---

## Success Criteria

✅ Database migration complete, table exists
✅ All helper functions implemented and tested
✅ "Pull Albums" button appears after artist validation
✅ Albums populate in dropdown within 10s
✅ Album selection triggers move to user space
✅ Download starts immediately after commit
✅ Staging reuse works (instant for fresh artists)
✅ Refresh works (stale artists get updated)
✅ No errors in logs
✅ Documentation updated (TODO, ROADMAP, HANDOFF)
✅ Git commit created and pushed

---

## Rollback Plan

If major issues encountered:
1. Keep database migration (safe, just new table)
2. Add feature flag: `ENABLE_STAGING = False`
3. Revert to old flow (direct artist add)
4. Document issues in TODO.md
5. Fix in Stage 4

---

## Time Budget

| Task | Est. Time | Cumulative |
|------|-----------|------------|
| 1. DB Migration | 30 min | 0:30 |
| 2. Backend Functions | 60 min | 1:30 |
| 3. Frontend UI | 30 min | 2:00 |
| 4. API Endpoints | 45 min | 2:45 |
| 5. Request Flow | 45 min | 3:30 |
| 6. Polling Logic | 30 min | 4:00 |
| Testing | 30 min | 4:30 |
| Documentation | 15 min | 4:45 |
| Deploy & Verify | 15 min | 5:00 |

**Total**: ~5 hours (fits in context window with buffer)

---

## Next Steps After Stage 3

**Stage 4** (if time/energy):
- Implement "Trigger search on monitor flip" (Task #1 from Stage 2)
- Improve status messages (Task #2 from Stage 2)
- Add version to banner (Task #3 from Stage 2)

OR pause and test Stage 3 thoroughly before continuing.

---

## Notes

- This is the biggest stage yet (5 hours)
- Acceptable because it's a single coherent feature
- If exceeding 4 hours, commit what works and defer polish to Stage 4
- Focus on happy path first, edge cases later
