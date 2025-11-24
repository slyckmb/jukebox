# Jukebox - Music Request Portal

**Version**: 0.4.0-dev
**Status**: Active Development 🚧

A simple, elegant music request portal with Lidarr integration. Built with Flask, designed mobile-first, secured with Cloudflare Zero Trust Access. Users request one album at a time with duplicate detection and user-friendly error handling.

---

## Features

- ✅ **User Authentication** - Per-user accounts with password management
- ✅ **Music Requests** - Submit album requests (one at a time, required)
- ✅ **Lidarr Integration** - Automatic artist lookup and library management
- ✅ **Duplicate Detection** - Check if artist already exists before adding (v0.4.0)
- ✅ **Error Handling** - User-friendly error messages instead of technical JSON (v0.4.0)
- ✅ **Media Server Links** - Direct links to Plex/Jellyfin/Navidrome for existing music
- ✅ **Mobile-First UI** - Responsive design optimized for phones and tablets
- ✅ **Security Enhanced** - Cloudflare Zero Trust Access with MFA
- ✅ **Request Tracking** - Monitor request status (new, submitted, failed, existing)

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.12+ (for local development)
- Lidarr instance with API access
- Cloudflare tunnel (optional, for production)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/slyckmb/jukebox.git
   cd jukebox
   ```

2. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings:
   # - LIDARR_URL
   # - LIDARR_API_KEY (store in secrets file)
   # - FLASK_SECRET_KEY (store in secrets file)
   ```

3. **Set up secrets** (recommended for production):
   ```bash
   mkdir -p /mnt/config/secrets/jukebox
   echo "your-flask-secret-key" > /mnt/config/secrets/jukebox/flask-secret
   echo "your-lidarr-api-key" > /mnt/config/secrets/bash/bash_lidarr-api-key.env
   ```

4. **Build and run**:
   ```bash
   # Build Docker image (offline mode supported)
   DOCKER_BUILDKIT=0 docker compose build jukebox

   # Start the service
   docker compose up -d jukebox

   # View logs
   docker compose logs -f jukebox
   ```

5. **Access the application**:
   - Local: http://localhost:5000
   - Production: https://your-domain.com (via Cloudflare tunnel)

6. **Default credentials** (change immediately!):
   - Username: `admin`
   - Password: `admin`
   - Go to "Change Password" after first login

---

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `LIDARR_URL` | Lidarr API base URL | `http://lidarr:8686/api/v1` | Yes |
| `LIDARR_API_KEY` | Lidarr API key | - | Yes |
| `FLASK_SECRET_KEY` | Flask session secret | `CHANGE_ME_IN_PROD_JUKEBOX` | Yes |
| `LIDARR_QUALITY_PROFILE_ID` | Quality profile ID | `1` | No |
| `LIDARR_METADATA_PROFILE_ID` | Metadata profile ID | `1` | No |
| `MUSIC_ROOT_BASE` | Base path for music folders | `/data/media/music` | No |
| `DB_PATH` | SQLite database path | `/app/data/requests.db` | No |

### Secrets Management

For security, use file-based secrets with `_FILE` suffix:

```bash
# Instead of FLASK_SECRET_KEY=value
FLASK_SECRET_KEY_FILE=/mnt/config/secrets/jukebox/flask-secret

# Instead of LIDARR_API_KEY=value
LIDARR_API_KEY_FILE=/mnt/config/secrets/bash/bash_lidarr-api-key.env
```

See `docs/SECRETS.md` for details.

### Cloudflare Zero Trust Access (Optional)

For production deployments, configure OAuth + MFA protection:

1. Follow the guide: `docs/CLOUDFLARE-ACCESS-SETUP.md`
2. Configure email whitelist via dashboard or automation script
3. Enforce MFA and geographic restrictions

---

## Architecture

### Tech Stack

- **Backend**: Flask 3.1.2, Python 3.12
- **Database**: SQLite (file-based, volume-mounted)
- **Frontend**: Vanilla HTML/CSS/JS (no frameworks)
- **Styling**: CSS Variables, mobile-first responsive
- **Container**: Docker with offline build support
- **Security**: Cloudflare Zero Trust Access, MFA, scrypt password hashing

### File Structure

