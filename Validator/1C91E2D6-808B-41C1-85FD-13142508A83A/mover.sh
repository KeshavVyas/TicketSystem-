#!/bin/bash

CURRENT_DIR="$(pwd)"
VALIDATOR_DIR="$(dirname "$CURRENT_DIR")"

if [ "$(basename "$VALIDATOR_DIR")" != "Validator" ]; then
    # Walk up to find Validator directory
    while [ "$VALIDATOR_DIR" != "/" ]; do
        if [ "$(basename "$VALIDATOR_DIR")" = "Validator" ]; then
            break
        fi
        VALIDATOR_DIR="$(dirname "$VALIDATOR_DIR")"
    done
fi

NEW_RANDOM_DIR=$(uuidgen)
# Create new directory directly under Validator
mkdir "$VALIDATOR_DIR/$NEW_RANDOM_DIR"

# Move files from current directory to new directory under Validator
mv index.html "$VALIDATOR_DIR/$NEW_RANDOM_DIR/index.html" 2>/dev/null
mv credentials.json "$VALIDATOR_DIR/$NEW_RANDOM_DIR/credentials.json" 2>/dev/null
mv mover.sh "$VALIDATOR_DIR/$NEW_RANDOM_DIR/mover.sh" 2>/dev/null
mv server.py "$VALIDATOR_DIR/$NEW_RANDOM_DIR/server.py" 2>/dev/null
mv success.py "$VALIDATOR_DIR/$NEW_RANDOM_DIR/success.py" 2>/dev/null
mv moved.py "$VALIDATOR_DIR/$NEW_RANDOM_DIR/moved.py" 2>/dev/null

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

# Write url 
# echo "$URL" > /dev/ttyUSB0 2>/dev/null || true
echo "/dev/ttyUSB0"
echo "$URL"

lsof -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null || true
lsof -ti:8001 2>/dev/null | xargs kill -9 2>/dev/null || true


pkill -9 -f "start_servers.sh" 2>/dev/null || true
pkill -9 -f "http.server" 2>/dev/null || true
pkill -9 -f "server.py" 2>/dev/null || true
