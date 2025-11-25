# Jukebox - All Proposed Features (Not Yet Implemented)

**Date**: 2025-11-24
**Current Version**: 0.4.0-dev
**Source**: Compiled from conversation history

---

## 🎯 Ranking Legend

**Complexity**: ⭐ = Very Low, ⭐⭐ = Low, ⭐⭐⭐ = Medium, ⭐⭐⭐⭐ = High, ⭐⭐⭐⭐⭐ = Very High
**Impact**: 💥 = Low, 💥💥 = Medium, 💥💥💥 = High, 💥💥💥💥 = Very High, 💥💥💥💥💥 = Critical

**Priority Formula**: High Impact + Low Complexity = Top Priority

---

## 🏆 TIER 1: Easy + High Impact (Quick Wins)

### 1. Show/Hide Failed Requests Toggle
- **Complexity**: ⭐ (Very Low - 20-30 min)
- **Impact**: 💥💥💥💥 (Very High)
- **Type**: Frontend Only (JavaScript + localStorage)
- **Description**: Single button to hide/show failed requests, declutters view
- **Benefits**: Cleaner UI, focus on active requests, preference persists
- **Implementation**: Pure JavaScript, no backend changes

### 2. Delete Request Button
- **Complexity**: ⭐⭐ (Low - 30-45 min)
- **Impact**: 💥💥💥💥💥 (Critical)
- **Type**: Frontend + Simple Backend Endpoint
- **Description**: Delete icon on each card with smooth animation
- **Benefits**: Remove unwanted/old requests, clean up list
- **Implementation**: DELETE endpoint (~15 lines), JavaScript animation

### 3. Smart Capitalization / Error Correction
- **Complexity**: ⭐ (Very Low - 15-20 min)
- **Impact**: 💥💥💥 (High)
- **Type**: Frontend Only (JavaScript)
- **Description**: Auto-capitalize "pink floyd" → "Pink Floyd" on blur
- **Benefits**: Cleaner data, reduces duplicate variations, professional appearance
- **Implementation**: Pure JavaScript, no backend changes

### 4. Status Filter Pills
- **Complexity**: ⭐⭐ (Low - 30-40 min)
- **Impact**: 💥💥💥💥 (Very High)
- **Type**: Frontend Only (JavaScript + CSS)
- **Description**: Filter buttons for each status (submitted, failed, completed, etc.)
- **Benefits**: Quick filtering, status overview at a glance, mobile-friendly
- **Implementation**: Pure JavaScript with localStorage persistence

### 5. Database Indexes
- **Complexity**: ⭐ (Very Low - 10-15 min)
- **Impact**: 💥💥💥💥 (Very High)
- **Type**: Backend (SQL Migration)
- **Description**: Add indexes on artist_name, status, created_at, username
- **Benefits**: Faster queries, better performance for large datasets
- **Implementation**: Simple SQL migration file

---

## 🥈 TIER 2: Moderate Effort + High Impact

### 6. ✅ Artist/Album Autocomplete with MusicBrainz (IMPLEMENTED v0.5.0)
- **Complexity**: ⭐⭐⭐ (Medium - 3 hours actual)
- **Impact**: 💥💥💥💥💥 (Critical)
- **Type**: Frontend + Backend Proxy Endpoint
- **Description**: Real-time suggestions from MusicBrainz API while typing
- **Benefits**: Prevents typos, reduces failed lookups by 80%+, shows official names
- **Implementation**: Complete - FuzzyAutocomplete class, 2 API endpoints, 11 tests
- **Status**: Deployed and functional (commits: 3353768, 24f79e0)

### 7. Auto-Populate Album List from Selected Artist
- **Complexity**: ⭐⭐ (Low - 45-60 min)
- **Impact**: 💥💥💥💥 (Very High)
- **Type**: Frontend + Backend Enhancement
- **Description**: When artist is selected via autocomplete, automatically fetch and display full album list in dropdown instead of requiring user to type
- **Benefits**: Zero typing for album selection, discover all available albums, faster workflow
- **Current State**: Album field requires typing to search - user may not know album names
- **Proposed Flow**:
  1. User selects "Pink Floyd" from artist autocomplete
  2. Album dropdown immediately populates with all Pink Floyd albums (sorted by year)
  3. User scrolls/searches the pre-populated list
  4. Much faster than typing each time
