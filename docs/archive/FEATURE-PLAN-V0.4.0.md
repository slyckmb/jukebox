# Jukebox Feature Plan - v0.4.0

**Version**: 0.4.0 (Feature Improvements)
**Created**: 2025-11-24
**Status**: Planning
**Estimated Time**: 3-4 hours

---

## Overview

This plan adds essential user experience improvements to the Jukebox application:
- **Search & Filter**: Find requests quickly by artist, album, status
- **Bulk Actions**: Admin capability to manage multiple requests at once
- **Request Details Modal**: View full request information without navigation
- **Enhanced UI**: Improved request cards with inline actions

**Priority**: High (User-requested feature improvements)

---

## Current State Analysis

**Database Schema**:
- `requests` table has 13 columns including: id, user_id, artist_name, album_title, note, status, tag, lidarr_artist_id, last_error, created_at, updated_at
- Indexes exist on: user_id, status, artist_name
- Current data: ~10 requests (7 failed, 3 submitted) from 2 users

**Current UI**:
- Card-based request list in `requests.html`
- Status badges (new, submitted, failed, existing)
- FAB for new requests
- Bottom navigation (mobile)
- No search/filter capability
- No bulk actions
- No request details view

**Technical Stack**:
- Flask 3.1.2 + Jinja2 templates
- Vanilla JavaScript (no frameworks)
- SQLite database
- Mobile-first responsive design

---

## Feature Breakdown

### Feature 1: Search & Filter System

**Priority**: High
**Time**: 1.5 hours
**Complexity**: Medium

#### User Stories:
- As a user, I want to search requests by artist name so I can quickly find specific requests
- As a user, I want to filter requests by status (new, submitted, failed, existing) so I can see what needs attention
- As a user, I want to filter by my own requests vs all requests (admin) so I can manage my list
- As a user, I want to clear filters easily to return to the full list

#### Implementation:

**Backend Changes** (`app/app.py`):
```python
@app.route("/requests", methods=["GET"])
@login_required
def list_requests():
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    # Get filter parameters
    search_query = request.args.get("search", "").strip()
    status_filter = request.args.get("status", "").strip()
    user_filter = request.args.get("user", "all")  # all, mine

    # Build dynamic query
    query = "SELECT * FROM requests WHERE 1=1"
    params = []

    # User filter (non-admins always see only their requests)
    if not user["is_admin"] or user_filter == "mine":
        query += " AND user_id = ?"
        params.append(user["id"])

    # Search filter (artist or album)
    if search_query:
        query += " AND (LOWER(artist_name) LIKE ? OR LOWER(album_title) LIKE ?)"
        search_pattern = f"%{search_query.lower()}%"
        params.extend([search_pattern, search_pattern])

    # Status filter
    if status_filter and status_filter in ["new", "submitted", "failed", "existing"]:
        query += " AND status = ?"
        params.append(status_filter)

    query += " ORDER BY created_at DESC"

    with closing(get_db()) as conn:
        cur = conn.execute(query, params)
        rows = cur.fetchall()

    # Get request count by status for filter badges
    count_query = "SELECT status, COUNT(*) as count FROM requests"
    if not user["is_admin"] or user_filter == "mine":
        count_query += " WHERE user_id = ?"
        count_params = [user["id"]]
    else:
        count_params = []
    count_query += " GROUP BY status"

    with closing(get_db()) as conn:
        cur = conn.execute(count_query, count_params)
        status_counts = {row["status"]: row["count"] for row in cur.fetchall()}

    return render_template(
        "requests.html",
        user=user,
        rows=rows,
        status_counts=status_counts,
        filters={
            "search": search_query,
            "status": status_filter,
            "user": user_filter,
        },
    )
```

**Frontend Changes** (`app/templates/requests.html`):

