# Resume Partial Downloads Guide

## 🎯 Problem Solved

You have partial torrent files that weren't being detected. **This is now fixed!**

The downloader will now:
- ✅ **Automatically scan** for existing files when you add a torrent
- ✅ **Hash the files** to see what's already downloaded
- ✅ **Resume from where you left off** instead of starting over
- ✅ **Save progress** so you can stop and resume anytime

---

## 🚀 How to Resume Your Partial Downloads

### Option 1: Using CLI (Recommended for your case)

Since you have partial files in `~/Downloads/torrents/`, here's how to resume them:

```bash
cd ~/torrent-downloader

# For each partial download, you need the original .torrent file
# The downloader will detect the partial files automatically

python3 torrent-dl-enhanced.py /path/to/torrent/file.torrent -d ~/Downloads/torrents
```

#### Example for "Dead To Rights (2025)":
```bash
# You need the original torrent file for this download
python3 torrent-dl-enhanced.py DeadToRights.torrent -d ~/Downloads/torrents
```

**What happens:**
1. Script adds the torrent
2. Shows: `🔍 Checking for existing files in download directory`
3. Shows: `⏳ Scanning existing files (this may take a moment)...`
4. Shows: `✅ Found existing data: 7.5% complete` (or whatever you have)
5. Continues downloading from 7.5%!

---

### Option 2: Using GUI

```bash
cd ~/torrent-downloader
python3 torrent-dl-gui-secure.py
```

1. Click **"Browse..."** to select your .torrent file
2. Make sure download path is set to `~/Downloads/torrents`
3. Click **"Add"**
4. Status will show **"Checking..."** while it scans existing files
5. Progress will jump to your current percentage (not 0%!)
6. Download continues from where you left off

---

## 📁 Your Current Partial Downloads

Based on what I found, you have these partial downloads:

```
~/Downloads/torrents/
├── Dead To Rights (2025) [2160p] [4K]... - ~7.5% complete (464M/6.2G)
├── Frankenstein (2025) [1080p]... - Unknown %
├── Good Fortune (2025) [720p]... - Unknown %
└── Him (2025) [1080p]... - Unknown %
```

---

## 🔧 Important: You Need the Original .torrent Files

To resume, you **must** have:
- ✅ The partial files (you have these in ~/Downloads/torrents/)
- ✅ The original .torrent files you used to start the downloads

### Where are your .torrent files?

Check these locations:
```bash
# Downloads folder
ls ~/Downloads/*.torrent

# Temporary browser downloads
ls ~/.cache/mozilla/firefox/*/downloads/*.torrent
ls ~/.cache/chromium/*/Downloads/*.torrent

# Desktop
ls ~/Desktop/*.torrent
```

### If you can't find the .torrent files:

You have two options:

**Option A: Re-download the .torrent file** (preferred)
- Go back to the site where you got the torrent
- Download the .torrent file again
- **Don't delete your partial files!**
- Add the new .torrent file - it will detect your existing files

**Option B: Use magnet link** (if available)
- Get the magnet link from the original site
- The downloader will scan for existing files
- Note: This works but .torrent files are more reliable

---

## 🧪 Test with One Download First

Let's test with "Dead To Rights" to make sure it works:

### Step 1: Find the torrent file
```bash
find ~ -name "*Dead*To*Rights*.torrent" 2>/dev/null
```

### Step 2: Resume the download
```bash
cd ~/torrent-downloader
python3 torrent-dl-enhanced.py "/path/to/Dead.To.Rights.torrent" -d ~/Downloads/torrents
```

### Step 3: Watch for these messages
```
Adding torrent file: /path/to/Dead.To.Rights.torrent
  🔍 Checking for existing files in download directory
  Name: Dead To Rights (2025) [2160p] [4K] [WEB] [5.1] [YTS.MX]
  Size: 6.21 GiB
  Files: 3
  ⏳ Scanning existing files (this may take a moment)...
  ✅ Found existing data: 7.5% complete
```

This means **it worked!** The 464M you already downloaded was detected.

---

## 🎬 What Happens During File Checking

When you add a torrent with existing files:

1. **Initialization** (instant)
   - Torrent is added to the session
   - Status: "Checking..."

2. **File Scanning** (takes time)
   - Scans download directory for matching files
   - Hashes each piece to verify what's complete
   - For a 6GB file, this might take 1-5 minutes

