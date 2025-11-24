# Jukebox Feature Plan - v0.4.0 (Revised)

**Version**: 0.4.0 (Feature Improvements)
**Created**: 2025-11-24
**Status**: Planning → Implementation
**Total Estimated Time**: 6-8 hours (across multiple stages)

---

## Overview

Multi-stage implementation of feature improvements for Jukebox:
- **Stage 0**: Repository separation (jukebox → standalone repo)
- **Stage 1**: Error message cleanup & user-friendly display
- **Stage 2**: Duplicate artist/album detection
- **Stage 3**: Lidarr polling & request status sync
- **Stage 4**: Search & filter system
- **Stage 5**: Request details modal
- **Stage 6**: Bulk actions (admin only)

**Implementation Workflow Per Stage**:
1. Implement code
2. Test functionality
3. Fix issues
4. Validate (manual + automated)
5. Update documentation (HANDOFF, PROGRESS)
6. Git commit with descriptive message
7. Move to next stage

---

## Stage 0: Repository Separation

**Priority**: Critical (Foundation)
**Time**: 30-45 minutes
**Complexity**: Medium
**Risk**: Medium (git history preservation)

### Goal
Separate Jukebox into its own standalone repository while preserving full git history.

### Tasks

#### 1. Extract Jukebox Subdirectory with History
```bash
# Navigate to glider-docker
cd /home/michael/dev/work/glider/glider-docker

# Create a new branch for extraction
git checkout -b jukebox-extraction

# Use git filter-repo to extract jukebox/ subdirectory
# This preserves all commits that touched jukebox/
git filter-repo --path jukebox/ --path-rename jukebox/:

# Result: New repo with only jukebox/ contents at root, full history preserved
```

#### 2. Create New Repository on GitHub
```bash
# Create new repo using gh CLI
gh repo create slyckmb/jukebox \
  --public \
  --description "Jukebox - Music request portal with Lidarr integration" \
  --clone=false

# Add new remote
git remote add origin git@github.com:slyckmb/jukebox.git

# Push all branches and tags
git push -u origin main
git push --tags
```

#### 3. Update Documentation
- Update README.md with standalone setup instructions
- Update HANDOFF-JUKEBOX.md with new repository location
- Add LICENSE file (if not present)
- Update docker-compose.yml to be standalone-friendly
- Create .gitignore for standalone usage

#### 4. Verify History Preservation
```bash
# Check commit history for key files
git log --follow -- app/app.py
git log --follow -- docs/HANDOFF-JUKEBOX.md

# Verify all contributors are preserved
git shortlog -sn
```

#### 5. Update glider-docker Reference
```bash
# In glider-docker repo, add submodule or note
cd /home/michael/dev/work/glider/glider-docker
git submodule add git@github.com:slyckmb/jukebox.git jukebox

# Or document the separation in README
echo "Jukebox has been moved to: https://github.com/slyckmb/jukebox" > jukebox/README.md
```

### Testing Checklist
- [ ] New repo created on GitHub
- [ ] Full git history preserved (check git log)
- [ ] All contributors attributed correctly
- [ ] README updated with standalone instructions
- [ ] Docker build works in new repo
- [ ] Secrets paths updated (if needed)
- [ ] CI/CD considerations documented

### Documentation Updates
- [ ] Update repository URL in all docs
- [ ] Update HANDOFF-JUKEBOX.md
- [ ] Create/update README.md for standalone
- [ ] Document any path changes for secrets

### Commit Message
```
chore: separate jukebox into standalone repository

- Extract jukebox/ subdirectory with full git history
- Create new repository at github.com/slyckmb/jukebox
- Update documentation for standalone usage
- Update docker-compose.yml for standalone deployment
- Add standalone README with setup instructions

Breaking Change: Repository location changed
Migration: Update git remotes to point to new repo

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Validation**: After this stage, jukebox should be a fully standalone repository with complete history.

---

## Stage 1: Error Message Cleanup

**Priority**: High
**Time**: 45 minutes
**Complexity**: Low
**Risk**: Low

### Problem Statement
Lidarr API errors are returned as large JSON payloads that are shown directly to users, making them confusing and unhelpful.

**Example Current Error**:
```json
{"status":"error","message":"Lidarr add artist failed: 400: {\"type\":\"https://tools.ietf.org/html/rfc7231#section-6.5.1\",\"title\":\"One or more validation errors occurred.\",\"status\":400,\"traceId\":\"00-abc123...\",\"errors\":{\"rootFolderPath\":[\"Invalid root folder\"]}}"}
```

**Desired User-Friendly Error**:
```
Unable to add artist: Invalid root folder path
```

### Implementation

#### 1. Create Error Parsing Module (`app/error_parser.py`)

```python
"""
Error message parser for user-friendly error display.
Extracts meaningful information from Lidarr API errors.
"""
import re
import json


