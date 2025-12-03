#!/usr/bin/env python3
# Jukebox – Lidarr Request Portal

"""
Jukebox – a simple web front end for requesting music via Lidarr.

Features:
- Per-user login (username/password)
- Simple HTML UI to submit requests (artist, optional album, note)
- SQLite-backed request log
- Forwards requests to Lidarr using API key and per-user root folders
"""

__version__ = "0.6.21"

import os
import sqlite3
from contextlib import closing
from datetime import datetime, UTC

import requests
from flask import (
    Flask,
    request,
    render_template,
    redirect,
    url_for,
    session,
    flash,
    jsonify,
)
from werkzeug.security import generate_password_hash, check_password_hash

# Import error parser for user-friendly error messages
from error_parser import parse_lidarr_error, parse_artist_lookup_error, parse_tag_error

# --- Configuration via environment ---------------------------------------------------


def _get_int_env(name: str, default: int) -> int:
    raw_value = os.environ.get(name)
    if raw_value in (None, ""):
        return default
    try:
        return int(raw_value)
    except ValueError:
        return default


def _get_secret_env(name: str, default: str = "") -> str:
    """Return env value, allowing optional *_FILE indirection to avoid duplication."""
    file_var = f"{name}_FILE"
    file_path = os.environ.get(file_var)
    if file_path:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except OSError:
            pass
    return os.environ.get(name, default)


LIDARR_URL = os.environ.get("LIDARR_URL", "http://lidarr:8686/api/v1")
LIDARR_API_KEY = _get_secret_env("LIDARR_API_KEY", "")
LIDARR_QUALITY_PROFILE_ID = _get_int_env("LIDARR_QUALITY_PROFILE_ID", 1)
LIDARR_METADATA_PROFILE_ID = _get_int_env("LIDARR_METADATA_PROFILE_ID", 1)
MUSIC_ROOT_BASE = os.environ.get("MUSIC_ROOT_BASE", "/data/media/music")
DB_PATH = os.environ.get("DB_PATH", "/app/data/requests.db")
SECRET_KEY = _get_secret_env("FLASK_SECRET_KEY", "CHANGE_ME_IN_PROD_JUKEBOX")

# Media server URLs (optional, for "Listen Now" links)
PLEX_URL = os.environ.get("PLEX_URL", "")
JELLYFIN_URL = os.environ.get("JELLYFIN_URL", "")
NAVIDROME_URL = os.environ.get("NAVIDROME_URL", "")

if not LIDARR_API_KEY:
    raise RuntimeError("LIDARR_API_KEY must be set for Jukebox to talk to Lidarr.")

app = Flask(__name__,
           static_folder='static',
           template_folder='templates')
app.config["SECRET_KEY"] = SECRET_KEY

_startup_done = False


# Make version available to all templates
@app.context_processor
def inject_version():
    return {"app_version": __version__}


# --- DB helpers ----------------------------------------------------------------------


def get_db():
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    schema = """
    CREATE TABLE IF NOT EXISTS users (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        username        TEXT NOT NULL UNIQUE,
        password_hash   TEXT NOT NULL,
        is_admin        INTEGER NOT NULL DEFAULT 0,
        email           TEXT,
        created_at      TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email) WHERE email IS NOT NULL;

    CREATE TABLE IF NOT EXISTS requests (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id             INTEGER NOT NULL,
        artist_name         TEXT NOT NULL,
        album_title         TEXT,
        note                TEXT,
        status              TEXT NOT NULL DEFAULT 'new',
        tag                 TEXT NOT NULL,
        root_folder_path    TEXT NOT NULL,
        lidarr_artist_id    INTEGER,
        lidarr_album_id     INTEGER,
        last_error          TEXT,
        created_at          TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at          TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    CREATE INDEX IF NOT EXISTS idx_requests_user_id ON requests(user_id);
    CREATE INDEX IF NOT EXISTS idx_requests_status ON requests(status);
    CREATE INDEX IF NOT EXISTS idx_requests_artist ON requests(artist_name);
    """
    with closing(get_db()) as conn:
        conn.executescript(schema)
        conn.commit()


def startup():
    global _startup_done
    if _startup_done:
        return
    init_db()
    # Auto-create an initial admin user if none exist
    with closing(get_db()) as conn:
        # Check if admin user exists
        cur = conn.execute("SELECT id FROM users WHERE username = 'admin'")
        admin_exists = cur.fetchone()

        if not admin_exists:
            # Create admin user with unique email
            conn.execute(
                "INSERT INTO users (username, password_hash, is_admin, email) VALUES (?, ?, ?, ?)",
                ("admin", generate_password_hash("admin"), 1, "admin@bikejeepyoga.com"),
            )
            conn.commit()
            app.logger.warning(
                "Jukebox: created default admin user 'admin' with password 'admin'. "
                "CHANGE THIS IMMEDIATELY via password change feature!"
            )
        else:
            # Check if admin is still using default password
            cur = conn.execute("SELECT password_hash FROM users WHERE username = 'admin'")
            row = cur.fetchone()
            if row and check_password_hash(row["password_hash"], "admin"):
                app.logger.error(
                    "SECURITY WARNING: Admin user still has default password 'admin'! "
                    "Change it immediately at /change-password"
                )
    _startup_done = True


@app.before_request
def ensure_startup():
    startup()


# --- Auth helpers --------------------------------------------------------------------


def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    with closing(get_db()) as conn:
        cur = conn.execute("SELECT * FROM users WHERE id = ?", (uid,))
        row = cur.fetchone()
        return row


def login_required(fn):
    from functools import wraps

    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user:
            if request.path.startswith("/api/"):
                return jsonify({"status": "error", "message": "login required"}), 401
            return redirect(url_for("login", next=request.path))
        return fn(*args, **kwargs)

    return wrapper


# --- Lidarr API integration ----------------------------------------------------------


def build_user_root_folder(username: str) -> str:
    """Derive a per-user root folder for new music, e.g. /data/media/music/lidarr_mike."""
    safe_username = username.replace(" ", "_").lower()
    return f"{MUSIC_ROOT_BASE}/lidarr_{safe_username}"


def build_user_tag(username: str) -> str:
    """Derive a per-user tag for Lidarr, e.g. requested_by_mike."""
    safe_username = username.replace(" ", "_").lower()
    return f"requested_by_{safe_username}"


def get_or_create_tag_id(tag: str):
    """Ensure Lidarr tag exists and return its ID."""
    list_url = f"{LIDARR_URL}/tag?apikey={LIDARR_API_KEY}"
    try:
        resp = requests.get(list_url, timeout=10)
        if resp.status_code == 200:
            for item in resp.json() or []:
                if item.get("label") == tag and "id" in item:
                    return item["id"], None
    except Exception as exc:
        return None, f"Lidarr tag lookup failed: {exc}"

    create_url = f"{LIDARR_URL}/tag?apikey={LIDARR_API_KEY}"
    try:
        resp = requests.post(create_url, json={"label": tag}, timeout=10)
    except Exception as exc:
        return None, f"Lidarr tag create failed: {exc}"

    if resp.status_code in (200, 201):
        try:
            data = resp.json()
            if "id" in data:
                return data["id"], None
        except Exception:
            pass
        return None, "Lidarr tag create returned no id"

    return None, f"Lidarr tag create error {resp.status_code}: {resp.text}"


def lookup_artist(artist_name: str):
    """Lookup artist in Lidarr to obtain foreignArtistId and cleaned name."""
    url = f"{LIDARR_URL}/artist/lookup"
    try:
        resp = requests.get(url, params={"term": artist_name, "apikey": LIDARR_API_KEY}, timeout=10)
    except Exception as exc:
        return None, f"Lidarr lookup failed: {exc}"
    if resp.status_code != 200:
        return None, f"Lidarr lookup error {resp.status_code}: {resp.text}"
    try:
        data = resp.json() or []
    except Exception as exc:
        return None, f"Lidarr lookup parse failed: {exc}"
    if not data:
        return None, "No matching artist found in Lidarr"
    return data[0], None