```
jukebox/
├── app/
│   ├── app.py                    # Flask application
│   ├── templates/                # Jinja2 templates
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── requests.html
│   │   ├── new_request.html
│   │   ├── change_password.html
│   │   ├── create_user.html
│   │   └── components/           # Reusable components
│   └── static/                   # CSS, JS, assets
│       ├── css/
│       │   ├── base.css
│       │   └── components.css
│       └── js/
│           └── app.js
├── db/
│   └── migrations/               # Database migrations
├── docker/
│   └── Dockerfile                # Container definition
├── tests/
│   └── test_app.py              # Pytest test suite
├── vendor/                       # Vendored Python wheels (offline build)
├── docs/                         # Documentation
├── docker-compose.yml
├── .env                          # Environment configuration
└── README.md                     # This file
```

---

## Development

### Local Development (Without Docker)

1. **Create virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables**:
   ```bash
   export LIDARR_URL="http://localhost:8686/api/v1"
   export LIDARR_API_KEY="your-api-key"
   export FLASK_SECRET_KEY="dev-secret-key"
   export DB_PATH="./data/requests.db"
   ```

4. **Run the application**:
   ```bash
   python app/app.py
   ```

5. **Access**: http://localhost:5000

### Running Tests

```bash
# Activate virtual environment
source .venv/bin/activate

# Run pytest
python -m pytest tests/test_app.py -v

# With coverage
python -m pytest tests/test_app.py -v --cov=app --cov-report=html
```

### Code Validation

```bash
# Python syntax check
python3 -m py_compile app/app.py

# JavaScript syntax check
node -c app/static/js/app.js
```

---

## Common Operations

### View Requests

```bash
sqlite3 data/requests.db 'SELECT id, artist_name, status, last_error FROM requests ORDER BY id DESC LIMIT 10;'
```

### View Users

```bash
sqlite3 data/requests.db 'SELECT id, username, email, is_admin FROM users;'
```

### Reset Admin Password

```bash
# Enter SQLite shell
sqlite3 data/requests.db

# Generate new hash (use Python)
python3 -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('new-password'))"

# Update admin password (replace HASH with output above)
UPDATE users SET password_hash = 'HASH' WHERE username = 'admin';
```

### Backup Database

```bash
# Stop container
docker compose stop jukebox

# Backup database
cp data/requests.db data/requests.db.backup-$(date +%Y%m%d)

# Restart container
docker compose up -d jukebox
```

---

## Roadmap

### v0.3.0 (Current) ✅
- Security enhancements (Cloudflare Access, MFA)
- Password change functionality
- Email-based user management
- Security audit (23/23 controls passed)

### v0.4.0 (In Progress)
- User-friendly error messages
- Duplicate artist/album detection
- Lidarr status polling & sync
- Search & filter requests
- Request details modal
- Bulk actions (admin)

### v0.5.0 (Future)
- PWA features (offline support, install prompt)
- Push notifications
- Request history/archive
- Advanced filters (date range, tags)
- Performance optimizations

---

## Documentation

- **[HANDOFF-JUKEBOX.md](docs/HANDOFF-JUKEBOX.md)** - Current status and operations guide
- **[SECURITY-AUDIT-REPORT.md](docs/SECURITY-AUDIT-REPORT.md)** - Security audit results (v0.3.0)
- **[SECURITY-ENHANCEMENT-PLAN.md](docs/SECURITY-ENHANCEMENT-PLAN.md)** - Security recommendations
- **[CLOUDFLARE-ACCESS-SETUP.md](docs/CLOUDFLARE-ACCESS-SETUP.md)** - OAuth setup guide
- **[MOBILE-UX-PROGRESS.md](docs/MOBILE-UX-PROGRESS.md)** - Mobile UX implementation tracking
- **[FEATURE-PLAN-V0.4.0-REVISED.md](docs/FEATURE-PLAN-V0.4.0-REVISED.md)** - Feature roadmap

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Support

- **Issues**: https://github.com/slyckmb/jukebox/issues
- **Discussions**: https://github.com/slyckmb/jukebox/discussions

---

## Acknowledgments

Built with ❤️ by Michael
Powered by Flask, Lidarr, and Cloudflare

---

**Live Demo**: https://jukebox.bikejeepyoga.com