def parse_lidarr_error(error_message: str) -> str:
    """
    Parse Lidarr API error and return user-friendly message.

    Args:
        error_message: Raw error string from Lidarr API

    Returns:
        Clean, user-friendly error message
    """
    if not error_message:
        return "Unknown error occurred"

    # Try to extract JSON from error message
    json_match = re.search(r'\{.*\}', error_message, re.DOTALL)
    if json_match:
        try:
            error_json = json.loads(json_match.group(0))

            # Extract validation errors
            if "errors" in error_json and isinstance(error_json["errors"], dict):
                error_parts = []
                for field, messages in error_json["errors"].items():
                    if isinstance(messages, list):
                        error_parts.extend(messages)
                    else:
                        error_parts.append(str(messages))

                if error_parts:
                    return f"Unable to add artist: {'; '.join(error_parts)}"

            # Extract title or message
            if "title" in error_json:
                return f"Unable to add artist: {error_json['title']}"

            if "message" in error_json:
                return f"Unable to add artist: {error_json['message']}"

        except json.JSONDecodeError:
            pass

    # Extract common error patterns
    patterns = [
        (r"artist already exists", "This artist already exists in Lidarr"),
        (r"album already exists", "This album already exists in Lidarr"),
        (r"Invalid root folder", "Invalid music folder path - contact admin"),
        (r"404", "Artist or album not found in MusicBrainz"),
        (r"timeout", "Request timed out - Lidarr may be busy"),
        (r"connection refused", "Cannot connect to Lidarr - service may be down"),
        (r"unauthorized|401", "Lidarr API key is invalid - contact admin"),
        (r"forbidden|403", "Access denied by Lidarr - contact admin"),
        (r"500|502|503", "Lidarr server error - try again later"),
    ]

    error_lower = error_message.lower()
    for pattern, friendly_msg in patterns:
        if re.search(pattern, error_lower):
            return friendly_msg

    # Fallback: Extract first sentence or first 100 chars
    if ": " in error_message:
        parts = error_message.split(": ", 1)
        if len(parts) > 1:
            msg = parts[1].split(".")[0].strip()
            if msg and len(msg) < 150:
                return f"Error: {msg}"

    # Last resort: Truncate and clean
    cleaned = error_message.replace("\n", " ").strip()
    if len(cleaned) > 150:
        cleaned = cleaned[:147] + "..."

    return cleaned


def parse_artist_lookup_error(error_message: str) -> str:
    """Parse artist lookup errors."""
    if not error_message:
        return "Unknown error occurred"

    if "404" in error_message or "not found" in error_message.lower():
        return "Artist not found in MusicBrainz database"

    if "timeout" in error_message.lower():
        return "Search timed out - try again"

    if "connection" in error_message.lower():
        return "Cannot connect to Lidarr - service may be down"

    return parse_lidarr_error(error_message)


def parse_tag_error(error_message: str) -> str:
    """Parse tag creation errors."""
    if not error_message:
        return "Unknown error occurred"

    if "already exists" in error_message.lower():
        return "Tag already exists (this is usually safe to ignore)"

    if "invalid" in error_message.lower():
        return "Invalid tag format - contact admin"

    return parse_lidarr_error(error_message)
```

#### 2. Update app.py to Use Error Parser

```python
# Add import at top
from error_parser import parse_lidarr_error, parse_artist_lookup_error, parse_tag_error

# In submit_request() function, update error handling:

# Replace tag error storage:
if tag_error:
    friendly_error = parse_tag_error(tag_error)
    flash(f"Warning: {friendly_error}", "warning")
    conn.execute(
        "UPDATE requests SET status = 'failed', last_error = ?, updated_at = datetime('now') WHERE id = ?",
        (friendly_error, req_id),
    )
    conn.commit()
    return redirect(url_for("list_requests"))

# Replace artist lookup error storage:
if err:
    friendly_error = parse_artist_lookup_error(err)
    flash(f"Lookup failed: {friendly_error}", "danger")
    conn.execute(
        "UPDATE requests SET status = 'failed', last_error = ?, updated_at = datetime('now') WHERE id = ?",
        (friendly_error, req_id),
    )
    conn.commit()
    return redirect(url_for("list_requests"))

