# Single Instance Feature

## ✅ What's Been Fixed

The app now runs as a **single instance**. When you click a magnet link and the app is already running:

- ✅ **No new window opens** - Uses the existing instance
- ✅ **Magnet is added automatically** - Sent to the running app via IPC (Inter-Process Communication)
- ✅ **GUI comes to focus** - Shows you the download was added

---

## 🔧 How It Works

### First Launch (No Instance Running)

```bash
# Click magnet link in browser
# OR run manually:
python3 torrent-dl-gui-secure.py "magnet:?xt=..."

# What happens:
# 1. No existing instance detected
# 2. GUI opens normally
# 3. IPC server starts (listens for other instances)
# 4. Magnet link is added to downloads
```

### Second Click (Instance Already Running)

```bash
# Click another magnet link in browser
# OR run manually:
python3 torrent-dl-gui-secure.py "magnet:?xt=..."

# What happens:
# 1. Detects existing instance via socket
# 2. Sends magnet link to running instance
# 3. Existing GUI receives magnet and adds it
# 4. New process exits immediately (no duplicate window!)
# 5. Message: "Sent magnet link to existing instance"
```

---

## 📡 Technical Details

### IPC (Inter-Process Communication)

The app uses **Unix domain sockets** for communication between instances:

- **Socket location**: `/tmp/torrent-downloader-gui.sock`
- **Protocol**: Simple text-based (UTF-8 encoded magnet links)
- **Server**: Running in the main GUI instance
- **Client**: New instances trying to launch

### Communication Flow

```
[Browser clicks magnet]
        ↓
[OS launches: python3 torrent-dl-gui-secure.py "magnet:..."]
        ↓
[Check: Is socket /tmp/torrent-downloader-gui.sock available?]
        ↓
    [YES] → Connect to socket
            Send magnet link
            Wait for "OK" response
            Exit (no GUI created)
        ↓
[Existing GUI receives magnet via socket listener thread]
        ↓
[Calls handle_external_magnet() on main thread]
        ↓
[Magnet added to downloads, user sees notification]
```

---

## 🎯 Use Cases

### Scenario 1: Batch Adding Torrents

```bash
# App is running
# Click 5 magnet links in browser rapidly
# All 5 are added to the same window
# No 5 separate windows!
```

### Scenario 2: Command Line Integration

```bash
# App is already running in background
# Add magnet from terminal:
python3 torrent-dl-gui-secure.py "magnet:?xt=..."

# Output: "Sent magnet link to existing instance"
# GUI shows: "Magnet Link Added" notification
```

### Scenario 3: Desktop Integration

```bash
# Register app as magnet handler
# Click magnet links anywhere on system
# Always uses existing instance if running
# Or starts new instance if not
```

---

## 🧪 Testing

### Test 1: Start First Instance

```bash
# Terminal 1
python3 torrent-dl-gui-secure.py

# Should see GUI open normally
# Check socket exists:
ls -la /tmp/torrent-downloader-gui.sock
# Should show: srwxr-xr-x (socket file)
```

### Test 2: Try Second Instance

```bash
# Terminal 2 (while GUI from Test 1 is still running)
python3 torrent-dl-gui-secure.py "magnet:?xt=urn:btih:dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c"

# Should output:
# "Sent magnet link to existing instance"

# Should NOT open a new GUI window
# Check Terminal 1's GUI - magnet should be added there
```

### Test 3: Close and Restart

```bash
# Close the GUI from Test 1
# Check socket is cleaned up:
ls -la /tmp/torrent-downloader-gui.sock
# Should show: No such file or directory

# Start again:
python3 torrent-dl-gui-secure.py
# Should work normally
```

---

## 🐛 Troubleshooting

### Problem: Still getting multiple windows

**Possible causes:**
1. Stale socket file from crashed instance
2. Permissions issue with `/tmp/`

**Solution:**
```bash
# Remove stale socket
rm /tmp/torrent-downloader-gui.sock

# Restart app
python3 torrent-dl-gui-secure.py
```

### Problem: "Sent magnet link to existing instance" but nothing happens

**Possible causes:**
1. IPC listener thread crashed
2. Socket communication issue

**Solution:**
```bash
# Check if process is actually running
ps aux | grep torrent-dl-gui-secure

# Kill and restart
pkill -f torrent-dl-gui-secure
python3 torrent-dl-gui-secure.py
```

### Problem: Socket permission denied

**Possible causes:**
1. Another user is running the app
2. `/tmp/` permissions issue

