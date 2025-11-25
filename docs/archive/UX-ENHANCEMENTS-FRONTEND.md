# Jukebox UX Enhancements - Frontend Focus

**Date**: 2025-11-24
**Focus**: Low-complexity, high-impact frontend improvements
**Philosophy**: Make it easier for users without major backend changes

---

## 🎯 Core UX Principles

1. **Reduce Friction** - Fewer steps, less typing, smarter defaults
2. **Provide Feedback** - Show what's happening, what went wrong, what to do next
3. **Prevent Errors** - Catch mistakes before they happen
4. **Quick Actions** - Common tasks should be one tap/click
5. **Progressive Disclosure** - Show advanced features only when needed

---

## 💡 Proposed Enhancements by Complexity

### ⭐ Low Complexity (< 1 hour each)

#### 1. **Show/Hide Failed Requests Toggle**
**Complexity**: ★☆☆☆☆ (Very Low)
**Impact**: ★★★★☆ (High)
**Time**: 20-30 minutes

**Problem**: Failed requests clutter the list, but users want to keep them for reference

**Solution**: Add a toggle button in the header to show/hide failed requests

**Implementation**:
```html
<!-- In requests.html header -->
<div class="view-controls">
  <button class="btn-icon" id="toggleFailed" aria-label="Show/Hide Failed">
    <span id="failedIcon">👁️</span>
    <span class="btn-label">Hide Failed</span>
  </button>
</div>
```

```javascript
// In app.js
document.addEventListener('DOMContentLoaded', () => {
  const toggleBtn = document.getElementById('toggleFailed');
  const failedIcon = document.getElementById('failedIcon');
  let showFailed = localStorage.getItem('showFailed') !== 'false';

  function updateView() {
    const failedCards = document.querySelectorAll('[data-status="failed"]');
    failedCards.forEach(card => {
      card.style.display = showFailed ? 'block' : 'none';
    });
    failedIcon.textContent = showFailed ? '👁️' : '🚫';
    toggleBtn.querySelector('.btn-label').textContent =
      showFailed ? 'Hide Failed' : 'Show Failed';
    localStorage.setItem('showFailed', showFailed);
  }

  toggleBtn.addEventListener('click', () => {
    showFailed = !showFailed;
    updateView();
  });

  updateView(); // Initial state
});
```

**Benefits**:
- Cleaner default view (success-focused)
- Failed requests still accessible
- Preference persists across sessions
- No database changes needed

---

#### 2. **Delete Request Card (Swipe or Button)**
**Complexity**: ★★☆☆☆ (Low)
**Impact**: ★★★★★ (Very High)
**Time**: 30-45 minutes

**Problem**: Users can't remove old/unwanted requests

**Solution**: Add delete button to each card (admin can delete any, users can delete their own)

**Implementation**:
```html
<!-- In request_card.html -->
<div class="card-actions">
  {% if user.is_admin or req.username == user.username %}
  <button class="btn-icon-small delete-btn"
          data-request-id="{{ req.id }}"
          aria-label="Delete request">
    🗑️
  </button>
  {% endif %}
</div>
```

```javascript
// In app.js
document.addEventListener('DOMContentLoaded', () => {
  document.addEventListener('click', (e) => {
    if (e.target.classList.contains('delete-btn') ||
        e.target.closest('.delete-btn')) {
      const btn = e.target.closest('.delete-btn');
      const requestId = btn.dataset.requestId;

      if (confirm('Delete this request?')) {
        fetch(`/api/request/${requestId}`, {
          method: 'DELETE',
          headers: { 'Content-Type': 'application/json' }
        })
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            // Remove card with animation
            const card = btn.closest('.request-card');
            card.style.opacity = '0';
            card.style.transform = 'translateX(-100%)';
            setTimeout(() => card.remove(), 300);
            showToast('Request deleted', 'success');
          } else {
            showToast('Delete failed: ' + data.error, 'danger');
          }
        })
        .catch(err => showToast('Delete failed', 'danger'));
      }
    }
  });
});
```

