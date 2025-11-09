#!/usr/bin/env python3
"""
Unit tests for torrent_utils module using built-in unittest
Run with: python3 test_torrent_utils_simple.py
"""

import unittest
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from torrent_utils import (
    format_size,
    format_speed,
    format_time,
    send_notification,
    sanitize_filename
)


class TestFormatSize(unittest.TestCase):
    """Tests for format_size function"""

    def test_bytes(self):
        self.assertEqual(format_size(0), "0.00 B")
        self.assertEqual(format_size(100), "100.00 B")
        self.assertEqual(format_size(1023), "1023.00 B")

    def test_kibibytes(self):
        self.assertEqual(format_size(1024), "1.00 KiB")
        self.assertEqual(format_size(1536), "1.50 KiB")
        self.assertEqual(format_size(2048), "2.00 KiB")

    def test_mebibytes(self):
        self.assertEqual(format_size(1024 * 1024), "1.00 MiB")
        self.assertEqual(format_size(int(1.5 * 1024 * 1024)), "1.50 MiB")
        self.assertEqual(format_size(100 * 1024 * 1024), "100.00 MiB")

    def test_gibibytes(self):
        self.assertEqual(format_size(1024 * 1024 * 1024), "1.00 GiB")
        self.assertEqual(format_size(int(2.5 * 1024 * 1024 * 1024)), "2.50 GiB")

    def test_tebibytes(self):
        self.assertEqual(format_size(1024 * 1024 * 1024 * 1024), "1.00 TiB")

    def test_pebibytes(self):
        self.assertEqual(format_size(1024 * 1024 * 1024 * 1024 * 1024), "1.00 PiB")

    def test_invalid_input(self):
        self.assertEqual(format_size("invalid"), "Unknown")
        self.assertEqual(format_size(None), "Unknown")

    def test_float(self):
        self.assertEqual(format_size(1536.7), "1.50 KiB")


class TestFormatSpeed(unittest.TestCase):
    """Tests for format_speed function"""

    def test_basic_speed(self):
        self.assertEqual(format_speed(1024), "1.00 KiB/s")
        self.assertEqual(format_speed(1024 * 1024), "1.00 MiB/s")

    def test_zero_speed(self):
        self.assertEqual(format_speed(0), "0.00 B/s")


class TestFormatTime(unittest.TestCase):
    """Tests for format_time function"""

    def test_seconds_only(self):
        self.assertEqual(format_time(0), "0s")
        self.assertEqual(format_time(30), "30s")
        self.assertEqual(format_time(59), "59s")

    def test_minutes(self):
        self.assertEqual(format_time(60), "1m 0s")
        self.assertEqual(format_time(90), "1m 30s")
        self.assertEqual(format_time(600), "10m 0s")

    def test_hours(self):
        self.assertEqual(format_time(3600), "1h 0m 0s")
        self.assertEqual(format_time(3661), "1h 1m 1s")
        self.assertEqual(format_time(7200), "2h 0m 0s")

    def test_combined(self):
        self.assertEqual(format_time(3723), "1h 2m 3s")
        self.assertEqual(format_time(5400), "1h 30m 0s")

    def test_negative(self):
        self.assertEqual(format_time(-1), "Unknown")
        self.assertEqual(format_time(-100), "Unknown")

    def test_infinity(self):
        self.assertEqual(format_time(float('inf')), "Unknown")

    def test_invalid(self):
        self.assertEqual(format_time("invalid"), "Unknown")
        self.assertEqual(format_time(None), "Unknown")


class TestSanitizeFilename(unittest.TestCase):
    """Tests for sanitize_filename function"""

    def test_simple_filename(self):
        self.assertEqual(sanitize_filename("test.txt"), "test.txt")
        self.assertEqual(sanitize_filename("my_file.torrent"), "my_file.torrent")

    def test_path_traversal(self):
        # Should remove path components
        self.assertEqual(sanitize_filename("../../../etc/passwd"), "passwd")
        self.assertEqual(sanitize_filename("/etc/passwd"), "passwd")
        self.assertEqual(sanitize_filename("dir/file.txt"), "file.txt")

    def test_dangerous_characters(self):
        # Should remove or replace dangerous characters
        result = sanitize_filename("file<>:|?*.txt")
        self.assertNotIn("<", result)
        self.assertNotIn(">", result)
        self.assertNotIn(":", result)
        self.assertNotIn("|", result)
        self.assertNotIn("?", result)
        self.assertNotIn("*", result)

    def test_long_filename(self):
        # Should limit length
        long_name = "a" * 200
        result = sanitize_filename(long_name)
        self.assertLessEqual(len(result), 100)

    def test_custom_max_length(self):
        long_name = "a" * 50
        result = sanitize_filename(long_name, max_length=20)
        self.assertEqual(len(result), 20)

    def test_empty_string(self):
        # Should return "unnamed" for empty string
        self.assertEqual(sanitize_filename(""), "unnamed")
        self.assertEqual(sanitize_filename("   "), "unnamed")

    def test_spaces(self):
        # Should keep spaces
        self.assertIn("file name", sanitize_filename("file name.txt"))


class TestSendNotification(unittest.TestCase):
    """Tests for send_notification function"""

    def test_notification_doesnt_crash(self):
        # Should not raise an exception even if notify-send is missing
        try:
            send_notification("Test", "Message")
            # If we get here, it didn't crash
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"send_notification should not raise exceptions: {e}")

    def test_with_special_characters(self):
        # Should handle special characters without crashing
        try:
            send_notification("Test <>&", "Message with \"quotes\" and 'apostrophes'")
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"send_notification should handle special characters: {e}")


class TestEdgeCases(unittest.TestCase):
    """Edge case tests"""

    def test_format_size_very_large(self):
        # Test with extremely large numbers
        huge_number = 1024 ** 6  # Beyond PiB
        result = format_size(huge_number)
        self.assertIn("PiB", result)

    def test_format_time_very_large(self):
        # 24+ hours
        result = format_time(86400)  # 24 hours
        self.assertIn("24h", result)

    def test_sanitize_filename_null_bytes(self):
        # Null bytes should be handled
        result = sanitize_filename("file\x00name.txt")
        self.assertNotIn("\x00", result)


class TestIntegration(unittest.TestCase):
    """Integration tests combining multiple functions"""

    def test_torrent_workflow(self):
        """Simulate a typical torrent workflow"""
        # Get a torrent name from search
        torrent_name = "Ubuntu 22.04 LTS.torrent"

        # Sanitize it
        safe_name = sanitize_filename(torrent_name)
        self.assertEqual(safe_name, "Ubuntu 22.04 LTS.torrent")

        # Format size
        size = 3 * 1024 * 1024 * 1024  # 3 GiB
        size_str = format_size(size)
        self.assertIn("3.00 GiB", size_str)

        # Format download speed
        speed = 5 * 1024 * 1024  # 5 MiB/s
        speed_str = format_speed(speed)
        self.assertIn("5.00 MiB/s", speed_str)

        # Format ETA
        eta = 600  # 10 minutes
        eta_str = format_time(eta)
        self.assertIn("10m", eta_str)


def run_tests():
    """Run all tests and display results"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestFormatSize))
    suite.addTests(loader.loadTestsFromTestCase(TestFormatSpeed))
    suite.addTests(loader.loadTestsFromTestCase(TestFormatTime))
    suite.addTests(loader.loadTestsFromTestCase(TestSanitizeFilename))
    suite.addTests(loader.loadTestsFromTestCase(TestSendNotification))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