Add search/filter bar after page header:
```html
<!-- Search & Filter Bar -->
<div class="filter-bar">
  <form method="GET" action="{{ url_for('list_requests') }}" class="filter-form" id="filterForm">
    <!-- Search Input -->
    <div class="search-box">
      <input
        type="search"
        name="search"
        id="searchInput"
        placeholder="Search artist or album..."
        value="{{ filters.search }}"
        class="search-input"
      >
      <button type="button" class="search-clear" id="clearSearch" aria-label="Clear search">
        ✕
      </button>
    </div>

    <!-- Status Filter Pills -->
    <div class="filter-pills">
      <button
        type="button"
        class="filter-pill {% if not filters.status %}active{% endif %}"
        data-status=""
      >
        All <span class="pill-count">{{ rows|length }}</span>
      </button>

      <button
        type="button"
        class="filter-pill status-new {% if filters.status == 'new' %}active{% endif %}"
        data-status="new"
      >
        New <span class="pill-count">{{ status_counts.new or 0 }}</span>
      </button>

      <button
        type="button"
        class="filter-pill status-submitted {% if filters.status == 'submitted' %}active{% endif %}"
        data-status="submitted"
      >
        Submitted <span class="pill-count">{{ status_counts.submitted or 0 }}</span>
      </button>

      <button
        type="button"
        class="filter-pill status-failed {% if filters.status == 'failed' %}active{% endif %}"
        data-status="failed"
      >
        Failed <span class="pill-count">{{ status_counts.failed or 0 }}</span>
      </button>

      <button
        type="button"
        class="filter-pill status-existing {% if filters.status == 'existing' %}active{% endif %}"
        data-status="existing"
      >
        Existing <span class="pill-count">{{ status_counts.existing or 0 }}</span>
      </button>
    </div>

    {% if user.is_admin %}
    <!-- User Filter (Admin Only) -->
    <div class="user-filter">
      <label class="filter-toggle">
        <input
          type="checkbox"
          name="user"
          value="mine"
          {% if filters.user == 'mine' %}checked{% endif %}
          onchange="this.form.submit()"
        >
        <span>My requests only</span>
      </label>
    </div>
    {% endif %}

    <input type="hidden" name="status" id="statusInput" value="{{ filters.status }}">
  </form>

  <!-- Active Filters Summary -->
  {% if filters.search or filters.status %}
  <div class="active-filters">
    <span class="filter-label">Filters:</span>
    {% if filters.search %}
    <span class="active-filter-tag">
      Search: "{{ filters.search }}"
      <a href="{{ url_for('list_requests', status=filters.status, user=filters.user) }}" class="remove-filter">✕</a>
    </span>
    {% endif %}
    {% if filters.status %}
    <span class="active-filter-tag">
      Status: {{ filters.status }}
      <a href="{{ url_for('list_requests', search=filters.search, user=filters.user) }}" class="remove-filter">✕</a>
    </span>
    {% endif %}
    <a href="{{ url_for('list_requests') }}" class="clear-all-filters">Clear all</a>
  </div>
  {% endif %}
</div>
```

**JavaScript** (`app/static/js/app.js` additions):
```javascript
// Search & Filter functionality
document.addEventListener('DOMContentLoaded', function() {
  const filterForm = document.getElementById('filterForm');
  const searchInput = document.getElementById('searchInput');
  const clearSearch = document.getElementById('clearSearch');
  const statusInput = document.getElementById('statusInput');
  const filterPills = document.querySelectorAll('.filter-pill');

  // Auto-submit search after typing stops
  let searchTimeout;
  if (searchInput) {
    searchInput.addEventListener('input', function() {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => {
        filterForm.submit();
      }, 500); // 500ms debounce
    });
  }

  // Clear search button
  if (clearSearch) {
    clearSearch.addEventListener('click', function() {
      searchInput.value = '';
      filterForm.submit();
    });

    // Show/hide clear button based on input
    searchInput.addEventListener('input', function() {
      clearSearch.style.display = this.value ? 'block' : 'none';
    });
  }

  // Status filter pills
  filterPills.forEach(pill => {
    pill.addEventListener('click', function() {
      const status = this.dataset.status;
      statusInput.value = status;
      filterForm.submit();
    });
  });
});
```

