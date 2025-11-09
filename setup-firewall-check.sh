#!/bin/bash
# Setup passwordless sudo for firewall checking

echo "Setting up passwordless firewall check for torrent downloader..."
echo ""
echo "This will allow the torrent app to check firewall status without sudo password."
echo ""

# Create sudoers rule
echo "$USER ALL=(ALL) NOPASSWD: /usr/sbin/ufw status" | sudo tee /etc/sudoers.d/torrent-firewall-check > /dev/null

# Set correct permissions
sudo chmod 0440 /etc/sudoers.d/torrent-firewall-check

# Verify it was created
if [ -f /etc/sudoers.d/torrent-firewall-check ]; then
    echo "✅ Setup complete! The torrent app can now check firewall status."
    echo ""
    echo "You can now launch the app with:"
    echo "  cd ~/torrent-downloader && ./launch-torrent-gui.sh"
else
    echo "❌ Setup failed. Please check for errors above."
    exit 1
fi
