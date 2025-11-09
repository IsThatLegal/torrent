#!/usr/bin/env python3
"""
Tests for single-instance functionality
"""

import unittest
import sys
import os
import socket
import tempfile
import time
import threading

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestSingleInstance(unittest.TestCase):
    """Test single-instance IPC functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.socket_path = os.path.join(tempfile.gettempdir(), "test-torrent-downloader.sock")
        self.cleanup_socket()

    def tearDown(self):
        """Clean up after tests"""
        self.cleanup_socket()

    def cleanup_socket(self):
        """Remove test socket file"""
        if os.path.exists(self.socket_path):
            try:
                os.remove(self.socket_path)
            except:
                pass

    def test_socket_creation(self):
        """Test that socket can be created"""
        # Create socket
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.bind(self.socket_path)
        sock.listen(1)

        # Verify socket file exists
        self.assertTrue(os.path.exists(self.socket_path))

        # Verify it's a socket
        self.assertTrue(os.path.isfile(self.socket_path) or
                       os.stat(self.socket_path).st_mode & 0o140000)

        sock.close()

    def test_socket_cleanup(self):
        """Test that socket is removed on cleanup"""
        # Create socket
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.bind(self.socket_path)
        self.assertTrue(os.path.exists(self.socket_path))

        # Close and cleanup
        sock.close()
        os.remove(self.socket_path)

        # Verify removed
        self.assertFalse(os.path.exists(self.socket_path))

    def test_client_server_communication(self):
        """Test basic IPC communication"""
        received_data = []

        def server():
            """Simple server that receives one message"""
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.bind(self.socket_path)
            sock.listen(1)

            conn, _ = sock.accept()
            data = conn.recv(4096).decode('utf-8')
            received_data.append(data)
            conn.send(b"OK")
            conn.close()
            sock.close()

        # Start server in thread
        server_thread = threading.Thread(target=server, daemon=True)
        server_thread.start()

        # Wait for server to be ready
        time.sleep(0.1)

        # Connect as client
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(self.socket_path)

        # Send test data
        test_message = "magnet:?xt=urn:btih:test123"
        client.send(test_message.encode('utf-8'))

        # Receive response
        response = client.recv(1024)
        self.assertEqual(response, b"OK")

        client.close()
        server_thread.join(timeout=1)

        # Verify server received the message
        self.assertEqual(len(received_data), 1)
        self.assertEqual(received_data[0], test_message)

    def test_connection_refused_no_server(self):
        """Test client behavior when no server is running"""
        # Try to connect when no server exists
        with self.assertRaises((socket.error, FileNotFoundError, ConnectionRefusedError)):
            client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client.settimeout(1)
            client.connect(self.socket_path)

    def test_multiple_clients(self):
        """Test multiple clients connecting to same server"""
        received_data = []

        def server():
            """Server that accepts multiple connections"""
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.bind(self.socket_path)
            sock.listen(5)

            for _ in range(3):
                conn, _ = sock.accept()
                data = conn.recv(4096).decode('utf-8')
                received_data.append(data)
                conn.send(b"OK")
                conn.close()

            sock.close()

        # Start server
        server_thread = threading.Thread(target=server, daemon=True)
        server_thread.start()
        time.sleep(0.1)

        # Connect multiple clients
        for i in range(3):
            client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client.connect(self.socket_path)
            client.send(f"message_{i}".encode('utf-8'))
            response = client.recv(1024)
            self.assertEqual(response, b"OK")
            client.close()

        server_thread.join(timeout=2)

        # Verify all messages received
        self.assertEqual(len(received_data), 3)
        self.assertIn("message_0", received_data)
        self.assertIn("message_1", received_data)
        self.assertIn("message_2", received_data)


class TestInstanceDetection(unittest.TestCase):
    """Test instance detection logic"""

    def setUp(self):
        """Set up test fixtures"""
        self.socket_path = os.path.join(tempfile.gettempdir(), "test-torrent-instance.sock")
        self.cleanup_socket()

    def tearDown(self):
        """Clean up after tests"""
        self.cleanup_socket()

    def cleanup_socket(self):
        """Remove test socket file"""
        if os.path.exists(self.socket_path):
            try:
                os.remove(self.socket_path)
            except:
                pass

    def send_to_instance(self, message):
        """Try to send message to existing instance"""
        try:
            client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client.settimeout(2)
            client.connect(self.socket_path)
            client.send(message.encode('utf-8'))
            response = client.recv(1024)
            client.close()
            return True
        except (socket.error, FileNotFoundError, ConnectionRefusedError):
            return False

    def test_no_instance_running(self):
        """Test detection when no instance exists"""
        result = self.send_to_instance("test")
        self.assertFalse(result)

    def test_instance_running(self):
        """Test detection when instance exists"""
        # Create mock server
        def server():
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.bind(self.socket_path)
            sock.listen(1)
            conn, _ = sock.accept()
            conn.recv(4096)
            conn.send(b"OK")
            conn.close()
            sock.close()

        server_thread = threading.Thread(target=server, daemon=True)
        server_thread.start()
        time.sleep(0.1)

        result = self.send_to_instance("test")
        self.assertTrue(result)

        server_thread.join(timeout=2)

    def test_stale_socket_detection(self):
        """Test handling of stale socket files"""
        # Create a stale socket file (not bound to any process)
        # This simulates a crashed application leaving socket file behind
        with open(self.socket_path, 'w') as f:
            f.write("")

        # Should detect no running instance
        result = self.send_to_instance("test")
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
