#!/usr/bin/env python3
"""
Enhanced CLI Torrent Downloader
Supports: .torrent files, magnet links, resume, and multiple downloads

Usage:
  python3 torrent-dl-enhanced.py <torrent_file_or_magnet> [download_directory]
  python3 torrent-dl-enhanced.py <file1> <file2> <file3> [download_directory]
"""

import libtorrent as lt
import sys
import time
import os
import argparse


def format_size(bytes):
    """Convert bytes to human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.2f} PB"


def format_time(seconds):
    """Convert seconds to human-readable format"""
    if seconds < 0 or seconds == float('inf'):
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


def is_magnet_link(string):
    """Check if string is a magnet link"""
    return string.startswith('magnet:?')


def get_torrent_info(handle, timeout=30):
    """Wait for torrent metadata to be available (for magnet links)"""
    print("Fetching metadata from peers...")
    start_time = time.time()

    while True:
        s = handle.status()
        if s.has_metadata:
            break
        time.sleep(0.5)
        if time.time() - start_time > timeout:
            raise Exception("Timeout waiting for metadata")
        print(".", end='', flush=True)

    print(" Done!")
    return handle.torrent_file()


class TorrentDownloader:
    """Manages torrent downloads with resume capability"""

    def __init__(self, download_path=".", resume_data_path=".torrent_resume"):
        self.download_path = os.path.abspath(download_path)
        self.resume_data_path = os.path.abspath(resume_data_path)
        os.makedirs(self.download_path, exist_ok=True)
        os.makedirs(self.resume_data_path, exist_ok=True)

        # Create session with resume support
        self.ses = lt.session()
        settings = self.ses.get_settings()
        settings['listen_interfaces'] = '0.0.0.0:6881'
        settings['enable_dht'] = True
        settings['enable_lsd'] = True  # Local service discovery
        settings['enable_upnp'] = True  # UPnP port mapping
        settings['enable_natpmp'] = True  # NAT-PMP port mapping
        self.ses.apply_settings(settings)

        # DHT bootstrap for better peer discovery
        # DHT routers are automatically bootstrapped by libtorrent

        self.handles = []
        self.metadata_saved = {}  # Track which magnets have saved metadata

    def add_torrent(self, torrent_input):
        """Add a torrent file or magnet link to download queue with resume support"""
        try:
            params = {
                'save_path': self.download_path,
                'storage_mode': lt.storage_mode_t.storage_mode_sparse,
            }

            info = None
            info_hash = None

            if is_magnet_link(torrent_input):
                print(f"Adding magnet link...")
                magnet_params = lt.parse_magnet_uri(torrent_input)
                params.update(magnet_params)
                info_hash = str(magnet_params.info_hash)

                # Check for existing resume data and metadata
                resume_file = os.path.join(self.resume_data_path, f"{info_hash}.fastresume")
                torrent_file = os.path.join(self.resume_data_path, f"{info_hash}.torrent")

                has_resume = os.path.exists(resume_file)
                has_metadata = os.path.exists(torrent_file)

                if has_resume and has_metadata:
                    print(f"  ⚡ Resume data found - loading saved torrent")
                    # Load the full torrent info
                    info = lt.torrent_info(torrent_file)
                    params['ti'] = info

                    # Load resume data
                    with open(resume_file, 'rb') as f:
                        params['resume_data'] = f.read()

                    handle = self.ses.add_torrent(params)

                    # Force recheck to detect existing files
                    print(f"  🔍 Checking for existing files...")
                    handle.force_recheck()

                    # Mark metadata as already saved
                    self.metadata_saved[info_hash] = True

                elif has_metadata:
                    # Have metadata but no resume data - still useful
                    print(f"  📦 Saved torrent found - loading")
                    info = lt.torrent_info(torrent_file)
                    params['ti'] = info

                    handle = self.ses.add_torrent(params)

                    # Force recheck to detect existing files
                    print(f"  🔍 Checking for existing files...")
                    handle.force_recheck()

                    # Mark metadata as already saved
                    self.metadata_saved[info_hash] = True

                else:
                    # No saved data - need to fetch metadata
                    print(f"  📥 Fetching metadata from peers...")
                    handle = self.ses.add_torrent(params)
                    info = get_torrent_info(handle)

            else:
                # Validate torrent file exists
                if not os.path.exists(torrent_input):
                    raise FileNotFoundError(f"Torrent file '{torrent_input}' not found")

                print(f"Adding torrent file: {torrent_input}")
                info = lt.torrent_info(torrent_input)
                params['ti'] = info
                info_hash = str(info.info_hash())

                # Check for existing resume data
                resume_file = os.path.join(self.resume_data_path, f"{info_hash}.fastresume")
                if os.path.exists(resume_file):
                    print(f"  ⚡ Resume data found - checking existing files")
                    with open(resume_file, 'rb') as f:
                        params['resume_data'] = f.read()
                else:
                    # No resume data, but force checking of existing files
                    print(f"  🔍 Checking for existing files in download directory")

                handle = self.ses.add_torrent(params)

            # Force recheck to detect existing files
            print(f"  ⏳ Scanning existing files (this may take a moment)...")
            handle.force_recheck()

            self.handles.append(handle)

            # Get status to display info
            s = handle.status()
            total_size = info.total_size() if hasattr(info, 'total_size') else 0
            num_files = info.num_files() if hasattr(info, 'num_files') else 0

            print(f"  Name: {s.name}")
            print(f"  Size: {format_size(total_size)}")
            print(f"  Files: {num_files}")

            # Wait a moment for initial file checking
            time.sleep(2)
            s = handle.status()

            if s.state == lt.torrent_status.checking_files:
                print(f"  📊 File checking in progress...")
            elif s.progress > 0:
                print(f"  ✅ Found existing data: {s.progress * 100:.1f}% complete")

            print("-" * 70)
            return True

        except Exception as e:
            print(f"Error adding torrent: {e}")
            import traceback
            traceback.print_exc()
            return False

    def save_metadata_if_ready(self, handle):
        """Save torrent metadata to file if it has arrived (for magnet links)"""
        info_hash = str(handle.status().info_hash)

        # Skip if already saved
        if info_hash in self.metadata_saved:
            return

        # Check if we have metadata
        if handle.status().has_metadata and handle.torrent_file():
            try:
                torrent_file = os.path.join(self.resume_data_path, f"{info_hash}.torrent")

                # Save the .torrent file
                ti = handle.torrent_file()
                try:
                    ct = lt.create_torrent(ti)
                    torrent_data = lt.bencode(ct.generate())
                    with open(torrent_file, 'wb') as f:
                        f.write(torrent_data)
                    print(f"\n✅ Saved metadata for {handle.status().name}")
                except Exception as e:
                    print(f"\n⚠️  Could not save .torrent file: {e}")
                self.metadata_saved[info_hash] = True
            except Exception as e:
                print(f"\n⚠️  Failed to save metadata: {e}")

    def download_all(self, seed_after=True):
        """Download all torrents in queue"""
        if not self.handles:
            print("No torrents to download")
            return

        print(f"\nDownloading {len(self.handles)} torrent(s)...\n")

        try:
            # Download loop
            all_complete = False
            while not all_complete:
                all_complete = True

                # Clear screen for cleaner output (optional)
                print("\033[2J\033[H", end='')  # ANSI clear screen

                for idx, h in enumerate(self.handles):
                    s = h.status()

                    # Save metadata if it arrived (for magnet links)
                    self.save_metadata_if_ready(h)

                    if not s.is_seeding:
                        all_complete = False

                    # Calculate stats
                    progress = s.progress * 100
                    download_rate = s.download_rate / 1000  # KB/s
                    upload_rate = s.upload_rate / 1000  # KB/s
                    num_peers = s.num_peers

                    # Calculate ETA
                    if download_rate > 0:
                        total_size = s.total_wanted
                        remaining_bytes = total_size * (1 - s.progress)
                        eta = remaining_bytes / (download_rate * 1000)
                    else:
                        eta = -1

                    # Progress bar
                    bar_length = 40
                    filled = int(bar_length * s.progress)
                    bar = '█' * filled + '░' * (bar_length - filled)

                    # Status indicator
                    if s.is_seeding:
                        status = "✓ Seeding"
                    elif s.paused:
                        status = "⏸ Paused"
                    elif s.state == lt.torrent_status.downloading:
                        status = "↓ Downloading"
                    elif s.state == lt.torrent_status.checking_files:
                        status = "🔍 Checking"
                    else:
                        status = "⏳ Queued"

                    # Print torrent status
                    print(f"[{idx+1}] {s.name[:45]}")
                    print(f"    [{bar}] {progress:.1f}%")
                    print(f"    {status} | ↓ {download_rate:.1f} KB/s | ↑ {upload_rate:.1f} KB/s | "
                          f"Peers: {num_peers} | ETA: {format_time(eta)}")
                    print()

                time.sleep(1)

            print("\n" + "=" * 70)
            print("All downloads complete!")
            print("=" * 70)

            # Save resume data
            self.save_resume_data()

            if seed_after:
                print("\nSeeding all torrents... Press Ctrl+C to stop and exit.")
                while True:
                    print("\033[2J\033[H", end='')  # Clear screen

                    for idx, h in enumerate(self.handles):
                        s = h.status()
                        upload_rate = s.upload_rate / 1000
                        print(f"[{idx+1}] {s.name[:50]}")
                        print(f"    Seeding: ↑ {upload_rate:.1f} KB/s | Peers: {s.num_peers}")
                        print()

                    time.sleep(1)

        except KeyboardInterrupt:
            print("\n\nStopping downloads...")
            self.save_resume_data()

    def save_resume_data(self):
        """Save resume data for all torrents"""
        print("Saving resume data...")

        # Request resume data for all torrents
        for h in self.handles:
            if h.is_valid():
                h.save_resume_data()

        # Wait for resume data alerts
        time.sleep(1)

        # Process alerts and save resume data
        alerts = self.ses.pop_alerts()
        saved_count = 0

        for alert in alerts:
            if isinstance(alert, lt.save_resume_data_alert):
                try:
                    torrent_status = alert.handle.status()
                    info_hash = str(torrent_status.info_hash)

                    # Save resume data to file
                    resume_file = os.path.join(self.resume_data_path, f"{info_hash}.fastresume")
                    with open(resume_file, 'wb') as f:
                        f.write(lt.bencode(alert.params))

                    # Also save the torrent file if available
                    if alert.handle.torrent_file():
                        torrent_file = os.path.join(self.resume_data_path, f"{info_hash}.torrent")
                        ti = alert.handle.torrent_file()
                        try:
                            ct = lt.create_torrent(ti)
                            torrent_data = lt.bencode(ct.generate())
                            with open(torrent_file, 'wb') as f:
                                f.write(torrent_data)
                        except Exception as e:
                            print(f"Could not save .torrent file: {e}")

                    saved_count += 1
                except Exception as e:
                    print(f"Error saving resume data: {e}")

        print(f"Resume data saved for {saved_count} torrent(s).")


def main():
    """Main function with enhanced argument parsing"""
    parser = argparse.ArgumentParser(
        description='Enhanced CLI Torrent Downloader',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download single torrent file
  %(prog)s ubuntu.torrent

  # Download using magnet link
  %(prog)s "magnet:?xt=urn:btih:..."

  # Download to specific directory
  %(prog)s ubuntu.torrent ~/Downloads

  # Download multiple torrents
  %(prog)s file1.torrent file2.torrent file3.torrent

  # Download and don't seed after
  %(prog)s --no-seed ubuntu.torrent
        """
    )

    parser.add_argument('torrents', nargs='+',
                        help='Torrent file(s), magnet link(s), or mix of both')
    parser.add_argument('-d', '--directory', default='./torrents',
                        help='Download directory (default: ./torrents)')
    parser.add_argument('--no-seed', action='store_true',
                        help='Exit after download without seeding')
    parser.add_argument('--resume-dir', default='.torrent_resume',
                        help='Directory for resume data (default: .torrent_resume)')

    args = parser.parse_args()

    try:
        # Initialize downloader
        downloader = TorrentDownloader(
            download_path=args.directory,
            resume_data_path=args.resume_dir
        )

        print("=" * 70)
        print("Enhanced Torrent Downloader")
        print("=" * 70)
        print(f"Download path: {downloader.download_path}")
        print("=" * 70)
        print()

        # Add all torrents to queue
        success_count = 0
        for torrent in args.torrents:
            if downloader.add_torrent(torrent):
                success_count += 1

        if success_count == 0:
            print("No valid torrents to download")
            sys.exit(1)

        # Start downloading
        downloader.download_all(seed_after=not args.no_seed)

    except KeyboardInterrupt:
        print("\n\nDownload cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
