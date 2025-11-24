# Jukebox Mobile UX - Staged Implementation Guide

**Version**: 1.0.0
**Updated**: 2025-11-23

This guide breaks the mobile UX improvement into 6 testable stages. Each stage follows the cycle: **Implement → Test → Fix → Validate → Commit**.

---

## Stage Workflow

For each stage:

1. **Implement**: Make code changes per stage instructions
2. **Test**: Run pytest + manual mobile testing
3. **Fix**: Address any issues found
4. **Validate**: Complete stage checklist
5. **Commit**: Git commit with specific message format

### Commit Message Format
```
feat(ux): stage N - short description

- Bullet point of changes
- Another change
- Test results summary

Validation: [checklist items completed]
```

---

## Stage 1: Foundation & Template System

**Goal**: Set up template infrastructure and mobile viewport

**Effort**: 2-3 hours

### 1.1 Implementation Steps

#### Create Directory Structure
```bash
cd glider-docker/jukebox
mkdir -p app/templates/components
mkdir -p app/static/css
mkdir -p app/static/js
mkdir -p app/static/icons
```

#### Update app.py Configuration
```python
# In app.py, update Flask initialization (around line 69)

app = Flask(__name__,
           static_folder='static',
           template_folder='templates')
app.config["SECRET_KEY"] = SECRET_KEY
```

#### Create Base Template
File: `app/templates/base.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta name="theme-color" content="#6366f1">
  <meta name="description" content="Jukebox - Music request portal for Lidarr">
  <title>{% block title %}Jukebox{% endblock %}</title>

  <!-- Preload critical CSS -->
  <link rel="stylesheet" href="{{ url_for('static', filename='css/base.css') }}">
  {% block extra_css %}{% endblock %}
</head>
<body>
  <div id="app">
    {% block content %}{% endblock %}
  </div>

  <!-- Toast container for notifications -->
  <div id="toast-container" aria-live="polite" aria-atomic="true"></div>

  <!-- Flash messages converted to toasts -->
  {% with messages = get_flashed_messages(with_categories=true) %}
    {% if messages %}
      <script>
        // Inject flash messages as toasts when JS loads
        window.flashMessages = [
          {% for category, message in messages %}
            { type: "{{ category }}", message: "{{ message|safe }}" },
          {% endfor %}
        ];
      </script>
    {% endif %}
  {% endwith %}

  <script src="{{ url_for('static', filename='js/app.js') }}"></script>
  {% block extra_js %}{% endblock %}
</body>
</html>
```

#### Create Base CSS
File: `app/static/css/base.css`

```css
/* ============================================================================
   Jukebox Base CSS - Mobile First
   ============================================================================ */

/* CSS Variables */
:root {
  /* Spacing scale (8px base unit) */
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
  --spacing-2xl: 48px;

  /* Typography scale */
  --font-xs: 12px;
  --font-sm: 14px;
  --font-base: 16px;
  --font-lg: 18px;
  --font-xl: 24px;
  --font-2xl: 32px;

  /* Border radius */
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-full: 9999px;

  /* Shadows */
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.1);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);

  /* Status colors */
  --status-new: #6366f1;      /* Indigo */
  --status-submitted: #10b981; /* Green */
  --status-failed: #ef4444;    /* Red */
  --status-existing: #64748b;  /* Slate */

  /* Semantic colors - Light mode */
  --bg-primary: #ffffff;
  --bg-secondary: #f8fafc;
  --bg-tertiary: #e2e8f0;
  --text-primary: #0f172a;
  --text-secondary: #64748b;
  --text-tertiary: #94a3b8;
  --accent: #6366f1;
  --accent-hover: #4f46e5;
  --success: #10b981;
  --danger: #ef4444;
  --warning: #f59e0b;
  --border: #e2e8f0;

  /* Touch targets */
  --tap-target: 44px;

  /* Layout constraints */
  --max-width: 600px;
  --header-height: 60px;
  --bottom-nav-height: 64px;
}

/* Dark mode */
@media (prefers-color-scheme: dark) {
  :root {
    --bg-primary: #1e293b;
    --bg-secondary: #0f172a;
    --bg-tertiary: #334155;
    --text-primary: #f1f5f9;
    --text-secondary: #94a3b8;
    --text-tertiary: #64748b;
    --accent: #818cf8;
    --accent-hover: #6366f1;
    --border: #334155;
  }
}

/* Reset & Base Styles */
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html {
  -webkit-tap-highlight-color: transparent;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto',
               'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
  font-size: var(--font-base);
  line-height: 1.5;
  color: var(--text-primary);
  background: var(--bg-secondary);
  min-height: 100vh;
}

/* Typography */
h1, h2, h3, h4, h5, h6 {
  line-height: 1.2;
  font-weight: 600;
}

h1 { font-size: var(--font-2xl); margin-bottom: var(--spacing-lg); }
h2 { font-size: var(--font-xl); margin-bottom: var(--spacing-md); }
h3 { font-size: var(--font-lg); margin-bottom: var(--spacing-sm); }

p {
  margin-bottom: var(--spacing-md);
}

a {
  color: var(--accent);
  text-decoration: none;
  transition: color 0.2s;
}

a:hover {
  color: var(--accent-hover);
}

/* Layout */
#app {
  min-height: 100vh;
}

.container {
  width: 100%;
  max-width: var(--max-width);
  margin: 0 auto;
  padding: var(--spacing-md);
}

/* Buttons */
button,
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: var(--tap-target);
  padding: 12px 24px;
  font-size: var(--font-base);
  font-weight: 500;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s;
  background: var(--accent);
  color: white;
  text-align: center;
  line-height: 1.5;
}

button:hover,
.btn:hover {
  background: var(--accent-hover);
  transform: translateY(-1px);
}

button:active,
.btn:active {
  transform: translateY(0);
}

button:disabled,
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.btn-secondary {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.btn-secondary:hover {
  background: var(--border);
}

.btn-danger {
  background: var(--danger);
}

.btn-danger:hover {
  background: #dc2626;
}

/* Forms */
input,
textarea,
select {
  width: 100%;
  min-height: var(--tap-target);
  padding: 12px 16px;
  font-size: var(--font-base); /* Prevent iOS zoom */
  font-family: inherit;
  border: 2px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg-primary);
  color: var(--text-primary);
  transition: border-color 0.2s;
}

input:focus,
textarea:focus,
select:focus {
  outline: none;
  border-color: var(--accent);
}

textarea {
  min-height: 120px;
  resize: vertical;
}

label {
  display: block;
  margin-bottom: var(--spacing-xs);
  font-weight: 500;
  color: var(--text-primary);
}

.form-group {
  margin-bottom: var(--spacing-lg);
}

/* Toast Notifications */
#toast-container {
  position: fixed;
  bottom: calc(var(--bottom-nav-height) + var(--spacing-md));
  left: var(--spacing-md);
  right: var(--spacing-md);
  z-index: 9999;
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  margin-bottom: var(--spacing-sm);
  background: var(--bg-primary);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  opacity: 0;
  transform: translateY(20px);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  pointer-events: auto;
}

.toast.show {
  opacity: 1;
  transform: translateY(0);
}

.toast-icon {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-lg);
}

.toast-success {
  border-left: 4px solid var(--success);
}

.toast-danger,
.toast-error {
  border-left: 4px solid var(--danger);
}

.toast-info {
  border-left: 4px solid var(--accent);
}

/* Utility Classes */
.text-center { text-align: center; }
.text-secondary { color: var(--text-secondary); }
.mt-sm { margin-top: var(--spacing-sm); }
.mt-md { margin-top: var(--spacing-md); }
.mt-lg { margin-top: var(--spacing-lg); }
.mb-sm { margin-bottom: var(--spacing-sm); }
.mb-md { margin-bottom: var(--spacing-md); }
.mb-lg { margin-bottom: var(--spacing-lg); }

/* Loading Spinner */
.spinner {
  width: 20px;
  height: 20px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Desktop adjustments */
@media (min-width: 768px) {
  .container {
    padding: var(--spacing-xl);
  }

  #toast-container {
    left: 50%;
    right: auto;
    transform: translateX(-50%);
    max-width: var(--max-width);
    bottom: var(--spacing-lg);
  }
}
```