**CSS Additions** (`requests.html` extra_css block):
```css
/* Filter Bar */
.filter-bar {
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border);
  padding: var(--spacing-md);
  position: sticky;
  top: 73px; /* Below header */
  z-index: 90;
}

.filter-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.search-box {
  position: relative;
  width: 100%;
}

.search-input {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  padding-right: 40px;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  font-size: var(--font-base);
  background: var(--bg-primary);
}

.search-input:focus {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.search-clear {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  width: 28px;
  height: 28px;
  border: none;
  background: var(--text-tertiary);
  color: var(--bg-primary);
  border-radius: 50%;
  cursor: pointer;
  display: none;
  font-size: 14px;
}

.search-input:not(:placeholder-shown) ~ .search-clear {
  display: block;
}

/* Filter Pills */
.filter-pills {
  display: flex;
  gap: var(--spacing-xs);
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}

.filter-pills::-webkit-scrollbar {
  display: none;
}

.filter-pill {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  border: 1px solid var(--border);
  border-radius: var(--radius-full);
  background: var(--bg-primary);
  font-size: var(--font-sm);
  font-weight: 500;
  white-space: nowrap;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-pill:hover {
  background: var(--bg-secondary);
}

.filter-pill.active {
  background: var(--accent);
  color: white;
  border-color: var(--accent);
}

.pill-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  background: rgba(0, 0, 0, 0.1);
  border-radius: var(--radius-full);
  font-size: var(--font-xs);
  font-weight: 600;
}

.filter-pill.active .pill-count {
  background: rgba(255, 255, 255, 0.2);
}

/* User Filter */
.user-filter {
  padding-top: var(--spacing-xs);
}

.filter-toggle {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  cursor: pointer;
  font-size: var(--font-sm);
}

.filter-toggle input[type="checkbox"] {
  width: 20px;
  height: 20px;
  cursor: pointer;
}

/* Active Filters */
.active-filters {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--spacing-xs);
  margin-top: var(--spacing-sm);
  padding-top: var(--spacing-sm);
  border-top: 1px solid var(--border);
  font-size: var(--font-sm);
}

.filter-label {
  font-weight: 600;
  color: var(--text-secondary);
}

.active-filter-tag {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: 4px 8px;
  background: var(--accent);
  color: white;
  border-radius: var(--radius-sm);
  font-size: var(--font-xs);
}

.remove-filter {
  color: white;
  font-weight: bold;
  text-decoration: none;
}

.clear-all-filters {
  color: var(--danger);
  font-weight: 600;
  text-decoration: underline;
  margin-left: auto;
}

/* Results info */
.results-info {
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border);
  font-size: var(--font-sm);
  color: var(--text-secondary);
  text-align: center;
}
```

#### Testing Checklist:
- [ ] Search by artist name filters correctly
- [ ] Search by album title filters correctly
- [ ] Search is case-insensitive
- [ ] Status filters work (all, new, submitted, failed, existing)
- [ ] Pill counts update correctly
- [ ] Admin can toggle "My requests only"
- [ ] Non-admin only sees their requests
- [ ] Clear search button works
- [ ] Clear all filters works
- [ ] Search auto-submits after typing stops (debounce)
- [ ] Filter bar is sticky below header
- [ ] Mobile responsive (horizontal scroll for pills)
- [ ] Active filters summary displays correctly
- [ ] Combining filters works (search + status + user)

---

### Feature 2: Request Details Modal

**Priority**: Medium
**Time**: 1 hour
**Complexity**: Low-Medium

#### User Stories:
- As a user, I want to click a request card to see full details without leaving the page
- As a user, I want to see all request metadata (created date, updated date, Lidarr IDs, tags, etc.)
- As a user, I want to see the full error message if a request failed
- As a user, I want to close the modal with ESC key or by clicking outside

#### Implementation:

**Backend Changes** (`app/app.py`):
```python
@app.route("/api/request/<int:request_id>", methods=["GET"])
@login_required
def get_request_details(request_id):
    """API endpoint to fetch full request details."""
    user = current_user()
    if not user:
        return jsonify({"status": "error", "message": "Not authenticated"}), 401

    with closing(get_db()) as conn:
        query = "SELECT r.*, u.username FROM requests r JOIN users u ON r.user_id = u.id WHERE r.id = ?"

        # Non-admins can only view their own requests
        if not user["is_admin"]:
            query += " AND r.user_id = ?"
            cur = conn.execute(query, (request_id, user["id"]))
        else:
            cur = conn.execute(query, (request_id,))

        row = cur.fetchone()

    if not row:
        return jsonify({"status": "error", "message": "Request not found"}), 404

    # Convert row to dict
    request_data = dict(row)

    return jsonify({
        "status": "success",
        "request": request_data
    })
```

**Frontend Changes** (`app/templates/requests.html`):

