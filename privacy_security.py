#!/usr/bin/env python3
"""
Privacy and Security Module for Torrent Downloader
Helps protect your privacy and ensure safe torrenting
"""

import subprocess
import requests
import socket
import os
import json


class PrivacySecurityChecker:
    """Check privacy and security status"""

    def __init__(self):
        self.checks = {}

    def check_vpn_status(self):
        """Check if VPN is active"""
        try:
            # Check for common VPN interfaces
            result = subprocess.run(['ip', 'link', 'show'],
                                  capture_output=True, text=True, timeout=5)
            output = result.stdout.lower()

            # Common VPN interface names
            vpn_indicators = ['tun', 'tap', 'wg', 'vpn', 'proton', 'nordvpn',
                            'expressvpn', 'mullvad']

            vpn_detected = any(indicator in output for indicator in vpn_indicators)

            self.checks['vpn'] = {
                'status': 'active' if vpn_detected else 'not_detected',
                'secure': vpn_detected,
                'message': 'VPN detected' if vpn_detected else 'No VPN detected'
            }

        except Exception as e:
            self.checks['vpn'] = {
                'status': 'unknown',
                'secure': False,
                'message': f'Could not check VPN: {e}'
            }

        return self.checks['vpn']

    def check_public_ip(self):
        """Check your public IP address"""
        try:
            # Use multiple services for redundancy
            services = [
                'https://api.ipify.org?format=json',
                'https://ifconfig.me/ip',
            ]

            ip = None
            for service in services:
                try:
                    response = requests.get(service, timeout=5)
                    if 'json' in service:
                        ip = response.json().get('ip')
                    else:
                        ip = response.text.strip()

                    if ip:
                        break
                except:
                    continue

            if ip:
                self.checks['public_ip'] = {
                    'ip': ip,
                    'message': f'Your public IP: {ip}'
                }
            else:
                self.checks['public_ip'] = {
                    'ip': 'unknown',
                    'message': 'Could not determine public IP'
                }

        except Exception as e:
            self.checks['public_ip'] = {
                'ip': 'error',
                'message': f'Error checking IP: {e}'
            }

        return self.checks.get('public_ip')

    def check_dns_leak(self):
        """Basic DNS leak check"""
        try:
            nameservers = []

            # First try resolvectl (systemd-resolved) for actual DNS servers
            try:
                result = subprocess.run(['resolvectl', 'status'],
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    # Parse resolvectl output
                    for line in result.stdout.split('\n'):
                        line = line.strip()
                        if line.startswith('DNS Servers:') or line.startswith('Current DNS Server:'):
                            # Extract IP from the line
                            parts = line.split(':')
                            if len(parts) > 1:
                                dns = parts[1].strip()
                                if dns and dns not in nameservers:
                                    nameservers.append(dns)
            except:
                pass

            # Fallback to /etc/resolv.conf if resolvectl didn't work
            if not nameservers:
                resolv_conf = '/etc/resolv.conf'
                if os.path.exists(resolv_conf):
                    with open(resolv_conf, 'r') as f:
                        content = f.read()

                    # Extract nameservers
                    for line in content.split('\n'):
                        if line.strip().startswith('nameserver'):
                            ns = line.split()[1]
                            nameservers.append(ns)

            # Check if using common VPN DNS or public DNS
            vpn_dns = ['10.', '172.16.', '100.64.']  # Common VPN ranges
            public_dns = ['8.8.8.8', '8.8.4.4', '1.1.1.1', '9.9.9.9']

            # Filter out localhost (systemd-resolved stub)
            real_nameservers = [ns for ns in nameservers if not ns.startswith('127.')]

            is_vpn_dns = any(ns.startswith(prefix) for ns in real_nameservers
                           for prefix in vpn_dns)
            is_public_dns = any(ns in public_dns for ns in real_nameservers)

            display_ns = real_nameservers if real_nameservers else nameservers
            self.checks['dns'] = {
                'nameservers': display_ns,
                'secure': is_vpn_dns or is_public_dns,
                'message': f'DNS Servers: {", ".join(display_ns)}'
            }

        except Exception as e:
            self.checks['dns'] = {
                'nameservers': [],
                'secure': False,
                'message': f'DNS check failed: {e}'
            }

        return self.checks.get('dns')

    def check_firewall_status(self):
        """Check if firewall is active"""
        try:
            # Check ufw status
            result = subprocess.run(['sudo', '-n', 'ufw', 'status'],
                                  capture_output=True, text=True, timeout=5)

            if result.returncode == 0:
                output = result.stdout.lower()
                active = 'status: active' in output

                self.checks['firewall'] = {
                    'status': 'active' if active else 'inactive',
                    'secure': active,
                    'message': f'Firewall is {"active" if active else "inactive"}'
                }
            else:
                self.checks['firewall'] = {
                    'status': 'unknown',
                    'secure': False,
                    'message': 'Could not check firewall (requires sudo)'
                }

        except Exception as e:
            self.checks['firewall'] = {
                'status': 'unknown',
                'secure': False,
                'message': 'Firewall check unavailable'
            }

        return self.checks.get('firewall')

    def get_security_recommendations(self):
        """Get security recommendations based on checks"""
        recommendations = []

        # VPN recommendation
        vpn_check = self.checks.get('vpn', {})
        if not vpn_check.get('secure', False):
            recommendations.append({
                'level': 'high',
                'category': 'Privacy',
                'issue': 'No VPN detected',
                'recommendation': 'Consider using a VPN for privacy. Your ISP can see your torrent activity.',
                'action': 'Install a VPN like ProtonVPN, Mullvad, or WireGuard'
            })

        # Firewall recommendation
        firewall_check = self.checks.get('firewall', {})
        if not firewall_check.get('secure', False):
            recommendations.append({
                'level': 'medium',
                'category': 'Security',
                'issue': 'Firewall not active',
                'recommendation': 'Enable a firewall to protect your system.',
                'action': 'Run: sudo ufw enable'
            })

        # DNS recommendation
        dns_check = self.checks.get('dns', {})
        if dns_check.get('nameservers'):
            isp_dns = True
            for ns in dns_check['nameservers']:
                if ns.startswith(('8.8.', '1.1.1', '9.9.9', '10.', '172.16', '100.64')):
                    isp_dns = False
                    break

            if isp_dns:
                recommendations.append({
                    'level': 'medium',
                    'category': 'Privacy',
                    'issue': 'Possible ISP DNS',
                    'recommendation': 'Consider using privacy-focused DNS (Cloudflare 1.1.1.1, Quad9 9.9.9.9)',
                    'action': 'Change DNS in network settings'
                })

        return recommendations

    def run_all_checks(self):
        """Run all privacy and security checks"""
        print("Running Privacy & Security Checks...")
        print("=" * 70)

        # VPN Check
        print("\n🔒 VPN Status:")
        vpn = self.check_vpn_status()
        status_icon = "✅" if vpn.get('secure') else "⚠️"
        print(f"{status_icon} {vpn.get('message')}")

        # Public IP Check
        print("\n🌐 Public IP:")
        ip_info = self.check_public_ip()
        print(f"   {ip_info.get('message')}")

        # DNS Check
        print("\n🔍 DNS Configuration:")
        dns = self.check_dns_leak()
        status_icon = "✅" if dns.get('secure') else "⚠️"
        print(f"{status_icon} {dns.get('message')}")

        # Firewall Check
        print("\n🛡️  Firewall Status:")
        fw = self.check_firewall_status()
        status_icon = "✅" if fw.get('secure') else "⚠️"
        print(f"{status_icon} {fw.get('message')}")

        # Recommendations
        print("\n" + "=" * 70)
        print("📋 Security Recommendations:")
        print("=" * 70)

        recommendations = self.get_security_recommendations()
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                level_icons = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
                icon = level_icons.get(rec['level'], '⚪')

                print(f"\n{i}. {icon} {rec['category']}: {rec['issue']}")
                print(f"   Recommendation: {rec['recommendation']}")
                print(f"   Action: {rec['action']}")
        else:
            print("\n✅ All security checks passed!")

        print("\n" + "=" * 70)

        return {
            'checks': self.checks,
            'recommendations': recommendations
        }


def main():
    """Run privacy and security checks"""
    checker = PrivacySecurityChecker()
    results = checker.run_all_checks()

    print("\n💡 Privacy Tips:")
    print("   1. Always use a VPN when torrenting")
    print("   2. Only download from trusted sources")
    print("   3. Keep your firewall enabled")
    print("   4. Use encrypted connections when possible")
    print("   5. Be careful what you share")
    print()


if __name__ == "__main__":
    main()