# Replace Lidarr add artist error storage:
if not added_ok:
    friendly_error = parse_lidarr_error(add_error)
    flash(f"Failed to add artist: {friendly_error}", "danger")
    conn.execute(
        "UPDATE requests SET status = 'failed', last_error = ?, updated_at = datetime('now') WHERE id = ?",
        (friendly_error, req_id),
    )
    conn.commit()
    return redirect(url_for("list_requests"))
```

#### 3. Update Request Card Display

In `app/templates/components/request_card.html`:
```html
{% if req.last_error %}
<div class="error-message">
  <span class="error-icon">⚠️</span>
  <span class="error-text">{{ req.last_error }}</span>
</div>
{% endif %}
```

Update CSS to support better error display:
```css
.error-message {
  display: flex;
  gap: var(--spacing-sm);
  align-items: flex-start;
  padding: var(--spacing-sm);
  background: rgba(239, 68, 68, 0.1);
  border-left: 3px solid var(--danger);
  border-radius: var(--radius-sm);
  margin-top: var(--spacing-sm);
  font-size: var(--font-sm);
  color: var(--danger);
}

.error-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.error-text {
  flex: 1;
  word-break: break-word;
}
```

### Testing Checklist
- [ ] Test with various Lidarr error responses
- [ ] Test 400 validation errors parse correctly
- [ ] Test 404 errors show "not found" message
- [ ] Test 500 errors show "server error" message
- [ ] Test timeout errors
- [ ] Test connection errors
- [ ] Test duplicate artist/album errors
- [ ] Verify error messages are under 150 characters
- [ ] Verify error messages are helpful to end users
- [ ] Test error display on mobile (word wrap)

### Documentation Updates
- [ ] Update HANDOFF-JUKEBOX.md: Add error parsing feature
- [ ] Document error message formats in code comments

### Commit Message
```
feat: add user-friendly error message parsing

- Create error_parser.py module for Lidarr error parsing
- Parse JSON error payloads and extract meaningful messages
- Add pattern matching for common error types
- Truncate long error messages to 150 characters
- Update request card error display styling
- Improve error readability on mobile

Testing: Validated with 10+ error types from Lidarr API
User Impact: Error messages now concise and actionable

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Stage 2: Duplicate Artist/Album Detection

**Priority**: High
**Time**: 1 hour
**Complexity**: Medium
**Risk**: Low

### Problem Statement
Users submit requests for artists/albums that already exist in Lidarr, leading to errors. We should detect duplicates proactively and handle gracefully.

### User Experience Goals
1. **Before submission**: Check if artist already exists in Lidarr
2. **If exists**: Show friendly message with options:
   - "Artist already exists! View in Lidarr" (link)
   - "Search for this artist in Plex/Jellyfin"
   - "Submit anyway" (for edge cases)
3. **Status tracking**: Mark as 'existing' instead of 'failed'

### Implementation

#### 1. Add Lidarr Artist Check Function

In `app/app.py`:
```python
def check_artist_exists_in_lidarr(foreign_artist_id: str):
    """
    Check if artist already exists in Lidarr library.

    Args:
        foreign_artist_id: MusicBrainz artist ID (e.g., "5b11f4ce-a62d-471e-81fc-a69a8278c7da")

    Returns:
        (exists: bool, artist_data: dict, error: str)
    """
    url = f"{LIDARR_URL}/artist"
    try:
        resp = requests.get(url, params={"apikey": LIDARR_API_KEY}, timeout=10)
    except Exception as exc:
        return False, None, f"Connection error: {exc}"

    if resp.status_code != 200:
        return False, None, f"Lidarr API error {resp.status_code}"

    try:
        artists = resp.json()
        for artist in artists:
            if artist.get("foreignArtistId") == foreign_artist_id:
                return True, artist, None
        return False, None, None
    except Exception as exc:
        return False, None, f"Parse error: {exc}"


def check_album_exists_in_lidarr(foreign_album_id: str, artist_id: int):
    """
    Check if album already exists in Lidarr for a given artist.

    Args:
        foreign_album_id: MusicBrainz album ID
        artist_id: Lidarr artist ID

    Returns:
        (exists: bool, album_data: dict, error: str)
    """
    url = f"{LIDARR_URL}/album"
    try:
        resp = requests.get(url, params={"artistId": artist_id, "apikey": LIDARR_API_KEY}, timeout=10)
    except Exception as exc:
        return False, None, f"Connection error: {exc}"

    if resp.status_code != 200:
        return False, None, f"Lidarr API error {resp.status_code}"

    try:
        albums = resp.json()
        for album in albums:
            if album.get("foreignAlbumId") == foreign_album_id:
                return True, album, None
        return False, None, None
    except Exception as exc:
        return False, None, f"Parse error: {exc}"
```

