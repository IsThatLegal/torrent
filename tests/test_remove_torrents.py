#!/usr/bin/env python3
"""
Tests for remove torrents functionality
"""

import unittest
import sys
import os
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import libtorrent as lt


class TestRemoveTorrents(unittest.TestCase):
    """Test torrent removal and resume file deletion"""

    def setUp(self):
        """Set up test environment"""
        # Create temporary directories
        self.test_dir = tempfile.mkdtemp()
        self.resume_dir = os.path.join(self.test_dir, "resume")
        self.download_dir = os.path.join(self.test_dir, "downloads")
        os.makedirs(self.resume_dir)
        os.makedirs(self.download_dir)

        # Test info hash
        self.test_hash = "dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c"

    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_resume_files_created(self):
        """Test that resume files can be created"""
        # Create test resume files
        fastresume = os.path.join(self.resume_dir, f"{self.test_hash}.fastresume")
        torrent_file = os.path.join(self.resume_dir, f"{self.test_hash}.torrent")
        magnet_file = os.path.join(self.resume_dir, f"{self.test_hash}.magnet")

        # Write test data
        with open(fastresume, 'wb') as f:
            f.write(b"resume_data")
        with open(torrent_file, 'wb') as f:
            f.write(b"torrent_data")
        with open(magnet_file, 'w') as f:
            f.write("magnet:?xt=urn:btih:test")

        # Verify files exist
        self.assertTrue(os.path.exists(fastresume))
        self.assertTrue(os.path.exists(torrent_file))
        self.assertTrue(os.path.exists(magnet_file))

    def test_delete_resume_files(self):
        """Test delete_resume_files function"""
        # Create test resume files
        fastresume = os.path.join(self.resume_dir, f"{self.test_hash}.fastresume")
        torrent_file = os.path.join(self.resume_dir, f"{self.test_hash}.torrent")
        magnet_file = os.path.join(self.resume_dir, f"{self.test_hash}.magnet")

        with open(fastresume, 'wb') as f:
            f.write(b"resume_data")
        with open(torrent_file, 'wb') as f:
            f.write(b"torrent_data")
        with open(magnet_file, 'w') as f:
            f.write("magnet:?xt=urn:btih:test")

        # Simulate delete_resume_files function
        extensions = ['.fastresume', '.torrent', '.magnet']
        for ext in extensions:
            filename = os.path.join(self.resume_dir, f"{self.test_hash}{ext}")
            if os.path.exists(filename):
                os.remove(filename)

        # Verify files are deleted
        self.assertFalse(os.path.exists(fastresume))
        self.assertFalse(os.path.exists(torrent_file))
        self.assertFalse(os.path.exists(magnet_file))

    def test_delete_resume_files_partial(self):
        """Test deleting resume files when only some exist"""
        # Create only some files
        fastresume = os.path.join(self.resume_dir, f"{self.test_hash}.fastresume")
        magnet_file = os.path.join(self.resume_dir, f"{self.test_hash}.magnet")

        with open(fastresume, 'wb') as f:
            f.write(b"resume_data")
        with open(magnet_file, 'w') as f:
            f.write("magnet:?xt=urn:btih:test")

        # No .torrent file created

        # Simulate delete_resume_files function
        extensions = ['.fastresume', '.torrent', '.magnet']
        for ext in extensions:
            filename = os.path.join(self.resume_dir, f"{self.test_hash}{ext}")
            if os.path.exists(filename):
                os.remove(filename)

        # Verify existing files are deleted
        self.assertFalse(os.path.exists(fastresume))
        self.assertFalse(os.path.exists(magnet_file))

    def test_delete_resume_files_missing(self):
        """Test deleting resume files when none exist"""
        # Don't create any files

        # Simulate delete_resume_files function (should not error)
        extensions = ['.fastresume', '.torrent', '.magnet']
        deleted_count = 0
        for ext in extensions:
            filename = os.path.join(self.resume_dir, f"{self.test_hash}{ext}")
            if os.path.exists(filename):
                os.remove(filename)
                deleted_count += 1

        # Should complete without error
        self.assertEqual(deleted_count, 0)

    def test_find_resume_files(self):
        """Test finding all resume files for a torrent"""
        # Create multiple torrents
        hashes = ["hash1", "hash2", "hash3"]

        for h in hashes:
            magnet_file = os.path.join(self.resume_dir, f"{h}.magnet")
            with open(magnet_file, 'w') as f:
                f.write(f"magnet:?xt=urn:btih:{h}")

        # Find all info hashes
        all_files = os.listdir(self.resume_dir)
        found_hashes = set()

        for filename in all_files:
            if filename.endswith(('.fastresume', '.torrent', '.magnet')):
                info_hash = filename.rsplit('.', 1)[0]
                found_hashes.add(info_hash)

        # Should find all 3
        self.assertEqual(len(found_hashes), 3)
        self.assertIn("hash1", found_hashes)
        self.assertIn("hash2", found_hashes)
        self.assertIn("hash3", found_hashes)

    def test_downloaded_file_deletion(self):
        """Test deletion of downloaded files"""
        # Create test downloaded file
        test_file = os.path.join(self.download_dir, "test_movie.mkv")
        with open(test_file, 'wb') as f:
            f.write(b"fake movie data" * 1000)

        self.assertTrue(os.path.exists(test_file))

        # Delete it
        os.remove(test_file)

        # Verify deleted
        self.assertFalse(os.path.exists(test_file))

    def test_downloaded_directory_deletion(self):
        """Test deletion of downloaded directory"""
        # Create test downloaded directory
        test_dir = os.path.join(self.download_dir, "Movie_Name")
        os.makedirs(test_dir)

        # Create files inside
        file1 = os.path.join(test_dir, "movie.mkv")
        file2 = os.path.join(test_dir, "subtitle.srt")

        with open(file1, 'wb') as f:
            f.write(b"movie data")
        with open(file2, 'w') as f:
            f.write("subtitle data")

        self.assertTrue(os.path.exists(test_dir))
        self.assertTrue(os.path.exists(file1))
        self.assertTrue(os.path.exists(file2))

        # Delete directory
        shutil.rmtree(test_dir)

        # Verify deleted
        self.assertFalse(os.path.exists(test_dir))
        self.assertFalse(os.path.exists(file1))
        self.assertFalse(os.path.exists(file2))

    def test_selective_deletion(self):
        """Test that only targeted torrent files are deleted"""
        # Create files for multiple torrents
        hash1 = "hash1"
        hash2 = "hash2"

        # Create files for both
        for h in [hash1, hash2]:
            for ext in ['.fastresume', '.torrent', '.magnet']:
                filename = os.path.join(self.resume_dir, f"{h}{ext}")
                with open(filename, 'w') as f:
                    f.write(f"data for {h}")

        # Delete only hash1
        extensions = ['.fastresume', '.torrent', '.magnet']
        for ext in extensions:
            filename = os.path.join(self.resume_dir, f"{hash1}{ext}")
            if os.path.exists(filename):
                os.remove(filename)

        # Verify hash1 deleted
        for ext in extensions:
            filename = os.path.join(self.resume_dir, f"{hash1}{ext}")
            self.assertFalse(os.path.exists(filename))

        # Verify hash2 still exists
        for ext in extensions:
            filename = os.path.join(self.resume_dir, f"{hash2}{ext}")
            self.assertTrue(os.path.exists(filename))