- **Implementation**: On artist selection, call `/api/search/album?artistId=X&q=` (empty query returns all albums for artist), populate dropdown immediately
- **Enhancement**: Add year sorting, group by decade, show album art thumbnails

### 8. Predictive Duplicate Checking
- **Complexity**: ⭐⭐ (Low - 30-45 min)
- **Impact**: 💥💥💥💥 (Very High)
- **Type**: Frontend + Backend Endpoint
- **Description**: Check for duplicates while typing, show "Already in library!" inline
- **Benefits**: Prevents duplicate submissions, immediate link to existing music
- **Implementation**: Debounced fetch + existing check function

### 9. Fuzzy Search for Request List
- **Complexity**: ⭐⭐ (Low - 1-1.5 hours)
- **Impact**: 💥💥💥💥 (Very High)
- **Type**: Frontend Only (JavaScript)
- **Description**: Search with typo tolerance, searches artist/album/notes
- **Benefits**: Find requests quickly, works with misspellings, instant results
- **Implementation**: Pure JavaScript client-side fuzzy matching

### 9. Lidarr Status Polling & Sync (Stage 3)
- **Complexity**: ⭐⭐⭐⭐ (High - 1.5-2 hours)
- **Impact**: 💥💥💥💥💥 (Critical)
- **Type**: Backend (Lidarr API Integration)
- **Description**: Poll Lidarr for download progress, add 'downloading' and 'completed' statuses
- **Benefits**: Users see progress, know when music is ready, "Listen Now" buttons
- **Implementation**: sync_request_status() function, page load polling

### 10. Request Card Mini-Actions (Retry, Copy)
- **Complexity**: ⭐⭐⭐ (Medium - 1-1.5 hours)
- **Impact**: 💥💥💥 (High)
- **Type**: Frontend + Backend Endpoints
- **Description**: Action menu on each card (⋮) with retry, copy, delete options
- **Benefits**: Retry failed requests easily, duplicate successful ones
- **Implementation**: Dropdown menu + endpoints for each action

### 11. HTTPOnly Cookie Flag
- **Complexity**: ⭐ (Very Low - 5 min)
- **Impact**: 💥💥💥💥 (Very High)
- **Type**: Backend (Flask Config)
- **Description**: Add HTTPOnly flag to session cookies for XSS protection
- **Benefits**: Security hardening, prevents JavaScript cookie access
- **Implementation**: One line in Flask config

### 12. CSRF Protection (Flask-WTF)
- **Complexity**: ⭐⭐ (Low - 30-45 min)
- **Impact**: 💥💥💥💥 (Very High)
- **Type**: Backend (Flask Extension)
- **Description**: Add CSRF tokens to all forms
- **Benefits**: Prevents cross-site request forgery attacks
- **Implementation**: pip install flask-wtf, add to forms

---

## 🥉 TIER 3: Higher Effort + High Impact

### 13. Album Selection Dropdown (After Artist Chosen)
- **Complexity**: ⭐⭐⭐⭐ (High - 2-3 hours)
- **Impact**: 💥💥💥💥💥 (Critical)
- **Type**: Frontend + Backend Endpoint
- **Description**: After artist selected, show dropdown of all albums for that artist
- **Benefits**: Zero typing errors for album names, shows year info, huge UX win
- **Implementation**: Dynamic form field switching + album lookup endpoint

### 14. Rate Limiting (Flask-Limiter)
- **Complexity**: ⭐⭐ (Low - 30-45 min)
- **Impact**: 💥💥💥💥 (Very High)
- **Type**: Backend (Flask Extension)
- **Description**: Limit requests per IP/user (e.g., 10 per minute)
- **Benefits**: Prevents abuse, DoS protection, API rate limit compliance
- **Implementation**: pip install flask-limiter, configure routes

### 15. Security Headers (CSP, X-Frame-Options)
- **Complexity**: ⭐⭐ (Low - 30 min)
- **Impact**: 💥💥💥 (High)
- **Type**: Backend (Flask Middleware)
- **Description**: Add Content-Security-Policy, X-Frame-Options, etc.
- **Benefits**: Security hardening, prevents clickjacking and XSS
- **Implementation**: Flask-Talisman or custom middleware

