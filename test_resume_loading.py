#!/usr/bin/env python3
"""
Test Resume Loading - Check if magnets load properly
"""

import os
import libtorrent as lt

def test_loading():
    """Test loading torrents from magnet files"""
    resume_dir = os.path.expanduser("~/.config/torrent-downloader/resume")

    print("=" * 70)
    print("Testing Resume Loading")
    print("=" * 70)
    print()

    # Find all magnet files
    magnet_files = [f for f in os.listdir(resume_dir) if f.endswith('.magnet')]

    print(f"Found {len(magnet_files)} magnet file(s)")
    print()

    for idx, filename in enumerate(magnet_files, 1):
        info_hash = filename.replace('.magnet', '')
        magnet_file = os.path.join(resume_dir, filename)

        print(f"Torrent {idx}:")
        print(f"  Info Hash: {info_hash}")
        print(f"  File: {filename}")

        try:
            # Read magnet link
            with open(magnet_file, 'r') as f:
                magnet = f.read().strip()

            print(f"  Magnet: {magnet[:80]}...")

            # Parse magnet
            params = lt.parse_magnet_uri(magnet)

            print(f"  Parsed successfully!")
            if params.name:
                print(f"  Name: {params.name}")
            else:
                print(f"  Name: (not in magnet)")

            print(f"  Trackers: {len(params.trackers)}")

            # Test creating add_torrent_params
            atp = lt.add_torrent_params()
            atp.save_path = "/tmp/test"

            # Add magnet info
            magnet_params = lt.parse_magnet_uri(magnet)
            atp.info_hash = magnet_params.info_hash
            if magnet_params.name:
                atp.name = magnet_params.name
            atp.trackers = magnet_params.trackers

            print(f"  ✓ Can be loaded!")

        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()

        print()

    print("=" * 70)
    print("Test complete!")
    print()
    print("If all magnets loaded successfully, the app should work.")
    print("Try running: python3 torrent-dl-gui-secure.py")
    print()


if __name__ == '__main__':
    test_loading()
