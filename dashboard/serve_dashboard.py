#!/usr/bin/env python3
"""
Simple HTTP Server for SIP Dashboard
Serves the dashboard on http://localhost:8000
"""

import http.server
import socketserver
import os
from pathlib import Path

PORT = 8000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Enable CORS
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

# Serve from parent directory so paths work correctly
os.chdir(Path(__file__).parent.parent)

Handler = MyHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"\n{'='*60}")
    print(f"  🚀 SIP Dashboard Server Started!")
    print(f"{'='*60}")
    print(f"\n  📊 Dashboard URL: http://localhost:{PORT}/dashboard/dashboard.html")
    print(f"\n  Press Ctrl+C to stop the server")
    print(f"\n{'='*60}\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n✅ Server stopped.")
