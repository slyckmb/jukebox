# Feature: User Email Address and Cloudflare Access Sync

**Version**: 1.0.0
**Created**: 2025-11-23
**Status**: Planned
**Priority**: Medium
**Estimated Effort**: 2-3 hours

---

## Overview

Add email address field to Jukebox users table and implement bidirectional synchronization with Cloudflare Access allowed email list. This creates a single source of truth for user access management.

---

## Problem Statement

**Current State**:
- Jukebox users have username/password but no email field
- Cloudflare Access email allowlist managed separately via CLI/dashboard
- Two disconnected systems for managing the same users
- Risk of desync: user exists in Jukebox but not in CF Access (or vice versa)

**Desired State**:
- Email address stored in Jukebox users table
- Cloudflare Access list automatically synced from database
- Single command to grant user access to both systems
- Admin can manage users entirely through Jukebox UI

---

## Requirements

### Functional Requirements

**FR1**: Users table SHALL have an `email` column
**FR2**: Email SHALL be optional for existing users (backward compatibility)
**FR3**: Email SHALL be required for new users
**FR4**: Email format SHALL be validated (standard email regex)
**FR5**: Email SHALL be unique per user
**FR6**: Email SHALL be displayed in user management UI
**FR7**: Sync script SHALL read emails from database
**FR8**: Sync script SHALL update Cloudflare Access policy
**FR9**: Sync SHALL be idempotent (safe to run multiple times)
**FR10**: Sync SHALL preserve non-email policy rules (MFA, geo, etc.)

### Non-Functional Requirements

**NFR1**: Migration SHALL not break existing users
**NFR2**: Sync operation SHALL complete in < 5 seconds
**NFR3**: Failed sync SHALL not corrupt database
**NFR4**: Email changes SHALL be logged

---

## Database Schema Changes

### Migration

```sql
-- Migration: Add email column to users table
-- Version: 0.3.0
-- Date: 2025-11-23

BEGIN TRANSACTION;

-- Add email column (nullable for backward compatibility)
ALTER TABLE users ADD COLUMN email TEXT;

-- Add unique constraint on email
CREATE UNIQUE INDEX idx_users_email ON users(email) WHERE email IS NOT NULL;

-- Update existing users (optional: set email based on username pattern)
-- UPDATE users SET email = username || '@example.com' WHERE email IS NULL;

COMMIT;
```

### Updated Schema

```sql
CREATE TABLE users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    is_admin        INTEGER NOT NULL DEFAULT 0,
    email           TEXT,                          -- NEW
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT                          -- NEW (optional)
);

CREATE UNIQUE INDEX idx_users_email ON users(email) WHERE email IS NOT NULL;
```

---

## Application Changes

### 1. Database Initialization (app.py)

```python
def init_db():
    schema = """
    CREATE TABLE IF NOT EXISTS users (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        username        TEXT NOT NULL UNIQUE,
        password_hash   TEXT NOT NULL,
        is_admin        INTEGER NOT NULL DEFAULT 0,
        email           TEXT,
        created_at      TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at      TEXT
    );

    CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email
        ON users(email) WHERE email IS NOT NULL;

    -- ... existing requests table ...
    """
    # ... rest of init_db ...
```

### 2. User Creation Form (create_user.html)

```html
<!-- Add email field to form -->
<div class="form-group">
  <label for="email">
    Email Address
    <span class="required">*</span>
  </label>
  <input
    type="email"
    id="email"
    name="email"
    required
    autocomplete="email"
    placeholder="user@example.com"
  >
  <p class="form-hint">Used for Cloudflare Access authentication</p>
</div>
```

### 3. User Creation Route (app.py)

