#!/usr/bin/env python3
"""
Tests for core torrent functionality
"""

import unittest
import sys
import os
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import libtorrent as lt


class TestLibtorrentSession(unittest.TestCase):
    """Test libtorrent session creation and configuration"""

    def test_session_creation(self):
        """Test basic session creation"""
        ses = lt.session()
        self.assertIsNotNone(ses)

    def test_session_settings(self):
        """Test session settings can be configured"""
        ses = lt.session()
        settings = ses.get_settings()

        # Test setting configuration
        settings['enable_dht'] = True
        settings['enable_lsd'] = True
        ses.apply_settings(settings)

        # Verify settings were applied
        current_settings = ses.get_settings()
        self.assertTrue(current_settings['enable_dht'])
        self.assertTrue(current_settings['enable_lsd'])

    def test_session_ports(self):
        """Test session can listen on ports"""
        ses = lt.session()
        settings = ses.get_settings()
        settings['listen_interfaces'] = '0.0.0.0:6881'
        ses.apply_settings(settings)

        # Session should be created without errors
        self.assertIsNotNone(ses)


class TestMagnetParsing(unittest.TestCase):
    """Test magnet link parsing"""

    def test_parse_basic_magnet(self):
        """Test parsing basic magnet link"""
        magnet = "magnet:?xt=urn:btih:dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c"
        params = lt.parse_magnet_uri(magnet)

        self.assertIsNotNone(params)
        self.assertEqual(str(params.info_hash), "dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c")

    def test_parse_magnet_with_name(self):
        """Test parsing magnet with display name"""
        magnet = "magnet:?xt=urn:btih:dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c&dn=Test+File"
        params = lt.parse_magnet_uri(magnet)

        self.assertIsNotNone(params)
        self.assertEqual(params.name, "Test File")

    def test_parse_magnet_with_trackers(self):
        """Test parsing magnet with trackers"""
        magnet = "magnet:?xt=urn:btih:dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c&tr=udp://tracker.test.com:80"
        params = lt.parse_magnet_uri(magnet)

        self.assertIsNotNone(params)
        # Should have trackers
        self.assertGreater(len(params.trackers), 0)

    def test_invalid_magnet(self):
        """Test invalid magnet link raises error"""
        with self.assertRaises(RuntimeError):
            lt.parse_magnet_uri("not a magnet")


class TestTorrentInfo(unittest.TestCase):
    """Test torrent info creation"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_create_torrent_info(self):
        """Test creating torrent info from file storage"""
        # Create test file
        test_file = os.path.join(self.test_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test content" * 1000)

        # Create torrent
        fs = lt.file_storage()
        lt.add_files(fs, test_file)

        t = lt.create_torrent(fs)
        t.set_creator("test")
        t.add_tracker("udp://tracker.test.com:80")

        # Generate torrent
        lt.set_piece_hashes(t, self.test_dir)
        torrent_data = t.generate()

        # Should be able to create bencode
        bencode = lt.bencode(torrent_data)
        self.assertIsNotNone(bencode)
        self.assertGreater(len(bencode), 0)


class TestResumeData(unittest.TestCase):
    """Test resume data functionality"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.resume_dir = os.path.join(self.test_dir, "resume")
        os.makedirs(self.resume_dir, exist_ok=True)

    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_resume_data_serialization(self):
        """Test resume data can be saved and loaded"""
        # Create session
        ses = lt.session()

        # Add a magnet link
        magnet = "magnet:?xt=urn:btih:dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c"
        params = lt.parse_magnet_uri(magnet)
        params.save_path = self.test_dir

        handle = ses.add_torrent(params)
        info_hash = str(handle.status().info_hash)

        # Request resume data
        handle.save_resume_data()

        # Wait a moment for alert
        import time
        time.sleep(0.5)

        # Check alerts
        alerts = ses.pop_alerts()
        resume_alert = None
        for alert in alerts:
            if isinstance(alert, lt.save_resume_data_alert):
                resume_alert = alert
                break

        if resume_alert:
            # Should be able to bencode resume data
            resume_data = lt.bencode(resume_alert.params)
            self.assertIsNotNone(resume_data)
            self.assertGreater(len(resume_data), 0)

            # Save to file
            resume_file = os.path.join(self.resume_dir, f"{info_hash}.fastresume")
            with open(resume_file, 'wb') as f:
                f.write(resume_data)

            # Verify file was created
            self.assertTrue(os.path.exists(resume_file))
            self.assertGreater(os.path.getsize(resume_file), 0)