#### Create Base JavaScript
File: `app/static/js/app.js`

```javascript
/**
 * Jukebox - Mobile UX JavaScript
 * Progressive enhancements for forms, toasts, and interactions
 */

// Toast notification system
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;

  const icons = {
    success: '✓',
    error: '✕',
    danger: '⚠',
    info: 'ℹ'
  };

  toast.innerHTML = `
    <span class="toast-icon">${icons[type] || icons.info}</span>
    <span>${message}</span>
  `;

  container.appendChild(toast);

  // Trigger animation
  requestAnimationFrame(() => {
    toast.classList.add('show');
  });

  // Auto-dismiss after 3 seconds
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// Display flash messages on page load
document.addEventListener('DOMContentLoaded', () => {
  if (window.flashMessages) {
    window.flashMessages.forEach(msg => {
      showToast(msg.message, msg.type);
    });
  }
});

// Form submission loading states
document.addEventListener('DOMContentLoaded', () => {
  const forms = document.querySelectorAll('form[method="POST"]');

  forms.forEach(form => {
    form.addEventListener('submit', (e) => {
      const submitBtn = form.querySelector('button[type="submit"]');
      if (submitBtn && !submitBtn.disabled) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner"></span> Processing...';
      }
    });
  });
});

// Export for use in other scripts
window.showToast = showToast;
```

### 1.2 Testing

#### Pytest Tests
```bash
cd glider-docker/jukebox
python -m pytest tests/test_app.py -v
```

Expected: All tests pass (no breaking changes yet)

#### Manual Testing
1. Start container:
   ```bash
   cd glider-docker/jukebox
   docker compose build jukebox
   docker compose up jukebox
   ```

2. Test on desktop browser:
   - Open http://localhost:5000
   - Should see current pages (still unstyled for now)
   - Check browser console for errors

3. Test on mobile:
   - Open Chrome DevTools
   - Toggle device toolbar (Cmd+Shift+M)
   - Select iPhone SE (375px)
   - Verify no console errors

### 1.3 Validation Checklist

- [ ] Directory structure created
- [ ] `base.html` template exists
- [ ] `base.css` loaded without errors
- [ ] `app.js` loaded without errors
- [ ] Mobile viewport meta tag present (check in DevTools)
- [ ] CSS variables defined (check in DevTools computed styles)
- [ ] No JavaScript console errors
- [ ] Pytest tests pass

### 1.4 Commit

```bash
git add app/templates app/static
git commit -m "feat(ux): stage 1 - foundation and template system

- Create template directory structure (templates/, static/)
- Add base.html with mobile viewport and CSS variables
- Implement base.css with mobile-first styles
- Add app.js with toast notification system
- Configure Flask to use templates/ and static/ folders

Testing: pytest passed, no console errors
Validation: Mobile viewport configured, CSS variables loaded"
```

---

## Stage 2: Login Page Migration

**Goal**: Convert login page to mobile-friendly template

**Effort**: 1-2 hours

### 2.1 Implementation Steps

#### Create Login Template
File: `app/templates/login.html`

