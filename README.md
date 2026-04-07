# Smart Battery Alert for Windows

A lightweight, feature-rich battery management tool for Windows with **complete feature parity** with the Linux GNOME Shell Extension.

## Features

### Low Battery Alerts
- Customizable low battery threshold (default: 30%)
- Critical battery threshold with persistent dialog (default: 20%)
- Alerts every N% decrease (configurable interval)
- **Critical battery dialog that blocks the screen until charger is connected**

### Charge Limit Alarm
- Set charge limits at 70%, 80%, 90%, or custom
- Get alerted when battery reaches the limit
- **Over-charge alerts every 1% beyond your limit**
- Protect Li-ion battery health

### Charge Time Prediction
- Shows exact time when battery will reach charge limit
- Clock-time format (e.g., "Charged by 12:15 PM")
- **Charger connected notification with ETA**
- Shutdown tip: Set a phone alarm for the predicted time

### Battery Health Tracking
- Monitor battery capacity degradation
- Track charge cycle count (cumulative discharge)
- Health warnings when capacity drops below threshold
- Historical data logging

### Sound Alerts
- System sounds for different events
- Volume control (0-100%)
- Enable/disable per alert type

### Usage Statistics
- Track charging/discharging sessions
- Battery usage patterns
- Weekly summaries
- Data cleanup for old entries

### System Tray Integration
- Live battery icon with percentage
- Dynamic icon color based on charge level
- Charging indicator (lightning bolt)
- **Quick-set charge limit buttons (70%, 80%, 90%)**
- Shutdown tip when charging
- Right-click menu with all options

### Settings GUI
- Tabbed interface (General, Low Battery, Charge Limit, Health, Statistics, About)
- All settings configurable via GUI
- Reset to defaults option

## Installation

### Requirements
- Windows 10/11
- Python 3.8 or higher

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run the Application
```bash
python main.py
```

## Configuration

Settings are stored in `config.json` and can be modified via the Settings GUI:

| Setting | Default | Description |
|---------|---------|-------------|
| Low battery threshold | 30% | Start alerting below this |
| Critical battery threshold | 20% | Show persistent dialog |
| Alert interval | 2% | Notify every N% decrease |
| Charge limit | 80% | Alert when reached |
| Update interval | 30s | Time between checks |
| Sound alerts | Enabled | Play system sounds |
| Critical dialog | Enabled | Block screen on critical |

## Feature Parity with Linux Version

This Windows version has **complete feature parity** with the Linux GNOME Shell Extension:

| Feature | Linux | Windows |
|---------|-------|---------|
| Low battery alerts | ✅ | ✅ |
| Critical battery modal dialog | ✅ | ✅ |
| Charge limit notifications | ✅ | ✅ |
| Over-charge alerts (every 1%) | ✅ | ✅ |
| Charger connected notification | ✅ | ✅ |
| Fully charged notification | ✅ | ✅ |
| Charge time prediction (ETA) | ✅ | ✅ |
| Shutdown tip | ✅ | ✅ |
| Battery health tracking | ✅ | ✅ |
| Charge cycle counting | ✅ | ✅ |
| Sound alerts | ✅ | ✅ |
| Quick-set charge limits | ✅ | ✅ |
| System tray / Panel indicator | ✅ | ✅ |
| Settings GUI / Preferences | ✅ | ✅ |
| Usage statistics | ✅ | ✅ |

## Architecture

```
Smart Battery Alert (Windows)
├── main.py                 # Entry point, coordinates all components
├── battery_monitor.py      # Core monitoring engine
│   ├── Battery state monitoring
│   ├── Low/critical battery alerts
│   ├── Charge limit & over-charge alerts
│   ├── Charger connected notification
│   ├── Charge time prediction (EMA)
│   ├── Health tracking & cycle counting
│   └── Shutdown tip generation
├── critical_dialog.py      # Modal dialogs
│   ├── CriticalBatteryDialog (cannot close until charger connected)
│   └── ChargeLimitDialog
├── system_tray.py          # System tray integration
│   ├── Dynamic battery icon
│   ├── Quick-set charge limit menu
│   └── Status display
├── sound_manager.py        # Sound alerts
├── usage_stats.py          # Usage statistics tracking
├── settings_gui.py         # Tkinter settings window
├── config.json             # Configuration (auto-generated)
└── battery_stats.json      # Statistics data (auto-generated)
```

## License

GPL-3.0-or-later

## Author

**Komesh Bathula** — [@KomeshBathula](https://github.com/KomeshBathula)

---

> Built with Python for Windows users. Feature parity with the Linux GNOME Extension.
> Because your battery deserves the same protection on every platform.