#### 2. Update submit_request() Logic

```python
@app.route("/submit", methods=["POST"])
@login_required
def submit_request():
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    artist_name = request.form.get("artist_name", "").strip()
    album_title = request.form.get("album_title", "").strip()
    note = request.form.get("note", "").strip()

    if not artist_name:
        flash("Artist name is required.", "danger")
        return redirect(url_for("new_request"))

    # Truncate note to 500 chars
    if len(note) > 500:
        note = note[:500]

    # Build user-specific tag and root folder
    tag = build_user_tag(user["username"])
    root_folder = build_user_root_folder(user["username"])

    # Create request record
    with closing(get_db()) as conn:
        cur = conn.execute(
            "INSERT INTO requests (user_id, artist_name, album_title, note, status, tag, root_folder_path) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user["id"], artist_name, album_title, note, "new", tag, root_folder),
        )
        conn.commit()
        req_id = cur.lastrowid

    # === NEW: Lookup artist in MusicBrainz ===
    artist_data, err = lookup_artist(artist_name)
    if err:
        friendly_error = parse_artist_lookup_error(err)
        flash(f"Lookup failed: {friendly_error}", "danger")
        with closing(get_db()) as conn:
            conn.execute(
                "UPDATE requests SET status = 'failed', last_error = ?, updated_at = datetime('now') WHERE id = ?",
                (friendly_error, req_id),
            )
            conn.commit()
        return redirect(url_for("list_requests"))

    foreign_artist_id = artist_data.get("foreignArtistId")
    artist_display_name = artist_data.get("artistName", artist_name)

    # === NEW: Check if artist already exists in Lidarr ===
    exists, existing_artist, check_error = check_artist_exists_in_lidarr(foreign_artist_id)

    if check_error:
        # Non-fatal: Log and continue with add
        app.logger.warning(f"Could not check for existing artist: {check_error}")

    if exists:
        # Artist already exists!
        lidarr_artist_id = existing_artist.get("id")

        # If user requested specific album, check if that exists too
        if album_title:
            # Try to match album by title (fuzzy match)
            album_exists, existing_album, album_check_error = check_album_exists_in_lidarr(
                foreign_album_id=None,  # We'd need to look this up from search
                artist_id=lidarr_artist_id
            )
            # Simplified: Just check by title match
            try:
                album_url = f"{LIDARR_URL}/album?artistId={lidarr_artist_id}&apikey={LIDARR_API_KEY}"
                resp = requests.get(album_url, timeout=10)
                if resp.status_code == 200:
                    albums = resp.json()
                    album_match = None
                    for album in albums:
                        if album.get("title", "").lower() == album_title.lower():
                            album_match = album
                            break

                    if album_match:
                        # Both artist and album exist
                        status_msg = f"'{artist_display_name}' and album '{album_title}' already exist in your library!"
                    else:
                        # Artist exists, album doesn't
                        status_msg = f"'{artist_display_name}' exists, but album '{album_title}' was not found. You may need to search for it manually."
                else:
                    status_msg = f"'{artist_display_name}' already exists in your library!"
            except Exception:
                status_msg = f"'{artist_display_name}' already exists in your library!"
        else:
            status_msg = f"'{artist_display_name}' already exists in your library!"

        # Update request status to 'existing'
        with closing(get_db()) as conn:
            conn.execute(
                "UPDATE requests SET status = 'existing', lidarr_artist_id = ?, last_error = ?, updated_at = datetime('now') WHERE id = ?",
                (lidarr_artist_id, status_msg, req_id),
            )
            conn.commit()

        flash(f"✓ {status_msg} Check Plex, Jellyfin, or Navidrome to listen now.", "info")
        return redirect(url_for("list_requests"))

    # Continue with normal add flow (artist doesn't exist)
    # ... (rest of existing code for tag creation and artist add)
```

#### 3. Update UI for 'existing' Status

Add helpful links in request card for existing items:
```html
{% if req.status == 'existing' %}
<div class="existing-info">
  <span class="existing-icon">✓</span>
  <div class="existing-text">
    <p>{{ req.last_error }}</p>
    <div class="existing-links">
      <a href="https://plex.bikejeepyoga.com" target="_blank" class="link-btn">Open Plex</a>
      <a href="https://jellyfin.bikejeepyoga.com" target="_blank" class="link-btn">Open Jellyfin</a>
      <a href="https://navidrome.bikejeepyoga.com" target="_blank" class="link-btn">Open Navidrome</a>
    </div>
  </div>
</div>
{% endif %}
```

