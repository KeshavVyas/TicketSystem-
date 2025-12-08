#!/usr/bin/env python3
import os
import subprocess
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
from pathlib import Path

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
                <li>POST /login-timeout - Called on 10-second timeout</li>
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
            
            # Find mover.sh - check current directory first, then search Validator subdirectories
            mover_script = os.path.join(script_dir, 'mover.sh')
            if not os.path.exists(mover_script):
                # Find Validator directory and search for mover.sh
                current = script_dir
                while current != os.path.dirname(current):  # Stop at root
                    if os.path.basename(current) == 'Validator':
                        # Search all subdirectories for mover.sh
                        for root, dirs, files in os.walk(current):
                            if 'mover.sh' in files:
                                mover_script = os.path.join(root, 'mover.sh')
                                print(f"Found mover.sh at: {mover_script}")
                                break
                        if os.path.exists(mover_script):
                            break
                    current = os.path.dirname(current)
            
            success_script = os.path.join(script_dir, 'success.py')
            
            # Run success.py first (before mover.sh moves the files)
            if os.path.exists(success_script):
                subprocess.run([sys.executable, success_script], cwd=script_dir, check=True)
            else:
                print(f"Warning: success.py not found at {success_script}", file=sys.stderr)
            
            # Run mover.sh (creates new directory, moves files, and prints URL)
            # Run from script_dir (where the files are) not mover_dir (where mover.sh is)
            if os.path.exists(mover_script):
                subprocess.run(['bash', mover_script], cwd=script_dir, check=True)
            else:
                raise FileNotFoundError(f"mover.sh not found. Searched in {script_dir} and Validator subdirectories")
            
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
            
            # Find mover.sh - check current directory first, then search Validator subdirectories
            mover_script = os.path.join(script_dir, 'mover.sh')
            if not os.path.exists(mover_script):
                # Find Validator directory and search for mover.sh
                current = script_dir
                while current != os.path.dirname(current):  # Stop at root
                    if os.path.basename(current) == 'Validator':
                        # Search all subdirectories for mover.sh
                        for root, dirs, files in os.walk(current):
                            if 'mover.sh' in files:
                                mover_script = os.path.join(root, 'mover.sh')
                                print(f"Found mover.sh at: {mover_script}")
                                break
                        if os.path.exists(mover_script):
                            break
                    current = os.path.dirname(current)
            
            moved_script = os.path.join(script_dir, 'moved.py')
            
            # Run moved.py first (before mover.sh moves the files)
            if os.path.exists(moved_script):
                subprocess.run([sys.executable, moved_script], cwd=script_dir, check=True)
            else:
                print(f"Warning: moved.py not found at {moved_script}", file=sys.stderr)
            
            # Run mover.sh (creates new directory, moves files, and prints URL)
            # Run from script_dir (where the files are) not mover_dir (where mover.sh is)
            if os.path.exists(mover_script):
                subprocess.run(['bash', mover_script], cwd=script_dir, check=True)
            else:
                raise FileNotFoundError(f"mover.sh not found. Searched in {script_dir} and Validator subdirectories")
            
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
    
    # Load .env file
    env = {}
    env_file = Path(script_dir) / '.env'
    if not env_file.exists():
        env_file = Path(script_dir).parent / '.env'
    
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    env[key] = value
    
    # Calculate path relative to Validator directory
    # Find 'Validator' in the path and get everything after it
    script_path = script_dir
    parts = script_path.split(os.sep)
    try:
        validator_idx = parts.index('Validator')
        # Get path from Validator onwards (everything after Validator)
        rel_parts = parts[validator_idx + 1:]
        website_path = '/'.join(rel_parts)
        
        # If server.py is directly in Validator directory, find the directory to use
        if not website_path or website_path == 'Validator':
            validator_dir = os.sep.join(parts[:validator_idx + 1])
            
            # First, try to read the latest directory from the file written by mover.sh
            latest_dir_file = os.path.join(validator_dir, '.latest_login_dir')
            if os.path.exists(latest_dir_file):
                try:
                    with open(latest_dir_file, 'r') as f:
                        latest_dir = f.read().strip()
                    # Verify the directory exists and has index.html
                    latest_dir_path = os.path.join(validator_dir, latest_dir)
                    if os.path.isdir(latest_dir_path) and os.path.exists(os.path.join(latest_dir_path, 'index.html')):
                        website_path = latest_dir
                        print(f"Using directory from .latest_login_dir: {website_path}")
                    else:
                        print(f"Warning: Directory {latest_dir} from .latest_login_dir not found or missing index.html")
                        latest_dir = None
                except Exception as e:
                    print(f"Warning: Could not read .latest_login_dir: {e}")
                    latest_dir = None
            else:
                latest_dir = None
            
            # Fallback: find the most recently created subdirectory with index.html
            if not latest_dir:
                subdirs = []
                for item in os.listdir(validator_dir):
                    item_path = os.path.join(validator_dir, item)
                    if os.path.isdir(item_path):
                        index_path = os.path.join(item_path, 'index.html')
                        if os.path.exists(index_path):
                            # Use creation time (st_ctime) for more accurate "newest" detection
                            stat_info = os.stat(item_path)
                            subdirs.append((stat_info.st_ctime, item))
                
                if subdirs:
                    # Sort by creation time (most recent first) and get the first one
                    subdirs.sort(reverse=True)
                    website_path = subdirs[0][1]
                    print(f"Found most recent login directory: {website_path}")
                else:
                    website_path = dir_name
    except (ValueError, IndexError):
        # If Validator not found, use the directory name
        website_path = dir_name
    
    # Listen on all interfaces (0.0.0.0) so it's accessible from external devices
    server = HTTPServer(('0.0.0.0', port), LoginHandler)
    # Get the Pi's IP address for display - try .env file first
    pi_ip = env.get('PI_IP', '').strip()
    if not pi_ip:
        # Fallback: detect IP automatically
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            pi_ip = s.getsockname()[0]
            s.close()
        except:
            pi_ip = "localhost"  # Final fallback
    
    print(f"Server running on http://{pi_ip}:{port}/{dir_name}")
    print(f"Website running at: http://{pi_ip}:8000/{website_path}/index.html")
    print(f"Directory: {script_dir}")
    print("Endpoints:")
    print("  POST /login-success - Called on successful login")
    print("  POST /login-timeout - Called on 10-second timeout")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
        server.server_close()