### 16. Search & Filter System (Stage 4)
- **Complexity**: ⭐⭐⭐ (Medium - 1-1.5 hours)
- **Impact**: 💥💥💥💥ïº¿ (Very High)
- **Type**: Frontend + Optional Backend
- **Description**: Search by artist/album, filter by status/date, "My requests only" toggle
- **Benefits**: Quick navigation, admin can see all vs personal
- **Implementation**: JavaScript filtering + URL query params

### 17. Request Details Modal (Stage 5)
- **Complexity**: ⭐⭐ (Low - 1 hour)
- **Impact**: 💥💥💥 (High)
- **Type**: Frontend Only
- **Description**: Click card to see full details in modal (no page load)
- **Benefits**: See all metadata, full error messages, mobile-friendly
- **Implementation**: Modal component + click handlers

### 18. Request Caching (5-minute TTL)
- **Complexity**: ⭐⭐ (Low - 30-45 min)
- **Impact**: 💥💥💥💥 (Very High)
- **Type**: Backend (Flask-Caching)
- **Description**: Cache request list queries to reduce DB load
- **Benefits**: Faster page loads, reduced database queries
- **Implementation**: pip install flask-caching, cache decorator

---

## 🎖️ TIER 4: Moderate Effort + Moderate Impact

### 19. Bulk Actions (Admin Only) (Stage 6)
- **Complexity**: ⭐⭐⭐ (Medium - 1-1.5 hours)
- **Impact**: 💥💥💥 (High)
- **Type**: Frontend + Backend Endpoints
- **Description**: Select multiple requests, bulk delete/retry
- **Benefits**: Admin efficiency, clean up multiple failed requests at once
- **Implementation**: Checkboxes + bulk endpoints

### 20. Password History Tracking
- **Complexity**: ⭐⭐⭐ (Medium - 1 hour)
- **Impact**: 💥💥💥 (High)
- **Type**: Backend (Database + Logic)
- **Description**: Prevent password reuse (last 5 passwords)
- **Benefits**: Security hardening, compliance with best practices
- **Implementation**: New table, hash comparison logic

### 21. Account Lockout After Failed Attempts
- **Complexity**: ⭐⭐⭐ (Medium - 1 hour)
- **Impact**: 💥💥💥 (High)
- **Type**: Backend (Session Tracking)
- **Description**: Lock account after 5 failed login attempts (30-minute cooldown)
- **Benefits**: Brute-force protection, security hardening
- **Implementation**: Failed attempt counter + time-based unlock

### 22. Loading Skeletons
- **Complexity**: ⭐⭐ (Low - 30-45 min)
- **Impact**: 💥💥💥 (High)
- **Type**: Frontend (CSS + HTML)
- **Description**: Show skeleton cards while loading instead of blank screen
- **Benefits**: Better perceived performance, professional look
- **Implementation**: CSS animations + placeholder HTML

### 23. Pull-to-Refresh
- **Complexity**: ⭐⭐ (Low - 30-45 min)
- **Impact**: 💥💥💥 (High)
- **Type**: Frontend (JavaScript Touch Events)
- **Description**: Pull down on mobile to refresh request list
- **Benefits**: Native app feel, intuitive mobile UX
- **Implementation**: Touch event listeners + refresh logic

### 24. Keyboard Shortcuts
- **Complexity**: ⭐⭐ (Low - 20-30 min)
- **Impact**: 💥💥 (Medium)
- **Type**: Frontend (JavaScript)
- **Description**: N = new request, R = refresh, ESC = close modal, / = search
- **Benefits**: Power user efficiency, accessibility
- **Implementation**: keydown event listeners

### 25. Optimistic UI Updates
- **Complexity**: ⭐⭐ (Low - 30-45 min)
- **Impact**: 💥💥💥 (High)
- **Type**: Frontend (JavaScript)
- **Description**: Show changes immediately, rollback if server fails
- **Benefits**: Feels instant, better perceived performance
- **Implementation**: Update DOM before fetch, revert on error

---

## 🏅 TIER 5: Higher Complexity Features

