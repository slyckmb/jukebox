# Jukebox Secrets Wiring

Follow `global/docs/SECRETS_POLICY.md`: reuse existing secret files, don’t duplicate values.

- Config env (tracked): `./.env` — non-secret defaults. You can set `FLASK_SECRET_KEY_FILE` here to point to your vault file.
- Lidarr key: reuse `/mnt/config/secrets/bash/bash_lidarr-api-key.env` (already referenced in `docker-compose.yml`). **Do not copy this key anywhere else.**
- Flask secret: create a new vault env file (vault-managed) and let compose load it:
  ```bash
  mkdir -p /mnt/config/secrets/jukebox
  cat <<'EOF' >/mnt/config/secrets/jukebox/env
  FLASK_SECRET_KEY=change_me_jukebox_secret
  EOF
  ```
  If you prefer indirection, put the secret in `/mnt/config/secrets/jukebox/flask-secret.key` and set `FLASK_SECRET_KEY_FILE=/mnt/config/secrets/jukebox/flask-secret.key` in `/mnt/config/secrets/jukebox/env` or `.env`.

Compose mounts: `.env`, `/mnt/config/secrets/jukebox/env`, and `/mnt/config/secrets/bash/bash_lidarr-api-key.env`. The app reads `_FILE` indirection automatically. Then run `docker compose up -d jukebox`.
