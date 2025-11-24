# Jukebox Security Enhancement Plan

**Version**: 1.0.0
**Created**: 2025-11-23
**Status**: Planning / Implementation

---

## Overview

Comprehensive security improvements for Jukebox v0.2.0 to address authentication, authorization, and infrastructure security concerns.

**Priority**: High
**Estimated Total Time**: 4-6 hours

---

## Security Issues Identified

1. ❌ **Admin credentials exposed on login page** - Security violation
2. ⚠️ **Admin/admin login not working** - No admin user in database
3. ❌ **No password change functionality** - Users can't update passwords
4. ⚠️ **No OAuth protection on jukebox domain** - Single auth layer only
5. ⚠️ **Missing security hardening** - No CSRF, rate limiting, secure headers

---

## Implementation Stages

### **Stage 1: Quick Security Fixes** ✅ Ready to Implement
**Priority**: Critical
**Time**: 30 minutes
**Risk**: Low

#### Tasks:
1. Remove "Default credentials: admin / admin" text from login page
2. Fix admin user creation bug
3. Add warning for default passwords

#### Files to Modify:
- `app/templates/login.html` - Remove lines 44-46
- `app/app.py` - Fix init_db() to ensure admin exists

#### Implementation:
```python
# In app.py init_db()
def init_db():
    # ... existing schema ...

    with closing(get_db()) as conn:
        # Check if admin user exists
        cur = conn.execute("SELECT id FROM users WHERE username = 'admin'")
        admin_exists = cur.fetchone()

        if not admin_exists:
            # Create admin user if missing
            conn.execute(
                "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)",
                ("admin", generate_password_hash("admin"), 1),
            )
            conn.commit()
            app.logger.warning(
                "Jukebox: created default admin user 'admin' with password 'admin'. "
                "CHANGE THIS IMMEDIATELY via password change feature!"
            )
        else:
            # Check if still using default password
            cur = conn.execute("SELECT password_hash FROM users WHERE username = 'admin'")
            row = cur.fetchone()
            if row and check_password_hash(row["password_hash"], "admin"):
                app.logger.error(
                    "SECURITY WARNING: Admin user still has default password 'admin'! "
                    "Change it immediately!"
                )
```

#### Testing:
```bash
# Test 1: Remove admin from DB and restart
sqlite3 data/requests.db "DELETE FROM users WHERE username = 'admin';"
docker compose restart jukebox
# Expected: Admin user recreated, warning logged

# Test 2: Login with admin/admin
curl -c cookies.txt -X POST http://localhost:5000/login \
  -d "username=admin&password=admin"
# Expected: Successful login

# Test 3: Check login page
curl -s http://localhost:5000/login | grep -i "default credentials"
# Expected: No match (text removed)
```

---

### **Stage 2: Password Change Functionality**
**Priority**: High
**Time**: 1-2 hours
**Risk**: Low

#### Design:
- Route: `/change-password` (GET/POST)
- Authentication: Required (login_required decorator)
- Fields: Current password, New password, Confirm password
- Validation:
  - Current password correct
  - New password ≥ 8 characters
  - Passwords match
  - New password != current password

#### Files to Create/Modify:
1. `app/templates/change_password.html` - Mobile-friendly form
2. `app/app.py` - Add route handler
3. `app/templates/requests.html` - Add "Change Password" nav item

#### Implementation:
```python
# In app.py
@app.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    if request.method == "POST":
        current_pw = request.form.get("current_password", "").strip()
        new_pw = request.form.get("new_password", "").strip()
        confirm_pw = request.form.get("confirm_password", "").strip()

        # Validation
        if not current_pw or not new_pw or not confirm_pw:
            flash("All fields are required.", "danger")
            return redirect(url_for("change_password"))

        # Verify current password
        with closing(get_db()) as conn:
            cur = conn.execute("SELECT password_hash FROM users WHERE id = ?", (user["id"],))
            row = cur.fetchone()

        if not row or not check_password_hash(row["password_hash"], current_pw):
            flash("Current password is incorrect.", "danger")
            return redirect(url_for("change_password"))

        # Validate new password
        if len(new_pw) < 8:
            flash("New password must be at least 8 characters.", "danger")
            return redirect(url_for("change_password"))

        if new_pw != confirm_pw:
            flash("New passwords do not match.", "danger")
            return redirect(url_for("change_password"))

        if new_pw == current_pw:
            flash("New password must be different from current password.", "danger")
            return redirect(url_for("change_password"))

        # Update password
        new_hash = generate_password_hash(new_pw)
        with closing(get_db()) as conn:
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (new_hash, user["id"])
            )
            conn.commit()

        app.logger.info(f"Password changed for user: {user['username']}")
        flash("Password changed successfully.", "success")
        return redirect(url_for("list_requests"))

    return render_template("change_password.html")
```

