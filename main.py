"""
Smart Battery Alert for Windows
Main Application - Entry point that ties all components together
Feature parity with Linux GNOME extension
"""

import sys
import time
import threading
import signal

# Import components
from battery_monitor import BatteryMonitor
from sound_manager import SoundManager
from system_tray import SystemTray
from usage_stats import UsageStats
from settings_gui import SettingsGUI
from critical_dialog import CriticalBatteryDialog, ChargeLimitDialog

# Try to import notification library
try:
    from plyer import notification
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False
    print("Warning: plyer not available. Desktop notifications disabled.")


class SmartBatteryAlert:
    """Main application class that coordinates all components"""
    
    def __init__(self):
        # Initialize components
        self.monitor = BatteryMonitor()
        self.sound = SoundManager(volume=self.monitor.config.get('sound_volume', 50))
        self.stats = UsageStats()
        self.tray = None
        self.settings_gui = None
        
        # Critical dialog management
        self.critical_dialog = None
        self.charge_limit_dialog = None
        
        # Application state
        self._running = False
        self._monitor_thread = None
        self._check_interval = self.monitor.config.get('update_interval', 30)
        
        # Track state changes for sessions
        self._last_plugged = None
        self._session_start_percent = None
        self._session_start_time = None
        
        # Charger notification delay
        self._charger_notify_timer = None
        self._charger_notify_delay = 5  # seconds to wait for stable ETA
    
    def start(self):
        """Start the application"""
        print("Starting Smart Battery Alert for Windows...")
        print("=" * 50)
        
        # Show initial battery status
        info = self.monitor.get_battery_info()
        if info:
            print(f"Battery: {info['percent']}%")
            print(f"Status: {'Charging' if info['power_plugged'] else 'On battery'}")
            print(f"Charge cycles: {self.monitor.config.get('charge_cycle_count', 0)}")
        else:
            print("Warning: No battery detected!")
        
        print()
        print("Settings:")
        print(f"  Low battery threshold: {self.monitor.config['low_battery_threshold']}%")
        print(f"  Critical threshold: {self.monitor.config['critical_battery_threshold']}%")
        print(f"  Charge limit: {self.monitor.config['charge_limit']}%")
        print(f"  Update interval: {self._check_interval}s")
        print()
        
        self._running = True
        
        # Start system tray
        self._start_tray()
        
        # Start monitoring thread
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        
        print("Smart Battery Alert is running in the system tray.")
        print("Right-click the tray icon for options.")
        print("Press Ctrl+C to quit.")
        print()
        
        # Keep main thread alive
        try:
            while self._running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
            self.stop()
    
    def _start_tray(self):
        """Start the system tray icon"""
        self.tray = SystemTray(
            monitor=self.monitor,
            sound_manager=self.sound,
            on_settings=self._show_settings,
            on_quit=self.stop
        )
        
        if not self.tray.start():
            print("Warning: System tray not available. Running in background mode.")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self._running:
            try:
                self._check_battery()
                time.sleep(self._check_interval)
            except Exception as e:
                print(f"Monitor error: {e}")
                time.sleep(5)
    
    def _check_battery(self):
        """Perform battery check and handle alerts"""
        info = self.monitor.get_battery_info()
        if not info:
            return
        
        percent = info['percent']
        plugged = info['power_plugged']
        
        # Record stats
        self.stats.record_sample(percent, plugged)
        
        # Track charge/discharge sessions
        self._track_session(percent, plugged)
        
        # Check for alerts
        alerts = self.monitor.monitor_once()
        for alert in alerts:
            self._handle_alert(alert, percent, plugged)
        
        # Auto-dismiss critical dialog when charger is connected
        if self.critical_dialog and self.critical_dialog.is_open and plugged:
            self.critical_dialog.close()
            self.critical_dialog = None
        
        # Update tray icon
        if self.tray:
            self.tray.update_icon()
    
    def _track_session(self, percent, plugged):
        """Track charge/discharge sessions for statistics"""
        # Detect state change
        if self._last_plugged is not None and plugged != self._last_plugged:
            # State changed - end previous session
            if self._session_start_time:
                duration = (time.time() - self._session_start_time) / 60  # minutes
                
                if self._last_plugged:
                    # Was charging, now discharging
                    self.stats.record_charge_session(
                        self._session_start_percent,
                        percent,
                        duration
                    )
                else:
                    # Was discharging, now charging
                    self.stats.record_discharge_session(
                        self._session_start_percent,
                        percent,
                        duration
                    )
            
            # Start new session
            self._session_start_percent = percent
            self._session_start_time = time.time()
        
        # Initialize if first run
        if self._last_plugged is None:
            self._session_start_percent = percent
            self._session_start_time = time.time()
        
        self._last_plugged = plugged
    
    def _handle_alert(self, alert, percent, plugged):
        """Handle an alert (notification, sound, and dialogs)"""
        alert_type = alert.get('type', 'default')
        title = alert.get('title', 'Battery Alert')
        message = alert.get('message', '')
        show_dialog = alert.get('show_dialog', False)
        delay_for_eta = alert.get('delay_for_eta', False)
        
        # Handle charger connected notification with delay for stable ETA
        if delay_for_eta:
            self._schedule_charger_notification(percent)
            return
        
        print(f"\n[ALERT] {title}")
        print(f"        {message}\n")
        
        # Show desktop notification
        self._show_notification(title, message)
        
        # Play sound if enabled
        if self.monitor.config.get('enable_sound_alerts', True):
            self.sound.play_alert(alert_type)
        
        # Show critical battery dialog (cannot be closed until charger is connected)
        if alert_type == 'critical_battery' and show_dialog:
            self._show_critical_dialog()
        
        # Show charge limit dialog
        if alert_type == 'charge_limit' and show_dialog:
            self._show_charge_limit_dialog(percent, self.monitor.config['charge_limit'])
    
    def _schedule_charger_notification(self, percent):
        """Schedule charger notification after delay to get stable ETA"""
        def delayed_notify():
            time.sleep(self._charger_notify_delay)
            if not self._running:
                return
            
            # Get the alert with ETA
            alert = self.monitor.get_charger_connected_alert(percent)
            if alert:
                self._show_notification(alert['title'], alert['message'])
                if self.monitor.config.get('enable_sound_alerts', True):
                    self.sound.play_alert('charger_connected')
                print(f"\n[ALERT] {alert['title']}")
                print(f"        {alert['message']}\n")
        
        # Cancel any existing timer
        if self._charger_notify_timer:
            # Can't cancel thread, but it will check _running
            pass
        
        # Start new timer
        self._charger_notify_timer = threading.Thread(target=delayed_notify, daemon=True)
        self._charger_notify_timer.start()
    
    def _show_notification(self, title, message):
        """Show a desktop notification"""
        if not NOTIFICATIONS_AVAILABLE:
            return
        
        try:
            notification.notify(
                title=title,
                message=message,
                app_name="Smart Battery Alert",
                timeout=10
            )
        except Exception as e:
            print(f"Notification error: {e}")
    
    def _show_critical_dialog(self):
        """Show the critical battery dialog (modal, cannot be closed easily)"""
        if self.critical_dialog and self.critical_dialog.is_open:
            return
        
        def get_state():
            info = self.monitor.get_battery_info()
            if info:
                return (info['percent'], info['power_plugged'])
            return (0, False)
        
        def on_dismissed():
            print("Critical battery dialog dismissed - charger connected.")
            self.critical_dialog = None
        
        # Show dialog in a separate thread
        def show_dialog():
            self.critical_dialog = CriticalBatteryDialog(get_state, on_dismissed)
            self.critical_dialog.show()
        
        dialog_thread = threading.Thread(target=show_dialog, daemon=True)
        dialog_thread.start()
    
    def _show_charge_limit_dialog(self, percent, limit):
        """Show the charge limit dialog"""
        if self.charge_limit_dialog:
            return
        
        def on_dismissed():
            self.charge_limit_dialog = None
        
        # Show dialog in a separate thread
        def show_dialog():
            self.charge_limit_dialog = ChargeLimitDialog(percent, limit, on_dismissed)
            self.charge_limit_dialog.show()
        
        dialog_thread = threading.Thread(target=show_dialog, daemon=True)
        dialog_thread.start()
    
    def _show_settings(self):
        """Show the settings window"""
        # Run settings in a separate thread to not block the tray
        def show_settings_thread():
            self.settings_gui = SettingsGUI(
                monitor=self.monitor,
                stats=self.stats,
                on_save=self._on_settings_saved
            )
            self.settings_gui.show()
        
        settings_thread = threading.Thread(target=show_settings_thread)
        settings_thread.start()
    
    def _on_settings_saved(self):
        """Called when settings are saved"""
        # Update sound volume
        self.sound.set_volume(self.monitor.config.get('sound_volume', 50))
        
        # Update check interval
        self._check_interval = self.monitor.config.get('update_interval', 30)
        
        # Update tray
        if self.tray:
            self.tray.update_icon()
        
        print("Settings updated.")
    
    def stop(self):
        """Stop the application"""
        print("Stopping Smart Battery Alert...")
        
        self._running = False
        
        # Close any open dialogs
        if self.critical_dialog:
            try:
                self.critical_dialog.close()
            except:
                pass
        
        if self.charge_limit_dialog:
            try:
                self.charge_limit_dialog.close()
            except:
                pass
        
        # Stop tray
        if self.tray:
            self.tray.stop()
        
        # Save stats
        self.stats.save_stats()
        
        # Save config
        self.monitor.save_config()
        
        print("Goodbye!")
        sys.exit(0)


def main():
    """Main entry point"""
    print()
    print("  Smart Battery Alert for Windows")
    print("  ================================")
    print("  Feature parity with Linux GNOME Extension")
    print()
    
    # Check for battery
    import psutil
    battery = psutil.sensors_battery()
    if battery is None:
        print("Error: No battery detected on this system.")
        print("This application requires a laptop with a battery.")
        sys.exit(1)
    
    # Create and start application
    app = SmartBatteryAlert()
    
    # Handle signals
    def signal_handler(sig, frame):
        app.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start the application
    app.start()


if __name__ == "__main__":
    main()