```python
@app.route("/users/new", methods=["GET", "POST"])
@login_required
def create_user():
    user = current_user()
    if not user or not user["is_admin"]:
        flash("Admin access required.", "danger")
        return redirect(url_for("list_requests"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        email = request.form.get("email", "").strip()  # NEW
        is_admin = 1 if request.form.get("is_admin") else 0

        # Validation
        if not username or not password:
            flash("Username and password are required.", "danger")
            return redirect(url_for("create_user"))

        if not email:
            flash("Email address is required.", "danger")
            return redirect(url_for("create_user"))

        # Validate email format
        import re
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            flash("Invalid email format.", "danger")
            return redirect(url_for("create_user"))

        try:
            with closing(get_db()) as conn:
                conn.execute(
                    """INSERT INTO users (username, password_hash, is_admin, email, created_at)
                       VALUES (?, ?, ?, ?, ?)""",
                    (username, generate_password_hash(password), is_admin, email,
                     datetime.utcnow().isoformat()),
                )
                conn.commit()
        except sqlite3.IntegrityError as e:
            if "email" in str(e).lower():
                flash("Email address already exists.", "danger")
            else:
                flash("Username already exists.", "danger")
            return redirect(url_for("create_user"))

        flash(f"User '{username}' created.", "success")

        # NEW: Trigger CF Access sync (optional)
        app.logger.info(f"User created: {username} ({email}). Run sync to update CF Access.")

        return redirect(url_for("list_requests"))

    return render_template("create_user.html")
```

### 4. Optional: Auto-sync on User Creation

```python
def sync_cloudflare_access():
    """Sync user emails to Cloudflare Access (background task)"""
    import subprocess
    script_path = "/home/michael/dev/work/glider/glider-docker/cloudflared/bin/manage-jukebox-access.sh"

    try:
        result = subprocess.run(
            [script_path, "sync", "--auto"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            app.logger.info("CF Access synced successfully")
        else:
            app.logger.error(f"CF Access sync failed: {result.stderr}")
    except Exception as e:
        app.logger.error(f"CF Access sync error: {e}")

# Call after user creation (optional):
# sync_cloudflare_access()
```

---

## Sync Implementation

### Manual Sync Command

```bash
# Sync Jukebox user emails to Cloudflare Access
./manage-jukebox-access.sh sync

# Example output:
# [INFO] Syncing emails from Jukebox user database...
#
# Jukebox Database Emails:
#   - user1@example.com
#   - user2@example.com
#   - user3@example.com
#
# Cloudflare Access Emails:
#   - braband@gmail.com
#
# Update Cloudflare Access to match database? [y/N]: y
# [SUCCESS] Synced 3 email(s) from database to Cloudflare Access
#
# Allowed emails (3):
#   ✓ user1@example.com
#   ✓ user2@example.com
#   ✓ user3@example.com
```

### Automated Sync (Optional)

**Option A: Cron Job**
```bash
# Add to crontab
# Sync every hour
0 * * * * /path/to/manage-jukebox-access.sh sync --auto >> /var/log/cf-sync.log 2>&1
```

**Option B: Post-User-Creation Hook**
```python
# In app.py create_user() route
# After successful user creation:
subprocess.run(["/path/to/manage-jukebox-access.sh", "sync", "--auto"])
```

**Option C: Systemd Timer**
```ini
# /etc/systemd/system/jukebox-cf-sync.timer
[Unit]
Description=Sync Jukebox users to Cloudflare Access

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
```

---

## Sync Script Enhancement

Add `--auto` flag for non-interactive sync:

```bash
# In manage-jukebox-access.sh

cmd_sync() {
  local auto_mode=false
  if [[ "${1:-}" == "--auto" ]]; then
    auto_mode=true
  fi

  # ... existing sync logic ...

  if [[ "$auto_mode" == false ]]; then
    echo ""
    read -p "Update Cloudflare Access to match database? [y/N]: " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
      log_info "Sync cancelled"
      exit 0
    fi
  fi

  # Update policy with DB emails
  if update_policy "${db_emails_array[@]}"; then
    log_success "Synced ${#db_emails_array[@]} email(s) from database to Cloudflare Access"
  fi
}
```

---

## Migration Plan

