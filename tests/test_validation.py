#!/usr/bin/env python3
"""
Tests for input validation
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from torrent_utils import validate_magnet_link, sanitize_filename


class TestMagnetValidation(unittest.TestCase):
    """Test magnet link validation"""

    def test_valid_magnet_basic(self):
        """Test valid basic magnet link"""
        magnet = "magnet:?xt=urn:btih:dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c"
        result = validate_magnet_link(magnet)
        self.assertTrue(result['valid'])
        self.assertEqual(result['info_hash'], "dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c")

    def test_valid_magnet_with_name(self):
        """Test valid magnet with display name"""
        magnet = "magnet:?xt=urn:btih:dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c&dn=Ubuntu"
        result = validate_magnet_link(magnet)
        self.assertTrue(result['valid'])

    def test_valid_magnet_with_trackers(self):
        """Test valid magnet with trackers"""
        magnet = "magnet:?xt=urn:btih:dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c&tr=udp://tracker.example.com:80"
        result = validate_magnet_link(magnet)
        self.assertTrue(result['valid'])

    def test_invalid_magnet_no_prefix(self):
        """Test invalid magnet without magnet: prefix"""
        result = validate_magnet_link("xt=urn:btih:dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c")
        self.assertFalse(result['valid'])
        self.assertIn('error', result)

    def test_invalid_magnet_no_xt(self):
        """Test invalid magnet without xt parameter"""
        result = validate_magnet_link("magnet:?dn=Test")
        self.assertFalse(result['valid'])

    def test_invalid_magnet_wrong_urn(self):
        """Test invalid magnet with wrong URN format"""
        result = validate_magnet_link("magnet:?xt=urn:sha1:dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c")
        self.assertFalse(result['valid'])

    def test_invalid_magnet_short_hash(self):
        """Test invalid magnet with too short hash"""
        result = validate_magnet_link("magnet:?xt=urn:btih:abc123")
        self.assertFalse(result['valid'])

    def test_invalid_magnet_long_hash(self):
        """Test invalid magnet with too long hash"""
        hash_too_long = "a" * 100
        result = validate_magnet_link(f"magnet:?xt=urn:btih:{hash_too_long}")
        self.assertFalse(result['valid'])

    def test_invalid_magnet_non_hex_hash(self):
        """Test invalid magnet with non-hex characters in hash"""
        result = validate_magnet_link("magnet:?xt=urn:btih:gggggggggggggggggggggggggggggggggggggggg")
        self.assertFalse(result['valid'])

    def test_invalid_magnet_empty(self):
        """Test invalid empty magnet"""
        result = validate_magnet_link("")
        self.assertFalse(result['valid'])

    def test_invalid_magnet_url(self):
        """Test that regular URLs are rejected"""
        result = validate_magnet_link("http://example.com/file.torrent")
        self.assertFalse(result['valid'])


class TestBandwidthValidation(unittest.TestCase):
    """Test bandwidth limit validation"""

    def test_valid_bandwidth_zero(self):
        """Test zero bandwidth (unlimited)"""
        self.assertTrue(self.validate_bandwidth("0"))

    def test_valid_bandwidth_positive(self):
        """Test positive bandwidth values"""
        self.assertTrue(self.validate_bandwidth("100"))
        self.assertTrue(self.validate_bandwidth("1000"))
        self.assertTrue(self.validate_bandwidth("50000"))

    def test_invalid_bandwidth_negative(self):
        """Test negative bandwidth"""
        self.assertFalse(self.validate_bandwidth("-100"))

    def test_invalid_bandwidth_non_numeric(self):
        """Test non-numeric bandwidth"""
        self.assertFalse(self.validate_bandwidth("abc"))
        self.assertFalse(self.validate_bandwidth("12.34.56"))

    def test_invalid_bandwidth_too_large(self):
        """Test bandwidth exceeding maximum"""
        self.assertFalse(self.validate_bandwidth("10000000"))

    def test_valid_bandwidth_empty(self):
        """Test empty bandwidth (treated as unlimited)"""
        self.assertTrue(self.validate_bandwidth(""))

    def validate_bandwidth(self, value):
        """Helper to validate bandwidth"""
        if value == "":
            return True
        try:
            limit = int(value)
            if limit < 0:
                return False
            if limit > 1000000:
                return False
            return True
        except ValueError:
            return False


class TestFilePathValidation(unittest.TestCase):
    """Test file path validation"""

    def test_valid_path_relative(self):
        """Test valid relative paths"""
        self.assertTrue(self.is_safe_path("torrents"))
        self.assertTrue(self.is_safe_path("downloads/movies"))

    def test_valid_path_absolute(self):
        """Test valid absolute paths"""
        self.assertTrue(self.is_safe_path("/home/user/downloads"))
        self.assertTrue(self.is_safe_path("/tmp/torrents"))

    def test_invalid_path_traversal(self):
        """Test path traversal attempts"""
        self.assertFalse(self.is_safe_path("../../etc/passwd"))
        self.assertFalse(self.is_safe_path("downloads/../../etc"))

    def test_invalid_path_null_byte(self):
        """Test null byte injection"""
        self.assertFalse(self.is_safe_path("/tmp/file\x00.txt"))

    def is_safe_path(self, path):
        """Helper to validate paths"""
        if '\x00' in path:
            return False
        # Normalize path
        normalized = os.path.normpath(path)
        # Check for traversal
        if normalized.startswith('..'):
            return False
        return True


class TestFilenameValidation(unittest.TestCase):
    """Test filename validation and sanitization"""

    def test_sanitize_normal_filename(self):
        """Test normal filenames pass through"""
        self.assertEqual(sanitize_filename("normal.txt"), "normal.txt")
        self.assertEqual(sanitize_filename("my_file_123.mkv"), "my_file_123.mkv")

    def test_sanitize_removes_dangerous_chars(self):
        """Test dangerous characters are removed"""
        result = sanitize_filename("file<>:|?*.txt")
        self.assertNotIn("<", result)
        self.assertNotIn(">", result)
        self.assertNotIn(":", result)
        self.assertNotIn("|", result)
        self.assertNotIn("?", result)
        self.assertNotIn("*", result)

    def test_sanitize_prevents_path_traversal(self):
        """Test path traversal is prevented"""
        result = sanitize_filename("../../etc/passwd")
        self.assertNotIn("..", result)
        self.assertEqual(result, "passwd")

    def test_sanitize_handles_null_bytes(self):
        """Test null bytes are removed"""
        result = sanitize_filename("file\x00.txt")
        self.assertNotIn("\x00", result)

    def test_sanitize_handles_empty(self):
        """Test empty filenames are handled"""
        result = sanitize_filename("")
        self.assertEqual(result, "unnamed")

    def test_sanitize_respects_length_limit(self):
        """Test length limits are enforced"""
        long_name = "a" * 200
        result = sanitize_filename(long_name, max_length=50)
        self.assertLessEqual(len(result), 50)


class TestSecurityValidation(unittest.TestCase):
    """Test security-related validation"""

    def test_no_command_injection(self):
        """Test command injection is prevented"""
        dangerous = "file; rm -rf /"
        safe = sanitize_filename(dangerous)
        self.assertNotIn(";", safe)

    def test_no_script_injection(self):
        """Test script injection is prevented"""
        dangerous = "<script>alert('xss')</script>"
        safe = sanitize_filename(dangerous)
        self.assertNotIn("<", safe)
        self.assertNotIn(">", safe)

    def test_no_sql_injection(self):
        """Test SQL injection characters are handled"""
        dangerous = "file' OR '1'='1"
        safe = sanitize_filename(dangerous)
        # Single quotes should be replaced or removed
        self.assertNotIn("'", safe)


if __name__ == '__main__':
    unittest.main()
