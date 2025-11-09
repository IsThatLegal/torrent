# Magnet Link Resume Functionality

## ✅ What's Been Fixed

Magnet links can now be resumed properly! When you download a torrent via magnet link, the app now:

1. **Saves metadata automatically** - When metadata arrives from peers, it's saved as a `.torrent` file
2. **Loads metadata on resume** - Next time you add the same magnet, it loads the saved metadata instantly
3. **Detects existing files** - Scans your download directory for partial files and resumes from where you left off

---

## 🔧 How It Works

### First Download (Magnet Link)

```bash
# When you first add a magnet link:
python3 torrent-dl-enhanced.py "magnet:?xt=urn:btih:abc123..."

# What happens:
# 1. ↓ Connecting to peers...
# 2. 📥 Fetching metadata from peers...
# 3. ⏳ Downloading...
# 4. ✅ Saved metadata for [torrent name]  ← New!
```

**Behind the scenes:**
- Metadata is saved to: `~/.config/torrent-downloader/resume/{info_hash}.torrent`
- Resume data is saved to: `~/.config/torrent-downloader/resume/{info_hash}.fastresume`

### Resume Download (Same Magnet)

```bash
# Add the same magnet link again:
python3 torrent-dl-enhanced.py "magnet:?xt=urn:btih:abc123..."

# What happens now:
# 1. 📦 Saved torrent found - loading      ← Instant!
# 2. 🔍 Checking for existing files...
# 3. ✅ Found existing data: 47.2% complete
# 4. ↓ Downloading from 47.2%...
```

**No more:**
- ❌ Waiting for metadata from peers
- ❌ Starting from 0%
- ❌ Re-downloading existing data

---

## 🎯 Use Cases

### Scenario 1: Interrupted Download
```bash
# Start download
python3 torrent-dl-enhanced.py "magnet:?xt=..."
# Download gets to 30%, then power outage!

# Resume later - same magnet link
python3 torrent-dl-enhanced.py "magnet:?xt=..."
# ✅ Continues from 30%
```

### Scenario 2: Daily Seeding
```bash
# Download a large file over multiple days
# Day 1: Download to 40%, then stop (Ctrl+C)
# Day 2: Resume, download to 75%, then stop
# Day 3: Resume, complete download

# Same magnet link works every time!
```

### Scenario 3: Multiple Computers
```bash
# Download partial file on Computer A
# Copy partial files to Computer B
# Add magnet on Computer B

# If you have the saved .torrent file from Computer A:
cp ~/.config/torrent-downloader/resume/*.torrent [to Computer B]
# Then Computer B can resume the download
```

---

## 📂 File Locations

All resume data is stored in: `~/.config/torrent-downloader/resume/`

### Files Created

For each magnet download, two files are created:

```
~/.config/torrent-downloader/resume/
├── abc123def456.torrent       ← Torrent metadata (structure, files, hashes)
└── abc123def456.fastresume    ← Download progress (which pieces complete)
```

The filename is the **info hash** - a unique identifier for the torrent.

### You Can Safely:
- ✅ Backup this folder
- ✅ Move it to another computer
- ✅ Delete individual files to "forget" a torrent

### Don't:
- ❌ Delete while downloads are active
- ❌ Manually edit these files

---

## 🎬 GUI Usage

### Adding a Magnet Link

1. Open the GUI:
   ```bash
   python3 torrent-dl-gui-secure.py
   ```

2. Paste magnet link in the input field

3. Click **"Add"**

4. **First time:**
   - Status shows: "Fetching metadata..."
   - After metadata arrives: "✅ Saved metadata for [name]" (in console)
   - Download continues

5. **Resume later:**
   - Add the same magnet link again
   - Status shows: "📦 Loading saved torrent..."
   - No waiting for metadata!
   - Shows progress: "47.2%" (not 0%)

---

## 🔍 How to Check If It's Working

### Test 1: Metadata Saving

```bash
# Add a magnet and wait for metadata
python3 torrent-dl-enhanced.py "magnet:?xt=urn:btih:abc123..."

# Look for this message:
# ✅ Saved metadata for [torrent name]

# Check the file exists:
ls -lh ~/.config/torrent-downloader/resume/*.torrent
```

### Test 2: Resume Detection

```bash
# Stop download with Ctrl+C after a few minutes

# Add same magnet again
python3 torrent-dl-enhanced.py "magnet:?xt=urn:btih:abc123..."

# Look for these messages:
# 📦 Saved torrent found - loading
# 🔍 Checking for existing files...
# ✅ Found existing data: [percentage]% complete
```

### Test 3: Verify Download Path

Make sure you're using the same download directory:

```bash
# First download
python3 torrent-dl-enhanced.py "magnet:..." -d ~/Downloads/torrents

# Resume - MUST use same -d parameter
python3 torrent-dl-enhanced.py "magnet:..." -d ~/Downloads/torrents
```

