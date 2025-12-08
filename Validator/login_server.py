#!/usr/bin/env python3
"""Simple login page server"""

import socket
import random
import string
import threading
import time
import subprocess
import glob
import os
import sys
import signal
from flask import Flask, request, render_template_string, session, redirect, url_for
from pathlib import Path
from gpiozero import OutputDevice

# Seed random for better randomness (uses system time)
random.seed()

app = Flask(__name__)
app.secret_key = 'secret-key-change-this'
# Disable session persistence - no caching
app.config['PERMANENT_SESSION_LIFETIME'] = 0
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

USERNAME = "Admin"
PASSWORD = "password"

# Load .env file for GPIO configuration
env = {}
env_file = Path(__file__).parent / '.env'
if not env_file.exists():
    env_file = Path(__file__).parent.parent / '.env'

if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                env[key] = value

GREEN_GPIO = int(env.get('GREEN_GPIO', '4'))
RED_GPIO = int(env.get('RED_GPIO', '22'))
YELLOW_GPIO = int(env.get('YELLOW_GPIO', '27'))

# Setup LEDs with error handling
try:
    green_led = OutputDevice(GREEN_GPIO, initial_value=False)
    print(f"✓ Green LED initialized on GPIO {GREEN_GPIO}")
except Exception as e:
    print(f"✗ Error initializing Green LED on GPIO {GREEN_GPIO}: {e}")
    green_led = None

try:
    red_led = OutputDevice(RED_GPIO, initial_value=False)
    print(f"✓ Red LED initialized on GPIO {RED_GPIO}")
except Exception as e:
    print(f"✗ Error initializing Red LED on GPIO {RED_GPIO}: {e}")
    red_led = None

try:
    yellow_led = OutputDevice(YELLOW_GPIO, initial_value=False)
    print(f"✓ Yellow LED initialized on GPIO {YELLOW_GPIO}")
except Exception as e:
    print(f"✗ Error initializing Yellow LED on GPIO {YELLOW_GPIO}: {e}")
    yellow_led = None

# Function to turn off LED after delay
def turn_off_led_after_delay(led, delay=3):
    time.sleep(delay)
    led.off()

# Function to turn off yellow and green LEDs
def turn_off_yellow_green():
    print("DEBUG: Turning off yellow and green LEDs...")
    try:
        if yellow_led:
            yellow_led.off()
        if green_led:
            green_led.off()
    except Exception as e:
        print(f"DEBUG: Error turning off LEDs: {e}")

# Global variable to track if we should shutdown
shutdown_event = threading.Event()

# Signal handler for clean shutdown
def signal_handler(sig, frame):
    """Handle shutdown signals"""
    print("\nReceived shutdown signal, exiting...")
    # Clean up GPIO
    if red_led:
        try:
            red_led.off()
            red_led.close()
        except:
            pass
    if yellow_led:
        try:
            yellow_led.off()
            yellow_led.close()
        except:
            pass
    if green_led:
        try:
            green_led.off()
            green_led.close()
        except:
            pass
    # Use os._exit for immediate exit (bypasses Python cleanup that might hang)
    os._exit(0)

# Register signal handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# Function to shutdown Flask server properly
def shutdown_server():
    """Trigger server shutdown - exits immediately"""
    shutdown_event.set()
    # GPIO cleanup already done in send_to_tty, so just exit immediately
    print("Exiting process...")
    # Force immediate exit - use os._exit which bypasses all cleanup
    # This kills the entire process including all threads
    try:
        os._exit(0)
    except:
        # Fallback: use SIGKILL if os._exit fails
        os.kill(os.getpid(), signal.SIGKILL)

# Function to find TTY device (similar to send_serial.sh)
def find_tty_device():
    # Check for common TTY devices (ttyACM* first, then ttyUSB*)
    patterns = ['/dev/ttyACM*', '/dev/ttyUSB*']
    for pattern in patterns:
        devices = glob.glob(pattern)
        if devices:
            return devices[0]  # Return first found device
    return None