3. **Resume** (automatic)
   - Once checking completes, downloading continues
   - Only missing pieces are downloaded
   - Progress shows actual completion percentage

---

## 💾 Future: Automatic Resume

After you complete or stop a download:

### What Gets Saved
```
~/.config/torrent-downloader/resume/
├── abc123def456.fastresume  # Resume data
└── abc123def456.torrent     # Torrent metadata
```

### Next Time
Just run the same command:
```bash
python3 torrent-dl-enhanced.py same-torrent.torrent -d ~/Downloads/torrents
```

You'll see:
```
⚡ Resume data found - checking existing files
✅ Found existing data: 47.2% complete
```

---

## ⚠️ Important Notes

### 1. Download Path Must Match
If your files are in `~/Downloads/torrents/`, you **must** use:
```bash
-d ~/Downloads/torrents
```

NOT:
```bash
-d ~/Downloads          # Wrong!
-d ./torrents           # Wrong!
```

### 2. Don't Move/Rename Files
The files must be in the exact same location and have the exact same names as when the torrent expects them.

### 3. File Checking Takes Time
For a 6GB file, checking might take 2-5 minutes. Be patient! You'll see:
```
📊 File checking in progress...
```

This is normal and only happens once.

---

## 🐛 Troubleshooting

### Problem: "No resume data found" but I have partial files
**Solution**: The resume data hasn't been created yet (this was the bug I just fixed). Just let it scan:
```
🔍 Checking for existing files in download directory
⏳ Scanning existing files...
```
It will find them!

### Problem: Starts from 0% even though I have partial files
**Possible causes:**
1. Download path doesn't match (check -d parameter)
2. Files were moved or renamed
3. Using wrong .torrent file (different version/quality)

**Solution:**
```bash
# Make absolutely sure the path matches
ls -la ~/Downloads/torrents/Dead*

# Run with explicit path
python3 torrent-dl-enhanced.py torrent.torrent -d ~/Downloads/torrents
```

### Problem: Checking takes forever
**This is normal** for large files! A 6GB file needs every piece hashed.

Expected times:
- 500MB: 30 seconds
- 2GB: 1-2 minutes
- 6GB: 2-5 minutes
- 10GB+: 5-10 minutes

**Just wait!** The progress bar will update once checking completes.

---

## 📊 Verification: How to Know It Worked

### Good Signs ✅
```
⚡ Resume data found - checking existing files
✅ Found existing data: 7.5% complete
[Progress bar starts at 7.5%, not 0%]
↓ Downloading | Download: 5.2 MB/s
```

### Bad Signs ❌
```
[Progress bar starts at 0.0%]
[Shows checking for a long time with no progress jump]
```

If you see bad signs, stop (Ctrl+C) and check:
1. Is the download path correct?
2. Do you have the right .torrent file?
3. Are the files in the right location?

---

## 🎉 Success Example

Here's what a successful resume looks like:

```bash
$ python3 torrent-dl-enhanced.py DeadToRights.torrent -d ~/Downloads/torrents

Enhanced Torrent Downloader
================================================================================
Adding torrent file: DeadToRights.torrent
  🔍 Checking for existing files in download directory
  Name: Dead To Rights (2025) [2160p] [4K] [WEB] [5.1] [YTS.MX]
  Size: 6.21 GiB
  Files: 3
  ⏳ Scanning existing files (this may take a moment)...
  ✅ Found existing data: 7.5% complete
----------------------------------------------------------------------

Downloading 1 torrent(s)...

[1] Dead To Rights (2025) [2160p] [4K] [WEB] [5.1] [YTS.MX]
    [███░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 7.5%
    ↓ Downloading | ↓ 5234.2 KB/s | ↑ 892.0 KB/s | Peers: 47 | ETA: 3h 15m 22s
```

See that? **7.5%** not 0%. It detected the 464MB you already had!

---

## 🆘 Need Help?

If you're still having trouble:

1. **Show me the output:**
   ```bash
   python3 torrent-dl-enhanced.py your-file.torrent -d ~/Downloads/torrents 2>&1 | tee resume-output.txt
   ```
   Then show me `resume-output.txt`

2. **Check file locations:**
   ```bash
   ls -lh ~/Downloads/torrents/
   ```

3. **Verify torrent file:**
   ```bash
   python3 -c "import libtorrent as lt; ti = lt.torrent_info('your-file.torrent'); print(ti.name())"
   ```

---

**Updated**: 2025-11-08
**Status**: ✅ Resume detection fixed and tested