**Backend** (simple endpoint):
```python
@app.route("/api/request/<int:request_id>", methods=["DELETE"])
@login_required
def delete_request(request_id):
    user = get_current_user()
    with closing(get_db()) as conn:
        req = conn.execute(
            "SELECT username FROM requests WHERE id = ?", (request_id,)
        ).fetchone()

        if not req:
            return jsonify({"success": False, "error": "Not found"}), 404

        # Only admin or owner can delete
        if not user["is_admin"] and req["username"] != user["username"]:
            return jsonify({"success": False, "error": "Unauthorized"}), 403

        conn.execute("DELETE FROM requests WHERE id = ?", (request_id,))
        conn.commit()

    return jsonify({"success": True})
```

**Benefits**:
- Clean up old requests easily
- No page reload needed
- Smooth animation feedback
- Permission-based (security)

---

#### 3. **Smart Capitalization / Error Correction**
**Complexity**: ★☆☆☆☆ (Very Low)
**Impact**: ★★★☆☆ (Medium)
**Time**: 15-20 minutes

**Problem**: Users type "pink floyd" but it should be "Pink Floyd"

**Solution**: Auto-capitalize artist/album names on blur

**Implementation**:
```javascript
// In new_request.html extra_js
function smartCapitalize(text) {
  // Common words that shouldn't be capitalized
  const lowercase = ['a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor', 'on', 'at', 'to', 'by', 'of', 'in'];

  return text.split(' ')
    .map((word, index) => {
      // Always capitalize first word
      if (index === 0) {
        return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
      }
      // Keep lowercase for common words
      if (lowercase.includes(word.toLowerCase())) {
        return word.toLowerCase();
      }
      // Capitalize others
      return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
    })
    .join(' ');
}

document.getElementById('artist_name').addEventListener('blur', (e) => {
  e.target.value = smartCapitalize(e.target.value.trim());
});

document.getElementById('album_title').addEventListener('blur', (e) => {
  e.target.value = smartCapitalize(e.target.value.trim());
});
```

**Benefits**:
- Cleaner data
- More professional appearance
- Reduces duplicates from case variations
- No user action required

---

#### 4. **Status Filter Pills**
**Complexity**: ★★☆☆☆ (Low)
**Impact**: ★★★★☆ (High)
**Time**: 30-40 minutes

**Problem**: Hard to see just submitted or just failed requests

**Solution**: Add filter pills (chips) above request list

**Implementation**:
```html
<!-- In requests.html, after header -->
<div class="filter-bar">
  <div class="filter-pills">
    <button class="pill active" data-filter="all">
      All <span class="pill-count">{{ rows|length }}</span>
    </button>
    <button class="pill" data-filter="submitted">
      Submitted <span class="pill-count" id="count-submitted">0</span>
    </button>
    <button class="pill" data-filter="downloading">
      Downloading <span class="pill-count" id="count-downloading">0</span>
    </button>
    <button class="pill" data-filter="completed">
      Completed <span class="pill-count" id="count-completed">0</span>
    </button>
    <button class="pill" data-filter="failed">
      Failed <span class="pill-count" id="count-failed">0</span>
    </button>
    <button class="pill" data-filter="existing">
      Existing <span class="pill-count" id="count-existing">0</span>
    </button>
  </div>
</div>
```

```css
.filter-bar {
  background: var(--bg-primary);
  padding: var(--spacing-sm) var(--spacing-md);
  border-bottom: 1px solid var(--border);
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.filter-pills {
  display: flex;
  gap: var(--spacing-xs);
  min-width: min-content;
}

.pill {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 20px;
  font-size: var(--font-sm);
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.pill.active {
  background: var(--primary);
  color: white;
  border-color: var(--primary);
}

.pill-count {
  background: rgba(0,0,0,0.15);
  padding: 2px 6px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
}

.pill.active .pill-count {
  background: rgba(255,255,255,0.25);
}
```