# Function to send message to TTY using talk.py (same as send_serial.sh)
def send_to_tty(message):
    # Find TTY device
    device = find_tty_device()
    if device is None:
        print("Error: TTY device not found (checked /dev/ttyACM* and /dev/ttyUSB*)")
        return
    
    # Get script directory
    script_dir = Path(__file__).parent
    
    # Wait a few seconds to let green LED be visible after successful login
    time.sleep(4.0)
    
    # Turn off yellow and green LEDs before TTY write
    turn_off_yellow_green()
    
    # Call talk.py via subprocess (same as send_serial.sh does)
    try:
        talk_py_path = script_dir / 'talk.py'
        result = subprocess.run(
            ['python3', str(talk_py_path), '--port', device, message],
            cwd=str(script_dir),
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print(f"Successfully sent to TTY via talk.py: {message}")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"Error from talk.py: {result.stderr}")
        
        # Turn on red LED after TTY write
        print("DEBUG: Turning on red LED after TTY write...")
        if red_led:
            try:
                red_led.on()
                # Wait 2 seconds
                time.sleep(2.0)
                # Turn off red LED
                print("DEBUG: Turning off red LED...")
                red_led.off()
            except Exception as e:
                print(f"DEBUG: Error controlling red LED: {e}")
        
        # Clean up GPIO pins before shutdown
        print("Cleaning up GPIO pins...")
        if red_led:
            try:
                red_led.off()
                red_led.close()
            except:
                pass
        if yellow_led:
            try:
                yellow_led.off()
                yellow_led.close()
            except:
                pass
        if green_led:
            try:
                green_led.off()
                green_led.close()
            except:
                pass
        
        # Shutdown server after TTY write and LED sequence complete
        print("Shutting down server to protect URL...")
        shutdown_server()
        
    except subprocess.TimeoutExpired:
        print("Error: talk.py timed out")
        shutdown_server()
    except Exception as e:
        print(f"Error calling talk.py: {e}")
        # Still shutdown on error
        print("Shutting down server...")
        shutdown_server()

# Function to get the next login URL
def get_next_login_url():
    # Get the next secret path (the one saved for next time)
    secret_file = Path(__file__).parent / 'secret_path.txt'
    if secret_file.exists():
        with open(secret_file, 'r') as f:
            next_secret_path = f.read().strip()
    else:
        # If file doesn't exist, generate one
        next_secret_path = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
    
    # Get IP address
    ip = get_ip()
    
    # Port is 5000
    port = 5000
    
    # Form the URL without http://
    url = f"{ip}:{port}/{next_secret_path}"
    return url

# Load secret path from file or generate new one
def get_secret_path():
    secret_file = Path(__file__).parent / 'secret_path.txt'
    
    # Load current secret path from file
    if secret_file.exists():
        with open(secret_file, 'r') as f:
            current_path = f.read().strip()
        print(f"Loaded secret path from file: {current_path}")
    else:
        # Generate first one if file doesn't exist
        current_path = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
        print(f"Generated new secret path (no file): {current_path}")
    
    # Generate next secret path and save it for next time
    next_path = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
    with open(secret_file, 'w') as f:
        f.write(next_path)
    print(f"Generated and saved next secret path: {next_path}")
    
    return current_path

SECRET_PATH = get_secret_path()

# Get IP address
def get_ip():
    # Try to get from .env file first
    env_file = Path(__file__).parent / '.env'
    if not env_file.exists():
        env_file = Path(__file__).parent.parent / '.env'
    
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if 'PI_IP' in line and '=' in line:
                    return line.split('=', 1)[1].strip()
    
    # Fallback: detect IP automatically
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head><title>Login</title></head>
<body style="font-family: Arial; text-align: center; padding-top: 100px;">
    <h2>Login</h2>
    <form method="POST">
        <input type="text" name="username" placeholder="Username" required><br><br>
        <input type="password" name="password" placeholder="Password" required><br><br>
        <button type="submit">Login</button>
    </form>
    {% if error %}<p style="color:red;">{{ error }}</p>{% endif %}
