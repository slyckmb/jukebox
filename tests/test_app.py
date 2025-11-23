import os
import tempfile
import unittest
from contextlib import closing
from typing import Any, Dict, List

os.environ.setdefault("LIDARR_API_KEY", "dummy-key")
os.environ.setdefault("FLASK_SECRET_KEY", "test-secret")

from app.app import (  # noqa: E402
    app,
    create_artist_in_lidarr,
    get_db,
)


class FakeRequests:
    def __init__(self):
        self.calls: List[Dict[str, Any]] = []
        self.lookup_payload = [
            {
                "foreignArtistId": "test-mbid",
                "artistName": "Test Artist",
            }
        ]
        self.tag_id = 42

    def get(self, url, params=None, timeout=10):
        self.calls.append({"method": "GET", "url": url, "params": params})
        if "/tag" in url:
            return self._resp(200, [{"id": self.tag_id, "label": "requested_by_user"}])
        if "artist/lookup" in url:
            return self._resp(200, self.lookup_payload)
        return self._resp(404, {})

    def post(self, url, json=None, timeout=10):
        self.calls.append({"method": "POST", "url": url, "json": json})
        return self._resp(201, {"id": 123})

    @staticmethod
    def _resp(status, payload):
        class R:
            def __init__(self, status, payload):
                self.status_code = status
                self._payload = payload
                self.text = str(payload)

            def json(self):
                return self._payload

        return R(status, payload)


class AppTests(unittest.TestCase):
    def setUp(self):
        fd, path = tempfile.mkstemp(prefix="jukebox-test-db-", suffix=".db")
        os.close(fd)
        os.environ["DB_PATH"] = path
        import app.app as appmod

        appmod.DB_PATH = path  # ensure the module-level path follows the test DB
        with closing(appmod.get_db()) as conn:
            conn.execute("SELECT 1")

    def test_create_artist_payload_includes_foreign_id_and_tag_id(self):
        fake = FakeRequests()
        import app.app as appmod

        appmod.requests = fake  # monkeypatch
        data, err = create_artist_in_lidarr("user", "Artist X")
        self.assertIsNone(err)
        self.assertTrue(any(c["method"] == "GET" and "/artist/lookup" in c["url"] for c in fake.calls))
        post_calls = [c for c in fake.calls if c["method"] == "POST" and "/artist" in c["url"]]
        self.assertEqual(len(post_calls), 1)
        payload = post_calls[0]["json"]
        self.assertEqual(payload["foreignArtistId"], "test-mbid")
        self.assertIn(fake.tag_id, payload["tags"])
        self.assertEqual(payload["artistName"], "Test Artist")
        self.assertEqual(payload["path"], "/data/media/music/lidarr_user/Test Artist")

    def test_api_flow_creates_and_lists_requests(self):
        fake = FakeRequests()
        import app.app as appmod

        appmod.requests = fake  # monkeypatch
        client = app.test_client()
        client.get("/api/health")
        client.post("/api/login", json={"username": "admin", "password": "admin"})
        resp = client.post(
            "/api/requests",
            json={"artist_name": "Artist X", "album_title": "", "note": "n"},
        )
        self.assertEqual(resp.status_code, 200)
        req = resp.get_json()
        self.assertEqual(req["status"], "submitted")
        list_resp = client.get("/api/requests")
        self.assertEqual(list_resp.status_code, 200)
        self.assertGreaterEqual(len(list_resp.get_json()), 1)


if __name__ == "__main__":
    unittest.main()
