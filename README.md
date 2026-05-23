# PC Temperature Monitor

[![GitHub Pages](https://img.shields.io/badge/GitHub-Pages-blue?logo=github)](https://jlaiii.github.io/pc-temp-monitor/)

A lightweight, real-time CPU and GPU temperature monitor for Windows with a clean dark-themed GUI.

## Features

- **Real-time monitoring** — CPU and GPU temperatures update every 2 seconds
- **Live min/max tracking** — tracks lowest and highest temps during the session
- **Color-coded** — green (safe), yellow (warm), red (hot)
- **°C / °F toggle** — click the unit button to switch
- **Self-elevating** — automatically requests admin rights for accurate CPU temp (one UAC prompt)
- **No dependencies to install** — auto-installs `psutil` and `pythonnet` via pip if missing
- **Dark theme** — easy on the eyes

## Requirements

- Windows 10 or later
- Python 3.8+
- NVIDIA GPU (for GPU temperature via nvidia-smi)
- Internet connection (first run only — auto-installs dependencies)

## Quick Start

Double-click `temp_monitor.py` and accept the UAC prompt for accurate CPU temperature readings.

```
python temp_monitor.py
```

## How It Works

| Component | Method | Source |
|-----------|--------|--------|
| CPU temp | LibreHardwareMonitor (LHM) via .NET interop | Direct hardware access (admin required) |
| CPU temp (fallback) | WMI thermal zone | Chassis/ambient sensor |
| GPU temp | nvidia-smi | NVIDIA driver |
| CPU/RAM usage | psutil | Windows API |

## Manual Installation

If auto-install fails, run:

```bash
pip install psutil pythonnet
```

## License

MIT