def check_artist_exists_in_lidarr(foreign_artist_id: str):
    """
    Check if artist already exists in Lidarr library.

    Args:
        foreign_artist_id: MusicBrainz artist ID (e.g., "5b11f4ce-a62d-471e-81fc-a69a8278c7da")

    Returns:
        (exists: bool, artist_data: dict, error: str)
    """
    url = f"{LIDARR_URL}/artist"
    try:
        resp = requests.get(url, params={"apikey": LIDARR_API_KEY}, timeout=10)
    except Exception as exc:
        return False, None, f"Connection error: {exc}"

    if resp.status_code != 200:
        return False, None, f"Lidarr API error {resp.status_code}"

    try:
        artists = resp.json()
        for artist in artists:
            if artist.get("foreignArtistId") == foreign_artist_id:
                return True, artist, None
        return False, None, None
    except Exception as exc:
        return False, None, f"Parse error: {exc}"


def sync_request_status(request_id: int) -> bool:
    """
    Sync request status with Lidarr (ALBUM-SPECIFIC).
    Returns True if status changed, False otherwise.

    v0.6.9: Now tracks individual album progress instead of artist-wide statistics.

    Status Transitions:
    - submitted → downloading (album monitored, tracks downloading)
    - downloading → completed (all tracks for THIS album downloaded)
    """
    with closing(get_db()) as conn:
        req = conn.execute(
            "SELECT id, lidarr_artist_id, lidarr_album_id, status FROM requests WHERE id = ?",
            (request_id,)
        ).fetchone()

        if not req:
            return False

        # Only sync active statuses
        if req["status"] not in ["submitted", "downloading"]:
            return False

        lidarr_artist_id = req["lidarr_artist_id"]
        lidarr_album_id = req["lidarr_album_id"]

        if not lidarr_artist_id:
            return False

        try:
            # v0.6.9: NEW - Query the SPECIFIC album instead of all artist albums
            if lidarr_album_id:
                # Get album-specific data
                album_url = f"{LIDARR_URL}/album/{lidarr_album_id}"
                album_resp = requests.get(album_url, params={"apikey": LIDARR_API_KEY}, timeout=10)

                if album_resp.status_code == 200:
                    album_data = album_resp.json()

                    # Check THIS album's monitoring status
                    album_monitored = album_data.get("monitored", False)

                    # Get THIS album's track statistics
                    album_stats = album_data.get("statistics", {})
                    album_total_tracks = album_stats.get("trackCount", 0)
                    album_downloaded_tracks = album_stats.get("trackFileCount", 0)

                    # v0.6.9 Phase 2: DEFENSIVE MONITORING VERIFICATION
                    # If album is NOT monitored but download is incomplete, re-enable monitoring
                    if not album_monitored and album_downloaded_tracks < album_total_tracks and album_total_tracks > 0:
                        app.logger.warning(
                            f"⚠️  Album {lidarr_album_id} for request {request_id} became unmonitored! "
                            f"Re-enabling monitoring (defensive fix for bug v0.6.8-1)"
                        )
                        # Try to re-enable monitoring
                        remonitor_success, remonitor_err = set_album_monitored(lidarr_album_id, monitored=True)
                        if remonitor_success:
                            app.logger.info(f"✓ Successfully re-enabled monitoring for album {lidarr_album_id}")
                            album_monitored = True  # Update local variable
                            # Trigger search again
                            trigger_album_search(lidarr_album_id)
                        else:
                            app.logger.error(f"✗ Failed to re-enable monitoring for album {lidarr_album_id}: {remonitor_err}")

                    # Determine status based on THIS album only
                    old_status = req["status"]
                    new_status = old_status

                    if not album_monitored and album_downloaded_tracks == 0:
                        new_status = "submitted"
                    elif album_monitored and album_downloaded_tracks == 0:
                        new_status = "submitted"  # Still searching
                    elif album_downloaded_tracks > 0 and album_downloaded_tracks < album_total_tracks:
                        new_status = "downloading"
                    elif album_downloaded_tracks == album_total_tracks and album_total_tracks > 0:
                        new_status = "completed"

                    app.logger.info(
                        f"Request {request_id}: {old_status} → {new_status} "
                        f"(album {lidarr_album_id}: {album_downloaded_tracks}/{album_total_tracks} tracks, "
                        f"monitored={album_monitored})"
                    )

                    # Update database with album-specific data
                    now = datetime.now(UTC).isoformat()
                    conn.execute(
                        """UPDATE requests
                           SET status = ?,
                               album_total_tracks = ?,
                               album_downloaded_tracks = ?,
                               album_monitored = ?,
                               last_sync_at = ?,
                               updated_at = ?
                           WHERE id = ?""",
                        (new_status, album_total_tracks, album_downloaded_tracks,
                         album_monitored, now, now, request_id)
                    )
                    conn.commit()

                    if new_status != old_status:
                        app.logger.info(f"✓ Request {request_id} status changed: {old_status} → {new_status}")

                    return new_status != old_status
                elif album_resp.status_code == 404:
                    # v0.6.12: BUG FIX - Stale album ID in database
                    # Album no longer exists in Lidarr (deleted or never existed)
                    app.logger.error(
                        f"[STALE ALBUM] Album {lidarr_album_id} not found in Lidarr for request {request_id}. "
                        f"Marking request as failed."
                    )
                    now = datetime.now(UTC).isoformat()
                    error_msg = f"Album no longer exists in Lidarr (ID {lidarr_album_id}). Please submit a new request."
                    conn.execute(
                        """UPDATE requests
                           SET status = 'failed',
                               last_error = ?,
                               updated_at = ?
                           WHERE id = ?""",
                        (error_msg, now, request_id)
                    )
                    conn.commit()
                    app.logger.info(f"✓ Request {request_id} marked as failed due to stale album ID")
                    return True  # Status changed from submitted/downloading to failed
                else:
                    app.logger.warning(
                        f"Could not fetch album {lidarr_album_id} for request {request_id} "
                        f"(status code: {album_resp.status_code})"
                    )
                    return False

            # Fallback: If no album_id, use old artist-wide logic (backward compatibility)
            # Query Lidarr for artist status
            url = f"{LIDARR_URL}/artist/{lidarr_artist_id}"
            resp = requests.get(url, params={"apikey": LIDARR_API_KEY}, timeout=10)

            if resp.status_code != 200:
                return False

            artist_data = resp.json()

            # Check if artist is monitored
            is_monitored = artist_data.get("monitored", False)
            if not is_monitored:
                return False

            # Get album statistics (artist-wide)
            statistics = artist_data.get("statistics", {})
            total_albums = statistics.get("albumCount", 0)

            # Query albums to count downloaded
            albums_url = f"{LIDARR_URL}/album"
            albums_resp = requests.get(
                albums_url,
                params={"artistId": lidarr_artist_id, "apikey": LIDARR_API_KEY},
                timeout=10
            )

            downloaded_count = 0
            if albums_resp.status_code == 200:
                albums = albums_resp.json()
                for album in albums:
                    album_stats = album.get("statistics", {})
                    track_file_count = album_stats.get("trackFileCount", 0)
                    if track_file_count > 0:
                        downloaded_count += 1

            # Determine new status
            old_status = req["status"]
            new_status = old_status

            if downloaded_count == 0:
                new_status = "submitted"
            elif downloaded_count < total_albums:
                new_status = "downloading"
            else:
                new_status = "completed"

            app.logger.info(f"Request {request_id}: {old_status} → {new_status} ({downloaded_count}/{total_albums} albums)")

            # Update database with artist-wide data (legacy)
            now = datetime.now(UTC).isoformat()
            conn.execute(
                """UPDATE requests
                   SET status = ?,
                       total_albums = ?,
                       downloaded_albums = ?,
                       last_sync_at = ?,
                       updated_at = ?
                   WHERE id = ?""",
                (new_status, total_albums, downloaded_count, now, now, request_id)
            )
            conn.commit()

            if new_status != old_status:
                app.logger.info(f"✓ Request {request_id} status changed: {old_status} → {new_status}")

            return new_status != old_status

        except Exception as exc:
            app.logger.error(f"Error syncing request {request_id}: {exc}")
            return False


