#!/usr/bin/env python3
"""
Unit tests for torrent_utils.py
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from torrent_utils import (
    format_size, format_speed, format_time,
    sanitize_filename, is_magnet_link, validate_magnet_link
)


class TestFormatSize(unittest.TestCase):
    """Test format_size function"""

    def test_bytes(self):
        self.assertEqual(format_size(0), "0.00 B")
        self.assertEqual(format_size(100), "100.00 B")
        self.assertEqual(format_size(1023), "1023.00 B")

    def test_kibibytes(self):
        self.assertEqual(format_size(1024), "1.00 KiB")
        self.assertEqual(format_size(1536), "1.50 KiB")
        self.assertEqual(format_size(1024 * 1023), "1023.00 KiB")

    def test_mebibytes(self):
        self.assertEqual(format_size(1024 * 1024), "1.00 MiB")
        self.assertEqual(format_size(1024 * 1024 * 2.5), "2.50 MiB")

    def test_gibibytes(self):
        self.assertEqual(format_size(1024 * 1024 * 1024), "1.00 GiB")
        self.assertEqual(format_size(1024 * 1024 * 1024 * 5.25), "5.25 GiB")

    def test_tebibytes(self):
        self.assertEqual(format_size(1024 * 1024 * 1024 * 1024), "1.00 TiB")

    def test_pebibytes(self):
        self.assertEqual(format_size(1024 * 1024 * 1024 * 1024 * 1024), "1.00 PiB")

    def test_invalid_input(self):
        self.assertEqual(format_size(None), "Unknown")
        self.assertEqual(format_size("invalid"), "Unknown")
        self.assertEqual(format_size(-100), "-100.00 B")


class TestFormatSpeed(unittest.TestCase):
    """Test format_speed function"""

    def test_bytes_per_second(self):
        self.assertEqual(format_speed(0), "0.00 B/s")
        self.assertEqual(format_speed(500), "500.00 B/s")

    def test_kilobytes_per_second(self):
        self.assertEqual(format_speed(1024), "1.00 KiB/s")
        self.assertEqual(format_speed(5120), "5.00 KiB/s")

    def test_megabytes_per_second(self):
        self.assertEqual(format_speed(1024 * 1024), "1.00 MiB/s")
        self.assertEqual(format_speed(1024 * 1024 * 10), "10.00 MiB/s")

    def test_invalid_input(self):
        self.assertEqual(format_speed(None), "Unknown/s")
        self.assertEqual(format_speed("invalid"), "Unknown/s")


class TestFormatTime(unittest.TestCase):
    """Test format_time function"""

    def test_seconds(self):
        self.assertEqual(format_time(0), "0s")
        self.assertEqual(format_time(30), "30s")
        self.assertEqual(format_time(59), "59s")

    def test_minutes(self):
        self.assertEqual(format_time(60), "1m 0s")
        self.assertEqual(format_time(90), "1m 30s")
        self.assertEqual(format_time(3599), "59m 59s")

    def test_hours(self):
        self.assertEqual(format_time(3600), "1h 0m 0s")
        self.assertEqual(format_time(3661), "1h 1m 1s")
        self.assertEqual(format_time(7200), "2h 0m 0s")

    def test_invalid_input(self):
        self.assertEqual(format_time(-1), "Unknown")
        self.assertEqual(format_time(float('inf')), "Unknown")


class TestSanitizeFilename(unittest.TestCase):
    """Test sanitize_filename function"""

    def test_normal_filename(self):
        self.assertEqual(sanitize_filename("normal_file.txt"), "normal_file.txt")
        self.assertEqual(sanitize_filename("Movie Name 2025.mkv"), "Movie Name 2025.mkv")

    def test_path_traversal(self):
        # Should strip path and only return basename
        result = sanitize_filename("../../etc/passwd")
        self.assertEqual(result, "passwd")

        result = sanitize_filename("/etc/passwd")
        self.assertEqual(result, "passwd")

    def test_special_characters(self):
        result = sanitize_filename("file<>:|?*.txt")
        self.assertNotIn("<", result)
        self.assertNotIn(">", result)
        self.assertNotIn(":", result)
        self.assertNotIn("|", result)
        self.assertNotIn("?", result)
        self.assertNotIn("*", result)

    def test_empty_string(self):
        self.assertEqual(sanitize_filename(""), "unnamed")
        self.assertEqual(sanitize_filename("   "), "unnamed")

    def test_length_limit(self):
        long_name = "a" * 200
        result = sanitize_filename(long_name, max_length=100)
        self.assertEqual(len(result), 100)

    def test_whitespace(self):
        result = sanitize_filename("  file name  ")
        self.assertEqual(result, "file name")


class TestMagnetLink(unittest.TestCase):
    """Test magnet link validation"""

    def test_is_magnet_link_valid(self):
        valid_magnet = "magnet:?xt=urn:btih:dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c"
        self.assertTrue(is_magnet_link(valid_magnet))

    def test_is_magnet_link_invalid(self):
        self.assertFalse(is_magnet_link("http://example.com"))
        self.assertFalse(is_magnet_link("not a magnet"))
        self.assertFalse(is_magnet_link(""))

    def test_validate_magnet_link_valid(self):
        valid_magnet = "magnet:?xt=urn:btih:dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c&dn=Test"
        result = validate_magnet_link(valid_magnet)
        self.assertTrue(result['valid'])
        self.assertIn('info_hash', result)

    def test_validate_magnet_link_invalid_format(self):
        result = validate_magnet_link("not a magnet")
        self.assertFalse(result['valid'])
        self.assertIn('error', result)

    def test_validate_magnet_link_invalid_hash(self):
        invalid_magnet = "magnet:?xt=urn:btih:invalid_hash"
        result = validate_magnet_link(invalid_magnet)
        self.assertFalse(result['valid'])

    def test_validate_magnet_link_too_short(self):
        short_magnet = "magnet:?xt=urn:btih:abc"
        result = validate_magnet_link(short_magnet)
        self.assertFalse(result['valid'])


class TestIntegrationWorkflow(unittest.TestCase):
    """Test complete workflows"""

    def test_torrent_filename_workflow(self):
        """Test complete filename sanitization workflow"""
        # Simulate downloading a torrent with problematic filename
        raw_filename = "../../Bad<>Movie|Name?.mkv"
        safe_filename = sanitize_filename(raw_filename)

        # Should be safe to use in file path
        self.assertNotIn("..", safe_filename)
        self.assertNotIn("<", safe_filename)
        self.assertNotIn(">", safe_filename)

        # Should still be recognizable
        self.assertIn("Bad", safe_filename)
        self.assertIn("Movie", safe_filename)

    def test_magnet_validation_workflow(self):
        """Test magnet link validation workflow"""
        # Valid magnet
        magnet = "magnet:?xt=urn:btih:dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c&dn=Ubuntu"

        # Check it's a magnet
        self.assertTrue(is_magnet_link(magnet))

        # Validate it
        result = validate_magnet_link(magnet)
        self.assertTrue(result['valid'])

        # Should have info hash
        self.assertEqual(len(result['info_hash']), 40)


if __name__ == '__main__':
    unittest.main()
