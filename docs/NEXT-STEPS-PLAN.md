# Jukebox - Next Steps Plan

**Date**: 2025-11-24
**Current Version**: 0.4.0-dev
**Status**: Stage 2 Complete ✅

---

## Current State Summary

### Completed (v0.4.0)
- ✅ **Stage 0**: Repository separation (standalone repo at github.com/slyckmb/jukebox)
- ✅ **Stage 1**: Error message cleanup with user-friendly parsing
- ✅ **Stage 2**: Duplicate artist/album detection with media server links
- ✅ **Album Requirement**: One album at a time policy enforced
- ✅ **Documentation**: All project docs updated and synced
- ✅ **Container**: Rebuilt, tested, and verified running

### Repository Status
- **Standalone**: `/home/michael/dev/work/glider/jukebox/jukebox/`
- **Production**: `/home/michael/dev/work/glider/glider-docker/jukebox/`
- **Status**: Both repositories in sync ✅

---

## Proposed Next Steps

### Option 1: Complete v0.4.0 Feature Set (Recommended)

Continue with remaining stages from FEATURE-PLAN-V0.4.0-REVISED.md:

#### Stage 3: Lidarr Status Polling & Sync
**Priority**: High
**Time**: 1.5-2 hours
**Complexity**: High

**Goal**: Provide real-time visibility into request progress

**Features**:
- Poll Lidarr on page load for request status updates
- Add 'downloading' status (artist monitored, albums being downloaded)
- Add 'completed' status (albums downloaded and available)
- Show download progress (e.g., "3 of 12 albums downloaded")
- Display "Listen Now" buttons when completed
- Auto-sync submitted/downloading requests

**Implementation**:
1. Create `sync_request_status(request_id)` function
2. Query Lidarr `/api/v1/artist/{id}` for monitoring status
3. Query Lidarr `/api/v1/album?artistId={id}` for album download status
4. Update database with new status and metadata
5. Add progress indicators to UI (progress bars, track counts)
6. Call sync on page load for active requests (status in ['submitted', 'downloading'])

**Benefits**:
- Users see real progress instead of "submitted" limbo
- Know when music is ready to listen
- Reduced "is it done yet?" questions

**Technical Considerations**:
- Only sync requests in active states to avoid excessive API calls
- Cache sync results for 30-60 seconds to prevent duplicate queries
- Handle Lidarr API rate limits gracefully
- Consider background worker for future enhancement

---

#### Stage 4: Search & Filter System
**Priority**: Medium
**Time**: 1-1.5 hours
**Complexity**: Medium

**Goal**: Help users find specific requests quickly

**Features**:
- Search by artist name or album title
- Filter by status (new, submitted, downloading, completed, failed, existing)
- Filter by date range (last 7 days, last 30 days, all time)
- Admin toggle: "My requests only" vs "All requests"
- Real-time search with debouncing (300ms)
- Clear filters button

**Implementation**:
1. Add search input in page header
2. Add filter pills for each status
3. JavaScript filtering (client-side for speed)
4. Optional: Server-side filtering for large datasets
5. Preserve filter state in URL query params
6. Add "X results found" counter

**Benefits**:
- Quickly find specific requests
- Focus on failed requests that need attention
- Admin can see all vs personal requests

---

#### Stage 5: Request Details Modal
**Priority**: Low
**Time**: 1 hour
**Complexity**: Low

**Goal**: Show full request details without leaving page

**Features**:
- Click card to open modal
- Show all metadata (artist, album, note, timestamps, status)
- Show Lidarr artist/album IDs
- Display full error messages (if truncated)
- Show submission history (who, when)
- ESC key and backdrop click to close
- Mobile-friendly design

**Implementation**:
1. Create modal component in base template
2. Add click handler to request cards
3. Populate modal with request data
4. Style for mobile and desktop
5. Add keyboard navigation (ESC, Tab)

**Benefits**:
- See all details without page navigation
- Better mobile experience (no new page load)
- Access to technical details for troubleshooting

---

#### Stage 6: Bulk Actions (Admin Only)
**Priority**: Low
**Time**: 1-1.5 hours
**Complexity**: Medium

