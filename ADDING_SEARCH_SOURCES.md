# Adding New Search Sources

This guide explains how to add new torrent search sources to your downloader.

## Quick Overview

To add a new search source, you need to:
1. Create a search method in `torrent_search.py`
2. Add it to the `search_all()` method
3. Test it!

---

## Step-by-Step Guide

### Step 1: Create a Search Method

Open `torrent_search.py` and add a new method to the `TorrentSearcher` class:

```python
def search_YOUR_SOURCE_NAME(self, query, limit=20):
    """Search YOUR SOURCE - description"""
    results = []

    # Your search logic here
    # Option A: Static database (fastest)
    # Option B: API call (requires internet)
    # Option C: Web scraping (slowest, use carefully)

    return results[:limit]
```

### Step 2: Return Format

Each result must be a dictionary with these keys:

```python
{
    'name': 'Torrent Name',           # String
    'size': '1.5 GB',                # String with unit
    'seeders': '100' or '100+',      # String or int
    'magnet': 'magnet:?xt=...' or 'https://...',  # Magnet link or torrent file URL
    'link': 'https://source.com/...',  # Info page URL
    'source': 'Source Name'           # String (shows in UI)
}
```

### Step 3: Add to search_all()

Find the `search_all()` method and add your search:

```python
def search_all(self, query, limit=20):
    all_results = []

    # ... existing searches ...

    # Add your new search here
    all_results.extend(self.search_YOUR_SOURCE_NAME(query, limit))

    # ... rest of searches ...

    return all_results[:limit]
```

---

## Examples

### Example 1: Static Database (Fastest)

Use this for a curated list of torrents:

```python
def search_my_collection(self, query, limit=20):
    """Search my personal collection"""
    results = []

    collection = {
        'keyword1': {
            'name': 'My Torrent 1',
            'magnet': 'magnet:?xt=urn:btih:...',
            'size': '500 MB',
            'seeders': '50',
            'link': 'https://example.com/torrent1'
        },
        'keyword2': {
            'name': 'My Torrent 2',
            'magnet': 'magnet:?xt=urn:btih:...',
            'size': '1.2 GB',
            'seeders': '100',
            'link': 'https://example.com/torrent2'
        }
    }

    query_lower = query.lower()
    for key, info in collection.items():
        if key in query_lower:
            results.append({
                'name': info['name'],
                'size': info['size'],
                'seeders': info['seeders'],
                'magnet': info['magnet'],
                'link': info['link'],
                'source': 'My Collection'
            })

    return results[:limit]
```

### Example 2: API Call (Dynamic)

Use this to search a live API:

```python
def search_example_api(self, query, limit=20):
    """Search Example API"""
    results = []

    try:
        # Make API request
        url = f"https://api.example.com/search"
        params = {'q': query, 'limit': limit}

        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()

            for item in data.get('results', []):
                results.append({
                    'name': item.get('title', 'Unknown'),
                    'size': self._format_size(item.get('size', 0)),
                    'seeders': item.get('seeds', 0),
                    'magnet': item.get('magnet', ''),
                    'link': item.get('url', ''),
                    'source': 'Example API'
                })

    except Exception as e:
        print(f"Example API error: {e}")

    return results[:limit]
```

### Example 3: Keyword Matching

Use this for pattern-based searching:

```python
def search_by_pattern(self, query, limit=20):
    """Search using patterns"""
    results = []
    query_lower = query.lower()

    # Match multiple keywords
    if 'linux' in query_lower and 'ubuntu' in query_lower:
        results.append({
            'name': 'Ubuntu 24.04 LTS',
            'size': '5.8 GB',
            'seeders': '1000+',
            'magnet': 'https://releases.ubuntu.com/...',
            'link': 'https://ubuntu.com/',
            'source': 'Ubuntu'
        })

    # Match any of several terms
    if any(term in query_lower for term in ['movie', 'film', 'video']):
        # Add movie results
        pass

    return results[:limit]
```

---

## Where to Find Legal Torrents

Good sources for legal torrents:

1. **Internet Archive** (archive.org) - Public domain content
   - API: `https://archive.org/advancedsearch.php`

2. **Academic Torrents** (academictorrents.com) - Research datasets
   - API: `https://academictorrents.com/apiv2/`

3. **Linux Distros** - Direct from project websites
   - Ubuntu: `https://releases.ubuntu.com/`
   - Debian: `https://www.debian.org/CD/torrent-cd/`
   - Fedora: `https://torrent.fedoraproject.org/`

4. **Creative Commons** - CC-licensed content
   - Blender movies
   - Free Music Archive
   - Wikimedia Commons

5. **Project Gutenberg** - Public domain books
   - Often available through archive.org

---

## Tips

1. **Start Simple** - Begin with a static list before adding API calls
2. **Handle Errors** - Always use try/except for network requests
3. **Test Thoroughly** - Test with various search terms
4. **Add Comments** - Document what your search does
5. **Respect Limits** - Don't hammer APIs, use timeouts
6. **Legal Only** - Only add sources for legal content

---

## Testing Your New Source

After adding a source, test it:

```bash
cd ~/torrent-downloader
python3 torrent_search.py
# Enter a search query that should match your new source
```

Or test in Python:

```python
from torrent_search import TorrentSearcher

searcher = TorrentSearcher()
results = searcher.search_YOUR_SOURCE_NAME('test query', limit=5)

for r in results:
    print(f"{r['name']} - {r['source']}")
```

---

## Restart the App

After making changes, restart the torrent app:

```bash
pkill -f "python3.*torrent-dl-gui"
cd ~/torrent-downloader
./launch-torrent-gui.sh
```

---

## Need Help?

- Check existing search methods in `torrent_search.py` for examples
- All methods follow the same pattern
- Results must include: name, size, seeders, magnet, link, source