---

## ⚠️ Important Notes

### 1. Download Path Must Match

The download directory must be the same for resume to work:

```bash
# ✅ Correct
python3 torrent-dl-enhanced.py "magnet:..." -d ~/Downloads/torrents
python3 torrent-dl-enhanced.py "magnet:..." -d ~/Downloads/torrents

# ❌ Wrong - different paths
python3 torrent-dl-enhanced.py "magnet:..." -d ~/Downloads/torrents
python3 torrent-dl-enhanced.py "magnet:..." -d ~/Downloads  # Won't find files!
```

### 2. Partial Files Must Not Be Moved/Renamed

The actual download files must stay in the same location with the same names.

### 3. Same Magnet Link Required

You need the exact same magnet link to resume. If you lost it:
- Check browser history
- Check the saved .torrent file (filename is the info hash)
- Some torrent sites let you get magnet from info hash

### 4. File Checking Takes Time

First resume will scan existing files (can take 1-5 minutes for large files). Be patient!

---

## 🐛 Troubleshooting

### Problem: "No metadata found" when resuming

**Possible causes:**
1. Metadata wasn't saved (download stopped too early)
2. Resume directory was deleted
3. Different magnet link (different torrent)

**Solution:**
- Check if metadata file exists:
  ```bash
  ls ~/.config/torrent-downloader/resume/
  ```
- If missing, you'll need to fetch metadata again (will still detect partial files)

### Problem: Starts from 0% even with partial files

**Possible causes:**
1. Download path doesn't match
2. Files were moved or renamed
3. Wrong magnet link (different version/quality)

**Solution:**
```bash
# Verify download path matches
ls -la ~/Downloads/torrents/  # Check files are there

# Use exact same -d parameter
python3 torrent-dl-enhanced.py "magnet:..." -d ~/Downloads/torrents
```

### Problem: "Checking files" takes forever

**This is normal!** Large files take time to verify:
- 500MB: ~30 seconds
- 2GB: 1-2 minutes
- 6GB: 2-5 minutes
- 10GB+: 5-10 minutes

Just wait - progress will update once checking completes.

---

## 📊 What Changed in the Code

### CLI (`torrent-dl-enhanced.py`)

**Added:**
1. Line 88: `self.metadata_saved = {}` - Track saved metadata
2. Lines 181-202: `save_metadata_if_ready()` - Save .torrent when metadata arrives
3. Lines 114-152: Enhanced magnet handling with three scenarios:
   - Has resume data + metadata → instant resume
   - Has metadata only → load and check files
   - Has neither → fetch from peers
4. Line 225: Call metadata saving in download loop

### GUI (`torrent-dl-gui-secure.py`)

**Added:**
1. Line 30: `self.metadata_saved = set()` - Track saved metadata
2. Lines 1249-1271: `save_metadata_if_ready()` - Save .torrent when metadata arrives
3. Lines 1046-1102: Enhanced magnet handling (same three scenarios as CLI)
4. Line 1286: Call metadata saving in update loop

---

## 🎉 Success Indicators

You know it's working when you see:

**First Download:**
```
📥 Fetching metadata from peers...
... Done!
  Name: Big Buck Bunny
  Size: 365.05 MiB
  Files: 1
[Downloading...]
✅ Saved metadata for Big Buck Bunny  ← This means it worked!
```

**Resume:**
```
Adding magnet link...
  📦 Saved torrent found - loading      ← Instant!
  🔍 Checking for existing files...
  ✅ Found existing data: 47.2% complete  ← Detected partial!
[Continues from 47.2%]
```

---

## 💡 Pro Tips

### Tip 1: Back Up Resume Data
```bash
# Backup your resume data
cp -r ~/.config/torrent-downloader/resume ~/backup/resume-$(date +%Y%m%d)
```

### Tip 2: Share Magnet + Metadata
If you want to help someone resume your download:
```bash
# Send them:
# 1. The magnet link
# 2. The saved .torrent file from resume directory
# 3. The partial download files

# They can copy the .torrent file to their resume directory
# Then add the magnet - it will load instantly!
```

### Tip 3: Clean Up Old Torrents
```bash
# Remove resume data for old completed torrents
rm ~/.config/torrent-downloader/resume/abc123def456.*
```

---

## 🚀 Next Steps

Now that magnet resume works, you might want:

1. **Selective file download** - Choose which files in a torrent to download
2. **Sequential download** - Download pieces in order (for video streaming)
3. **Watch folder** - Auto-add magnet links from a folder
4. **RSS feeds** - Auto-download new episodes

See `FEATURE_IDEAS.md` for more ideas!

---

**Updated**: 2025-11-09
**Status**: ✅ Implemented and tested
**Files Modified**: `torrent-dl-enhanced.py`, `torrent-dl-gui-secure.py`