Add modal HTML before closing `</div>` of `.requests-page`:
```html
<!-- Request Details Modal -->
<div id="requestModal" class="modal" style="display: none;">
  <div class="modal-backdrop" onclick="closeRequestModal()"></div>
  <div class="modal-content">
    <div class="modal-header">
      <h2>Request Details</h2>
      <button class="modal-close" onclick="closeRequestModal()" aria-label="Close">✕</button>
    </div>
    <div class="modal-body" id="modalBody">
      <div class="loading-spinner">Loading...</div>
    </div>
  </div>
</div>
```

Update request cards to be clickable (modify `app/templates/components/request_card.html`):
```html
<div class="request-card" onclick="openRequestModal({{ req.id }})" style="cursor: pointer;">
  <!-- existing card content -->
</div>
```

**JavaScript** (`app/static/js/app.js` additions):
```javascript
// Request Details Modal
function openRequestModal(requestId) {
  const modal = document.getElementById('requestModal');
  const modalBody = document.getElementById('modalBody');

  // Show modal with loading state
  modal.style.display = 'flex';
  modalBody.innerHTML = '<div class="loading-spinner">Loading...</div>';
  document.body.style.overflow = 'hidden'; // Prevent background scroll

  // Fetch request details
  fetch(`/api/request/${requestId}`)
    .then(response => response.json())
    .then(data => {
      if (data.status === 'success') {
        renderRequestDetails(data.request);
      } else {
        modalBody.innerHTML = `<div class="error-message">Error: ${data.message}</div>`;
      }
    })
    .catch(error => {
      modalBody.innerHTML = `<div class="error-message">Failed to load request details</div>`;
      console.error('Error fetching request:', error);
    });
}

function closeRequestModal() {
  const modal = document.getElementById('requestModal');
  modal.style.display = 'none';
  document.body.style.overflow = ''; // Restore scroll
}

function renderRequestDetails(req) {
  const modalBody = document.getElementById('modalBody');

  const statusBadgeClass = `status-${req.status}`;
  const statusIcon = {
    'new': '🆕',
    'submitted': '✅',
    'failed': '❌',
    'existing': '📀'
  }[req.status] || '📝';

  const createdDate = new Date(req.created_at).toLocaleString();
  const updatedDate = new Date(req.updated_at).toLocaleString();

  modalBody.innerHTML = `
    <div class="detail-group">
      <div class="detail-header">
        <h3 class="detail-artist">${escapeHtml(req.artist_name)}</h3>
        <span class="status-badge ${statusBadgeClass}">
          ${statusIcon} ${req.status}
        </span>
      </div>
      ${req.album_title ? `<p class="detail-album">${escapeHtml(req.album_title)}</p>` : ''}
    </div>

    ${req.note ? `
    <div class="detail-group">
      <label class="detail-label">Note</label>
      <p class="detail-note">${escapeHtml(req.note)}</p>
    </div>
    ` : ''}

    <div class="detail-group">
      <label class="detail-label">Requested by</label>
      <p class="detail-value">${escapeHtml(req.username)}</p>
    </div>

    <div class="detail-group">
      <label class="detail-label">Tag</label>
      <p class="detail-value"><code>${escapeHtml(req.tag)}</code></p>
    </div>

    <div class="detail-group">
      <label class="detail-label">Root Folder</label>
      <p class="detail-value"><code>${escapeHtml(req.root_folder_path)}</code></p>
    </div>

    ${req.lidarr_artist_id ? `
    <div class="detail-group">
      <label class="detail-label">Lidarr Artist ID</label>
      <p class="detail-value">${req.lidarr_artist_id}</p>
    </div>
    ` : ''}

    ${req.lidarr_album_id ? `
    <div class="detail-group">
      <label class="detail-label">Lidarr Album ID</label>
      <p class="detail-value">${req.lidarr_album_id}</p>
    </div>
    ` : ''}

    ${req.last_error ? `
    <div class="detail-group error-group">
      <label class="detail-label">Error Details</label>
      <pre class="detail-error">${escapeHtml(req.last_error)}</pre>
    </div>
    ` : ''}

    <div class="detail-group detail-meta">
      <div class="meta-item">
        <label class="detail-label">Created</label>
        <p class="detail-value">${createdDate}</p>
      </div>
      <div class="meta-item">
        <label class="detail-label">Updated</label>
        <p class="detail-value">${updatedDate}</p>
      </div>
    </div>
  `;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Close modal on ESC key
document.addEventListener('keydown', function(event) {
  if (event.key === 'Escape') {
    closeRequestModal();
  }
});
```

