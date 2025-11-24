# Stage 3: Lidarr Status Tracking & Sync - THE MONEY SHOT

**Priority**: 💰 CRITICAL (The complete user journey)
**Complexity**: ⭐⭐⭐⭐ (High)
**Impact**: 💥💥💥💥💥 (CRITICAL - This is the payoff!)
**Time Estimate**: 1.5-2 hours
**Type**: Backend + Frontend

---

## 🎯 The Money Shot

**Complete User Journey:**
1. User submits request → Status: "Submitted"
2. Lidarr starts downloading → Status: "Downloading (3 of 12 albums)" 📥
3. Download completes → Status: "Completed" ✅
4. User sees **"Listen Now"** buttons → 🎬 Plex | 🎞️ Jellyfin | 🎵 Navidrome
5. User clicks → Opens music, starts listening! 🎵🎉

**This is what makes it all worth it!**

---

## 💡 The Problem

**Current State:**
```
User submits request
    ↓
Status: "Submitted"
    ↓
...crickets... 🦗
    ↓
User checks back hours later
    ↓
Still "Submitted" 😞
    ↓
User doesn't know if it's downloading, failed, or complete
```

**Desired State:**
```
User submits request
    ↓
Status: "Submitted" → "Downloading (2 of 10 albums)"
    ↓
Status updates automatically: "Downloading (5 of 10 albums)"
    ↓
Status: "Completed ✓"
    ↓
[🎬 Listen on Plex] [🎞️ Listen on Jellyfin] [🎵 Listen on Navidrome]
    ↓
Click → Music plays! 🎉
```

---

## 🎨 UI Design

### Status Badge Evolution

**Submitted:**
```
┌────────────────────────────────────┐
│ Pink Floyd - The Wall              │
│ 🕐 Submitted                       │
│ Waiting for Lidarr to process...  │
└────────────────────────────────────┘
```

**Downloading:**
```
┌────────────────────────────────────┐
│ Pink Floyd - The Wall              │
│ 📥 Downloading                     │
│ ████████░░░░░░░░ 5 of 10 albums   │
│ 50% complete                       │
└────────────────────────────────────┘
```

**Completed (THE MONEY SHOT):**
```
┌────────────────────────────────────┐
│ Pink Floyd - The Wall              │
│ ✅ Ready to Listen!                │
│                                    │
│ [🎬 Open in Plex]                  │
│ [🎞️ Open in Jellyfin]              │
│ [🎵 Open in Navidrome]             │
│                                    │
│ All 10 albums downloaded           │
└────────────────────────────────────┘
```

---

## 🔧 Technical Implementation

### 1. New Status Values

**Update Database Schema:**
```sql
-- Status values:
-- 'new'         - Just created, not yet processed
-- 'submitted'   - Sent to Lidarr, artist added
-- 'downloading' - Artist monitored, albums downloading
-- 'completed'   - All albums downloaded
-- 'failed'      - Error occurred
-- 'existing'    - Already in library

-- Add new fields for tracking
ALTER TABLE requests ADD COLUMN total_albums INTEGER DEFAULT 0;
ALTER TABLE requests ADD COLUMN downloaded_albums INTEGER DEFAULT 0;
ALTER TABLE requests ADD COLUMN last_sync_at TEXT;
```

**Migration File:** `db/migrations/003_add_download_tracking.sql`
```sql
-- Add download tracking fields
ALTER TABLE requests ADD COLUMN total_albums INTEGER DEFAULT 0;
ALTER TABLE requests ADD COLUMN downloaded_albums INTEGER DEFAULT 0;
ALTER TABLE requests ADD COLUMN last_sync_at TEXT;

-- Update existing 'submitted' requests to have last_sync_at = NULL (needs sync)
UPDATE requests SET last_sync_at = NULL WHERE status = 'submitted';
```

---

### 2. Sync Function (Core Logic)

**File:** `app/app.py`

