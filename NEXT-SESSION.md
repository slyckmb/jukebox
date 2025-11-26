# Next Development Session - Jukebox v0.6.11

**Date**: 2025-11-26
**Current Version**: v0.6.10 (deployed and stable)
**Repo**: /home/michael/dev/work/jukebox
**Production**: https://jukebox.bikejeepyoga.com

---

## Quick Start for New Agent

```bash
# Navigate to project
cd /home/michael/dev/work/jukebox

# Read these files FIRST (in order):
1. AGENT-HANDOFF.md        # Current status, how-tos, log locations
2. TODO.md                 # Work queue organized by priority (P0-P3)
3. HOUSEKEEPING-PLAN.md    # Recent cleanup reference

# Check production status
docker compose ps jukebox
docker compose logs --tail=30 jukebox

# Review recent commits
git log --oneline -5
```

---

## Current State Summary

### ✅ What's Working (v0.6.10)
- **Album-specific tracking**: Per-album progress, not artist-wide
- **Defensive monitoring**: Auto re-enables unmonitored albums
- **UX polish**: Better labels, filter pills, delete buttons, monitoring badges
- **Full workflow monitoring**: Log review process for all 7 services documented
- **Clean project**: Housekeeping complete, docs organized, priorities clear

### 🚨 Priority Work Queue

**Start here** → Work from top to bottom:

#### P0: Critical (Do First)
**BUG v0.6.10-1**: Stale Album ID in Database
- Request 23 references album 2131 that doesn't exist in Lidarr
- Causing log noise + incorrect status display
- **Solution options**: Cleanup script OR enhance sync_request_status() error handling
- **Effort**: 2-3 hours
- **Location**: app/app.py:303-464

#### P1: High Priority Quick Wins (Do Next)
1. **BUG v0.6.10-2**: Python datetime.utcnow() deprecation (15-30 min)
   - Replace 7+ locations with datetime.now(datetime.UTC)
   - Locations documented in TODO.md

2. **FEATURE**: "Ready to Listen!" as Direct Album Link (30 min)
   - Make header clickable to open album in Navidrome
   - app/templates/components/request_card.html

3. **FEATURE**: User Onboarding Process (3-4 hours)
   - Auto-create root folders + add to Lidarr when creating users
   - Prevents BUG v0.6.10-3 from recurring
   - Check Lidarr `/api/v1/rootfolder` endpoint

#### P2: Medium Priority (Backlog)
- Partial album download visibility investigation
- Real-time download status from qBit/SABnzbd
- Add cloudflared to log review
- API health check button
- Media server buttons testing

---

## Recommended Approach for Next Session

### Option A: Quick Wins Sprint (1.5-2 hours) ⚡
**Goal**: Build momentum with easy wins

```
1. Fix Python datetime deprecation (30 min)
   - Find/replace datetime.utcnow() → datetime.now(datetime.UTC)
   - Test, commit

2. Add "Ready to Listen!" direct link (30 min)
   - Update request_card.html template
   - Test with completed album, commit

3. Test & document (30 min)
   - Verify both features work
   - Update TODO.md
   - Deploy v0.6.11 (minor version bump for 2 fixes)
```

**Outcome**: v0.6.11 deployed, 2 bugs fixed, momentum established

---

### Option B: Critical Bug Fix (2-3 hours) 🐛
**Goal**: Fix stale album ID issue

```
1. Investigate (30 min)
   - Read app/app.py sync_request_status()
   - Check database for request 23
   - Understand album 2131 reference

2. Implement solution (1-1.5 hours)
   - Option 1: Add 404 detection in sync_request_status()
   - Option 2: Create cleanup script for orphaned requests
   - Option 3: Admin page to view/clean stale requests

3. Test & deploy (30 min)
   - Verify request 23 handled correctly
   - Check logs (should be clean)
   - Deploy v0.6.11
```

**Outcome**: P0 bug fixed, cleaner logs, better error handling

---

### Option C: Prevention Feature (3-4 hours) 🛡️
**Goal**: Implement user onboarding to prevent root folder bugs

```
1. Research Lidarr API (30 min)
   - Test /api/v1/rootfolder endpoint
   - Understand payload format

2. Implement onboarding (2-2.5 hours)
   - When admin creates user → create /data/media/music/lidarr_<username>
   - Add folder to Lidarr via API
   - Verify folder exists and recognized
   - Error handling

3. Test & deploy (1 hour)
   - Create test user
   - Verify folder created + added to Lidarr
   - Test error cases
   - Deploy v0.6.11 or v0.7.0 (feature = minor bump)
```

