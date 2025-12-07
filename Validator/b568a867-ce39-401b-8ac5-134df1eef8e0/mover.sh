#!/bin/bash

# Get the directory where this script is located (the subdirectory with files to move)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CURRENT_DIR="$SCRIPT_DIR"

# Walk up to find Validator directory (parent of the subdirectory)
VALIDATOR_DIR="$CURRENT_DIR"
while [ "$VALIDATOR_DIR" != "/" ]; do
    if [ "$(basename "$VALIDATOR_DIR")" = "Validator" ]; then
        break
    fi
    VALIDATOR_DIR="$(dirname "$VALIDATOR_DIR")"
done

# Safety check: make sure we found Validator and we're not in the Validator directory itself
if [ "$VALIDATOR_DIR" = "/" ] || [ "$CURRENT_DIR" = "$VALIDATOR_DIR" ]; then
    echo "Error: mover.sh must be run from a subdirectory of Validator, not from Validator itself" >&2
    exit 1
fi

# Turn on GPIO 22 to indicate moving has started
python3 -c "
from gpiozero import OutputDevice
import time
gpio_22 = OutputDevice(22, initial_value=True)
print('GPIO 22 turned ON - Moving files...')
time.sleep(0.1)  # Ensure state is set
gpio_22.close()
" || echo "Warning: Could not set GPIO 22" >&2

# Generate UUID using Python (uuidgen may not be available)
NEW_RANDOM_DIR=$(python3 -c "import uuid; print(uuid.uuid4())")

# Validate that we got a UUID
if [ -z "$NEW_RANDOM_DIR" ] || [ "$NEW_RANDOM_DIR" = "" ]; then
    echo "Error: Failed to generate UUID" >&2
    # Turn off GPIO 22 on error
    python3 -c "from gpiozero import OutputDevice; gpio_22 = OutputDevice(22, initial_value=False); gpio_22.close()" 2>/dev/null || true
    exit 1
fi

# Create new directory directly under Validator
mkdir -p "$VALIDATOR_DIR/$NEW_RANDOM_DIR"

if [ ! -d "$VALIDATOR_DIR/$NEW_RANDOM_DIR" ]; then
    echo "Error: Failed to create directory $VALIDATOR_DIR/$NEW_RANDOM_DIR" >&2
    exit 1
fi

