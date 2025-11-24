#!/usr/bin/env python3
"""
Test script for error_parser module.
Tests various error scenarios that might come from Lidarr API.
"""

import sys
sys.path.insert(0, 'app')

from error_parser import parse_lidarr_error, parse_artist_lookup_error, parse_tag_error


def test_json_validation_error():
    """Test parsing of JSON validation errors from Lidarr"""
    error = '{"type":"https://tools.ietf.org/html/rfc7231#section-6.5.1","title":"One or more validation errors occurred.","status":400,"traceId":"00-abc123","errors":{"rootFolderPath":["Invalid root folder"],"qualityProfileId":["Quality profile not found"]}}'
    result = parse_lidarr_error(error)
    print(f"✓ JSON validation error: {result}")
    assert "Invalid root folder" in result or "Quality profile not found" in result


def test_404_error():
    """Test 404 not found errors"""
    error = "Lidarr error 404: Not found"
    result = parse_lidarr_error(error)
    print(f"✓ 404 error: {result}")
    assert "not found" in result.lower()


def test_timeout_error():
    """Test timeout errors"""
    error = "Lidarr lookup failed: timeout exceeded after 10 seconds"
    result = parse_lidarr_error(error)
    print(f"✓ Timeout error: {result}")
    assert "timeout" in result.lower() or "timed out" in result.lower()


def test_connection_error():
    """Test connection errors"""
    error = "Lidarr request failed: Connection refused by host lidarr:8686"
    result = parse_lidarr_error(error)
    print(f"✓ Connection error: {result}")
    assert "cannot connect" in result.lower() or "connection" in result.lower()


def test_artist_already_exists():
    """Test duplicate artist errors"""
    error = "Lidarr error 400: Artist already exists in library"
    result = parse_lidarr_error(error)
    print(f"✓ Duplicate artist error: {result}")
    assert "already exists" in result.lower()


def test_server_error():
    """Test 500 server errors"""
    error = "Lidarr error 500: Internal server error - database timeout"
    result = parse_lidarr_error(error)
    print(f"✓ Server error: {result}")
    assert "server error" in result.lower() or "try again" in result.lower()


def test_artist_lookup_specific():
    """Test artist lookup specific parsing"""
    error = "No matching artist found in Lidarr"
    result = parse_artist_lookup_error(error)
    print(f"✓ Artist lookup error: {result}")
    assert "found" in result.lower() or "no artist" in result.lower()


def test_tag_error():
    """Test tag operation errors"""
    error = "Tag already exists with label: requested_by_mike"
    result = parse_tag_error(error)
    print(f"✓ Tag error: {result}")
    assert "already exists" in result.lower()


def test_long_error_truncation():
    """Test that very long errors are truncated"""
    error = "A" * 200 + " - This error is too long"
    result = parse_lidarr_error(error)
    print(f"✓ Long error truncation: {len(result)} chars (max 150)")
    assert len(result) <= 150
    assert result.endswith("...")


def test_empty_error():
    """Test handling of empty errors"""
    result = parse_lidarr_error("")
    print(f"✓ Empty error: {result}")
    assert result == "Unknown error occurred"


def test_none_error():
    """Test handling of None errors"""
    result = parse_lidarr_error(None)
    print(f"✓ None error: {result}")
    assert result == "Unknown error occurred"


def test_nested_colon_error():
    """Test extraction of meaningful part from colon-separated errors"""
    error = "Lidarr error 400: Bad request: Invalid artist ID: Artist not found in MusicBrainz"
    result = parse_lidarr_error(error)
    print(f"✓ Nested colon error: {result}")
    # Should extract meaningful part
    assert len(result) < len(error)


if __name__ == "__main__":
    print("Testing error_parser module...\n")

    tests = [
        test_json_validation_error,
        test_404_error,
        test_timeout_error,
        test_connection_error,
        test_artist_already_exists,
        test_server_error,
        test_artist_lookup_specific,
        test_tag_error,
        test_long_error_truncation,
        test_empty_error,
        test_none_error,
        test_nested_colon_error,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} ERROR: {e}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'='*60}")

    if failed > 0:
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
        sys.exit(0)