```python
def sync_request_status(request_id: int) -> bool:
    """
    Sync request status with Lidarr.
    Returns True if status changed, False otherwise.

    Status Transitions:
    - submitted → downloading (artist monitored, albums downloading)
    - downloading → completed (all albums downloaded)
    - submitted → completed (small artists, immediate download)
    """
    with closing(get_db()) as conn:
        req = conn.execute(
            "SELECT id, lidarr_artist_id, artist_name, album_title, status "
            "FROM requests WHERE id = ?",
            (request_id,)
        ).fetchone()

        if not req:
            return False

        # Only sync active statuses
        if req["status"] not in ["submitted", "downloading"]:
            return False

        lidarr_artist_id = req["lidarr_artist_id"]
        if not lidarr_artist_id:
            return False

        try:
            # Query Lidarr for artist status
            url = f"{LIDARR_URL}/artist/{lidarr_artist_id}"
            resp = requests.get(url, params={"apikey": LIDARR_API_KEY}, timeout=10)

            if resp.status_code != 200:
                app.logger.warning(f"Failed to sync request {request_id}: Lidarr returned {resp.status_code}")
                return False

            artist_data = resp.json()

            # Check if artist is monitored
            is_monitored = artist_data.get("monitored", False)

            if not is_monitored:
                # Artist was added but not monitored - still "submitted"
                return False

            # Get album statistics
            statistics = artist_data.get("statistics", {})
            total_albums = statistics.get("albumCount", 0)

            # Query albums to count downloaded
            albums_url = f"{LIDARR_URL}/album"
            albums_resp = requests.get(
                albums_url,
                params={"artistId": lidarr_artist_id, "apikey": LIDARR_API_KEY},
                timeout=10
            )

            downloaded_count = 0
            if albums_resp.status_code == 200:
                albums = albums_resp.json()

                # Count albums that have files
                for album in albums:
                    album_stats = album.get("statistics", {})
                    track_file_count = album_stats.get("trackFileCount", 0)
                    if track_file_count > 0:
                        downloaded_count += 1

            # Determine new status
            old_status = req["status"]
            new_status = old_status

            if downloaded_count == 0:
                # Still waiting for downloads to start
                new_status = "submitted"
            elif downloaded_count < total_albums:
                # Downloads in progress
                new_status = "downloading"
            else:
                # All albums downloaded!
                new_status = "completed"

            # Update database
            now = datetime.utcnow().isoformat()
            conn.execute(
                """UPDATE requests
                   SET status = ?,
                       total_albums = ?,
                       downloaded_albums = ?,
                       last_sync_at = ?,
                       updated_at = ?
                   WHERE id = ?""",
                (new_status, total_albums, downloaded_count, now, now, request_id)
            )
            conn.commit()

            # Return True if status changed
            return new_status != old_status

        except Exception as exc:
            app.logger.error(f"Error syncing request {request_id}: {exc}")
            return False


def sync_active_requests():
    """
    Sync all active requests (submitted, downloading).
    Called on page load.
    """
    with closing(get_db()) as conn:
        active = conn.execute(
            "SELECT id FROM requests WHERE status IN ('submitted', 'downloading')"
        ).fetchall()

    changed_count = 0
    for req in active:
        if sync_request_status(req["id"]):
            changed_count += 1

    return changed_count
```

---

### 3. Page Load Sync

**File:** `app/app.py` - Update `list_requests()` route

```python
@app.route("/")
@app.route("/requests")
@login_required
def list_requests():
    user = get_current_user()

    # Sync active requests before displaying
    sync_active_requests()

    # Build query based on user role
    if user["is_admin"]:
        query = """
            SELECT id, artist_name, album_title, note, status,
                   created_at, updated_at, username, last_error,
                   lidarr_artist_id, total_albums, downloaded_albums
            FROM requests
            ORDER BY id DESC
        """
        params = ()
    else:
        query = """
            SELECT id, artist_name, album_title, note, status,
                   created_at, updated_at, username, last_error,
                   lidarr_artist_id, total_albums, downloaded_albums
            FROM requests
            WHERE username = ?
            ORDER BY id DESC
        """
        params = (user["username"],)

    with closing(get_db()) as conn:
        rows = conn.execute(query, params).fetchall()

    # Pass media servers to template
    media_servers = {
        "plex": PLEX_URL,
        "jellyfin": JELLYFIN_URL,
        "navidrome": NAVIDROME_URL,
    }

    return render_template("requests.html", user=user, rows=rows, media_servers=media_servers)
```