**CSS Additions** (`requests.html` extra_css block):
```css
/* Modal */
.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-md);
}

.modal-backdrop {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
}

.modal-content {
  position: relative;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  box-shadow: var(--shadow-2xl);
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--border);
}

.modal-header h2 {
  margin: 0;
  font-size: var(--font-xl);
}

.modal-close {
  width: 36px;
  height: 36px;
  border: none;
  background: var(--bg-secondary);
  border-radius: 50%;
  font-size: 20px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.modal-close:hover {
  background: var(--border);
}

.modal-body {
  padding: var(--spacing-md);
  overflow-y: auto;
  flex: 1;
}

/* Detail Groups */
.detail-group {
  margin-bottom: var(--spacing-lg);
}

.detail-group:last-child {
  margin-bottom: 0;
}

.detail-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
}

.detail-artist {
  margin: 0;
  font-size: var(--font-xl);
  font-weight: 700;
  flex: 1;
}

.detail-album {
  margin: 0;
  font-size: var(--font-lg);
  color: var(--text-secondary);
}

.detail-label {
  display: block;
  font-size: var(--font-sm);
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.detail-value {
  margin: 0;
  font-size: var(--font-base);
}

.detail-value code {
  background: var(--bg-secondary);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  font-family: 'Courier New', monospace;
  font-size: var(--font-sm);
}

.detail-note {
  margin: 0;
  padding: var(--spacing-sm);
  background: var(--bg-secondary);
  border-radius: var(--radius-sm);
  font-style: italic;
  color: var(--text-secondary);
}

.error-group {
  background: rgba(239, 68, 68, 0.05);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: var(--radius-md);
  padding: var(--spacing-sm);
}

.detail-error {
  margin: 0;
  padding: var(--spacing-sm);
  background: var(--bg-primary);
  border-radius: var(--radius-sm);
  font-family: 'Courier New', monospace;
  font-size: var(--font-sm);
  color: var(--danger);
  white-space: pre-wrap;
  word-break: break-word;
  overflow-x: auto;
}

.detail-meta {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-md);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--border);
}

.meta-item {
  min-width: 0;
}

.loading-spinner {
  text-align: center;
  padding: var(--spacing-2xl);
  color: var(--text-secondary);
}

/* Mobile adjustments */
@media (max-width: 640px) {
  .modal {
    padding: 0;
    align-items: flex-end;
  }

  .modal-content {
    max-height: 85vh;
    border-radius: var(--radius-lg) var(--radius-lg) 0 0;
  }

  .detail-meta {
    grid-template-columns: 1fr;
  }
}
```

#### Testing Checklist:
- [ ] Clicking request card opens modal
- [ ] Modal displays all request details correctly
- [ ] Status badge displays correctly
- [ ] Error details display for failed requests
- [ ] Created/Updated dates format correctly
- [ ] ESC key closes modal
- [ ] Clicking backdrop closes modal
- [ ] Close button works
- [ ] Non-admin can only view their own requests
- [ ] Admin can view all requests
- [ ] Modal is scrollable for long content
- [ ] Mobile: Modal slides up from bottom
- [ ] Loading spinner shows during fetch

---

### Feature 3: Bulk Actions (Admin Only)

**Priority**: Medium
**Time**: 1-1.5 hours
**Complexity**: Medium

#### User Stories:
- As an admin, I want to select multiple requests so I can perform bulk actions
- As an admin, I want to delete multiple failed requests at once
- As an admin, I want to retry multiple failed requests at once
- As an admin, I want to see how many requests are selected
- As an admin, I want to select/deselect all requests easily

#### Implementation:

**Backend Changes** (`app/app.py`):
```python
@app.route("/api/requests/bulk-delete", methods=["POST"])
@login_required
def bulk_delete_requests():
    """Admin-only: Delete multiple requests by ID."""
    user = current_user()
    if not user or not user["is_admin"]:
        return jsonify({"status": "error", "message": "Admin access required"}), 403

    request_ids = request.json.get("request_ids", [])
    if not request_ids or not isinstance(request_ids, list):
        return jsonify({"status": "error", "message": "Invalid request_ids"}), 400

    # Validate all IDs are integers
    try:
        request_ids = [int(rid) for rid in request_ids]
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "Invalid request ID format"}), 400

    if len(request_ids) > 100:
        return jsonify({"status": "error", "message": "Maximum 100 requests per bulk action"}), 400

    # Delete requests
    placeholders = ",".join("?" * len(request_ids))
    query = f"DELETE FROM requests WHERE id IN ({placeholders})"

    with closing(get_db()) as conn:
        cursor = conn.execute(query, request_ids)
        conn.commit()
        deleted_count = cursor.rowcount

    app.logger.info(f"Admin {user['username']} bulk deleted {deleted_count} requests: {request_ids}")

    return jsonify({
        "status": "success",
        "message": f"Deleted {deleted_count} request(s)",
        "deleted_count": deleted_count
    })


@app.route("/api/requests/bulk-retry", methods=["POST"])
@login_required
def bulk_retry_requests():
    """Admin-only: Reset status of multiple failed requests to 'new' for retry."""
    user = current_user()
    if not user or not user["is_admin"]:
        return jsonify({"status": "error", "message": "Admin access required"}), 403

    request_ids = request.json.get("request_ids", [])
    if not request_ids or not isinstance(request_ids, list):
        return jsonify({"status": "error", "message": "Invalid request_ids"}), 400

    # Validate all IDs are integers
    try:
        request_ids = [int(rid) for rid in request_ids]
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "Invalid request ID format"}), 400

    if len(request_ids) > 100:
        return jsonify({"status": "error", "message": "Maximum 100 requests per bulk action"}), 400

    # Reset status to 'new' and clear error
    placeholders = ",".join("?" * len(request_ids))
    query = f"""
        UPDATE requests
        SET status = 'new', last_error = NULL, updated_at = datetime('now')
        WHERE id IN ({placeholders}) AND status = 'failed'
    """

    with closing(get_db()) as conn:
        cursor = conn.execute(query, request_ids)
        conn.commit()
        updated_count = cursor.rowcount

    app.logger.info(f"Admin {user['username']} bulk retried {updated_count} requests: {request_ids}")

    return jsonify({
        "status": "success",
        "message": f"Reset {updated_count} request(s) to 'new' status",
        "updated_count": updated_count
    })
```

**Frontend Changes** (`app/templates/requests.html`):

Add bulk actions toolbar after filter bar:
```html
{% if user.is_admin %}
<!-- Bulk Actions Toolbar (Hidden by default) -->
<div id="bulkToolbar" class="bulk-toolbar" style="display: none;">
  <div class="bulk-toolbar-content">
    <div class="bulk-selection-info">
      <input
        type="checkbox"
        id="selectAll"
        class="bulk-checkbox"
        onchange="toggleSelectAll(this.checked)"
      >
      <label for="selectAll" class="bulk-label">
        <span id="selectedCount">0</span> selected
      </label>
    </div>

    <div class="bulk-actions">
      <button
        class="btn btn-sm btn-danger"
        onclick="bulkDeleteRequests()"
        id="bulkDeleteBtn"
      >
        🗑️ Delete
      </button>
      <button
        class="btn btn-sm btn-secondary"
        onclick="bulkRetryRequests()"
        id="bulkRetryBtn"
      >
        🔄 Retry Failed
      </button>
      <button
        class="btn btn-sm btn-secondary"
        onclick="clearSelection()"
      >
        ✕ Cancel
      </button>
    </div>
  </div>
</div>
{% endif %}
```

Update request card to include checkbox (modify `app/templates/components/request_card.html`):
```html
<div class="request-card" data-request-id="{{ req.id }}">
  {% if user.is_admin %}
  <div class="card-checkbox-container">
    <input
      type="checkbox"
      class="request-checkbox"
      data-request-id="{{ req.id }}"
      data-status="{{ req.status }}"
      onchange="handleCheckboxChange()"
      onclick="event.stopPropagation()"
    >
  </div>
  {% endif %}

  <div class="card-content" onclick="openRequestModal({{ req.id }})">
    <!-- existing card content -->
  </div>
</div>
```