def sync_active_requests():
    """
    Sync all active requests (submitted, downloading).
    Called on page load.
    """
    with closing(get_db()) as conn:
        active = conn.execute(
            "SELECT id FROM requests WHERE status IN ('submitted', 'downloading')"
        ).fetchall()

    app.logger.info(f"Syncing {len(active)} active requests")
    changed_count = 0
    for req in active:
        if sync_request_status(req["id"]):
            changed_count += 1

    if changed_count > 0:
        app.logger.info(f"Sync complete: {changed_count} requests changed status")

    return changed_count


def create_artist_in_lidarr(username: str, artist_name: str):
    """
    Create/monitor an artist in Lidarr for a specific user.

    Returns (data, error):
      - data: parsed JSON from Lidarr on success
      - error: None on success, or an error string on failure
    """
    root_folder = build_user_root_folder(username)
    tag_label = build_user_tag(username)
    tag_id, tag_err = get_or_create_tag_id(tag_label)
    if tag_err:
        return None, tag_err

    artist_data, lookup_err = lookup_artist(artist_name)
    if lookup_err:
        return None, lookup_err

    foreign_id = artist_data.get("foreignArtistId")
    name = artist_data.get("artistName") or artist_name
    path = f"{root_folder}/{name}"

    payload = {
        "artistName": name,
        "monitored": True,
        "qualityProfileId": LIDARR_QUALITY_PROFILE_ID,
        "metadataProfileId": LIDARR_METADATA_PROFILE_ID,
        "rootFolderPath": root_folder,
        "tags": [tag_id] if tag_id is not None else [],
        "foreignArtistId": foreign_id,
        "addOptions": {"monitor": "all", "searchForMissingAlbums": True},
        "path": path,
    }

    url = f"{LIDARR_URL}/artist?apikey={LIDARR_API_KEY}"
    try:
        resp = requests.post(url, json=payload, timeout=10)
    except Exception as exc:  # network or similar
        return None, f"Lidarr request failed: {exc}"

    if resp.status_code in (200, 201):
        try:
            data = resp.json()
        except Exception:
            data = {}
        return data, None

    return None, f"Lidarr error {resp.status_code}: {resp.text}"


def find_album_in_artist(lidarr_artist_id: int, album_title: str):
    """
    Find a specific album in an artist's albums by title (fuzzy match).

    Returns:
        (album_data: dict, error: str)
    """
    from difflib import SequenceMatcher

    url = f"{LIDARR_URL}/album"
    try:
        resp = requests.get(
            url,
            params={"artistId": lidarr_artist_id, "apikey": LIDARR_API_KEY},
            timeout=10
        )
    except Exception as exc:
        return None, f"Connection error: {exc}"

    if resp.status_code != 200:
        return None, f"Lidarr API error {resp.status_code}"

    try:
        albums = resp.json()

        # Find best matching album by title
        best_match = None
        best_score = 0.0

        for album in albums:
            album_name = album.get("title", "").lower()
            score = SequenceMatcher(None, album_title.lower(), album_name).ratio()
            if score > best_score:
                best_score = score
                best_match = album

        # Require at least 60% match
        if best_match and best_score >= 0.6:
            return best_match, None

        return None, None  # Album not found

    except Exception as exc:
        return None, f"Parse error: {exc}"


def set_album_monitored(album_id: int, monitored: bool = True):
    """
    Update an album's monitored status in Lidarr.
    If setting to monitored=True, also triggers an album search.

    Returns:
        (success: bool, error: str)
    """
    # First, get the current album data
    url = f"{LIDARR_URL}/album/{album_id}"
    try:
        resp = requests.get(url, params={"apikey": LIDARR_API_KEY}, timeout=10)
    except Exception as exc:
        return False, f"Connection error: {exc}"

    if resp.status_code != 200:
        return False, f"Lidarr API error {resp.status_code}"

    try:
        album_data = resp.json()

        # Update the monitored flag
        album_data["monitored"] = monitored

        # Send PUT request to update
        put_url = f"{LIDARR_URL}/album/{album_id}?apikey={LIDARR_API_KEY}"
        put_resp = requests.put(put_url, json=album_data, timeout=10)

        if put_resp.status_code in (200, 202):
            # If we just set album to monitored, trigger a search immediately
            if monitored:
                trigger_album_search(album_id)
            return True, None

        return False, f"Update failed with status {put_resp.status_code}: {put_resp.text}"

    except Exception as exc:
        return False, f"Parse error: {exc}"


def trigger_album_search(album_id: int):
    """
    Trigger an album search in Lidarr to start download immediately.
    This is a fire-and-forget operation - errors are logged but not returned.
    """
    print(f"[ALBUM SEARCH TRIGGER] Called for album ID {album_id}", flush=True)
    app.logger.info(f"trigger_album_search called for album ID {album_id}")
    url = f"{LIDARR_URL}/command"
    payload = {
        "name": "AlbumSearch",
        "albumIds": [album_id]
    }

    try:
        print(f"[ALBUM SEARCH TRIGGER] Sending to Lidarr: {payload}", flush=True)
        app.logger.info(f"Sending AlbumSearch command to Lidarr: {payload}")
        resp = requests.post(url, json=payload, params={"apikey": LIDARR_API_KEY}, timeout=10)
        if resp.status_code in (201, 202):
            print(f"[ALBUM SEARCH TRIGGER] ✓ SUCCESS - Lidarr accepted search for album {album_id}", flush=True)
            app.logger.info(f"✓ AlbumSearch command accepted by Lidarr for album ID {album_id}")
        else:
            print(f"[ALBUM SEARCH TRIGGER] ✗ FAILED - HTTP {resp.status_code}: {resp.text}", flush=True)
            app.logger.warning(f"✗ AlbumSearch command rejected: HTTP {resp.status_code} - {resp.text}")
    except Exception as exc:
        print(f"[ALBUM SEARCH TRIGGER] ✗ EXCEPTION: {exc}", flush=True)
        app.logger.error(f"✗ Exception triggering AlbumSearch for album {album_id}: {exc}")


# --- Artist Staging Functions --------------------------------------------------------


# Configuration
STAGING_REFRESH_DAYS = int(os.getenv("STAGING_REFRESH_DAYS", "7"))


def create_artist_in_staging(artist_name: str, mb_artist_id: str, user_id: int):
    """
    Add artist to Lidarr staging area (admin space, unmonitored).

    Returns (lidarr_artist_id, error)
    """
    # Use admin root folder and staging tag
    root_folder = build_user_root_folder("admin")
    tag_label = "staging"
    tag_id, tag_err = get_or_create_tag_id(tag_label)
    if tag_err:
        return None, tag_err

    # Lookup artist in MusicBrainz
    artist_data, lookup_err = lookup_artist(artist_name)
    if lookup_err:
        return None, lookup_err

    foreign_id = artist_data.get("foreignArtistId")
    name = artist_data.get("artistName") or artist_name

    # BUG FIX 0.6.4-2: Make path unique by appending MB ID to prevent collisions
    # for artists with identical names (e.g., multiple "NF" artists)
    mb_id_suffix = mb_artist_id[:8] if mb_artist_id else ""
    path = f"{root_folder}/{name}-{mb_id_suffix}" if mb_id_suffix else f"{root_folder}/{name}"

    payload = {
        "artistName": name,
        "monitored": False,  # KEY: Not monitored in staging
        "qualityProfileId": LIDARR_QUALITY_PROFILE_ID,
        "metadataProfileId": LIDARR_METADATA_PROFILE_ID,
        "rootFolderPath": root_folder,
        "tags": [tag_id] if tag_id is not None else [],
        "foreignArtistId": foreign_id,
        "addOptions": {
            "monitor": "none",  # No albums monitored
            "searchForMissingAlbums": False  # Don't search
        },
        "path": path,
    }

    url = f"{LIDARR_URL}/artist?apikey={LIDARR_API_KEY}"
    try:
        resp = requests.post(url, json=payload, timeout=10)
    except Exception as exc:
        return None, f"Lidarr request failed: {exc}"

    if resp.status_code in (200, 201):
        try:
            data = resp.json()
            lidarr_artist_id = data.get("id")

            # Store in staging table
            with closing(get_db()) as conn:
                conn.execute(
                    """INSERT INTO artist_staging
                       (user_id, artist_name, lidarr_artist_id, mb_artist_id, created_at, last_refreshed_at, refresh_count)
                       VALUES (?, ?, ?, ?, ?, ?, 0)""",
                    (user_id, name, lidarr_artist_id, mb_artist_id,
                     datetime.now(UTC).isoformat(), datetime.now(UTC).isoformat())
                )
                conn.commit()

            app.logger.info(f"Created staging artist: {name} (Lidarr ID: {lidarr_artist_id})")
            return lidarr_artist_id, None
        except Exception as exc:
            return None, f"Failed to save staging record: {exc}"

    return None, f"Lidarr error {resp.status_code}: {resp.text}"


