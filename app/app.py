#!/usr/bin/env python3
# Jukebox – Lidarr Request Portal app.py v0.1.0 – Last updated: 2025-11-23T12:00:00-05:00

"""
Jukebox – a simple web front end for requesting music via Lidarr.

Features:
- Per-user login (username/password)
- Simple HTML UI to submit requests (artist, optional album, note)
- SQLite-backed request log
- Forwards requests to Lidarr using API key and per-user root folders
"""

import os
import sqlite3
from contextlib import closing
from datetime import datetime

import requests
from flask import (
    Flask,
    request,
    render_template_string,
    redirect,
    url_for,
    session,
    flash,
    jsonify,
)
from werkzeug.security import generate_password_hash, check_password_hash

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

if not LIDARR_API_KEY:
    raise RuntimeError("LIDARR_API_KEY must be set for Jukebox to talk to Lidarr.")

app = Flask(__name__,
           static_folder='static',
           template_folder='templates')
app.config["SECRET_KEY"] = SECRET_KEY

_startup_done = False


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
        created_at      TEXT NOT NULL DEFAULT (datetime('now'))
    );

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
        cur = conn.execute("SELECT COUNT(*) AS c FROM users")
        row = cur.fetchone()
        user_count = row["c"] if row else 0
        if user_count == 0:
            conn.execute(
                "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)",
                ("admin", generate_password_hash("admin"), 1),
            )
            conn.commit()
            app.logger.warning(
                "Jukebox: created default admin user 'admin' with password 'admin'. Change this ASAP."
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

    return render_template_string(
        """
        <h1>Jukebox Login</h1>
        <form method="POST">
          <label>Username:</label><br>
          <input name="username" /><br>
          <label>Password:</label><br>
          <input name="password" type="password" /><br><br>
          <button type="submit">Login</button>
        </form>
        """
    )


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

    return render_template_string(
        """
        <h1>Create User</h1>
        <form method="POST">
          <label>Username:</label><br>
          <input name="username" /><br><br>
          <label>Password:</label><br>
          <input name="password" type="password" /><br><br>
          <label>Is Admin?</label>
          <input type="checkbox" name="is_admin" /><br><br>
          <button type="submit">Create</button>
        </form>
        <p><a href="{{ url_for('list_requests') }}">Back to requests</a></p>
        """
    )


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

    return render_template_string(
        """
        <h1>Jukebox – Your Requests</h1>
        <p>Logged in as: {{ user.username }}</p>
        <form method="POST" action="{{ url_for('logout') }}">
          <button type="submit">Logout</button>
        </form>
        <p><a href="{{ url_for('new_request') }}">New Request</a></p>
        {% if user.is_admin %}
        <p><a href="{{ url_for('create_user') }}">Create User</a></p>
        {% endif %}
        <table border="1" cellspacing="0" cellpadding="4">
          <tr>
            <th>ID</th><th>User</th><th>Artist</th><th>Album</th>
            <th>Status</th><th>Created</th><th>Updated</th><th>Note</th>
          </tr>
          {% for r in rows %}
          <tr>
            <td>{{ r.id }}</td>
            <td>{{ r.username }}</td>
            <td>{{ r.artist_name }}</td>
            <td>{{ r.album_title or '' }}</td>
            <td>{{ r.status }}</td>
            <td>{{ r.created_at }}</td>
            <td>{{ r.updated_at }}</td>
            <td>{{ r.note or '' }}</td>
          </tr>
          {% endfor %}
        </table>
        """,
        user=user,
        rows=rows,
    )


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

    return render_template_string(
        """
        <h1>Jukebox – New Request</h1>
        <form method="POST">
          <label>Artist Name (required):</label><br>
          <input name="artist_name" size="40" /><br><br>
          <label>Album Title (optional):</label><br>
          <input name="album_title" size="40" /><br><br>
          <label>Note (optional):</label><br>
          <textarea name="note" rows="3" cols="40"></textarea><br><br>
          <button type="submit">Submit Request</button>
        </form>
        """
    )


# --- JSON API for Postman / programmatic use ----------------------------------------


@app.route("/api/health", methods=["GET"])
def api_health():
    return jsonify({"status": "ok", "app": "Jukebox"})


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
                "ORDER BY r.created_at DESC"
            )
        else:
            cur = conn.execute(
                "SELECT r.*, u.username FROM requests r JOIN users u ON r.user_id = u.id "
                "WHERE r.user_id = ? ORDER BY r.created_at DESC",
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
                datetime.utcnow().isoformat(),
                datetime.utcnow().isoformat(),
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
            (status, lidarr_artist_id, last_error, datetime.utcnow().isoformat(), req_id),
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


# --- Main ---------------------------------------------------------------------------

if __name__ == "__main__":
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    startup()
    app.run(host="0.0.0.0", port=5000, debug=False)
