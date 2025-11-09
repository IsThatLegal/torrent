#!/usr/bin/env python3
"""
GUI Torrent Downloader with Search
A graphical interface for searching and downloading torrents
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import libtorrent as lt
import threading
import time
import os
from torrent_search import TorrentSearcher
from torrent_utils import format_size, format_speed, send_notification, sanitize_filename


class TorrentGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Torrent Downloader with Search")
        self.root.geometry("1000x750")

        # Session and torrents
        self.ses = None
        self.torrents = []
        self.running = False

        # Search
        self.searcher = TorrentSearcher()
        self.search_results = []

        # Settings
        self.download_path = os.path.expanduser("~/Downloads/torrents")
        self.max_download_rate = 0
        self.max_upload_rate = 0

        self.setup_ui()
        self.init_session()

    def setup_ui(self):
        """Setup the user interface with tabs"""
        # Create main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Title
        title_label = ttk.Label(main_frame, text="🔍 Torrent Downloader with Search",
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, pady=(0, 10))

        # Create notebook (tabs)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Tab 1: Search
        self.search_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.search_tab, text="🔍 Search")
        self.setup_search_tab()

        # Tab 2: Downloads
        self.downloads_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.downloads_tab, text="📥 Downloads")
        self.setup_downloads_tab()

        # Tab 3: Settings
        self.settings_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.settings_tab, text="⚙️ Settings")
        self.setup_settings_tab()

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var,
                              relief=tk.SUNKEN, padding=5)
        status_bar.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))

    def setup_search_tab(self):
        """Setup search tab"""
        self.search_tab.columnconfigure(0, weight=1)
        self.search_tab.rowconfigure(2, weight=1)

        # Search input
        search_frame = ttk.LabelFrame(self.search_tab, text="Search for Torrents", padding="10")
        search_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        search_frame.columnconfigure(1, weight=1)

        ttk.Label(search_frame, text="Query:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.search_entry = ttk.Entry(search_frame, width=50)
        self.search_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        self.search_entry.bind('<Return>', lambda e: self.search_torrents())

        ttk.Button(search_frame, text="Search",
                  command=self.search_torrents).grid(row=0, column=2, padx=5)

        # Info label
        info_label = ttk.Label(self.search_tab,
                              text="🔒 Searches legal sources: Creative Commons, Linux Distros, Internet Archive",
                              foreground="gray")
        info_label.grid(row=1, column=0, pady=(0, 10))

        # Results table
        results_frame = ttk.LabelFrame(self.search_tab, text="Search Results", padding="10")
        results_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)

        # Create Treeview for results
        columns = ('Name', 'Size', 'Seeders', 'Source')
        self.search_tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=15)

        self.search_tree.heading('Name', text='Name')
        self.search_tree.heading('Size', text='Size')
        self.search_tree.heading('Seeders', text='Seeders')
        self.search_tree.heading('Source', text='Source')

        self.search_tree.column('Name', width=400)
        self.search_tree.column('Size', width=100)
        self.search_tree.column('Seeders', width=100)
        self.search_tree.column('Source', width=150)

        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.search_tree.yview)
        self.search_tree.configure(yscrollcommand=scrollbar.set)

        self.search_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # Double-click to download
        self.search_tree.bind('<Double-1>', self.download_from_search)

        # Buttons
        button_frame = ttk.Frame(results_frame)
        button_frame.grid(row=1, column=0, pady=(10, 0))

        ttk.Button(button_frame, text="Download Selected",
                  command=self.download_from_search).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="View Details",
                  command=self.view_details).pack(side=tk.LEFT, padx=5)

    def setup_downloads_tab(self):
        """Setup downloads tab"""
        self.downloads_tab.columnconfigure(0, weight=1)
        self.downloads_tab.rowconfigure(1, weight=1)

        # Add torrent section
        add_frame = ttk.LabelFrame(self.downloads_tab, text="Add Torrent Manually", padding="10")
        add_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        add_frame.columnconfigure(1, weight=1)

        ttk.Label(add_frame, text="Torrent File:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Button(add_frame, text="Browse...",
                  command=self.browse_torrent).grid(row=0, column=1, sticky=tk.W, padx=5)

        ttk.Label(add_frame, text="Magnet Link:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.magnet_entry = ttk.Entry(add_frame, width=50)
        self.magnet_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(add_frame, text="Add",
                  command=self.add_magnet).grid(row=1, column=2, padx=5)

        # Downloads list
        downloads_frame = ttk.LabelFrame(self.downloads_tab, text="Active Downloads", padding="10")
        downloads_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        downloads_frame.columnconfigure(0, weight=1)
        downloads_frame.rowconfigure(0, weight=1)

        columns = ('Name', 'Size', 'Progress', 'Speed', 'Peers', 'Status')
        self.tree = ttk.Treeview(downloads_frame, columns=columns, show='headings', height=12)

        self.tree.heading('Name', text='Name')
        self.tree.heading('Size', text='Size')
        self.tree.heading('Progress', text='Progress')
        self.tree.heading('Speed', text='Speed')
        self.tree.heading('Peers', text='Peers')
        self.tree.heading('Status', text='Status')

        self.tree.column('Name', width=300)
        self.tree.column('Size', width=80)
        self.tree.column('Progress', width=80)
        self.tree.column('Speed', width=100)
        self.tree.column('Peers', width=60)
        self.tree.column('Status', width=100)

        scrollbar = ttk.Scrollbar(downloads_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # Control buttons
        control_frame = ttk.Frame(downloads_frame)
        control_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0))

        ttk.Button(control_frame, text="Remove Selected",
                  command=self.remove_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Clear Completed",
                  command=self.clear_completed).pack(side=tk.LEFT, padx=5)

    def setup_settings_tab(self):
        """Setup settings tab"""
        # Download path
        path_frame = ttk.LabelFrame(self.settings_tab, text="Download Location", padding="10")
        path_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        path_frame.columnconfigure(1, weight=1)

        ttk.Label(path_frame, text="Save to:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.path_label = ttk.Label(path_frame, text=self.download_path,
                                    relief=tk.SUNKEN, padding=5)
        self.path_label.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(path_frame, text="Change",
                  command=self.browse_download_path).grid(row=0, column=2, padx=5)

        # Bandwidth limits
        bandwidth_frame = ttk.LabelFrame(self.settings_tab, text="Bandwidth Limits", padding="10")
        bandwidth_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Label(bandwidth_frame, text="Download Limit (KB/s):").grid(row=0, column=0,
                                                                       sticky=tk.W, padx=5)
        self.download_limit_var = tk.StringVar(value="0")
        ttk.Spinbox(bandwidth_frame, from_=0, to=10000, increment=100,
                   textvariable=self.download_limit_var, width=10).grid(row=0, column=1,
                                                                         sticky=tk.W, padx=5)
        ttk.Label(bandwidth_frame, text="(0 = unlimited)").grid(row=0, column=2, sticky=tk.W)

        ttk.Label(bandwidth_frame, text="Upload Limit (KB/s):").grid(row=1, column=0,
                                                                     sticky=tk.W, padx=5, pady=5)
        self.upload_limit_var = tk.StringVar(value="0")
        ttk.Spinbox(bandwidth_frame, from_=0, to=10000, increment=100,
                   textvariable=self.upload_limit_var, width=10).grid(row=1, column=1,
                                                                       sticky=tk.W, padx=5, pady=5)
        ttk.Label(bandwidth_frame, text="(0 = unlimited)").grid(row=1, column=2, sticky=tk.W)

        ttk.Button(bandwidth_frame, text="Apply Limits",
                  command=self.apply_limits).grid(row=0, column=3, rowspan=2, padx=20)

    def init_session(self):
        """Initialize libtorrent session"""
        self.ses = lt.session()
        settings = self.ses.get_settings()
        settings['listen_interfaces'] = '0.0.0.0:6881'
        settings['enable_dht'] = True
        settings['enable_lsd'] = True
        settings['enable_upnp'] = True
        settings['enable_natpmp'] = True
        self.ses.apply_settings(settings)

        self.running = True
        self.update_thread = threading.Thread(target=self.update_loop, daemon=True)
        self.update_thread.start()

    def search_torrents(self):
        """Search for torrents"""
        query = self.search_entry.get().strip()
        if not query:
            messagebox.showwarning("Warning", "Please enter a search query")
            return

        # Clear previous results
        for item in self.search_tree.get_children():
            self.search_tree.delete(item)

        self.status_var.set(f"Searching for '{query}'...")
        self.search_results = []

        # Run search in background thread
        def do_search():
            try:
                results = self.searcher.search_all(query, limit=50)
                self.search_results = results

                # Update UI in main thread
                self.root.after(0, lambda: self.display_search_results(results))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Search Error", str(e)))

        threading.Thread(target=do_search, daemon=True).start()

    def display_search_results(self, results):
        """Display search results in tree"""
        # Clear tree
        for item in self.search_tree.get_children():
            self.search_tree.delete(item)

        # Add results
        for result in results:
            self.search_tree.insert('', 'end', values=(
                result['name'],
                result['size'],
                result['seeders'],
                result['source']
            ))

        self.status_var.set(f"Found {len(results)} results")

    def download_from_search(self, event=None):
        """Download selected search result"""
        selection = self.search_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a torrent to download")
            return

        # Get selected result
        item = selection[0]
        values = self.search_tree.item(item, 'values')
        name = values[0]

        # Find the result
        for result in self.search_results:
            if result['name'] == name:
                # Switch to downloads tab
                self.notebook.select(1)

                # Download
                magnet = result['magnet']
                if magnet.startswith('http'):
                    # It's a torrent file URL, download it
                    self.add_torrent_from_url(magnet, result['name'])
                else:
                    # It's a magnet link
                    self.add_magnet_direct(magnet)
                break

    def view_details(self):
        """View details of selected search result"""
        selection = self.search_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a torrent to view")
            return

        item = selection[0]
        values = self.search_tree.item(item, 'values')
        name = values[0]

        for result in self.search_results:
            if result['name'] == name:
                details = f"Name: {result['name']}\n"
                details += f"Size: {result['size']}\n"
                details += f"Seeders: {result['seeders']}\n"
                details += f"Source: {result['source']}\n"
                details += f"Link: {result['link']}\n"
                details += f"\nMagnet/Torrent:\n{result['magnet']}"

                messagebox.showinfo("Torrent Details", details)
                break

    def add_torrent_from_url(self, url, name):
        """Download and add torrent from URL"""
        self.status_var.set(f"Downloading torrent file for {name}...")

        def download_and_add():
            try:
                import requests
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    # Sanitize filename to prevent path traversal
                    safe_name = sanitize_filename(name)
                    temp_path = os.path.join('/tmp', f"{safe_name}.torrent")

                    with open(temp_path, 'wb') as f:
                        f.write(response.content)

                    # Add torrent
                    self.root.after(0, lambda: self.add_torrent_file(temp_path))
                else:
                    self.root.after(0, lambda: messagebox.showerror("Error",
                                    "Failed to download torrent file"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))

        threading.Thread(target=download_and_add, daemon=True).start()

    def browse_torrent(self):
        """Browse for torrent file"""
        filename = filedialog.askopenfilename(
            title="Select Torrent File",
            filetypes=[("Torrent files", "*.torrent"), ("All files", "*.*")]
        )
        if filename:
            self.add_torrent_file(filename)

    def add_torrent_file(self, filepath):
        """Add a torrent file"""
        try:
            os.makedirs(self.download_path, exist_ok=True)

            info = lt.torrent_info(filepath)
            params = {
                'ti': info,
                'save_path': self.download_path,
                'storage_mode': lt.storage_mode_t.storage_mode_sparse,
            }

            handle = self.ses.add_torrent(params)

            item_id = self.tree.insert('', 'end', values=(
                info.name(),
                format_size(info.total_size()),
                '0%',
                '0 KB/s',
                '0',
                'Added'
            ))

            self.torrents.append({
                'handle': handle,
                'info': info,
                'item_id': item_id,
                'completed': False
            })

            self.status_var.set(f"Added: {info.name()}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to add torrent: {e}")

    def add_magnet(self):
        """Add a magnet link from entry"""
        magnet = self.magnet_entry.get().strip()
        if magnet:
            self.add_magnet_direct(magnet)
            self.magnet_entry.delete(0, tk.END)

    def add_magnet_direct(self, magnet):
        """Add a magnet link directly"""
        if not magnet.startswith('magnet:?'):
            messagebox.showerror("Error", "Invalid magnet link")
            return

        try:
            os.makedirs(self.download_path, exist_ok=True)

            magnet_params = lt.parse_magnet_uri(magnet)
            params = {
                'save_path': self.download_path,
                'storage_mode': lt.storage_mode_t.storage_mode_sparse,
            }
            params.update(magnet_params)

            handle = self.ses.add_torrent(params)

            item_id = self.tree.insert('', 'end', values=(
                'Fetching metadata...',
                '?',
                '0%',
                '0 KB/s',
                '0',
                'Metadata'
            ))

            self.torrents.append({
                'handle': handle,
                'info': None,
                'item_id': item_id,
                'completed': False
            })

            self.status_var.set("Added magnet link")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to add magnet: {e}")

    def browse_download_path(self):
        """Browse for download directory"""
        directory = filedialog.askdirectory(title="Select Download Directory")
        if directory:
            self.download_path = directory
            self.path_label.config(text=directory)

    def apply_limits(self):
        """Apply bandwidth limits"""
        try:
            download_limit = int(self.download_limit_var.get()) * 1000
            upload_limit = int(self.upload_limit_var.get()) * 1000

            settings = self.ses.get_settings()
            settings['download_rate_limit'] = download_limit
            settings['upload_rate_limit'] = upload_limit
            self.ses.apply_settings(settings)

            dl_text = f"{int(download_limit/1000)} KB/s" if download_limit > 0 else "unlimited"
            ul_text = f"{int(upload_limit/1000)} KB/s" if upload_limit > 0 else "unlimited"

            self.status_var.set(f"Limits: Download {dl_text}, Upload {ul_text}")
            messagebox.showinfo("Success", "Bandwidth limits applied!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply limits: {e}")

    def remove_selected(self):
        """Remove selected torrent"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a torrent to remove")
            return

        if messagebox.askyesno("Confirm", "Remove selected torrent?"):
            for item_id in selection:
                for i, torrent in enumerate(self.torrents):
                    if torrent['item_id'] == item_id:
                        self.ses.remove_torrent(torrent['handle'])
                        self.torrents.pop(i)
                        break
                self.tree.delete(item_id)

            self.status_var.set("Torrent removed")

    def clear_completed(self):
        """Clear all completed torrents"""
        to_remove = []
        for torrent in self.torrents:
            if torrent['completed']:
                to_remove.append(torrent)

        for torrent in to_remove:
            self.tree.delete(torrent['item_id'])
            self.torrents.remove(torrent)

        self.status_var.set(f"Cleared {len(to_remove)} completed torrent(s)")

    def update_loop(self):
        """Background thread to update torrent status"""
        while self.running:
            try:
                for torrent in self.torrents:
                    handle = torrent['handle']
                    s = handle.status()

                    if torrent['info'] is None and s.has_metadata:
                        torrent['info'] = handle.torrent_file()

                    if torrent['info']:
                        name = s.name[:40]
                        size = format_size(torrent['info'].total_size())
                    else:
                        name = "Fetching metadata..."
                        size = "?"

                    progress = f"{s.progress * 100:.1f}%"
                    download_rate = s.download_rate / 1000
                    upload_rate = s.upload_rate / 1000
                    speed = f"↓{download_rate:.0f} ↑{upload_rate:.0f} KB/s"
                    peers = str(s.num_peers)

                    if s.is_seeding:
                        status = "Seeding"
                        if not torrent['completed']:
                            torrent['completed'] = True
                            send_notification("Download Complete", f"{name}")
                    elif s.state == lt.torrent_status.downloading:
                        status = "Downloading"
                    elif s.state == lt.torrent_status.checking_files:
                        status = "Checking"
                    elif s.has_metadata:
                        status = "Queued"
                    else:
                        status = "Metadata"

                    self.tree.item(torrent['item_id'], values=(
                        name, size, progress, speed, peers, status
                    ))

            except Exception as e:
                print(f"Update error: {e}")

            time.sleep(1)

    def on_closing(self):
        """Handle window closing"""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.running = False
            self.root.destroy()


def main():
    root = tk.Tk()
    app = TorrentGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