#### Template (change_password.html):
```html
{% extends "base.html" %}

{% block title %}Change Password - Jukebox{% endblock %}

{% block content %}
<div class="change-password-page">
  <header class="page-header">
    <a href="{{ url_for('list_requests') }}" class="back-button" aria-label="Back">
      <span>←</span>
    </a>
    <h1>Change Password</h1>
    <div></div>
  </header>

  <div class="container">
    <form method="POST" class="password-form">
      <div class="form-group">
        <label for="current_password">
          Current Password
          <span class="required">*</span>
        </label>
        <input
          type="password"
          id="current_password"
          name="current_password"
          required
          autofocus
          autocomplete="current-password"
        >
      </div>

      <div class="form-group">
        <label for="new_password">
          New Password
          <span class="required">*</span>
        </label>
        <input
          type="password"
          id="new_password"
          name="new_password"
          required
          autocomplete="new-password"
          minlength="8"
        >
        <p class="form-hint">Minimum 8 characters</p>
      </div>

      <div class="form-group">
        <label for="confirm_password">
          Confirm New Password
          <span class="required">*</span>
        </label>
        <input
          type="password"
          id="confirm_password"
          name="confirm_password"
          required
          autocomplete="new-password"
          minlength="8"
        >
      </div>

      <div class="form-actions">
        <a href="{{ url_for('list_requests') }}" class="btn btn-secondary">
          Cancel
        </a>
        <button type="submit" class="btn btn-primary">
          Change Password
        </button>
      </div>
    </form>
  </div>
</div>
{% endblock %}
```

#### Testing:
```bash
# Test 1: Change password flow
# - Login as admin
# - Navigate to /change-password
# - Try wrong current password → should fail
# - Try passwords that don't match → should fail
# - Try password < 8 chars → should fail
# - Use valid inputs → should succeed

# Test 2: Verify new password works
# - Logout
# - Login with old password → should fail
# - Login with new password → should succeed

# Test 3: Mobile responsiveness
# - Test on 375px viewport
# - Ensure form is touch-friendly
```

---

### **Stage 3: Cloudflare Access Configuration** ✅ Documentation Complete
**Priority**: High
**Time**: 30-45 minutes
**Risk**: Low (external configuration)

#### Implementation Options:

**Option A: Manual Setup (Recommended for immediate use)**
- Follow guide: `jukebox/docs/CLOUDFLARE-ACCESS-SETUP.md`
- Configure via Cloudflare Zero Trust dashboard
- Time: 5-10 minutes
- No code changes required

**Option B: Automated Setup (For repeatable deployments)**
- Create Zero Trust API token (guide in documentation)
- Run: `./cloudflared/bin/setup-jukebox-access.sh`
- Time: 2-3 minutes (after token created)

#### Configuration:
```bash
# Automated setup
cd /home/michael/dev/work/glider/glider-docker/cloudflared/bin

# Test with dry run first
./setup-jukebox-access.sh --dry-run

# Apply configuration
./setup-jukebox-access.sh

# Follow prompts:
# - Select identity provider (Google/GitHub/Email)
# - Configure allowed emails or domains
# - Review and confirm
```

#### Verification:
```bash
# Test 1: OAuth required
# Visit: https://jukebox.bikejeepyoga.com
# Expected: Redirect to Cloudflare Access / OAuth provider

# Test 2: Successful authentication
# Authenticate with allowed email
# Expected: Redirect to Jukebox login page

# Test 3: Access denied
# Authenticate with unauthorized email
# Expected: "Access Denied" page

# Test 4: Session persistence
# Close and reopen browser
# Expected: No OAuth prompt (session valid for 24h)
```

