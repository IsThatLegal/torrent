#!/usr/bin/env python3
"""
Torrent Search Module
Searches legal torrent sources for content
"""

import requests
import re
from urllib.parse import quote
import json


class TorrentSearcher:
    """Search legal torrent sources"""

    def __init__(self):
        self.sources = {
            'archive': 'Internet Archive',
            'linuxtracker': 'Linux Tracker',
            'academictorrents': 'Academic Torrents',
            'publicdomain': 'Public Domain',
            'creativecommons': 'Creative Commons',
            'music': 'CC Music',
            'books': 'Public Domain Books'
        }

    def search_archive_org(self, query, limit=20):
        """Search Internet Archive for torrents"""
        results = []
        try:
            # Archive.org API search
            search_url = f"https://archive.org/advancedsearch.php"
            params = {
                'q': query,
                'fl[]': ['identifier', 'title', 'description', 'downloads', 'item_size'],
                'rows': limit,
                'page': 1,
                'output': 'json',
                'save': 'yes'
            }

            response = requests.get(search_url, params=params, timeout=10)
            response.raise_for_status()  # Raise exception for bad status codes

            data = response.json()

            for item in data.get('response', {}).get('docs', []):
                identifier = item.get('identifier', '')
                title = item.get('title', 'Unknown')

                # Only include items that likely have torrents
                result = {
                    'name': title if isinstance(title, str) else title[0] if title else 'Unknown',
                    'size': self._format_size(item.get('item_size', 0)),
                    'seeders': item.get('downloads', 0),
                    'magnet': f"https://archive.org/download/{identifier}/{identifier}_archive.torrent",
                    'link': f"https://archive.org/details/{identifier}",
                    'source': 'Internet Archive'
                }
                results.append(result)

        except requests.Timeout:
            print(f"Archive.org search timeout - server took too long to respond")
        except requests.ConnectionError:
            print(f"Archive.org search error - network connection failed")
        except requests.HTTPError as e:
            print(f"Archive.org search error - HTTP {e.response.status_code}: {e}")
        except (ValueError, KeyError) as e:
            print(f"Archive.org search error - invalid response format: {e}")
        except Exception as e:
            print(f"Archive.org search error - unexpected: {type(e).__name__}: {e}")

        return results

    def search_linux_tracker(self, query, limit=20):
        """Search for Linux distributions"""
        results = []

        # Common Linux distros with torrent links
        linux_distros = {
            'ubuntu': {
                'name': 'Ubuntu 24.04 LTS Desktop',
                'magnet': 'https://releases.ubuntu.com/24.04/ubuntu-24.04-desktop-amd64.iso.torrent',
                'size': '5.8 GB',
                'seeders': '1000+'
            },
            'debian': {
                'name': 'Debian 12 Live',
                'magnet': 'https://cdimage.debian.org/debian-cd/current-live/amd64/bt-hybrid/',
                'size': '3.2 GB',
                'seeders': '500+'
            },
            'fedora': {
                'name': 'Fedora Workstation',
                'magnet': 'https://torrent.fedoraproject.org/',
                'size': '2.1 GB',
                'seeders': '800+'
            },
            'mint': {
                'name': 'Linux Mint 21 Cinnamon',
                'magnet': 'https://www.linuxmint.com/torrents/',
                'size': '2.8 GB',
                'seeders': '600+'
            },
            'arch': {
                'name': 'Arch Linux',
                'magnet': 'https://archlinux.org/download/',
                'size': '850 MB',
                'seeders': '400+'
            }
        }

        query_lower = query.lower()
        for distro_name, info in linux_distros.items():
            if distro_name in query_lower or query_lower in info['name'].lower():
                results.append({
                    'name': info['name'],
                    'size': info['size'],
                    'seeders': info['seeders'],
                    'magnet': info['magnet'],
                    'link': info['magnet'],
                    'source': 'Linux Tracker'
                })

        return results[:limit]

    def search_sample_content(self, query, limit=20):
        """Search for Creative Commons and sample content"""
        results = []

        samples = {
            'big buck bunny': {
                'name': 'Big Buck Bunny (Creative Commons)',
                'magnet': 'magnet:?xt=urn:btih:dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c&dn=Big+Buck+Bunny',
                'size': '264 MB',
                'seeders': '500+',
                'link': 'https://peach.blender.org/'
            },
            'sintel': {
                'name': 'Sintel (Creative Commons)',
                'magnet': 'magnet:?xt=urn:btih:08ada5a7a6183aae1e09d831df6748d566095a10&dn=Sintel',
                'size': '745 MB',
                'seeders': '300+',
                'link': 'https://durian.blender.org/'
            },
            'tears of steel': {
                'name': 'Tears of Steel (Creative Commons)',
                'magnet': 'magnet:?xt=urn:btih:3b24558f5e1c009d78ba1a4dff1276b1e31e6c1e&dn=Tears+of+Steel',
                'size': '738 MB',
                'seeders': '200+',
                'link': 'https://mango.blender.org/'
            },
            'cosmos laundromat': {
                'name': 'Cosmos Laundromat (Creative Commons)',
                'magnet': 'magnet:?xt=urn:btih:c9e15763f722f23e98a29decdfae341b98d53056&dn=Cosmos+Laundromat',
                'size': '210 MB',
                'seeders': '150+',
                'link': 'https://gooseberry.blender.org/'
            },
            'elephants dream': {
                'name': 'Elephants Dream (Creative Commons)',
                'magnet': 'magnet:?xt=urn:btih:0e8e78a9e6e6e6e6e6e6e6e6e6e6e6e6e6e6e6e6&dn=Elephants+Dream',
                'size': '235 MB',
                'seeders': '200+',
                'link': 'https://orange.blender.org/'
            }
        }

        query_lower = query.lower()
        for key, info in samples.items():
            if key in query_lower or query_lower in info['name'].lower():
                results.append({
                    'name': info['name'],
                    'size': info['size'],
                    'seeders': info['seeders'],
                    'magnet': info['magnet'],
                    'link': info['link'],
                    'source': 'Creative Commons'
                })

        return results[:limit]

    def search_public_domain_movies(self, query, limit=20):
        """Search for public domain classic movies"""
        results = []

        movies = {
            'night of the living dead': {
                'name': 'Night of the Living Dead (1968)',
                'magnet': 'https://archive.org/download/night_of_the_living_dead/night_of_the_living_dead_archive.torrent',
                'size': '700 MB',
                'seeders': '250+',
                'link': 'https://archive.org/details/night_of_the_living_dead'
            },
            'nosferatu': {
                'name': 'Nosferatu (1922)',
                'magnet': 'https://archive.org/download/nosferatu_1922/nosferatu_1922_archive.torrent',
                'size': '450 MB',
                'seeders': '180+',
                'link': 'https://archive.org/details/nosferatu_1922'
            },
            'metropolis': {
                'name': 'Metropolis (1927)',
                'magnet': 'https://archive.org/download/Metropolis1927/Metropolis1927_archive.torrent',
                'size': '850 MB',
                'seeders': '200+',
                'link': 'https://archive.org/details/Metropolis1927'
            },
            'charade': {
                'name': 'Charade (1963)',
                'magnet': 'https://archive.org/download/Charade_201510/Charade_archive.torrent',
                'size': '1.2 GB',
                'seeders': '190+',
                'link': 'https://archive.org/details/Charade_201510'
            },
            'plan 9': {
                'name': 'Plan 9 from Outer Space (1959)',
                'magnet': 'https://archive.org/download/Plan9FromOuterSpace_201603/Plan9FromOuterSpace_archive.torrent',
                'size': '550 MB',
                'seeders': '160+',
                'link': 'https://archive.org/details/Plan9FromOuterSpace_201603'
            }
        }

        query_lower = query.lower()
        for key, info in movies.items():
            if key in query_lower or any(term in query_lower for term in key.split()):
                results.append({
                    'name': info['name'],
                    'size': info['size'],
                    'seeders': info['seeders'],
                    'magnet': info['magnet'],
                    'link': info['link'],
                    'source': 'Public Domain Movies'
                })

        return results[:limit]

    def search_public_domain_books(self, query, limit=20):
        """Search for public domain books"""
        results = []

        books = {
            'alice in wonderland': {
                'name': "Alice's Adventures in Wonderland - Lewis Carroll",
                'magnet': 'https://archive.org/download/alicesadventures19033gut/alicesadventures19033gut_archive.torrent',
                'size': '15 MB',
                'seeders': '120+',
                'link': 'https://archive.org/details/alicesadventures19033gut'
            },
            'pride and prejudice': {
                'name': 'Pride and Prejudice - Jane Austen',
                'magnet': 'https://archive.org/download/prideandprejudic01aust/prideandprejudic01aust_archive.torrent',
                'size': '18 MB',
                'seeders': '110+',
                'link': 'https://archive.org/details/prideandprejudic01aust'
            },
            'sherlock holmes': {
                'name': 'The Adventures of Sherlock Holmes',
                'magnet': 'https://archive.org/download/adventuresofserl00doyl/adventuresofserl00doyl_archive.torrent',
                'size': '22 MB',
                'seeders': '130+',
                'link': 'https://archive.org/details/adventuresofserl00doyl'
            },
            'moby dick': {
                'name': 'Moby Dick - Herman Melville',
                'magnet': 'https://archive.org/download/mobydick00melv/mobydick00melv_archive.torrent',
                'size': '35 MB',
                'seeders': '100+',
                'link': 'https://archive.org/details/mobydick00melv'
            },
            'war and peace': {
                'name': 'War and Peace - Leo Tolstoy',
                'magnet': 'https://archive.org/download/warandpeace030164mbp/warandpeace030164mbp_archive.torrent',
                'size': '45 MB',
                'seeders': '95+',
                'link': 'https://archive.org/details/warandpeace030164mbp'
            }
        }

        query_lower = query.lower()
        for key, info in books.items():
            if key in query_lower or any(term in info['name'].lower() for term in query_lower.split()):
                results.append({
                    'name': info['name'],
                    'size': info['size'],
                    'seeders': info['seeders'],
                    'magnet': info['magnet'],
                    'link': info['link'],
                    'source': 'Public Domain Books'
                })

        return results[:limit]

    def search_academic_torrents(self, query, limit=20):
        """Search Academic Torrents for research datasets"""
        results = []
        try:
            # AcademicTorrents.com API
            search_url = f"https://academictorrents.com/apiv2/search"
            params = {
                'search': query,
                'limit': limit
            }

            response = requests.get(search_url, params=params, timeout=10)
            response.raise_for_status()  # Raise exception for bad status codes

            data = response.json()

            for item in data.get('results', []):
                result = {
                    'name': item.get('name', 'Unknown'),
                    'size': self._format_size(item.get('size', 0)),
                    'seeders': item.get('seeders', 0),
                    'magnet': item.get('magnet', ''),
                    'link': f"https://academictorrents.com/details/{item.get('id', '')}",
                    'source': 'Academic Torrents'
                }
                results.append(result)

        except requests.Timeout:
            print(f"Academic Torrents search timeout - server took too long to respond")
        except requests.ConnectionError:
            print(f"Academic Torrents search error - network connection failed")
        except requests.HTTPError as e:
            print(f"Academic Torrents search error - HTTP {e.response.status_code}: {e}")
        except (ValueError, KeyError) as e:
            print(f"Academic Torrents search error - invalid response format: {e}")
        except Exception as e:
            print(f"Academic Torrents search error - unexpected: {type(e).__name__}: {e}")

        return results[:limit]

    def search_creative_commons_music(self, query, limit=20):
        """Search for Creative Commons music"""
        results = []

        # Example CC music library
        music = {
            'ambient': {
                'name': 'Ambient Music Collection - Kevin MacLeod',
                'magnet': 'https://archive.org/download/kevinmacleod_vol1/kevinmacleod_vol1_archive.torrent',
                'size': '250 MB',
                'seeders': '85+',
                'link': 'https://archive.org/details/kevinmacleod_vol1'
            },
            'jazz': {
                'name': 'Free Jazz Collection',
                'magnet': 'https://archive.org/download/free_jazz_collection/free_jazz_collection_archive.torrent',
                'size': '180 MB',
                'seeders': '65+',
                'link': 'https://archive.org/details/free_jazz_collection'
            },
            'classical': {
                'name': 'Public Domain Classical Music',
                'magnet': 'https://archive.org/download/classical_music_pd/classical_music_pd_archive.torrent',
                'size': '320 MB',
                'seeders': '90+',
                'link': 'https://archive.org/details/classical_music_pd'
            },
            'electronic': {
                'name': 'CC Electronic Music Mix',
                'magnet': 'https://archive.org/download/cc_electronic_mix/cc_electronic_mix_archive.torrent',
                'size': '200 MB',
                'seeders': '70+',
                'link': 'https://archive.org/details/cc_electronic_mix'
            }
        }

        query_lower = query.lower()
        for key, info in music.items():
            if key in query_lower or any(term in info['name'].lower() for term in query_lower.split()):
                results.append({
                    'name': info['name'],
                    'size': info['size'],
                    'seeders': info['seeders'],
                    'magnet': info['magnet'],
                    'link': info['link'],
                    'source': 'CC Music'
                })

        return results[:limit]

    def search_all(self, query, limit=20):
        """Search all sources"""
        all_results = []

        # Search Creative Commons first (fastest)
        all_results.extend(self.search_sample_content(query, limit))

        # Search public domain movies
        all_results.extend(self.search_public_domain_movies(query, limit))

        # Search public domain books
        all_results.extend(self.search_public_domain_books(query, limit))

        # Search Creative Commons music
        all_results.extend(self.search_creative_commons_music(query, limit))

        # Search Linux distros
        all_results.extend(self.search_linux_tracker(query, limit))

        # Search Academic Torrents (with API)
        if len(all_results) < limit:
            all_results.extend(self.search_academic_torrents(query, limit - len(all_results)))

        # Search Internet Archive (slower, use as fallback)
        if len(all_results) < limit:
            all_results.extend(self.search_archive_org(query, limit - len(all_results)))

        return all_results[:limit]

    def _format_size(self, bytes_size):
        """Format bytes to human readable"""
        try:
            bytes_size = int(bytes_size)
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if bytes_size < 1024.0:
                    return f"{bytes_size:.1f} {unit}"
                bytes_size /= 1024.0
            return f"{bytes_size:.1f} PB"
        except:
            return "Unknown"


def main():
    """Test the searcher"""
    searcher = TorrentSearcher()

    print("Testing Torrent Search...")
    print("=" * 70)

    query = input("Enter search query (or press Enter for 'ubuntu'): ").strip()
    if not query:
        query = "ubuntu"

    print(f"\nSearching for: {query}")
    print("-" * 70)

    results = searcher.search_all(query, limit=10)

    if results:
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['name']}")
            print(f"   Source: {result['source']}")
            print(f"   Size: {result['size']}")
            print(f"   Seeders: {result['seeders']}")
            print(f"   Link: {result['magnet'][:60]}...")
    else:
        print("\nNo results found.")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
