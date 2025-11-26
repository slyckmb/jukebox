# Artist Staging Workflow - Requirements

**Version**: v0.6.0
**Feature**: Admin Staging Area for Artist Pulls
**Priority**: HIGH (Core v0.6.0 feature)

---

## Problem Statement

Current workflow issues:
1. Users type album names that don't exist in MusicBrainz yet
2. No way to validate artist before adding to Lidarr
3. Wrong artists pollute user libraries
4. Manual album entry prone to typos/mismatches

---

## Solution: Two-Phase Commit with Admin Staging

### Phase 1: Pull Albums (Staging)
User validates artist → clicks "Pull Albums" → artist added to **admin staging area** (unmonitored)

### Phase 2: Commit Album (User Space)
User selects album → artist **moved** to user space → album monitored → download triggered

---

## Functional Requirements

### FR1: Admin Staging Area
- **FR1.1**: Artists added to staging use admin root folder: `/data/media/music/lidarr_admin`
- **FR1.2**: Artists added to staging use tag: `staging` (or `requested_by_admin`)
- **FR1.3**: Artists in staging have `monitored = false`
- **FR1.4**: Albums in staging have `monitored = false` (no downloads)
- **FR1.5**: Staging artists fetch full album list from MusicBrainz/Lidarr

### FR2: Staging Reuse & Refresh
- **FR2.1**: If artist exists in staging, reuse it (don't duplicate)
- **FR2.2**: Track `last_refreshed_at` timestamp for each staged artist
- **FR2.3**: Auto-refresh if `last_refreshed_at > 7 days ago`
- **FR2.4**: Refresh triggers Lidarr's `RefreshArtist` command
- **FR2.5**: Fresh staging artists (< 7 days) load instantly (no delay)

### FR3: Move to User Space
- **FR3.1**: When user commits to album, move artist from staging to user space
- **FR3.2**: Update `rootFolderPath` from admin → user folder
- **FR3.3**: Update `tags` from `staging` → `requested_by_{username}`
- **FR3.4**: Set selected album's `monitored = true`
- **FR3.5**: Trigger `AlbumSearch` command for immediate download

### FR4: Artist Already in User Space
- **FR4.1**: If artist exists in user's library, skip staging entirely
- **FR4.2**: Show album dropdown directly (from user's artist)
- **FR4.3**: Support existing unmonitored album workflow (flip to monitored)

### FR5: User Experience
- **FR5.1**: "Pull Albums" button appears after artist validation
- **FR5.2**: Show loading states:
  - New artist: "Loading albums from Lidarr..." (3-10s)
  - Stale artist: "Refreshing albums..." (2-5s)
  - Fresh artist: Instant (no spinner)
- **FR5.3**: Album dropdown shows all albums for artist
- **FR5.4**: Clear feedback on successful commit
- **FR5.5**: Handle errors gracefully (Lidarr failures, timeouts)

### FR6: Database Tracking
- **FR6.1**: Track staging artists in `artist_staging` table:
  ```sql
  CREATE TABLE artist_staging (
      id INTEGER PRIMARY KEY,
      user_id INTEGER,  -- Who first pulled
      artist_name TEXT,
      lidarr_artist_id INTEGER,
      mb_artist_id TEXT,
      created_at TEXT,
      last_refreshed_at TEXT,
      refresh_count INTEGER DEFAULT 0
  );
  ```
- **FR6.2**: Link requests to staging via `artist_staging_id` (optional)

### FR7: Cleanup (Future)
- **FR7.1**: Monthly cleanup job deletes orphaned staging artists
- **FR7.2**: Criteria:
  - `last_refreshed_at > 30 days ago`
  - No associated committed requests
  - No monitored albums in Lidarr
- **FR7.3**: Admin can view/manage staging pool (future UI)

---

## Non-Functional Requirements

### NFR1: Performance
- Staging reuse reduces Lidarr/MB API load
- Fresh staging artists (< 7 days) provide instant results
- Refresh operations complete in 2-5 seconds

### NFR2: Reliability
- Polling with timeout for album population (max 20s)
- Graceful degradation if Lidarr is slow/unavailable
- Transaction safety (move operations are atomic)

### NFR3: Maintainability
- Refresh threshold configurable via environment variable
- Clear logging for staging operations
- Database migrations for new table

---

## User Stories

### US1: New Artist Request
**As a** user
**I want to** validate an artist before adding to my library
**So that** I don't pollute my collection with wrong artists

**Acceptance Criteria**:
- User types "taylor swift"
- User sees artist details (bio, image, years active)
- User clicks "Pull Albums"
- System adds artist to staging (admin space)
- User sees album dropdown within 10 seconds
- User selects "Folklore"
- System moves artist to user space and starts download

### US2: Reuse Staged Artist
**As a** user
**I want to** benefit from artists other users have pulled
**So that** I get faster results

**Acceptance Criteria**:
- User A pulls "Taylor Swift" on Day 1
- User B requests "Taylor Swift" on Day 3
- System reuses staging artist (fresh, < 7 days)
- User B sees album dropdown instantly
- Both users have separate copies in their libraries after commit

### US3: Stale Staged Artist
**As a** user
**I want to** see current album listings
**So that** I can request newly released albums

**Acceptance Criteria**:
- Artist pulled 15 days ago (stale)
- User clicks "Pull Albums"
- System refreshes from Lidarr
- User sees "Refreshing albums..." for 2-5 seconds
- Updated album list includes new releases

### US4: Existing Artist in User Library
**As a** user
**I want to** request additional albums from artists I already have
**So that** I can expand my collection

**Acceptance Criteria**:
- User previously requested "Taylor Swift - Folklore"
- User types "taylor swift" again
- System detects artist in user space
- Skips staging entirely
- Shows album dropdown immediately (from user's artist)
- User selects new album → monitored + downloaded

---

## Technical Architecture

### Components

#### 1. Backend Functions (app.py)
- `create_artist_in_staging(artist_name, mb_artist_id)`
- `find_staging_artist(mb_artist_id)`
- `trigger_artist_refresh(lidarr_artist_id)`
- `poll_for_albums(lidarr_artist_id, timeout=20)`
- `move_artist_to_user(lidarr_artist_id, username)`
- `check_artist_in_user_space(username, mb_artist_id)`

#### 2. Database
- New table: `artist_staging`
- New column: `requests.artist_staging_id` (optional)

#### 3. Frontend (new_request.html)
- "Pull Albums" button (appears after artist validation)
- Album dropdown (populated from Lidarr)
- Loading states with context-aware messages

#### 4. API Endpoints
- Existing: `/api/search/artist` (MB validation)
- New: `/api/artist/pull-albums` (trigger staging)
- New: `/api/artist/albums/{lidarr_id}` (get album list)
- Existing: `/request/new` (commit album, move artist)

---

## Implementation Phases

### Stage 3: Core Staging Workflow (3-4 hours)
1. Database migration (`artist_staging` table)
2. Backend functions (staging, refresh, move)
3. Frontend UI ("Pull Albums" button, album dropdown)
4. API endpoints
5. Testing

### Stage 4: Optimizations (2-3 hours)
1. Reuse logic (check staging before adding)
2. User space check (skip staging for existing artists)
3. Refresh logic (time-based staleness)
4. Polish UX (loading states, error handling)

### Future: Cleanup & Admin Tools
1. Cleanup job (`cleanup_staging_artists()`)
2. Admin UI (view staging pool, manual cleanup)
3. Analytics (most pulled artists, refresh patterns)

---

## Configuration

```python
# Environment variables
STAGING_REFRESH_DAYS = 7  # Refresh threshold
STAGING_POLL_TIMEOUT = 20  # Max wait for album population
STAGING_POLL_INTERVAL = 2  # Check every 2 seconds
```

---

## Success Metrics

- 📊 **Staging reuse rate**: % of pulls that use existing staging artists
- ⚡ **Instant load rate**: % of pulls that are instant (< 1s)
- 🎯 **Commit rate**: % of pulls that result in album commits (vs abandons)
- 🗑️ **Cleanup volume**: Staging artists deleted monthly (low = good reuse)

---

## Risk Mitigation

### Risk 1: Lidarr Slow to Populate Albums
**Mitigation**: Polling with timeout (20s max), clear error message

### Risk 2: Race Condition (Duplicate Staging)
**Mitigation**: Check before add, use MB ID as unique key

### Risk 3: User Abandons After Pull
**Mitigation**: Expected behavior, cleanup handles orphans

### Risk 4: Stale Data Shown to User
**Mitigation**: 7-day refresh threshold, configurable

---

## Testing Checklist

### Unit Tests
- [ ] `create_artist_in_staging()` - adds unmonitored artist
- [ ] `find_staging_artist()` - finds by MB ID
- [ ] `trigger_artist_refresh()` - sends command to Lidarr
- [ ] `move_artist_to_user()` - updates path, tags, monitored

### Integration Tests
- [ ] Full flow: Pull → Poll → Dropdown → Commit → Download
- [ ] Reuse flow: User B benefits from User A's pull
- [ ] Refresh flow: Stale artist gets updated data
- [ ] Existing artist flow: Skip staging for user space artists

### Manual Tests
- [ ] "Taylor Swift" (new artist) → full flow
- [ ] "Taylor Swift" again (reuse) → instant
- [ ] Wait 8 days → "Taylor Swift" (refresh) → updated
- [ ] Artist in library → skip to albums

---

## Open Questions

1. ❓ Should "Pull Albums" button be automatic or manual?
   - **Decision**: Manual (user control, validates choice)

2. ❓ What if Lidarr takes > 20s to populate albums?
   - **Decision**: Show timeout error, suggest retry

3. ❓ Should we show staging vs user space to user?
   - **Decision**: No (implementation detail, confusing)

4. ❓ Cleanup: Manual admin action or cron job?
   - **Decision**: Manual for now, cron in future

---

## Future Enhancements

- Real-time progress (WebSocket) instead of polling
- Staging pool browser (admin UI)
- "Recently pulled" suggestions
- Smart prefetch (pre-pull popular artists)
- Collaborative filtering (users who pulled X also pulled Y)