#### Rollback Plan:
```bash
# If issues occur, remove Access application:
# 1. Cloudflare Dashboard → Zero Trust → Access → Applications
# 2. Find "Jukebox" application
# 3. Click Delete
# Result: Traffic flows directly to Jukebox (OAuth bypassed)
```

---

### **Stage 4: Comprehensive Security Review**
**Priority**: Medium
**Time**: 2-3 hours
**Risk**: Medium (requires testing)

#### Areas to Audit and Harden:

##### 4.1 Session Security
**Current State**: Basic Flask sessions
**Required Improvements**:
- Secure cookie flags (httponly, secure, samesite)
- Session timeout (30 minutes idle)
- Session regeneration on login
- Logout invalidates session properly

**Implementation**:
```python
# In app.py configuration
app.config.update(
    SESSION_COOKIE_SECURE=True,       # HTTPS only
    SESSION_COOKIE_HTTPONLY=True,     # No JS access
    SESSION_COOKIE_SAMESITE='Lax',    # CSRF protection
    PERMANENT_SESSION_LIFETIME=1800,  # 30 minutes
)

# Add session timeout middleware
@app.before_request
def check_session_timeout():
    if 'user_id' in session:
        last_activity = session.get('last_activity')
        if last_activity:
            now = datetime.utcnow().timestamp()
            if now - last_activity > 1800:  # 30 minutes
                session.clear()
                flash("Session expired. Please login again.", "info")
                return redirect(url_for('login'))
        session['last_activity'] = datetime.utcnow().timestamp()
```

##### 4.2 CSRF Protection
**Current State**: None
**Required**: CSRF tokens on all forms

**Implementation**:
```python
# Option 1: Flask-WTF (recommended)
# Add to requirements.txt: Flask-WTF==1.2.1

from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)

# In templates:
# <form method="POST">
#   {{ csrf_token() }}
#   ...
# </form>

# Option 2: Manual CSRF tokens
import secrets

def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(16)
    return session['_csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token

@app.before_request
def csrf_protect():
    if request.method == "POST":
        token = session.get('_csrf_token')
        if not token or token != request.form.get('_csrf_token'):
            abort(403)
```

##### 4.3 Rate Limiting
**Current State**: None (brute force vulnerable)
**Required**: Rate limits on login and API endpoints

**Implementation**:
```python
# Add to requirements.txt: Flask-Limiter==3.5.0

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Apply to login route
@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():
    # ... existing code ...
```

##### 4.4 Security Headers
**Current State**: Minimal
**Required**: CSP, X-Frame-Options, HSTS, etc.

**Implementation**:
```python
# Add to requirements.txt: Flask-Talisman==1.1.0

from flask_talisman import Talisman

Talisman(app,
    force_https=True,
    strict_transport_security=True,
    content_security_policy={
        'default-src': "'self'",
        'style-src': ["'self'", "'unsafe-inline'"],  # For inline styles
        'script-src': ["'self'"],
    },
    content_security_policy_nonce_in=['script-src']
)
```

##### 4.5 Input Validation
**Current State**: Basic validation
**Required**: Comprehensive input sanitization

**Checklist**:
- ✅ SQL injection: Using parameterized queries
- ⚠️ XSS: Audit Jinja2 auto-escaping (verify with tests)
- ⚠️ Artist/album names: Add length limits and character validation
- ✅ Note field: 500 char limit exists
- ⚠️ Username: Add validation (alphanumeric + underscore only)

**Implementation**:
```python
import re

def validate_username(username):
    """Validate username: 3-20 chars, alphanumeric + underscore"""
    if not username or len(username) < 3 or len(username) > 20:
        return False
    return bool(re.match(r'^[a-zA-Z0-9_]+$', username))

def validate_artist_name(name):
    """Validate artist name: 1-200 chars, printable characters"""
    if not name or len(name) > 200:
        return False
    return bool(re.match(r'^[\w\s\-\.\,\'\"&()]+$', name))
```

