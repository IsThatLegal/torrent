# Resume Functionality Fix Guide

## 🔧 What Was Fixed

The app wasn't displaying unfinished downloads on startup. This has been fixed!

### Changes Made:

1. **Updated `load_session_state()` function** (lines 119-203)
   - Now checks for `.torrent` files first (preferred)
   - Falls back to `.magnet` files if no .torrent exists
   - Forces file recheck to detect existing partial downloads
   - Adds proper error handling with tracebacks

2. **Updated `save_session_state()` function** (lines 237-250)
   - Now saves both `.torrent` AND `.magnet` files
   - `.torrent` files provide complete metadata
   - `.magnet` files serve as backup

3. **Created diagnostic tool** (`check_resume_data.py`)
   - Shows what torrents are saved
   - Identifies which can be resumed
   - Helps troubleshoot resume issues

---

## 🧪 Testing the Fix

### Step 1: Check Current Resume Data

```bash
cd ~/torrent-downloader
python3 check_resume_data.py
```

**Expected output:**
```
Resume Data Diagnostic Tool
======================================================================

✓ Resume directory exists: ~/.config/torrent-downloader/resume

Found 3 torrent(s) with resume data:

Torrent 1:
  Info Hash: 83de20148749b8bf74e41b6f4572f521a016603a
  Files:
    ✓ .fastresume (resume data)
    ⚠ .torrent (missing)
    ✓ .magnet (magnet link)
  Name: Dead To Rights (2025) [2160p] [4K] [WEB] [5.1] [YTS.MX]
  Status: ✓ Can be resumed
```

### Step 2: Open the App

```bash
python3 torrent-dl-gui-secure.py
```

**What you should see:**
- App opens normally
- Console shows: `Loading magnet: Dead To Rights (2025)...`
- Console shows: `Loading magnet: Frankenstein (2025)...`
- Torrents appear in the Downloads tab with status "Checking files"
- After file checking completes, they show actual progress

### Step 3: Verify Torrents Loaded

In the GUI:
1. Go to **Downloads** tab
2. You should see your unfinished torrents
3. Status might say "Checking files" initially
4. After checking, they resume downloading from where they left off

---

## 🐛 Known Issue with Your Current Data

Your resume files show:
```
Total torrents: 3
Resumable: 3
With full metadata: 1 (corrupted)
```

**Problem:** The `.fastresume` files are only 2 bytes (essentially empty). This happened because:
1. Torrents were added but never started downloading
2. App was closed before libtorrent could save meaningful resume data

**Impact:**
- Torrents will still be loaded (using magnet links)
- They will need to re-check files from scratch
- Progress will be detected but may take a moment

---

## 🔧 If Torrents Still Don't Appear

### Option 1: Clean Start

```bash
# Backup current resume data
cp -r ~/.config/torrent-downloader/resume ~/.config/torrent-downloader/resume.backup

# Remove empty resume files
cd ~/.config/torrent-downloader/resume/
rm *.fastresume

# Re-add torrents manually using the magnet links
cat *.magnet
# Copy each magnet and add via GUI
```

### Option 2: Rebuild Resume Data

The corrupted .torrent file needs to be removed:

```bash
# Remove corrupted torrent file
rm ~/.config/torrent-downloader/resume/866a52eee305b2eacc0ed7c3c86532ccdf0453a7.torrent

# Restart app
python3 torrent-dl-gui-secure.py
```

### Option 3: Manual Re-add

If you have the original magnet links or .torrent files:

1. Open the app
2. Click "Add" or paste magnet in the field
3. Point it to the same download directory
4. It will detect existing files automatically

---

## 📊 Testing New Resume Functionality

To test that resume works properly going forward:

### Test 1: Add New Torrent

```bash
# Open app
python3 torrent-dl-gui-secure.py

# Add a test torrent (Big Buck Bunny)
# Paste in GUI: magnet:?xt=urn:btih:dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c&dn=Big+Buck+Bunny
```

### Test 2: Let It Download Partially

