# Housekeeping Plan - Pre-v0.6.11

**Date**: 2025-11-26
**Purpose**: Clean up project before next development stage
**Scope**: File organization, documentation updates, code cleanup

---

## Current State Analysis

### Uncommitted Changes (v0.6.10)
- ✅ AGENT-HANDOFF.md - Updated with log locations
- ✅ TODO.md - Updated with new issues and tasks
- ✅ app/app.py - v0.6.10 changes (delete endpoint, version)
- ✅ app/templates/* - v0.6.10 UX features
- ✅ docs/STAGE-TEST-PLAN.md - Added systemic log review
- ⚠️ docs/CLOUDFLARE-ACCESS-SETUP.md - Modified (check why)
- ⚠️ check_albums.py - Untracked debug script

### Files/Directories to Clean
1. **check_albums.py** - Debug script for Caravan Palace investigation (v0.6.9)
2. **app/__pycache__/** - Python bytecode cache
3. **Old STAGE plans** - STAGE-2-PLAN.md, STAGE-3-*.md should be archived
4. **Cloudflared**: No cleanup needed in jukebox repo (handled elsewhere)

---

## Housekeeping Tasks

### 1. File Organization (15 min)

#### A. Archive Debug Script
```bash
mkdir -p utils/debug-scripts
mv check_albums.py utils/debug-scripts/
echo "# Debug Scripts

Temporary debugging/investigation scripts from various development sessions.

- check_albums.py: Caravan Palace album investigation (v0.6.9)
" > utils/debug-scripts/README.md
git add utils/
```

#### B. Clean Python Cache
```bash
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete
```

#### C. Archive Old STAGE Plans
```bash
# These are superseded by current workflow
mv docs/STAGE-2-PLAN.md docs/archive/
mv docs/STAGE-3-PLAN.md docs/archive/
mv docs/STAGE-3-CONTINUE.md docs/archive/

# Update archive README
cat >> docs/archive/README.md <<'EOF'

## Stage Plans (Superseded)
- STAGE-2-PLAN.md: Original v0.6.0 Stage 2 plan
- STAGE-3-PLAN.md: Original v0.6.0 Stage 3 plan
- STAGE-3-CONTINUE.md: Continuation notes
- Now using: PLAN-v0.6.9.md pattern and STAGE-TEST-PLAN.md
EOF
```

---

### 2. Documentation Updates (30 min)

#### A. Update AGENT-HANDOFF.md
- [x] Update version to v0.6.10
- [x] Add log locations section (already done)
- [ ] Add v0.6.10 session summary
- [ ] Update "Recent Work" section
- [ ] Update version history

#### B. Update TODO.md
- [x] Add v0.6.10 completion section (already done)
- [x] Add new systemic issues (already done)
- [ ] Reorganize by actual priority (see Section 3)
- [ ] Archive completed v0.6.9 items

#### C. Review CLOUDFLARE-ACCESS-SETUP.md
- [ ] Check what changed
- [ ] Verify still accurate
- [ ] Consider archiving if obsolete

---

### 3. TODO Reorganization (20 min)

**Current Problem**: Tasks scattered across 4 tiers, not clear priority

**New Structure**:

```markdown
## Active Development Queue

### 🚨 P0: Critical - Fix Now
- BUG v0.6.10-1: Stale Album ID (request 23, album 2131)
- BUG v0.6.10-3: Monitor root folder fix effectiveness

### 🔥 P1: High Priority - Next Sprint
- User onboarding process (prevents bugs, 3-4hrs)
- BUG v0.6.10-2: Python datetime deprecation (15-30min)
- "Ready to Listen" direct link (30min)

### 📋 P2: Medium Priority - Backlog
- Partial album download visibility
- Real-time download status from qBit
- Add cloudflared to log review
- API health check button

### 🧹 P3: Low Priority - Housekeeping
- Archive cloudflared docs/tools
- Fuzzy search for MusicBrainz (API limitation)

## Monitoring & Investigation
- ISSUE v0.6.10-4: Plex crashes (external)
- Media server buttons testing

## Future/Strategic
- Local MusicBrainz cache
- Debounced search UX
```

---

### 4. Pre-Commit Audit (15 min)

#### Code Quality Checks
```bash
# Python syntax validation
python3 -m py_compile app/app.py
python3 -m py_compile app/error_parser.py

# Check for TODOs/FIXMEs in code
grep -rn "TODO\|FIXME" app/*.py

# Check for hardcoded secrets
grep -rn "api.*key\|password\|secret" app/*.py | grep -v "getenv\|environ"
```

#### Files Changed Summary
```bash
git status --short
git diff --stat
```

---

### 5. Documentation Consistency (10 min)

#### Version Alignment
- [ ] AGENT-HANDOFF.md: v0.6.10
- [ ] TODO.md: v0.6.10
- [ ] app/app.py: v0.6.10 (already updated)
- [ ] All references to "current version"

#### Cross-Reference Check
- [ ] TODO.md → AGENT-HANDOFF.md references accurate
- [ ] STAGE-TEST-PLAN.md → AGENT-HANDOFF.md references accurate
- [ ] No broken internal links

---

### 6. Git Commit Strategy (10 min)

#### Option A: Single Housekeeping Commit
```bash
git add -A
git commit -m "chore(v0.6.10): housekeeping and documentation updates

## Housekeeping
- Archive check_albums.py debug script to utils/debug-scripts/
- Clean Python __pycache__ directories
- Archive old STAGE-2/3 plan docs to docs/archive/

## Documentation
- Update AGENT-HANDOFF.md with v0.6.10 session summary
- Reorganize TODO.md by actual priority (P0-P3)
- Add systemic log review to STAGE-TEST-PLAN.md
- Update all version references to v0.6.10

## Files Changed
- docs/: Reorganized and archived old plans
- utils/: New debug-scripts directory
- TODO.md: Reprioritized and reorganized
- AGENT-HANDOFF.md: v0.6.10 session notes

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
"
```

#### Option B: Separate v0.6.10 and Housekeeping Commits
1. First commit: v0.6.10 code changes
2. Second commit: Housekeeping only

**Recommendation**: Option A (single commit) - these changes are all part of v0.6.10 wrap-up

---

## Execution Order

1. ✅ **File Organization** (15 min)
   - Archive check_albums.py
   - Clean __pycache__
   - Archive old STAGE plans

2. ✅ **TODO Reorganization** (20 min)
   - Restructure by priority
   - Move completed items to history

3. ✅ **Documentation Updates** (30 min)
   - AGENT-HANDOFF v0.6.10 session
   - Version alignment
   - Cross-reference check

4. ✅ **Pre-Commit Audit** (15 min)
   - Syntax validation
   - Code quality checks
   - Review diff

5. ✅ **Commit & Push** (10 min)
   - Stage all changes
   - Create detailed commit message
   - Push to remote

**Total Estimated Time**: 90 minutes (1.5 hours)

---

## Success Criteria

- [ ] No untracked files in root directory
- [ ] All Python cache cleaned
- [ ] Old plans archived with README
- [ ] TODO.md reorganized by priority
- [ ] AGENT-HANDOFF.md has v0.6.10 session summary
- [ ] All docs reference v0.6.10
- [ ] Pre-commit audit passes
- [ ] Git history clean with single housekeeping commit
- [ ] Ready for next development stage

---

## Post-Housekeeping

**Next Steps**:
1. User reviews v0.6.10 in production
2. Monitor BUG v0.6.10-3 (root folder fix)
3. Start P0 tasks (stale album ID cleanup)
4. Plan v0.6.11 or v0.7.0 scope

**Clean Slate**: Repository organized, documented, and ready for next feature development!
