#!/usr/bin/env python3
import requests
import os
import sys

lidarr_url = os.getenv("LIDARR_URL", "http://lidarr:8686/api/v1")
api_key = os.getenv("LIDARR_API_KEY")

if not api_key:
    print("ERROR: LIDARR_API_KEY not set")
    sys.exit(1)

# Get Caravan Palace albums (artist ID 157)
resp = requests.get(f"{lidarr_url}/album", params={"artistId": 157, "apikey": api_key}, timeout=10)

if resp.status_code != 200:
    print(f"Error: HTTP {resp.status_code}")
    sys.exit(1)

albums = resp.json()
print(f"Found {len(albums)} albums for Caravan Palace:")
print()
print("ID\tTitle\t\t\t\t\tMonitored\tTracks")
print("-" * 80)

for a in albums:
    title = a['title'][:40].ljust(40)
    monitored = "YES" if a.get('monitored', False) else "NO"
    stats = a.get('statistics', {})
    track_count = stats.get('trackCount', 0)
    track_file_count = stats.get('trackFileCount', 0)
    tracks = f"{track_file_count}/{track_count}"
    print(f"{a['id']}\t{title}\t{monitored}\t{tracks}")
