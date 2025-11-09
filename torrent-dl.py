#!/usr/bin/env python3
"""
Simple CLI Torrent Downloader
Usage: python3 torrent-dl.py <torrent_file> [download_directory]
"""

import libtorrent as lt
import sys
import time
import os


def format_size(bytes):
    """Convert bytes to human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.2f} PB"


def format_time(seconds):
    """Convert seconds to human-readable format"""
    if seconds < 0:
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


def download_torrent(torrent_file, download_path="."):
    """Download a torrent file and show progress"""

    # Validate torrent file exists
    if not os.path.exists(torrent_file):
        print(f"Error: Torrent file '{torrent_file}' not found")
        return False

    # Create download directory if it doesn't exist
    os.makedirs(download_path, exist_ok=True)

    print(f"Starting download...")
    print(f"Torrent file: {torrent_file}")
    print(f"Download path: {os.path.abspath(download_path)}")
    print("-" * 70)

    # Create session with settings
    ses = lt.session()
    settings = ses.get_settings()
    settings['listen_interfaces'] = '0.0.0.0:6881'
    ses.apply_settings(settings)

    # Add torrent
    info = lt.torrent_info(torrent_file)
    h = ses.add_torrent({
        'ti': info,
        'save_path': download_path
    })

    # Get initial status
    s = h.status()
    print(f"Downloading: {s.name}")
    print(f"Total size: {format_size(info.total_size())}")
    print(f"Files: {info.num_files()}")
    print("-" * 70)

    # Download loop
    while True:
        s = h.status()
        if s.is_seeding:
            break

        # Calculate stats
        progress = s.progress * 100
        download_rate = s.download_rate / 1000  # KB/s
        upload_rate = s.upload_rate / 1000  # KB/s
        num_peers = s.num_peers

        # Calculate ETA
        if download_rate > 0:
            remaining_bytes = info.total_size() * (1 - s.progress)
            eta = remaining_bytes / (download_rate * 1000)
        else:
            eta = -1

        # Progress bar
        bar_length = 40
        filled = int(bar_length * s.progress)
        bar = '█' * filled + '░' * (bar_length - filled)

        # Print status (using \r to overwrite the same line)
        status_line = (
            f"\r[{bar}] {progress:.1f}% | "
            f"↓ {download_rate:.1f} KB/s | "
            f"↑ {upload_rate:.1f} KB/s | "
            f"Peers: {num_peers} | "
            f"ETA: {format_time(eta)}"
        )
        print(status_line, end='', flush=True)

        time.sleep(1)

    print("\n" + "-" * 70)
    print("Download complete!")
    print(f"Saved to: {os.path.abspath(download_path)}")

    # Ask if user wants to keep seeding
    print("\nSeeding... Press Ctrl+C to stop and exit.")
    try:
        while True:
            s = h.status()
            upload_rate = s.upload_rate / 1000
            print(f"\rSeeding: ↑ {upload_rate:.1f} KB/s | Peers: {s.num_peers}  ",
                  end='', flush=True)
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopping...")
        return True


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python3 torrent-dl.py <torrent_file> [download_directory]")
        print("\nExample:")
        print("  python3 torrent-dl.py ubuntu.torrent")
        print("  python3 torrent-dl.py ubuntu.torrent ~/Downloads")
        sys.exit(1)

    torrent_file = sys.argv[1]
    download_path = sys.argv[2] if len(sys.argv) > 2 else "."

    try:
        download_torrent(torrent_file, download_path)
    except KeyboardInterrupt:
        print("\n\nDownload cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