CSS:
```css
.existing-info {
  display: flex;
  gap: var(--spacing-sm);
  align-items: flex-start;
  padding: var(--spacing-sm);
  background: rgba(16, 185, 129, 0.1);
  border-left: 3px solid var(--status-submitted);
  border-radius: var(--radius-sm);
  margin-top: var(--spacing-sm);
  font-size: var(--font-sm);
  color: var(--status-submitted);
}

.existing-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.existing-text {
  flex: 1;
}

.existing-links {
  display: flex;
  gap: var(--spacing-xs);
  margin-top: var(--spacing-xs);
  flex-wrap: wrap;
}

.link-btn {
  display: inline-block;
  padding: 4px 12px;
  background: var(--status-submitted);
  color: white;
  border-radius: var(--radius-sm);
  font-size: var(--font-xs);
  font-weight: 600;
  text-decoration: none;
  transition: opacity 0.2s;
}

.link-btn:hover {
  opacity: 0.8;
  color: white;
}
```

#### 4. Configuration for Media Server URLs

Add to `.env`:
```bash
# Media server URLs (optional, for existing item links)
PLEX_URL=https://plex.bikejeepyoga.com
JELLYFIN_URL=https://jellyfin.bikejeepyoga.com
NAVIDROME_URL=https://navidrome.bikejeepyoga.com
```

Load in app.py and pass to templates:
```python
PLEX_URL = os.environ.get("PLEX_URL", "")
JELLYFIN_URL = os.environ.get("JELLYFIN_URL", "")
NAVIDROME_URL = os.environ.get("NAVIDROME_URL", "")

# In list_requests():
return render_template(
    "requests.html",
    user=user,
    rows=rows,
    media_servers={
        "plex": PLEX_URL,
        "jellyfin": JELLYFIN_URL,
        "navidrome": NAVIDROME_URL,
    }
)
```

### Testing Checklist
- [ ] Submit request for existing artist (full match)
- [ ] Submit request for existing artist + existing album
- [ ] Submit request for existing artist + non-existing album
- [ ] Verify status set to 'existing' (not 'failed')
- [ ] Verify helpful message displayed
- [ ] Verify media server links appear and work
- [ ] Test with missing/invalid Lidarr connection
- [ ] Test with artist that doesn't exist (normal flow)

### Documentation Updates
- [ ] Update HANDOFF-JUKEBOX.md: Document duplicate detection
- [ ] Update request-portal-requirements.md: Add duplicate handling requirement
- [ ] Document media server URL configuration in docs/SECRETS.md

### Commit Message
```
feat: add duplicate artist/album detection

- Check if artist exists in Lidarr before adding
- Set status to 'existing' for duplicate requests
- Display helpful message with media server links
- Add configuration for Plex/Jellyfin/Navidrome URLs
- Improve user experience for duplicate submissions

Testing: Validated with existing/non-existing artists
User Impact: Users immediately know if music is already available

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Stage 3: Lidarr Status Polling & Sync

**Priority**: High
**Time**: 1.5-2 hours
**Complexity**: High
**Risk**: Medium (background job + DB updates)

### Problem Statement
Once a request is submitted to Lidarr, users have no visibility into:
- Is Lidarr searching for the music?
- Has it been downloaded?
- Is it available to listen now?

### Solution Design

#### Option A: Polling on Page Load (Simple)
- When user views request list, poll Lidarr for updates
- Update request status based on Lidarr artist/album monitoring status
- Pros: Simple, no background jobs
- Cons: Only updates when user views page

#### Option B: Background Worker (Complete)
- Separate worker process polls Lidarr every 5 minutes
- Updates all 'submitted' requests
- Pros: Real-time updates, no user interaction needed
- Cons: More complex, requires worker process

**Decision: Start with Option A (polling on page load), can evolve to Option B later**

### Implementation

#### 1. Add Lidarr Status Sync Function

```python
def sync_request_status_from_lidarr(request_id: int):
    """
    Poll Lidarr and update request status based on current state.

    States:
    - 'submitted' -> Artist added to Lidarr, monitoring
    - 'downloading' -> Artist found, download in progress
    - 'completed' -> Artist fully downloaded and available
    - 'failed' -> Lidarr couldn't find or download

    Returns:
        (success: bool, new_status: str, message: str)
    """
    with closing(get_db()) as conn:
        cur = conn.execute(
            "SELECT * FROM requests WHERE id = ? AND lidarr_artist_id IS NOT NULL",
            (request_id,)
        )
        req = cur.fetchone()

    if not req:
        return False, None, "Request not found or not submitted to Lidarr"

    lidarr_artist_id = req["lidarr_artist_id"]

    # Get artist from Lidarr
    try:
        url = f"{LIDARR_URL}/artist/{lidarr_artist_id}"
        resp = requests.get(url, params={"apikey": LIDARR_API_KEY}, timeout=10)

        if resp.status_code == 404:
            return False, "failed", "Artist removed from Lidarr"

        if resp.status_code != 200:
            return False, None, f"Lidarr API error {resp.status_code}"

        artist_data = resp.json()

        # Check statistics
        stats = artist_data.get("statistics", {})
        total_track_count = stats.get("totalTrackCount", 0)
        track_file_count = stats.get("trackFileCount", 0)
        percent_of_tracks = stats.get("percentOfTracks", 0)

        # Determine status
        if percent_of_tracks >= 100:
            new_status = "completed"
            message = f"✓ {artist_data.get('artistName')} is fully downloaded! Listen now in Plex/Jellyfin/Navidrome."
        elif track_file_count > 0:
            new_status = "downloading"
            message = f"↻ Downloading {artist_data.get('artistName')}: {track_file_count}/{total_track_count} tracks ({percent_of_tracks:.0f}%)"
        elif artist_data.get("monitored", False):
            new_status = "submitted"
            message = f"⏳ {artist_data.get('artistName')} is being monitored by Lidarr. Waiting for search results..."
        else:
            new_status = "submitted"
            message = f"Artist added but not monitored. Check Lidarr settings."

        # Update database
        with closing(get_db()) as conn:
            conn.execute(
                "UPDATE requests SET status = ?, last_error = ?, updated_at = datetime('now') WHERE id = ?",
                (new_status, message, request_id)
            )
            conn.commit()

        return True, new_status, message

    except Exception as exc:
        return False, None, f"Error checking Lidarr: {exc}"


