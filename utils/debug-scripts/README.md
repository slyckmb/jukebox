# Debug Scripts

Temporary debugging/investigation scripts from various development sessions.

## Scripts

### check_albums.py
**Created**: v0.6.9 (2025-11-26)
**Purpose**: Investigate Caravan Palace album monitoring status
**Context**: BUG v0.6.8-1 - Albums becoming unmonitored after initial monitoring

Queries Lidarr API for Caravan Palace (artist ID 157) albums and displays:
- Album ID
- Title
- Monitored status (YES/NO)
- Track counts (downloaded/total)

**Usage**:
```bash
export LIDARR_API_KEY=your_api_key_here
python3 check_albums.py
```

**Outcome**: Helped identify that status sync was tracking artist-wide stats instead of per-album stats, leading to v0.6.9 fix.
