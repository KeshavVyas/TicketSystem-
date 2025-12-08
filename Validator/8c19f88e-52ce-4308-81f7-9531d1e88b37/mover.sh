#!/bin/bash

# Use the current working directory (where server.py is running) as the source directory
# This allows mover.sh to be called from any location and work with files
# in the directory where it's invoked from
CURRENT_DIR="$(pwd)"

# Walk up to find Validator directory
VALIDATOR_DIR="$CURRENT_DIR"
while [ "$VALIDATOR_DIR" != "/" ]; do
    if [ "$(basename "$VALIDATOR_DIR")" = "Validator" ]; then
        break
    fi
    VALIDATOR_DIR="$(dirname "$VALIDATOR_DIR")"
done

# Safety check: make sure we found Validator
if [ "$VALIDATOR_DIR" = "/" ]; then
    echo "Error: Could not find Validator directory" >&2
    exit 1
fi

echo "Source directory: $CURRENT_DIR"
echo "Validator directory: $VALIDATOR_DIR"

# Find the directory with the login files (index.html and credentials.json)
# First check if .latest_login_dir exists and has a valid directory
SOURCE_LOGIN_DIR=""
LATEST_DIR_FILE="$VALIDATOR_DIR/.latest_login_dir"
if [ -f "$LATEST_DIR_FILE" ]; then
    LATEST_DIR=$(cat "$LATEST_DIR_FILE" | tr -d '\n\r ')
    if [ -n "$LATEST_DIR" ] && [ -d "$VALIDATOR_DIR/$LATEST_DIR" ] && [ -f "$VALIDATOR_DIR/$LATEST_DIR/index.html" ]; then
        SOURCE_LOGIN_DIR="$VALIDATOR_DIR/$LATEST_DIR"
        echo "Found login files in: $SOURCE_LOGIN_DIR (from .latest_login_dir)"
    fi
fi