### Phase 1: Database Migration (30 min)
1. Create migration script: `db/migrations/002_add_user_email.sql`
2. Test on dev database
3. Backup production database
4. Run migration: `sqlite3 data/requests.db < migrations/002_add_user_email.sql`
5. Verify migration: `sqlite3 data/requests.db ".schema users"`

### Phase 2: Application Updates (1 hour)
1. Update `init_db()` with new schema
2. Update `create_user.html` template
3. Update `create_user()` route with email validation
4. Test user creation with email
5. Deploy changes

### Phase 3: Existing User Migration (30 min)
**Option A: Manual**
```sql
-- Set emails for existing users
UPDATE users SET email = 'kim@example.com' WHERE username = 'kim';
UPDATE users SET email = 'mike@example.com' WHERE username = 'mike';
-- ... etc
```

**Option B: Script**
```python
# migrate_user_emails.py
import sqlite3

# Prompt admin for each user's email
conn = sqlite3.connect('data/requests.db')
cur = conn.execute("SELECT id, username FROM users WHERE email IS NULL")

for row in cur.fetchall():
    email = input(f"Email for user '{row[1]}': ")
    if email:
        conn.execute("UPDATE users SET email = ? WHERE id = ?", (email, row[0]))

conn.commit()
```

### Phase 4: Initial Sync (5 min)
```bash
# Run first sync to populate CF Access from database
./manage-jukebox-access.sh sync
```

---

## Testing Plan

### Unit Tests
```python
def test_email_validation():
    assert validate_email("user@example.com") == True
    assert validate_email("invalid-email") == False

def test_unique_email_constraint():
    # Try to create two users with same email
    # Should fail with IntegrityError
    pass

def test_sync_script():
    # Mock database with test users
    # Run sync
    # Verify CF Access policy updated
    pass
```

### Manual Testing
1. ✅ Create user with valid email → Success
2. ✅ Create user with invalid email → Error
3. ✅ Create user with duplicate email → Error
4. ✅ Run sync → CF Access updated
5. ✅ Remove user from DB, sync → Removed from CF Access
6. ✅ Add user to DB, sync → Added to CF Access

---

## Rollback Plan

If issues occur:

```bash
# Rollback database migration
BEGIN TRANSACTION;
DROP INDEX IF EXISTS idx_users_email;
-- Note: SQLite doesn't support DROP COLUMN
-- Create new table without email, copy data, rename
CREATE TABLE users_backup AS SELECT id, username, password_hash, is_admin, created_at FROM users;
DROP TABLE users;
ALTER TABLE users_backup RENAME TO users;
COMMIT;

# Revert application code
git revert <commit-hash>
docker compose restart jukebox

# Manually restore CF Access list
./manage-jukebox-access.sh add braband@gmail.com
```

---

## Success Criteria

- ✅ Email column added to users table
- ✅ User creation form includes email field
- ✅ Email validation prevents invalid formats
- ✅ Unique constraint prevents duplicate emails
- ✅ Sync script reads emails from database
- ✅ Sync script updates CF Access policy
- ✅ Existing users migrated with emails
- ✅ No data loss or corruption
- ✅ CF Access list matches database

---

## Future Enhancements

1. **Email verification**: Send verification email on user creation
2. **Email change**: Allow users to update their email
3. **Automatic sync**: Trigger sync on user create/update/delete
4. **Audit log**: Track CF Access policy changes
5. **Bulk import**: Import users from CSV with emails
6. **Self-service**: Allow users to set their own email

---

## Related Documentation

- [SECURITY-ENHANCEMENT-PLAN.md](./SECURITY-ENHANCEMENT-PLAN.md)
- [CLOUDFLARE-ACCESS-SETUP.md](./CLOUDFLARE-ACCESS-SETUP.md)
- `manage-jukebox-access.sh` - Email management script
- `create-jukebox-access-simple.sh` - Initial setup script

---

**Status**: Ready for implementation
**Next Steps**: Review and approve, then proceed with Phase 1 migration