```javascript
// In app.js
document.addEventListener('DOMContentLoaded', () => {
  // Count each status
  const counts = {};
  document.querySelectorAll('.request-card').forEach(card => {
    const status = card.dataset.status;
    counts[status] = (counts[status] || 0) + 1;
  });

  // Update pill counts
  Object.keys(counts).forEach(status => {
    const counter = document.getElementById(`count-${status}`);
    if (counter) counter.textContent = counts[status];
  });

  // Filter functionality
  document.querySelectorAll('.pill').forEach(pill => {
    pill.addEventListener('click', () => {
      const filter = pill.dataset.filter;

      // Update active state
      document.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');

      // Filter cards
      document.querySelectorAll('.request-card').forEach(card => {
        if (filter === 'all' || card.dataset.status === filter) {
          card.style.display = 'block';
        } else {
          card.style.display = 'none';
        }
      });

      // Save preference
      localStorage.setItem('statusFilter', filter);
    });
  });

  // Restore saved filter
  const savedFilter = localStorage.getItem('statusFilter');
  if (savedFilter && savedFilter !== 'all') {
    document.querySelector(`[data-filter="${savedFilter}"]`)?.click();
  }
});
```

**Benefits**:
- Quick visual overview of request distribution
- One-tap filtering
- Persisted preference
- Mobile-friendly horizontal scroll

---

### ⭐⭐ Medium Complexity (1-2 hours each)

#### 5. **Artist/Album Autocomplete with MusicBrainz**
**Complexity**: ★★★☆☆ (Medium)
**Impact**: ★★★★★ (Very High)
**Time**: 1.5-2 hours

**Problem**: Users type incorrect artist/album names, leading to failed lookups

**Solution**: Real-time autocomplete using MusicBrainz API

**Implementation**:
```javascript
// In new_request.html extra_js
let artistDebounce;
let albumDebounce;

function setupAutocomplete(inputId, type) {
  const input = document.getElementById(inputId);
  const resultsDiv = document.createElement('div');
  resultsDiv.className = 'autocomplete-results';
  input.parentNode.appendChild(resultsDiv);

  input.addEventListener('input', (e) => {
    clearTimeout(type === 'artist' ? artistDebounce : albumDebounce);
    const query = e.target.value.trim();

    if (query.length < 2) {
      resultsDiv.innerHTML = '';
      resultsDiv.style.display = 'none';
      return;
    }

    // Debounce API calls (wait 300ms after typing stops)
    const debounce = setTimeout(() => {
      fetch(`/api/search/${type}?q=${encodeURIComponent(query)}`)
        .then(res => res.json())
        .then(data => {
          if (data.results && data.results.length > 0) {
            resultsDiv.innerHTML = data.results
              .slice(0, 5) // Limit to 5 results
              .map(item => `
                <div class="autocomplete-item" data-value="${item.name}">
                  <div class="item-name">${item.name}</div>
                  ${item.disambiguation ? `<div class="item-hint">${item.disambiguation}</div>` : ''}
                </div>
              `)
              .join('');
            resultsDiv.style.display = 'block';
          } else {
            resultsDiv.innerHTML = '<div class="autocomplete-no-results">No results found</div>';
            resultsDiv.style.display = 'block';
          }
        })
        .catch(err => {
          console.error('Autocomplete error:', err);
          resultsDiv.innerHTML = '';
          resultsDiv.style.display = 'none';
        });
    }, 300);

    if (type === 'artist') artistDebounce = debounce;
    else albumDebounce = debounce;
  });

  // Click to select
  resultsDiv.addEventListener('click', (e) => {
    const item = e.target.closest('.autocomplete-item');
    if (item) {
      input.value = item.dataset.value;
      resultsDiv.style.display = 'none';
      input.focus();
    }
  });

  // Hide on blur (with delay for click)
  input.addEventListener('blur', () => {
    setTimeout(() => {
      resultsDiv.style.display = 'none';
    }, 200);
  });
}

setupAutocomplete('artist_name', 'artist');
setupAutocomplete('album_title', 'album');
```

```css
.autocomplete-results {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: var(--bg-primary);
  border: 1px solid var(--border);
  border-top: none;
  border-radius: 0 0 var(--radius-md) var(--radius-md);
  box-shadow: var(--shadow-md);
  z-index: 1000;
  max-height: 300px;
  overflow-y: auto;
  display: none;
}

.autocomplete-item {
  padding: var(--spacing-sm) var(--spacing-md);
  cursor: pointer;
  transition: background 0.2s;
}

.autocomplete-item:hover {
  background: var(--bg-secondary);
}

.item-name {
  font-weight: 600;
  color: var(--text-primary);
}

.item-hint {
  font-size: var(--font-xs);
  color: var(--text-secondary);
  margin-top: 2px;
}

.autocomplete-no-results {
  padding: var(--spacing-sm) var(--spacing-md);
  color: var(--text-secondary);
  font-size: var(--font-sm);
}
```

