# Stage Test Plan - Jukebox

**Purpose**: Standardized test workflow for each development stage to ensure quality and enable frequent commits within the 5-hour context window.

---

## Stage Workflow

### 1. Pre-Deploy Checklist
- [ ] Syntax validation complete (Python, JavaScript, SQL)
- [ ] All modified files listed
- [ ] Breaking changes identified (if any)

### 2. Deploy Stage
```bash
cd /home/michael/dev/work/jukebox
docker compose build jukebox && docker compose up -d jukebox
```

### 3. Health Check
```bash
# Wait 5 seconds for startup
sleep 5

# Check container status
docker compose ps jukebox

# Check health endpoint
curl -s http://localhost:5000/api/health | jq .

# Review startup logs
docker compose logs --tail=100 jukebox
```

**Expected**: Container running, health returns `{"status":"ok","app":"Jukebox"}`, no errors in logs

### 4. Systemic Log Review (Required for Major Builds)

**When to Run**: After major feature releases (v0.X.0), before production deployment, when investigating workflow issues

**Purpose**: Detect systemic issues across the complete Jukebox → Lidarr → Download → Media Server workflow

#### Quick Scan All Services for Errors/Warnings
```bash
for service in jukebox lidarr prowlarr qbittorrent_vpn navidrome jellyfin plex; do
  echo "=== $service ==="
  docker logs $service --tail=30 2>&1 | grep -iE "error|warn|fatal|crash|fail" | head -10
  echo
done
```

#### Red Flags to Investigate:
- [ ] **Jukebox**: Repeated "Could not fetch album" warnings → Stale album IDs in database (BUG: needs cleanup)
- [ ] **Jukebox**: Python deprecation warnings → Update datetime calls to timezone-aware
- [ ] **Lidarr**: "Album with ID X does not exist" errors → Database integrity issue (cross-reference with Jukebox)
- [ ] **Lidarr**: "Not scanning ... not a subdirectory of root folder" → Path configuration mismatch
- [ ] **Plex**: Crash dumps → Service instability (external issue, document for user)
- [ ] **Download Client**: No activity during expected downloads → Indexer or Prowlarr connectivity issues

#### Full Service Log Commands (when needed):
```bash
# Jukebox - Check request processing
docker compose logs --tail=100 jukebox | grep -E "WARNING|ERROR|Album|STAGING|UNMONITOR"

# Lidarr - Check artist/album operations
docker logs lidarr --tail=100 2>&1 | grep -E "Error|Warn|AddArtist|RefreshAlbum|AlbumSearch|DiskScan"

# Prowlarr - Check indexer health
docker logs prowlarr --tail=50 2>&1 | grep -E "Info.*Searching|disabled|failed"

# Navidrome - Check streaming success
docker logs navidrome --tail=30 2>&1 | grep -E "Streaming|Scrobbled|error"

# Jellyfin - Check library updates
docker logs jellyfin --tail=30 2>&1 | grep -E "LibraryMonitor|refresh|error"

# Plex - Check for crashes
docker logs plex --tail=50 2>&1 | grep -iE "crash|error|fatal" | head -20
```

#### Document Issues Found:
- [ ] Add systemic issues to TODO.md with priority and investigation plan
- [ ] Cross-reference errors between services (e.g., Jukebox album ID vs Lidarr album existence)
- [ ] Note any external service issues (Plex crashes, indexer downtime) for user awareness

**Reference**: See AGENT-HANDOFF.md "Service Log Locations & Monitoring" section for detailed log analysis guide

---

### 5. New Feature Tests

Test each new feature/fix implemented in this stage:

**Stage v0.6.0-stage1 (Current)**:
- [ ] Message removal: Artist exists → no "Check Plex..." text appears
- [ ] Unmonitored album: Request album from existing artist → album flips to monitored
- [ ] Search flicker: Type "Frank Sinatra" slowly → results stay visible
- [ ] Album search: Search for obscure album → fallback search triggers

### 6. Regression Tests

Core functionality that must continue working:

#### Authentication
- [ ] Login with valid credentials → success
- [ ] Login with invalid credentials → error message

