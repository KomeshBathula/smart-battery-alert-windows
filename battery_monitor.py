"""
Smart Battery Alert for Windows
Core battery monitoring engine
"""

import psutil
import time
import json
import os
from datetime import datetime
from pathlib import Path


class BatteryMonitor:
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.config = self.load_config()
        
        # State tracking
        self.last_alerted_percent = self.config['low_battery_threshold']
        self.last_state = None
        self.last_percent = -1
        
    def load_config(self):
        """Load configuration with defaults"""
        default_config = {
            'low_battery_threshold': 30,
            'critical_battery_threshold': 20,
            'alert_interval': 2,
            'charge_limit': 80,
            'enable_low_battery_alarm': True,
            'enable_charge_limit_alarm': True,
            'enable_charge_prediction': True,
            'enable_sound_alerts': True,
            'sound_volume': 50,
            'health_warning_threshold': 80,
            'charge_cycle_count': 0,
            'last_full_capacity': 0,
            'usage_stats': {},
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
        
        # Low battery alerts
        if percent <= low_threshold and percent > critical_threshold:
            if percent <= self.last_alerted_percent - interval:
                self.last_alerted_percent = percent
                return {
                    'type': 'low_battery',
                    'title': '🔋 Low Battery',
                    'message': f'Battery is at {percent}%. Connect your charger.'
                }
        
        # Critical battery
        if percent <= critical_threshold:
            if percent <= self.last_alerted_percent - interval:
                self.last_alerted_percent = percent
                return {
                    'type': 'critical_battery',
                    'title': '🚨 Critical Battery!',
                    'message': f'Battery at {percent}%! Connect charger NOW!'
                }
        
        return None
    
    def check_charge_limit(self, percent, power_plugged):
        """Check if charge limit is reached"""
        if not power_plugged or not self.config['enable_charge_limit_alarm']:
            return None
        
        limit = self.config['charge_limit']
        
        if percent >= limit:
            return {
                'type': 'charge_limit',
                'title': '🔋 Charge Limit Reached',
                'message': f'Battery is at {percent}%. You set a limit of {limit}%.\nPlease unplug the charger to protect battery health.'
            }
        
        return None
    
    def monitor_once(self):
        """Single monitoring check - returns alert if needed"""
        info = self.get_battery_info()
        if not info:
            return None
        
        percent = info['percent']
        power_plugged = info['power_plugged']
        
        # State change detection
        state_changed = (power_plugged != self.last_state)
        
        if state_changed and self.last_state is not None:
            if power_plugged:
                # Just plugged in
                self.last_alerted_percent = self.config['low_battery_threshold']
            else:
                # Just unplugged
                pass
        
        self.last_state = power_plugged
        self.last_percent = percent
        
        # Check for alerts
        alert = self.check_low_battery(percent, power_plugged)
        if alert:
            return alert
        
        alert = self.check_charge_limit(percent, power_plugged)
        if alert:
            return alert
        
        return None


if __name__ == "__main__":
    # Test the monitor
    monitor = BatteryMonitor()
    
    print("Battery Monitor Test")
    print("=" * 50)
    
    for i in range(5):
        info = monitor.get_battery_info()
        if info:
            print(f"Battery: {info['percent']}% | Plugged: {info['power_plugged']}")
            alert = monitor.monitor_once()
            if alert:
                print(f"ALERT: {alert['title']} - {alert['message']}")
        else:
            print("No battery detected")
        
        time.sleep(2)
