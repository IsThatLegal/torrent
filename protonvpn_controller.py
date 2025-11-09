#!/usr/bin/env python3
"""
ProtonVPN Controller Module
Controls ProtonVPN (official app) from within Python applications
Works with the official ProtonVPN Linux app using NetworkManager
"""

import subprocess
import re
import time


class ProtonVPNController:
    """Control ProtonVPN (official app) from Python via NetworkManager"""

    def __init__(self):
        self.is_installed = self.check_installed()
        self.connection_name = None
        if self.is_installed:
            self._find_connection()

    def check_installed(self):
        """Check if ProtonVPN GUI app is installed"""
        try:
            # Check for official ProtonVPN app
            result = subprocess.run(['which', 'protonvpn-app'],
                                  capture_output=True, timeout=5)
            if result.returncode == 0:
                return True

            # Check if nmcli is available (NetworkManager)
            result = subprocess.run(['which', 'nmcli'],
                                  capture_output=True, timeout=5)
            return result.returncode == 0

        except Exception:
            return False

    def _find_connection(self):
        """Find the ProtonVPN connection name in NetworkManager"""
        try:
            result = subprocess.run(['nmcli', 'connection', 'show'],
                                  capture_output=True, text=True, timeout=5)

            # Look for ProtonVPN connection
            for line in result.stdout.split('\n'):
                if 'ProtonVPN' in line or 'protonvpn' in line.lower():
                    # Extract connection name (first column)
                    parts = line.split()
                    if parts:
                        # Connection name might have spaces, so we need to be careful
                        # Format: NAME  UUID  TYPE  DEVICE
                        # We'll take everything before the UUID
                        match = re.match(r'(.+?)\s+([a-f0-9-]{36})', line)
                        if match:
                            self.connection_name = match.group(1).strip()
                            return True

            return False
        except Exception:
            return False

    def get_status(self):
        """Get current VPN status"""
        if not self.is_installed:
            return {
                'connected': False,
                'status': 'not_installed',
                'server': None,
                'ip': None,
                'protocol': None,
                'message': 'ProtonVPN not installed. Install from protonvpn.com'
            }

        try:
            # Check if any ProtonVPN connection is active
            result = subprocess.run(['nmcli', 'connection', 'show', '--active'],
                                  capture_output=True, text=True, timeout=5)

            output = result.stdout
            connected = 'ProtonVPN' in output or 'protonvpn' in output.lower()

            status_info = {
                'connected': connected,
                'status': 'connected' if connected else 'disconnected',
                'server': None,
                'ip': None,
                'protocol': 'WireGuard',  # Official app uses WireGuard
                'country': None,
                'load': None
            }

            if connected:
                # Extract server/connection info
                for line in output.split('\n'):
                    if 'ProtonVPN' in line:
                        parts = line.split()
                        if parts:
                            connection_name = parts[0]
                            status_info['server'] = connection_name

                            # Try to extract country from name (e.g., "ProtonVPN US-FREE#26")
                            country_match = re.search(r'ProtonVPN\s+([A-Z]{2})', connection_name)
                            if country_match:
                                status_info['country'] = country_match.group(1)

                # Get IP address
                try:
                    ip_result = subprocess.run(['curl', '-s', 'ifconfig.me'],
                                             capture_output=True, text=True, timeout=5)
                    if ip_result.returncode == 0:
                        status_info['ip'] = ip_result.stdout.strip()
                except:
                    pass

                status_info['message'] = f"Connected to {status_info.get('server', 'ProtonVPN')}"
            else:
                status_info['message'] = 'Not connected'

            return status_info

        except Exception as e:
            return {
                'connected': False,
                'status': 'error',
                'message': f'Error checking status: {str(e)}'
            }

    def connect(self, server_type='free', country=None):
        """
        Connect to ProtonVPN

        Note: With the official app, you need to use the GUI to select servers.
        This method will connect to the last configured server.

        server_type: ignored (use GUI to select server)
        country: ignored (use GUI to select server)
        """
        if not self.is_installed:
            return False, "ProtonVPN not installed. Install from protonvpn.com"

        # Find connection if not already found
        if not self.connection_name:
            self._find_connection()

        if not self.connection_name:
            return False, "No ProtonVPN connection found. Please connect via GUI first."

        try:
            # Check if already connected
            status = self.get_status()
            if status['connected']:
                return False, "Already connected. Disconnect first."

            # Connect using NetworkManager
            result = subprocess.run(['nmcli', 'connection', 'up', self.connection_name],
                                  capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                # Wait a moment for connection to establish
                time.sleep(2)
                return True, "Connected successfully"
            else:
                error_msg = result.stderr or result.stdout
                return False, f"Connection failed: {error_msg[:100]}"

        except subprocess.TimeoutExpired:
            return False, "Connection timeout. Check your internet connection."
        except Exception as e:
            return False, f"Error connecting: {str(e)}"

    def disconnect(self):
        """Disconnect from ProtonVPN"""
        if not self.is_installed:
            return False, "ProtonVPN not installed"

        # Find connection if not already found
        if not self.connection_name:
            self._find_connection()

        try:
            # Check if connected
            status = self.get_status()
            if not status['connected']:
                return True, "Already disconnected"

            # Disconnect using NetworkManager
            if self.connection_name:
                result = subprocess.run(['nmcli', 'connection', 'down', self.connection_name],
                                      capture_output=True, text=True, timeout=15)
            else:
                # If we don't have the connection name, try to disconnect any ProtonVPN connection
                result = subprocess.run(['nmcli', 'connection', 'show', '--active'],
                                      capture_output=True, text=True, timeout=5)
                for line in result.stdout.split('\n'):
                    if 'ProtonVPN' in line:
                        parts = line.split()
                        if parts:
                            match = re.match(r'(.+?)\s+([a-f0-9-]{36})', line)
                            if match:
                                conn_name = match.group(1).strip()
                                result = subprocess.run(['nmcli', 'connection', 'down', conn_name],
                                                      capture_output=True, text=True, timeout=15)
                                break

            if result.returncode == 0 or "successfully deactivated" in result.stdout:
                return True, "Disconnected successfully"
            else:
                return False, f"Disconnect failed: {result.stderr}"

        except Exception as e:
            return False, f"Error disconnecting: {str(e)}"

    def reconnect(self):
        """Reconnect to ProtonVPN (disconnect and connect)"""
        if not self.is_installed:
            return False, "ProtonVPN not installed"

        try:
            # Disconnect first
            self.disconnect()
            time.sleep(2)

            # Then connect
            success, message = self.connect()
            return success, message

        except Exception as e:
            return False, f"Error reconnecting: {str(e)}"

    def get_countries(self):
        """Get list of available countries"""
        # ProtonVPN Free countries
        return ['US', 'NL', 'JP']

    def is_logged_in(self):
        """Check if user is logged in to ProtonVPN"""
        # With the official app, check if connections exist
        if not self.is_installed:
            return False

        try:
            result = subprocess.run(['nmcli', 'connection', 'show'],
                                  capture_output=True, text=True, timeout=5)
            return 'ProtonVPN' in result.stdout
        except Exception:
            return False


def main():
    """Test the controller"""
    controller = ProtonVPNController()

    print("ProtonVPN Controller Test (Official App)")
    print("=" * 50)

    if not controller.is_installed:
        print("❌ ProtonVPN not installed!")
        print("Download from: https://protonvpn.com/download-linux")
        return

    print("✅ ProtonVPN is installed")
    print()

    # Check if connection exists
    if controller.connection_name:
        print(f"✅ Found connection: {controller.connection_name}")
    else:
        print("⚠️  No ProtonVPN connection found")
        print("Please connect via GUI app first to create a connection")

    print()

    # Get status
    status = controller.get_status()
    print("Current Status:")
    print(f"  Connected: {status['connected']}")
    print(f"  Message: {status['message']}")

    if status['connected']:
        print(f"  Server: {status.get('server')}")
        print(f"  IP: {status.get('ip')}")
        print(f"  Country: {status.get('country')}")
        print(f"  Protocol: {status.get('protocol')}")

    print()
    print("=" * 50)
    print()
    print("NOTE: Use the ProtonVPN GUI app to:")
    print("  - Login to your account")
    print("  - Select specific servers")
    print("  - Configure VPN settings")
    print()
    print("This Python controller can:")
    print("  - Check VPN status")
    print("  - Connect/disconnect")
    print("  - Integrate VPN control into apps")
    print()


if __name__ == "__main__":
    main()
