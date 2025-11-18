#!/usr/bin/env python3
import os
import subprocess
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json

class LoginHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        message = """
        <html>
        <head><title>Login Server</title></head>
        <body>
            <h1>Login Server is Running</h1>
            <p>Available endpoints:</p>
            <ul>
                <li>POST /login-success - Called on successful login</li>
                <li>POST /login-timeout - Called on 15-second timeout</li>
            </ul>
        </body>
        </html>
        """
        self.wfile.write(message.encode())
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS, GET')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/login-success':
            self.handle_login_success()
        elif parsed_path.path == '/login-timeout':
            self.handle_login_timeout()
        else:
            self.send_response(404)
            self.end_headers()
    
    def handle_login_success(self):
        """Handle successful login: run success script then mover.sh"""
        try:
            # Get the directory where this script is located
            script_dir = os.path.dirname(os.path.abspath(__file__))
            mover_script = os.path.join(script_dir, 'mover.sh')
            success_script = os.path.join(script_dir, 'success.py')
            
            # Run success.py first (before mover.sh moves the files)
            subprocess.run([sys.executable, success_script], cwd=script_dir, check=True)
            
            # Run mover.sh (creates new directory, moves files, and prints URL)
            subprocess.run(['bash', mover_script], cwd=script_dir, check=True)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'success'}).encode())
        except Exception as e:
            print(f"Error in login-success: {e}", file=sys.stderr)
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
    
    def handle_login_timeout(self):
        """Handle login timeout: run moved script then mover.sh"""
        try:
            # Get the directory where this script is located
            script_dir = os.path.dirname(os.path.abspath(__file__))
            mover_script = os.path.join(script_dir, 'mover.sh')
            moved_script = os.path.join(script_dir, 'moved.py')
            
            # Run moved.py first (before mover.sh moves the files)
            subprocess.run([sys.executable, moved_script], cwd=script_dir, check=True)
            
            # Run mover.sh (creates new directory, moves files, and prints URL)
            subprocess.run(['bash', mover_script], cwd=script_dir, check=True)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'timeout'}).encode())
        except Exception as e:
            print(f"Error in login-timeout: {e}", file=sys.stderr)
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
    
    def log_message(self, format, *args):
        """Override to prevent default logging"""
        pass

if __name__ == '__main__':
    port = 8001
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dir_name = os.path.basename(script_dir)
    
    # Calculate path relative to Validator directory
    # Find 'Validator' in the path and get everything after it
    script_path = script_dir
    parts = script_path.split(os.sep)
    try:
        validator_idx = parts.index('Validator')
        # Get path from Validator onwards (everything after Validator)
        rel_parts = parts[validator_idx + 1:]
        website_path = '/'.join(rel_parts)
    except (ValueError, IndexError):
        # If Validator not found, use the directory name
        website_path = dir_name
    
    server = HTTPServer(('localhost', port), LoginHandler)
    print(f"Server running on http://localhost:{port}/{dir_name}")
    print(f"Website running at: http://localhost:8000/{website_path}/index.html")
    print(f"Directory: {script_dir}")
    print("Endpoints:")
    print("  POST /login-success - Called on successful login")
    print("  POST /login-timeout - Called on 15-second timeout")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
        server.server_close()