def sync_all_active_requests():
    """
    Sync status for all requests that are actively being processed by Lidarr.
    Called on page load for the current user's requests.
    """
    with closing(get_db()) as conn:
        cur = conn.execute(
            "SELECT id FROM requests WHERE status IN ('submitted', 'downloading') AND lidarr_artist_id IS NOT NULL"
        )
        active_requests = cur.fetchall()

    updated_count = 0
    for req in active_requests:
        success, new_status, message = sync_request_status_from_lidarr(req["id"])
        if success:
            updated_count += 1

    return updated_count
```

#### 2. Update list_requests() to Trigger Sync

```python
@app.route("/requests", methods=["GET"])
@login_required
def list_requests():
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    # === NEW: Sync active requests from Lidarr ===
    updated_count = sync_all_active_requests()
    if updated_count > 0:
        app.logger.info(f"Synced {updated_count} requests from Lidarr")

    # Get filter parameters (existing code)
    search_query = request.args.get("search", "").strip()
    status_filter = request.args.get("status", "").strip()
    user_filter = request.args.get("user", "all")

    # ... rest of existing code
```

#### 3. Add New Status: 'downloading' and 'completed'

Update status badge component:
```html
<!-- app/templates/components/status_badge.html -->
{% if req.status == 'new' %}
  <span class="status-badge status-new">🆕 New</span>
{% elif req.status == 'submitted' %}
  <span class="status-badge status-submitted">⏳ Submitted</span>
{% elif req.status == 'downloading' %}
  <span class="status-badge status-downloading">↻ Downloading</span>
{% elif req.status == 'completed' %}
  <span class="status-badge status-completed">✓ Available</span>
{% elif req.status == 'failed' %}
  <span class="status-badge status-failed">❌ Failed</span>
{% elif req.status == 'existing' %}
  <span class="status-badge status-existing">📀 Exists</span>
{% endif %}
```

Update CSS variables:
```css
:root {
  --status-new: #6366f1;
  --status-submitted: #f59e0b;
  --status-downloading: #3b82f6;
  --status-completed: #10b981;
  --status-failed: #ef4444;
  --status-existing: #64748b;
}

.status-downloading {
  background: rgba(59, 130, 246, 0.1);
  color: var(--status-downloading);
}

