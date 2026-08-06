# Android Local NTP

A lightweight NTP (Network Time Protocol) server written in pure Python for Android TV boxes and Android devices.

This project was created to solve a very specific problem:

- Android TV boxes without a battery-backed RTC (Real Time Clock)
- Frequent power outages causing the system clock to reset
- Android configured to synchronize time from Internet NTP servers that are blocked or unreachable
- Need a simple local NTP server without installing Chrony, Docker, or other services

The server listens for NTP requests and replies with the current system time from the host computer.

---

## Why I Created This

I have an Android 12 TV Box that loses its system time after every power outage because it does not have a battery-backed RTC.

Normally Android synchronizes with public NTP servers (such as Google's), but due to network restrictions they were unreachable from my network.

Changing the Android NTP server to a computer on my local network completely solved the problem.

---

## Features

- Pure Python (standard library only)
- No external dependencies
- Single-file application
- Works on Windows and Linux
- Supports NTP v3 and v4 clients
- Configurable host and port
- Configurable time offset (hours and minutes)
- Optional verbose logging
- Logs incoming client requests
- Graceful shutdown (Ctrl+C)
- Version information (`--version`)

---

## Requirements

- Python 3.8+
- UDP port 123 available
- Firewall allowing inbound UDP port 123

---

## Running

Default:

```bash
python ntp_server.py
```

Verbose logging:

```bash
python ntp_server.py --verbose
```

Custom port:

```bash
python ntp_server.py --port 9123
```

Custom bind address:

```bash
python ntp_server.py --host 192.168.1.5
```

Offset by one hour:

```bash
python ntp_server.py --offset-hours -1
```

Offset by 30 minutes:

```bash
python ntp_server.py --offset-minutes 30
```

Combine offsets:

```bash
python ntp_server.py --offset-hours -1 --offset-minutes 15
```

Display version:

```bash
python ntp_server.py --version
```

---

## Example Output

```
[2026-08-06 19:30:04] Android Local NTP v1.1.0
[2026-08-06 19:30:04] Listening on 0.0.0.0:123
[2026-08-06 19:30:04] Effective time offset: +0 minute(s)

[2026-08-06 19:30:15] Request from 192.168.1.108:40739 (NTPv3, mode=3)
[2026-08-06 19:30:15] Response sent to 192.168.1.108
```

---

## Configuring Android

Using ADB:

```bash
adb shell settings put global ntp_server 192.168.1.5
adb shell settings put global auto_time 1
```

Replace `192.168.1.5` with the IP address of the computer running this server.

Verify:

```bash
adb shell settings get global ntp_server
```

---

## How It Works

Android sends a standard NTP request (UDP port 123).

```
Android Box
      │
      │ UDP 123
      ▼
Android Local NTP
      │
      ▼
Host Computer System Clock
```

The server:

1. Receives the 48-byte NTP packet.
2. Copies the client's transmit timestamp.
3. Generates the required NTP timestamps.
4. Applies the configured time offset (if any).
5. Sends a valid NTP response.
6. Android updates its clock.

---

## Verifying Synchronization

On Android:

```bash
adb shell dumpsys network_time_update_service
```

Successful synchronization looks similar to:

```
NTP cache result:
TimeResult{...}
```

If it shows

```
NTP cache result: null
```

Android has not successfully synchronized yet.

---

## Troubleshooting

### No requests appear in the server

Check:

```bash
adb shell settings get global ntp_server
```

Verify that:

- Android is using the correct NTP server.
- UDP port 123 is allowed through the firewall.
- The Android device and computer are on the same network.

---

### Android sends requests but time does not update

Verify that the computer's system clock is correct.

The server always returns the host computer's current time.

---

### Android does not retry after the computer starts

On the tested Android 12 TV Box, the observed behavior was:

- Retry approximately every minute for a few attempts.
- If all retries fail, retry roughly once every 24 hours.

This behavior may vary depending on the Android version and manufacturer.

A simple workaround is toggling Automatic Date & Time:

```bash
adb shell settings put global auto_time 0
adb shell settings put global auto_time 1
```

or manually turning **Automatic Date & Time** off and back on.

This immediately triggers a new NTP request.

---

### Incorrect displayed time

NTP only provides UTC.

The Android device applies its configured timezone.

Some Android TV boxes contain outdated timezone (tzdata) information, which may cause incorrect daylight saving time adjustments.

If needed, the server can temporarily compensate using:

```bash
python ntp_server.py --offset-hours -1
```

or

```bash
python ntp_server.py --offset-minutes -60
```

---

### Port 123 already in use

Windows:

```cmd
netstat -ano -p udp | find ":123"
```

Linux:

```bash
sudo ss -lunp | grep :123
```

Stop the conflicting application or use another port for testing.

> Android uses UDP port 123 for NTP.

---

### Windows Firewall

Allow inbound UDP port 123.

Otherwise Android will send requests but never receive replies.

---

## Debugging

Wireshark display filter:

```
udp.port == 123
```

A successful request should look like:

```
Source:
192.168.x.x

Destination:
Your PC

UDP Port:
123

Protocol:
NTP
```

---

## Known Limitations

This project is intentionally lightweight.

It is **not** intended to replace full NTP implementations such as:

- Chrony
- ntpd
- Windows Time Service

Missing features include:

- Clock discipline
- Drift correction
- Leap second handling
- Multiple upstream servers
- Authentication
- High-precision synchronization

For home networks and Android TV boxes that simply need the correct time after boot, these features are generally unnecessary.

---

## Tested On

### Server

- Windows 11
- Python 3.13

### Client

- Android 12 TV Box

---

## Roadmap

- [x] Basic NTP server
- [x] Android compatibility
- [x] Configurable host and port
- [x] Configurable time offset
- [x] Version information
- [ ] Optional log file output
- [ ] Standalone executable (PyInstaller)

---

## License

MIT License