**Goal**: Manage multiple requests efficiently

**Features**:
- Select multiple requests (checkboxes)
- Bulk delete (admin only)
- Bulk retry failed requests (admin only)
- "Select all" / "Select none" buttons
- Confirmation dialogs for destructive actions
- Show count of selected requests

**Implementation**:
1. Add checkbox column to request cards
2. Add bulk action toolbar (appears when items selected)
3. Implement bulk delete endpoint
4. Implement bulk retry endpoint
5. Add JavaScript for select/deselect
6. Add confirmation modals

**Benefits**:
- Quickly clean up old/failed requests
- Retry multiple failed requests at once
- Better admin workflow

---

### Option 2: Production Hardening & Optimization

Focus on making v0.4.0 production-ready:

#### A. Performance Optimization
- [ ] Add database indexes (artist_name, status, created_at)
- [ ] Implement request caching (5-minute TTL)
- [ ] Optimize Lidarr API calls (batch operations)
- [ ] Add CDN for static assets
- [ ] Enable gzip compression

**Time**: 1-2 hours

#### B. Security Enhancements (from SECURITY-AUDIT-REPORT.md)
- [ ] Strengthen admin password (current: admin123)
- [ ] Add HTTPOnly flag to session cookies
- [ ] Implement CSRF protection (Flask-WTF)
- [ ] Add rate limiting (Flask-Limiter)
- [ ] Add security headers (CSP, X-Frame-Options)
- [ ] Password history tracking
- [ ] Account lockout after failed attempts

**Time**: 2-3 hours

#### C. Monitoring & Observability
- [ ] Add application logging (structured JSON logs)
- [ ] Add health check endpoint enhancements
- [ ] Add metrics endpoint (Prometheus format)
- [ ] Track request success/failure rates
- [ ] Monitor Lidarr API response times
- [ ] Add error alerting (email or webhook)

**Time**: 1-2 hours

#### D. Testing & Quality
- [ ] Expand pytest test coverage (currently minimal)
- [ ] Add integration tests with mock Lidarr
- [ ] Add UI tests (Playwright or Selenium)
- [ ] Add load testing (simulate 10+ concurrent users)
- [ ] Add E2E smoke tests

**Time**: 2-3 hours

---

### Option 3: User Experience Enhancements

Focus on polish and usability:

#### A. Mobile PWA Features
- [ ] Add service worker for offline support
- [ ] Add "Add to Home Screen" prompt
- [ ] Enable push notifications (request completed)
- [ ] Add app manifest (icons, theme colors)
- [ ] Implement pull-to-refresh

**Time**: 2-3 hours

#### B. UI/UX Polish
- [ ] Add loading skeletons for async operations
- [ ] Add empty states with helpful CTAs
- [ ] Improve error state designs
- [ ] Add success animations
- [ ] Implement optimistic UI updates
- [ ] Add keyboard shortcuts (N = new request, R = refresh)

**Time**: 1-2 hours

#### C. Enhanced Notifications
- [ ] Email notifications on request completion
- [ ] Discord webhook integration
- [ ] Slack integration
- [ ] Telegram bot support

**Time**: 2-3 hours

---

### Option 4: Advanced Features

Add power-user features:

#### A. Advanced Request Management
- [ ] Request scheduling (add in future, not now)
- [ ] Request priority levels
- [ ] Request notes/comments
- [ ] Request approval workflow (admin approves before submission)
- [ ] Request templates (favorite artists)

**Time**: 3-4 hours

#### B. Analytics & Reporting
- [ ] Request statistics dashboard
- [ ] Most requested artists
- [ ] Success/failure rate charts
- [ ] Average download time
- [ ] User activity metrics
- [ ] Export to CSV

**Time**: 2-3 hours

#### C. Multi-Library Support
- [ ] Support multiple Lidarr instances
- [ ] Library selection per request
- [ ] Per-user default library

**Time**: 2-3 hours

---

## Recommended Path Forward

### Immediate (Next Session)

**Recommendation**: Complete Stage 3 (Lidarr Status Polling & Sync)