**JavaScript** (`app/static/js/app.js` additions):
```javascript
// Bulk Actions
let selectedRequests = new Set();

function handleCheckboxChange() {
  selectedRequests.clear();

  document.querySelectorAll('.request-checkbox:checked').forEach(checkbox => {
    selectedRequests.add({
      id: parseInt(checkbox.dataset.requestId),
      status: checkbox.dataset.status
    });
  });

  updateBulkToolbar();
}

function toggleSelectAll(checked) {
  document.querySelectorAll('.request-checkbox').forEach(checkbox => {
    checkbox.checked = checked;
  });
  handleCheckboxChange();
}

function updateBulkToolbar() {
  const toolbar = document.getElementById('bulkToolbar');
  const count = document.getElementById('selectedCount');
  const selectAll = document.getElementById('selectAll');
  const retryBtn = document.getElementById('bulkRetryBtn');

  count.textContent = selectedRequests.size;

  if (selectedRequests.size > 0) {
    toolbar.style.display = 'block';

    // Enable/disable retry button based on selection
    const hasFailedRequests = Array.from(selectedRequests).some(req => req.status === 'failed');
    retryBtn.disabled = !hasFailedRequests;
    retryBtn.title = hasFailedRequests ? 'Retry failed requests' : 'No failed requests selected';
  } else {
    toolbar.style.display = 'none';
    selectAll.checked = false;
  }
}

function clearSelection() {
  document.querySelectorAll('.request-checkbox').forEach(checkbox => {
    checkbox.checked = false;
  });
  selectedRequests.clear();
  updateBulkToolbar();
}

async function bulkDeleteRequests() {
  if (selectedRequests.size === 0) return;

  const confirmed = confirm(`Are you sure you want to delete ${selectedRequests.size} request(s)? This cannot be undone.`);
  if (!confirmed) return;

  const requestIds = Array.from(selectedRequests).map(req => req.id);

  try {
    const response = await fetch('/api/requests/bulk-delete', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ request_ids: requestIds })
    });

    const data = await response.json();

    if (data.status === 'success') {
      showToast(data.message, 'success');
      // Reload page to show updated list
      setTimeout(() => window.location.reload(), 1000);
    } else {
      showToast(`Error: ${data.message}`, 'danger');
    }
  } catch (error) {
    showToast('Failed to delete requests', 'danger');
    console.error('Bulk delete error:', error);
  }
}

async function bulkRetryRequests() {
  const failedRequests = Array.from(selectedRequests).filter(req => req.status === 'failed');

  if (failedRequests.length === 0) {
    showToast('No failed requests selected', 'warning');
    return;
  }

  const confirmed = confirm(`Reset ${failedRequests.length} failed request(s) to 'new' status for retry?`);
  if (!confirmed) return;

  const requestIds = failedRequests.map(req => req.id);

  try {
    const response = await fetch('/api/requests/bulk-retry', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ request_ids: requestIds })
    });

    const data = await response.json();

    if (data.status === 'success') {
      showToast(data.message, 'success');
      // Reload page to show updated list
      setTimeout(() => window.location.reload(), 1000);
    } else {
      showToast(`Error: ${data.message}`, 'danger');
    }
  } catch (error) {
    showToast('Failed to retry requests', 'danger');
    console.error('Bulk retry error:', error);
  }
}
```

**CSS Additions** (`requests.html` extra_css block):
```css
/* Bulk Actions */
.bulk-toolbar {
  position: sticky;
  top: 145px; /* Below header + filter bar */
  z-index: 85;
  background: var(--accent);
  color: white;
  padding: var(--spacing-sm) var(--spacing-md);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: var(--shadow-md);
}

.bulk-toolbar-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
}

.bulk-selection-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.bulk-checkbox {
  width: 20px;
  height: 20px;
  cursor: pointer;
}

.bulk-label {
  font-weight: 600;
  font-size: var(--font-base);
  margin: 0;
  cursor: pointer;
}

.bulk-actions {
  display: flex;
  gap: var(--spacing-xs);
  flex-wrap: wrap;
}

.bulk-actions .btn {
  background: white;
  color: var(--text-primary);
  border: none;
}

.bulk-actions .btn-danger {
  background: var(--danger);
  color: white;
}

.bulk-actions .btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Request Card Checkbox */
.request-card {
  display: flex;
  gap: var(--spacing-sm);
  align-items: flex-start;
}

.card-checkbox-container {
  padding-top: var(--spacing-xs);
}

.request-checkbox {
  width: 20px;
  height: 20px;
  cursor: pointer;
}

.card-content {
  flex: 1;
  cursor: pointer;
}

/* Mobile adjustments */
@media (max-width: 640px) {
  .bulk-toolbar-content {
    flex-direction: column;
    align-items: stretch;
  }

  .bulk-actions {
    justify-content: stretch;
  }

  .bulk-actions .btn {
    flex: 1;
  }
}
```