---

### 4. Request Card Updates

**File:** `app/templates/components/request_card.html`

```html
{% macro request_card(req, media_servers) %}
<div class="request-card"
     data-status="{{ req.status }}"
     data-artist="{{ req.artist_name }}"
     data-album="{{ req.album_title or '' }}"
     data-note="{{ req.note or '' }}">

  <div class="card-header">
    <div class="card-title">
      <h3>{{ req.artist_name }}</h3>
      {% if req.album_title %}
      <p class="album-title">{{ req.album_title }}</p>
      {% endif %}
    </div>
    {{ status_badge(req.status) }}
  </div>

  <div class="card-body">
    {% if req.note %}
    <p class="card-note">{{ req.note }}</p>
    {% endif %}

    <!-- Download Progress (downloading status) -->
    {% if req.status == 'downloading' %}
    <div class="download-progress">
      <div class="progress-bar-container">
        {% set percent = (req.downloaded_albums / req.total_albums * 100) | int if req.total_albums > 0 else 0 %}
        <div class="progress-bar" style="width: {{ percent }}%"></div>
      </div>
      <p class="progress-text">
        📥 {{ req.downloaded_albums }} of {{ req.total_albums }} albums downloaded ({{ percent }}%)
      </p>
    </div>
    {% endif %}

    <!-- THE MONEY SHOT: Listen Now Buttons -->
    {% if req.status == 'completed' %}
    <div class="listen-now-section">
      <p class="listen-now-header">✅ Ready to Listen!</p>
      <div class="listen-now-buttons">
        {% if media_servers.plex %}
        <a href="{{ media_servers.plex }}/#!/search?query={{ req.artist_name | urlencode }}"
           target="_blank"
           class="listen-btn plex-btn">
          <span class="btn-icon">🎬</span>
          <span class="btn-label">Plex</span>
        </a>
        {% endif %}

        {% if media_servers.jellyfin %}
        <a href="{{ media_servers.jellyfin }}/#!/search?query={{ req.artist_name | urlencode }}"
           target="_blank"
           class="listen-btn jellyfin-btn">
          <span class="btn-icon">🎞️</span>
          <span class="btn-label">Jellyfin</span>
        </a>
        {% endif %}

        {% if media_servers.navidrome %}
        <a href="{{ media_servers.navidrome }}/app/#!/search/{{ req.artist_name | urlencode }}"
           target="_blank"
           class="listen-btn navidrome-btn">
          <span class="btn-icon">🎵</span>
          <span class="btn-label">Navidrome</span>
        </a>
        {% endif %}
      </div>
      {% if req.total_albums > 0 %}
      <p class="albums-complete">All {{ req.total_albums }} albums downloaded</p>
      {% endif %}
    </div>
    {% endif %}

    <!-- Existing status for already in library -->
    {% if req.status == 'existing' %}
    <div class="existing-info">
      <span class="existing-icon">✓</span>
      <div class="existing-text">
        <p>{{ req.last_error }}</p>
        {% if media_servers.plex or media_servers.jellyfin or media_servers.navidrome %}
        <div class="existing-links">
          {% if media_servers.plex %}
          <a href="{{ media_servers.plex }}/#!/search?query={{ req.artist_name | urlencode }}"
             target="_blank"
             class="media-btn plex-btn">🎬 Plex</a>
          {% endif %}
          {% if media_servers.jellyfin %}
          <a href="{{ media_servers.jellyfin }}/#!/search?query={{ req.artist_name | urlencode }}"
             target="_blank"
             class="media-btn jellyfin-btn">🎞️ Jellyfin</a>
          {% endif %}
          {% if media_servers.navidrome %}
          <a href="{{ media_servers.navidrome }}/app/#!/search/{{ req.artist_name | urlencode }}"
             target="_blank"
             class="media-btn navidrome-btn">🎵 Navidrome</a>
          {% endif %}
        </div>
        {% endif %}
      </div>
    </div>
    {% endif %}

    <!-- Error message -->
    {% if req.status == 'failed' and req.last_error %}
    <div class="error-message">
      <span class="error-icon">⚠️</span>
      <span class="error-text">{{ req.last_error }}</span>
    </div>
    {% endif %}
  </div>

  <div class="card-footer">
    <span class="card-timestamp">{{ req.created_at | format_datetime }}</span>
    <span class="card-user">{{ req.username }}</span>
  </div>
</div>
{% endmacro %}
```

