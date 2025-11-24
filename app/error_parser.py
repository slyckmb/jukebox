"""
Error message parser for user-friendly error display.
Extracts meaningful information from Lidarr API errors.
"""
import re
import json


def parse_lidarr_error(error_message: str) -> str:
    """
    Parse Lidarr API error and return user-friendly message.

    Args:
        error_message: Raw error string from Lidarr API

    Returns:
        Clean, user-friendly error message (max 150 chars)
    """
    if not error_message:
        return "Unknown error occurred"

    # Try to extract JSON from error message
    json_match = re.search(r'\{.*\}', error_message, re.DOTALL)
    if json_match:
        try:
            error_json = json.loads(json_match.group(0))

            # Extract validation errors (most common case)
            if "errors" in error_json and isinstance(error_json["errors"], dict):
                error_parts = []
                for field, messages in error_json["errors"].items():
                    if isinstance(messages, list):
                        error_parts.extend(messages)
                    else:
                        error_parts.append(str(messages))

                if error_parts:
                    combined = "; ".join(error_parts)
                    return _truncate(f"Unable to add artist: {combined}", 150)

            # Extract title or message
            if "title" in error_json:
                return _truncate(f"Unable to add artist: {error_json['title']}", 150)

            if "message" in error_json:
                return _truncate(f"Unable to add artist: {error_json['message']}", 150)

        except json.JSONDecodeError:
            pass

    # Extract common error patterns with friendly messages
    patterns = [
        (r"artist already exists", "This artist already exists in Lidarr"),
        (r"album already exists", "This album already exists in Lidarr"),
        (r"[Ii]nvalid root folder", "Invalid music folder path - contact admin"),
        (r"root.*folder.*not found", "Music folder not found - contact admin"),
        (r"404", "Artist or album not found in MusicBrainz database"),
        (r"timeout|timed out", "Request timed out - Lidarr may be busy, try again"),
        (r"connection refused|connection error", "Cannot connect to Lidarr - service may be down"),
        (r"unauthorized|401", "Lidarr API key is invalid - contact admin"),
        (r"forbidden|403", "Access denied by Lidarr - contact admin"),
        (r"500|502|503|504", "Lidarr server error - try again later"),
        (r"[Nn]o matching artist", "Artist not found in MusicBrainz database"),
    ]

    error_lower = error_message.lower()
    for pattern, friendly_msg in patterns:
        if re.search(pattern, error_lower):
            return friendly_msg

    # Fallback: Extract first meaningful sentence
    if ": " in error_message:
        parts = error_message.split(": ", 1)
        if len(parts) > 1:
            msg = parts[1].split(".")[0].strip()
            if msg and len(msg) < 150:
                return f"Error: {msg}"

    # Last resort: Truncate and clean
    cleaned = error_message.replace("\n", " ").replace("\r", " ").strip()
    return _truncate(cleaned, 150)


def parse_artist_lookup_error(error_message: str) -> str:
    """
    Parse artist lookup errors with specific handling.

    Args:
        error_message: Raw error string from artist lookup

    Returns:
        User-friendly error message
    """
    if not error_message:
        return "Unknown error occurred"

    error_lower = error_message.lower()

    # Specific patterns for lookup errors
    if "404" in error_lower or "not found" in error_lower:
        return "Artist not found in MusicBrainz database"

    if "no matching artist" in error_lower:
        return "No artist found matching that name"

    if "timeout" in error_lower or "timed out" in error_lower:
        return "Search timed out - try again"

    if "connection" in error_lower:
        return "Cannot connect to Lidarr - service may be down"

    if "parse" in error_lower:
        return "Error reading Lidarr response - try again"

    # Fall back to generic parser
    return parse_lidarr_error(error_message)


def parse_tag_error(error_message: str) -> str:
    """
    Parse tag creation/lookup errors.

    Args:
        error_message: Raw error string from tag operations

    Returns:
        User-friendly error message
    """
    if not error_message:
        return "Unknown error occurred"

    error_lower = error_message.lower()

    # Tag-specific patterns
    if "already exists" in error_lower:
        # This is actually not a failure - tag already existing is fine
        return "Tag already exists (request will continue)"

    if "invalid" in error_lower:
        return "Invalid tag format - contact admin"

    if "create" in error_lower and "no id" in error_lower:
        return "Tag created but Lidarr didn't return ID - contact admin"

    if "connection" in error_lower:
        return "Cannot connect to Lidarr - service may be down"

    # Fall back to generic parser
    return parse_lidarr_error(error_message)


def _truncate(message: str, max_length: int = 150) -> str:
    """
    Truncate message to max length with ellipsis.

    Args:
        message: Message to truncate
        max_length: Maximum length (default 150)

    Returns:
        Truncated message
    """
    if len(message) <= max_length:
        return message

    # Try to truncate at word boundary
    truncated = message[:max_length - 3]
    last_space = truncated.rfind(" ")

    if last_space > max_length * 0.8:  # If we can keep 80%+ of the message
        return truncated[:last_space] + "..."

    return truncated + "..."


# Example error messages for testing
if __name__ == "__main__":
    test_errors = [
        # JSON validation error
        '{"type":"https://tools.ietf.org/html/rfc7231#section-6.5.1","title":"One or more validation errors occurred.","status":400,"traceId":"00-abc123","errors":{"rootFolderPath":["Invalid root folder"]}}',

        # Simple error messages
        "Lidarr error 404: Not found",
        "Lidarr lookup failed: timeout",
        "Artist already exists in library",
        "Lidarr tag create error 500: Internal server error",
        "No matching artist found in Lidarr",

        # Connection errors
        "Lidarr request failed: Connection refused",
        "Lidarr request failed: HTTPSConnectionPool(host='lidarr', port=8686): Max retries exceeded",
    ]

    print("Testing error parser:\n")
    for i, error in enumerate(test_errors, 1):
        print(f"{i}. Original: {error[:80]}...")
        print(f"   Parsed:   {parse_lidarr_error(error)}")
        print()