# If not found, search for the most recent directory with index.html
if [ -z "$SOURCE_LOGIN_DIR" ]; then
    echo "Searching for directory with login files..."
    MOST_RECENT_DIR=""
    MOST_RECENT_TIME=0
    for item in "$VALIDATOR_DIR"/*; do
        if [ -d "$item" ]; then
            index_file="$item/index.html"
            if [ -f "$index_file" ]; then
                # Get creation time
                item_time=$(stat -c %W "$item" 2>/dev/null || stat -f %B "$item" 2>/dev/null || echo "0")
                if [ -z "$item_time" ] || [ "$item_time" = "0" ]; then
                    item_time=$(stat -c %Y "$item" 2>/dev/null || echo "0")
                fi
                if [ "$item_time" -gt "$MOST_RECENT_TIME" ]; then
                    MOST_RECENT_TIME=$item_time
                    MOST_RECENT_DIR="$item"
                fi
            fi
        fi
    done
    if [ -n "$MOST_RECENT_DIR" ]; then
        SOURCE_LOGIN_DIR="$MOST_RECENT_DIR"
        echo "Found login files in: $SOURCE_LOGIN_DIR (most recent)"
    fi
fi

# Fallback to CURRENT_DIR if still not found
if [ -z "$SOURCE_LOGIN_DIR" ]; then
    SOURCE_LOGIN_DIR="$CURRENT_DIR"
    echo "Using current directory as source: $SOURCE_LOGIN_DIR"
fi

# Generate UUID and use only the part before the first hyphen
FULL_UUID=$(uuidgen)
NEW_RANDOM_DIR="${FULL_UUID%%-*}"  # Extract everything before the first hyphen
# Create new directory directly under Validator
echo "Creating new directory: $NEW_RANDOM_DIR"
mkdir -p "$VALIDATOR_DIR/$NEW_RANDOM_DIR"
if [ ! -d "$VALIDATOR_DIR/$NEW_RANDOM_DIR" ]; then
    echo "Error: Failed to create directory $VALIDATOR_DIR/$NEW_RANDOM_DIR" >&2
    exit 1
fi
echo "Directory created successfully: $VALIDATOR_DIR/$NEW_RANDOM_DIR"

# Get the Pi's IP address from .env file first
PI_IP=""
if [ -f "$VALIDATOR_DIR/.env" ]; then
    PI_IP=$(grep "^PI_IP=" "$VALIDATOR_DIR/.env" | cut -d'=' -f2 | tr -d '"' | tr -d "'" | xargs)
fi

# Fallback: detect IP automatically if not in .env
if [ -z "$PI_IP" ] || [ "$PI_IP" = "" ]; then
    PI_IP=$(hostname -I | awk '{print $1}')
    if [ -z "$PI_IP" ] || [ "$PI_IP" = "" ]; then
        PI_IP=$(ip addr show | grep 'inet ' | grep -v '127.0.0.1' | awk '{print $2}' | cut -d/ -f1 | head -n1)
    fi
    # Final fallback to localhost if IP can't be determined
    if [ -z "$PI_IP" ] || [ "$PI_IP" = "" ]; then
        PI_IP="localhost"
    fi
fi

# Move only index.html and credentials.json to the new directory (login page files)
LOGIN_FILES_MOVED=0
if [ -f "$SOURCE_LOGIN_DIR/index.html" ]; then
    # Copy and replace localhost with Pi IP in index.html
    cp "$SOURCE_LOGIN_DIR/index.html" "$VALIDATOR_DIR/$NEW_RANDOM_DIR/index.html" 2>/dev/null
    if [ -f "$VALIDATOR_DIR/$NEW_RANDOM_DIR/index.html" ]; then
        # Replace localhost:8001 with Pi IP:8001
        sed -i "s|http://localhost:8001|http://${PI_IP}:8001|g" "$VALIDATOR_DIR/$NEW_RANDOM_DIR/index.html"
        # Also replace any other localhost references
        sed -i "s|http://localhost:8000|http://${PI_IP}:8000|g" "$VALIDATOR_DIR/$NEW_RANDOM_DIR/index.html"
        LOGIN_FILES_MOVED=$((LOGIN_FILES_MOVED + 1))
        echo "Moved and updated index.html from $SOURCE_LOGIN_DIR to $NEW_RANDOM_DIR (replaced localhost with $PI_IP)"
    fi
fi
if [ -f "$SOURCE_LOGIN_DIR/credentials.json" ]; then
    mv "$SOURCE_LOGIN_DIR/credentials.json" "$VALIDATOR_DIR/$NEW_RANDOM_DIR/credentials.json" 2>/dev/null && LOGIN_FILES_MOVED=$((LOGIN_FILES_MOVED + 1)) || true
    echo "Moved credentials.json from $SOURCE_LOGIN_DIR to $NEW_RANDOM_DIR"
fi

echo "Moved $LOGIN_FILES_MOVED login files to $NEW_RANDOM_DIR"

# Move all other files (scripts) to the Validator directory (parent directory)
SCRIPTS_MOVED=0
for file in "$CURRENT_DIR"/*; do
    if [ -e "$file" ] && [ -f "$file" ]; then
        filename=$(basename "$file")
        # Skip mover.sh itself (we're still running from it) and login files (already moved)
        if [ "$filename" != "mover.sh" ] && [ "$filename" != "index.html" ] && [ "$filename" != "credentials.json" ]; then
            mv "$file" "$VALIDATOR_DIR/$filename" 2>/dev/null && SCRIPTS_MOVED=$((SCRIPTS_MOVED + 1)) || true
        fi
    fi
done

# Also move any hidden files (except . and ..) to Validator directory
for file in "$CURRENT_DIR"/.*; do
    if [ -e "$file" ] && [ -f "$file" ]; then
        filename=$(basename "$file")
        # Skip . and .. directory references
        if [ "$filename" != "." ] && [ "$filename" != ".." ]; then
            mv "$file" "$VALIDATOR_DIR/$filename" 2>/dev/null && SCRIPTS_MOVED=$((SCRIPTS_MOVED + 1)) || true
        fi
    fi
done

echo "Moved $SCRIPTS_MOVED script files to Validator directory"

# Remove the now-empty current directory
cd "$VALIDATOR_DIR" 2>/dev/null || true
rmdir "$CURRENT_DIR" 2>/dev/null || true

find "$VALIDATOR_DIR" -type d -empty -delete 2>/dev/null || true

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

# Write the new directory name to a file so server.py knows which directory to use next time
# This ensures the directory name is synced across all uses
LATEST_DIR_FILE="$VALIDATOR_DIR/.latest_login_dir"
echo "$NEW_RANDOM_DIR" > "$LATEST_DIR_FILE"
echo "=========================================="
echo "SYNCED DIRECTORY: $NEW_RANDOM_DIR"
echo "=========================================="
echo "✓ Directory created: $VALIDATOR_DIR/$NEW_RANDOM_DIR"
echo "✓ Files moved to: $VALIDATOR_DIR/$NEW_RANDOM_DIR/"
echo "✓ Saved to .latest_login_dir: $NEW_RANDOM_DIR"
echo "✓ Will send to serial: $NEW_RANDOM_DIR"
echo "=========================================="

# Call send_serial.sh with the new directory UUID as the last thing before ending
# This will send the message: {IP}:8000/{NEW_RANDOM_DIR}/index.html
# The same NEW_RANDOM_DIR variable is used everywhere to ensure sync
SEND_SERIAL_SCRIPT="$VALIDATOR_DIR/send_serial.sh"
if [ -f "$SEND_SERIAL_SCRIPT" ]; then
    echo "Calling send_serial.sh with directory: $NEW_RANDOM_DIR"
    cd "$VALIDATOR_DIR"
    bash "$SEND_SERIAL_SCRIPT" "$NEW_RANDOM_DIR" || echo "Warning: Could not send serial message" >&2
else
    echo "Warning: send_serial.sh not found at $SEND_SERIAL_SCRIPT" >&2
fi

lsof -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null || true
lsof -ti:8001 2>/dev/null | xargs kill -9 2>/dev/null || true

pkill -9 -f "start_servers.sh" 2>/dev/null || true
pkill -9 -f "http.server" 2>/dev/null || true
pkill -9 -f "server.py" 2>/dev/null || true

# Turn on GPIO 22 for 3 seconds before exiting
echo "Turning on GPIO 22 for 3 seconds..."
python3 -u -c "
from gpiozero import OutputDevice
import time
import sys
gpio_22 = None
try:
    gpio_22 = OutputDevice(22, initial_value=True)
    print('GPIO 22 turned ON', flush=True)
    time.sleep(3)
    gpio_22.off()
    print('GPIO 22 turned OFF', flush=True)
except Exception as e:
    print(f'Error: {e}', file=sys.stderr, flush=True)
finally:
    if gpio_22:
        gpio_22.close()
    sys.stdout.flush()
    sys.stderr.flush()
" 2>&1 || true

echo "mover.sh completed successfully"

# Call read_temp.py as the very last thing
READ_TEMP_SCRIPT="$VALIDATOR_DIR/read_temp.py"
if [ -f "$READ_TEMP_SCRIPT" ]; then
    echo "Starting read_temp.py..."
    cd "$VALIDATOR_DIR"
    # Run in background but keep output visible (or redirect to log file)
    python3 "$READ_TEMP_SCRIPT" > /tmp/read_temp.log 2>&1 &
    echo "read_temp.py started in background (output in /tmp/read_temp.log)"
    echo "To view output: tail -f /tmp/read_temp.log"
else
    echo "Warning: read_temp.py not found at $READ_TEMP_SCRIPT" >&2
fi

exit 0