- Let it download to ~10-20%
- Close the app (File → Quit)

### Test 3: Reopen and Verify Resume

```bash
python3 torrent-dl-gui-secure.py
```

**Expected:**
- Console shows: `Loading torrent: Big Buck Bunny`
- Torrent appears in Downloads tab
- Shows progress: "Checking files"
- After checking: "10.5%" (or whatever percentage you had)
- Continues downloading from there!

### Test 4: Check Resume Files

```bash
python3 check_resume_data.py
```

**Expected:**
```
Found 4 torrent(s) with resume data:

Torrent 4:
  Info Hash: dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c
  Files:
    ✓ .fastresume (resume data)
    ✓ .torrent (full metadata)
    ✓ .magnet (magnet link)
  Name: Big Buck Bunny
  Status: ✓ Can be resumed
```

---

## 🎯 What Each File Does

```
~/.config/torrent-downloader/resume/
├── {hash}.fastresume    ← Resume data (which pieces downloaded)
├── {hash}.torrent       ← Full torrent metadata (structure, files, hashes)
└── {hash}.magnet        ← Magnet link (backup if .torrent missing)
```

### Resume Priority:
1. **Best**: `.fastresume` + `.torrent` = Instant resume with full metadata
2. **Good**: `.fastresume` + `.magnet` = Resume but need to fetch metadata
3. **Fallback**: `.magnet` only = Must re-fetch everything

---

## 💡 Recommendations

### For Your Current Torrents

Since your current `.fastresume` files are empty:

**Option A: Start Fresh (Recommended)**
```bash
# Keep only the magnet files
cd ~/.config/torrent-downloader/resume/
rm *.fastresume *.torrent

# Restart app - it will use magnets to reload
python3 torrent-dl-gui-secure.py
```

**Option B: Re-add Manually**
```bash
# View your magnet links
cat ~/.config/torrent-downloader/resume/*.magnet

# Copy each one and add via GUI
# Point to existing download directory: ~/Downloads/torrents
# App will detect existing files!
```

### For Future Downloads

The fix ensures:
- ✅ Torrents save properly on close
- ✅ Torrents load on startup
- ✅ Full metadata is saved
- ✅ Resume works reliably

---

## 🔍 Debugging Commands

```bash
# Check what torrents are saved
python3 check_resume_data.py

# List resume files
ls -lh ~/.config/torrent-downloader/resume/

# Check resume data size (should be > 100 bytes for active torrents)
du -h ~/.config/torrent-downloader/resume/*.fastresume

# View magnet links
cat ~/.config/torrent-downloader/resume/*.magnet

# Check for corrupted .torrent files (0 bytes)
find ~/.config/torrent-downloader/resume/ -name "*.torrent" -size 0
```

---

## ✅ Verification Checklist

After implementing the fix:

- [ ] Run `check_resume_data.py` - see your 3 torrents
- [ ] Open app - torrents appear in Downloads tab
- [ ] Add new torrent - let it download partially
- [ ] Close app properly (File → Quit)
- [ ] Run `check_resume_data.py` - see new torrent with full metadata
- [ ] Reopen app - all torrents resume, including new one
- [ ] Check console - see "Loading torrent: [name]" messages
- [ ] Verify progress preserved (not restarting from 0%)

---

## 📞 Still Having Issues?

If torrents still don't appear:

1. **Check console output**
   ```bash
   python3 torrent-dl-gui-secure.py 2>&1 | tee app.log
   ```

2. **Look for errors**
   - "Failed to resume..." errors
   - "Failed to load session state" errors

3. **Check file permissions**
   ```bash
   ls -la ~/.config/torrent-downloader/resume/
   ```

4. **Verify download path matches**
   - Settings → Download path should be: `~/Downloads/torrents`
   - That's where your partial files are

---

**Fixed**: 2025-11-09
**Files Modified**:
- `torrent-dl-gui-secure.py` (load/save session state)
**Files Created**:
- `check_resume_data.py` (diagnostic tool)
- `RESUME_FIX_GUIDE.md` (this file)
