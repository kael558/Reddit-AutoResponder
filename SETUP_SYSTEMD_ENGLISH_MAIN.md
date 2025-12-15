# systemd Setup (Ubuntu / DigitalOcean) — `english_main.py` (venv)

This runs your bot as a **native system service** (no npm/PM2), with:

- Auto-start on boot
- Auto-restart on crash
- Stop retrying after repeated fast crashes (rate-limited restarts)

## 1) Confirm your venv Python path

From your project root:

```bash
cd /root/Reddit-AutoResponder
ls -la venv/bin/python3
```

If your project lives somewhere else, adjust paths below accordingly.

## 2) Create a systemd service file

```bash
sudo nano /etc/systemd/system/english-main.service
```

Paste this (adjust `User` + `WorkingDirectory` if needed):

```ini
[Unit]
Description=English Reddit Lead Monitor (english_main.py)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/Reddit-AutoResponder

# Use the venv interpreter so deps match your venv
ExecStart=/root/Reddit-AutoResponder/venv/bin/python3 -u english_main.py

Restart=on-failure
RestartSec=5

# "Pause if it keeps crashing":
# If it restarts too many times within the interval, systemd stops trying.
StartLimitIntervalSec=600
StartLimitBurst=10

KillSignal=SIGINT
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
```

## 3) Enable + start

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now english-main
sudo systemctl status english-main
```

## 4) Logs

```bash
journalctl -u english-main -f
```

## 5) If it hit the restart limit (StartLimit) after repeated crashes

After you fix the underlying issue:

```bash
sudo systemctl reset-failed english-main
sudo systemctl restart english-main
```