def find_staging_artist(mb_artist_id: str):
    """
    Check if artist exists in staging.

    Returns (staging_record, error)
    """
    try:
        with closing(get_db()) as conn:
            cur = conn.execute(
                "SELECT * FROM artist_staging WHERE mb_artist_id = ?",
                (mb_artist_id,)
            )
            row = cur.fetchone()
            return row, None
    except Exception as exc:
        return None, f"Database error: {exc}"


def trigger_artist_refresh(lidarr_artist_id: int):
    """
    Tell Lidarr to refresh artist metadata from MusicBrainz.

    Returns (success: bool, error)
    """
    url = f"{LIDARR_URL}/command"
    payload = {
        "name": "RefreshArtist",
        "artistId": lidarr_artist_id
    }

    try:
        resp = requests.post(url, json=payload, params={"apikey": LIDARR_API_KEY}, timeout=10)

        if resp.status_code in (201, 202):  # Command queued
            # Update timestamp in DB
            with closing(get_db()) as conn:
                conn.execute(
                    """UPDATE artist_staging
                       SET last_refreshed_at = ?, refresh_count = refresh_count + 1
                       WHERE lidarr_artist_id = ?""",
                    (datetime.now(UTC).isoformat(), lidarr_artist_id)
                )
                conn.commit()

            app.logger.info(f"Triggered RefreshArtist for Lidarr ID {lidarr_artist_id}")
            return True, None

        return False, f"Lidarr command failed: {resp.status_code}"
    except Exception as exc:
        return False, f"Refresh request failed: {exc}"


def get_artist_albums(lidarr_artist_id: int):
    """
    Get all albums for artist from Lidarr.

    Returns (albums: list, error)
    """
    url = f"{LIDARR_URL}/album"
    try:
        resp = requests.get(
            url,
            params={"artistId": lidarr_artist_id, "apikey": LIDARR_API_KEY},
            timeout=10
        )

        if resp.status_code == 200:
            albums = resp.json()
            # Return simplified album list
            result = []
            for album in albums:
                result.append({
                    "id": album.get("id"),
                    "title": album.get("title"),
                    "releaseDate": album.get("releaseDate"),
                    "monitored": album.get("monitored", False),
                    "statistics": album.get("statistics", {})
                })
            return result, None

        return None, f"Lidarr error {resp.status_code}"
    except Exception as exc:
        return None, f"Failed to get albums: {exc}"


def unmonitor_all_albums(lidarr_artist_id: int):
    """
    Set ALL albums for an artist to monitored=False.
    Used before moving artist to user to ensure only selected album is monitored.

    v0.6.9 Phase 3: Enhanced logging and verification to prevent bug v0.6.8-2

    Returns (success: bool, error)
    """
    try:
        # Get all albums for artist
        url = f"{LIDARR_URL}/album"
        resp = requests.get(
            url,
            params={"artistId": lidarr_artist_id, "apikey": LIDARR_API_KEY},
            timeout=10
        )

        if resp.status_code != 200:
            return False, f"Failed to get albums: {resp.status_code}"

        albums = resp.json()
        app.logger.info(f"[UNMONITOR] Starting: {len(albums)} albums for artist {lidarr_artist_id}")

        # v0.6.9: Log BEFORE state
        for album in albums:
            album_id = album.get("id")
            album_title = album.get("title", "Unknown")
            was_monitored = album.get("monitored", False)
            app.logger.info(f"  [BEFORE] Album {album_id} '{album_title}': monitored={was_monitored}")

        # Update each album to monitored=False
        failed_albums = []
        for album in albums:
            album["monitored"] = False
            album_id = album.get("id")
            album_title = album.get("title", "Unknown")

            put_url = f"{LIDARR_URL}/album/{album_id}?apikey={LIDARR_API_KEY}"
            put_resp = requests.put(put_url, json=album, timeout=10)

            if put_resp.status_code not in (200, 202):
                app.logger.warning(f"  [FAILED] Album {album_id} '{album_title}': {put_resp.status_code}")
                failed_albums.append((album_id, album_title))
            else:
                app.logger.info(f"  [UNMONITORED] Album {album_id} '{album_title}'")

        # v0.6.9: VERIFICATION - Re-query albums to confirm they're unmonitored
        app.logger.info(f"[UNMONITOR] Verifying all albums are actually unmonitored...")
        verify_resp = requests.get(
            url,
            params={"artistId": lidarr_artist_id, "apikey": LIDARR_API_KEY},
            timeout=10
        )

        if verify_resp.status_code == 200:
            verify_albums = verify_resp.json()
            still_monitored = []
            for album in verify_albums:
                album_id = album.get("id")
                album_title = album.get("title", "Unknown")
                is_monitored = album.get("monitored", False)
                if is_monitored:
                    still_monitored.append((album_id, album_title))
                    app.logger.warning(f"  [VERIFY FAILED] Album {album_id} '{album_title}' is STILL monitored!")

            if still_monitored:
                app.logger.error(
                    f"⚠️  {len(still_monitored)} albums remain monitored after unmonitor attempt: {still_monitored}"
                )
            else:
                app.logger.info(f"✓ Verification passed: All {len(verify_albums)} albums confirmed unmonitored")

        if failed_albums:
            app.logger.warning(f"[UNMONITOR] Completed with {len(failed_albums)} failures: {failed_albums}")
        else:
            app.logger.info(f"✓ [UNMONITOR] Successfully unmonitored all albums for artist {lidarr_artist_id}")

        return True, None

    except Exception as exc:
        app.logger.error(f"[UNMONITOR] Exception: {exc}")
        return False, f"Unmonitor failed: {exc}"


def move_artist_to_user(lidarr_artist_id: int, username: str):
    """
    Move artist from staging to user space.
    Updates rootFolderPath, path, and tags.

    Returns (success: bool, error)
    """
    # Get current artist data
    url = f"{LIDARR_URL}/artist/{lidarr_artist_id}"
    try:
        resp = requests.get(url, params={"apikey": LIDARR_API_KEY}, timeout=10)
    except Exception as exc:
        return False, f"Connection error: {exc}"

    if resp.status_code != 200:
        return False, f"Lidarr API error {resp.status_code}"

    try:
        artist_data = resp.json()

        # Update fields for user space
        user_root = build_user_root_folder(username)
        user_tag_label = build_user_tag(username)
        user_tag_id, tag_err = get_or_create_tag_id(user_tag_label)
        if tag_err:
            return False, tag_err

        artist_name = artist_data.get("artistName")
        artist_data["rootFolderPath"] = user_root
        artist_data["path"] = f"{user_root}/{artist_name}"
        artist_data["tags"] = [user_tag_id] if user_tag_id is not None else []

        # BUG FIX #6: Set artist to monitored when moving to user space
        artist_data["monitored"] = True

        # Send PUT request to update
        put_url = f"{LIDARR_URL}/artist/{lidarr_artist_id}?apikey={LIDARR_API_KEY}"
        put_resp = requests.put(put_url, json=artist_data, timeout=10)

        if put_resp.status_code in (200, 202):
            app.logger.info(f"Moved artist {artist_name} (ID {lidarr_artist_id}) to user {username} (monitored=True)")
            return True, None

        return False, f"Update failed with status {put_resp.status_code}: {put_resp.text}"

    except Exception as exc:
        return False, f"Move operation failed: {exc}"


