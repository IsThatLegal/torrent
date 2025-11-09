# Torrent Downloader Guide

You now have THREE torrent downloaders:

## 1. GUI Version (`torrent-dl-gui.py`) ⭐ RECOMMENDED
Beautiful graphical interface - perfect for most users!

### Usage:
```bash
python3 torrent-dl-gui.py
# OR
./launch-torrent-gui.sh
# OR search for "Torrent Downloader" in your application menu
```

### Features:
- ✓ **Easy-to-use graphical interface**
- ✓ **Browse for .torrent files with file picker**
- ✓ **Paste magnet links directly**
- ✓ **Download multiple torrents simultaneously**
- ✓ **Live progress tracking in a table**
- ✓ **Bandwidth limiting controls** (set download/upload speed limits)
- ✓ **Desktop notifications** when downloads complete
- ✓ **Select custom download directory**
- ✓ **Remove or clear completed torrents**
- ✓ **Real-time speed and peer information**

### How to Use:
1. Launch the application
2. Click "Browse..." to select a .torrent file, OR paste a magnet link
3. Choose where to save files (default: ~/Downloads/torrents)
4. Click "Add" to start downloading
5. Monitor progress in the table
6. Set bandwidth limits if needed (optional)
7. Get a notification when complete!

### Screenshots/Features:
- **Add Torrent**: Browse for files or paste magnet links
- **Active Downloads Table**: See all downloads with progress, speed, and status
- **Bandwidth Controls**: Limit download/upload speeds (KB/s)
- **Status Bar**: See what's happening at a glance

---

## 2. Simple CLI Version (`torrent-dl.py`)
Basic torrent downloader - perfect for quick downloads.

### Usage:
```bash
python3 torrent-dl.py <torrent_file> [download_directory]
```

### Examples:
```bash
# Download to current directory
python3 torrent-dl.py ubuntu.torrent

# Download to specific directory
python3 torrent-dl.py ubuntu.torrent ~/Downloads
```

### Features:
- ✓ Download .torrent files
- ✓ Real-time progress bar
- ✓ Download/upload speed display
- ✓ Peer count and ETA
- ✓ Automatic seeding after download

---

## 3. Enhanced CLI Version (`torrent-dl-enhanced.py`)
Advanced torrent downloader with all the bells and whistles.

### Usage:
```bash
python3 torrent-dl-enhanced.py [OPTIONS] <torrent(s)>
```

### Features:
- ✓ Download .torrent files
- ✓ **Magnet link support**
- ✓ **Resume interrupted downloads**
- ✓ **Download multiple torrents simultaneously**
- ✓ Better error handling
- ✓ DHT, LSD, UPnP, and NAT-PMP support for better peer discovery
- ✓ Clean multi-torrent status display
- ✓ Status indicators (✓ Seeding, ↓ Downloading, 🔍 Checking, ⏸ Paused)

### Examples:

#### Single torrent file
```bash
python3 torrent-dl-enhanced.py ubuntu.torrent
```

#### With magnet link
```bash
python3 torrent-dl-enhanced.py "magnet:?xt=urn:btih:..."
```

#### Custom download directory
```bash
python3 torrent-dl-enhanced.py -d ~/Downloads ubuntu.torrent
```

#### Multiple torrents at once
```bash
python3 torrent-dl-enhanced.py file1.torrent file2.torrent file3.torrent
```

#### Mix of torrent files and magnet links
```bash
python3 torrent-dl-enhanced.py ubuntu.torrent "magnet:?xt=..." debian.torrent
```

#### Don't seed after download
```bash
python3 torrent-dl-enhanced.py --no-seed ubuntu.torrent
```

### Options:
- `-d DIRECTORY, --directory DIRECTORY` - Download directory (default: ./torrents)
- `--no-seed` - Exit after download without seeding
- `--resume-dir RESUME_DIR` - Directory for resume data (default: .torrent_resume)
- `-h, --help` - Show help message

---

## Resume Functionality

The enhanced version automatically saves progress. If a download is interrupted:

1. Simply run the same command again
2. It will detect existing files and resume from where it left off
3. No need to start from scratch!

---

## Making It Easier to Use

### Create aliases in your ~/.bashrc:
```bash
echo 'alias torrent-dl="python3 ~/torrent-dl.py"' >> ~/.bashrc
echo 'alias torrent-dl-pro="python3 ~/torrent-dl-enhanced.py"' >> ~/.bashrc
source ~/.bashrc
```

Now you can use:
```bash
torrent-dl ubuntu.torrent
torrent-dl-pro -d ~/Downloads file1.torrent file2.torrent
```

---

## Tips

1. **Legal torrents**: Always download legal content. Good sources:
   - Linux distributions (Ubuntu, Debian, Fedora)
   - Creative Commons movies/music
   - Open source software
   - Public domain content

2. **Seeding**: Keep seeding after download to help others (be a good peer!)

3. **Port forwarding**: For better speeds, forward port 6881 in your router

4. **Multiple downloads**: The enhanced version handles multiple torrents efficiently

5. **Magnet links**: Just paste the magnet link in quotes

---

## Test Files

To test, you can use these legal torrents:

### Big Buck Bunny (Creative Commons movie - already downloaded)
```bash
# Torrent file
python3 torrent-dl-enhanced.py big-buck-bunny.torrent

# Magnet link
python3 torrent-dl-enhanced.py "magnet:?xt=urn:btih:dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c&dn=Big+Buck+Bunny"
```

### Ubuntu Linux
Download from: https://ubuntu.com/download/alternative-downloads

---

## Troubleshooting

**No peers connecting?**
- Check your internet connection
- Make sure port 6881 isn't blocked by firewall
- DHT takes a few seconds to bootstrap

**Slow downloads?**
- Popular torrents are faster (more peers)
- Older/rare torrents may have few peers
- Your ISP might throttle torrent traffic

**Download stuck?**
- Press Ctrl+C and restart
- Resume functionality will continue from where it stopped
