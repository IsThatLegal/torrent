#!/usr/bin/env python3
"""
Check Resume Data - Diagnostic Tool
Checks what torrents are saved and can be resumed
"""

import os
import sys

def check_resume_data():
    """Check resume data directory"""
    resume_dir = os.path.expanduser("~/.config/torrent-downloader/resume")

    print("=" * 70)
    print("Resume Data Diagnostic Tool")
    print("=" * 70)
    print()

    # Check if directory exists
    if not os.path.exists(resume_dir):
        print(f"❌ Resume directory does not exist: {resume_dir}")
        print()
        print("This is normal if you haven't downloaded anything yet.")
        return

    print(f"✓ Resume directory exists: {resume_dir}")
    print()

    # List all files
    files = sorted(os.listdir(resume_dir))

    if not files:
        print("No resume files found.")
        print()
        print("This means:")
        print("  - No torrents have been added yet")
        print("  - OR torrents were added but app was closed before saving")
        print("  - OR resume files were deleted")
        return

    # Group files by info hash
    torrents = {}
    for file in files:
        if file.endswith('.fastresume'):
            info_hash = file.replace('.fastresume', '')
            if info_hash not in torrents:
                torrents[info_hash] = {'resume': False, 'torrent': False, 'magnet': False}
            torrents[info_hash]['resume'] = True
        elif file.endswith('.torrent'):
            info_hash = file.replace('.torrent', '')
            if info_hash not in torrents:
                torrents[info_hash] = {'resume': False, 'torrent': False, 'magnet': False}
            torrents[info_hash]['torrent'] = True
        elif file.endswith('.magnet'):
            info_hash = file.replace('.magnet', '')
            if info_hash not in torrents:
                torrents[info_hash] = {'resume': False, 'torrent': False, 'magnet': False}
            torrents[info_hash]['magnet'] = True

    # Display results
    print(f"Found {len(torrents)} torrent(s) with resume data:")
    print()

    for idx, (info_hash, data) in enumerate(torrents.items(), 1):
        print(f"Torrent {idx}:")
        print(f"  Info Hash: {info_hash}")

        # Check what files exist
        print(f"  Files:")
        if data['resume']:
            print(f"    ✓ .fastresume (resume data)")
        else:
            print(f"    ✗ .fastresume (missing - can't resume!)")

        if data['torrent']:
            print(f"    ✓ .torrent (full metadata)")
        else:
            print(f"    ⚠ .torrent (missing)")

        if data['magnet']:
            print(f"    ✓ .magnet (magnet link)")
        else:
            print(f"    ⚠ .magnet (missing)")

        # Try to load torrent name
        name = None
        if data['torrent']:
            try:
                import libtorrent as lt
                torrent_file = os.path.join(resume_dir, f"{info_hash}.torrent")
                ti = lt.torrent_info(torrent_file)
                name = ti.name()
                size = ti.total_size()

                print(f"  Name: {name}")
                print(f"  Size: {format_size(size)}")
            except Exception as e:
                print(f"  Name: Unable to read ({e})")
        elif data['magnet']:
            try:
                magnet_file = os.path.join(resume_dir, f"{info_hash}.magnet")
                with open(magnet_file, 'r') as f:
                    magnet = f.read().strip()

                import libtorrent as lt
                params = lt.parse_magnet_uri(magnet)
                if params.name:
                    print(f"  Name: {params.name}")
                else:
                    print(f"  Name: Unknown (no metadata)")
            except Exception as e:
                print(f"  Name: Unable to read ({e})")

        # Can this be resumed?
        if data['resume'] and (data['torrent'] or data['magnet']):
            print(f"  Status: ✓ Can be resumed")
        elif data['resume']:
            print(f"  Status: ⚠ Can be resumed but missing metadata")
        else:
            print(f"  Status: ✗ Cannot be resumed (missing .fastresume)")

        print()

    # Summary
    print("=" * 70)
    print("Summary:")
    print("=" * 70)

    resumable = sum(1 for t in torrents.values() if t['resume'])
    with_metadata = sum(1 for t in torrents.values() if t['torrent'])

    print(f"Total torrents: {len(torrents)}")
    print(f"Resumable: {resumable}")
    print(f"With full metadata: {with_metadata}")
    print()

    if resumable == 0:
        print("⚠️  No torrents can be resumed!")
        print()
        print("Possible reasons:")
        print("  1. App was closed before torrents were added")
        print("  2. Resume data was not saved properly")
        print("  3. Resume files were deleted")
    elif with_metadata < resumable:
        print(f"⚠️  {resumable - with_metadata} torrent(s) missing metadata")
        print()
        print("These torrents can still resume but will need to fetch")
        print("metadata from peers again.")
    else:
        print("✓ All torrents can be resumed with full metadata!")

    print()
    print("To test resume functionality:")
    print("  python3 torrent-dl-gui-secure.py")
    print()


def format_size(bytes_count):
    """Format bytes to human readable"""
    for unit in ['B', 'KiB', 'MiB', 'GiB', 'TiB']:
        if bytes_count < 1024.0:
            return f"{bytes_count:.2f} {unit}"
        bytes_count /= 1024.0
    return f"{bytes_count:.2f} PiB"


if __name__ == '__main__':
    try:
        check_resume_data()
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