**Backend** (simple proxy to MusicBrainz):
```python
@app.route("/api/search/<search_type>")
@login_required
def search_musicbrainz(search_type):
    query = request.args.get("q", "").strip()
    if not query or len(query) < 2:
        return jsonify({"results": []})

    try:
        if search_type == "artist":
            url = f"{LIDARR_URL}/artist/lookup?term={query}"
        elif search_type == "album":
            url = f"{LIDARR_URL}/album/lookup?term={query}"
        else:
            return jsonify({"results": []})

        resp = requests.get(url, params={"apikey": LIDARR_API_KEY}, timeout=5)

        if resp.status_code == 200:
            data = resp.json()
            results = []

            for item in data[:5]:  # Limit to 5
                if search_type == "artist":
                    results.append({
                        "name": item.get("artistName", ""),
                        "disambiguation": item.get("disambiguation", "")
                    })
                elif search_type == "album":
                    results.append({
                        "name": item.get("title", ""),
                        "disambiguation": item.get("artistName", "")
                    })

            return jsonify({"results": results})

        return jsonify({"results": []})

    except Exception as exc:
        app.logger.error(f"Search error: {exc}")
        return jsonify({"results": []})
```

**Benefits**:
- Prevents typos and misspellings
- Shows official names (e.g., "Pink Floyd" not "pink flyd")
- Shows disambiguation (e.g., "King Crimson (UK prog band)")
- Reduces failed lookups by 80%+
- Great mobile UX (tap to select)

---

#### 6. **Fuzzy Search for Request List**
**Complexity**: ★★☆☆☆ (Low-Medium)
**Impact**: ★★★★☆ (High)
**Time**: 1-1.5 hours

**Problem**: Users can't find specific requests in long lists

**Solution**: Add search box with fuzzy matching (client-side, fast)

**Implementation**:
```html
<!-- In requests.html header -->
<div class="search-bar">
  <input type="text"
         id="searchInput"
         placeholder="Search artists, albums, notes..."
         class="search-input">
  <button class="btn-icon" id="clearSearch" style="display: none;">✕</button>
</div>
```

```javascript
// In app.js - Simple fuzzy match
function fuzzyMatch(str, pattern) {
  const strLower = str.toLowerCase();
  const patternLower = pattern.toLowerCase();

  // Exact match (highest priority)
  if (strLower.includes(patternLower)) return 10;

  // Fuzzy match (allow some character differences)
  let patternIdx = 0;
  let strIdx = 0;
  let matches = 0;

  while (strIdx < strLower.length && patternIdx < patternLower.length) {
    if (strLower[strIdx] === patternLower[patternIdx]) {
      matches++;
      patternIdx++;
    }
    strIdx++;
  }

  // Return match score (higher = better)
  return patternIdx === patternLower.length ? matches : 0;
}

document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('searchInput');
  const clearBtn = document.getElementById('clearSearch');

  searchInput.addEventListener('input', (e) => {
    const query = e.target.value.trim();

    if (query.length === 0) {
      clearBtn.style.display = 'none';
      // Show all cards
      document.querySelectorAll('.request-card').forEach(card => {
        card.style.display = 'block';
      });
      return;
    }

    clearBtn.style.display = 'block';

    // Search in artist, album, note
    document.querySelectorAll('.request-card').forEach(card => {
      const artist = card.dataset.artist || '';
      const album = card.dataset.album || '';
      const note = card.dataset.note || '';

      const artistScore = fuzzyMatch(artist, query);
      const albumScore = fuzzyMatch(album, query);
      const noteScore = fuzzyMatch(note, query);

      if (artistScore > 0 || albumScore > 0 || noteScore > 0) {
        card.style.display = 'block';
        // Optionally highlight matched text
      } else {
        card.style.display = 'none';
      }
    });
  });

  clearBtn.addEventListener('click', () => {
    searchInput.value = '';
    searchInput.dispatchEvent(new Event('input'));
    searchInput.focus();
  });
});
```

**Benefits**:
- Instant search (no server round-trip)
- Works with typos (fuzzy matching)
- Searches artist, album, and notes
- Clear button for easy reset
- Mobile-friendly

