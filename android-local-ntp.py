#!/usr/bin/env python3

import argparse
import signal
import socket
import struct
import sys
import time
from datetime import datetime


VERSION = "1.1.0"


NTP_EPOCH = 2208988800  # Seconds between 1900-01-01 and 1970-01-01


def ntp_timestamp(offset_seconds=0):
    """
    Return the current time as an NTP timestamp (seconds, fraction).
    """
    now = time.time() + offset_seconds + NTP_EPOCH
    seconds = int(now)
    fraction = int((now - seconds) * (2 ** 32))
    return seconds, fraction


def log_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class NTPServer:

    def __init__(self, host, port, verbose=False,
                 offset_hours=0, offset_minutes=0):

        self.host = host
        self.port = port
        self.verbose = verbose

        self.offset_seconds = (
            (offset_hours * 60 + offset_minutes) * 60
        )

        self.running = False

    def log(self, message):
        print(f"[{log_time()}] {message}")

    def build_response(self, request):

        recv_sec, recv_frac = ntp_timestamp(self.offset_seconds)

        # Copy client's transmit timestamp (bytes 40-47)
        originate = request[40:48]

        tx_sec, tx_frac = ntp_timestamp(self.offset_seconds)

        flags = request[0]
        version = (flags >> 3) & 0x07

        leap = 0
        mode = 4  # server

        first = (leap << 6) | (version << 3) | mode

        stratum = 2
        poll = 4
        precision = -20

        root_delay = 0
        root_dispersion = 0

        ref_id = b"LOCL"

        packet = struct.pack(
            "!BBBbIII",
            first,
            stratum,
            poll,
            precision,
            root_delay,
            root_dispersion,
            struct.unpack("!I", ref_id)[0]
        )

        reference = struct.pack("!II", recv_sec, recv_frac)
        receive = struct.pack("!II", recv_sec, recv_frac)
        transmit = struct.pack("!II", tx_sec, tx_frac)

        packet += reference
        packet += originate
        packet += receive
        packet += transmit

        return packet

    def serve(self):

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        try:
            sock.bind((self.host, self.port))

        except PermissionError:
            print("\nERROR: Permission denied.")
            print("Try running the script as Administrator/root.")
            return

        except OSError as e:
            print(f"\nERROR: {e}")
            return

        self.running = True

        total_offset = self.offset_seconds // 60

        self.log(
            f"Android Local NTP v{VERSION}"
        )

        self.log(
            f"Listening on {self.host}:{self.port}"
        )

        self.log(
            f"Effective time offset: {total_offset:+d} minute(s)"
        )

        while self.running:

            try:
                data, addr = sock.recvfrom(1024)

            except KeyboardInterrupt:
                break

            if len(data) < 48:
                self.log(f"Ignored short packet from {addr[0]}")
                continue

            flags = data[0]
            version = (flags >> 3) & 0x07
            mode = flags & 0x07

            self.log(
                f"Request from {addr[0]}:{addr[1]} "
                f"(NTPv{version}, mode={mode})"
            )

            if self.verbose:
                served = datetime.fromtimestamp(
                    time.time() + self.offset_seconds
                )
                self.log(f"Serving time: {served}")

            response = self.build_response(data)

            sock.sendto(response, addr)

            self.log(f"Response sent to {addr[0]}")

        sock.close()

    def stop(self):
        self.running = False


def main():

    parser = argparse.ArgumentParser(
        description="Simple Python NTP Server"
    )
    
    parser.add_argument(
    "--version",
    action="version",
    version=f"%(prog)s v{VERSION}"
    )

    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind (default: 0.0.0.0)"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=123,
        help="UDP port (default: 123)"
    )

    parser.add_argument(
        "--offset-hours",
        type=int,
        default=0,
        help="Hour offset (default: 0)"
    )

    parser.add_argument(
        "--offset-minutes",
        type=int,
        default=0,
        help="Minute offset (default: 0)"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose logging"
    )

    args = parser.parse_args()

    server = NTPServer(
        host=args.host,
        port=args.port,
        verbose=args.verbose,
        offset_hours=args.offset_hours,
        offset_minutes=args.offset_minutes
    )

    def shutdown(sig, frame):
        print()
        server.log("Stopping server...")
        server.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)

    server.serve()


if __name__ == "__main__":
    main()