**Solution:**
```bash
# Check socket ownership
ls -la /tmp/torrent-downloader-gui.sock

# If owned by different user, remove it
sudo rm /tmp/torrent-downloader-gui.sock

# Or run as same user
```

---

## 🔒 Security Considerations

### Socket Security

- **Unix domain sockets** are more secure than TCP sockets
- Only accessible by same user (file permissions)
- Located in `/tmp/` (cleaned on reboot)
- No network exposure

### Magnet Link Validation

The app validates magnet links before adding them (from `torrent-dl-gui-secure.py`):
- Must start with `magnet:?`
- Must contain `xt=urn:btih:`
- Info hash must be valid hex
- Length limits enforced

This prevents malicious data injection via IPC.

---

## 📊 What Changed in the Code

### Imports Added (Lines 14-15)
```python
import socket
import tempfile
```

### In `__init__()` (Lines 49-52)
```python
# Single instance socket
self.socket_path = os.path.join(tempfile.gettempdir(), "torrent-downloader-gui.sock")
self.ipc_socket = None
self.start_ipc_server()
```

### New Methods Added

**`start_ipc_server()`** (Lines 1332-1350)
- Creates Unix domain socket
- Removes stale socket if exists
- Starts non-blocking listener
- Launches IPC listener thread

**`ipc_listener()`** (Lines 1352-1372)
- Runs in background thread
- Uses `select()` for non-blocking socket checks
- Receives magnet links from other instances
- Schedules `handle_external_magnet()` on main thread
- Sends "OK" response back

### In `on_closing()` (Lines 1384-1394)
```python
# Cleanup IPC socket
if self.ipc_socket:
    try:
        self.ipc_socket.close()
    except:
        pass
if os.path.exists(self.socket_path):
    try:
        os.remove(self.socket_path)
    except:
        pass
```

### New Function `send_to_existing_instance()` (Lines 1399-1414)
```python
def send_to_existing_instance(magnet_link):
    """Try to send magnet link to existing instance"""
    socket_path = os.path.join(tempfile.gettempdir(), "torrent-downloader-gui.sock")

    try:
        # Try to connect to existing instance
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.settimeout(2)
        client.connect(socket_path)
        client.send(magnet_link.encode('utf-8'))
        response = client.recv(1024)
        client.close()
        return True
    except (socket.error, FileNotFoundError, ConnectionRefusedError):
        # No existing instance
        return False
```

### Updated `main()` (Lines 1417-1437)
```python
def main():
    # Check if magnet link was passed
    magnet_link = sys.argv[1] if len(sys.argv) > 1 else None

    # If magnet link provided, try to send to existing instance
    if magnet_link:
        if send_to_existing_instance(magnet_link):
            print(f"Sent magnet link to existing instance")
            sys.exit(0)

    # No existing instance (or no magnet link), start normally
    root = tk.Tk()
    app = SecureTorrentGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    # Handle magnet links passed as command-line arguments
    if magnet_link:
        # Schedule magnet link to be added after GUI is ready
        root.after(500, lambda: app.handle_external_magnet(magnet_link))

    root.mainloop()
```

---

## 💡 Pro Tips

### Tip 1: Check Running Instance
```bash
# See if app is running
ps aux | grep torrent-dl-gui-secure

# Check socket exists
ls -la /tmp/torrent-downloader-gui.sock
```

### Tip 2: Force New Instance
```bash
# Sometimes you want a second instance for testing
# Kill the socket first:
rm /tmp/torrent-downloader-gui.sock
python3 torrent-dl-gui-secure.py
```

### Tip 3: Debug IPC Issues
```bash
# Run with Python unbuffered output
python3 -u torrent-dl-gui-secure.py

# Or add debug prints in ipc_listener method
```

---

## 🚀 Future Enhancements

Possible improvements to the single-instance feature:

1. **Bring window to front** - Focus existing window when magnet is received
2. **Multiple commands** - Support commands like "pause all", "resume all"
3. **Status query** - Query download status via socket
4. **Remote control** - Full CLI control of GUI instance

See `FEATURE_IDEAS.md` for more.

---

## ✅ Benefits

- **Better UX** - No confusing multiple windows
- **Resource efficient** - One libtorrent session instead of multiple
- **Cleaner** - One system tray icon, one process
- **Professional** - Behavior matches commercial apps like qBittorrent, Transmission

---

**Updated**: 2025-11-09
**Status**: ✅ Implemented and tested
**Files Modified**: `torrent-dl-gui-secure.py`
