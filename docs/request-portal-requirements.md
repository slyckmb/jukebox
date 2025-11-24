# Jukebox (Lidarr Request Portal) – Requirements

**Version**: 0.2.0
**Last Updated**: 2025-11-23
**Status**: Production (v0.2.0 mobile UX complete ✅)

---

## Document Status

### Current Implementation (v0.2.0) ✅ Complete
- ✅ Core functionality deployed
- ✅ Live at https://jukebox.bikejeepyoga.com
- ✅ Lidarr integration working
- ✅ User authentication implemented
- ✅ Request tracking functional
- ✅ Mobile-first UX redesign complete
- ✅ Card-based layouts implemented
- ✅ Toast notifications system
- ✅ Touch-friendly navigation (FAB + bottom nav)
- ✅ All mobile UX requirements (R14-R36) validated

### Implementation History
- **v0.1.0** (2025-11-15): Initial release with basic HTML UI
- **v0.2.0** (2025-11-23): Mobile-first UX redesign (6 stages complete)

See `MOBILE-UX-PROGRESS.md` for complete implementation details.

---

## 1. Purpose

Provide a simple, secure web front end for non-admin users to request music.
Each request is translated into a Lidarr API call so that requested music is downloaded and eventually appears in Jellyfin/Navidrome for streaming and raw-file download.

The app should be:

- **Simple (KISS)**: Minimal dependencies, straightforward workflows
- **Robust and reliable**: Error handling, status tracking, retries
- **Reasonably secure**: Per-user accounts, no direct Lidarr access
- **Mobile-friendly**: Primary interface is phone/tablet (v0.2.0+)

---

## 2. System Context

- **Environment**: Runs as a Docker container on the same Docker network as Lidarr
- **Upstream service**: Lidarr at `http://lidarr:8686` (reachable as `lidarr` inside Docker network)
- **Downstream consumers**: Jellyfin and/or Navidrome reading the same music library path as Lidarr
- **Users**: One account per human user; each user can log in and submit requests
- **Access**: Public internet via Cloudflare tunnel at `https://jukebox.bikejeepyoga.com`

### Integration Points

```
┌─────────┐      HTTPS       ┌──────────────┐
│ User    │ ───────────────> │ Cloudflare   │
│ (Phone) │                  │ Tunnel       │
└─────────┘                  └──────┬───────┘
                                    │
                                    ▼
                            ┌───────────────┐
                            │ Jukebox       │
                            │ (Flask)       │
                            └───────┬───────┘
                                    │ HTTP API
                                    ▼
                            ┌───────────────┐      ┌──────────────┐
                            │ Lidarr        │ ───> │ Music Files  │
                            │ (Music mgmt)  │      │ /data/media  │
                            └───────────────┘      └──────────────┘
                                    │
                                    ▼
                            ┌───────────────────────────┐
                            │ Jellyfin / Navidrome      │
                            │ (Streaming)               │
                            └───────────────────────────┘
```

---

## 3. High-Level Workflow

### User Request Flow

