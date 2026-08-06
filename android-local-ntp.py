#!/usr/bin/env python3

import argparse
import signal
import socket
import struct
import sys
import threading
import time
from datetime import datetime

NTP_EPOCH = 2208988800  # Seconds between 1900 and 1970


def ntp_timestamp():
    """
    Return current time as NTP seconds and fraction.
    """
    now = time.time() + NTP_EPOCH
    seconds = int(now)
    fraction = int((now - seconds) * (2 ** 32))
    return seconds, fraction


def timestamp_string():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class NTPServer:

    def __init__(self, host, port, verbose=False):
        self.host = host
        self.port = port
        self.verbose = verbose
        self.running = False

    def log(self, msg):
        print(f"[{timestamp_string()}] {msg}")

    def build_response(self, request):
        recv_sec, recv_frac = ntp_timestamp()

        # Copy client's transmit timestamp (bytes 40-47)
        originate = request[40:48]

        tx_sec, tx_frac = ntp_timestamp()

        leap = 0
        version = 4
        mode = 4          # server

        first = (leap << 6) | (version << 3) | mode

        stratum = 2
        poll = 4
        precision = -20

        root_delay = 0
        root_dispersion = 0

        ref_id = b"LOCL"

        reference = struct.pack("!II", recv_sec, recv_frac)
        receive = struct.pack("!II", recv_sec, recv_frac)
        transmit = struct.pack("!II", tx_sec, tx_frac)

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

        packet += reference
        packet += originate
        packet += receive
        packet += transmit

        return packet

    def handle_packet(self, data, addr, sock):

        if len(data) < 48:
            self.log(f"Ignored short packet from {addr[0]}")
            return

        flags = data[0]
        version = (flags >> 3) & 0x07
        mode = flags & 0x07

        self.log(
            f"Request from {addr[0]}:{addr[1]} "
            f"(NTPv{version}, mode={mode})"
        )

        if self.verbose:
            self.log(f"Packet size: {len(data)} bytes")

        response = self.build_response(data)

        sock.sendto(response, addr)

        self.log(f"Response sent to {addr[0]}")

    def serve(self):

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.host, self.port))

        self.running = True

        self.log(f"NTP server listening on {self.host}:{self.port}")

        while self.running:
            try:
                data, addr = sock.recvfrom(1024)
                threading.Thread(
                    target=self.handle_packet,
                    args=(data, addr, sock),
                    daemon=True
                ).start()

            except KeyboardInterrupt:
                break

        sock.close()

    def stop(self):
        self.running = False


def main():

    parser = argparse.ArgumentParser(description="Simple Python NTP Server")

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
        "--verbose",
        action="store_true",
        help="Verbose logging"
    )

    args = parser.parse_args()

    server = NTPServer(args.host, args.port, args.verbose)

    def shutdown(sig, frame):
        print()
        server.log("Stopping server...")
        server.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)

    server.serve()


if __name__ == "__main__":
    main()