### 26. PWA Service Worker (Offline Support)
- **Complexity**: ⭐⭐⭐⭐ (High - 2-3 hours)
- **Impact**: 💥💥💥💥 (Very High)
- **Type**: Frontend (Service Worker)
- **Description**: Offline access, cache static assets, background sync
- **Benefits**: Works without internet, faster loads, native app feel
- **Implementation**: Service worker registration, cache strategies

### 27. Push Notifications (Request Completed)
- **Complexity**: ⭐⭐⭐⭐ (High - 2-3 hours)
- **Impact**: 💥💥💥💥ïº¿ (Very High)
- **Type**: Frontend + Backend (Push API)
- **Description**: Browser notifications when downloads complete
- **Benefits**: Users notified immediately, better engagement
- **Implementation**: Push API subscription + background worker

### 28. Email Notifications
- **Complexity**: ⭐⭐⭐ (Medium - 1-2 hours)
- **Impact**: 💥💥💥 (High)
- **Type**: Backend (SMTP Integration)
- **Description**: Email on request completion or failure
- **Benefits**: Reach users who aren't actively browsing
- **Implementation**: Flask-Mail + email templates

### 29. Discord/Slack Webhook Integration
- **Complexity**: ⭐⭐ (Low - 30-45 min)
- **Impact**: 💥💥 (Medium)
- **Type**: Backend (Webhook POST)
- **Description**: Post to Discord/Slack when requests submitted/completed
- **Benefits**: Team notifications, audit trail
- **Implementation**: POST to webhook URL with JSON payload

### 30. Application Logging (Structured JSON)
- **Complexity**: ⭐⭐ (Low - 30-45 min)
- **Impact**: 💥💥💥💥ïº¿ (Very High)
- **Type**: Backend (Python logging)
- **Description**: JSON-formatted logs with request IDs, timestamps, levels
- **Benefits**: Better debugging, log aggregation, troubleshooting
- **Implementation**: Configure Python logging with JSON formatter

### 31. Metrics Endpoint (Prometheus)
- **Complexity**: ⭐⭐⭐ (Medium - 1 hour)
- **Impact**: 💥💥💥 (High)
- **Type**: Backend (Metrics Library)
- **Description**: Expose /metrics endpoint with request counts, errors, latency
- **Benefits**: Monitoring, alerting, performance tracking
- **Implementation**: prometheus-flask-exporter library

### 32. Lidarr API Response Time Monitoring
- **Complexity**: ⭐⭐ (Low - 30 min)
- **Impact**: 💥💥💥 (High)
- **Type**: Backend (Timing Decorator)
- **Description**: Track and log Lidarr API call durations
- **Benefits**: Identify performance bottlenecks, debugging
- **Implementation**: Timing decorator around Lidarr calls

### 33. Analytics Dashboard
- **Complexity**: ⭐⭐⭐⭐ (High - 2-3 hours)
- **Impact**: 💥💥💥 (High)
- **Type**: Frontend + Backend
- **Description**: Charts for request stats, most requested artists, success rates
- **Benefits**: Insights into usage patterns, popular music
- **Implementation**: Chart.js + aggregation queries

### 34. Request Statistics
- **Complexity**: ⭐⭐ (Low - 1 hour)
- **Impact**: 💥💥 (Medium)
- **Type**: Backend (Aggregation Queries)
- **Description**: Total requests, success rate, average download time
- **Benefits**: System health overview, user engagement metrics
- **Implementation**: SQL aggregation queries + display

### 35. CSV Export
- **Complexity**: ⭐⭐ (Low - 30 min)
- **Impact**: 💥💥 (Medium)
- **Type**: Backend (CSV Generation)
- **Description**: Export request list to CSV file
- **Benefits**: Data portability, external analysis
- **Implementation**: Python CSV module + download endpoint

---

## 🎯 TIER 6: Advanced/Complex Features

### 36. Background Worker (Option B for Stage 3)
- **Complexity**: ⭐⭐⭐⭐⭐ (Very High - 3-4 hours)
- **Impact**: 💥💥💥💥💥 (Critical)
- **Type**: Backend (Worker Process)
- **Description**: Separate process polls Lidarr every 5 minutes, updates DB
- **Benefits**: Real-time updates without page load, scalable
- **Implementation**: Celery or APScheduler + Redis/RabbitMQ