---

### 5. CSS Styles

**File:** `app/templates/requests.html` (add to existing styles)

```css
/* Download Progress */
.download-progress {
  margin-top: var(--spacing-md);
  padding: var(--spacing-sm);
  background: rgba(59, 130, 246, 0.1);
  border-radius: var(--radius-md);
}

.progress-bar-container {
  width: 100%;
  height: 8px;
  background: var(--bg-secondary);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: var(--spacing-xs);
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #60a5fa);
  transition: width 0.5s ease;
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% { opacity: 1; }
  50% { opacity: 0.8; }
  100% { opacity: 1; }
}

.progress-text {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  margin: 0;
  text-align: center;
}

/* THE MONEY SHOT: Listen Now Section */
.listen-now-section {
  margin-top: var(--spacing-md);
  padding: var(--spacing-md);
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.1));
  border: 2px solid var(--success);
  border-radius: var(--radius-lg);
  text-align: center;
}

.listen-now-header {
  font-size: var(--font-lg);
  font-weight: 700;
  color: var(--success);
  margin: 0 0 var(--spacing-md) 0;
  animation: pulse-success 2s infinite;
}

@keyframes pulse-success {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.8; }
}

.listen-now-buttons {
  display: flex;
  gap: var(--spacing-sm);
  justify-content: center;
  flex-wrap: wrap;
  margin-bottom: var(--spacing-sm);
}

.listen-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-lg);
  border-radius: var(--radius-md);
  font-weight: 600;
  font-size: var(--font-md);
  text-decoration: none;
  transition: all 0.2s;
  box-shadow: var(--shadow-sm);
  min-height: 44px; /* Touch target */
  min-width: 120px;
  justify-content: center;
}

.listen-btn:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.listen-btn:active {
  transform: translateY(0);
}

.plex-btn {
  background: linear-gradient(135deg, #e5a00d, #f0b429);
  color: white;
}

.plex-btn:hover {
  background: linear-gradient(135deg, #d69000, #e5a00d);
  color: white;
}

.jellyfin-btn {
  background: linear-gradient(135deg, #00a4dc, #00b8eb);
  color: white;
}

.jellyfin-btn:hover {
  background: linear-gradient(135deg, #0094cc, #00a4dc);
  color: white;
}

.navidrome-btn {
  background: linear-gradient(135deg, #6b46c1, #8b5cf6);
  color: white;
}

.navidrome-btn:hover {
  background: linear-gradient(135deg, #5b3ba1, #6b46c1);
  color: white;
}

.btn-icon {
  font-size: 20px;
}

.btn-label {
  font-weight: 600;
}

.albums-complete {
  font-size: var(--font-xs);
  color: var(--text-secondary);
  margin: var(--spacing-xs) 0 0 0;
}

/* Mobile Optimizations */
@media (max-width: 768px) {
  .listen-now-buttons {
    flex-direction: column;
  }

  .listen-btn {
    width: 100%;
    min-height: 56px; /* Larger touch targets on mobile */
  }
}
```

---

### 6. Status Badge Updates

**File:** `app/templates/components/status_badge.html`

```html
{% macro status_badge(status) %}
<span class="status-badge status-{{ status }}">
  {% if status == 'new' %}
    🆕 New
  {% elif status == 'submitted' %}
    🕐 Submitted
  {% elif status == 'downloading' %}
    📥 Downloading
  {% elif status == 'completed' %}
    ✅ Completed
  {% elif status == 'failed' %}
    ❌ Failed
  {% elif status == 'existing' %}
    ✓ Existing
  {% else %}
    {{ status }}
  {% endif %}
</span>
{% endmacro %}
```

**CSS:**
```css
.status-downloading {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
  border: 1px solid #3b82f6;
}

.status-completed {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
  border: 1px solid #10b981;
  font-weight: 700;
  animation: pulse-completed 2s infinite;
}

@keyframes pulse-completed {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}
```

---