##### 4.6 Docker Security
**Current State**: Good baseline
**Optional Improvements**:

```dockerfile
# In Dockerfile
# Run as non-root user
RUN adduser --disabled-password --gecos '' jukebox
USER jukebox

# Read-only root filesystem (where possible)
# In docker-compose.yml:
# read_only: true
# tmpfs:
#   - /tmp
#   - /app/data  # Unless using volume
```

---

## Implementation Priority Order

1. **Stage 1** (30 min) - Remove admin note, fix admin user
2. **Stage 3** (30 min) - Cloudflare OAuth setup (manual)
3. **Stage 2** (1-2 hours) - Password change functionality
4. **Stage 4** (2-3 hours) - Security hardening

**Total Time**: 4-6 hours

---

## Testing Plan

### Stage 1 Testing
- [ ] Login page has no credential hints
- [ ] Admin user exists in database
- [ ] Admin/admin login works
- [ ] Warning logged for default password

### Stage 2 Testing
- [ ] Change password page renders
- [ ] Form validation works (all error cases)
- [ ] Password successfully changes
- [ ] Old password stops working
- [ ] New password works for login
- [ ] Mobile responsive

### Stage 3 Testing
- [ ] OAuth prompt appears when visiting jukebox
- [ ] Authorized emails can access
- [ ] Unauthorized emails see "Access Denied"
- [ ] Session persists (24h)
- [ ] Jukebox login still required after OAuth

### Stage 4 Testing
- [ ] Session timeout works (30 min idle)
- [ ] CSRF protection blocks invalid tokens
- [ ] Rate limiting blocks brute force
- [ ] Security headers present (check with curl)
- [ ] No XSS vulnerabilities (manual testing)
- [ ] Input validation rejects invalid data

---

## Security Checklist (Post-Implementation)

### Authentication & Authorization
- [x] Password hashing (werkzeug.security)
- [x] Session management (Flask sessions)
- [ ] Session timeout implemented
- [ ] CSRF protection enabled
- [x] Admin-only routes protected
- [ ] OAuth layer (Cloudflare Access)
- [ ] Password change functionality

### Network Security
- [x] HTTPS enforced (via Cloudflare)
- [ ] Security headers (CSP, HSTS, X-Frame-Options)
- [ ] Rate limiting enabled
- [x] Secrets in files (not env vars)

### Input Validation
- [x] SQL injection protected (parameterized queries)
- [ ] XSS protection verified
- [ ] Input length limits enforced
- [ ] Character validation for usernames

### Monitoring & Logging
- [x] Login attempts logged
- [ ] Failed authentication logged
- [ ] Password changes logged
- [ ] Admin actions logged
- [ ] Access logs reviewed regularly

---

## Rollback Procedures

### Stage 1 Rollback
```bash
# Restore login.html from git
git checkout HEAD~1 -- app/templates/login.html
docker compose restart jukebox
```

### Stage 2 Rollback
```bash
# Remove password change route and template
git revert <commit-hash>
docker compose restart jukebox
```

### Stage 3 Rollback
```bash
# Delete Access application via dashboard or:
# Cloudflare Dashboard → Zero Trust → Access → Applications → Delete "Jukebox"
```

### Stage 4 Rollback
```bash
# Revert security hardening changes
git revert <commit-hash>
# Update requirements.txt
docker compose build jukebox
docker compose up -d jukebox
```

---

## Documentation Updates Required

After implementation:
- [ ] Update HANDOFF-JUKEBOX.md with security features
- [ ] Update request-portal-requirements.md with security requirements
- [ ] Create SECURITY.md with security policy
- [ ] Document password requirements
- [ ] Document OAuth setup in deployment guide

---

## Success Criteria

- ✅ No credentials exposed in UI
- ✅ Admin user can be created and login works
- ✅ Users can change their passwords
- ✅ OAuth protection active on production
- ✅ CSRF protection on all forms
- ✅ Rate limiting prevents brute force
- ✅ Security headers present
- ✅ All tests pass
- ✅ No regressions in functionality

---

**Next Steps**: Begin with Stage 1 implementation - ready to proceed?