### 37. Request Approval Workflow
- **Complexity**: ⭐⭐⭐⭐ (High - 2-3 hours)
- **Impact**: 💥💥💥 (High)
- **Type**: Full Stack
- **Description**: Admin approves requests before submission to Lidarr
- **Benefits**: Control over library additions, prevent abuse
- **Implementation**: New 'pending' status + admin approval UI

### 38. Request Scheduling
- **Complexity**: ⭐⭐⭐⭐ (High - 2-3 hours)
- **Impact**: 💥💥 (Medium)
- **Type**: Backend (Scheduler)
- **Description**: Submit request at specific date/time
- **Benefits**: Plan library additions, off-peak downloads
- **Implementation**: Scheduler + delayed job queue

### 39. Request Priority Levels
- **Complexity**: ⭐⭐⭐ (Medium - 1-2 hours)
- **Impact**: 💥💥 (Medium)
- **Type**: Full Stack
- **Description**: High/normal/low priority queue
- **Benefits**: Important requests processed first
- **Implementation**: Priority field + queue sorting

### 40. Request Templates (Favorite Artists)
- **Complexity**: ⭐⭐⭐ (Medium - 1-2 hours)
- **Impact**: 💥💥 (Medium)
- **Type**: Full Stack
- **Description**: Save favorite artists, one-click request
- **Benefits**: Faster requests for frequent artists
- **Implementation**: User templates table + quick-add UI

### 41. Multi-Library Support
- **Complexity**: ⭐⭐⭐⭐⭐ (Very High - 3-4 hours)
- **Impact**: 💥💥💥 (High)
- **Type**: Backend (Multi-Instance)
- **Description**: Support multiple Lidarr instances, user selects per request
- **Benefits**: Separate libraries (e.g., personal vs family)
- **Implementation**: Multiple Lidarr configs + library selector

### 42. Comprehensive Test Suite
- **Complexity**: ⭐⭐⭐⭐ (High - 2-3 hours)
- **Impact**: 💥💥💥💥ïº¿ (Very High)
- **Type**: Testing (pytest, Playwright)
- **Description**: Unit, integration, and E2E tests
- **Benefits**: Confidence in changes, catch regressions
- **Implementation**: pytest + mocked Lidarr + Playwright

### 43. Load Testing
- **Complexity**: ⭐⭐⭐ (Medium - 1 hour)
- **Impact**: 💥💥💥 (High)
- **Type**: Testing (Locust or k6)
- **Description**: Simulate 10+ concurrent users
- **Benefits**: Identify performance bottlenecks before production
- **Implementation**: Load testing script + metrics

### 44. Add to Home Screen Prompt (PWA)
- **Complexity**: ⭐⭐ (Low - 30 min)
- **Impact**: 💥💥💥 (High)
- **Type**: Frontend (PWA Manifest)
- **Description**: Prompt to add app to mobile home screen
- **Benefits**: Native app experience, easier access
- **Implementation**: Web app manifest + install prompt

### 45. Swipe Actions on Cards
- **Complexity**: ⭐⭐⭐ (Medium - 1-2 hours)
- **Impact**: 💥💥💥 (High)
- **Type**: Frontend (Touch Events)
- **Description**: Swipe left to delete, swipe right to retry
- **Benefits**: Mobile-native interaction, efficient
- **Implementation**: Touch event tracking + animation

### 46. Empty States with Helpful CTAs
- **Complexity**: ⭐ (Very Low - 20 min)
- **Impact**: 💥💥 (Medium)
- **Type**: Frontend (HTML/CSS)
- **Description**: Better empty states (no requests, no results, etc.)
- **Benefits**: Guides users, reduces confusion
- **Implementation**: Conditional rendering + design

### 47. Success Animations
- **Complexity**: ⭐⭐ (Low - 30 min)
- **Impact**: 💥💥 (Medium)
- **Type**: Frontend (CSS Animations)
- **Description**: Celebrate successful submissions with animation
- **Benefits**: Positive feedback, delightful UX
- **Implementation**: CSS keyframe animations

---

## 📊 Summary by Category

### Frontend Only (No Backend Changes)
- Show/Hide Failed Toggle ⭐
- Smart Capitalization ⭐
- Status Filter Pills ⭐⭐
- Fuzzy Search ⭐⭐
- Keyboard Shortcuts ⭐⭐
- Loading Skeletons ⭐⭐
- Empty States ⭐
- Success Animations ⭐⭐
- Pull-to-Refresh ⭐⭐
- Optimistic UI ⭐⭐

