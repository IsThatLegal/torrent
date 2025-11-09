#!/usr/bin/env python3
"""
Unit tests for torrent_utils module
Run with: python3 -m pytest test_torrent_utils.py -v
"""

import pytest
import os
import tempfile
from torrent_utils import (
    format_size,
    format_speed,
    format_time,
    send_notification,
    sanitize_filename
)


class TestFormatSize:
    """Tests for format_size function"""

    def test_bytes(self):
        assert format_size(0) == "0.00 B"
        assert format_size(100) == "100.00 B"
        assert format_size(1023) == "1023.00 B"

    def test_kibibytes(self):
        assert format_size(1024) == "1.00 KiB"
        assert format_size(1536) == "1.50 KiB"
        assert format_size(2048) == "2.00 KiB"

    def test_mebibytes(self):
        assert format_size(1024 * 1024) == "1.00 MiB"
        assert format_size(1.5 * 1024 * 1024) == "1.50 MiB"
        assert format_size(100 * 1024 * 1024) == "100.00 MiB"

    def test_gibibytes(self):
        assert format_size(1024 * 1024 * 1024) == "1.00 GiB"
        assert format_size(2.5 * 1024 * 1024 * 1024) == "2.50 GiB"

    def test_tebibytes(self):
        assert format_size(1024 * 1024 * 1024 * 1024) == "1.00 TiB"

    def test_pebibytes(self):
        assert format_size(1024 * 1024 * 1024 * 1024 * 1024) == "1.00 PiB"

    def test_invalid_input(self):
        assert format_size("invalid") == "Unknown"
        assert format_size(None) == "Unknown"

    def test_negative(self):
        # Negative numbers should still format
        result = format_size(-1024)
        assert "KiB" in result

    def test_float(self):
        assert format_size(1536.7) == "1.50 KiB"


class TestFormatSpeed:
    """Tests for format_speed function"""

    def test_basic_speed(self):
        assert format_speed(1024) == "1.00 KiB/s"
        assert format_speed(1024 * 1024) == "1.00 MiB/s"

    def test_zero_speed(self):
        assert format_speed(0) == "0.00 B/s"


class TestFormatTime:
    """Tests for format_time function"""

    def test_seconds_only(self):
        assert format_time(0) == "0s"
        assert format_time(30) == "30s"
        assert format_time(59) == "59s"

    def test_minutes(self):
        assert format_time(60) == "1m 0s"
        assert format_time(90) == "1m 30s"
        assert format_time(600) == "10m 0s"

    def test_hours(self):
        assert format_time(3600) == "1h 0m 0s"
        assert format_time(3661) == "1h 1m 1s"
        assert format_time(7200) == "2h 0m 0s"

    def test_combined(self):
        assert format_time(3723) == "1h 2m 3s"
        assert format_time(5400) == "1h 30m 0s"

    def test_negative(self):
        assert format_time(-1) == "Unknown"
        assert format_time(-100) == "Unknown"

    def test_infinity(self):
        assert format_time(float('inf')) == "Unknown"

    def test_invalid(self):
        assert format_time("invalid") == "Unknown"
        assert format_time(None) == "Unknown"


class TestSanitizeFilename:
    """Tests for sanitize_filename function"""

    def test_simple_filename(self):
        assert sanitize_filename("test.txt") == "test.txt"
        assert sanitize_filename("my_file.torrent") == "my_file.torrent"

    def test_path_traversal(self):
        # Should remove path components
        assert sanitize_filename("../../../etc/passwd") == "_etc_passwd"
        assert sanitize_filename("/etc/passwd") == "passwd"
        assert sanitize_filename("dir/file.txt") == "file.txt"

    def test_dangerous_characters(self):
        # Should remove or replace dangerous characters
        result = sanitize_filename("file<>:|?*.txt")
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result
        assert "|" not in result
        assert "?" not in result
        assert "*" not in result

    def test_long_filename(self):
        # Should limit length
        long_name = "a" * 200
        result = sanitize_filename(long_name)
        assert len(result) <= 100

    def test_custom_max_length(self):
        long_name = "a" * 50
        result = sanitize_filename(long_name, max_length=20)
        assert len(result) == 20

    def test_empty_string(self):
        # Should return "unnamed" for empty string
        assert sanitize_filename("") == "unnamed"
        assert sanitize_filename("   ") == "unnamed"

    def test_only_dangerous_chars(self):
        # Should return "unnamed" if all chars are stripped
        result = sanitize_filename("<<<>>>")
        assert len(result) > 0  # Should have something

    def test_unicode(self):
        # Should handle unicode characters
        result = sanitize_filename("файл.txt")
        assert len(result) > 0

    def test_spaces(self):
        # Should keep spaces
        assert "file name" in sanitize_filename("file name.txt")


class TestSendNotification:
    """Tests for send_notification function"""

    def test_notification_doesnt_crash(self):
        # Should not raise an exception even if notify-send is missing
        try:
            send_notification("Test", "Message")
            # If we get here, it didn't crash
            assert True
        except Exception:
            pytest.fail("send_notification should not raise exceptions")

    def test_with_special_characters(self):
        # Should handle special characters without crashing
        try:
            send_notification("Test <>&", "Message with \"quotes\" and 'apostrophes'")
            assert True
        except Exception:
            pytest.fail("send_notification should handle special characters")


class TestEdgeCases:
    """Edge case tests"""

    def test_format_size_very_large(self):
        # Test with extremely large numbers
        huge_number = 1024 ** 6  # Beyond PiB
        result = format_size(huge_number)
        assert "PiB" in result

    def test_format_time_very_large(self):
        # 24+ hours
        result = format_time(86400)  # 24 hours
        assert "24h" in result

    def test_sanitize_filename_null_bytes(self):
        # Null bytes should be handled
        result = sanitize_filename("file\x00name.txt")
        assert "\x00" not in result


# Integration tests
class TestIntegration:
    """Integration tests combining multiple functions"""

    def test_torrent_workflow(self):
        """Simulate a typical torrent workflow"""
        # Get a torrent name from search
        torrent_name = "Ubuntu 22.04 LTS.torrent"

        # Sanitize it
        safe_name = sanitize_filename(torrent_name)
        assert safe_name == "Ubuntu_22.04_LTS.torrent"

        # Format size
        size = 3 * 1024 * 1024 * 1024  # 3 GiB
        size_str = format_size(size)
        assert "3.00 GiB" in size_str

        # Format download speed
        speed = 5 * 1024 * 1024  # 5 MiB/s
        speed_str = format_speed(speed)
        assert "5.00 MiB/s" in speed_str

        # Format ETA
        eta = 600  # 10 minutes
        eta_str = format_time(eta)
        assert "10m" in eta_str


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