```html
{% extends "base.html" %}

{% block title %}Login - Jukebox{% endblock %}

{% block content %}
<div class="login-page">
  <div class="login-container">
    <div class="login-header">
      <h1>🎵 Jukebox</h1>
      <p class="text-secondary">Request music for your library</p>
    </div>

    <form method="POST" class="login-form">
      <div class="form-group">
        <label for="username">Username</label>
        <input
          type="text"
          id="username"
          name="username"
          autocomplete="username"
          autofocus
          required
          placeholder="Enter your username"
        >
      </div>

      <div class="form-group">
        <label for="password">Password</label>
        <input
          type="password"
          id="password"
          name="password"
          autocomplete="current-password"
          required
          placeholder="Enter your password"
        >
      </div>

      <button type="submit" class="btn btn-primary btn-block">
        Login
      </button>
    </form>

    <p class="login-footer text-secondary text-center mt-lg">
      Default credentials: admin / admin
    </p>
  </div>
</div>
{% endblock %}

{% block extra_css %}
<style>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-md);
}

.login-container {
  width: 100%;
  max-width: 400px;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-xl);
  box-shadow: var(--shadow-md);
}

.login-header {
  text-align: center;
  margin-bottom: var(--spacing-xl);
}

.login-header h1 {
  font-size: var(--font-2xl);
  margin-bottom: var(--spacing-xs);
}

.login-form {
  margin-bottom: var(--spacing-md);
}

.btn-block {
  width: 100%;
}

.login-footer {
  font-size: var(--font-sm);
}
</style>
{% endblock %}
```

#### Update app.py Login Route
```python
# In app.py, replace the login route (around line 299)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        with closing(get_db()) as conn:
            cur = conn.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cur.fetchone()

        if row and check_password_hash(row["password_hash"], password):
            session["user_id"] = row["id"]
            flash("Logged in successfully.", "success")
            next_url = request.args.get("next") or url_for("list_requests")
            return redirect(next_url)

        flash("Invalid username or password.", "danger")

    return render_template("login.html")
```

### 2.2 Testing

#### Automated Tests
```bash
python -m pytest tests/test_app.py::AppTests::test_api_flow_creates_and_lists_requests -v
```

#### Manual Testing
1. Rebuild and restart:
   ```bash
   docker compose build jukebox
   docker compose up -d jukebox
   ```

2. Desktop test:
   - Navigate to http://localhost:5000/login
   - Verify centered card layout
   - Test login with admin/admin
   - Verify success toast appears
   - Verify redirect to /requests

3. Mobile test (Chrome DevTools):
   - iPhone SE (375px width)
   - Verify card is centered and readable
   - Tap username field (should not zoom page)
   - Test login flow
   - Verify toast appears at bottom

4. Test invalid credentials:
   - Enter wrong password
   - Verify error toast appears
   - Form should remain filled (not cleared)

### 2.3 Validation Checklist

- [ ] Login page uses `render_template("login.html")`
- [ ] Page renders on mobile (320px width)
- [ ] Font size is 16px (prevents iOS zoom)
- [ ] Inputs have proper autocomplete attributes
- [ ] Form submits successfully
- [ ] Success toast appears after login
- [ ] Error toast appears for invalid credentials
- [ ] Loading state appears on button during submit
- [ ] Pytest tests still pass

### 2.4 Commit

```bash
git add app/templates/login.html app/app.py
git commit -m "feat(ux): stage 2 - mobile-friendly login page

- Migrate login route from render_template_string to render_template
- Create login.html with centered card layout
- Add mobile-first responsive design
- Implement autofocus and autocomplete attributes
- Add password field with proper security attributes
- Style with CSS variables from base.css

Testing: Manual login tested on 320px-768px widths
Validation: No iOS zoom, toast notifications working"
```

---

## Stage 3: Request List (Card Layout)

**Goal**: Replace table with mobile-friendly card layout

**Effort**: 3-4 hours

### 3.1 Implementation Steps

#### Create Status Badge Component
File: `app/templates/components/status_badge.html`

```html
{% macro status_badge(status) %}
<span class="status-badge status-{{ status }}">
  {% if status == 'new' %}
    <span class="status-icon">🔵</span>
  {% elif status == 'submitted' %}
    <span class="status-icon">✓</span>
  {% elif status == 'failed' %}
    <span class="status-icon">✕</span>
  {% elif status == 'existing' %}
    <span class="status-icon">ℹ</span>
  {% endif %}
  <span class="status-text">{{ status|upper }}</span>
</span>
{% endmacro %}
```

#### Create Request Card Component
File: `app/templates/components/request_card.html`

```html
{% from 'components/status_badge.html' import status_badge %}

{% macro request_card(req) %}
<div class="request-card" data-status="{{ req.status }}">
  <div class="card-header">
    <h3 class="artist-name">{{ req.artist_name }}</h3>
    {{ status_badge(req.status) }}
  </div>

  {% if req.album_title %}
  <p class="album-title">{{ req.album_title }}</p>
  {% endif %}

  <div class="card-meta">
    <span class="meta-item">
      <span class="meta-icon">👤</span>
      <span>{{ req.username }}</span>
    </span>
    <span class="meta-item">
      <span class="meta-icon">📅</span>
      <span>{{ req.created_at[:10] }}</span>
    </span>
  </div>

  {% if req.note %}
  <p class="card-note">{{ req.note }}</p>
  {% endif %}

  {% if req.last_error %}
  <div class="error-message">
    <span class="error-icon">⚠️</span>
    <span class="error-text">{{ req.last_error }}</span>
  </div>
  {% endif %}
</div>
{% endmacro %}
```

#### Create Requests List Page
File: `app/templates/requests.html`

