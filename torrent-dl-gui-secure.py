#!/usr/bin/env python3
"""
Secure Torrent Downloader with Privacy & Security Features
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import libtorrent as lt
import threading
import time
import os
import sys
import json
import socket
import tempfile
from torrent_search import TorrentSearcher
from privacy_security import PrivacySecurityChecker
from torrent_utils import format_size, send_notification, sanitize_filename


class SecureTorrentGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Secure Torrent Downloader")
        self.root.geometry("1050x800")

        # Session and torrents
        self.ses = None
        self.torrents = []
        self.torrents_lock = threading.Lock()  # Protect torrents list from race conditions
        self.running = False
        self.metadata_saved = set()  # Track which magnets have saved metadata

        # Search and security
        self.searcher = TorrentSearcher()
        self.security_checker = PrivacySecurityChecker()
        self.search_results = []
        self.sort_column = None
        self.sort_reverse = False

        # Config paths
        self.config_dir = os.path.expanduser("~/.config/torrent-downloader")
        self.config_file = os.path.join(self.config_dir, "settings.json")
        self.session_file = os.path.join(self.config_dir, "session.state")
        self.resume_dir = os.path.join(self.config_dir, "resume")
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.resume_dir, exist_ok=True)

        # Single instance socket
        self.socket_path = os.path.join(tempfile.gettempdir(), "torrent-downloader-gui.sock")
        self.ipc_socket = None
        self.start_ipc_server()

        # Dark mode
        self.dark_mode = False
        self.setup_themes()

        # Settings (defaults, will be overwritten by load_settings)
        self.download_path = os.path.expanduser("~/Downloads/torrents")
        # Reasonable defaults: 1 MB/s download, 200 KB/s upload (in bytes/sec)
        self.max_download_rate = 1000 * 1000  # 1000 KB/s = 1 MB/s
        self.max_upload_rate = 200 * 1000     # 200 KB/s

        # Privacy settings
        self.encryption_enabled = True
        self.dht_enabled = True  # Can be disabled for more privacy

        # Load saved settings
        self.load_settings()

        self.setup_ui()
        self.init_session()
        self.load_session_state()
        self.check_security_on_start()

    def check_security_on_start(self):
        """Check security status when app starts"""
        def do_check():
            time.sleep(2)  # Wait for UI to load
            vpn_check = self.security_checker.check_vpn_status()

            if not vpn_check.get('secure'):
                self.root.after(0, lambda: self.show_vpn_warning())

        threading.Thread(target=do_check, daemon=True).start()

    def load_settings(self):
        """Load settings from config file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    settings = json.load(f)

                self.download_path = settings.get('download_path', self.download_path)
                self.max_download_rate = settings.get('max_download_rate', 0)
                self.max_upload_rate = settings.get('max_upload_rate', 0)
                self.dark_mode = settings.get('dark_mode', False)
                self.encryption_enabled = settings.get('encryption_enabled', True)
                self.dht_enabled = settings.get('dht_enabled', True)
        except Exception as e:
            print(f"Failed to load settings: {e}")

    def save_settings(self):
        """Save settings to config file"""
        try:
            settings = {
                'download_path': self.download_path,
                'max_download_rate': self.max_download_rate,
                'max_upload_rate': self.max_upload_rate,
                'dark_mode': self.dark_mode,
                'encryption_enabled': self.encryption_enabled,
                'dht_enabled': self.dht_enabled
            }

            with open(self.config_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Failed to save settings: {e}")

    def load_session_state(self):
        """Load saved torrents and resume them"""
        try:
            # Load all .torrent and .fastresume files from resume directory
            if not os.path.exists(self.resume_dir):
                return

            # Find all unique info hashes from any file type
            all_files = os.listdir(self.resume_dir)
            info_hashes = set()

            for filename in all_files:
                if filename.endswith(('.fastresume', '.torrent', '.magnet')):
                    info_hash = filename.rsplit('.', 1)[0]
                    info_hashes.add(info_hash)

            for info_hash in info_hashes:
                resume_file = os.path.join(self.resume_dir, f"{info_hash}.fastresume")

                try:
                    # Load resume data if available and valid
                    if os.path.exists(resume_file) and os.path.getsize(resume_file) > 10:
                        try:
                            with open(resume_file, 'rb') as f:
                                resume_data = f.read()
                            # Use read_resume_data() for proper loading
                            params = lt.read_resume_data(resume_data)
                            params.save_path = self.download_path
                            print(f"  Loaded resume data for {info_hash}")
                        except Exception as e:
                            print(f"  Resume data invalid, starting fresh: {e}")
                            # Invalid resume data, create fresh params
                            params = lt.add_torrent_params()
                            params.save_path = self.download_path
                    else:
                        # No resume data or file too small (corrupted), create fresh params
                        if os.path.exists(resume_file):
                            print(f"  Resume file too small ({os.path.getsize(resume_file)} bytes), starting fresh")
                        params = lt.add_torrent_params()
                        params.save_path = self.download_path

                    # Check for .torrent file first (preferred)
                    torrent_file = os.path.join(self.resume_dir, f"{info_hash}.torrent")
                    if os.path.exists(torrent_file):
                        # Load full torrent info
                        ti = lt.torrent_info(torrent_file)
                        params.ti = ti
                        print(f"Loading torrent: {ti.name()}")
                    else:
                        # Fall back to .magnet file
                        magnet_file = os.path.join(self.resume_dir, f"{info_hash}.magnet")
                        if os.path.exists(magnet_file):
                            with open(magnet_file, 'r') as f:
                                magnet = f.read().strip()
                            # Parse magnet and update params
                            magnet_params = lt.parse_magnet_uri(magnet)
                            params.info_hash = magnet_params.info_hash
                            if magnet_params.name:
                                params.name = magnet_params.name
                            params.trackers = magnet_params.trackers
                            print(f"Loading magnet: {magnet_params.name or info_hash}")
                        else:
                            # No metadata available, just use info hash
                            print(f"Loading torrent by info hash: {info_hash}")

                    # Add the torrent
                    handle = self.ses.add_torrent(params)

                    # Check existing files
                    handle.force_recheck()

                    # Add to UI
                    item_id = self.tree.insert('', 'end', values=(
                        'Loading...',
                        '?',
                        '0%',
                        '0 KB/s',
                        '0',
                        'Checking files'
                    ))

                    with self.torrents_lock:
                        self.torrents.append({
                            'handle': handle,
                            'info': handle.torrent_file() if handle.torrent_file() else None,
                            'item_id': item_id,
                            'completed': False
                        })

                    # Mark metadata as saved if we have torrent file
                    if os.path.exists(torrent_file):
                        self.metadata_saved.add(info_hash)

                except Exception as e:
                    print(f"Failed to resume {filename}: {e}")
                    import traceback
                    traceback.print_exc()

        except Exception as e:
            print(f"Failed to load session state: {e}")
            import traceback
            traceback.print_exc()

    def save_session_state(self):
        """Save all torrents for resume"""
        try:
            if not self.ses:
                return

            # Request resume data for all torrents
            for torrent in self.torrents:
                try:
                    handle = torrent['handle']
                    if handle.is_valid():
                        handle.save_resume_data()
                except:
                    pass

            # Wait a bit for resume data alerts
            time.sleep(0.5)

            # Process alerts and save resume data
            alerts = self.ses.pop_alerts()
            for alert in alerts:
                if isinstance(alert, lt.save_resume_data_alert):
                    try:
                        handle = alert.handle
                        status = handle.status()
                        info_hash = str(status.info_hash)

                        # Save resume data
                        resume_file = os.path.join(self.resume_dir, f"{info_hash}.fastresume")
                        with open(resume_file, 'wb') as f:
                            f.write(lt.bencode(alert.params))

                        # Save torrent metadata if available
                        if handle.torrent_file():
                            ti = handle.torrent_file()

                            # Save .torrent file (preferred for resume)
                            torrent_file = os.path.join(self.resume_dir, f"{info_hash}.torrent")
                            try:
                                # Create torrent from torrent_info and generate bencode
                                ct = lt.create_torrent(ti)
                                torrent_data = lt.bencode(ct.generate())
                                with open(torrent_file, 'wb') as f:
                                    f.write(torrent_data)
                            except Exception as e:
                                print(f"Could not save .torrent file: {e}")

                            # Also save magnet link as backup
                            try:
                                magnet = lt.make_magnet_uri(ti)
                                magnet_file = os.path.join(self.resume_dir, f"{info_hash}.magnet")
                                with open(magnet_file, 'w') as f:
                                    f.write(magnet)
                            except Exception as e:
                                print(f"Could not save .magnet file: {e}")

                    except Exception as e:
                        print(f"Failed to save torrent resume data: {e}")

        except Exception as e:
            print(f"Failed to save session state: {e}")

    def show_vpn_warning(self):
        """Show VPN warning on startup"""
        response = messagebox.askwarning(
            "VPN Not Detected",
            "⚠️ No VPN detected!\n\n"
            "Your IP address is visible to other peers and your ISP.\n\n"
            "For privacy, it's recommended to use a VPN.\n\n"
            "Check the Privacy tab for more information.\n\n"
            "Continue anyway?",
            type=messagebox.OKCANCEL
        )

        if response == 'cancel':
            self.on_closing()

    def setup_themes(self):
        """Setup light and dark themes"""
        self.themes = {
            'light': {
                'bg': '#f0f0f0',
                'fg': '#000000',
                'select_bg': '#0078d7',
                'select_fg': '#ffffff',
                'entry_bg': '#ffffff',
                'button_bg': '#e1e1e1'
            },
            'dark': {
                'bg': '#2b2b2b',
                'fg': '#ffffff',
                'select_bg': '#404040',
                'select_fg': '#ffffff',
                'entry_bg': '#3c3c3c',
                'button_bg': '#3c3c3c'
            }
        }

    def toggle_dark_mode(self):
        """Toggle between dark and light mode"""
        self.dark_mode = not self.dark_mode
        self.apply_theme()
        self.save_settings()

    def apply_theme(self):
        """Apply the selected theme"""
        theme = self.themes['dark'] if self.dark_mode else self.themes['light']

        # Configure root window
        self.root.configure(bg=theme['bg'])

        # Configure ttk styles
        style = ttk.Style()

        # Frame style
        style.configure('TFrame', background=theme['bg'])
        style.configure('TLabelframe', background=theme['bg'], foreground=theme['fg'])
        style.configure('TLabelframe.Label', background=theme['bg'], foreground=theme['fg'])

        # Label style
        style.configure('TLabel', background=theme['bg'], foreground=theme['fg'])

        # Button style
        style.configure('TButton', background=theme['button_bg'], foreground=theme['fg'])
        style.map('TButton', background=[('active', theme['select_bg'])])

        # Entry style
        style.configure('TEntry', fieldbackground=theme['entry_bg'], foreground=theme['fg'])

        # Treeview style
        style.configure('Treeview',
                       background=theme['entry_bg'],
                       foreground=theme['fg'],
                       fieldbackground=theme['entry_bg'])
        style.map('Treeview',
                 background=[('selected', theme['select_bg'])],
                 foreground=[('selected', theme['select_fg'])])
        style.configure('Treeview.Heading',
                       background=theme['button_bg'],
                       foreground=theme['fg'])

        # Notebook style
        style.configure('TNotebook', background=theme['bg'])
        style.configure('TNotebook.Tab', background=theme['button_bg'], foreground=theme['fg'])
        style.map('TNotebook.Tab',
                 background=[('selected', theme['select_bg'])],
                 foreground=[('selected', theme['select_fg'])])

        # Checkbutton style
        style.configure('TCheckbutton', background=theme['bg'], foreground=theme['fg'])

        # Update button text
        if hasattr(self, 'dark_mode_button'):
            self.dark_mode_button.config(text='🌞 Light Mode' if self.dark_mode else '🌙 Dark Mode')

    def setup_ui(self):
        """Setup the user interface"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Title
        title_label = ttk.Label(main_frame, text="🔒 Secure Torrent Downloader",
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, pady=(0, 10))

        # Initialize status var before tabs (needed by privacy tab)
        self.status_var = tk.StringVar(value="Ready - Check Privacy tab for security status")

        # Create notebook
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Tabs
        self.privacy_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.privacy_tab, text="🔒 Privacy")
        self.setup_privacy_tab()

        self.search_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.search_tab, text="🔍 Search")
        self.setup_search_tab()

        self.downloads_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.downloads_tab, text="📥 Downloads")
        self.setup_downloads_tab()

        self.settings_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.settings_tab, text="⚙️ Settings")
        self.setup_settings_tab()

        # Status bar (status_var already initialized above)
        status_bar = ttk.Label(main_frame, textvariable=self.status_var,
                              relief=tk.SUNKEN, padding=5)
        status_bar.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))

        # Bandwidth status bar
        self.bandwidth_var = tk.StringVar(value="Bandwidth: ↓ 0 KB/s  ↑ 0 KB/s")
        bandwidth_bar = ttk.Label(main_frame, textvariable=self.bandwidth_var,
                                 relief=tk.SUNKEN, padding=5, font=('TkDefaultFont', 9, 'bold'))
        bandwidth_bar.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(5, 0))

        # Apply initial theme
        self.apply_theme()

    def setup_privacy_tab(self):
        """Setup privacy and security tab"""
        self.privacy_tab.columnconfigure(0, weight=1)
        self.privacy_tab.rowconfigure(2, weight=1)

        # Warning banner
        warning_frame = ttk.Frame(self.privacy_tab, relief=tk.RAISED, borderwidth=2)
        warning_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        warning_frame.columnconfigure(0, weight=1)

        ttk.Label(warning_frame,
                 text="⚠️ IMPORTANT: Always use a VPN when torrenting for privacy!",
                 font=('Arial', 11, 'bold'),
                 foreground='red').grid(row=0, column=0, pady=5, padx=10)

        # Security Status
        status_frame = ttk.LabelFrame(self.privacy_tab, text="Security Status", padding="10")
        status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(1, weight=1)

        # VPN Status
        ttk.Label(status_frame, text="VPN:", font=('Arial', 10, 'bold')).grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.vpn_status_label = ttk.Label(status_frame, text="Checking...",
                                          foreground="gray")
        self.vpn_status_label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        # Public IP
        ttk.Label(status_frame, text="Public IP:", font=('Arial', 10, 'bold')).grid(
            row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.ip_status_label = ttk.Label(status_frame, text="Checking...",
                                         foreground="gray")
        self.ip_status_label.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

        # DNS
        ttk.Label(status_frame, text="DNS:", font=('Arial', 10, 'bold')).grid(
            row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.dns_status_label = ttk.Label(status_frame, text="Checking...",
                                          foreground="gray")
        self.dns_status_label.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)

        # Firewall
        ttk.Label(status_frame, text="Firewall:", font=('Arial', 10, 'bold')).grid(
            row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.firewall_status_label = ttk.Label(status_frame, text="Checking...",
                                               foreground="gray")
        self.firewall_status_label.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)

        # Refresh button
        ttk.Button(status_frame, text="🔄 Refresh Security Check",
                  command=self.refresh_security_status).grid(row=4, column=0,
                                                             columnspan=2, pady=10)

        # Recommendations
        rec_frame = ttk.LabelFrame(self.privacy_tab, text="Security Recommendations",
                                  padding="10")
        rec_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        rec_frame.columnconfigure(0, weight=1)
        rec_frame.rowconfigure(0, weight=1)

        # Recommendations text
        self.recommendations_text = tk.Text(rec_frame, height=12, wrap=tk.WORD,
                                           font=('Courier', 9))
        self.recommendations_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        rec_scroll = ttk.Scrollbar(rec_frame, orient=tk.VERTICAL,
                                   command=self.recommendations_text.yview)
        self.recommendations_text.configure(yscrollcommand=rec_scroll.set)
        rec_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # Quick actions
        actions_frame = ttk.Frame(self.privacy_tab)
        actions_frame.grid(row=3, column=0, pady=(10, 0))

        ttk.Button(actions_frame, text="📖 View Security Guide",
                  command=self.view_security_guide).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="🔍 Test IP Leak",
                  command=self.test_ip_leak).pack(side=tk.LEFT, padx=5)

        # Run initial check
        self.refresh_security_status()

    def refresh_security_status(self):
        """Refresh security status"""
        self.status_var.set("Running security checks...")

        def do_check():
            try:
                # Run all checks
                vpn = self.security_checker.check_vpn_status()
                ip = self.security_checker.check_public_ip()
                dns = self.security_checker.check_dns_leak()
                firewall = self.security_checker.check_firewall_status()
                recommendations = self.security_checker.get_security_recommendations()

                # Update UI
                self.root.after(0, lambda: self.update_security_ui(
                    vpn, ip, dns, firewall, recommendations))

            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error",
                               f"Security check failed: {e}"))

        threading.Thread(target=do_check, daemon=True).start()

    def update_security_ui(self, vpn, ip, dns, firewall, recommendations):
        """Update security UI with check results"""
        # VPN
        if vpn.get('secure'):
            self.vpn_status_label.config(text="✅ " + vpn.get('message'), foreground="green")
        else:
            self.vpn_status_label.config(text="⚠️ " + vpn.get('message'), foreground="red")

        # IP
        self.ip_status_label.config(text=ip.get('message'), foreground="blue")

        # DNS
        if dns.get('secure'):
            self.dns_status_label.config(text="✅ " + dns.get('message'), foreground="green")
        else:
            self.dns_status_label.config(text="⚠️ " + dns.get('message'), foreground="orange")

        # Firewall
        if firewall.get('secure'):
            self.firewall_status_label.config(text="✅ " + firewall.get('message'),
                                             foreground="green")
        else:
            self.firewall_status_label.config(text="⚠️ " + firewall.get('message'),
                                             foreground="orange")

        # Recommendations
        self.recommendations_text.delete('1.0', tk.END)

        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                level_icons = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
                icon = level_icons.get(rec['level'], '⚪')

                self.recommendations_text.insert(tk.END,
                    f"{i}. {icon} {rec['category']}: {rec['issue']}\n")
                self.recommendations_text.insert(tk.END,
                    f"   {rec['recommendation']}\n")
                self.recommendations_text.insert(tk.END,
                    f"   Action: {rec['action']}\n\n")
        else:
            self.recommendations_text.insert(tk.END, "✅ All security checks passed!\n\n")
            self.recommendations_text.insert(tk.END, "You're good to go!")

        self.status_var.set("Security check complete")

    def view_security_guide(self):
        """Open security guide"""
        guide_path = os.path.expanduser("~/PRIVACY-SECURITY-GUIDE.md")
        if os.path.exists(guide_path):
            subprocess.Popen(['xdg-open', guide_path])
        else:
            messagebox.showinfo("Guide", "Security guide: ~/PRIVACY-SECURITY-GUIDE.md")

    def test_ip_leak(self):
        """Open IP leak test website"""
        import webbrowser
        webbrowser.open("https://ipleak.net/")
        messagebox.showinfo("IP Leak Test",
                          "Opening IP leak test in your browser.\n\n"
                          "Check if your real IP is exposed!")

    def setup_search_tab(self):
        """Setup search tab (same as before)"""
        self.search_tab.columnconfigure(0, weight=1)
        self.search_tab.rowconfigure(2, weight=1)

        search_frame = ttk.LabelFrame(self.search_tab, text="Search for Torrents", padding="10")
        search_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        search_frame.columnconfigure(1, weight=1)

        ttk.Label(search_frame, text="Query:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.search_entry = ttk.Entry(search_frame, width=50)
        self.search_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        self.search_entry.bind('<Return>', lambda e: self.search_torrents())

        ttk.Button(search_frame, text="Search",
                  command=self.search_torrents).grid(row=0, column=2, padx=5)

        info_label = ttk.Label(self.search_tab,
                              text="🔒 Searches legal sources: Creative Commons, Linux Distros, Internet Archive",
                              foreground="gray")
        info_label.grid(row=1, column=0, pady=(0, 10))

        results_frame = ttk.LabelFrame(self.search_tab, text="Search Results", padding="10")
        results_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)

        columns = ('Name', 'Size', 'Seeders', 'Source')
        self.search_tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=15)

        # Make column headers clickable for sorting
        self.search_tree.heading('Name', text='Name ▼', command=lambda: self.sort_search_results('name'))
        self.search_tree.heading('Size', text='Size ▼', command=lambda: self.sort_search_results('size'))
        self.search_tree.heading('Seeders', text='Seeders ▼', command=lambda: self.sort_search_results('seeders'))
        self.search_tree.heading('Source', text='Source ▼', command=lambda: self.sort_search_results('source'))

        self.search_tree.column('Name', width=400)
        self.search_tree.column('Size', width=100)
        self.search_tree.column('Seeders', width=100)
        self.search_tree.column('Source', width=150)

        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL,
                                 command=self.search_tree.yview)
        self.search_tree.configure(yscrollcommand=scrollbar.set)

        self.search_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        self.search_tree.bind('<Double-1>', self.download_from_search)

        button_frame = ttk.Frame(results_frame)
        button_frame.grid(row=1, column=0, pady=(10, 0))

        ttk.Button(button_frame, text="Download Selected",
                  command=self.download_from_search).pack(side=tk.LEFT, padx=5)

    def setup_downloads_tab(self):
        """Setup downloads tab (simplified version)"""
        self.downloads_tab.columnconfigure(0, weight=1)
        self.downloads_tab.rowconfigure(1, weight=1)

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

        downloads_frame = ttk.LabelFrame(self.downloads_tab, text="Active Downloads", padding="10")
        downloads_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        downloads_frame.columnconfigure(0, weight=1)
        downloads_frame.rowconfigure(0, weight=1)

        columns = ('Name', 'Size', 'Progress', 'Speed', 'Peers', 'Status')
        self.tree = ttk.Treeview(downloads_frame, columns=columns, show='headings', height=12)

        for col in columns:
            self.tree.heading(col, text=col)

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

        control_frame = ttk.Frame(downloads_frame)
        control_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0))

        ttk.Button(control_frame, text="Remove Selected",
                  command=self.remove_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Clear Completed",
                  command=self.clear_completed).pack(side=tk.LEFT, padx=5)

    def setup_settings_tab(self):
        """Setup settings tab with privacy options"""
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

        # Privacy settings
        privacy_frame = ttk.LabelFrame(self.settings_tab, text="Privacy Settings", padding="10")
        privacy_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        self.encryption_var = tk.BooleanVar(value=self.encryption_enabled)
        ttk.Checkbutton(privacy_frame, text="Enable Protocol Encryption (Recommended)",
                       variable=self.encryption_var).grid(row=0, column=0,
                                                          sticky=tk.W, pady=5)

        self.dht_var = tk.BooleanVar(value=self.dht_enabled)
        ttk.Checkbutton(privacy_frame, text="Enable DHT (Better performance, less privacy)",
                       variable=self.dht_var).grid(row=1, column=0, sticky=tk.W, pady=5)

        ttk.Button(privacy_frame, text="Apply Privacy Settings",
                  command=self.apply_privacy_settings).grid(row=2, column=0, pady=10)

        # Bandwidth limits
        bandwidth_frame = ttk.LabelFrame(self.settings_tab, text="Bandwidth Limits", padding="10")
        bandwidth_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))

        ttk.Label(bandwidth_frame, text="Download Limit (KB/s):").grid(row=0, column=0,
                                                                       sticky=tk.W, padx=5)
        self.download_limit_var = tk.StringVar(value=str(self.max_download_rate // 1000))
        ttk.Spinbox(bandwidth_frame, from_=0, to=10000, increment=100,
                   textvariable=self.download_limit_var, width=10).grid(row=0, column=1,
                                                                         sticky=tk.W, padx=5)

        ttk.Label(bandwidth_frame, text="Upload Limit (KB/s):").grid(row=1, column=0,
                                                                     sticky=tk.W, padx=5, pady=5)
        self.upload_limit_var = tk.StringVar(value=str(self.max_upload_rate // 1000))
        ttk.Spinbox(bandwidth_frame, from_=0, to=10000, increment=100,
                   textvariable=self.upload_limit_var, width=10).grid(row=1, column=1,
                                                                       sticky=tk.W, padx=5, pady=5)

        ttk.Button(bandwidth_frame, text="Apply Limits",
                  command=self.apply_limits).grid(row=0, column=2, rowspan=2, padx=20)

        # Appearance settings
        appearance_frame = ttk.LabelFrame(self.settings_tab, text="Appearance", padding="10")
        appearance_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(10, 0))

        self.dark_mode_button = ttk.Button(appearance_frame,
                                          text='🌙 Dark Mode',
                                          command=self.toggle_dark_mode)
        self.dark_mode_button.pack(pady=10)

    def init_session(self):
        """Initialize libtorrent session with privacy settings"""
        self.ses = lt.session()
        settings = self.ses.get_settings()
        settings['listen_interfaces'] = '0.0.0.0:6881'
        settings['enable_dht'] = self.dht_enabled
        settings['enable_lsd'] = True
        settings['enable_upnp'] = True
        settings['enable_natpmp'] = True

        # Bandwidth limits (apply saved or default settings)
        settings['download_rate_limit'] = self.max_download_rate
        settings['upload_rate_limit'] = self.max_upload_rate

        # Connection limits to prevent bandwidth hogging
        settings['connections_limit'] = 200        # Max total connections
        settings['active_downloads'] = 3           # Max active downloads at once
        settings['active_seeds'] = 5               # Max active seeds at once
        settings['active_limit'] = 8               # Max active torrents total

        # Per-torrent connection limits
        settings['unchoke_slots_limit'] = 8        # Max upload slots per torrent
        settings['max_peerlist_size'] = 1000       # Limit peer list size

        # Rate-based unchoking for smoother bandwidth usage
        settings['seed_choking_algorithm'] = lt.seed_choking_algorithm_t.fastest_upload
        settings['choking_algorithm'] = lt.choking_algorithm_t.rate_based_choker

        # Privacy: Enable encryption
        if self.encryption_enabled:
            settings['out_enc_policy'] = lt.enc_policy.enabled
            settings['in_enc_policy'] = lt.enc_policy.enabled
            settings['allowed_enc_level'] = lt.enc_level.both
        else:
            settings['out_enc_policy'] = lt.enc_policy.disabled
            settings['in_enc_policy'] = lt.enc_policy.disabled

        self.ses.apply_settings(settings)

        self.running = True
        self.update_thread = threading.Thread(target=self.update_loop, daemon=True)
        self.update_thread.start()

    def apply_privacy_settings(self):
        """Apply privacy settings"""
        try:
            self.encryption_enabled = self.encryption_var.get()
            self.dht_enabled = self.dht_var.get()

            settings = self.ses.get_settings()
            settings['enable_dht'] = self.dht_enabled

            if self.encryption_enabled:
                settings['out_enc_policy'] = lt.enc_policy.enabled
                settings['in_enc_policy'] = lt.enc_policy.enabled
            else:
                settings['out_enc_policy'] = lt.enc_policy.disabled
                settings['in_enc_policy'] = lt.enc_policy.disabled

            self.ses.apply_settings(settings)

            self.save_settings()
            messagebox.showinfo("Success", "Privacy settings applied!")
            self.status_var.set("Privacy settings updated")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply settings: {e}")

    # Rest of the methods (search, download, etc.) similar to previous GUI
    # I'll include key methods below:

    def search_torrents(self):
        """Search for torrents"""
        query = self.search_entry.get().strip()
        if not query:
            messagebox.showwarning("Warning", "Please enter a search query")
            return

        for item in self.search_tree.get_children():
            self.search_tree.delete(item)

        self.status_var.set(f"Searching for '{query}'...")
        self.search_results = []

        def do_search():
            try:
                results = self.searcher.search_all(query, limit=50)
                self.search_results = results
                self.root.after(0, lambda: self.display_search_results(results))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Search Error", str(e)))

        threading.Thread(target=do_search, daemon=True).start()

    def display_search_results(self, results):
        """Display search results"""
        for item in self.search_tree.get_children():
            self.search_tree.delete(item)

        for result in results:
            self.search_tree.insert('', 'end', values=(
                result['name'],
                result['size'],
                result['seeders'],
                result['source']
            ))

        self.status_var.set(f"Found {len(results)} results")

    def sort_search_results(self, column):
        """Sort search results by column"""
        if not self.search_results:
            return

        # Toggle sort direction if clicking same column
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False

        # Define sort key functions
        def get_sort_key(result):
            if column == 'name':
                return result.get('name', '').lower()
            elif column == 'size':
                # Convert size string to bytes for proper sorting
                size_str = result.get('size', '0 B')
                try:
                    parts = size_str.split()
                    if len(parts) == 2:
                        value = float(parts[0])
                        unit = parts[1].upper()
                        multipliers = {'B': 1, 'KB': 1024, 'MB': 1024**2,
                                     'GB': 1024**3, 'TB': 1024**4}
                        return value * multipliers.get(unit, 0)
                except:
                    pass
                return 0
            elif column == 'seeders':
                # Handle "500+" format
                seeders = result.get('seeders', '0')
                try:
                    if isinstance(seeders, str):
                        seeders = seeders.replace('+', '').replace(',', '')
                    return int(seeders)
                except:
                    return 0
            elif column == 'source':
                return result.get('source', '').lower()
            return ''

        # Sort the results
        sorted_results = sorted(self.search_results, key=get_sort_key, reverse=self.sort_reverse)

        # Update column headers to show sort direction
        arrow = ' ▲' if self.sort_reverse else ' ▼'
        self.search_tree.heading('Name', text='Name' + (arrow if column == 'name' else ' ▼'))
        self.search_tree.heading('Size', text='Size' + (arrow if column == 'size' else ' ▼'))
        self.search_tree.heading('Seeders', text='Seeders' + (arrow if column == 'seeders' else ' ▼'))
        self.search_tree.heading('Source', text='Source' + (arrow if column == 'source' else ' ▼'))

        # Display sorted results
        self.display_search_results(sorted_results)

    def download_from_search(self, event=None):
        """Download from search results"""
        selection = self.search_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a torrent")
            return

        item = selection[0]
        values = self.search_tree.item(item, 'values')
        name = values[0]

        for result in self.search_results:
            if result['name'] == name:
                self.notebook.select(2)  # Switch to downloads tab
                magnet = result['magnet']
                if magnet.startswith('http'):
                    self.add_torrent_from_url(magnet, result['name'])
                else:
                    self.add_magnet_direct(magnet)
                break

    def add_torrent_from_url(self, url, name):
        """Download torrent from URL"""
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
        """Add torrent file with validation"""
        # Validate file path
        if not filepath or not isinstance(filepath, str):
            messagebox.showerror("Invalid Input", "File path cannot be empty")
            return

        filepath = filepath.strip()

        # Check if file exists
        if not os.path.exists(filepath):
            messagebox.showerror("File Not Found",
                f"Torrent file not found:\n{filepath}")
            return

        # Check if it's a file (not a directory)
        if not os.path.isfile(filepath):
            messagebox.showerror("Invalid File",
                f"Path is not a file:\n{filepath}")
            return

        # Check file size (torrent files should be < 10MB)
        try:
            file_size = os.path.getsize(filepath)
            if file_size > 10 * 1024 * 1024:  # 10 MB
                messagebox.showerror("File Too Large",
                    f"Torrent file too large ({file_size} bytes).\nMaximum: 10 MB")
                return
            if file_size == 0:
                messagebox.showerror("Empty File",
                    "Torrent file is empty")
                return
        except OSError as e:
            messagebox.showerror("File Error",
                f"Cannot read file:\n{str(e)}")
            return

        try:
            os.makedirs(self.download_path, exist_ok=True)

            # Try to parse torrent file
            try:
                info = lt.torrent_info(filepath)
            except RuntimeError as e:
                messagebox.showerror("Invalid Torrent File",
                    f"Failed to parse torrent file:\n{str(e)}\n\nMake sure this is a valid .torrent file.")
                return

            # Validate torrent info
            if not info.name():
                messagebox.showerror("Invalid Torrent",
                    "Torrent file is missing required name field")
                return

            params = {
                'ti': info,
                'save_path': self.download_path,
                'storage_mode': lt.storage_mode_t.storage_mode_sparse,
            }

            # Check for resume data
            info_hash = str(info.info_hash())
            resume_file = os.path.join(self.resume_dir, f"{info_hash}.fastresume")
            if os.path.exists(resume_file):
                try:
                    with open(resume_file, 'rb') as f:
                        params['resume_data'] = f.read()
                    self.status_var.set("Loading resume data...")
                except Exception as e:
                    print(f"Failed to load resume data: {e}")

            handle = self.ses.add_torrent(params)

            # Force recheck to detect existing files
            handle.force_recheck()

            item_id = self.tree.insert('', 'end', values=(
                info.name(),
                format_size(info.total_size()),
                '0%',
                '0 KB/s',
                '0',
                'Checking...'
            ))

            with self.torrents_lock:
                self.torrents.append({
                    'handle': handle,
                    'info': info,
                    'item_id': item_id,
                    'completed': False
                })

            self.status_var.set(f"Added: {info.name()}")

        except OSError as e:
            messagebox.showerror("File System Error",
                f"Failed to create download directory:\n{str(e)}")
        except RuntimeError as e:
            messagebox.showerror("Torrent Error",
                f"Failed to add torrent:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Unexpected Error",
                f"An unexpected error occurred:\n{str(e)}")

    def add_magnet(self):
        """Add magnet from entry"""
        magnet = self.magnet_entry.get().strip()
        if magnet:
            self.add_magnet_direct(magnet)
            self.magnet_entry.delete(0, tk.END)

    def add_magnet_direct(self, magnet):
        """Add magnet link with validation"""
        # Validate magnet link format
        if not magnet or not isinstance(magnet, str):
            messagebox.showerror("Invalid Input", "Magnet link cannot be empty")
            return

        magnet = magnet.strip()

        if not magnet.startswith('magnet:?'):
            messagebox.showerror("Invalid Input",
                "Invalid magnet link format. Must start with 'magnet:?'")
            return

        # Check for info_hash (required component)
        if 'xt=urn:btih:' not in magnet:
            messagebox.showerror("Invalid Input",
                "Invalid magnet link. Missing info hash (xt=urn:btih:)")
            return

        # Check length (magnet links should be reasonably sized)
        if len(magnet) > 10000:
            messagebox.showerror("Invalid Input",
                "Magnet link too long. Maximum 10,000 characters.")
            return

        try:
            os.makedirs(self.download_path, exist_ok=True)

            # Parse magnet URI and validate it
            try:
                params = lt.parse_magnet_uri(magnet)
            except RuntimeError as e:
                messagebox.showerror("Invalid Magnet Link",
                    f"Failed to parse magnet link:\n{str(e)}")
                return

            # Verify we got an info_hash
            if not hasattr(params, 'info_hash') or not params.info_hash:
                messagebox.showerror("Invalid Magnet Link",
                    "Magnet link is missing required info hash")
                return

            params.save_path = self.download_path
            params.storage_mode = lt.storage_mode_t.storage_mode_sparse

            # Check for saved metadata and resume data
            info_hash = str(params.info_hash)
            resume_file = os.path.join(self.resume_dir, f"{info_hash}.fastresume")
            torrent_file = os.path.join(self.resume_dir, f"{info_hash}.torrent")

            has_resume = os.path.exists(resume_file)
            has_metadata = os.path.exists(torrent_file)

            if has_resume and has_metadata:
                # Best case: have both metadata and resume data
                try:
                    # Load the full torrent info
                    ti = lt.torrent_info(torrent_file)
                    params.ti = ti

                    # Load resume data
                    with open(resume_file, 'rb') as f:
                        resume_data = f.read()
                        # Note: resume_data parameter works differently for add_torrent_params

                    self.status_var.set("⚡ Resuming download...")
                    self.metadata_saved.add(info_hash)
                except Exception as e:
                    print(f"Failed to load saved data: {e}")

            elif has_metadata:
                # Have metadata but no resume - still better than nothing
                try:
                    ti = lt.torrent_info(torrent_file)
                    params.ti = ti
                    self.status_var.set("📦 Loading saved torrent...")
                    self.metadata_saved.add(info_hash)
                except Exception as e:
                    print(f"Failed to load metadata: {e}")

            handle = self.ses.add_torrent(params)

            # Force recheck to detect existing files
            if has_metadata:
                handle.force_recheck()

            # Set initial status based on what we have
            if has_resume and has_metadata:
                initial_status = 'Checking...'
            elif has_metadata:
                initial_status = 'Checking...'
            else:
                initial_status = 'Getting metadata...'

            item_id = self.tree.insert('', 'end', values=(
                'Fetching metadata...' if not has_metadata else 'Checking files...',
                '?',
                '0%',
                '0 KB/s',
                '0',
                initial_status
            ))

            with self.torrents_lock:
                self.torrents.append({
                    'handle': handle,
                    'info': None,
                    'item_id': item_id,
                    'completed': False
                })

            self.status_var.set("Added magnet link")

        except OSError as e:
            messagebox.showerror("File System Error",
                f"Failed to create download directory:\n{str(e)}")
        except RuntimeError as e:
            messagebox.showerror("Torrent Error",
                f"Failed to add torrent:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Unexpected Error",
                f"An unexpected error occurred:\n{str(e)}")

    def handle_external_magnet(self, magnet_link):
        """Handle magnet link from external source (browser, command line)"""
        try:
            # Switch to Downloads tab
            self.notebook.select(self.downloads_tab)

            # Add the magnet link
            self.add_magnet_direct(magnet_link)

            # Show notification
            messagebox.showinfo(
                "Magnet Link Added",
                "The torrent has been added to your downloads!"
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to handle magnet link: {e}")

    def browse_download_path(self):
        """Browse for download path"""
        directory = filedialog.askdirectory(title="Select Download Directory")
        if directory:
            self.download_path = directory
            self.path_label.config(text=directory)
            self.save_settings()

    def apply_limits(self):
        """Apply bandwidth limits with input validation"""
        try:
            # Validate download limit
            download_str = self.download_limit_var.get().strip()
            if not download_str:
                download_limit = 0
            else:
                try:
                    download_limit = int(download_str)
                    if download_limit < 0:
                        messagebox.showerror("Invalid Input",
                            "Download limit must be 0 or positive")
                        return
                    if download_limit > 1000000:  # 1 GB/s max
                        messagebox.showerror("Invalid Input",
                            "Download limit too large (max: 1,000,000 KB/s)")
                        return
                except ValueError:
                    messagebox.showerror("Invalid Input",
                        f"Download limit must be a number, got: '{download_str}'")
                    return

            # Validate upload limit
            upload_str = self.upload_limit_var.get().strip()
            if not upload_str:
                upload_limit = 0
            else:
                try:
                    upload_limit = int(upload_str)
                    if upload_limit < 0:
                        messagebox.showerror("Invalid Input",
                            "Upload limit must be 0 or positive")
                        return
                    if upload_limit > 1000000:  # 1 GB/s max
                        messagebox.showerror("Invalid Input",
                            "Upload limit too large (max: 1,000,000 KB/s)")
                        return
                except ValueError:
                    messagebox.showerror("Invalid Input",
                        f"Upload limit must be a number, got: '{upload_str}'")
                    return

            # Convert to bytes/sec
            download_limit *= 1000
            upload_limit *= 1000

            self.max_download_rate = download_limit
            self.max_upload_rate = upload_limit

            settings = self.ses.get_settings()
            settings['download_rate_limit'] = download_limit
            settings['upload_rate_limit'] = upload_limit
            self.ses.apply_settings(settings)

            self.save_settings()

            # Show success message with actual values
            dl_text = f"{download_limit // 1000} KB/s" if download_limit > 0 else "unlimited"
            ul_text = f"{upload_limit // 1000} KB/s" if upload_limit > 0 else "unlimited"
            messagebox.showinfo("Success",
                f"Bandwidth limits applied!\nDownload: {dl_text}\nUpload: {ul_text}")

        except AttributeError as e:
            messagebox.showerror("Error", "Session not initialized")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {e}")

    def remove_selected(self):
        """Remove selected torrent"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a torrent")
            return

        # Ask if user wants to delete files too
        response = messagebox.askyesnocancel(
            "Remove Torrent",
            "Remove torrent from list?\n\n"
            "• Yes = Remove and delete resume data (torrent can be re-added)\n"
            "• No = Remove and delete downloaded files too\n"
            "• Cancel = Keep torrent"
        )

        if response is None:  # Cancel
            return

        delete_files = (response == False)  # No = delete files

        with self.torrents_lock:
            for item_id in selection:
                for i, torrent in enumerate(self.torrents):
                    if torrent['item_id'] == item_id:
                        # Get info hash and info before removing
                        handle = torrent['handle']
                        info_hash = str(handle.status().info_hash)

                        # If deleting files, get file paths first
                        if delete_files:
                            try:
                                status = handle.status()
                                save_path = status.save_path
                                if torrent['info']:
                                    torrent_name = torrent['info'].name()
                                else:
                                    torrent_name = status.name

                                # Full path to downloaded files
                                full_path = os.path.join(save_path, torrent_name)
                            except:
                                full_path = None

                        # Remove from session
                        self.ses.remove_torrent(handle)
                        self.torrents.pop(i)

                        # Delete resume files so it doesn't reload on restart
                        self.delete_resume_files(info_hash)

                        # Delete downloaded files if requested
                        if delete_files and full_path and os.path.exists(full_path):
                            try:
                                import shutil
                                if os.path.isdir(full_path):
                                    shutil.rmtree(full_path)
                                else:
                                    os.remove(full_path)
                                print(f"Deleted downloaded files: {full_path}")
                            except Exception as e:
                                print(f"Warning: Could not delete files: {e}")

                        break
                self.tree.delete(item_id)

    def clear_completed(self):
        """Clear completed torrents"""
        to_remove = []

        with self.torrents_lock:
            for torrent in self.torrents:
                if torrent['completed']:
                    to_remove.append(torrent)

            for torrent in to_remove:
                # Get info hash before removing
                info_hash = str(torrent['handle'].status().info_hash)

                # Remove from session and UI
                self.tree.delete(torrent['item_id'])
                self.torrents.remove(torrent)

                # Delete resume files so it doesn't reload on restart
                self.delete_resume_files(info_hash)

        self.status_var.set(f"Cleared {len(to_remove)} completed torrent(s)")

    def delete_resume_files(self, info_hash):
        """Delete all resume files for a torrent"""
        try:
            # List of file extensions to delete
            extensions = ['.fastresume', '.torrent', '.magnet']

            for ext in extensions:
                filename = os.path.join(self.resume_dir, f"{info_hash}{ext}")
                if os.path.exists(filename):
                    os.remove(filename)
                    print(f"Deleted resume file: {info_hash}{ext}")

            # Remove from metadata_saved set
            if info_hash in self.metadata_saved:
                self.metadata_saved.remove(info_hash)

        except Exception as e:
            print(f"Warning: Could not delete resume files for {info_hash}: {e}")

    def save_metadata_if_ready(self, torrent):
        """Save torrent metadata to file if it has arrived (for magnet links)"""
        handle = torrent['handle']
        info_hash = str(handle.status().info_hash)

        # Skip if already saved
        if info_hash in self.metadata_saved:
            return

        # Check if we have metadata
        if handle.status().has_metadata and handle.torrent_file():
            try:
                torrent_file = os.path.join(self.resume_dir, f"{info_hash}.torrent")

                # Save the .torrent file
                ti = handle.torrent_file()
                try:
                    # Create torrent from torrent_info and generate bencode
                    ct = lt.create_torrent(ti)
                    torrent_data = lt.bencode(ct.generate())
                    with open(torrent_file, 'wb') as f:
                        f.write(torrent_data)
                    print(f"✅ Saved metadata for {handle.status().name}")
                    self.metadata_saved.add(info_hash)
                except Exception as create_error:
                    # If create_torrent fails, try saving magnet as fallback
                    print(f"⚠️ Could not save .torrent file, saving magnet instead: {create_error}")
                    magnet = lt.make_magnet_uri(ti)
                    magnet_file = os.path.join(self.resume_dir, f"{info_hash}.magnet")
                    with open(magnet_file, 'w') as f:
                        f.write(magnet)
                    self.metadata_saved.add(info_hash)

            except Exception as e:
                print(f"⚠️ Failed to save metadata: {e}")

    def update_loop(self):
        """Update torrents"""
        while self.running:
            try:
                # Create a copy of torrents list to avoid race conditions
                with self.torrents_lock:
                    torrents_copy = self.torrents.copy()

                for torrent in torrents_copy:
                    handle = torrent['handle']
                    s = handle.status()

                    # Save metadata if it arrived (for magnet links)
                    self.save_metadata_if_ready(torrent)

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
                    else:
                        status = "Queued"

                    self.tree.item(torrent['item_id'], values=(
                        name, size, progress, speed, peers, status
                    ))

                # Update total session bandwidth
                try:
                    status = self.ses.status()
                    total_download = status.download_rate / 1000  # Convert to KB/s
                    total_upload = status.upload_rate / 1000      # Convert to KB/s

                    # Show limits if they exist
                    dl_limit_text = ""
                    ul_limit_text = ""
                    if self.max_download_rate > 0:
                        dl_limit = self.max_download_rate / 1000
                        dl_limit_text = f" / {dl_limit:.0f}"
                    if self.max_upload_rate > 0:
                        ul_limit = self.max_upload_rate / 1000
                        ul_limit_text = f" / {ul_limit:.0f}"

                    bandwidth_text = f"Bandwidth: ↓ {total_download:.0f}{dl_limit_text} KB/s  ↑ {total_upload:.0f}{ul_limit_text} KB/s"
                    self.bandwidth_var.set(bandwidth_text)
                except Exception as bw_error:
                    pass  # Silently ignore bandwidth update errors

            except Exception as e:
                print(f"Update error: {e}")

            time.sleep(1)

    def start_ipc_server(self):
        """Start IPC server to handle single instance communication"""
        try:
            # Remove stale socket file if exists
            if os.path.exists(self.socket_path):
                os.remove(self.socket_path)

            # Create Unix domain socket
            self.ipc_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.ipc_socket.bind(self.socket_path)
            self.ipc_socket.listen(5)
            self.ipc_socket.setblocking(False)

            # Start listener thread
            ipc_thread = threading.Thread(target=self.ipc_listener, daemon=True)
            ipc_thread.start()
        except Exception as e:
            print(f"Failed to start IPC server: {e}")
            self.ipc_socket = None

    def ipc_listener(self):
        """Listen for incoming magnet links from other instances"""
        while self.running or not hasattr(self, 'running'):
            try:
                # Check if there's an incoming connection (non-blocking)
                import select
                ready, _, _ = select.select([self.ipc_socket], [], [], 0.5)

                if ready:
                    conn, _ = self.ipc_socket.accept()
                    try:
                        data = conn.recv(4096).decode('utf-8')
                        if data:
                            # Schedule magnet link to be added on main thread
                            self.root.after(0, lambda: self.handle_external_magnet(data))
                            conn.send(b"OK")
                    finally:
                        conn.close()
            except Exception as e:
                if self.running:
                    time.sleep(0.5)

    def on_closing(self):
        """Handle closing"""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            # Save settings and session state
            self.save_settings()
            self.save_session_state()

            # Stop the app
            self.running = False

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

            self.root.destroy()


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


if __name__ == "__main__":
    main()