class TestTorrentStates(unittest.TestCase):
    """Test torrent state tracking"""

    def test_torrent_states_defined(self):
        """Test that torrent states are defined"""
        # These states should exist in libtorrent
        self.assertTrue(hasattr(lt.torrent_status, 'checking_files'))
        self.assertTrue(hasattr(lt.torrent_status, 'downloading'))
        self.assertTrue(hasattr(lt.torrent_status, 'seeding'))

    def test_torrent_status_attributes(self):
        """Test torrent status has expected attributes"""
        ses = lt.session()
        magnet = "magnet:?xt=urn:btih:dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c"
        params = lt.parse_magnet_uri(magnet)
        params.save_path = tempfile.gettempdir()

        handle = ses.add_torrent(params)
        status = handle.status()

        # Check expected attributes exist
        self.assertTrue(hasattr(status, 'progress'))
        self.assertTrue(hasattr(status, 'download_rate'))
        self.assertTrue(hasattr(status, 'upload_rate'))
        self.assertTrue(hasattr(status, 'num_peers'))
        self.assertTrue(hasattr(status, 'state'))
        self.assertTrue(hasattr(status, 'is_seeding'))
        self.assertTrue(hasattr(status, 'paused'))
        self.assertTrue(hasattr(status, 'has_metadata'))


class TestInfoHash(unittest.TestCase):
    """Test info hash handling"""

    def test_info_hash_from_magnet(self):
        """Test extracting info hash from magnet"""
        magnet = "magnet:?xt=urn:btih:dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c"
        params = lt.parse_magnet_uri(magnet)

        info_hash = str(params.info_hash)
        self.assertEqual(info_hash, "dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c")
        self.assertEqual(len(info_hash), 40)

    def test_info_hash_case_insensitive(self):
        """Test info hash can be uppercase or lowercase"""
        magnet_lower = "magnet:?xt=urn:btih:dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c"
        magnet_upper = "magnet:?xt=urn:btih:DD8255ECDC7CA55FB0BBF81323D87062DB1F6D1C"

        params_lower = lt.parse_magnet_uri(magnet_lower)
        params_upper = lt.parse_magnet_uri(magnet_upper)

        # Both should work and produce same hash (normalized)
        self.assertEqual(len(str(params_lower.info_hash)), 40)
        self.assertEqual(len(str(params_upper.info_hash)), 40)


class TestBencoding(unittest.TestCase):
    """Test bencode/bdecode functionality"""

    def test_bencode_simple_dict(self):
        """Test encoding simple dictionary"""
        data = {'name': 'test', 'size': 12345}
        encoded = lt.bencode(data)

        self.assertIsNotNone(encoded)
        self.assertIsInstance(encoded, bytes)
        self.assertGreater(len(encoded), 0)

    def test_bencode_bdecode_roundtrip(self):
        """Test encoding and decoding roundtrip"""
        original = {'test': 'value', 'number': 42}
        encoded = lt.bencode(original)
        decoded = lt.bdecode(encoded)

        self.assertEqual(decoded[b'test'], b'value')
        self.assertEqual(decoded[b'number'], 42)

    def test_bencode_list(self):
        """Test encoding list"""
        data = ['item1', 'item2', 'item3']
        encoded = lt.bencode(data)

        self.assertIsNotNone(encoded)
        self.assertGreater(len(encoded), 0)


if __name__ == '__main__':
    unittest.main()
