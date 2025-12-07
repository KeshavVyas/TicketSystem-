#!/bin/bash


VALIDATOR_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$VALIDATOR_DIR"

# Run idle.py to turn on GPIO 17
IDLE_PATH=$(find . -name "idle.py" -type f | sort | tail -1)
if [ -n "$IDLE_PATH" ]; then
    IDLE_DIR="$(cd "$VALIDATOR_DIR/$(dirname "$IDLE_PATH")" && pwd)"
    echo "Running idle.py to turn on GPIO 17..."
    cd "$IDLE_DIR"
    python3 idle.py &
    IDLE_PID=$!
    sleep 0.5  # Give it time to set GPIO
    cd "$VALIDATOR_DIR"
fi

SERVER_PATH=$(find . -name "server.py" -type f | sort | tail -1)

if [ -z "$SERVER_PATH" ]; then
    echo "No server.py found. Starting HTTP server only..."
    echo "Starting HTTP server (frontend) on port 8000..."
    python3 -m http.server 8000
    exit 0
fi

SERVER_DIR="$(cd "$VALIDATOR_DIR/$(dirname "$SERVER_PATH")" && pwd)"

echo "Found server.py in: $SERVER_DIR"
echo ""

echo "Stopping any existing servers on ports 8000 and 8001..."
lsof -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null
lsof -ti:8001 2>/dev/null | xargs kill -9 2>/dev/null
sleep 1

echo "Starting HTTP server (frontend) on port 8000..."
cd "$VALIDATOR_DIR"
python3 -m http.server 8000 > /dev/null 2>&1 &
HTTP_PID=$!
echo "HTTP server started (PID: $HTTP_PID)"
echo ""

echo "Starting backend server on port 8001..."
echo "Server directory: $SERVER_DIR"
echo ""
cd "$SERVER_DIR"
python3 server.py

# If server.py exits, kill the HTTP server too
kill $HTTP_PID 2>/dev/null

