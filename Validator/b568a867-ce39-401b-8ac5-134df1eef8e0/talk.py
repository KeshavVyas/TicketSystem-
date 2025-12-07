#!/usr/bin/env python3
import serial
import time
import argparse

def main():
    parser = argparse.ArgumentParser(description="Serial read/write helper.")
    parser.add_argument("message", help="Message to send over serial.")
    parser.add_argument(
        "-c", "--continuous", action="store_true",
        help="Continuously read lines instead of exiting after one."
    )
    parser.add_argument(
        "--port", default="/dev/ttyUSB0",
        help="Serial port (default: /dev/ttyUSB0)"
    )
    parser.add_argument(
        "--baud", type=int, default=115200,
        help="Baud rate (default: 115200)"
    )
    args = parser.parse_args()

    ser = serial.Serial(args.port, args.baud, timeout=0.1)

    # --- Drain existing serial buffer ---
    time.sleep(0.1)
    ser.reset_input_buffer()
    linelead = 4
    i = 0
    while i < linelead:
        line = ser.readline()
        if line:
            print("RX:", line.decode(errors="replace").rstrip())
            i+=1
    print("Input buffer cleared.")

    # --- Write the message with CRLF ---
    ser.write((args.message + "\r\n").encode("utf-8"))
    ser.flush()
    print(f"Sent: {args.message}")

    # --- Continuous read ---
    if args.continuous:
        
        try:
            while True:
                line = ser.readline()
                if line:
                    print("RX:", line.decode(errors="replace").rstrip())
        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            ser.close()

if __name__ == "__main__":
    main()

