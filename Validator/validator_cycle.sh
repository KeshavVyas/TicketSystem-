#!/bin/bash
# Validator cycle script
# Continuously runs: temperature monitoring -> login server -> repeat

VALIDATOR_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$VALIDATOR_DIR"

CORE_LOOP_SCRIPT="$VALIDATOR_DIR/core-loop.py"
LOGIN_SERVER_SCRIPT="$VALIDATOR_DIR/login_server.py"

echo "=========================================="
echo "Validator Cycle Script Starting"
echo "=========================================="
echo ""

# Main cycle loop
while true; do
    echo "----------------------------------------"
    echo "Starting temperature monitoring cycle..."
    echo "----------------------------------------"
    
    # Run core-loop.py (monitors temperature/humidity)
    # Exits when humidity > 50%
    python3 "$CORE_LOOP_SCRIPT"
    CORE_LOOP_EXIT_CODE=$?
    
    if [ $CORE_LOOP_EXIT_CODE -ne 0 ]; then
        echo "Warning: core-loop.py exited with code $CORE_LOOP_EXIT_CODE"
        echo "Waiting 5 seconds before retrying..."
        sleep 5
        continue
    fi
    
    echo ""
    echo "Humidity threshold reached. Starting login server..."
    echo "----------------------------------------"
    
    # Run login_server.py
    # Exits after successful login and TTY write
    python3 "$LOGIN_SERVER_SCRIPT"
    LOGIN_SERVER_EXIT_CODE=$?
    
    if [ $LOGIN_SERVER_EXIT_CODE -ne 0 ]; then
        echo "Warning: login_server.py exited with code $LOGIN_SERVER_EXIT_CODE"
    else
        echo "Login server completed successfully."
    fi
    
    echo ""
    echo "Cycle complete. Restarting temperature monitoring..."
    echo ""
    sleep 1  # Brief pause before restarting cycle
done

