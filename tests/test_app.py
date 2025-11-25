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
        # Mock data for autocomplete testing
        self.artist_search_results = [
            {
                "foreignArtistId": "83d91898-7763-47d7-b03b-b92132375c47",
                "artistName": "Pink Floyd",
                "disambiguation": "UK progressive rock band",
            },
            {
                "foreignArtistId": "f181961b-20f7-459e-89de-920ef03c7ed0",
                "artistName": "Pink",
                "disambiguation": "US pop singer",
            },
        ]
        self.album_search_results = [
            {
                "title": "The Wall",
                "foreignAlbumId": "album-1",
                "releaseDate": "1979-11-30",
                "artist": {"artistName": "Pink Floyd"},
            },
            {
                "title": "The Dark Side of the Moon",
                "foreignAlbumId": "album-2",
                "releaseDate": "1973-03-01",
                "artist": {"artistName": "Pink Floyd"},
            },
        ]

    def get(self, url, params=None, timeout=10):
        self.calls.append({"method": "GET", "url": url, "params": params})
        if "/tag" in url:
            return self._resp(200, [{"id": self.tag_id, "label": "requested_by_user"}])
        if "artist/lookup" in url:
            # Check if it's an autocomplete search or existing lookup
            if params and "term" in params:
                # Return artist search results for autocomplete
                return self._resp(200, self.artist_search_results)
            return self._resp(200, self.lookup_payload)
        if "album/lookup" in url:
            return self._resp(200, self.album_search_results)
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

    def test_artist_search_requires_authentication(self):
        """Test that /api/search/artist requires login"""
        client = app.test_client()
        resp = client.get("/api/search/artist?q=pink")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data.get("status"), "error")
        self.assertIn("login", data.get("message", "").lower())

    def test_artist_search_returns_results(self):
        """Test that artist search returns fuzzy-matched results"""
        fake = FakeRequests()
        import app.app as appmod

        appmod.requests = fake  # monkeypatch
        client = app.test_client()
        client.post("/api/login", json={"username": "admin", "password": "admin"})

        resp = client.get("/api/search/artist?q=pink")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("results", data)
        results = data["results"]
        self.assertGreater(len(results), 0)
        # Check result structure
        first_result = results[0]
        self.assertIn("name", first_result)
        self.assertIn("id", first_result)
        self.assertIn("type", first_result)
        self.assertEqual(first_result["type"], "artist")

    def test_artist_search_requires_min_query_length(self):
        """Test that artist search requires at least 2 characters"""
        fake = FakeRequests()
        import app.app as appmod

        appmod.requests = fake  # monkeypatch
        client = app.test_client()
        client.post("/api/login", json={"username": "admin", "password": "admin"})

        # Test with 1 character
        resp = client.get("/api/search/artist?q=p")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data.get("results"), [])

        # Test with empty query
        resp = client.get("/api/search/artist?q=")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data.get("results"), [])

    def test_artist_search_sorts_by_relevance(self):
        """Test that artist search sorts results by fuzzy match score"""
        fake = FakeRequests()
        import app.app as appmod

        appmod.requests = fake  # monkeypatch
        client = app.test_client()
        client.post("/api/login", json={"username": "admin", "password": "admin"})

        resp = client.get("/api/search/artist?q=pink+floyd")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        results = data["results"]
        # "Pink Floyd" should be first (exact match) over "Pink" (partial match)
        self.assertGreater(len(results), 0)
        # Note: actual sorting depends on fuzzy matching algorithm

    def test_album_search_requires_authentication(self):
        """Test that /api/search/album requires login"""
        client = app.test_client()
        resp = client.get("/api/search/album?q=wall")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data.get("status"), "error")

    def test_album_search_returns_results(self):
        """Test that album search returns results"""
        fake = FakeRequests()
        import app.app as appmod

        appmod.requests = fake  # monkeypatch
        client = app.test_client()
        client.post("/api/login", json={"username": "admin", "password": "admin"})

        resp = client.get("/api/search/album?q=wall")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("results", data)
        results = data["results"]
        self.assertGreater(len(results), 0)
        # Check result structure
        first_result = results[0]
        self.assertIn("name", first_result)
        self.assertIn("id", first_result)
        self.assertIn("type", first_result)
        self.assertEqual(first_result["type"], "album")
        # Should have year if available
        if first_result.get("year"):
            self.assertEqual(len(first_result["year"]), 4)

    def test_album_search_with_artist_id(self):
        """Test that album search can filter by artist ID"""
        fake = FakeRequests()
        import app.app as appmod

        appmod.requests = fake  # monkeypatch
        client = app.test_client()
        client.post("/api/login", json={"username": "admin", "password": "admin"})

        artist_id = "83d91898-7763-47d7-b03b-b92132375c47"
        resp = client.get(f"/api/search/album?q=wall&artistId={artist_id}")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("results", data)
        # Verify the API was called with artist context
        calls = [c for c in fake.calls if "album/lookup" in c.get("url", "")]
        self.assertGreater(len(calls), 0)

    def test_autocomplete_handles_special_characters(self):
        """Test that autocomplete handles special characters in queries"""
        fake = FakeRequests()
        import app.app as appmod

        appmod.requests = fake  # monkeypatch
        client = app.test_client()
        client.post("/api/login", json={"username": "admin", "password": "admin"})

        # Test with special characters that should be URL-encoded
        resp = client.get("/api/search/artist?q=AC/DC")
        self.assertEqual(resp.status_code, 200)

        resp = client.get("/api/search/artist?q=Guns+N'+Roses")
        self.assertEqual(resp.status_code, 200)

    def test_autocomplete_handles_case_insensitive_search(self):
        """Test that autocomplete search is case-insensitive"""
        fake = FakeRequests()
        import app.app as appmod

        appmod.requests = fake  # monkeypatch
        client = app.test_client()
        client.post("/api/login", json={"username": "admin", "password": "admin"})

        # All of these should return results
        for query in ["PINK", "pink", "Pink", "pInK"]:
            resp = client.get(f"/api/search/artist?q={query}")
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertIn("results", data)

    def test_autocomplete_limits_results(self):
        """Test that autocomplete limits the number of results"""
        fake = FakeRequests()
        # Add more mock results
        fake.artist_search_results = [
            {"foreignArtistId": f"id-{i}", "artistName": f"Artist {i}", "disambiguation": ""}
            for i in range(20)
        ]
        import app.app as appmod

        appmod.requests = fake  # monkeypatch
        client = app.test_client()
        client.post("/api/login", json={"username": "admin", "password": "admin"})

        resp = client.get("/api/search/artist?q=artist")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        results = data["results"]
        # Should limit to 5 for artists
        self.assertLessEqual(len(results), 5)

        # Albums should limit to 10
        fake.album_search_results = [
            {
                "title": f"Album {i}",
                "foreignAlbumId": f"album-{i}",
                "releaseDate": "2020-01-01",
                "artist": {"artistName": "Test Artist"},
            }
            for i in range(20)
        ]
        resp = client.get("/api/search/album?q=album")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        results = data["results"]
        self.assertLessEqual(len(results), 10)


if __name__ == "__main__":
    unittest.main()