---

#### 7. **Predictive Feedback: "Checking for duplicates..."**
**Complexity**: ★★☆☆☆ (Low-Medium)
**Impact**: ★★★☆☆ (Medium)
**Time**: 30-45 minutes

**Problem**: Users don't know if duplicate check is happening

**Solution**: Show inline feedback while typing in new request form

**Implementation**:
```html
<!-- In new_request.html -->
<div class="form-group">
  <label for="artist_name">Artist Name</label>
  <input type="text" id="artist_name" name="artist_name" required>
  <p class="form-hint" id="artist-feedback">
    <span class="feedback-icon"></span>
    <span class="feedback-text">Enter the artist or band name</span>
  </p>
</div>
```

```javascript
// In new_request.html extra_js
let checkDebounce;

document.getElementById('artist_name').addEventListener('input', (e) => {
  const artistName = e.target.value.trim();
  const feedback = document.getElementById('artist-feedback');
  const icon = feedback.querySelector('.feedback-icon');
  const text = feedback.querySelector('.feedback-text');

  clearTimeout(checkDebounce);

  if (artistName.length < 2) {
    icon.textContent = '';
    text.textContent = 'Enter the artist or band name';
    feedback.className = 'form-hint';
    return;
  }

  // Show checking state
  icon.textContent = '🔍';
  text.textContent = 'Checking...';
  feedback.className = 'form-hint checking';

  // Debounce check (wait 500ms after typing)
  checkDebounce = setTimeout(() => {
    fetch(`/api/check-duplicate?artist=${encodeURIComponent(artistName)}`)
      .then(res => res.json())
      .then(data => {
        if (data.exists) {
          icon.textContent = '✓';
          text.textContent = `Already in library! Click here to listen →`;
          feedback.className = 'form-hint existing';
          feedback.style.cursor = 'pointer';
          feedback.onclick = () => {
            window.open(data.listen_url, '_blank');
          };
        } else if (data.found) {
          icon.textContent = '✓';
          text.textContent = 'Artist found on MusicBrainz';
          feedback.className = 'form-hint success';
        } else {
          icon.textContent = '⚠️';
          text.textContent = 'Artist not found - check spelling';
          feedback.className = 'form-hint warning';
        }
      })
      .catch(err => {
        icon.textContent = '';
        text.textContent = 'Enter the artist or band name';
        feedback.className = 'form-hint';
      });
  }, 500);
});
```

```css
.form-hint.checking {
  color: var(--text-secondary);
}

.form-hint.success {
  color: var(--success);
}

.form-hint.warning {
  color: var(--warning);
}

.form-hint.existing {
  color: var(--primary);
  font-weight: 600;
}

.feedback-icon {
  margin-right: 4px;
}
```

**Backend** (simple check endpoint):
```python
@app.route("/api/check-duplicate")
@login_required
def check_duplicate():
    artist_name = request.args.get("artist", "").strip()

    if not artist_name:
        return jsonify({"exists": False, "found": False})

    # Lookup in MusicBrainz
    artist_data, err = lookup_artist(artist_name)

    if err or not artist_data:
        return jsonify({"exists": False, "found": False})

    foreign_id = artist_data.get("foreignArtistId")

    # Check if exists in Lidarr
    exists, data, err = check_artist_exists_in_lidarr(foreign_id)

    if exists:
        return jsonify({
            "exists": True,
            "found": True,
            "listen_url": f"{PLEX_URL}/#!/search?query={artist_name}"
        })

    return jsonify({"exists": False, "found": True})
```

**Benefits**:
- Prevents duplicate submissions before form submit
- Shows what's happening (transparency)
- Immediate link to existing music
- Reduces failed requests
- Great UX feedback loop

---

### ⭐⭐⭐ Higher Complexity (2-3 hours each)

#### 8. **Album Selection Dropdown (after artist chosen)**
**Complexity**: ★★★★☆ (High)
**Impact**: ★★★★★ (Very High)
**Time**: 2-3 hours

**Problem**: Users don't know which albums exist for an artist

**Solution**: After artist is selected, show dropdown of all albums for that artist