</body>
</html>
"""

SUCCESS_HTML = """
<!DOCTYPE html>
<html>
<head><title>Success</title></head>
<body style="font-family: Arial; text-align: center; padding-top: 100px;">
    <h2>Login Successful!</h2>
    <p>Welcome, {{ username }}!</p>
</body>
</html>
"""

@app.route('/')
def root():
    # Return 404 for root path - security through obscurity
    return "Not Found", 404

@app.route(f'/{SECRET_PATH}', methods=['GET', 'POST'])
def login():
    # Make session non-permanent (no caching)
    session.permanent = False
    
    # Initialize failed attempts counter if not exists
    if 'failed_attempts' not in session:
        session['failed_attempts'] = 0
    
    # Check if blocked (2 or more failed attempts)
    if session.get('failed_attempts', 0) >= 2:
        return render_template_string(LOGIN_HTML, error="Access blocked. Too many failed attempts.")
    
    if request.method == 'POST':
        if request.form.get('username') == USERNAME and request.form.get('password') == PASSWORD:
            # Successful login - reset failed attempts
            session['failed_attempts'] = 0
            session['logged_in'] = True
            session['username'] = USERNAME
            session.permanent = False  # Don't persist session
            # Turn on green LED on successful login
            if green_led:
                try:
                    green_led.on()
                    # Turn off LED after 6 seconds (longer duration so it's visible)
                    threading.Thread(target=turn_off_led_after_delay, args=(green_led, 6), daemon=True).start()
                except Exception as e:
                    print(f"Error controlling green LED: {e}")
            # Send next login URL to TTY (this will turn off yellow/green LEDs when it starts)
            # Add a small delay before starting TTY write to let green LED be visible
            next_url = get_next_login_url()
            threading.Thread(target=send_to_tty, args=(next_url,), daemon=True).start()
            return redirect(url_for('success'))
        else:
            # Incorrect credentials - increment failed attempts
            session['failed_attempts'] = session.get('failed_attempts', 0) + 1
            attempts_remaining = 2 - session['failed_attempts']
            
            # Incorrect credentials detected - turn on red LED
            if red_led:
                try:
                    red_led.on()
                    # Turn off red LED after 3 seconds
                    threading.Thread(target=turn_off_led_after_delay, args=(red_led, 3), daemon=True).start()
                except Exception as e:
                    print(f"Error controlling red LED: {e}")
            print(f"Failed login attempt - Username: {request.form.get('username')} ({session['failed_attempts']}/2 attempts)")
            
            if session['failed_attempts'] >= 2:
                # Send next login URL to TTY after 2 failed attempts
                next_url = get_next_login_url()
                threading.Thread(target=send_to_tty, args=(next_url,), daemon=True).start()
                return render_template_string(LOGIN_HTML, error="Access blocked. Too many failed attempts.")
            else:
                return render_template_string(LOGIN_HTML, error=f"Invalid credentials. {attempts_remaining} attempt(s) remaining.")
    
    # Don't check for existing login - always show login page
    # Clear any existing session
    session.clear()
    return render_template_string(LOGIN_HTML)

@app.route(f'/{SECRET_PATH}/success')
def success():
    # Check login but clear session immediately after
    if not session.get('logged_in'):
        session.clear()
        return redirect(url_for('login'))
    
    username = session.get('username')
    # Clear session immediately after checking (no caching)
    session.clear()
    return render_template_string(SUCCESS_HTML, username=username)

if __name__ == '__main__':
    ip = get_ip()
    port = 5000
    login_url = f"http://{ip}:{port}/{SECRET_PATH}"
    print(f"\n{'='*50}")
    print(f"Login server starting...")
    print(f"Secret login URL: {login_url}")
    print(f"{'='*50}\n")
    
    # Turn on yellow LED when server starts
    if yellow_led:
        try:
            yellow_led.on()
            print(f"✓ Yellow LED turned on (server running)")
        except Exception as e:
            print(f"✗ Error turning on yellow LED: {e}")
    
    app.run(host='0.0.0.0', port=port)