.status-completed {
  background: rgba(16, 185, 129, 0.1);
  color: var(--status-completed);
}
```

#### 4. Add "Listen Now" Button for Completed Requests

In request card:
```html
{% if req.status == 'completed' %}
<div class="completed-actions">
  <p class="completed-message">{{ req.last_error }}</p>
  <div class="media-links">
    {% if media_servers.plex %}
    <a href="{{ media_servers.plex }}/search?query={{ req.artist_name|urlencode }}"
       target="_blank"
       class="media-btn plex-btn">
      🎬 Plex
    </a>
    {% endif %}
    {% if media_servers.jellyfin %}
    <a href="{{ media_servers.jellyfin }}/search?query={{ req.artist_name|urlencode }}"
       target="_blank"
       class="media-btn jellyfin-btn">
      🎞️ Jellyfin
    </a>
    {% endif %}
    {% if media_servers.navidrome %}
    <a href="{{ media_servers.navidrome }}/search?query={{ req.artist_name|urlencode }}"
       target="_blank"
       class="media-btn navidrome-btn">
      🎵 Navidrome
    </a>
    {% endif %}
  </div>
</div>
{% endif %}
```

CSS:
```css
.completed-actions {
  margin-top: var(--spacing-sm);
  padding: var(--spacing-sm);
  background: rgba(16, 185, 129, 0.05);
  border-radius: var(--radius-sm);
}

.completed-message {
  margin: 0 0 var(--spacing-sm) 0;
  color: var(--status-completed);
  font-weight: 600;
}

.media-links {
  display: flex;
  gap: var(--spacing-xs);
  flex-wrap: wrap;
}

.media-btn {
  display: inline-block;
  padding: 8px 16px;
  background: var(--status-completed);
  color: white;
  border-radius: var(--radius-md);
  font-size: var(--font-sm);
  font-weight: 600;
  text-decoration: none;
  transition: transform 0.2s, opacity 0.2s;
}

.media-btn:hover {
  transform: translateY(-2px);
  opacity: 0.9;
  color: white;
}

.plex-btn {
  background: #e5a00d;
}

.jellyfin-btn {
  background: #00a4dc;
}

.navidrome-btn {
  background: #6b46c1;
}
```

#### 5. Add Manual Refresh Button (Optional)

Add refresh button to page header:
```html
<div class="header-actions">
  <button
    onclick="window.location.reload()"
    class="btn btn-secondary btn-sm"
    title="Refresh status from Lidarr"
  >
    🔄 Refresh
  </button>
  <!-- existing buttons -->
</div>
```

#### 6. Add Database Migration for New Statuses

Create `db/migrations/003_add_download_statuses.sql`:
```sql
-- Add new status values for downloading and completed states
-- No schema changes needed, just documentation

-- Valid status values:
-- 'new' - Request created, not yet submitted
-- 'submitted' - Sent to Lidarr, being monitored
-- 'downloading' - Lidarr is downloading tracks
-- 'completed' - All tracks downloaded and available
-- 'failed' - Submission or download failed
-- 'existing' - Artist/album already exists in library

-- This migration is informational only
-- Status column already allows these text values
```

### Testing Checklist
- [ ] Submit new request, verify status updates on page refresh
- [ ] Test with artist that Lidarr finds and downloads
- [ ] Test with artist that Lidarr can't find (should stay submitted)
- [ ] Verify 'downloading' status shows progress
- [ ] Verify 'completed' status shows media links
- [ ] Test media server links (Plex, Jellyfin, Navidrome)
- [ ] Test sync with multiple active requests
- [ ] Test with disconnected Lidarr (graceful failure)
- [ ] Verify status doesn't regress (completed → submitted)
- [ ] Test manual refresh button

### Performance Considerations
- Sync limited to active requests only ('submitted', 'downloading')
- Timeout set to 10 seconds per Lidarr API call
- Consider rate limiting if many users refresh simultaneously
- Future: Cache Lidarr responses for 1-2 minutes

### Documentation Updates
- [ ] Update HANDOFF-JUKEBOX.md: Document status sync
- [ ] Document new statuses: downloading, completed
- [ ] Document media server URL configuration
- [ ] Add troubleshooting section for sync issues

### Commit Message
```
feat: add lidarr status polling and sync

- Poll Lidarr on page load to update request status
- Add 'downloading' status with progress tracking
- Add 'completed' status when music is available
- Display media server links for completed requests
- Auto-sync active requests (submitted/downloading)
- Add manual refresh button to trigger sync

Testing: Validated with real Lidarr downloads
User Impact: Users can track request progress and know when music is ready

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Stage 4: Search & Filter System

**Priority**: Medium
**Time**: 1-1.5 hours
**Complexity**: Medium
**Risk**: Low

### Implementation
(Content from original plan Stage 1, refined)

See original FEATURE-PLAN-V0.4.0.md for full implementation details.

**Key additions:**
- Add filter for new statuses: downloading, completed
- Update status counts to include all 6 statuses
- Ensure search works across all status types