```html
{% extends "base.html" %}
{% from 'components/request_card.html' import request_card %}

{% block title %}Requests - Jukebox{% endblock %}

{% block content %}
<div class="requests-page">
  <!-- Header -->
  <header class="page-header">
    <div class="header-content">
      <h1>🎵 Jukebox</h1>
      <p class="user-info">{{ user.username }}</p>
    </div>
    <form method="POST" action="{{ url_for('logout') }}" class="logout-form">
      <button type="submit" class="btn btn-secondary btn-sm">Logout</button>
    </form>
  </header>

  <!-- Request List -->
  <div class="container">
    {% if rows|length == 0 %}
    <div class="empty-state">
      <div class="empty-icon">🎵</div>
      <h2>No requests yet</h2>
      <p class="text-secondary">Tap the + button to request music</p>
    </div>
    {% else %}
    <div class="request-list">
      {% for req in rows %}
        {{ request_card(req) }}
      {% endfor %}
    </div>
    {% endif %}
  </div>

  <!-- Floating Action Button -->
  <a href="{{ url_for('new_request') }}" class="fab" aria-label="New Request">
    <span class="fab-icon">+</span>
  </a>

  <!-- Bottom Navigation -->
  <nav class="bottom-nav">
    <a href="{{ url_for('list_requests') }}" class="nav-item active">
      <span class="nav-icon">🏠</span>
      <span class="nav-label">Home</span>
    </a>
    <a href="{{ url_for('new_request') }}" class="nav-item">
      <span class="nav-icon">➕</span>
      <span class="nav-label">New</span>
    </a>
    {% if user.is_admin %}
    <a href="{{ url_for('create_user') }}" class="nav-item">
      <span class="nav-icon">👤</span>
      <span class="nav-label">Users</span>
    </a>
    {% endif %}
  </nav>
</div>
{% endblock %}

{% block extra_css %}
<style>
.requests-page {
  min-height: 100vh;
  padding-bottom: var(--bottom-nav-height);
}

.page-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border);
  padding: var(--spacing-md);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-content h1 {
  font-size: var(--font-xl);
  margin: 0;
}

.user-info {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  margin: 0;
}

.logout-form {
  margin: 0;
}

.btn-sm {
  min-height: 36px;
  padding: 8px 16px;
  font-size: var(--font-sm);
}

/* Request Cards */
.request-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  padding: var(--spacing-md) 0;
}

.request-card {
  background: var(--bg-primary);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  box-shadow: var(--shadow-sm);
  transition: transform 0.2s, box-shadow 0.2s;
}

.request-card:active {
  transform: scale(0.98);
}

.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-xs);
}

.artist-name {
  font-size: var(--font-lg);
  font-weight: 600;
  margin: 0;
  flex: 1;
}

.album-title {
  font-size: var(--font-base);
  color: var(--text-secondary);
  margin: 0 0 var(--spacing-sm) 0;
}

.card-meta {
  display: flex;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-sm);
  font-size: var(--font-sm);
  color: var(--text-secondary);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.card-note {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  font-style: italic;
  margin: var(--spacing-sm) 0 0 0;
  padding: var(--spacing-sm);
  background: var(--bg-secondary);
  border-radius: var(--radius-sm);
}

/* Status Badge */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  border-radius: var(--radius-full);
  font-size: var(--font-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  white-space: nowrap;
}

.status-new {
  background: rgba(99, 102, 241, 0.1);
  color: var(--status-new);
}

.status-submitted {
  background: rgba(16, 185, 129, 0.1);
  color: var(--status-submitted);
}

.status-failed {
  background: rgba(239, 68, 68, 0.1);
  color: var(--status-failed);
}

.status-existing {
  background: rgba(100, 116, 139, 0.1);
  color: var(--status-existing);
}

/* Error Message */
.error-message {
  display: flex;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm);
  background: rgba(239, 68, 68, 0.1);
  border-left: 3px solid var(--danger);
  border-radius: var(--radius-sm);
  margin-top: var(--spacing-sm);
  font-size: var(--font-sm);
  color: var(--danger);
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: var(--spacing-2xl) var(--spacing-md);
}

.empty-icon {
  font-size: 64px;
  margin-bottom: var(--spacing-md);
}

.empty-state h2 {
  color: var(--text-primary);
  margin-bottom: var(--spacing-sm);
}

/* Floating Action Button */
.fab {
  position: fixed;
  bottom: calc(var(--bottom-nav-height) + var(--spacing-md));
  right: var(--spacing-md);
  width: 56px;
  height: 56px;
  background: var(--accent);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--shadow-lg);
  z-index: 90;
  transition: transform 0.2s;
}

.fab:hover {
  transform: scale(1.1);
  color: white;
}

.fab-icon {
  font-size: var(--font-2xl);
  font-weight: 300;
  line-height: 1;
}

/* Bottom Navigation */
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: var(--bottom-nav-height);
  background: var(--bg-primary);
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: space-around;
  align-items: center;
  z-index: 100;
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: var(--spacing-xs);
  color: var(--text-secondary);
  min-width: 64px;
  transition: color 0.2s;
}

.nav-item:hover,
.nav-item.active {
  color: var(--accent);
}

.nav-icon {
  font-size: 24px;
  line-height: 1;
}

.nav-label {
  font-size: var(--font-xs);
  font-weight: 500;
}

/* Desktop adjustments */
@media (min-width: 768px) {
  .fab {
    bottom: var(--spacing-xl);
  }

  .bottom-nav {
    display: none;
  }

  .requests-page {
    padding-bottom: 0;
  }
}
</style>
{% endblock %}
```

