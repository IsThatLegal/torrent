#!/usr/bin/env python3
"""
Shared utility functions for torrent downloader applications
"""

import subprocess


def format_size(bytes_count):
    """
    Convert bytes to human-readable format using binary units (KiB, MiB, etc.)

    Args:
        bytes_count: Number of bytes (int or float)

    Returns:
        str: Formatted string like "1.23 GiB"
    """
    try:
        bytes_count = float(bytes_count)
    except (ValueError, TypeError):
        return "Unknown"

    # Use 1024 for binary units (KiB, MiB, GiB, TiB)
    for unit in ['B', 'KiB', 'MiB', 'GiB', 'TiB']:
        if bytes_count < 1024.0:
            return f"{bytes_count:.2f} {unit}"
        bytes_count /= 1024.0
    return f"{bytes_count:.2f} PiB"


def format_speed(bytes_per_sec):
    """
    Convert bytes/sec to human-readable format

    Args:
        bytes_per_sec: Speed in bytes per second

    Returns:
        str: Formatted string like "1.23 MiB/s"
    """
    return format_size(bytes_per_sec) + "/s"


def format_time(seconds):
    """
    Convert seconds to human-readable format

    Args:
        seconds: Time in seconds (int or float)

    Returns:
        str: Formatted string like "1h 23m 45s"
    """
    try:
        if seconds < 0 or seconds == float('inf'):
            return "Unknown"

        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    except (ValueError, TypeError):
        return "Unknown"


def send_notification(title, message):
    """
    Send desktop notification (Linux only)

    Args:
        title: Notification title
        message: Notification message
    """
    try:
        subprocess.run(['notify-send', title, message], check=False, timeout=5)
    except Exception:
        pass  # Silently fail if notify-send is not available


def sanitize_filename(filename, max_length=100):
    """
    Sanitize a filename to prevent path traversal and other issues

    Args:
        filename: Original filename
        max_length: Maximum filename length

    Returns:
        str: Sanitized filename
    """
    import os
    import re

    # Remove path components (this handles / and \)
    safe_name = os.path.basename(filename)

    # Replace dangerous characters (but keep spaces, dots, hyphens, underscores)
    safe_name = re.sub(r'[^\w\s.-]', '_', safe_name)

    # Strip whitespace
    safe_name = safe_name.strip()

    # Limit length
    safe_name = safe_name[:max_length]

    # Ensure it's not empty
    if not safe_name or safe_name.isspace():
        safe_name = "unnamed"

    return safe_name


def is_magnet_link(link):
    """
    Check if a string is a magnet link

    Args:
        link: String to check

    Returns:
        bool: True if string starts with "magnet:?"
    """
    if not link:
        return False
    return link.strip().startswith('magnet:?')


def validate_magnet_link(magnet_link):
    """
    Validate a magnet link and extract info hash

    Args:
        magnet_link: Magnet link to validate

    Returns:
        dict: {'valid': bool, 'info_hash': str or None, 'error': str or None}
    """
    import re

    result = {
        'valid': False,
        'info_hash': None,
        'error': None
    }

    if not magnet_link:
        result['error'] = "Empty magnet link"
        return result

    # Check basic format
    if not is_magnet_link(magnet_link):
        result['error'] = "Must start with 'magnet:?'"
        return result

    # Check for xt parameter with btih
    if 'xt=urn:btih:' not in magnet_link:
        result['error'] = "Missing 'xt=urn:btih:' parameter"
        return result

    # Extract info hash
    match = re.search(r'xt=urn:btih:([a-fA-F0-9]+)', magnet_link)
    if not match:
        result['error'] = "Invalid info hash format"
        return result

    info_hash = match.group(1)

    # Validate info hash length (40 chars for SHA1, 64 for SHA256)
    if len(info_hash) not in [40, 64]:
        result['error'] = f"Invalid info hash length: {len(info_hash)} (expected 40 or 64)"
        return result

    # Validate info hash is hex
    if not re.match(r'^[a-fA-F0-9]+$', info_hash):
        result['error'] = "Info hash contains non-hexadecimal characters"
        return result

    # All checks passed
    result['valid'] = True
    result['info_hash'] = info_hash.lower()
    return result