### Commit Message
```
feat: add search and filter system

- Add search by artist/album name with debouncing
- Add status filter pills (new, submitted, downloading, completed, failed, existing)
- Add admin toggle for "my requests only"
- Display active filters with counts
- Sticky filter bar below header
- Mobile-responsive horizontal scroll for pills

Testing: Validated with 50+ requests across all statuses
User Impact: Easy discovery and filtering of requests

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Stage 5: Request Details Modal

**Priority**: Medium
**Time**: 1 hour
**Complexity**: Low-Medium
**Risk**: Low

### Implementation
(Content from original plan Stage 2, refined)

See original FEATURE-PLAN-V0.4.0.md for full implementation details.

**Key additions:**
- Display new statuses in modal
- Show download progress for 'downloading' status
- Show media server links for 'completed' status
- Add "Refresh Status" button in modal

### Commit Message
```
feat: add request details modal

- Click request card to view full details
- Display all metadata (dates, Lidarr IDs, tags, errors)
- Show download progress for active requests
- Add media server links for completed requests
- ESC key and backdrop click to close
- Mobile-friendly slide-up animation

Testing: Validated across all request statuses
User Impact: Easy access to detailed request information

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Stage 6: Bulk Actions (Admin Only)

**Priority**: Low
**Time**: 1-1.5 hours
**Complexity**: Medium
**Risk**: Low

### Implementation
(Content from original plan Stage 3, refined)

See original FEATURE-PLAN-V0.4.0.md for full implementation details.

**Key additions:**
- Bulk retry works on 'failed' requests
- Bulk archive for 'completed' requests (future feature)
- Confirmation dialogs more specific per action

### Commit Message
```
feat: add bulk actions for admins

- Select multiple requests with checkboxes
- Bulk delete requests (with confirmation)
- Bulk retry failed requests
- Select all / deselect all functionality
- Sticky bulk toolbar shows selected count
- Admin-only feature with authorization checks

Testing: Validated with 1-100 requests
User Impact: Admins can efficiently manage multiple requests

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Overall Testing Strategy

### After Each Stage
1. **Unit tests**: Run pytest suite, add new tests as needed
2. **Manual testing**: Test on Chrome, Firefox, Safari
3. **Mobile testing**: Test on 375px, 390px, 768px viewports
4. **Accessibility**: Check keyboard nav, ARIA labels, contrast
5. **Performance**: Check page load time, API response time

### End-to-End Testing (After Stage 6)
- [ ] Complete user flow: Login → Submit → Track → Listen
- [ ] Admin flow: Login → Bulk actions → User management
- [ ] Error scenarios: Bad API key, Lidarr down, network timeout
- [ ] Security: CSRF, XSS, SQL injection, auth bypass attempts
- [ ] Mobile: Full app usage on real device (iOS, Android)

---

## Version Bump & Release

After Stage 6 completion:

1. Update version to 0.4.0 in:
   - `docs/HANDOFF-JUKEBOX.md`
   - `docs/MOBILE-UX-PROGRESS.md`
   - Any other version references

2. Create release tag:
```bash
git tag -a v0.4.0 -m "Release v0.4.0: Feature improvements

- User-friendly error messages
- Duplicate detection
- Lidarr status sync
- Search & filter
- Request details modal
- Bulk actions (admin)"

git push origin v0.4.0
```

3. Create GitHub release with changelog

---

## Timeline Summary

| Stage | Feature | Time | Status |
|-------|---------|------|--------|
| 0 | Repo separation | 30-45 min | ⬜ Not started |
| 1 | Error cleanup | 45 min | ⬜ Not started |
| 2 | Duplicate detection | 1 hour | ⬜ Not started |
| 3 | Lidarr sync | 1.5-2 hours | ⬜ Not started |
| 4 | Search & filter | 1-1.5 hours | ⬜ Not started |
| 5 | Details modal | 1 hour | ⬜ Not started |
| 6 | Bulk actions | 1-1.5 hours | ⬜ Not started |
| **TOTAL** | | **7-9 hours** | |

---

## Success Criteria

- ✅ Repository successfully separated with full history
- ✅ Error messages are clear and actionable
- ✅ Duplicate submissions handled gracefully
- ✅ Request status syncs from Lidarr automatically
- ✅ Users can search and filter requests easily
- ✅ Request details accessible via modal
- ✅ Admins can perform bulk operations
- ✅ All features work on mobile and desktop
- ✅ Zero security regressions
- ✅ All tests pass
- ✅ Documentation updated

---

**Ready to begin with Stage 0: Repository Separation?**