**Implementation**:
```javascript
// After artist is confirmed via autocomplete
document.getElementById('artist_name').addEventListener('change', async (e) => {
  const artistName = e.target.value.trim();
  const albumInput = document.getElementById('album_title');

  if (!artistName) return;

  // Fetch albums for this artist
  const res = await fetch(`/api/albums-for-artist?artist=${encodeURIComponent(artistName)}`);
  const data = await res.json();

  if (data.albums && data.albums.length > 0) {
    // Convert album input to select dropdown
    const select = document.createElement('select');
    select.id = 'album_title';
    select.name = 'album_title';
    select.required = true;
    select.className = albumInput.className;

    // Add placeholder option
    const placeholder = document.createElement('option');
    placeholder.value = '';
    placeholder.textContent = 'Select an album...';
    select.appendChild(placeholder);

    // Add album options
    data.albums.forEach(album => {
      const option = document.createElement('option');
      option.value = album.title;
      option.textContent = `${album.title} (${album.year || 'Unknown'})`;
      select.appendChild(option);
    });

    // Replace input with select
    albumInput.parentNode.replaceChild(select, albumInput);

    // Add "or type manually" link
    const manualLink = document.createElement('a');
    manualLink.href = '#';
    manualLink.textContent = 'Or type album name manually';
    manualLink.className = 'manual-link';
    manualLink.onclick = (e) => {
      e.preventDefault();
      // Switch back to input
      const input = document.createElement('input');
      input.type = 'text';
      input.id = 'album_title';
      input.name = 'album_title';
      input.required = true;
      input.className = albumInput.className;
      select.parentNode.replaceChild(input, select);
      manualLink.remove();
    };
    select.parentNode.appendChild(manualLink);
  }
});
```

**Backend**:
```python
@app.route("/api/albums-for-artist")
@login_required
def albums_for_artist():
    artist_name = request.args.get("artist", "").strip()

    # Lookup artist
    artist_data, err = lookup_artist(artist_name)
    if err or not artist_data:
        return jsonify({"albums": []})

    try:
        # Get albums from MusicBrainz via Lidarr
        mb_id = artist_data.get("foreignArtistId")
        url = f"{LIDARR_URL}/album/lookup?term=mbid:{mb_id}"
        resp = requests.get(url, params={"apikey": LIDARR_API_KEY}, timeout=10)

        if resp.status_code == 200:
            albums = resp.json()
            result = []
            for album in albums[:20]:  # Limit to 20
                result.append({
                    "title": album.get("title", ""),
                    "year": album.get("releaseDate", "")[:4] if album.get("releaseDate") else None
                })
            return jsonify({"albums": result})
    except Exception as exc:
        app.logger.error(f"Album lookup error: {exc}")

    return jsonify({"albums": []})
```

**Benefits**:
- Zero typing errors for album names
- Shows year info (helpful for disambiguation)
- Still allows manual entry (flexibility)
- Massive reduction in failed requests
- Great progressive disclosure UX

---

#### 9. **Request Card Mini-Actions (Retry, Copy, Share)**
**Complexity**: ★★★☆☆ (Medium)
**Impact**: ★★★☆☆ (Medium)
**Time**: 1-1.5 hours

**Problem**: Users want to retry failed requests or duplicate successful ones

**Solution**: Add action menu to each card

**Implementation**:
```html
<!-- In request_card.html -->
<div class="card-actions-menu">
  <button class="btn-icon-small" aria-label="Actions" data-toggle="actions">⋮</button>
  <div class="actions-dropdown" style="display: none;">
    {% if req.status == 'failed' %}
    <button class="action-item" data-action="retry" data-id="{{ req.id }}">
      🔄 Retry Request
    </button>
    {% endif %}
    <button class="action-item" data-action="copy" data-id="{{ req.id }}">
      📋 Copy as New
    </button>
    {% if user.is_admin or req.username == user.username %}
    <button class="action-item danger" data-action="delete" data-id="{{ req.id }}">
      🗑️ Delete
    </button>
    {% endif %}
  </div>
</div>
```