**Rationale**:
1. **High User Impact**: Users currently have no visibility into download progress
2. **Completes Core Workflow**: Request → Submit → Monitor → Listen
3. **Moderate Complexity**: Achievable in 1.5-2 hours
4. **Foundation for Features**: Enables "Listen Now" buttons for completed requests
5. **Aligns with Original Plan**: Stage 3 of 6 in v0.4.0

**Implementation Approach**:
- Start with simple polling on page load (Option A)
- Only sync active requests (status: submitted, downloading)
- Cache results to minimize API calls
- Add progress indicators to UI
- Update status badges with new states

**Expected Outcome**:
- Users see "Downloading: 3 of 12 albums" instead of just "Submitted"
- Completed requests show "Listen Now" buttons
- Better user satisfaction and reduced support questions

---

### Short-Term (1-2 weeks)

After completing Stage 3:
1. **Stage 4**: Search & Filter (1-1.5 hours)
2. **Production Hardening**: Database indexes, security headers (1 hour)
3. **Testing**: Expand test coverage for new features (1 hour)

**Total**: ~4 hours to complete v0.4.0 core features

---

### Medium-Term (1 month)

Focus on production readiness:
1. Complete Stages 5-6 (Request details modal, bulk actions)
2. Implement security enhancements (CSRF, rate limiting, stronger auth)
3. Add monitoring and observability
4. Comprehensive testing suite

**Release**: v0.4.0 stable

---

### Long-Term (2-3 months)

Polish and advanced features:
1. PWA features (offline, push notifications)
2. Analytics dashboard
3. Enhanced integrations (Discord, Slack)
4. Multi-library support

**Release**: v0.5.0

---

## Decision Points

### Question 1: Feature Completion vs. Production Hardening?
- **Option A**: Complete Stages 3-6 first (user-facing features)
- **Option B**: Focus on security/performance now (infrastructure)
- **Recommendation**: Complete Stage 3, then mix features + hardening

### Question 2: Simple Polling vs. Background Worker?
- **Option A**: Polling on page load (simple, good enough)
- **Option B**: Background worker (complex, real-time)
- **Recommendation**: Start with Option A, evolve to B if needed

### Question 3: MVP vs. Full Feature Set?
- **Option A**: Ship v0.4.0 after Stage 3 (core workflow complete)
- **Option B**: Complete all 6 stages before release
- **Recommendation**: Complete Stage 3, evaluate user feedback

---

## Success Metrics

### Stage 3 Success Criteria
- [ ] Users can see download progress for active requests
- [ ] Status automatically updates on page load
- [ ] Completed requests show "Listen Now" buttons
- [ ] No performance degradation (page load < 2s)
- [ ] Lidarr API calls limited (< 10 per page load)
- [ ] All tests passing
- [ ] Documentation updated

### v0.4.0 Success Criteria
- [ ] All 6 stages complete OR Stage 3 + user validation
- [ ] No critical bugs
- [ ] Container running stable for 7+ days
- [ ] User satisfaction feedback positive
- [ ] Code coverage > 70%
- [ ] Documentation complete

---

## Next Step Recommendation

**Start Stage 3: Lidarr Status Polling & Sync**

1. Review FEATURE-PLAN-V0.4.0-REVISED.md Stage 3 section
2. Implement `sync_request_status()` function
3. Add 'downloading' and 'completed' statuses
4. Update UI with progress indicators
5. Test with real Lidarr instance
6. Update documentation
7. Commit and deploy

**Estimated Time**: 1.5-2 hours
**Expected Completion**: Same session or next session

---

## Questions for Consideration

1. **Do you want to complete Stage 3 now?**
   - Pros: High user impact, completes core workflow
   - Cons: 1.5-2 hour time commitment

2. **Should we focus on production hardening instead?**
   - Pros: More stable, secure application
   - Cons: Less visible user impact

3. **Do you want to ship v0.4.0 after Stage 3?**
   - Pros: Get user feedback earlier
   - Cons: Missing search/filter features

4. **Any other priorities or concerns?**
   - Technical debt to address?
   - Specific user requests?
   - Infrastructure issues?

---

**End of Next Steps Plan**
**Document**: NEXT-STEPS-PLAN.md
**Repository**: github.com/slyckmb/jukebox
**Author**: Claude Code