**Outcome**: Critical bug prevention, reduced admin work, better consistency

---

## My Recommendation

**Start with Option A (Quick Wins Sprint)**

**Why?**
1. **Momentum**: 2 easy fixes in ~1.5 hours
2. **Clean technical debt**: Python deprecation fixed
3. **User value**: Direct link improves UX
4. **Energy for P0**: After quick wins, tackle stale album ID with fresh energy

**Then** → Move to Option B (Critical Bug) in same session if time permits

**Session Plan**:
```
Hour 1: Quick wins (datetime + direct link)
Hour 2: Deploy v0.6.11, then start P0 investigation
Hour 3-4: Finish P0 bug fix, deploy v0.6.12 or v0.7.0
```

---

## Important Context

### Recent Changes (v0.6.10)
- Added 6 UX features (filter pills, delete button, monitoring badge, etc.)
- Conducted systemic log review across all 7 services
- Found 4 new bugs/issues from log analysis
- Reorganized TODO.md by priority
- Comprehensive housekeeping (archived old docs, cleaned cache, etc.)

### Known Issues to Monitor
- **BUG v0.6.10-3**: Root folder path error → User fixed manually, needs confirmation testing
- **ISSUE v0.6.10-4**: Plex crashes (external, not blocking)

### Key Files to Know
- `app/app.py`: Main Flask application (2000+ lines)
- `app/templates/components/request_card.html`: Request card UI
- `db/migrations/`: Database schema changes
- `TODO.md`: Work queue (read this first!)
- `AGENT-HANDOFF.md`: How-tos, log locations, gotchas

---

## Testing Workflow

Always use the STAGE-TEST-PLAN.md process:

```bash
# 1. Build & deploy
docker compose build jukebox && docker compose up -d jukebox

# 2. Health check
sleep 5
curl -s http://localhost:5000/api/health | jq .

# 3. Check logs
docker compose logs --tail=50 jukebox

# 4. (For major builds) Run systemic log review
for service in jukebox lidarr prowlarr qbittorrent_vpn navidrome jellyfin plex; do
  echo "=== $service ==="
  docker logs $service --tail=30 2>&1 | grep -iE "error|warn|fatal|crash|fail" | head -10
  echo
done
```

---

## Git Workflow

```bash
# Check current state
git status
git log --oneline -3

# After changes
git add -A
git commit -m "feat(v0.6.11): <description>

<detailed commit message following established format>

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
"

git push
```

---

## Success Criteria for Next Session

### Minimum (Quick Wins)
- [ ] Python datetime deprecation fixed
- [ ] "Ready to Listen!" direct link implemented
- [ ] v0.6.11 deployed
- [ ] TODO.md updated
- [ ] Git committed & pushed

### Ideal (Quick Wins + P0)
- [ ] All minimum criteria met
- [ ] Stale album ID bug investigated and fixed
- [ ] v0.6.12 or v0.7.0 deployed (depending on scope)
- [ ] Logs clean (no more album 2131 warnings)
- [ ] AGENT-HANDOFF.md updated

### Stretch (All of the above + Prevention)
- [ ] User onboarding process implemented
- [ ] Tested with new user creation
- [ ] Documentation updated
- [ ] v0.7.0 deployed

---

## Questions to Ask User (if needed)

1. **For stale album ID fix**: "Do you want me to soft-delete the bad request, or mark it as 'failed' with a helpful error message?"

2. **For user onboarding**: "Should I run this retroactively for existing users (lidarr_mike, lidarr_admin, lidarr_kim)?"

3. **For version bumping**: "2 bug fixes = v0.6.11. But if I add user onboarding feature, should it be v0.7.0?"

---

## Don't Do

- ❌ Don't create new planning docs (use TODO.md)
- ❌ Don't modify ROADMAP.md unless major scope change
- ❌ Don't add features from ALL-PROPOSED-FEATURES.md without user request
- ❌ Don't skip testing before deploying
- ❌ Don't commit without running pre-commit audit (see HOUSEKEEPING-PLAN.md)

## Do

- ✅ Read TODO.md first (it's organized by priority)
- ✅ Use TodoWrite tool to track multi-step tasks
- ✅ Small commits > big commits
- ✅ Test early and often
- ✅ Update AGENT-HANDOFF.md with session summary when done
- ✅ Run systemic log review for major builds

---

## One-Line Summary

**v0.6.10 is stable with 6 new UX features and full monitoring. Next session: Fix 2 quick bugs (datetime + direct link) then tackle stale album ID cleanup. Start with TODO.md P0-P1 items.**

---

**Good luck! The codebase is clean, well-documented, and ready for your work. 🚀**