```javascript
// Toggle actions dropdown
document.addEventListener('click', (e) => {
  const toggle = e.target.closest('[data-toggle="actions"]');
  if (toggle) {
    const dropdown = toggle.nextElementSibling;
    dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
    return;
  }

  // Close all dropdowns if clicking outside
  if (!e.target.closest('.actions-dropdown')) {
    document.querySelectorAll('.actions-dropdown').forEach(d => d.style.display = 'none');
  }

  // Handle action clicks
  const action = e.target.closest('.action-item');
  if (action) {
    const type = action.dataset.action;
    const id = action.dataset.id;

    if (type === 'retry') {
      retryRequest(id);
    } else if (type === 'copy') {
      copyRequest(id);
    } else if (type === 'delete') {
      deleteRequest(id);
    }
  }
});
```

**Benefits**:
- Quick actions without leaving page
- Retry failed requests easily
- Duplicate successful requests
- Clean, discoverable UI

---

## 📊 Complexity vs Impact Matrix

| Enhancement | Complexity | Impact | Time | Priority |
|------------|-----------|--------|------|----------|
| Show/Hide Failed | ★☆☆☆☆ | ★★★★☆ | 20-30m | **HIGH** |
| Delete Request | ★★☆☆☆ | ★★★★★ | 30-45m | **HIGH** |
| Smart Capitalize | ★☆☆☆☆ | ★★★☆☆ | 15-20m | **MEDIUM** |
| Status Filters | ★★☆☆☆ | ★★★★☆ | 30-40m | **HIGH** |
| Autocomplete | ★★★☆☆ | ★★★★★ | 1.5-2h | **HIGH** |
| Fuzzy Search | ★★☆☆☆ | ★★★★☆ | 1-1.5h | **MEDIUM** |
| Predictive Check | ★★☆☆☆ | ★★★☆☆ | 30-45m | **MEDIUM** |
| Album Dropdown | ★★★★☆ | ★★★★★ | 2-3h | **MEDIUM** |
| Card Actions | ★★★☆☆ | ★★★☆☆ | 1-1.5h | **LOW** |

---

## 🎯 Recommended Implementation Order

### Phase 1: Quick Wins (2-3 hours total)
1. **Show/Hide Failed Toggle** (20-30m)
2. **Delete Request Button** (30-45m)
3. **Smart Capitalization** (15-20m)
4. **Status Filter Pills** (30-40m)

**Total Impact**: Clean up UI, basic filtering, data cleanup
**All frontend JavaScript** - minimal backend changes

---

### Phase 2: Smart Input (2-3 hours total)
5. **Artist/Album Autocomplete** (1.5-2h)
6. **Predictive Duplicate Check** (30-45m)

**Total Impact**: Massively reduce failed requests, better UX
**Requires simple backend endpoints** - still mostly frontend

---

### Phase 3: Advanced Search (1.5 hours)
7. **Fuzzy Search** (1-1.5h)

**Total Impact**: Better navigation for large lists
**Pure frontend** - no backend changes

---

### Phase 4: Power Features (3-4 hours total)
8. **Album Selection Dropdown** (2-3h)
9. **Request Card Mini-Actions** (1-1.5h)

**Total Impact**: Professional-grade UX
**Moderate backend work**

---

## 💰 Total Time Investment

- **Phase 1 (Quick Wins)**: 2-3 hours
- **Phase 2 (Smart Input)**: 2-3 hours
- **Phase 3 (Advanced Search)**: 1.5 hours
- **Phase 4 (Power Features)**: 3-4 hours

**Grand Total**: 8.5-11.5 hours for all enhancements

**Recommended First Session**: Phase 1 (2-3 hours)
- Immediate visible improvement
- Clean up UI clutter
- Foundation for future enhancements
- All low-complexity, high-impact

---

## 🚀 What's Possible Without Backend Changes?

**100% Frontend (JavaScript + CSS only)**:
- Show/Hide Failed Toggle ✅
- Smart Capitalization ✅
- Status Filter Pills ✅
- Fuzzy Search ✅
- Card animations and transitions ✅
- Keyboard shortcuts ✅
- Loading states and skeletons ✅

**Minimal Backend (< 20 lines)**:
- Delete Request (simple DELETE endpoint)
- Autocomplete (proxy to MusicBrainz)
- Predictive Check (existing function + endpoint)
- Album Dropdown (existing function + endpoint)

---

**Next Step**: Would you like to implement Phase 1 (Quick Wins) now? All 4 features in 2-3 hours with huge UX improvement?