#### Update app.py Routes
```python
# In app.py, replace _render_requests_page and list_requests (around line 386)

def _render_requests_page(user):
    with closing(get_db()) as conn:
        if user["is_admin"]:
            cur = conn.execute(
                "SELECT r.*, u.username FROM requests r JOIN users u ON r.user_id = u.id "
                "ORDER BY r.created_at DESC"
            )
        else:
            cur = conn.execute(
                "SELECT r.*, u.username FROM requests r JOIN users u ON r.user_id = u.id "
                "WHERE r.user_id = ? ORDER BY r.created_at DESC",
                (user["id"],),
            )
        rows = cur.fetchall()

    return render_template("requests.html", user=user, rows=rows)


@app.route("/", methods=["GET"])
@app.route("/requests", methods=["GET"])
@login_required
def list_requests():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    return _render_requests_page(user)
```

### 3.2 Testing

#### Automated Tests
```bash
python -m pytest tests/test_app.py -v
```

#### Manual Testing
1. Rebuild:
   ```bash
   docker compose build jukebox
   docker compose up -d jukebox
   ```

2. Create test data:
   - Login as admin
   - Create 2-3 test requests with different statuses
   - Add notes to some requests

3. Desktop test:
   - Verify card layout
   - Check status badges render correctly
   - Test FAB button navigation
   - Verify bottom nav hidden on desktop

4. Mobile test (375px width):
   - Verify cards stack vertically
   - Test sticky header scroll behavior
   - Tap FAB button → should navigate to new request
   - Test bottom nav buttons
   - Verify empty state (logout, login as new user)

5. Test with errors:
   - Check that `last_error` displays properly
   - Verify error message styling

### 3.3 Validation Checklist

- [ ] Cards display instead of table
- [ ] Status badges show correct colors
- [ ] Empty state displays when no requests
- [ ] FAB button visible and functional
- [ ] Bottom nav displays on mobile
- [ ] Bottom nav hidden on desktop (>768px)
- [ ] Header is sticky on scroll
- [ ] Error messages display properly
- [ ] All card data renders correctly
- [ ] Pytest tests pass

### 3.4 Commit

```bash
git add app/templates app/app.py
git commit -m "feat(ux): stage 3 - card-based request list

- Replace table layout with mobile-friendly cards
- Create status_badge and request_card components
- Add floating action button (FAB) for new requests
- Implement bottom navigation bar
- Add empty state for zero requests
- Style status indicators with color coding
- Add sticky header with user info

Testing: Tested on 320px-1024px widths, all layouts working
Validation: Cards readable, FAB accessible, bottom nav functional"
```

---

## Stage 4: New Request Form

**Goal**: Mobile-optimized request form

**Effort**: 2-3 hours

### 4.1 Implementation Steps

#### Create New Request Template
File: `app/templates/new_request.html`

```html
{% extends "base.html" %}

{% block title %}New Request - Jukebox{% endblock %}

{% block content %}
<div class="new-request-page">
  <!-- Header -->
  <header class="page-header">
    <a href="{{ url_for('list_requests') }}" class="back-button" aria-label="Back">
      <span>←</span>
    </a>
    <h1>New Request</h1>
    <div></div> <!-- Spacer for flex layout -->
  </header>

  <!-- Form -->
  <div class="container">
    <form method="POST" class="request-form" id="requestForm">
      <div class="form-group">
        <label for="artist_name">
          Artist Name
          <span class="required">*</span>
        </label>
        <input
          type="text"
          id="artist_name"
          name="artist_name"
          required
          autofocus
          placeholder="e.g., Pink Floyd"
          aria-describedby="artist-hint"
        >
        <p id="artist-hint" class="form-hint">Enter the artist or band name</p>
      </div>

      <div class="form-group">
        <label for="album_title">Album Title (optional)</label>
        <input
          type="text"
          id="album_title"
          name="album_title"
          placeholder="e.g., The Wall"
          aria-describedby="album-hint"
        >
        <p id="album-hint" class="form-hint">Leave blank to request all albums</p>
      </div>

      <div class="form-group">
        <label for="note">Note (optional)</label>
        <textarea
          id="note"
          name="note"
          rows="4"
          placeholder="Any special requests or notes..."
          maxlength="500"
          aria-describedby="note-hint"
        ></textarea>
        <p id="note-hint" class="form-hint">
          <span id="charCount">0</span>/500 characters
        </p>
      </div>

      <div class="form-actions">
        <a href="{{ url_for('list_requests') }}" class="btn btn-secondary">
          Cancel
        </a>
        <button type="submit" class="btn btn-primary">
          Submit Request
        </button>
      </div>
    </form>
  </div>
</div>
{% endblock %}

{% block extra_css %}
<style>
.new-request-page {
  min-height: 100vh;
  background: var(--bg-secondary);
}

.page-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border);
  padding: var(--spacing-md);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.page-header h1 {
  font-size: var(--font-xl);
  margin: 0;
}

.back-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  color: var(--text-primary);
  font-size: 24px;
  transition: background 0.2s;
}

.back-button:hover {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.request-form {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  margin-top: var(--spacing-md);
  box-shadow: var(--shadow-sm);
}

.required {
  color: var(--danger);
}

.form-hint {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  margin: var(--spacing-xs) 0 0 0;
}

.form-actions {
  display: flex;
  gap: var(--spacing-md);
  margin-top: var(--spacing-xl);
}

.form-actions .btn {
  flex: 1;
}

/* Character counter */
#charCount {
  font-weight: 600;
  color: var(--text-primary);
}

/* Form validation styles */
input:invalid:not(:placeholder-shown),
textarea:invalid:not(:placeholder-shown) {
  border-color: var(--danger);
}

input:valid:not(:placeholder-shown) {
  border-color: var(--success);
}
</style>
{% endblock %}

{% block extra_js %}
<script>
// Character counter for note field
document.addEventListener('DOMContentLoaded', () => {
  const noteField = document.getElementById('note');
  const charCount = document.getElementById('charCount');

  if (noteField && charCount) {
    noteField.addEventListener('input', () => {
      charCount.textContent = noteField.value.length;
    });
  }

  // Form validation
  const form = document.getElementById('requestForm');
  const artistField = document.getElementById('artist_name');

  if (form && artistField) {
    form.addEventListener('submit', (e) => {
      if (!artistField.value.trim()) {
        e.preventDefault();
        showToast('Artist name is required', 'danger');
        artistField.focus();
      }
    });
  }
});
</script>
{% endblock %}
```