# --- Routes --------------------------------------------------------------------------


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "app": "Jukebox"})


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


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("login"))


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


def _render_requests_page(user):
    # Sync active requests before displaying
    sync_active_requests()

    with closing(get_db()) as conn:
        if user["is_admin"]:
            cur = conn.execute(
                "SELECT r.*, u.username FROM requests r JOIN users u ON r.user_id = u.id "
                "WHERE r.status != 'deleted' "
                "ORDER BY r.created_at DESC"
            )
        else:
            cur = conn.execute(
                "SELECT r.*, u.username FROM requests r JOIN users u ON r.user_id = u.id "
                "WHERE r.user_id = ? AND r.status != 'deleted' "
                "ORDER BY r.created_at DESC",
                (user["id"],),
            )
        rows = cur.fetchall()

    # Pass media server URLs to template
    media_servers = {
        "plex": PLEX_URL,
        "jellyfin": JELLYFIN_URL,
        "navidrome": NAVIDROME_URL,
    }

    return render_template("requests.html", user=user, rows=rows, media_servers=media_servers)


@app.route("/", methods=["GET"])
@app.route("/requests", methods=["GET"])
@login_required
def list_requests():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    return _render_requests_page(user)


@app.route("/request/new", methods=["GET", "POST"])
@login_required
def new_request():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    if request.method == "POST":
        artist_name = request.form.get("artist_name", "").strip()
        album_title = request.form.get("album_title", "").strip()
        note = request.form.get("note", "").strip() or None

        if not artist_name:
            flash("Artist name is required.", "danger")
            return redirect(url_for("new_request"))

        if not album_title:
            flash("Album title is required. Please specify one album at a time.", "danger")
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
                    datetime.now(UTC).isoformat(),
                    datetime.now(UTC).isoformat(),
                ),
            )
            req_id = cur.lastrowid
            conn.commit()

        # First, lookup artist to get foreign ID
        artist_data, lookup_err = lookup_artist(artist_name)
        if lookup_err:
            # Artist not found in MusicBrainz - fail the request
            friendly_error = parse_artist_lookup_error(lookup_err)
            with closing(get_db()) as conn:
                conn.execute(
                    "UPDATE requests SET status = ?, last_error = ?, updated_at = ? WHERE id = ?",
                    ("failed", friendly_error, datetime.now(UTC).isoformat(), req_id),
                )
                conn.commit()
            flash(f"Artist lookup failed: {friendly_error}", "danger")
            return redirect(url_for("list_requests"))

        foreign_artist_id = artist_data.get("foreignArtistId")
        artist_display_name = artist_data.get("artistName", artist_name)

        # NEW: Check if artist exists in staging first
        staging_artist, staging_err = find_staging_artist(foreign_artist_id)

        app.logger.info(f"[STAGING] Checking for artist {artist_display_name} (MB ID: {foreign_artist_id}): found={staging_artist is not None}")

        if staging_artist:
            # Artist is in staging - move to user space
            lidarr_artist_id = staging_artist["lidarr_artist_id"]

            # v0.6.9 Phase 3: Verify artist still exists in Lidarr before proceeding
            verify_url = f"{LIDARR_URL}/artist/{lidarr_artist_id}"
            verify_resp = requests.get(verify_url, params={"apikey": LIDARR_API_KEY}, timeout=10)
            if verify_resp.status_code == 404:
                app.logger.error(
                    f"[STAGING] Artist {lidarr_artist_id} in staging but NOT in Lidarr (deleted?) - "
                    f"removing from staging"
                )
                with closing(get_db()) as conn:
                    conn.execute("DELETE FROM artist_staging WHERE lidarr_artist_id = ?", (lidarr_artist_id,))
                    conn.commit()
                # Fall through to create new artist
                staging_artist = None

        if staging_artist:
            app.logger.info(f"[STAGING] Using existing artist {lidarr_artist_id} from staging")

            # BUG FIX #7: Unmonitor all albums before moving (ensures only selected album gets monitored)
            app.logger.info(f"[STAGING] Unmonitoring all albums for artist {lidarr_artist_id} before move")
            unmonitor_success, unmonitor_err = unmonitor_all_albums(lidarr_artist_id)
            if not unmonitor_success:
                app.logger.warning(f"[STAGING] Failed to unmonitor albums: {unmonitor_err} - continuing anyway")

            success, move_err = move_artist_to_user(lidarr_artist_id, user["username"])

            if not success:
                # Failed to move artist from staging
                friendly_error = f"Failed to move artist from staging: {move_err}"
                with closing(get_db()) as conn:
                    conn.execute(
                        "UPDATE requests SET status = ?, last_error = ?, updated_at = ? WHERE id = ?",
                        ("failed", friendly_error, datetime.now(UTC).isoformat(), req_id),
                    )
                    conn.commit()
                flash(f"✗ {friendly_error}", "danger")
                return redirect(url_for("list_requests"))

            # BUG FIX 0.6.5-1: Remove artist from staging after successful move
            # This prevents subsequent album requests from re-triggering "unmonitor all"
            app.logger.info(f"Removing artist {lidarr_artist_id} from staging after successful move")
            with closing(get_db()) as conn:
                conn.execute("DELETE FROM artist_staging WHERE lidarr_artist_id = ?", (lidarr_artist_id,))
                conn.commit()

            # Successfully moved - now find and monitor the selected album ONLY
            album_data, album_err = find_album_in_artist(lidarr_artist_id, album_title)

            if album_err:
                # Error finding album
                app.logger.warning(f"Could not search for album after staging move: {album_err}")
                status_msg = f"Artist moved to your library, but could not find album '{album_title}'"
                with closing(get_db()) as conn:
                    conn.execute(
                        "UPDATE requests SET status = ?, lidarr_artist_id = ?, last_error = ?, updated_at = ? WHERE id = ?",
                        ("failed", lidarr_artist_id, status_msg, datetime.now(UTC).isoformat(), req_id),
                    )
                    conn.commit()
                flash(f"✗ {status_msg}", "warning")
                return redirect(url_for("list_requests"))

            if not album_data:
                # Album not found in artist's albums
                status_msg = f"Album '{album_title}' not found for {artist_display_name}. Check the album title."
                with closing(get_db()) as conn:
                    conn.execute(
                        "UPDATE requests SET status = ?, lidarr_artist_id = ?, last_error = ?, updated_at = ? WHERE id = ?",
                        ("failed", lidarr_artist_id, status_msg, datetime.now(UTC).isoformat(), req_id),
                    )
                    conn.commit()
                flash(f"✗ {status_msg}", "warning")
                return redirect(url_for("list_requests"))

            # Album found - set it to monitored
            album_id = album_data.get("id")
            is_monitored = album_data.get("monitored", False)

            if not is_monitored:
                app.logger.info(f"Setting album {album_id} ('{album_title}') to monitored")
                success, monitor_err = set_album_monitored(album_id, monitored=True)

                if success:
                    app.logger.info(f"Album {album_id} successfully set to monitored")
                    status_msg = f"'{album_title}' by {artist_display_name} is now being monitored!"
                    with closing(get_db()) as conn:
                        conn.execute(
                            "UPDATE requests SET status = ?, lidarr_artist_id = ?, lidarr_album_id = ?, last_error = ?, updated_at = ? WHERE id = ?",
                            ("submitted", lidarr_artist_id, album_id, None, datetime.now(UTC).isoformat(), req_id),
                        )
                        conn.commit()
                    flash(f"✓ {status_msg}", "success")
                    return redirect(url_for("list_requests"))
                else:
                    # Failed to update monitoring status
                    app.logger.error(f"Failed to set album monitored: {monitor_err}")
                    status_msg = f"Could not enable monitoring for '{album_title}'"
                    with closing(get_db()) as conn:
                        conn.execute(
                            "UPDATE requests SET status = ?, lidarr_artist_id = ?, lidarr_album_id = ?, last_error = ?, updated_at = ? WHERE id = ?",
                            ("failed", lidarr_artist_id, album_id, status_msg, datetime.now(UTC).isoformat(), req_id),
                        )
                        conn.commit()
                    flash(f"✗ {status_msg}", "danger")
                    return redirect(url_for("list_requests"))
            else:
                # Album is already monitored - check if it's available or just requested
                app.logger.info(f"Album {album_id} ('{album_title}') is already monitored, checking availability")
                statistics = album_data.get("statistics", {})
                track_count = statistics.get("trackCount", 0)

                app.logger.info(f"Album {album_id} statistics: trackCount={track_count}, statistics={statistics}")

                if track_count > 0:
                    # Album has tracks - it's available
                    status_msg = f"Album '{album_title}' is already available! (Artist: {artist_display_name})"
                else:
                    # Album is monitored but no tracks yet - still downloading/requested
                    status_msg = f"Album '{album_title}' is already requested and downloading! (Artist: {artist_display_name})"

                with closing(get_db()) as conn:
                    conn.execute(
                        "UPDATE requests SET status = ?, lidarr_artist_id = ?, lidarr_album_id = ?, last_error = ?, updated_at = ? WHERE id = ?",
                        ("existing", lidarr_artist_id, album_id, status_msg, datetime.now(UTC).isoformat(), req_id),
                    )
                    conn.commit()
                flash(f"✓ {status_msg}", "info")
                return redirect(url_for("list_requests"))

        # Check if artist already exists in Lidarr
        exists, existing_artist, check_error = check_artist_exists_in_lidarr(foreign_artist_id)

        if check_error:
            # Non-fatal: Log warning and continue with add attempt
            app.logger.warning(f"Could not check for existing artist: {check_error}")

        app.logger.info(f"Checking if artist {artist_display_name} exists in Lidarr: exists={exists}")

        if exists:
            # Artist already exists - check if the album is monitored
            lidarr_artist_id = existing_artist.get("id")

            # Try to find the requested album in the artist's albums
            album_data, album_err = find_album_in_artist(lidarr_artist_id, album_title)

            if album_err:
                # Error finding album - log and proceed with default behavior
                app.logger.warning(f"Could not search for album: {album_err}")
                status_msg = f"'{artist_display_name}' already exists in your library!"
                with closing(get_db()) as conn:
                    conn.execute(
                        "UPDATE requests SET status = ?, lidarr_artist_id = ?, last_error = ?, updated_at = ? WHERE id = ?",
                        ("existing", lidarr_artist_id, status_msg, datetime.now(UTC).isoformat(), req_id),
                    )
                    conn.commit()
                flash(f"✓ {status_msg}", "info")
                return redirect(url_for("list_requests"))

            if album_data:
                # Album exists - check if monitored
                album_id = album_data.get("id")
                is_monitored = album_data.get("monitored", False)

                if not is_monitored:
                    # Album exists but is unmonitored - flip it to monitored
                    app.logger.info(f"Existing artist path: Setting album {album_id} ('{album_title}') to monitored")
                    success, monitor_err = set_album_monitored(album_id, monitored=True)

                    if success:
                        app.logger.info(f"Existing artist path: Album {album_id} successfully set to monitored")
                        status_msg = f"'{album_title}' by {artist_display_name} is now being monitored!"
                        with closing(get_db()) as conn:
                            conn.execute(
                                "UPDATE requests SET status = ?, lidarr_artist_id = ?, lidarr_album_id = ?, last_error = ?, updated_at = ? WHERE id = ?",
                                ("submitted", lidarr_artist_id, album_id, None, datetime.now(UTC).isoformat(), req_id),
                            )
                            conn.commit()
                        flash(f"✓ {status_msg}", "success")
                        return redirect(url_for("list_requests"))
                    else:
                        # Failed to update monitoring status
                        app.logger.error(f"Failed to set album monitored: {monitor_err}")
                        status_msg = f"Could not enable monitoring for '{album_title}'"
                        with closing(get_db()) as conn:
                            conn.execute(
                                "UPDATE requests SET status = ?, last_error = ?, updated_at = ? WHERE id = ?",
                                ("failed", status_msg, datetime.now(UTC).isoformat(), req_id),
                            )
                            conn.commit()
                        flash(f"✗ {status_msg}", "danger")
                        return redirect(url_for("list_requests"))
                else:
                    # Album is already monitored - check if it's available or just requested
                    app.logger.info(f"Existing artist path: Album {album_id} ('{album_title}') is already monitored")
                    statistics = album_data.get("statistics", {})
                    track_count = statistics.get("trackCount", 0)

                    app.logger.info(f"Album {album_id} statistics: trackCount={track_count}")

                    if track_count > 0:
                        # Album has tracks - it's available
                        status_msg = f"Album '{album_title}' is already available! (Artist: {artist_display_name})"
                    else:
                        # Album is monitored but no tracks yet - still downloading/requested
                        status_msg = f"Album '{album_title}' is already requested and downloading! (Artist: {artist_display_name})"

                    with closing(get_db()) as conn:
                        conn.execute(
                            "UPDATE requests SET status = ?, lidarr_artist_id = ?, lidarr_album_id = ?, last_error = ?, updated_at = ? WHERE id = ?",
                            ("existing", lidarr_artist_id, album_id, status_msg, datetime.now(UTC).isoformat(), req_id),
                        )
                        conn.commit()
                    flash(f"✓ {status_msg}", "info")
                    return redirect(url_for("list_requests"))
            else:
                # Album not found in artist's albums - artist exists but album doesn't
                # This could be a new album or a typo - report as such
                status_msg = f"'{artist_display_name}' exists in your library, but album '{album_title}' was not found. Check the album title."
                with closing(get_db()) as conn:
                    conn.execute(
                        "UPDATE requests SET status = ?, lidarr_artist_id = ?, last_error = ?, updated_at = ? WHERE id = ?",
                        ("failed", lidarr_artist_id, status_msg, datetime.now(UTC).isoformat(), req_id),
                    )
                    conn.commit()
                flash(f"✗ {status_msg}", "warning")
                return redirect(url_for("list_requests"))

        # Artist doesn't exist - continue with normal add flow
        data, err = create_artist_in_lidarr(user["username"], artist_name)

        with closing(get_db()) as conn:
            if err:
                # Parse error for user-friendly message
                friendly_error = parse_lidarr_error(err)
                conn.execute(
                    "UPDATE requests SET status = ?, last_error = ?, updated_at = ? WHERE id = ?",
                    ("failed", friendly_error, datetime.now(UTC).isoformat(), req_id),
                )
                conn.commit()
                flash(f"Failed to send request to Lidarr: {friendly_error}", "danger")
            else:
                lidarr_artist_id = data.get("id") if data else None
                conn.execute(
                    """
                    UPDATE requests
                    SET status = ?, lidarr_artist_id = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    ("submitted", lidarr_artist_id, datetime.now(UTC).isoformat(), req_id),
                )
                conn.commit()
                flash("Request submitted to Lidarr.", "success")

        return redirect(url_for("list_requests"))

    return render_template("new_request.html")


# --- JSON API for Postman / programmatic use ----------------------------------------


@app.route("/api/health", methods=["GET"])
def api_health():
    return jsonify({"status": "ok", "app": "Jukebox"})


@app.route("/api/search/artist")
@login_required
def search_artist():
    """
    Fuzzy search for artists via Lidarr/MusicBrainz.
    Returns top 5 matches sorted by relevance.
    """
    from difflib import SequenceMatcher

    query = request.args.get("q", "").strip()

    if not query or len(query) < 2:
        return jsonify({"results": []})

    try:
        # Query Lidarr artist lookup (which queries MusicBrainz)
        url = f"{LIDARR_URL}/artist/lookup"
        params = {
            "term": query,
            "apikey": LIDARR_API_KEY
        }

        resp = requests.get(url, params=params, timeout=10)

        if resp.status_code != 200:
            app.logger.error(f"Lidarr artist search failed: {resp.status_code}")
            return jsonify({"results": []})

        data = resp.json()

        # Transform and score results
        results = []
        for item in data:
            artist_name = item.get("artistName", "")
            if not artist_name:
                continue

            # Calculate fuzzy match score
            score = SequenceMatcher(None, query.lower(), artist_name.lower()).ratio()

            results.append({
                "name": artist_name,
                "id": item.get("foreignArtistId", ""),
                "disambiguation": item.get("disambiguation", ""),
                "score": score,
                "type": "artist"
            })

        # Sort by score (highest first), then limit to top 5
        results.sort(key=lambda x: x["score"], reverse=True)
        results = results[:5]

        # Remove score from response (internal use only)
        for result in results:
            del result["score"]

        return jsonify({"results": results})

    except Exception as exc:
        app.logger.error(f"Artist search error: {exc}")
        return jsonify({"results": []})


@app.route("/api/search/album")
@login_required
def search_album():
    """
    Search for albums via Lidarr/MusicBrainz.
    Returns albums sorted by release date and relevance.
    """
    from difflib import SequenceMatcher

    query = request.args.get("q", "").strip()
    artist_id = request.args.get("artistId", "").strip()

    if not query or len(query) < 2:
        return jsonify({"results": []})

    try:
        # If we have artist ID, search within that artist's albums
        if artist_id:
            url = f"{LIDARR_URL}/album/lookup"
            params = {
                "term": f"lidarr:{artist_id}",  # Search by artist MusicBrainz ID
                "apikey": LIDARR_API_KEY
            }
        else:
            # Generic album search
            url = f"{LIDARR_URL}/album/lookup"
            params = {
                "term": query,
                "apikey": LIDARR_API_KEY
            }

        resp = requests.get(url, params=params, timeout=10)

        if resp.status_code != 200:
            app.logger.error(f"Lidarr album search failed: {resp.status_code}")
            return jsonify({"results": []})

        data = resp.json()

        # Transform results
        results = []
        for item in data:
            album_title = item.get("title", "")
            if not album_title:
                continue

            # Calculate fuzzy match score
            score = SequenceMatcher(None, query.lower(), album_title.lower()).ratio()

            # Extract year from releaseDate (YYYY-MM-DD)
            release_date = item.get("releaseDate", "")
            year = release_date[:4] if release_date else None

            # Get artist name from the album data
            artist_name = ""
            if "artist" in item and "artistName" in item["artist"]:
                artist_name = item["artist"]["artistName"]

            results.append({
                "name": album_title,
                "id": item.get("foreignAlbumId", ""),
                "disambiguation": artist_name,
                "year": year,
                "score": score,
                "type": "album"
            })

        # Sort by score (highest first), then limit to 10
        results.sort(key=lambda x: x["score"], reverse=True)

        # If artist-specific search returned no good matches (all scores < 0.4), try generic search
        if artist_id and (not results or results[0]["score"] < 0.4):
            app.logger.info(f"Artist-specific search found no good matches for '{query}', trying generic search")

            # Try generic album search as fallback
            generic_url = f"{LIDARR_URL}/album/lookup"
            generic_params = {
                "term": query,
                "apikey": LIDARR_API_KEY
            }

            generic_resp = requests.get(generic_url, params=generic_params, timeout=10)

            if generic_resp.status_code == 200:
                generic_data = generic_resp.json()

                # Add generic results (avoiding duplicates)
                existing_ids = {r["id"] for r in results}

                for item in generic_data:
                    album_id = item.get("foreignAlbumId", "")
                    if album_id in existing_ids:
                        continue

                    album_title = item.get("title", "")
                    if not album_title:
                        continue

                    # Calculate fuzzy match score
                    score = SequenceMatcher(None, query.lower(), album_title.lower()).ratio()

                    # Extract year from releaseDate (YYYY-MM-DD)
                    release_date = item.get("releaseDate", "")
                    year = release_date[:4] if release_date else None

                    # Get artist name from the album data
                    artist_name = ""
                    if "artist" in item and "artistName" in item["artist"]:
                        artist_name = item["artist"]["artistName"]

                    results.append({
                        "name": album_title,
                        "id": album_id,
                        "disambiguation": artist_name,
                        "year": year,
                        "score": score,
                        "type": "album"
                    })

                # Re-sort with combined results
                results.sort(key=lambda x: x["score"], reverse=True)

        results = results[:10]

        # Remove score from response
        for result in results:
            del result["score"]

        return jsonify({"results": results})

    except Exception as exc:
        app.logger.error(f"Album search error: {exc}")
        return jsonify({"results": []})


@app.route("/api/artist/pull-albums", methods=["POST"])
@login_required
def pull_albums_api():
    """
    Trigger album pull for artist (add to staging or reuse existing).
    Returns {status, lidarr_artist_id, message, state}
    """
    user = current_user()
    data = request.get_json(force=True, silent=True) or {}

    artist_name = (data.get("artist_name") or "").strip()
    mb_artist_id = (data.get("mb_artist_id") or "").strip()

    if not artist_name or not mb_artist_id:
        return jsonify({"status": "error", "message": "artist_name and mb_artist_id required"}), 400

    # Check if already in staging
    staging_artist, staging_err = find_staging_artist(mb_artist_id)

    if staging_err:
        app.logger.error(f"Error checking staging: {staging_err}")
        return jsonify({"status": "error", "message": staging_err}), 500

    if staging_artist:
        # Artist exists in staging - verify it still exists in Lidarr
        lidarr_artist_id = staging_artist["lidarr_artist_id"]

        # BUG FIX 0.6.4-1: Check if artist still exists in Lidarr before using cached entry
        try:
            url = f"{LIDARR_URL}/artist/{lidarr_artist_id}"
            resp = requests.get(url, params={"apikey": LIDARR_API_KEY}, timeout=10)

            if resp.status_code == 404:
                # Artist was deleted from Lidarr - clean up stale staging entry
                app.logger.warning(f"Staging artist {artist_name} (ID {lidarr_artist_id}) no longer exists in Lidarr - removing from staging")
                with closing(get_db()) as conn:
                    conn.execute("DELETE FROM artist_staging WHERE lidarr_artist_id = ?", (lidarr_artist_id,))
                    conn.commit()
                # Fall through to create new artist below
                staging_artist = None
            elif resp.status_code != 200:
                app.logger.error(f"Error checking artist existence: HTTP {resp.status_code}")
                return jsonify({"status": "error", "message": f"Lidarr error {resp.status_code}"}), 500
        except Exception as exc:
            app.logger.error(f"Exception checking artist existence: {exc}")
            return jsonify({"status": "error", "message": f"Failed to verify artist: {exc}"}), 500

        # If staging_artist is still valid, proceed with refresh logic
        if staging_artist:
            last_refresh = staging_artist["last_refreshed_at"]

            if last_refresh:
                last_refresh_dt = datetime.fromisoformat(last_refresh)
                days_old = (datetime.now(UTC) - last_refresh_dt).days
            else:
                days_old = 999

            if days_old > STAGING_REFRESH_DAYS:
                # Stale, trigger refresh
                success, refresh_err = trigger_artist_refresh(lidarr_artist_id)
                if not success:
                    app.logger.error(f"Refresh failed: {refresh_err}")

                return jsonify({
                    "status": "ok",
                    "lidarr_artist_id": lidarr_artist_id,
                    "state": "refreshing",
                    "message": f"Refreshing {artist_name} (last updated {days_old} days ago)"
                })
            else:
                # Fresh, use immediately
                return jsonify({
                    "status": "ok",
                    "lidarr_artist_id": lidarr_artist_id,
                    "state": "ready",
                    "message": f"Using cached {artist_name}"
                })

    # staging_artist is None (either not found or was deleted) - continue to creation
    if not staging_artist:
        # Not in staging - check if artist already exists in Lidarr
        exists, existing_artist, check_err = check_artist_exists_in_lidarr(mb_artist_id)

        if check_err:
            app.logger.warning(f"Error checking for existing artist: {check_err}")
            # Non-fatal - continue with creation attempt

        if exists and existing_artist:
            # Artist already exists in Lidarr (any root folder)
            lidarr_artist_id = existing_artist.get("id")
            app.logger.info(f"Artist {artist_name} already exists in Lidarr (ID: {lidarr_artist_id}), using existing")

            # Return as ready since artist and albums already exist
            return jsonify({
                "status": "ok",
                "lidarr_artist_id": lidarr_artist_id,
                "state": "ready",
                "message": f"Using existing {artist_name} from library"
            })

        # New artist, add to staging
        lidarr_artist_id, add_err = create_artist_in_staging(artist_name, mb_artist_id, user["id"])

        if add_err:
            app.logger.error(f"Failed to create staging artist: {add_err}")
            return jsonify({"status": "error", "message": add_err}), 500

        return jsonify({
            "status": "ok",
            "lidarr_artist_id": lidarr_artist_id,
            "state": "loading",
            "message": f"Loading albums for {artist_name}"
        })


@app.route("/api/artist/albums/<int:lidarr_id>", methods=["GET"])
@login_required
def get_albums_api(lidarr_id):
    """
    Get album list for artist (used for polling).
    Returns {albums: [...], ready: bool}
    """
    albums, err = get_artist_albums(lidarr_id)

    if err:
        return jsonify({"ready": False, "error": err}), 500

    # Consider ready if we have albums
    ready = len(albums) > 0

    return jsonify({
        "ready": ready,
        "albums": albums
    })


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(force=True, silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    with closing(get_db()) as conn:
        cur = conn.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cur.fetchone()

    if row and check_password_hash(row["password_hash"], password):
        session["user_id"] = row["id"]
        return jsonify({"status": "ok", "message": "logged in"})

    return (
        jsonify({"status": "error", "message": "invalid credentials"}),
        401,
    )


@app.route("/api/requests", methods=["GET"])
@login_required
def api_list_requests():
    user = current_user()
    with closing(get_db()) as conn:
        if user["is_admin"]:
            cur = conn.execute(
                "SELECT r.*, u.username FROM requests r JOIN users u ON r.user_id = u.id "
                "WHERE r.status != 'deleted' "
                "ORDER BY r.created_at DESC"
            )
        else:
            cur = conn.execute(
                "SELECT r.*, u.username FROM requests r JOIN users u ON r.user_id = u.id "
                "WHERE r.user_id = ? AND r.status != 'deleted' "
                "ORDER BY r.created_at DESC",
                (user["id"],),
            )
        rows = [dict(r) for r in cur.fetchall()]
    return jsonify(rows)


@app.route("/api/requests", methods=["POST"])
@login_required
def api_new_request():
    user = current_user()
    data = request.get_json(force=True, silent=True) or {}
    artist_name = (data.get("artist_name") or "").strip()
    album_title = (data.get("album_title") or "").strip() or None
    note = (data.get("note") or "").strip() or None

    if not artist_name:
        return (
            jsonify({"status": "error", "message": "artist_name is required"}),
            400,
        )

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
                datetime.now(UTC).isoformat(),
                datetime.now(UTC).isoformat(),
            ),
        )
        req_id = cur.lastrowid
        conn.commit()

    data_resp, err = create_artist_in_lidarr(user["username"], artist_name)

    status = "submitted"
    lidarr_artist_id = None
    last_error = None
    if err:
        status = "failed"
        last_error = err
    else:
        lidarr_artist_id = data_resp.get("id") if data_resp else None

    with closing(get_db()) as conn:
        conn.execute(
            """
            UPDATE requests
            SET status = ?, lidarr_artist_id = ?, last_error = ?, updated_at = ?
            WHERE id = ?
            """,
            (status, lidarr_artist_id, last_error, datetime.now(UTC).isoformat(), req_id),
        )
        conn.commit()

    return (
        jsonify(
            {
                "id": req_id,
                "status": status,
                "artist_name": artist_name,
                "album_title": album_title,
                "note": note,
                "tag": tag,
                "root_folder_path": root_folder,
                "lidarr_artist_id": lidarr_artist_id,
                "error": last_error,
            }
        ),
        200 if status == "submitted" else 500,
    )


@app.route("/api/requests/<int:req_id>", methods=["GET"])
@login_required
def api_get_request(req_id: int):
    user = current_user()
    with closing(get_db()) as conn:
        cur = conn.execute(
            """
            SELECT r.*, u.username
            FROM requests r
            JOIN users u ON r.user_id = u.id
            WHERE r.id = ?
            """,
            (req_id,),
        )
        row = cur.fetchone()
    if not row:
        return jsonify({"status": "error", "message": "not found"}), 404
    if not user["is_admin"] and row["user_id"] != user["id"]:
        return jsonify({"status": "error", "message": "forbidden"}), 403
    return jsonify(dict(row))


@app.route("/api/requests/<int:req_id>", methods=["DELETE"])
@login_required
def delete_request(req_id: int):
    """Soft-delete a request (sets status='deleted')."""
    user = current_user()
    with closing(get_db()) as conn:
        # Verify request exists and user owns it (or is admin)
        req = conn.execute(
            "SELECT user_id FROM requests WHERE id = ?",
            (req_id,)
        ).fetchone()

        if not req:
            return jsonify({"error": "Request not found"}), 404

        # Only owner or admin can delete
        if not user["is_admin"] and req["user_id"] != user["id"]:
            return jsonify({"error": "Forbidden"}), 403

        # Soft delete: set status to 'deleted'
        conn.execute(
            "UPDATE requests SET status = 'deleted', updated_at = ? WHERE id = ?",
            (datetime.now(UTC).isoformat(), req_id)
        )
        conn.commit()

    return jsonify({"success": True})


# --- Main ---------------------------------------------------------------------------

if __name__ == "__main__":
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    startup()
    app.run(host="0.0.0.0", port=5000, debug=False)


@app.route("/debug/urls", methods=["GET"])
@login_required
def debug_urls():
    """Debug endpoint to show generated URLs for testing."""
    user = current_user()
    if not user:
        return jsonify({"error": "Not authenticated"}), 401
    
    # Get a completed request for testing
    with closing(get_db()) as conn:
        req = conn.execute(
            "SELECT * FROM requests WHERE status = 'completed' LIMIT 1"
        ).fetchone()
    
    if not req:
        return jsonify({"error": "No completed requests found"}), 404
    
    from urllib.parse import quote
    artist_encoded = quote(req["artist_name"])
    album_encoded = quote(req["album_title"]) if req["album_title"] else None
    
    debug_info = {
        "request_id": req["id"],
        "artist_name": req["artist_name"],
        "album_title": req["album_title"],
        "artist_encoded": artist_encoded,
        "album_encoded": album_encoded,
        "media_servers": {
            "navidrome": NAVIDROME_URL,
            "jellyfin": JELLYFIN_URL,
            "plex": PLEX_URL,
        },
        "generated_urls": {
            "navidrome_header": f"{NAVIDROME_URL}/#!/search?query={artist_encoded}",
            "navidrome_button": f"{NAVIDROME_URL}/#!/search?query={artist_encoded}",
            "jellyfin": f"{JELLYFIN_URL}/#!/search?query={artist_encoded}",
            "plex": f"{PLEX_URL}/#!/search?query={artist_encoded}",
        },
        "test_instructions": "Open these URLs in your browser and see which ones work"
    }
    
    return jsonify(debug_info)