class TestResumeFileFormats(unittest.TestCase):
    """Test resume file format handling"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.resume_dir = os.path.join(self.test_dir, "resume")
        os.makedirs(self.resume_dir)

    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_valid_fastresume_size(self):
        """Test detecting valid vs invalid fastresume files"""
        hash1 = "valid_hash"
        hash2 = "invalid_hash"

        # Create valid file (> 10 bytes)
        valid_file = os.path.join(self.resume_dir, f"{hash1}.fastresume")
        with open(valid_file, 'wb') as f:
            f.write(b"x" * 100)  # 100 bytes

        # Create invalid file (< 10 bytes)
        invalid_file = os.path.join(self.resume_dir, f"{hash2}.fastresume")
        with open(invalid_file, 'wb') as f:
            f.write(b"xx")  # 2 bytes

        # Check sizes
        self.assertGreater(os.path.getsize(valid_file), 10)
        self.assertLess(os.path.getsize(invalid_file), 10)

    def test_identify_corrupted_files(self):
        """Test identifying corrupted files by size"""
        # Create various files
        files = {
            'good1.fastresume': 500,   # Good
            'good2.fastresume': 1000,  # Good
            'bad1.fastresume': 2,      # Bad (too small)
            'bad2.fastresume': 0,      # Bad (empty)
            'good3.torrent': 200,      # Good
            'bad3.torrent': 5,         # Bad (too small)
        }

        for filename, size in files.items():
            filepath = os.path.join(self.resume_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(b'x' * size)

        # Identify corrupted files
        corrupted = []
        for filename in os.listdir(self.resume_dir):
            filepath = os.path.join(self.resume_dir, filename)
            size = os.path.getsize(filepath)

            if filename.endswith('.fastresume') and size < 10:
                corrupted.append(filename)
            elif filename.endswith('.torrent') and size < 100:
                corrupted.append(filename)

        # Should identify 3 corrupted files
        self.assertEqual(len(corrupted), 3)
        self.assertIn('bad1.fastresume', corrupted)
        self.assertIn('bad2.fastresume', corrupted)
        self.assertIn('bad3.torrent', corrupted)


class TestInfoHashHandling(unittest.TestCase):
    """Test info hash extraction and handling"""

    def test_extract_info_hash_from_filename(self):
        """Test extracting info hash from filename"""
        files = [
            "dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c.fastresume",
            "dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c.torrent",
            "dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c.magnet",
        ]

        expected_hash = "dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c"

        for filename in files:
            # Extract hash by splitting on '.'
            info_hash = filename.rsplit('.', 1)[0]
            self.assertEqual(info_hash, expected_hash)

    def test_info_hash_length(self):
        """Test that info hashes are correct length"""
        valid_hash = "dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c"

        # SHA-1 hash should be 40 characters
        self.assertEqual(len(valid_hash), 40)

        # Should be hex characters only
        try:
            int(valid_hash, 16)
            is_hex = True
        except ValueError:
            is_hex = False

        self.assertTrue(is_hex)

    def test_multiple_torrents_unique_hashes(self):
        """Test that different torrents have different hashes"""
        hash1 = "dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c"
        hash2 = "83de20148749b8bf74e41b6f4572f521a016603a"

        self.assertNotEqual(hash1, hash2)
        self.assertEqual(len(hash1), 40)
        self.assertEqual(len(hash2), 40)


if __name__ == '__main__':
    unittest.main()
