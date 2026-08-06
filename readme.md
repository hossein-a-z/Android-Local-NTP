# Simple Python NTP Server for Android TV / Android Box

A lightweight NTP (Network Time Protocol) server written in pure Python.

This project was created to solve a very specific problem:

- Android TV boxes without a battery-backed RTC (Real Time Clock)
- Frequent power outages
- Android configured to synchronize time from Internet NTP servers that are blocked or unreachable
- Need a simple local NTP server without installing Chrony, Docker, or other services

The server listens for NTP requests and replies with the current system time from the host computer.

---

# Why I Created This

I have a android 12 TV Box with frequent power outages and in every reboot resets the device clock. Automatic network time pointed to `time.google.com` and Google NTP servers were unreachable due to network restrictions. Changing the Android NTP server to a local computer solved the problem.

---

# Features

- Pure Python (standard library only)
- No external dependencies
- Single file
- Works on Windows and Linux
- Supports NTP v3 and v4 clients
- Configurable host and port
- Optional verbose logging
- Logs incoming requests
- Graceful shutdown (Ctrl+C)

---

# Requirements

- Python 3.8+
- UDP port 123 available
- Firewall allowing inbound UDP 123

---

# Running

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

---

# Example Output

```
[2026-08-06 18:54:09] NTP server listening on 0.0.0.0:123
[2026-08-06 18:54:19] Request from 192.168.1.5:40739 (NTPv3, mode=3)
[2026-08-06 18:54:19] Response sent to 192.168.1.108
```

---

# Configuring Android

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

# How It Works

Android sends a standard NTP request (UDP port 123).

```
Android Box
      │
      │ UDP 123
      ▼
Python NTP Server
      │
      ▼
Current System Time
```

The server:

1. Receives the 48-byte NTP packet.
2. Copies the client's transmit timestamp.
3. Generates the required NTP timestamps.
4. Sends a valid server response.
5. Android updates its clock.

---

# Verifying Synchronization

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

# Troubleshooting

## No requests appear in the server

Check:

- Android is using the correct NTP server

```
adb shell settings get global ntp_server
```

- The PC firewall allows UDP port 123.
- The computer and Android device are on the same network.

---

## Android sends requests but time does not update

Verify that the computer's clock is correct.

This server returns the host computer's current system time.

If the computer's time is incorrect, Android will synchronize to the incorrect time.

---

## Android does not retry after the computer starts

Android does not continuously poll for time.

On Android 12 the observed behavior was:

- Retry every minute for a few attempts
- Afterwards retry approximately every 24 hours

If the computer starts after those retries have already failed, Android may keep the incorrect time.

A simple workaround is toggling automatic time:

```bash
adb shell settings put global auto_time 0
adb shell settings put global auto_time 1
```
Or turing automatic date and time off and then on

This immediately triggers a new NTP request.

---

## Port 123 already in use

Check which application is using UDP port 123.

Windows:

```cmd
netstat -ano -p udp | find ":123"
```

Linux:

```bash
sudo ss -lunp | grep :123
```

Stop the conflicting service or choose another port (for testing only).

> Android NTP uses UDP port 123 by default.

---

## Windows Firewall

Allow inbound UDP port 123.

Otherwise Android will send requests but never receive a reply.

---

# Debugging

Wireshark filter:

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

# Known Limitations

This project is intentionally minimal.

It is **not** intended to replace full NTP implementations such as:

- Chrony
- ntpd
- Windows Time Service

Missing features include:

- Multiple upstream NTP servers
- Clock discipline
- Drift correction
- Leap second handling
- Authentication
- High-precision synchronization

For home networks or Android TV boxes that simply need the correct time after boot, this implementation is sufficient.

---

# Tested On

Server:

- Windows 11
- Python 3.x

Client:

- Android 12 TV Box

---

# License

MIT