## 🧪 Testing Checklist

### Sync Logic
- [ ] Submit new request → Status transitions to "submitted"
- [ ] After Lidarr starts download → Status becomes "downloading"
- [ ] Progress shows correct album counts (e.g., "3 of 10")
- [ ] When all albums done → Status becomes "completed"
- [ ] Completed request shows "Listen Now" buttons
- [ ] Each button opens correct media server
- [ ] Search query includes artist name in URL

### Edge Cases
- [ ] Request for single album → Can go straight to "completed"
- [ ] Request for large discography → Shows progress accurately
- [ ] Lidarr API down → Sync fails gracefully, no crashes
- [ ] Artist not monitored → Stays as "submitted"
- [ ] Partial downloads → Shows correct progress percentage

### UI/UX
- [ ] Progress bar animates smoothly
- [ ] Button colors correct (Plex=orange, Jellyfin=blue, Navidrome=purple)
- [ ] Mobile: buttons stack vertically, large touch targets
- [ ] Desktop: buttons horizontal, hover effects work
- [ ] Completed animation plays (pulse effect)

---

## 🚀 Implementation Steps

### Step 1: Database Migration (15 min)
1. Create `db/migrations/003_add_download_tracking.sql`
2. Add `total_albums`, `downloaded_albums`, `last_sync_at` columns
3. Run migration on database

### Step 2: Sync Function (45 min)
4. Implement `sync_request_status()` function
5. Implement `sync_active_requests()` function
6. Add Lidarr API calls for artist + album data
7. Test status transitions with real data

### Step 3: UI Updates (30 min)
8. Update request card template with progress bar
9. Add "Listen Now" section with buttons
10. Update status badge macro
11. Add CSS styles for all new elements

### Step 4: Integration (15 min)
12. Call `sync_active_requests()` in `list_requests()` route
13. Pass media_servers to template
14. Test end-to-end flow

### Step 5: Polish (15 min)
15. Add animations (progress bar shimmer, completed pulse)
16. Mobile responsive testing
17. Error handling edge cases

**Total: 1.5-2 hours**

---

## 📊 Success Metrics

**User Satisfaction:**
- Users see progress instead of mystery
- Know when music is ready
- One-click access to listening

**Technical:**
- Sync completes in < 2 seconds per page load
- Status accuracy > 95%
- No failed syncs due to timeouts

**Business:**
- Increased engagement (users check back more)
- Reduced support questions ("Is it ready yet?")
- Higher satisfaction scores

---

## 🎯 The Money Shot in Action

**What the user sees:**

```
10 minutes after submitting:
┌─────────────────────────────────────┐
│ Pink Floyd - The Wall               │
│ 📥 Downloading                      │
│ ████████░░░░░░░░ 4 of 10 albums    │
└─────────────────────────────────────┘

30 minutes later:
┌─────────────────────────────────────┐
│ Pink Floyd - The Wall               │
│ 📥 Downloading                      │
│ ████████████████ 10 of 10 albums   │
└─────────────────────────────────────┘

Page refresh:
┌─────────────────────────────────────┐
│ Pink Floyd - The Wall               │
│ ✅ Ready to Listen!                 │
│                                     │
│ [🎬 Open in Plex] ← CLICK THIS!    │
│                                     │
└─────────────────────────────────────┘

*Click* → Music starts playing! 🎉🎵
```

**THAT'S the money shot!**

---

## 🔮 Future Enhancements

1. **Auto-refresh**: WebSocket or polling for real-time updates
2. **Notifications**: Browser notification when completed
3. **Email**: Send email when download completes
4. **Deep links**: Link directly to album, not search
5. **Album artwork**: Show cover art for completed albums
6. **Download speed**: Show estimated time remaining

---

## 💰 Why This is Critical

This completes the **full user journey**:
1. ✅ Request music (easy form)
2. ✅ Check for duplicates (no wasted requests)
3. ✅ See progress (transparency)
4. ✅ **Listen immediately** (THE PAYOFF!)

Without #4, users request music and then... what? They don't know when it's ready or how to listen. **This is what makes the whole app worth using!**

---

**Ready to implement THE MONEY SHOT?** 🎯💰

This is the feature that will make users **love** your app!