#### Update app.py New Request Route
```python
# In app.py, replace new_request route (around line 446)

@app.route("/request/new", methods=["GET", "POST"])
@login_required
def new_request():
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    if request.method == "POST":
        artist_name = request.form.get("artist_name", "").strip()
        album_title = request.form.get("album_title", "").strip() or None
        note = request.form.get("note", "").strip() or None

        if not artist_name:
            flash("Artist name is required.", "danger")
            return redirect(url_for("new_request"))

        tag = build_user_tag(user["username"])
        root_folder = build_user_root_folder(user["username"])

        with closing(get_db()) as conn:
            cur = conn.execute(
                """
                INSERT INTO requests (user_id, artist_name, album_title, note,
                                      status, tag, root_folder_path, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user["id"],
                    artist_name,
                    album_title,
                    note,
                    "new",
                    tag,
                    root_folder,
                    datetime.utcnow().isoformat(),
                    datetime.utcnow().isoformat(),
                ),
            )
            req_id = cur.lastrowid
            conn.commit()

        data, err = create_artist_in_lidarr(user["username"], artist_name)

        with closing(get_db()) as conn:
            if err:
                conn.execute(
                    "UPDATE requests SET status = ?, last_error = ?, updated_at = ? WHERE id = ?",
                    ("failed", err, datetime.utcnow().isoformat(), req_id),
                )
                conn.commit()
                flash(f"Failed to send request to Lidarr: {err}", "danger")
            else:
                lidarr_artist_id = data.get("id") if data else None
                conn.execute(
                    """
                    UPDATE requests
                    SET status = ?, lidarr_artist_id = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    ("submitted", lidarr_artist_id, datetime.utcnow().isoformat(), req_id),
                )
                conn.commit()
                flash("Request submitted to Lidarr.", "success")

        return redirect(url_for("list_requests"))

    return render_template("new_request.html")
```

### 4.2 Testing

#### Automated Tests
```bash
python -m pytest tests/test_app.py -v
```

#### Manual Testing
1. Rebuild:
   ```bash
   docker compose build jukebox
   docker compose up -d jukebox
   ```

2. Form validation test:
   - Open new request form
   - Try submitting empty form → should show error toast
   - Fill artist name only → should submit
   - Fill all fields → should submit

3. Character counter test:
   - Type in note field
   - Verify counter updates in real-time
   - Test 500 character limit

4. Mobile UX test (375px):
   - Verify back button works
   - Test form inputs (should not zoom on iOS)
   - Verify buttons are touch-friendly
   - Test cancel button
   - Test submit with loading state

5. Success flow test:
   - Submit valid request
   - Verify redirect to request list
   - Verify success toast appears
   - Verify new card appears in list

### 4.3 Validation Checklist

- [ ] Form template renders correctly
- [ ] Back button navigates to request list
- [ ] Artist name field is required
- [ ] Character counter works
- [ ] Form validation prevents empty submission
- [ ] Submit button shows loading state
- [ ] Success flow redirects and shows toast
- [ ] Error flow shows error toast
- [ ] Cancel button works
- [ ] No iOS zoom on input focus (font-size: 16px)
- [ ] Pytest tests pass

### 4.4 Commit

```bash
git add app/templates/new_request.html app/app.py
git commit -m "feat(ux): stage 4 - mobile-optimized request form

- Create new_request.html with mobile-first design
- Add back button navigation to header
- Implement character counter for note field
- Add client-side form validation
- Style form with proper spacing and touch targets
- Add form hints and placeholder text
- Implement loading state on submit

Testing: Form validated on mobile, character counter working
Validation: Submit flow tested, error handling verified"
```

---

## Stage 5: Create User & Polish

**Goal**: Complete remaining pages and add polish

**Effort**: 2-3 hours

### 5.1 Implementation Steps

#### Create User Template
File: `app/templates/create_user.html`

```html
{% extends "base.html" %}

{% block title %}Create User - Jukebox{% endblock %}

{% block content %}
<div class="create-user-page">
  <!-- Header -->
  <header class="page-header">
    <a href="{{ url_for('list_requests') }}" class="back-button" aria-label="Back">
      <span>←</span>
    </a>
    <h1>Create User</h1>
    <div></div>
  </header>

  <!-- Form -->
  <div class="container">
    <form method="POST" class="user-form">
      <div class="form-group">
        <label for="username">
          Username
          <span class="required">*</span>
        </label>
        <input
          type="text"
          id="username"
          name="username"
          required
          autofocus
          autocomplete="off"
          placeholder="Enter username"
        >
      </div>

      <div class="form-group">
        <label for="password">
          Password
          <span class="required">*</span>
        </label>
        <input
          type="password"
          id="password"
          name="password"
          required
          autocomplete="new-password"
          placeholder="Enter password"
        >
        <p class="form-hint">Choose a secure password</p>
      </div>

      <div class="form-group">
        <label class="checkbox-label">
          <input
            type="checkbox"
            name="is_admin"
            class="checkbox-input"
          >
          <span class="checkbox-text">Admin privileges</span>
        </label>
        <p class="form-hint">Admins can view all requests and create users</p>
      </div>

      <div class="form-actions">
        <a href="{{ url_for('list_requests') }}" class="btn btn-secondary">
          Cancel
        </a>
        <button type="submit" class="btn btn-primary">
          Create User
        </button>
      </div>
    </form>
  </div>
</div>
{% endblock %}

{% block extra_css %}
<style>
.create-user-page {
  min-height: 100vh;
  background: var(--bg-secondary);
}

.user-form {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  margin-top: var(--spacing-md);
  box-shadow: var(--shadow-sm);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  cursor: pointer;
  margin: 0;
}

.checkbox-input {
  width: 24px;
  height: 24px;
  cursor: pointer;
}

.checkbox-text {
  font-weight: 500;
  color: var(--text-primary);
}
</style>
{% endblock %}
```

