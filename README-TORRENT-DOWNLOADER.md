# 🌐 Torrent Downloader Suite

A complete set of torrent downloaders for Linux, from simple CLI to full-featured GUI!

## 🚀 Quick Start

### For Beginners (GUI):
```bash
python3 ~/torrent-dl-gui.py
```
or search for "Torrent Downloader" in your application menu!

### For Command Line Users:
```bash
# Simple download
python3 ~/torrent-dl.py myfile.torrent

# Advanced with options
python3 ~/torrent-dl-enhanced.py -d ~/Downloads myfile.torrent
```

---

## 📦 What's Included

### 1. 🖼️ GUI Version (RECOMMENDED)
**File:** `torrent-dl-gui.py`

A beautiful graphical application with:
- Point-and-click interface
- Drag & drop torrent files
- Magnet link support
- Multiple simultaneous downloads
- Bandwidth controls
- Desktop notifications
- Progress tracking table

**Launch:** `python3 ~/torrent-dl-gui.py`

---

### 2. 🖥️ Simple CLI Version
**File:** `torrent-dl.py`

Basic command-line downloader for quick tasks.
- Single torrent downloads
- Real-time progress bar
- Speed and peer stats

**Usage:** `python3 ~/torrent-dl.py file.torrent ~/Downloads`

---

### 3. ⚡ Enhanced CLI Version
**File:** `torrent-dl-enhanced.py`

Advanced CLI with all features:
- Magnet links
- Multiple torrents
- Resume capability
- Better peer discovery

**Usage:** `python3 ~/torrent-dl-enhanced.py file1.torrent file2.torrent`

---

## 🎯 Common Tasks

### Download a torrent file (GUI)
1. Open Torrent Downloader
2. Click "Browse..."
3. Select your .torrent file
4. Click anywhere to start!

### Download from magnet link (GUI)
1. Copy the magnet link
2. Open Torrent Downloader
3. Paste in "Magnet Link" field
4. Click "Add"

### Set speed limits (GUI)
1. Go to Settings section
2. Enter limits in KB/s (0 = unlimited)
3. Click "Apply Limits"

### Download from command line
```bash
# Basic
python3 ~/torrent-dl.py ubuntu.torrent

# With custom directory
python3 ~/torrent-dl.py ubuntu.torrent ~/Downloads

# Multiple files
python3 ~/torrent-dl-enhanced.py file1.torrent file2.torrent file3.torrent

# Magnet link
python3 ~/torrent-dl-enhanced.py "magnet:?xt=urn:btih:..."
```

---

## 📚 Documentation

**Full Guide:** See `TORRENT_DOWNLOADER_GUIDE.md` for detailed documentation

**Test Script:** Run `./test-downloader.sh` to test all versions

---

## ✨ Features Comparison

| Feature | GUI | Simple CLI | Enhanced CLI |
|---------|-----|------------|--------------|
| Graphical Interface | ✅ | ❌ | ❌ |
| .torrent files | ✅ | ✅ | ✅ |
| Magnet links | ✅ | ❌ | ✅ |
| Multiple downloads | ✅ | ❌ | ✅ |
| Bandwidth limits | ✅ | ❌ | ❌ |
| Desktop notifications | ✅ | ❌ | ❌ |
| Resume downloads | ✅ | ❌ | ✅ |
| Progress tracking | ✅ | ✅ | ✅ |
| Easy to use | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ |

---

## 🛠️ Installation Summary

All dependencies are already installed:
- ✅ Python 3.12
- ✅ libtorrent (torrent library)
- ✅ tkinter (GUI toolkit)
- ✅ notify-send (notifications)

---

## 🎓 What You Learned

By creating this project, you learned about:
1. **Python programming** - Functions, classes, threading
2. **GUI development** - tkinter, event handling, layouts
3. **Network protocols** - BitTorrent, DHT, peer discovery
4. **Linux integration** - Desktop files, notifications, bash scripts
5. **Software architecture** - CLI vs GUI, modularity, user experience

---

## 🔧 Customization

Want to customize? All scripts are in your home directory:
- `~/torrent-dl.py` - Simple CLI
- `~/torrent-dl-enhanced.py` - Enhanced CLI
- `~/torrent-dl-gui.py` - GUI version

Edit them with any text editor!

---

## 💡 Tips

1. **Legal Content Only**: Download legal torrents (Linux ISOs, Creative Commons media, etc.)
2. **Seed Back**: Help others by seeding after downloading
3. **Port Forwarding**: Forward port 6881 for better speeds
4. **Firewall**: Make sure port 6881 isn't blocked
5. **Bandwidth**: Set limits if you need internet for other tasks

---

## 🆘 Troubleshooting

**GUI won't open?**
```bash
python3 ~/torrent-dl-gui.py
```
Check the terminal for errors.

**No peers connecting?**
- Wait 30 seconds for DHT to bootstrap
- Check your internet connection
- Try a more popular torrent

**Slow downloads?**
- Popular torrents = more peers = faster
- Check your internet speed
- Try different torrents

**Need help?**
Read the full guide: `less ~/TORRENT_DOWNLOADER_GUIDE.md`

---

## 🎉 Next Steps

Your torrent downloader is complete! You can:
1. **Use it daily** - Download Linux ISOs, open source software
2. **Customize it** - Edit the code to add features
3. **Share it** - Teach others how to build one
4. **Build more** - Try creating other Linux tools!

**Enjoy your new torrent downloader!** 🚀