#### Testing Checklist:
- [ ] Checkboxes appear only for admins
- [ ] Selecting checkboxes shows bulk toolbar
- [ ] Selected count updates correctly
- [ ] Select all checkbox works
- [ ] Deselecting all hides toolbar
- [ ] Delete action requires confirmation
- [ ] Delete removes selected requests
- [ ] Retry only works on failed requests
- [ ] Retry resets status to 'new' and clears error
- [ ] Non-admin users cannot access bulk endpoints
- [ ] Maximum 100 requests per bulk action enforced
- [ ] Toast notifications appear for success/error
- [ ] Page reloads after successful bulk action
- [ ] Clicking checkbox doesn't open modal

---

## Implementation Sequence

### Phase 1: Search & Filter (1.5 hours)
1. Update `app.py` list_requests route with filter logic
2. Add filter bar to `requests.html`
3. Add JavaScript for search debounce and filter pills
4. Add CSS for filter bar components
5. Test all filter combinations

### Phase 2: Request Details Modal (1 hour)
1. Add API endpoint for request details
2. Add modal HTML to `requests.html`
3. Make request cards clickable
4. Add JavaScript for modal open/close/render
5. Add CSS for modal styling
6. Test modal functionality

### Phase 3: Bulk Actions (1-1.5 hours)
1. Add bulk delete/retry API endpoints
2. Add bulk toolbar to `requests.html`
3. Add checkboxes to request cards
4. Add JavaScript for selection and bulk operations
5. Add CSS for bulk UI components
6. Test bulk operations

### Total Estimated Time: 3.5-4 hours

---

## Testing Strategy

### Unit Testing (pytest)
Add tests to `tests/test_app.py`:
- Test filter query building (search, status, user)
- Test API endpoint `/api/request/<id>` (auth, not found, success)
- Test bulk delete endpoint (auth, validation, execution)
- Test bulk retry endpoint (auth, validation, execution)

### Manual Testing
- Test on mobile (375px, 390px, 768px)
- Test on desktop (1024px+)
- Test with 0, 1, 10, 50 requests
- Test with different user roles (admin, non-admin)
- Test keyboard navigation (tab, enter, escape)
- Test accessibility (screen reader, color contrast)

### Performance Testing
- Test filter performance with 100+ requests
- Test modal load time
- Test bulk operations with max requests (100)

---

## Success Criteria

- ✅ Users can search requests by artist/album name
- ✅ Users can filter requests by status
- ✅ Admins can filter between all/own requests
- ✅ Active filters display clearly with counts
- ✅ Users can click request cards to view full details
- ✅ Modal displays all request metadata
- ✅ Modal closes on ESC, backdrop click, close button
- ✅ Admins can select multiple requests
- ✅ Admins can bulk delete requests
- ✅ Admins can bulk retry failed requests
- ✅ All features work on mobile and desktop
- ✅ All features maintain existing security controls
- ✅ Zero regression in existing functionality

---

## Future Enhancements (v0.5.0+)

Ideas for future versions:
- **Advanced Filters**: Date range, user filter, custom tags
- **Sorting**: Sort by created date, artist name, status
- **Export**: Export filtered requests to CSV/JSON
- **Request History**: Archive completed/deleted requests
- **Inline Edit**: Edit artist/album/note without opening modal
- **Drag & Drop**: Reorder requests (priority queue)
- **Push Notifications**: Notify when request status changes
- **Request Comments**: Add notes/comments to requests
- **Batch Import**: Upload CSV of requests

---

## Documentation Updates

After implementation:
- [ ] Update `HANDOFF-JUKEBOX.md` with v0.4.0 features
- [ ] Update `MOBILE-UX-PROGRESS.md` with new UI components
- [ ] Create `FEATURE-SEARCH-FILTER.md` with usage guide
- [ ] Update screenshots in `docs/`
- [ ] Update API documentation (if creating separate API docs)

---

## Rollback Plan

If issues arise:
```bash
# Revert to v0.3.0
git revert <v0.4.0-commit-hash>
docker compose build jukebox
docker compose up -d jukebox

# Database: No schema changes, so no migration rollback needed
```

---

**Ready to begin implementation?**
