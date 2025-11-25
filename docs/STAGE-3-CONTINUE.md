# Stage 3 Continuation - Pickup Prompt

**Status**: Stage 3 is 67% complete (4/6 tasks done)
**Remaining Work**: ~2 hours
**Context**: Fresh session, ready to implement final 2 tasks

---

## Quick Prompt for New Agent

```
Continue Stage 3 (Artist Staging Workflow) for Jukebox at /home/michael/dev/work/jukebox.

Read these files in order:
1. AGENT-HANDOFF.md (full context)
2. docs/STAGE-3-PLAN.md (implementation plan)
3. docs/STAGE-3-CONTINUE.md (this file - current status)
4. TODO.md (task tracking)

**Already Complete** (committed: 5d2cc2d):
✅ Task 1: Database migration (artist_staging table)
✅ Task 2: Backend functions (5 functions in app.py lines 539-741)
✅ Task 3: Configuration (STAGING_REFRESH_DAYS)
✅ Task 4: API endpoints (/api/artist/pull-albums, /api/artist/albums/<id>)

**Next Tasks** (implement these):
⏳ Task 5: Update request submission flow (app/app.py, new_request route)
⏳ Task 6: Frontend UI + polling (app/templates/new_request.html)

Then:
- Test: rebuild container, test flow
- Document: update TODO.md, AGENT-HANDOFF.md
- Commit: Stage 3 complete

Deploy with: docker compose build jukebox && docker compose up -d jukebox
```

---

## What Was Built (Tasks 1-4)

