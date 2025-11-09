#!/usr/bin/env python3
"""
Cleanup Resume Data - Remove corrupted or empty resume files
"""

import os
import sys

def cleanup_resume_data():
    """Clean up corrupted resume files"""
    resume_dir = os.path.expanduser("~/.config/torrent-downloader/resume")

    print("=" * 70)
    print("Resume Data Cleanup Tool")
    print("=" * 70)
    print()

    if not os.path.exists(resume_dir):
        print(f"✓ No resume directory found - nothing to clean")
        return

    print(f"Checking: {resume_dir}")
    print()

    # Find corrupted files
    corrupted_files = []
    valid_files = []

    for filename in sorted(os.listdir(resume_dir)):
        filepath = os.path.join(resume_dir, filename)
        size = os.path.getsize(filepath)

        if filename.endswith('.fastresume'):
            # Resume files should be at least 100 bytes for real data
            if size < 10:
                corrupted_files.append((filename, size, "too small"))
            else:
                valid_files.append((filename, size))

        elif filename.endswith('.torrent'):
            # Torrent files should be at least 100 bytes
            if size < 100:
                corrupted_files.append((filename, size, "too small"))
            else:
                valid_files.append((filename, size))

    # Show results
    if corrupted_files:
        print(f"Found {len(corrupted_files)} corrupted file(s):")
        print()
        for filename, size, reason in corrupted_files:
            print(f"  ✗ {filename}")
            print(f"    Size: {size} bytes ({reason})")
        print()

        # Ask for confirmation
        response = input("Delete these corrupted files? [y/N]: ").strip().lower()

        if response in ['y', 'yes']:
            deleted = 0
            for filename, size, reason in corrupted_files:
                filepath = os.path.join(resume_dir, filename)
                try:
                    os.remove(filepath)
                    print(f"  ✓ Deleted: {filename}")
                    deleted += 1
                except Exception as e:
                    print(f"  ✗ Failed to delete {filename}: {e}")

            print()
            print(f"Deleted {deleted} corrupted file(s)")
        else:
            print("Cancelled - no files deleted")
    else:
        print("✓ No corrupted files found")

    if valid_files:
        print()
        print(f"Valid files ({len(valid_files)}):")
        for filename, size in valid_files:
            print(f"  ✓ {filename} ({size} bytes)")

    print()
    print("=" * 70)


if __name__ == '__main__':
    try:
        cleanup_resume_data()
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