#### Artist Request Flow
- [ ] Search for new artist (not in library)
- [ ] Select from autocomplete dropdown
- [ ] Select album from dropdown
- [ ] Submit request → status shows "submitted"

#### Request List
- [ ] View all requests → list displays
- [ ] Request cards show correct status badges
- [ ] Pagination works (if >10 requests)

#### Status Sync
- [ ] Refresh page → active requests sync with Lidarr
- [ ] Downloading request shows progress
- [ ] Completed request shows "completed" status

### 7. Bug Fixes

If issues found:
- [ ] Document bug in comments/notes
- [ ] Fix bug
- [ ] Re-run relevant tests (goto step 2)
- [ ] Mark fixed bugs in TODO.md

### 8. Validation

- [ ] No JavaScript console errors (check browser DevTools)
- [ ] No Python exceptions in logs
- [ ] Mobile UX tested (or defer to production)
- [ ] All stage tests passing

### 9. Documentation Updates

Update these files to reflect stage completion:

#### TODO.md
- [ ] Mark completed tasks with [x]
- [ ] Move to "Completed (This Version)" section
- [ ] Update task counts

#### ROADMAP.md
- [ ] Update completion percentages
- [ ] Note any scope changes
- [ ] Update ETA if needed

#### AGENT-HANDOFF.md
- [ ] Update "Recent Work" section
- [ ] Add any new gotchas/issues discovered
- [ ] Update project status if changed

### 10. Commit & Push

```bash
# Stage changes
git add -A

# Verify what's staged
git status

# Create commit with detailed message
git commit -m "$(cat <<'EOF'
feat(v0.6.0): stage 1 - quick wins and search bug fixes

## Changes
- Remove "Check Plex, Jellyfin..." message from artist exists notification
- Add album monitoring flip for existing artists (unmonitored → monitored)
- Fix search flicker race condition (Frank Sinatra bug)
- Add fallback album search for better coverage (Taylor Swift bug)

## New Functions
- find_album_in_artist(): Fuzzy match album in artist's library
- set_album_monitored(): Update Lidarr album monitoring status

## Modified Files
- app/app.py: Backend logic (lines 457-843)
- app/templates/new_request.html: Autocomplete JS (lines 349-458)

## Testing
- Manual testing: All 4 features verified
- Regression: Core flows working
- Logs: Clean, no errors

## Documentation
- TODO.md: Tasks 1-4 marked complete
- ROADMAP.md: Updated progress
- AGENT-HANDOFF.md: Added stage 1 notes

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

# Push to remote
git push
```

### 11. Stage Complete

- [ ] Git commit created and pushed
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Ready for next stage or handoff

---

## Stage Sizing Guidelines

**Target**: Complete stage within 3-4 hours to allow 1-2 hours buffer before context window expires.

**Small Stage** (1-2 hours):
- 1-3 quick wins or simple bug fixes
- Minimal new functions (<100 lines total)
- Clear test scenarios

**Medium Stage** (2-3 hours):
- 1-2 features requiring new components
- 100-300 lines of new code
- Multiple test scenarios

**Large Stage** (3-4 hours):
- 1 complex feature or major refactor
- 300+ lines of new code
- Extensive testing needed

**If approaching 4 hours**: Stop, commit current work, document next steps in HANDOFF.md

---

## Quick Reference Commands

```bash
# Full test cycle
cd /home/michael/dev/work/jukebox
docker compose build jukebox && docker compose up -d jukebox && sleep 5 && docker compose logs --tail=50 jukebox

# Check health
curl -s http://localhost:5000/api/health | jq .

# Watch logs live
docker compose logs -f jukebox

# Restart without rebuild
docker compose restart jukebox

# Full teardown
docker compose down jukebox
```

---

## Notes

- **Keep stages small**: Better to have 5 small commits than 1 giant one
- **Test early**: Deploy after each logical unit of work
- **Document issues**: Add to TODO.md or HANDOFF.md immediately
- **Time management**: If >4 hours, wrap up and commit what works
- **Regression first**: If core functionality breaks, fix before adding features
