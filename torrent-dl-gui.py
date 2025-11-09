#!/usr/bin/env python3
"""
GUI Torrent Downloader
A simple graphical interface for downloading torrents
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import libtorrent as lt
import threading
import time
import os
from torrent_utils import format_size, format_speed, send_notification, sanitize_filename


class TorrentGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Torrent Downloader")
        self.root.geometry("900x700")

        # Session and torrents
        self.ses = None
        self.torrents = []  # List of (handle, info_dict) tuples
        self.torrents_lock = threading.Lock()  # Protect torrents list from race conditions
        self.running = False

        # Settings
        self.download_path = os.path.expanduser("~/Downloads/torrents")
        self.max_download_rate = 0  # 0 = unlimited
        self.max_upload_rate = 0    # 0 = unlimited

        self.setup_ui()
        self.init_session()

    def setup_ui(self):
        """Setup the user interface"""
        # Create main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)

        # Title
        title_label = ttk.Label(main_frame, text="🌐 Torrent Downloader",
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, pady=(0, 10))

        # Add Torrent Section
        add_frame = ttk.LabelFrame(main_frame, text="Add Torrent", padding="10")
        add_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        add_frame.columnconfigure(1, weight=1)

        # Torrent file selection
        ttk.Label(add_frame, text="Torrent File:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Button(add_frame, text="Browse...",
                  command=self.browse_torrent).grid(row=0, column=1, sticky=tk.W, padx=5)

        # Magnet link input
        ttk.Label(add_frame, text="Magnet Link:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.magnet_entry = ttk.Entry(add_frame, width=50)
        self.magnet_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(add_frame, text="Add",
                  command=self.add_magnet).grid(row=1, column=2, padx=5)

        # Download path
        ttk.Label(add_frame, text="Save to:").grid(row=2, column=0, sticky=tk.W, pady=5)
        path_frame = ttk.Frame(add_frame)
        path_frame.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=5)
        path_frame.columnconfigure(0, weight=1)

        self.path_label = ttk.Label(path_frame, text=self.download_path,
                                    relief=tk.SUNKEN, padding=5)
        self.path_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Button(path_frame, text="Change",
                  command=self.browse_download_path).grid(row=0, column=1, padx=(5, 0))

        # Downloads List
        downloads_frame = ttk.LabelFrame(main_frame, text="Active Downloads", padding="10")
        downloads_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        downloads_frame.columnconfigure(0, weight=1)
        downloads_frame.rowconfigure(0, weight=1)

        # Create Treeview for downloads
        columns = ('Name', 'Size', 'Progress', 'Speed', 'Peers', 'Status')
        self.tree = ttk.Treeview(downloads_frame, columns=columns, show='headings', height=10)

        # Define headings
        self.tree.heading('Name', text='Name')
        self.tree.heading('Size', text='Size')
        self.tree.heading('Progress', text='Progress')
        self.tree.heading('Speed', text='Speed')
        self.tree.heading('Peers', text='Peers')
        self.tree.heading('Status', text='Status')

        # Define column widths
        self.tree.column('Name', width=300)
        self.tree.column('Size', width=80)
        self.tree.column('Progress', width=80)
        self.tree.column('Speed', width=100)
        self.tree.column('Peers', width=60)
        self.tree.column('Status', width=100)

        # Add scrollbar
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

        # Settings Section
        settings_frame = ttk.LabelFrame(main_frame, text="Settings", padding="10")
        settings_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        # Bandwidth limits
        ttk.Label(settings_frame, text="Download Limit (KB/s):").grid(row=0, column=0,
                                                                      sticky=tk.W, padx=5)
        self.download_limit_var = tk.StringVar(value="0")
        download_spin = ttk.Spinbox(settings_frame, from_=0, to=10000, increment=100,
                                   textvariable=self.download_limit_var, width=10)
        download_spin.grid(row=0, column=1, sticky=tk.W, padx=5)
        ttk.Label(settings_frame, text="(0 = unlimited)").grid(row=0, column=2, sticky=tk.W)

        ttk.Label(settings_frame, text="Upload Limit (KB/s):").grid(row=1, column=0,
                                                                    sticky=tk.W, padx=5, pady=5)
        self.upload_limit_var = tk.StringVar(value="0")
        upload_spin = ttk.Spinbox(settings_frame, from_=0, to=10000, increment=100,
                                 textvariable=self.upload_limit_var, width=10)
        upload_spin.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(settings_frame, text="(0 = unlimited)").grid(row=1, column=2, sticky=tk.W)

        ttk.Button(settings_frame, text="Apply Limits",
                  command=self.apply_limits).grid(row=0, column=3, rowspan=2, padx=20)

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var,
                              relief=tk.SUNKEN, padding=5)
        status_bar.grid(row=4, column=0, sticky=(tk.W, tk.E))

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

        # Start update thread
        self.running = True
        self.update_thread = threading.Thread(target=self.update_loop, daemon=True)
        self.update_thread.start()

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

            # Add to tree
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
        """Add a magnet link"""
        magnet = self.magnet_entry.get().strip()
        if not magnet:
            messagebox.showwarning("Warning", "Please enter a magnet link")
            return

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

            # Add to tree with placeholder name
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

            self.magnet_entry.delete(0, tk.END)
            self.status_var.set("Added magnet link, fetching metadata...")

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
            download_limit = int(self.download_limit_var.get()) * 1000  # Convert to bytes
            upload_limit = int(self.upload_limit_var.get()) * 1000

            settings = self.ses.get_settings()
            settings['download_rate_limit'] = download_limit
            settings['upload_rate_limit'] = upload_limit
            self.ses.apply_settings(settings)

            dl_text = f"{int(download_limit/1000)} KB/s" if download_limit > 0 else "unlimited"
            ul_text = f"{int(upload_limit/1000)} KB/s" if upload_limit > 0 else "unlimited"

            self.status_var.set(f"Limits applied - Download: {dl_text}, Upload: {ul_text}")
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
                # Find and remove torrent
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

                    # Update info for magnet links once metadata is available
                    if torrent['info'] is None and s.has_metadata:
                        torrent['info'] = handle.torrent_file()

                    # Get info
                    if torrent['info']:
                        name = s.name[:40]
                        size = format_size(torrent['info'].total_size())
                    else:
                        name = "Fetching metadata..."
                        size = "?"

                    progress = f"{s.progress * 100:.1f}%"
                    download_rate = s.download_rate / 1000  # KB/s
                    upload_rate = s.upload_rate / 1000
                    speed = f"↓{download_rate:.0f} ↑{upload_rate:.0f} KB/s"
                    peers = str(s.num_peers)

                    # Status
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

                    # Update tree
                    self.tree.item(torrent['item_id'], values=(
                        name, size, progress, speed, peers, status
                    ))

            except Exception as e:
                print(f"Update error: {e}")

            time.sleep(1)

    def on_closing(self):
        """Handle window closing"""
        if messagebox.askokcancel("Quit", "Do you want to quit? Active downloads will be stopped."):
            self.running = False
            if self.ses:
                # Save session state would go here
                pass
            self.root.destroy()


def main():
    root = tk.Tk()
    app = TorrentGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