#### Update app.py Create User Route
```python
# In app.py, replace create_user route (around line 338)

@app.route("/users/new", methods=["GET", "POST"])
@login_required
def create_user():
    user = current_user()
    if not user or not user["is_admin"]:
        flash("Admin access required to create users.", "danger")
        return redirect(url_for("list_requests"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        is_admin = 1 if request.form.get("is_admin") == "on" else 0

        if not username or not password:
            flash("Username and password are required.", "danger")
            return redirect(url_for("create_user"))

        try:
            with closing(get_db()) as conn:
                conn.execute(
                    "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)",
                    (username, generate_password_hash(password), is_admin),
                )
                conn.commit()
        except sqlite3.IntegrityError:
            flash("Username already exists.", "danger")
            return redirect(url_for("create_user"))

        flash(f"User '{username}' created.", "success")
        return redirect(url_for("list_requests"))

    return render_template("create_user.html")
```

#### Add CSS for Components
File: `app/static/css/components.css`

```css
/* ============================================================================
   Jukebox Components CSS
   ============================================================================ */

/* Page Header Styles (shared across pages) */
.page-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border);
  padding: var(--spacing-md);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.page-header h1 {
  font-size: var(--font-xl);
  margin: 0;
}

.back-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  color: var(--text-primary);
  font-size: 24px;
  transition: background 0.2s;
}

.back-button:hover {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

/* Form Styles (shared) */
.form-hint {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  margin: var(--spacing-xs) 0 0 0;
}

.required {
  color: var(--danger);
}

.form-actions {
  display: flex;
  gap: var(--spacing-md);
  margin-top: var(--spacing-xl);
}

.form-actions .btn {
  flex: 1;
}

/* Checkbox Styles */
.checkbox-label {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  cursor: pointer;
  margin: 0;
}

.checkbox-input {
  width: 24px;
  height: 24px;
  cursor: pointer;
}

.checkbox-text {
  font-weight: 500;
  color: var(--text-primary);
}
```

#### Update base.html to Include Components CSS
```html
<!-- In app/templates/base.html, update the CSS links -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/base.css') }}">
<link rel="stylesheet" href="{{ url_for('static', filename='css/components.css') }}">
{% block extra_css %}{% endblock %}
```

### 5.2 Testing

#### Automated Tests
```bash
python -m pytest tests/test_app.py -v
```

#### Manual Testing
1. Rebuild:
   ```bash
   docker compose build jukebox
   docker compose up -d jukebox
   ```

2. Admin access test:
   - Login as admin
   - Verify "Users" nav item appears
   - Navigate to create user page
   - Verify form renders

3. Non-admin test:
   - Login as non-admin user (create one first)
   - Verify "Users" nav item hidden
   - Try accessing `/users/new` directly
   - Should redirect with error toast

4. User creation test:
   - Fill form with new username
   - Toggle admin checkbox
   - Submit form
   - Verify success toast
   - Verify redirect to requests list

5. Duplicate username test:
   - Try creating user with existing username
   - Verify error toast appears

6. Mobile UX test (375px):
   - Test all form interactions
   - Verify touch targets
   - Test navigation flows

### 5.3 Validation Checklist

- [ ] Create user page renders
- [ ] Admin-only access enforced
- [ ] Form validation works
- [ ] Checkbox toggles correctly
- [ ] Success flow creates user
- [ ] Duplicate username shows error
- [ ] Non-admin redirect works
- [ ] Toast notifications appear
- [ ] Mobile layout correct
- [ ] Pytest tests pass

### 5.4 Commit

```bash
git add app/templates app/static app/app.py
git commit -m "feat(ux): stage 5 - create user page and component polish

- Create create_user.html with mobile-first design
- Add components.css for shared component styles
- Update base.html to include components.css
- Implement checkbox styling for admin toggle
- Add form validation and error handling
- Ensure admin-only access enforcement

Testing: All user creation flows tested, access control verified
Validation: Mobile layout confirmed, pytest passing"
```

---

## Stage 6: Final Testing & Validation

**Goal**: Comprehensive testing and fixes

**Effort**: 1-2 hours

### 6.1 Cross-Device Testing

#### Test Matrix

| Device/Browser | Width | Tests |
|----------------|-------|-------|
| iPhone SE | 375px | All flows |
| iPhone 12 Pro | 390px | All flows |
| Pixel 5 | 393px | All flows |
| iPad Mini | 768px | Responsive |
| Desktop Chrome | 1024px+ | Desktop view |
| Desktop Firefox | 1024px+ | Desktop view |
| Desktop Safari | 1024px+ | Desktop view |

#### Test Flows
1. **Login Flow**
   - [ ] Login with valid credentials
   - [ ] Login with invalid credentials
   - [ ] Verify toast notifications
   - [ ] Check redirect after login

