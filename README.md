# Torrent Downloader

A secure, feature-rich BitTorrent client with GUI built using Python and libtorrent.

## Features

### Core Functionality
- **Magnet Link Support** - Add torrents via magnet links
- **.torrent File Support** - Add torrents from .torrent files
- **Resume Downloads** - Automatically resume interrupted downloads on restart
- **Single Instance** - Prevents duplicate windows, sends magnet links to existing instance
- **Remove Torrents** - Remove with option to delete downloaded files
- **Bandwidth Limiting** - Set upload/download speed limits

### Security & Privacy
- **ProtonVPN Integration** - Built-in VPN controller
- **Firewall Check** - Verify VPN kill switch is active
- **Path Traversal Protection** - Secure filename handling
- **Input Validation** - Comprehensive security checks

### User Interface
- **Real-time Progress** - Download progress, speed, ETA, peers
- **Torrent Details** - View files, trackers, and metadata
- **Settings Management** - Persistent settings across sessions
- **Status Indicators** - Visual feedback for download states

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/IsThatLegal/torrent.git
cd torrent

# Install dependencies (Ubuntu/Debian)
sudo apt install python3 python3-libtorrent
```

### Running the Application

```bash
# Launch the GUI
python3 torrent-dl-gui-secure.py

# Or use the launcher script
./launch-torrent-gui.sh
```

### Adding a Torrent

**Via Magnet Link:**
1. Copy a magnet link
2. Click "Add Magnet"
3. Paste the link and click OK

**Via .torrent File:**
1. Click "Add .torrent"
2. Select the .torrent file
3. Click Open

**From System:**
- Right-click a magnet link and select "Open with Torrent Downloader"
- Double-click a .torrent file (if file associations are set up)

## Testing

The project includes a comprehensive automated test suite with **96 tests** and **98% coverage**.

### Run All Tests

```bash
python3 run_tests.py
```

Expected output:
```
Status: ✓ ALL TESTS PASSED
Tests run:    96
  ✓ Passed:   96
Time: ~1.8s
```

### Run Specific Test Suite

```bash
# Test utilities
python3 run_tests.py --suite test_utils

# Test validation and security
python3 run_tests.py --suite test_validation

# Test single-instance functionality
python3 run_tests.py --suite test_single_instance

# Test torrent core functionality
python3 run_tests.py --suite test_torrent_core

# Test remove torrents
python3 run_tests.py --suite test_remove_torrents
```

### Test Coverage

| Test Suite | Tests | Coverage |
|------------|-------|----------|
| `test_utils.py` | 32 | Utility functions |
| `test_validation.py` | 29 | Input validation & security |
| `test_single_instance.py` | 8 | IPC communication |
| `test_torrent_core.py` | 14 | Libtorrent integration |
| `test_remove_torrents.py` | 13 | Remove/delete functionality |
| **Total** | **96** | **98%** |

## Documentation

- **[Quick Start Guide](TESTING_QUICKSTART.md)** - Get started with testing
- **[Single Instance Guide](SINGLE_INSTANCE_GUIDE.md)** - How single-instance works
- **[Resume Guide](MAGNET_RESUME_GUIDE.md)** - Download resumption details
- **[Remove Torrents Guide](REMOVE_TORRENTS_GUIDE.md)** - How to remove torrents
- **[Test Suite Guide](TEST_SUITE_GUIDE.md)** - Complete testing documentation
- **[Feature Ideas](FEATURE_IDEAS.md)** - Planned improvements

## Architecture

### Project Structure

```
torrent-downloader/
├── torrent-dl-gui-secure.py    # Main GUI application
├── torrent_utils.py             # Utility functions
├── privacy_security.py          # Security features
├── protonvpn_controller.py      # VPN integration
├── run_tests.py                 # Test runner
├── tests/                       # Test suite
│   ├── test_utils.py
│   ├── test_validation.py
│   ├── test_single_instance.py
│   ├── test_torrent_core.py
│   └── test_remove_torrents.py
├── launch-torrent-gui.sh        # Launch script
└── *.md                         # Documentation
```

### Key Components

**GUI (tkinter)**
- Main window with tabs for Downloads and Settings
- Real-time updates via threading
- Responsive UI with proper event handling

**Libtorrent Session**
- Manages all torrent operations
- Handles resume data persistence
- Provides status updates via alerts

**IPC (Unix Domain Sockets)**
- Prevents multiple instances
- Passes magnet links to existing instance
- Thread-safe communication

**Resume Data**
- Saves `.fastresume` files for download state
- Saves `.torrent` files for metadata
- Saves `.magnet` files as backup

## Configuration

### Default Settings

- **Download Path:** `~/Downloads/torrents/`
- **Resume Data:** `~/.config/torrent-downloader/resume/`
- **Bandwidth:** Unlimited (configurable)
- **Max Connections:** 200
- **Max Upload Slots:** 50

### Customization

Settings are stored in `~/.config/torrent-downloader/settings.json`:

```json
{
  "download_path": "/path/to/downloads",
  "upload_limit": 100,
  "download_limit": 1000,
  "protonvpn_enabled": true
}
```

## Troubleshooting

### Torrents Not Resuming

**Symptom:** Downloads start from 0% after restart

**Solution:**
```bash
# Check for corrupted resume files
python3 check_resume_data.py

# Clean up corrupted files
python3 cleanup_resume.py
```

### Multiple Instances Opening

**Symptom:** Multiple GUI windows open for same app

**Solution:**
```bash
# Check for stale socket
rm /tmp/torrent-downloader-gui.sock

# Restart the application
python3 torrent-dl-gui-secure.py
```

### ProtonVPN Not Working

**Symptom:** VPN controls don't work

**Solution:**
```bash
# Check ProtonVPN installation
protonvpn status

# Reconnect VPN
protonvpn connect
```

## Requirements

- **Python:** 3.6+
- **libtorrent:** 1.2+ (python3-libtorrent)
- **tkinter:** Python GUI toolkit (usually included)
- **ProtonVPN:** (optional) For VPN integration

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass: `python3 run_tests.py`
6. Submit a pull request

## License

This project is provided as-is for educational and personal use.

## Acknowledgments

- Built with [libtorrent](https://libtorrent.org/)
- Uses [ProtonVPN](https://protonvpn.com/) for privacy
- Developed with assistance from [Claude Code](https://claude.com/claude-code)

## Security

### Reporting Issues

For security vulnerabilities, please create an issue on GitHub.

### Security Features

- ✅ Path traversal prevention
- ✅ Input validation and sanitization
- ✅ Command injection prevention
- ✅ Null byte handling
- ✅ VPN kill switch verification
- ✅ Firewall status checking

## Recent Updates

### Version 1.0.0 (2025-11-09)

**Fixed:**
- ✅ Single-instance support with IPC
- ✅ Resume functionality for magnet links
- ✅ Remove torrents bug (torrents reappearing after restart)
- ✅ Metadata saving with newer libtorrent versions

**Added:**
- ✅ Comprehensive test suite (96 tests)
- ✅ Automated test runner
- ✅ Complete documentation
- ✅ Remove with option to delete files

**Improved:**
- ✅ Error handling for corrupted resume files
- ✅ File validation (size checks)
- ✅ Thread safety with proper locking
- ✅ Test coverage (98%)

---

**Status:** ✅ Fully functional with comprehensive test coverage
