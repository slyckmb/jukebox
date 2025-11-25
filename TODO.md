# Jukebox TODO

**Current Sprint**: UI Cleanup (v0.6.0)

---

## Active Tasks

### 1. Show/Hide Failed Requests Toggle
- [ ] Add toggle button to requests page header
- [ ] Store preference in localStorage
- [ ] Filter requests on client side
- [ ] Test on mobile

### 2. Delete Request Button
- [ ] Add DELETE /api/requests/<id> endpoint
- [ ] Add delete icon to request cards
- [ ] Add confirmation dialog
- [ ] Add smooth delete animation
- [ ] Test authorization (users can only delete their own)

### 3. Status Filter Pills
- [ ] Add filter pills UI (All, Submitted, Downloading, Completed, Failed)
- [ ] Implement client-side filtering
- [ ] Store active filter in localStorage
- [ ] Test on mobile

### 4. Database Indexes
- [ ] Create migration: INDEX on artist_name
- [ ] Create migration: INDEX on status
- [ ] Create migration: INDEX on created_at
- [ ] Create migration: INDEX on username
- [ ] Test performance improvement

---

## Backlog

See `docs/ALL-PROPOSED-FEATURES.md` for 47 ranked feature ideas.

When user requests a feature, move it here as a task.

---

## Completed (This Version)

- [x] Fuzzy autocomplete for artist search
- [x] Fuzzy autocomplete for album search
- [x] Fix Lidarr API endpoint paths bug
- [x] Add 11 automated tests
- [x] Consolidate documentation (13 docs archived)