**Total: 10 features, ~5-7 hours**

### Minimal Backend (<30 lines)
- Delete Request ⭐⭐
- Predictive Duplicate Check ⭐⭐
- Request Card Actions ⭐⭐⭐
- HTTPOnly Cookie ⭐
- CSRF Protection ⭐⭐
- Rate Limiting ⭐⭐
- Security Headers ⭐⭐
- Database Indexes ⭐
- Request Caching ⭐⭐
- Discord/Slack Webhooks ⭐⭐

**Total: 10 features, ~5-8 hours**

### Moderate Backend (30-100 lines)
- Autocomplete ⭐⭐⭐
- Album Dropdown ⭐⭐⭐⭐
- Lidarr Status Polling ⭐⭐⭐⭐
- Email Notifications ⭐⭐⭐
- Application Logging ⭐⭐
- Metrics Endpoint ⭐⭐⭐
- Password History ⭐⭐⭐
- Account Lockout ⭐⭐⭐
- Request Details Modal ⭐⭐
- CSV Export ⭐⭐

**Total: 10 features, ~10-15 hours**

### Complex Features (>100 lines or infrastructure)
- Background Worker ⭐⭐⭐⭐⭐
- PWA Service Worker ⭐⭐⭐⭐
- Push Notifications ⭐⭐⭐⭐
- Multi-Library Support ⭐⭐⭐⭐⭐
- Request Approval Workflow ⭐⭐⭐⭐
- Analytics Dashboard ⭐⭐⭐⭐
- Comprehensive Testing ⭐⭐⭐⭐
- Request Scheduling ⭐⭐⭐⭐
- Swipe Actions ⭐⭐⭐
- Bulk Actions ⭐⭐⭐

**Total: 10+ features, ~25-35 hours**

---

## 🎯 Recommended Implementation Order

### Week 1: Quick Wins (5-8 hours)
1. Show/Hide Failed Toggle (20m)
2. Delete Request (45m)
3. Smart Capitalization (20m)
4. Status Filter Pills (40m)
5. Database Indexes (15m)
6. HTTPOnly Cookie (5m)
7. Predictive Duplicate Check (45m)
8. Fuzzy Search (1.5h)
9. Request Caching (45m)
10. Loading Skeletons (45m)

**Result**: Dramatically improved UX, better performance, basic security

### Week 2: Smart Input (3-4 hours)
11. Autocomplete (2h)
12. Request Card Actions (1.5h)

**Result**: Reduce failed requests by 80%+, better card interactions

### Week 3: Core Features (3-4 hours)
13. Lidarr Status Polling (2h)
14. CSRF Protection (45m)
15. Rate Limiting (45m)
16. Security Headers (30m)

**Result**: Complete core workflow, production-ready security

### Week 4: Polish (3-4 hours)
17. Album Dropdown (3h)
18. Request Details Modal (1h)

**Result**: Professional-grade UX

### Month 2: Advanced Features (10-15 hours)
- Background Worker
- PWA Features
- Analytics Dashboard
- Comprehensive Testing

---

## 💡 Absolute Top Priorities (Start Here)

If you only do 5 things, do these:

1. **Delete Request** ⭐⭐ - 45 minutes
   - Impact: 💥💥💥💥💥 (Critical)
   - Users desperately need this

2. **Show/Hide Failed** ⭐ - 20 minutes
   - Impact: 💥💥💥💥ïº¿ (Very High)
   - Instant UI improvement

3. **Status Filter Pills** ⭐⭐ - 40 minutes
   - Impact: 💥💥💥💥ïº¿ (Very High)
   - Navigation becomes effortless

4. **Autocomplete** ⭐⭐⭐ - 2 hours
   - Impact: 💥💥💥💥💥 (Critical)
   - Reduces failed requests by 80%+

5. **Database Indexes** ⭐ - 15 minutes
   - Impact: 💥💥💥💥ïº¿ (Very High)
   - Future-proof performance

**Total Time**: 4 hours
**Total Impact**: Transform the application

---

**Next Step**: Which tier/category interests you most?