# Move ALL files from current directory to new directory under Validator
# Exclude mover.sh itself (since it's still running) and the parent directory references
MOVED_FILES=0
for file in "$CURRENT_DIR"/*; do
    if [ -e "$file" ] && [ -f "$file" ]; then
        filename=$(basename "$file")
        # Skip mover.sh itself (we're still running from it)
        if [ "$filename" != "mover.sh" ]; then
            mv "$file" "$VALIDATOR_DIR/$NEW_RANDOM_DIR/$filename" 2>/dev/null && MOVED_FILES=$((MOVED_FILES + 1)) || true
        fi
    fi
done

# Also move any hidden files (except . and ..)
for file in "$CURRENT_DIR"/.*; do
    if [ -e "$file" ] && [ -f "$file" ]; then
        filename=$(basename "$file")
        # Skip . and .. directory references
        if [ "$filename" != "." ] && [ "$filename" != ".." ]; then
            mv "$file" "$VALIDATOR_DIR/$NEW_RANDOM_DIR/$filename" 2>/dev/null && MOVED_FILES=$((MOVED_FILES + 1)) || true
        fi
    fi
done

# Explicitly ensure send_serial.sh and talk.py are moved (in case they weren't caught above)
if [ -f "$CURRENT_DIR/send_serial.sh" ] && [ ! -f "$VALIDATOR_DIR/$NEW_RANDOM_DIR/send_serial.sh" ]; then
    mv "$CURRENT_DIR/send_serial.sh" "$VALIDATOR_DIR/$NEW_RANDOM_DIR/send_serial.sh" 2>/dev/null && MOVED_FILES=$((MOVED_FILES + 1)) || true
    echo "Explicitly moved send_serial.sh"
fi

if [ -f "$CURRENT_DIR/talk.py" ] && [ ! -f "$VALIDATOR_DIR/$NEW_RANDOM_DIR/talk.py" ]; then
    mv "$CURRENT_DIR/talk.py" "$VALIDATOR_DIR/$NEW_RANDOM_DIR/talk.py" 2>/dev/null && MOVED_FILES=$((MOVED_FILES + 1)) || true
    echo "Explicitly moved talk.py"
fi

echo "Moved $MOVED_FILES files to $NEW_RANDOM_DIR"

# Remove the now-empty current directory
# First, make sure we're not in the directory we're trying to delete
cd "$VALIDATOR_DIR" 2>/dev/null || true

# Try to remove the directory - use force if needed
if [ -d "$CURRENT_DIR" ]; then
    # Check if directory is empty
    if [ -z "$(ls -A "$CURRENT_DIR" 2>/dev/null)" ]; then
        rmdir "$CURRENT_DIR" 2>/dev/null || true
    else
        # Directory not empty, try to remove remaining files and then directory
        rm -rf "$CURRENT_DIR" 2>/dev/null || true
    fi
fi

# Clean up any empty directories
find "$VALIDATOR_DIR" -type d -empty -delete 2>/dev/null || true

# Turn off GPIO 22 to indicate moving is complete
python3 -c "
from gpiozero import OutputDevice
gpio_22 = OutputDevice(22, initial_value=False)
print('GPIO 22 turned OFF - Moving complete')
gpio_22.close()
" || echo "Warning: Could not turn off GPIO 22" >&2

NEW_DIR_PATH="$VALIDATOR_DIR/$NEW_RANDOM_DIR"
IFS='/' read -ra PARTS <<< "$NEW_DIR_PATH"
VALIDATOR_FOUND=0
VALIDATOR_IDX=0
for i in "${!PARTS[@]}"; do
    if [ "${PARTS[$i]}" = "Validator" ]; then
        VALIDATOR_FOUND=1
        VALIDATOR_IDX=$i
        break
    fi
done

if [ $VALIDATOR_FOUND -eq 1 ]; then
    WEBSITE_PATH=""
    for ((i=VALIDATOR_IDX+1; i<${#PARTS[@]}; i++)); do
        if [ -z "$WEBSITE_PATH" ]; then
            WEBSITE_PATH="${PARTS[$i]}"
        else
            WEBSITE_PATH="$WEBSITE_PATH/${PARTS[$i]}"
        fi
    done
    URL="http://localhost:8000/$WEBSITE_PATH/index.html"
else
    # Fallback: just use the new directory name
    URL="http://localhost:8000/$NEW_RANDOM_DIR/index.html"
fi

# Get the Pi's IP address
PI_IP=$(hostname -I | awk '{print $1}')
# Fallback if hostname -I doesn't work
if [ -z "$PI_IP" ] || [ "$PI_IP" = "" ]; then
    PI_IP=$(ip addr show | grep 'inet ' | grep -v '127.0.0.1' | awk '{print $2}' | cut -d/ -f1 | head -n1)
fi
# Final fallback to localhost if IP can't be determined
if [ -z "$PI_IP" ] || [ "$PI_IP" = "" ]; then
    PI_IP="localhost"
fi

# Also print for debugging
echo "New directory UUID: $NEW_RANDOM_DIR"
echo "URL: $URL"

lsof -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null || true
lsof -ti:8001 2>/dev/null | xargs kill -9 2>/dev/null || true

pkill -9 -f "start_servers.sh" 2>/dev/null || true
pkill -9 -f "http.server" 2>/dev/null || true
pkill -9 -f "server.py" 2>/dev/null || true

# Call send_serial.sh with the new directory UUID as the last thing before ending
# This will send the message: {IP}:8000/{NEW_RANDOM_DIR}/index.html
# send_serial.sh should be in the new directory (it was moved there)
SEND_SERIAL_SCRIPT="$VALIDATOR_DIR/$NEW_RANDOM_DIR/send_serial.sh"
if [ -f "$SEND_SERIAL_SCRIPT" ]; then
    echo "Calling send_serial.sh to send URL to Arduino..."
    cd "$VALIDATOR_DIR/$NEW_RANDOM_DIR"
    bash "$SEND_SERIAL_SCRIPT" "$NEW_RANDOM_DIR" || echo "Warning: Could not send serial message" >&2
else
    echo "Warning: send_serial.sh not found at $SEND_SERIAL_SCRIPT" >&2
    # Try to find send_serial.sh in Validator directory as fallback
    FALLBACK_SCRIPT="$VALIDATOR_DIR/send_serial.sh"
    if [ -f "$FALLBACK_SCRIPT" ]; then
        echo "Using fallback send_serial.sh from Validator directory..."
        cd "$VALIDATOR_DIR"
        bash "$FALLBACK_SCRIPT" "$NEW_RANDOM_DIR" || echo "Warning: Could not send serial message" >&2
    fi
fi
