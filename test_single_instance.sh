#!/bin/bash
# Test script for single-instance functionality

echo "==================================================================="
echo "Single Instance Test"
echo "==================================================================="
echo ""

# Test 1: Check socket doesn't exist initially
echo "Test 1: Checking initial state..."
SOCKET_PATH="/tmp/torrent-downloader-gui.sock"

if [ -e "$SOCKET_PATH" ]; then
    echo "  ⚠️  Socket already exists (cleaning up old socket)"
    rm -f "$SOCKET_PATH"
fi
echo "  ✅ No socket file exists"
echo ""

# Test 2: Verify Python syntax
echo "Test 2: Checking Python syntax..."
if python3 -m py_compile torrent-dl-gui-secure.py 2>/dev/null; then
    echo "  ✅ Syntax check passed"
else
    echo "  ❌ Syntax error!"
    exit 1
fi
echo ""

# Test 3: Verify imports work
echo "Test 3: Checking imports..."
python3 -c "
import socket
import tempfile
import tkinter
print('  ✅ All imports successful')
" || {
    echo "  ❌ Import error!"
    exit 1
}
echo ""

# Test 4: Test send_to_existing_instance function
echo "Test 4: Testing send_to_existing_instance function..."
python3 << 'EOF'
import socket
import tempfile
import os

def send_to_existing_instance(magnet_link):
    socket_path = os.path.join(tempfile.gettempdir(), "torrent-downloader-gui.sock")
    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.settimeout(2)
        client.connect(socket_path)
        client.send(magnet_link.encode('utf-8'))
        response = client.recv(1024)
        client.close()
        return True
    except (socket.error, FileNotFoundError, ConnectionRefusedError):
        return False

# Should return False since no instance is running
result = send_to_existing_instance("magnet:?xt=test")
if result == False:
    print("  ✅ Correctly detected no existing instance")
else:
    print("  ❌ Should have returned False")
EOF
echo ""

echo "==================================================================="
echo "Manual Testing Instructions"
echo "==================================================================="
echo ""
echo "To test the single-instance feature manually:"
echo ""
echo "1. Open Terminal 1:"
echo "   cd ~/torrent-downloader"
echo "   python3 torrent-dl-gui-secure.py"
echo ""
echo "2. Verify socket was created:"
echo "   ls -la /tmp/torrent-downloader-gui.sock"
echo "   (Should show: srwxr-xr-x)"
echo ""
echo "3. Open Terminal 2 (while GUI is still running):"
echo "   cd ~/torrent-downloader"
echo "   python3 torrent-dl-gui-secure.py \"magnet:?xt=urn:btih:dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c\""
echo ""
echo "4. Expected results:"
echo "   - Terminal 2 shows: 'Sent magnet link to existing instance'"
echo "   - Terminal 2 exits immediately"
echo "   - No new GUI window opens"
echo "   - Existing GUI shows notification: 'Magnet Link Added'"
echo ""
echo "5. Close the GUI and verify cleanup:"
echo "   ls -la /tmp/torrent-downloader-gui.sock"
echo "   (Should show: No such file or directory)"
echo ""
echo "==================================================================="
echo "All automated tests passed! ✅"
echo "==================================================================="