2. **Request List Flow**
   - [ ] View empty state (new user)
   - [ ] View populated list
   - [ ] Scroll through many requests
   - [ ] Test status badge colors
   - [ ] Test FAB button
   - [ ] Test bottom navigation

3. **Create Request Flow**
   - [ ] Navigate from FAB
   - [ ] Navigate from bottom nav
   - [ ] Fill artist only
   - [ ] Fill all fields
   - [ ] Test character counter
   - [ ] Submit and verify success
   - [ ] Test cancel button

4. **Create User Flow (Admin)**
   - [ ] Navigate to create user
   - [ ] Create regular user
   - [ ] Create admin user
   - [ ] Test duplicate username
   - [ ] Verify created users can login

5. **Non-Admin Flow**
   - [ ] Login as regular user
   - [ ] Verify no admin nav items
   - [ ] Try accessing admin routes
   - [ ] Verify can only see own requests

### 6.2 Performance Testing

#### Lighthouse Audit
```bash
# Use Chrome DevTools
# 1. Open http://localhost:5000
# 2. Open DevTools (F12)
# 3. Go to Lighthouse tab
# 4. Select "Mobile" device
# 5. Run audit
```

**Target Scores:**
- Performance: ≥ 90
- Accessibility: ≥ 95
- Best Practices: ≥ 90
- SEO: ≥ 90

#### Performance Fixes

If performance < 90:
- Inline critical CSS in `<head>`
- Add `defer` to JavaScript
- Optimize CSS (remove unused rules)
- Add caching headers

### 6.3 Accessibility Testing

#### Keyboard Navigation
- [ ] Tab through all interactive elements
- [ ] Enter key submits forms
- [ ] Escape key closes modals (if any)
- [ ] Arrow keys work as expected

#### Screen Reader Testing
- [ ] Test with Chrome screen reader extension
- [ ] Verify ARIA labels present
- [ ] Check form field labels
- [ ] Test toast announcements

#### Color Contrast
- [ ] Check text contrast ratios (4.5:1 minimum)
- [ ] Test dark mode contrast
- [ ] Verify status badge readability

### 6.4 Bug Fixes

Common issues to check:

1. **iOS-specific**
   - [ ] No zoom on input focus (font-size ≥ 16px)
   - [ ] Sticky header works on Safari
   - [ ] Touch targets ≥ 44px

2. **Android-specific**
   - [ ] Bottom nav doesn't overlap content
   - [ ] Material design interactions feel native

3. **Cross-browser**
   - [ ] CSS Grid works in all browsers
   - [ ] Flexbox layouts correct
   - [ ] Border radius renders properly

### 6.5 Final Validation Checklist

#### Code Quality
- [ ] All `render_template_string()` removed
- [ ] No inline styles (use CSS files)
- [ ] JavaScript follows conventions
- [ ] CSS variables used consistently
- [ ] No console errors

#### Functionality
- [ ] All forms submit correctly
- [ ] All navigation works
- [ ] Toasts display properly
- [ ] Loading states appear
- [ ] Error handling works

#### Mobile UX
- [ ] Readable on 320px width
- [ ] Touch targets ≥ 44px
- [ ] No horizontal scroll
- [ ] Bottom nav functional
- [ ] FAB accessible

#### Desktop UX
- [ ] Layout scales to desktop
- [ ] Bottom nav hidden on desktop
- [ ] Cards have max-width
- [ ] Hover states work

#### Tests
- [ ] All pytest tests pass
- [ ] No regression bugs
- [ ] Error paths tested
- [ ] Success paths tested

### 6.6 Final Commit

```bash
# After all fixes
git add .
git commit -m "feat(ux): stage 6 - final testing and validation

- Cross-device testing completed (iOS, Android, Desktop)
- Performance optimization (Lighthouse score: XX)
- Accessibility improvements (ARIA labels, keyboard nav)
- Bug fixes for iOS and Android
- Final validation of all user flows

Testing: All devices tested, Lighthouse score ≥ 90
Validation: Complete checklist, pytest passing, no regressions"
```

---

## Post-Implementation

### Documentation Updates
- [ ] Update `HANDOFF-JUKEBOX.md` with new UX
- [ ] Update `request-portal-requirements.md`
- [ ] Create screenshots for `docs/`
- [ ] Update `MOBILE-UX-PROGRESS.md` with completion

### Deployment
- [ ] Build production image
- [ ] Test on staging environment
- [ ] Deploy to production
- [ ] Verify live site on real devices

### Monitoring
- [ ] Check error logs
- [ ] Monitor toast notification frequency
- [ ] Gather user feedback
- [ ] Track Lighthouse scores over time

---

## Troubleshooting

### Common Issues

**Issue: Font size too small on mobile**
```css
/* Ensure base font is 16px */
body {
  font-size: 16px; /* Not 14px! */
}
```

**Issue: iOS zoom on input focus**
```css
input, textarea {
  font-size: 16px; /* Must be ≥ 16px */
}
```

**Issue: Bottom nav covers content**
```css
.requests-page {
  padding-bottom: var(--bottom-nav-height);
}
```

**Issue: Sticky header not working**
```css
.page-header {
  position: sticky; /* Not fixed! */
  top: 0;
  z-index: 100;
}
```

**Issue: FAB button not clickable**
```css
.fab {
  z-index: 90; /* Must be below toasts (9999) but above content */
}
```

---

## Success Criteria

Stage 6 is complete when:

- ✅ All 6 stages committed
- ✅ All pytest tests passing
- ✅ Lighthouse score ≥ 90
- ✅ Tested on 3+ real devices
- ✅ No console errors
- ✅ All user flows work
- ✅ Documentation updated
- ✅ Production deployment successful

**Congratulations!** Jukebox now has a production-quality mobile UX! 🎉
