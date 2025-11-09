# Remove Torrents Feature - Fixed! ✅

## Problem Solved

When you removed a download, it would reappear when you reopened the app. This has been fixed!

## What Was Wrong

Previously:
- Removing a torrent only deleted it from the current session
- Resume files (`.fastresume`, `.torrent`, `.magnet`) were NOT deleted
- On restart, the app would reload from those files
- Torrent would reappear! 😞

## What's Fixed

Now when you remove a torrent:
- ✅ Removes from current session
- ✅ **Deletes all resume files** so it won't reload
- ✅ Optionally deletes downloaded files too
- ✅ Stays removed after restart!

## How to Use

### Removing a Single Torrent

1. **Select the torrent** in the Downloads tab
2. **Right-click → Remove** (or click Remove button)
3. **Choose an option:**

   ```
   Remove torrent from list?

   • Yes = Remove and delete resume data (torrent can be re-added)
   • No = Remove and delete downloaded files too
   • Cancel = Keep torrent
   ```

### Option Details

**Click "Yes"** - Remove from app, keep files
- Removes torrent from the list
- Deletes resume data (won't reload on restart)
- **Downloaded files are kept** on disk
- You can re-add this torrent later and it will detect existing files

**Click "No"** - Remove everything
- Removes torrent from the list
- Deletes resume data (won't reload on restart)
- **Deletes downloaded files** from disk
- Complete removal - frees up disk space

**Click "Cancel"** - Keep it
- Nothing happens
- Torrent stays in the list

### Clearing Completed Torrents

When you use **"Clear Completed"**:
- Removes all completed/seeding torrents
- Deletes their resume data
- **Keeps downloaded files** (they're complete!)
- Won't reload on restart

## Technical Details

### Files Deleted

When you remove a torrent, these files are deleted:

```
~/.config/torrent-downloader/resume/
├── {info_hash}.fastresume   ← Deleted
├── {info_hash}.torrent       ← Deleted
└── {info_hash}.magnet        ← Deleted
```

### Downloaded Files

If you choose "No" (delete files), this is deleted:

```
~/Downloads/torrents/
└── [Torrent Name]/          ← Entire folder deleted
    ├── movie.mkv
    ├── subtitle.srt
    └── ...
```

Or for single-file torrents:
```
~/Downloads/torrents/
└── movie.mkv                ← File deleted
```

## Use Cases

### Use Case 1: Remove Duplicate

You accidentally added the same torrent twice:

1. Select the duplicate
2. Remove → **Yes** (keep files)
3. First copy continues downloading
4. Duplicate won't reload on restart ✓

### Use Case 2: Don't Want This Anymore

You started downloading something but changed your mind:

1. Select the torrent
2. Remove → **No** (delete files)
3. Torrent removed
4. Downloaded files deleted (free space)
5. Won't reload on restart ✓

### Use Case 3: Completed, Keep File

Download is complete and you want the file:

1. Wait for "Seeding" status
2. Remove → **Yes** (keep files)
3. Torrent removed from list
4. Downloaded files kept in ~/Downloads/torrents/
5. Won't reload on restart ✓

### Use Case 4: Clean Up All Completed

You have many completed torrents seeding:

1. Click **"Clear Completed"**
2. All completed torrents removed
3. Downloaded files kept
4. Won't reload on restart ✓

## Before & After

### Before (Old Behavior)

```
1. Add torrent → Downloads
2. Remove torrent → Disappears
3. Close app
4. Reopen app
5. Torrent reappears! 😞
```

### After (New Behavior)

```
1. Add torrent → Downloads
2. Remove torrent → Choose option
   - Yes: Keep files, delete resume
   - No: Delete everything
3. Close app
4. Reopen app
5. Torrent stays removed! ✓
```

## Testing

To verify it works:

1. **Add a test torrent**
   ```bash
   # In GUI, add: magnet:?xt=urn:btih:dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c
   ```

2. **Let it download a bit** (10-20%)

3. **Remove it** (choose "Yes" to keep files)

4. **Check resume directory**
   ```bash
   ls ~/.config/torrent-downloader/resume/
   # Should NOT see files for that torrent
   ```

5. **Restart the app**
   ```bash
   python3 torrent-dl-gui-secure.py
   ```

6. **Verify torrent doesn't reappear** ✓

7. **Check downloaded files still exist**
   ```bash
   ls ~/Downloads/torrents/
   # Files should still be there
   ```

## What Gets Deleted

### Always Deleted (Both Options)
- `.fastresume` file
- `.torrent` file
- `.magnet` file
- From metadata_saved set

### Only Deleted if You Choose "No"
- Downloaded files/folders
- All content in torrent directory

## Safety Features

### Confirmation Dialog
- Always asks before removing
- Clear description of each option
- Can cancel anytime

### Error Handling
- If file deletion fails, shows warning
- Doesn't crash the app
- Logs errors to console

### No Accidental Deletion
- Two-step process (select + confirm)
- Clear labeling of options
- Cancel button always available

## Commands for Testing

```bash
# Check what resume files exist
ls -lh ~/.config/torrent-downloader/resume/

# Check downloaded files
ls -lh ~/Downloads/torrents/

# Check app behavior
cd ~/torrent-downloader
python3 torrent-dl-gui-secure.py
```

## Related Functions

### remove_selected()
- Called when you click Remove button
- Handles single torrent removal
- Offers choice to delete files

### clear_completed()
- Called when you click Clear Completed
- Removes all seeding torrents
- Always keeps downloaded files

### delete_resume_files(info_hash)
- Internal helper function
- Deletes all resume files for a torrent
- Called by both remove functions

## Troubleshooting

### Issue: Removed torrent still reappears

**Check:**
```bash
# See if resume files still exist
ls ~/.config/torrent-downloader/resume/ | grep {info_hash}
```

**Fix:**
```bash
# Manually delete resume files
cd ~/.config/torrent-downloader/resume/
rm {info_hash}.*
```

### Issue: Deleted files by accident

**Recovery:**
- If you still have the resume files, re-add the torrent
- It will re-download from 0%
- Or check your backup

**Prevention:**
- Read the dialog carefully
- "Yes" = keep files
- "No" = delete files

### Issue: Can't delete files (permission error)

**Symptoms:**
```
Warning: Could not delete files: Permission denied
```

**Fix:**
```bash
# Check permissions
ls -la ~/Downloads/torrents/

# Fix if needed
chmod -R u+w ~/Downloads/torrents/
```

## Summary

✅ **Remove Torrent**
- Deletes resume files
- Won't reload on restart
- Choose to keep or delete downloaded files

✅ **Clear Completed**
- Removes all seeding torrents
- Deletes resume files
- Keeps downloaded files

✅ **Persistent**
- Stays removed after restart
- No more surprise reappearances

---

**Fixed**: 2025-11-09
**Files Modified**: `torrent-dl-gui-secure.py`
**Functions Added**:
- `delete_resume_files(info_hash)`
- Enhanced `remove_selected()`
- Enhanced `clear_completed()`
