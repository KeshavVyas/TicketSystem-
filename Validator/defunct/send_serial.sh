#!/bin/bash

# Get directory UUID as argument (required)
DIRECTORY_UUID="${1}"

if [ -z "$DIRECTORY_UUID" ]; then
    echo "Error: Directory UUID required as argument" >&2
    exit 1
fi

# Get script directory to find .env file
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Get the Pi's IP address from .env file first
PI_IP=""
if [ -f "$SCRIPT_DIR/.env" ]; then
    PI_IP=$(grep "^PI_IP=" "$SCRIPT_DIR/.env" | cut -d'=' -f2 | tr -d '"' | tr -d "'" | xargs)
fi

# Fallback: detect IP automatically if not in .env
if [ -z "$PI_IP" ] || [ "$PI_IP" = "" ]; then
    PI_IP=$(hostname -I | awk '{print $1}')
    # Fallback if hostname -I doesn't work
    if [ -z "$PI_IP" ] || [ "$PI_IP" = "" ]; then
        PI_IP=$(ip addr show | grep 'inet ' | grep -v '127.0.0.1' | awk '{print $2}' | cut -d/ -f1 | head -n1)
    fi
    # Final fallback to localhost if IP can't be determined
    if [ -z "$PI_IP" ] || [ "$PI_IP" = "" ]; then
        PI_IP="localhost"
    fi
fi

# Construct message: IP:8000/{directory}/index.html
MESSAGE="${PI_IP}:8000/${DIRECTORY_UUID}/index.html"

# Auto-detect Arduino device (Raspberry Pi / Linux)
ARDUINO_DEVICE=""
for pattern in /dev/ttyACM* /dev/ttyUSB*; do
    for dev in $pattern; do
        if [ -e "$dev" ]; then
            ARDUINO_DEVICE="$dev"
            break 2
        fi
    done
done

if [ -z "$ARDUINO_DEVICE" ]; then
    echo "Error: Arduino device not found" >&2
    exit 1
fi

# Get the script directory to find talk.py
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Activate virtual environment if it exists, then run talk.py
if [ -f "$SCRIPT_DIR/env/bin/activate" ]; then
    source "$SCRIPT_DIR/env/bin/activate"
fi

cd "$SCRIPT_DIR"
python3 talk.py --port "$ARDUINO_DEVICE" "$MESSAGE" 
