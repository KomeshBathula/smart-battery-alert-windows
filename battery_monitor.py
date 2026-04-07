"""
Smart Battery Alert for Windows
Core battery monitoring engine - Feature parity with Linux GNOME extension
"""

import psutil
import time
import json
import os
from datetime import datetime, timedelta
from pathlib import Path


class BatteryMonitor:
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.config = self.load_config()
        
        # State tracking
        self.last_alerted_percent = self.config['low_battery_threshold']
        self.last_state = None
        self.last_percent = -1
        self.charge_limit_reached = False
        self.last_over_charge_alert_pct = -1
        self.charger_notified = False
        self.fully_charged_notified = False
        
        # Charge prediction (using exponential moving average like Linux version)
        self.charge_start_time = None
        self.charge_start_percent = None
        self.energy_rate_ema = 0
        self.ema_alpha = 0.3
        
        # Battery health tracking
        self.last_cycle_percentage = 100
        self.discharged_accumulator = 0
        
        # Session tracking for statistics
        self.session_start_time = time.time()
        self.charging_start_time = None
        self.discharging_start_time = None
        
    def load_config(self):
        """Load configuration with defaults"""
        default_config = {
            # Alert thresholds
            'low_battery_threshold': 30,
            'critical_battery_threshold': 20,
            'alert_interval': 2,
            'charge_limit': 80,
            
            # Enable/disable features
            'enable_low_battery_alarm': True,
            'enable_charge_limit_alarm': True,
            'enable_charge_prediction': True,
            'enable_sound_alerts': True,
            'enable_critical_dialog': True,  # Force overlay for critical battery
            'show_panel_percentage': True,
            
            # Sound settings
            'sound_volume': 50,
            
            # Health tracking
            'health_warning_threshold': 80,
            'charge_cycle_count': 0,
            'last_full_capacity': 0,
            'last_health_percent': 100,
            
            # Poll interval (seconds)
            'update_interval': 30,
            
            # Statistics
            'usage_stats': {
                'total_charging_time': 0,
                'total_discharging_time': 0,
                'sessions': []
            },
            'battery_health_log': {}
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    loaded = json.load(f)
                    default_config.update(loaded)
            except Exception as e:
                print(f"Error loading config: {e}")
        
        return default_config
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get_battery_info(self):
        """Get current battery information"""
        try:
            battery = psutil.sensors_battery()
            if battery is None:
                return None
            
            return {
                'percent': int(battery.percent),
                'power_plugged': battery.power_plugged,
                'seconds_left': battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else None
            }
        except Exception as e:
            print(f"Error getting battery info: {e}")
            return None
    
    def check_low_battery(self, percent, power_plugged):
        """Check and alert for low battery"""
        if power_plugged or not self.config['enable_low_battery_alarm']:
            return None
        
        low_threshold = self.config['low_battery_threshold']
        critical_threshold = self.config['critical_battery_threshold']
        interval = self.config['alert_interval']
        
        # Low battery alerts (between low and critical threshold)
        if percent <= low_threshold and percent > critical_threshold:
            if percent <= self.last_alerted_percent - interval:
                self.last_alerted_percent = percent
                return {
                    'type': 'low_battery',
                    'title': '🔋 Low Battery',
                    'message': f'Battery is at {percent}%. Connect your charger.'
                }
        
        # Critical battery - triggers persistent dialog
        if percent <= critical_threshold:
            if percent <= self.last_alerted_percent - interval:
                self.last_alerted_percent = percent
                return {
                    'type': 'critical_battery',
                    'title': '🚨 Critical Battery!',
                    'message': f'Battery at {percent}%! Connect charger NOW!',
                    'show_dialog': self.config.get('enable_critical_dialog', True)
                }
        
        return None
    
    def check_charge_limit(self, percent, power_plugged):
        """Check if charge limit is reached"""
        if not power_plugged or not self.config['enable_charge_limit_alarm']:
            self.charge_limit_reached = False
            self.last_over_charge_alert_pct = -1
            return None
        
        limit = self.config['charge_limit']
        
        # Charge limit reached (first time)
        if percent >= limit and not self.charge_limit_reached:
            self.charge_limit_reached = True
            self.last_over_charge_alert_pct = percent
            return {
                'type': 'charge_limit',
                'title': '🔋 Charge Limit Reached',
                'message': f'Battery is at {percent}%. You set a limit of {limit}%.\nPlease unplug the charger to protect battery health.',
                'show_dialog': True
            }
        
        # Over-charge alerts: every 1% beyond limit (like Linux version)
        if self.charge_limit_reached and percent > limit:
            if percent != self.last_over_charge_alert_pct:
                self.last_over_charge_alert_pct = percent
                return {
                    'type': 'over_charge',
                    'title': '⚠️ Over-Charging!',
                    'message': f'Battery is at {percent}% — {percent - limit}% beyond your {limit}% limit.\nRemove the charger now!'
                }
        
        return None
    
    def check_fully_charged(self, percent, power_plugged):
        """Check if battery is fully charged"""
        if not power_plugged:
            self.fully_charged_notified = False
            return None
        
        if percent >= 100 and not self.fully_charged_notified:
            self.fully_charged_notified = True
            return {
                'type': 'fully_charged',
                'title': '✅ Battery Fully Charged',
                'message': 'Your battery is at 100%. You can unplug the charger.'
            }
        
        return None
    
    def check_charger_connected(self, percent, power_plugged, state_changed):
        """Check if charger was just connected and notify with ETA"""
        if not power_plugged or not state_changed:
            return None
        
        if not self.config['enable_charge_prediction']:
            return None
        
        # Reset notification flag when charger is connected
        self.charger_notified = False
        
        # We'll return the charger connected alert after a delay
        # to get a stable ETA reading (handled in main.py)
        return {
            'type': 'charger_connected',
            'title': '⚡ Charger Connected',
            'message': f'Charging started at {percent}%.',
            'delay_for_eta': True  # Signal to delay notification
        }
    
    def get_charger_connected_alert(self, percent):
        """Get charger connected alert with ETA (called after delay)"""
        if self.charger_notified:
            return None
        
        eta = self.get_charge_eta(percent, True)
        self.charger_notified = True
        
        if eta:
            return {
                'type': 'charger_connected',
                'title': '⚡ Charger Connected',
                'message': f'Your laptop will be charged by {eta}.\n📱 Set a phone alarm for {eta} if you plan to shut down.'
            }
        else:
            return {
                'type': 'charger_connected',
                'title': '⚡ Charger Connected',
                'message': f'Charging started at {percent}%. Calculating time to full...'
            }
    
    def predict_charge_time(self, percent, power_plugged):
        """Predict when battery will be fully charged (or reach charge limit)"""
        if not power_plugged or not self.config['enable_charge_prediction']:
            return None
        
        # Start tracking when plugged in
        if self.charge_start_time is None:
            self.charge_start_time = time.time()
            self.charge_start_percent = percent
            self.energy_rate_ema = 0
        
        # Calculate elapsed time
        now = time.time()
        elapsed = now - self.charge_start_time
        
        if elapsed > 60:  # After 1 minute of charging
            # Calculate charge rate (% per second)
            percent_gained = percent - self.charge_start_percent
            if percent_gained > 0:
                current_rate = percent_gained / elapsed
                
                # Update exponential moving average
                if self.energy_rate_ema <= 0:
                    self.energy_rate_ema = current_rate
                else:
                    self.energy_rate_ema = (self.ema_alpha * current_rate + 
                                            (1 - self.ema_alpha) * self.energy_rate_ema)
                
                # Use charge limit as target (like Linux version)
                limit = self.config['charge_limit']
                target_percent = min(limit, 100)
                
                if percent >= target_percent:
                    return None
                
                remaining_percent = target_percent - percent
                
                if self.energy_rate_ema > 0:
                    seconds_to_target = remaining_percent / self.energy_rate_ema
                    
                    # Sanity cap: > 12 hours likely means bad data
                    if seconds_to_target > 12 * 3600 or seconds_to_target < 0:
                        return None
                    
                    # Format as clock time
                    eta = datetime.now() + timedelta(seconds=seconds_to_target)
                    return eta.strftime("%I:%M %p")
        
        return None
    
    def monitor_once(self):
        """Single monitoring check - returns list of alerts if needed"""
        info = self.get_battery_info()
        if not info:
            return []
        
        percent = info['percent']
        power_plugged = info['power_plugged']
        
        alerts = []
        
        # State change detection
        state_changed = (power_plugged != self.last_state)
        
        if state_changed and self.last_state is not None:
            if power_plugged:
                # Just plugged in
                self.last_alerted_percent = self.config['low_battery_threshold']
                self.charge_start_time = time.time()
                self.charge_start_percent = percent
                self.energy_rate_ema = 0
                self.charge_limit_reached = False
                self.last_over_charge_alert_pct = -1
                self.charger_notified = False
                self.fully_charged_notified = False
                
                # Track usage stats
                if self.discharging_start_time:
                    duration = time.time() - self.discharging_start_time
                    self.config['usage_stats']['total_discharging_time'] += duration
                    self.discharging_start_time = None
                self.charging_start_time = time.time()
                
            else:
                # Just unplugged
                self.charge_start_time = None
                self.charge_start_percent = None
                self.charge_limit_reached = False
                self.last_over_charge_alert_pct = -1
                self.charger_notified = False
                
                # Track usage stats
                if self.charging_start_time:
                    duration = time.time() - self.charging_start_time
                    self.config['usage_stats']['total_charging_time'] += duration
                    self.charging_start_time = None
                self.discharging_start_time = time.time()
        
        self.last_state = power_plugged
        self.last_percent = percent
        
        # Track charge cycles
        self.track_charge_cycles(percent, power_plugged)
        
        # Check for charger connected (with ETA)
        if state_changed and power_plugged:
            alert = self.check_charger_connected(percent, power_plugged, state_changed)
            if alert:
                alerts.append(alert)
        
        # Check for low/critical battery
        alert = self.check_low_battery(percent, power_plugged)
        if alert:
            alerts.append(alert)
        
        # Check for charge limit
        alert = self.check_charge_limit(percent, power_plugged)
        if alert:
            alerts.append(alert)
        
        # Check for fully charged
        alert = self.check_fully_charged(percent, power_plugged)
        if alert:
            alerts.append(alert)
        
        return alerts
    
    def get_charge_eta(self, percent, power_plugged):
        """Get estimated time for full charge"""
        return self.predict_charge_time(percent, power_plugged)
    
    def get_shutdown_tip(self, percent, power_plugged):
        """Get shutdown tip message (like Linux version)"""
        if not power_plugged:
            return None
        
        eta = self.get_charge_eta(percent, power_plugged)
        if eta:
            return f"📱 Shutting down? Set a phone alarm for {eta}, then shutdown safely."
        return None
    
    def get_battery_health(self):
        """Get battery health percentage using WMI on Windows"""
        try:
            import subprocess
            
            # Try PowerShell command to get battery info
            result = subprocess.run(
                ['powershell', '-Command', 
                 '(Get-WmiObject -Class Win32_Battery).EstimatedChargeRemaining'],
                capture_output=True, text=True, timeout=5
            )
            
            # For actual health, we'd need design vs full capacity
            # This is a placeholder - actual implementation needs battery report
            return self.config.get('last_health_percent', 100)
        except:
            return self.config.get('last_health_percent', 100)
    
    def track_charge_cycles(self, percent, power_plugged):
        """Track battery charge cycles"""
        if not power_plugged:
            # Track discharge
            drop = self.last_cycle_percentage - percent
            if drop > 0:
                self.discharged_accumulator += drop
                
                # One full cycle = 100% discharged
                while self.discharged_accumulator >= 100:
                    self.config['charge_cycle_count'] += 1
                    self.discharged_accumulator -= 100
                    self.save_config()
            
            self.last_cycle_percentage = percent
        elif percent == 100:
            # Reset on full charge
            self.last_cycle_percentage = 100
        else:
            # Update on charging
            self.last_cycle_percentage = percent
    
    def check_battery_health(self):
        """Check if battery health needs warning"""
        health = self.get_battery_health()
        if health and health < self.config['health_warning_threshold']:
            return {
                'type': 'health_warning',
                'title': '⚠️ Battery Health Warning',
                'message': f'Battery capacity is at {health}%. Consider battery replacement.'
            }
        return None
    
    def set_charge_limit(self, limit):
        """Set the charge limit (quick-set function)"""
        self.config['charge_limit'] = limit
        self.charge_limit_reached = False
        self.last_over_charge_alert_pct = -1
        self.save_config()
    
    def get_status_text(self):
        """Get formatted status text for display"""
        info = self.get_battery_info()
        if not info:
            return "No battery detected"
        
        percent = info['percent']
        plugged = info['power_plugged']
        
        if plugged:
            eta = self.get_charge_eta(percent, plugged)
            if eta:
                return f"{percent}% ⚡ → {eta}"
            else:
                return f"{percent}% ⚡ Charging"
        else:
            return f"{percent}% 🔋 On battery"


if __name__ == "__main__":
    # Test the monitor
    monitor = BatteryMonitor()
    
    print("Battery Monitor Test")
    print("=" * 50)
    
    for i in range(5):
        info = monitor.get_battery_info()
        if info:
            print(f"Battery: {info['percent']}% | Plugged: {info['power_plugged']}")
            
            # Check for alerts
            alerts = monitor.monitor_once()
            for alert in alerts:
                print(f"ALERT: {alert['title']} - {alert['message']}")
            
            # Show charge prediction
            if info['power_plugged']:
                eta = monitor.get_charge_eta(info['percent'], info['power_plugged'])
                if eta:
                    print(f"Charged by: {eta}")
                
                tip = monitor.get_shutdown_tip(info['percent'], info['power_plugged'])
                if tip:
                    print(tip)
        else:
            print("No battery detected")
        
        time.sleep(2)