### Database Migration ✅
Created `artist_staging` table with:
- `mb_artist_id` (unique constraint - prevents duplicates)
- `lidarr_artist_id` (tracks Lidarr's internal ID)
- `last_refreshed_at` (for staleness tracking)
- `refresh_count` (analytics)
- Indexes on mb_id, lidarr_id, last_refresh, user_id

**Migration already applied** to production DB in container.

### Backend Functions ✅
Added 5 functions to `app/app.py` (lines 539-741):

1. **`create_artist_in_staging(artist_name, mb_artist_id, user_id)`**
   - Adds artist to Lidarr with admin root folder
   - `monitored = False`, `addOptions.monitor = "none"`
   - Tags with "staging"
   - Stores in artist_staging table
   - Returns (lidarr_artist_id, error)

2. **`find_staging_artist(mb_artist_id)`**
   - Queries artist_staging table by MusicBrainz ID
   - Returns (staging_record, error)

3. **`trigger_artist_refresh(lidarr_artist_id)`**
   - POSTs to `/command` with `RefreshArtist` command
   - Updates `last_refreshed_at` and `refresh_count` in DB
   - Returns (success, error)

4. **`get_artist_albums(lidarr_artist_id)`**
   - GETs from `/album?artistId={id}`
   - Returns simplified album list with id, title, releaseDate, monitored, statistics
   - Returns (albums, error)

5. **`move_artist_to_user(lidarr_artist_id, username)`**
   - GETs current artist data from Lidarr
   - Updates rootFolderPath, path, tags to user's values
   - PUTs back to Lidarr
   - Returns (success, error)

### API Endpoints ✅
Added 2 endpoints to `app/app.py` (lines 1287-1375):

1. **`POST /api/artist/pull-albums`**
   - Receives: `{artist_name, mb_artist_id}`
   - Checks staging with `find_staging_artist()`
   - If exists & fresh (< 7 days): returns `state: "ready"` immediately
   - If exists & stale (> 7 days): triggers refresh, returns `state: "refreshing"`
   - If new: calls `create_artist_in_staging()`, returns `state: "loading"`
   - Returns: `{status, lidarr_artist_id, state, message}`

2. **`GET /api/artist/albums/<lidarr_id>`**
   - Used for polling by frontend
   - Calls `get_artist_albums(lidarr_id)`
   - Returns: `{ready: bool, albums: [...]}`
   - `ready = true` when albums list is populated

### Configuration ✅
- `STAGING_REFRESH_DAYS = 7` (configurable via env var)
- Environment variable: `STAGING_REFRESH_DAYS`

---

## What Needs to Be Built (Tasks 5-6)

### Task 5: Update Request Submission Flow
**File**: `app/app.py`, `new_request()` route (currently around line 900)

**Current Flow**:
1. User submits form with artist_name + album_title
2. Lookup artist in MusicBrainz
3. Check if artist exists in Lidarr
4. If exists: use it (or flip album to monitored)
5. If not exists: create artist in user space

**New Flow** (modify to support staging):
1. User submits form with artist_name + album_title
2. Lookup artist in MusicBrainz → get mb_artist_id
3. **NEW**: Check if artist in staging (`find_staging_artist()`)
4. **NEW**: If in staging: call `move_artist_to_user()` to move to user space
5. If in user space already: use it (existing logic)
6. If nowhere: error (must use "Pull Albums" first)
7. Continue with album monitoring logic (find album, set monitored, trigger search)

**Key Changes**:
```python
# After artist lookup (line ~760)
foreign_artist_id = artist_data.get("foreignArtistId")  # This is mb_artist_id

# NEW: Check staging first
staging_artist, _ = find_staging_artist(foreign_artist_id)

if staging_artist:
    # Move from staging to user
    success, err = move_artist_to_user(
        staging_artist["lidarr_artist_id"],
        user["username"]
    )
    if success:
        lidarr_artist_id = staging_artist["lidarr_artist_id"]
        # Continue to album monitoring...
    else:
        # Handle error
        flash(f"Failed to move artist: {err}", "danger")
        return redirect(url_for("list_requests"))
else:
    # Existing logic: check if in user space, or create new
    # (Keep existing code mostly as-is)
```

**Testing**:
- Submit request after "Pull Albums" → should move artist
- Submit request for existing user artist → should work
- Submit request without "Pull Albums" → should error

---

### Task 6: Frontend UI + Polling
**File**: `app/templates/new_request.html`

**What to Add**:

1. **"Pull Albums" Button** (after artist selection)
   - Shows after user selects artist from autocomplete
   - Hidden initially, revealed when artist validated
   - Click triggers `/api/artist/pull-albums`

2. **Loading States**
   - "Loading albums from Lidarr..." (new artist)
   - "Refreshing albums..." (stale artist)
   - Instant (no spinner) for fresh artist

3. **Album Dropdown**
   - `<select>` populated with albums from Lidarr
   - Hidden until albums loaded
   - Replaces or augments existing album text input

4. **Polling Logic**
   - After `/api/artist/pull-albums` returns `lidarr_artist_id`
   - If `state === "ready"`: get albums immediately
   - If `state === "loading"` or `"refreshing"`: poll `/api/artist/albums/<id>`
   - Exponential backoff: 1s, 2s, 2s, 3s, 3s, 4s... (max 30s)
   - On success: populate dropdown
   - On timeout: show error

**Example HTML Structure**:
```html
<!-- After artist autocomplete -->
<div id="artist-validated" style="display:none;">
  <div class="artist-card">
    <h3 id="validated-artist-name"></h3>
    <p id="validated-artist-info"></p>
    <button id="pull-albums-btn" class="btn btn-primary" type="button">
      Pull Albums from Lidarr
    </button>
  </div>
</div>

<!-- Loading state -->
<div id="loading-albums" style="display:none;">
  <span class="spinner"></span>
  <span id="loading-message">Loading albums...</span>
</div>

<!-- Album dropdown -->
<div id="album-dropdown-container" style="display:none;">
  <label for="album-select">Select Album *</label>
  <select id="album-select" name="album_title" required>
    <option value="">Choose an album...</option>
  </select>
</div>
```

**Example JavaScript** (add to existing JS block):
```javascript
// After artist selected from autocomplete
artistAutocomplete.on('select', (artist) => {
    // Show "Pull Albums" button
    document.getElementById('artist-validated').style.display = 'block';
    document.getElementById('validated-artist-name').textContent = artist.name;

    // Store MB ID for later
    window.selectedArtist = {
        name: artist.name,
        mbId: artist.id  // foreignArtistId from MB
    };
});

// Pull Albums button click
document.getElementById('pull-albums-btn').addEventListener('click', async () => {
    const artist = window.selectedArtist;

    // Show loading
    document.getElementById('loading-albums').style.display = 'block';
    document.getElementById('loading-message').textContent = 'Loading albums...';

    // Call API
    const response = await fetch('/api/artist/pull-albums', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            artist_name: artist.name,
            mb_artist_id: artist.mbId
        })
    });

    const data = await response.json();

    if (data.state === 'ready') {
        // Get albums immediately
        const albums = await getAlbums(data.lidarr_artist_id);
        populateAlbumDropdown(albums);
    } else {
        // Poll for albums
        pollForAlbums(data.lidarr_artist_id, data.state);
    }
});

// Polling function
async function pollForAlbums(lidarrId, initialState) {
    const delays = [1000, 2000, 2000, 3000, 3000, 4000, 4000, 5000]; // Total ~30s
    const message = initialState === 'refreshing' ? 'Refreshing albums...' : 'Loading albums...';
    document.getElementById('loading-message').textContent = message;

    for (let i = 0; i < delays.length; i++) {
        await sleep(delays[i]);

        const response = await fetch(`/api/artist/albums/${lidarrId}`);
        const data = await response.json();

        if (data.ready && data.albums.length > 0) {
            populateAlbumDropdown(data.albums);
            return;
        }

        document.getElementById('loading-message').textContent =
            `${message} (${i + 1}/${delays.length})`;
    }

    // Timeout
    alert('Lidarr is taking longer than expected. Please try again.');
    document.getElementById('loading-albums').style.display = 'none';
}

function populateAlbumDropdown(albums) {
    const select = document.getElementById('album-select');
    select.innerHTML = '<option value="">Choose an album...</option>';

    albums.forEach(album => {
        const option = document.createElement('option');
        option.value = album.title;
        option.textContent = `${album.title} ${album.releaseDate ? '(' + album.releaseDate.substring(0,4) + ')' : ''}`;
        select.appendChild(option);
    });

    // Hide loading, show dropdown
    document.getElementById('loading-albums').style.display = 'none';
    document.getElementById('album-dropdown-container').style.display = 'block';
}
```

---

## Testing Checklist

### Test 1: New Artist Flow
1. Search "frank sinatra" → validates
2. Click "Pull Albums" → loading spinner (5-10s)
3. Albums appear in dropdown
4. Select album → submit form
5. Verify: artist in user's root folder, album monitored
6. Check Lidarr: artist has user's tag, album downloading

### Test 2: Staging Reuse (Fresh)
1. User A pulls "Taylor Swift"
2. Wait 1 minute
3. User B searches "taylor swift"
4. Click "Pull Albums" → instant (< 1s, no spinner)
5. Albums appear immediately
6. Both users can select different albums

### Test 3: Staging Refresh (Stale)
1. Manually set `last_refreshed_at` to 10 days ago in DB
2. Search artist → click "Pull Albums"
3. See "Refreshing albums..." message (2-5s)
4. Albums appear with updated data

### Test 4: Error Handling
1. Try to submit without clicking "Pull Albums" → error
2. Timeout scenario (Lidarr slow) → timeout message
3. Lidarr down → error message

---

## Deployment

```bash
cd /home/michael/dev/work/jukebox
docker compose build jukebox && docker compose up -d jukebox

# Verify
curl http://localhost:5000/api/health
docker compose logs --tail=50 jukebox

# Test API
curl -X POST http://localhost:5000/api/artist/pull-albums \
  -H "Content-Type: application/json" \
  -d '{"artist_name":"Test Artist","mb_artist_id":"test-id"}' \
  --cookie "session=..."
```

---

## Files Modified So Far

- ✅ `db/migrations/003_artist_staging.sql` (new)
- ✅ `app/app.py` (lines 539-741: functions, lines 1287-1375: API)
- ⏳ `app/app.py` (need to modify: new_request route ~line 900)
- ⏳ `app/templates/new_request.html` (need to add: UI + JS)

---

## Documentation to Update After Completion

- [ ] TODO.md: Mark Task #1 (Artist Staging) as complete
- [ ] AGENT-HANDOFF.md: Update "Recent Work" and "Next Steps"
- [ ] ROADMAP.md: Update v0.6.0 progress
- [ ] STAGE-TEST-PLAN.md: Note Stage 3 completion

---

## Success Criteria

✅ Artist can be pulled to staging (admin space)
✅ Staging is reused across users
✅ Stale artists are refreshed (7-day threshold)
✅ Artist moves to user space on album commit
✅ Album monitoring + download triggered
✅ No errors in logs
✅ All manual tests pass
✅ Documentation updated
✅ Git commit created and pushed

---

**Estimated Time**: 2 hours
**Current Progress**: 67% (4/6 tasks)
**Token Budget**: Fresh session, full context available
