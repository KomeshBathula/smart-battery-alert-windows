# Smart Battery Alert for Windows ⚡🔋

A lightweight, feature-rich battery management tool for Windows that protects your laptop's battery health.

## ✨ Features

### 🔋 Smart Low Battery Alerts
- Alerts when battery drops below 30%
- Notifications every 2% decrease
- Critical alerts at 20%

### ⚡ Charge Limit Alarm
- Set charge limits at 70%, 80%, or 90%
- Get alerted when battery reaches the limit
- Protect Li-ion battery health

### 📊 Battery Health Tracking
- Monitor battery capacity degradation
- Track charge cycle count
- Health warnings when capacity drops

### 🔊 Sound Alerts
- Customizable sounds for different events
- Volume control
- Enable/disable sounds

### 📈 Usage Statistics
- Track charging/discharging time
- Battery usage patterns
- Historical data logging

### ⚡ Charge Time Prediction
- Shows exact time when battery will be fully charged
- Clock-time format (e.g., "Charged by 12:15 PM")

## 📦 Installation

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

## 🔧 Configuration

Settings are stored in `config.json` and can be modified:
- Low battery threshold (default: 30%)
- Critical battery threshold (default: 20%)
- Charge limit (default: 80%)
- Alert intervals
- Sound settings

## 🏗️ Architecture

```
Smart Battery Alert (Windows)
  ├─ BatteryMonitor (Core engine)
  │   ├─ Battery state monitoring
  │   ├─ Low battery alerts
  │   ├─ Charge limit alerts
  │   ├─ Health tracking
  │   └─ Cycle counting
  ├─ System Tray Integration
  │   ├─ Battery percentage display
  │   ├─ Quick settings menu
  │   └─ Status notifications
  └─ Settings GUI
      ├─ Configure thresholds
      ├─ Sound preferences
      └─ View statistics
```

## 📄 License

GPL-3.0-or-later

## 👤 Author

**Komesh Bathula** — [@KomeshBathula](https://github.com/KomeshBathula)

---

> Built with ❤️ for Windows users. Because your battery deserves better.