1. User opens Jukebox in mobile browser (https://jukebox.bikejeepyoga.com)
2. User logs in with username/password
3. User taps "New Request" button (FAB or bottom nav)
4. User fills form:
   - Artist name (required)
   - Album title (optional)
   - Note (optional, e.g., "Prefer FLAC")
5. User submits request
6. Jukebox stores request in SQLite with status `new`
7. Jukebox calls Lidarr API:
   - Looks up artist metadata (gets `foreignArtistId`)
   - Gets or creates tag: `requested_by_<username>`
   - POSTs artist to Lidarr with per-user root folder
8. Jukebox updates request status:
   - `submitted` if successful
   - `failed` if error (with error message)
9. User sees success/error toast notification
10. User redirected to request list (sees new card)

### Background Processing (Future)

- Periodic job queries Lidarr for download progress
- Updates request status: `downloading` → `complete`
- User sees updated status badge in request list

### Media Availability

- Lidarr downloads music to `/data/media/music/lidarr_<username>/`
- Jellyfin/Navidrome scan library periodically
- Music appears in user's streaming apps

---

## 4. Functional Requirements

### 4.1 Authentication & Authorization

#### User Authentication (Implemented)
- **R1**: The portal SHALL support per-user accounts
- **R2**: A user SHALL authenticate with username + password
- **R3**: Passwords SHALL be stored as salted hashes using Werkzeug `generate_password_hash()`
- **R4**: Sessions SHALL be cookie-based using Flask's secure session mechanism
- **R5**: There SHALL be an "admin" flag in the user table to differentiate admin vs normal user

#### Authorization Rules (Implemented)
- **R6**: Admin users MAY list all requests; normal users SHOULD only see their own
- **R7**: Admin users MAY create new user accounts
- **R8**: Non-admin users SHALL NOT access user creation endpoints
- **R9**: Users SHALL only submit requests under their own username (enforced server-side)

### 4.2 Request Capture

#### Required Fields (Implemented)
Each request SHALL capture:

- **Request ID**: Auto-incrementing integer primary key
- **Requesting user**: Foreign key to `users.id`
- **Artist name**: Required text field
- **Album title**: Optional text field (empty means "all albums")
- **Note**: Optional free-text field (max 500 chars recommended)
- **Status**: One of `new`, `submitted`, `existing`, `failed`
- **Tag**: Auto-generated as `requested_by_<username>`
- **Root folder path**: Auto-generated as `/data/media/music/lidarr_<username>`
- **Timestamps**: `created_at`, `updated_at` (ISO 8601 format)

#### Optional Fields (Implemented)
- **lidarr_artist_id**: Integer, populated after successful Lidarr API call
- **lidarr_album_id**: Integer, for future album-specific requests
- **last_error**: Text, populated when status is `failed`

### 4.3 Request Status States

#### Status Definitions (Implemented)
- **`new`**: Created in portal, not yet sent to Lidarr
- **`submitted`**: Successfully sent to Lidarr; artist added/monitored
- **`existing`**: Lidarr indicated the artist/album already exists
- **`failed`**: Attempt to send to Lidarr failed (network, validation, or API error)

#### Future Status States (Planned)
- **`downloading`**: Lidarr is actively downloading the music (requires polling)
- **`complete`**: Music fully downloaded and available (requires polling)

#### Status Transitions
```
new ─────┬──> submitted ───┬──> downloading ──> complete
         │                 │
         └──> failed       └──> existing
```

### 4.4 API Forwarding to Lidarr

#### Lidarr Integration (Implemented)
- **R10**: The app SHALL call Lidarr using `LIDARR_API_KEY` from environment
- **R11**: Base URL SHALL be configurable via `LIDARR_URL` (default: `http://lidarr:8686/api/v1`)
- **R12**: Each new request SHALL:
  1. Call `/artist/lookup?term=<artist_name>` to get metadata
  2. Extract `foreignArtistId` from response
  3. Call `/tag` to get or create user tag
  4. POST to `/artist` with payload:
     ```json
     {
       "artistName": "Pink Floyd",
       "foreignArtistId": "83d91898-7763-47d7-b03b-b92132375c47",
       "monitored": true,
       "qualityProfileId": 1,
       "metadataProfileId": 1,
       "rootFolderPath": "/data/media/music/lidarr_mike",
       "tags": [42],
       "addOptions": {
         "monitor": "all",
         "searchForMissingAlbums": true
       },
       "path": "/data/media/music/lidarr_mike/Pink Floyd"
     }
     ```

- **R13**: On failure (non-2xx), the portal SHALL:
  - Log the error
  - Set request status to `failed`
  - Store error message in `last_error` field
  - Display user-friendly error toast

#### Error Handling (Implemented)
- Network timeouts (10 second timeout)
- Lidarr API errors (4xx, 5xx)
- Invalid artist names (no results from lookup)
- Missing `foreignArtistId` in response

---

## 5. User Interface Requirements

### 5.1 Web UI Endpoints (v0.1.0 - Current)

**Implemented with basic HTML:**
- `GET /login` – Render login form
- `POST /login` – Authenticate user
- `POST /logout` – Destroy session
- `GET /` or `/requests` – List current user's requests
- `GET /request/new` – Render new request form
- `POST /request/new` – Create request and forward to Lidarr
- `GET /users/new` – Render user creation form (admin only)
- `POST /users/new` – Create new user (admin only)

### 5.2 Web UI Endpoints (v0.2.0 - Mobile UX)

**Enhanced with mobile-first templates:**

All endpoints remain the same, but rendering changes:
- Templates use `render_template()` instead of `render_template_string()`
- Mobile-first responsive design
- Card-based layouts (not tables)
- Toast notifications (not flash messages in page)
- Touch-friendly navigation (FAB, bottom nav)
- Loading states and animations

See `MOBILE-UX-PLAN.md` for detailed UX specifications.

### 5.3 JSON API Endpoints (Implemented)

**For programmatic access and testing:**
- `GET /api/health` – Return `{ "status": "ok" }`
- `POST /api/login` – Accept `{ "username", "password" }`, return session cookie
- `GET /api/requests` – Return JSON array of user's requests
- `POST /api/requests` – Accept `{ "artist_name", "album_title", "note" }`, create request
- `GET /api/requests/<id>` – Return single request JSON

All JSON API endpoints SHALL return appropriate HTTP status codes:
- `200 OK` for successful operations
- `201 Created` for new resource creation
- `400 Bad Request` for validation errors
- `401 Unauthorized` for unauthenticated requests
- `403 Forbidden` for unauthorized access
- `404 Not Found` for missing resources
- `500 Internal Server Error` for server errors

### 5.4 Mobile UX Requirements (v0.2.0)

#### Responsive Design
- **R14**: All pages SHALL be mobile-first responsive
- **R15**: Minimum supported width: 320px (iPhone SE)
- **R16**: Touch targets SHALL be ≥ 44px (Apple HIG recommendation)
- **R17**: Font size SHALL be ≥ 16px on inputs to prevent iOS zoom

#### Visual Design
- **R18**: Request list SHALL use card layout (not HTML tables)
- **R19**: Status SHALL be indicated by color-coded badges:
  - Blue: `new`
  - Green: `submitted`
  - Red: `failed`
  - Gray: `existing`
- **R20**: Empty states SHALL provide clear next actions
- **R21**: Loading states SHALL appear during asynchronous operations

#### Navigation
- **R22**: Mobile devices SHALL show bottom navigation bar
- **R23**: Primary action (new request) SHALL use Floating Action Button (FAB)
- **R24**: Desktop devices (>768px) SHALL hide bottom nav
- **R25**: Back buttons SHALL provide clear navigation context

#### Notifications
- **R26**: Flash messages SHALL render as toast notifications
- **R27**: Toasts SHALL auto-dismiss after 3-5 seconds
- **R28**: Toasts SHALL be color-coded by type (success/error/info)

#### Accessibility
- **R29**: All interactive elements SHALL be keyboard accessible
- **R30**: ARIA labels SHALL be present for screen readers
- **R31**: Color contrast SHALL meet WCAG AA standards (4.5:1)
- **R32**: Dark mode SHALL respect system preference

#### Performance
- **R33**: Lighthouse Performance score SHALL be ≥ 90
- **R34**: First Contentful Paint SHALL be < 1.5s
- **R35**: Time to Interactive SHALL be < 3s
- **R36**: Total page weight SHALL be < 100KB (excluding user content)

---

## 6. Non-Functional Requirements

### 6.1 Technology Stack (Implemented)

- **N1**: KISS principle: minimal dependencies
  - Flask 3.1.2 (web framework)
  - Requests 2.32.5 (HTTP client)
  - Werkzeug 3.1.3 (password hashing, utilities)
  - SQLite3 (database, Python stdlib)
- **N2**: Deployment: Docker container
- **N3**: Configuration: Environment variables
- **N4**: Offline build: Vendored Python wheels in `vendor/`

### 6.2 Security (Implemented)

- **N5**: Password hashing: Werkzeug `generate_password_hash()` with salt
- **N6**: Session security: Flask secure sessions with secret key
- **N7**: HTTPS: Terminated at Cloudflare tunnel (TLS 1.3)
- **N8**: Secret management:
  - Secrets stored in `/mnt/config/secrets/` (vault-managed)
  - Support for `*_FILE` environment variables
  - API keys never logged or exposed in UI
- **N9**: Input validation:
  - Server-side validation on all form submissions
  - SQL injection prevention via parameterized queries
  - XSS prevention via Jinja2 auto-escaping

### 6.3 Reliability (Implemented)

- **N10**: Error handling: All Lidarr API calls have timeout and exception handling
- **N11**: Request tracking: All requests stored in DB regardless of Lidarr outcome
- **N12**: Status reporting: Clear error messages in `last_error` field
- **N13**: Container restart: `restart: unless-stopped` in docker-compose

### 6.4 Logging (Implemented)

- **N14**: Application logs:
  - Request creation events
  - Lidarr API call outcomes
  - Authentication events
  - Error conditions with stack traces
- **N15**: Log level: Configurable via environment (default: INFO)
- **N16**: Log format: Timestamp, level, message
- **N17**: Log destination: Docker stdout (captured by Docker logging driver)

### 6.5 Performance (Current)

- **N18**: Response time: < 500ms for page loads (excluding Lidarr API)
- **N19**: Lidarr API timeout: 10 seconds
- **N20**: Concurrent users: Designed for 5-10 users (family/friends)
- **N21**: Database: SQLite adequate for < 10,000 requests

### 6.6 Maintainability

- **N22**: Code style: Python Black formatting
- **N23**: Testing: Pytest unit tests with mocked Lidarr API
- **N24**: Documentation:
  - Inline code comments for complex logic
  - Separate docs for requirements, handoff, UX plans
- **N25**: Version control: Git with semantic commit messages

---

## 7. Database Requirements (SQLite)

### 7.1 Schema (Implemented)

#### users table
```sql
CREATE TABLE users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    is_admin        INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
```

#### requests table
```sql
CREATE TABLE requests (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             INTEGER NOT NULL,
    artist_name         TEXT NOT NULL,
    album_title         TEXT,
    note                TEXT,
    status              TEXT NOT NULL DEFAULT 'new',
    tag                 TEXT NOT NULL,
    root_folder_path    TEXT NOT NULL,
    lidarr_artist_id    INTEGER,
    lidarr_album_id     INTEGER,
    last_error          TEXT,
    created_at          TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at          TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_requests_user_id ON requests(user_id);
CREATE INDEX idx_requests_status ON requests(status);
CREATE INDEX idx_requests_artist ON requests(artist_name);
```

### 7.2 Data Management

- **Database path**: `/app/data/requests.db` (inside container)
- **Volume mount**: `./data:/app/data` (persistent storage)
- **Backup strategy**: Volume-level backups (host responsibility)
- **Migration**: Schema changes applied via `init_db()` on startup

---

## 8. Configuration & Deployment

### 8.1 Environment Variables (Required)

```bash
# Lidarr integration
LIDARR_URL=http://lidarr:8686/api/v1
LIDARR_API_KEY=<from vault>
LIDARR_QUALITY_PROFILE_ID=1
LIDARR_METADATA_PROFILE_ID=1

# Music library paths
MUSIC_ROOT_BASE=/data/media/music

# Database
DB_PATH=/app/data/requests.db

# Security
FLASK_SECRET_KEY=<from vault>
```

### 8.2 Secrets Management (Implemented)

Follows `global/docs/SECRETS_POLICY.md`:

**Config files:**
- `.env` (tracked): Non-secret defaults
- `/mnt/config/secrets/jukebox/env` (vault): Flask secret key
- `/mnt/config/secrets/bash/bash_lidarr-api-key.env` (vault): Lidarr API key (reused)

**Docker Compose mounts:**
```yaml
env_file:
  - .env
  - /mnt/config/secrets/jukebox/env
  - /mnt/config/secrets/bash/bash_lidarr-api-key.env
```

**Secret file indirection:**
```bash
# In vault-managed env file
FLASK_SECRET_KEY_FILE=/mnt/config/secrets/jukebox/flask-secret.key
```

App code supports `*_FILE` environment variables for all secrets.

### 8.3 Docker Deployment (Implemented)

**Dockerfile:** Offline build with vendored wheels
```dockerfile
FROM python:3.12-slim
COPY vendor /tmp/vendor
RUN pip install --no-index --find-links /tmp/vendor flask requests
COPY app/app.py /app/app.py
CMD ["python", "app.py"]
```

**docker-compose.yml:**
```yaml
services:
  jukebox:
    build:
      context: .
      dockerfile: docker/Dockerfile
      network: gluetun_network
    container_name: jukebox
    restart: unless-stopped
    env_file:
      - .env
      - /mnt/config/secrets/jukebox/env
      - /mnt/config/secrets/bash/bash_lidarr-api-key.env
    volumes:
      - ./data:/app/data
    ports:
      - "5000:5000"
    networks:
      - gluetun_network
```

**Network:** Shared `gluetun_network` with Lidarr

### 8.4 Cloudflare Tunnel (Implemented)

**Public access:** https://jukebox.bikejeepyoga.com

**Cloudflared ingress rule:**
```yaml
- hostname: jukebox.bikejeepyoga.com
  service: http://jukebox:5000
```

**DNS:** Managed via `cloudflared tunnel route dns glider-tunnel jukebox.bikejeepyoga.com`

---

## 9. Testing Requirements

### 9.1 Automated Testing (Implemented)

**Pytest tests:** `tests/test_app.py`

Test coverage:
- ✅ Artist payload includes `foreignArtistId` and tag IDs
- ✅ API flow creates and lists requests
- ✅ Path construction per-user
- ✅ Mocked Lidarr responses

**Run tests:**
```bash
python -m pytest tests/test_app.py -v
```

### 9.2 Manual Testing (Current)

**Test cases:**
1. Login flow (valid/invalid credentials)
2. Request creation (all fields, minimal fields)
3. Request list display
4. Admin user creation
5. Non-admin access restrictions
6. Error handling (network errors, Lidarr errors)

### 9.3 Mobile Testing (v0.2.0 - Planned)

**Cross-device testing:**
- iPhone SE (375px)
- iPhone 12 Pro (390px)
- Android Pixel 5 (393px)
- iPad Mini (768px)
- Desktop (1024px+)

**Test checklist per stage:**
- Visual layout correct
- Touch targets ≥ 44px
- No horizontal scroll
- Toasts display properly
- Navigation functional
- Forms submit successfully

See `MOBILE-UX-STAGES.md` for detailed test procedures.

---

## 10. Known Issues & Future Enhancements

### 10.1 Known Issues (Current)

**Outstanding bug:**
- ⚠️ Two failed requests in production DB with error: `ForeignArtistId must not be empty`
- **Root cause**: Some Lidarr lookup responses missing `foreignArtistId`
- **Status**: Under investigation (see `HANDOFF-JUKEBOX.md`)

**UX issues:**
- ⚠️ UI not optimized for mobile (v0.1.0 uses basic HTML)
- **Fix**: Mobile UX redesign in progress (v0.2.0)

### 10.2 Future Enhancements (Planned)

**Phase 2 - Status Polling:**
- [ ] Background job to query Lidarr for download progress
- [ ] Update request status to `downloading` / `complete`
- [ ] User notifications when music is ready

**Phase 3 - Advanced UX:**
- [ ] Search/filter requests by artist, album, status
- [ ] Request details modal with Lidarr metadata
- [ ] Retry button for failed requests
- [ ] Bulk actions (admin)
- [ ] Request history/archive

**Phase 4 - PWA Features:**
- [ ] Add to home screen prompt
- [ ] Offline support (service worker)
- [ ] Push notifications
- [ ] Background sync

**Phase 5 - User Features:**
- [ ] User profile page
- [ ] Password change flow
- [ ] Email notifications
- [ ] Request comments/updates

---

## 11. Success Criteria

### v0.1.0 (Completed ✅)
- [x] User authentication working
- [x] Request creation and Lidarr forwarding functional
- [x] Admin user creation implemented
- [x] Deployed to production
- [x] Cloudflare tunnel configured
- [x] Basic UI functional (desktop-focused)

### v0.2.0 (In Progress 🔄)
- [ ] Mobile-first UX implemented
- [ ] Card-based request list
- [ ] Touch-friendly navigation
- [ ] Toast notifications
- [ ] Lighthouse score ≥ 90
- [ ] Tested on 3+ real mobile devices
- [ ] All pytest tests passing
- [ ] Documentation updated

### v0.3.0 (Future)
- [ ] Status polling implemented
- [ ] Download progress tracking
- [ ] User notifications
- [ ] Search/filter functionality
- [ ] Request details modal

---

## 12. References

### Internal Documentation
- `HANDOFF-JUKEBOX.md` - Current implementation status and debugging notes
- `MOBILE-UX-PLAN.md` - Mobile UX redesign overview
- `MOBILE-UX-STAGES.md` - Staged implementation guide
- `MOBILE-UX-PROGRESS.md` - Real-time progress tracking
- `SECRETS.md` - Secrets management and wiring

### External References
- Flask documentation: https://flask.palletsprojects.com/
- Lidarr API documentation: https://lidarr.audio/docs/api/
- Werkzeug security: https://werkzeug.palletsprojects.com/en/latest/utils/#werkzeug.security
- Apple Human Interface Guidelines (touch targets): https://developer.apple.com/design/human-interface-guidelines/

---

**Document Version**: 0.2.0
**Last Updated**: 2025-11-23
**Next Review**: After mobile UX implementation (Stage 6 complete)
