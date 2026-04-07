"""
Smart Battery Alert for Windows
Settings GUI - Tkinter-based settings window
Feature parity with Linux GNOME extension prefs.js
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json


class SettingsGUI:
    """Settings window for Smart Battery Alert"""
    
    def __init__(self, monitor, stats=None, on_save=None):
        """
        Initialize settings GUI
        
        Args:
            monitor: BatteryMonitor instance
            stats: UsageStats instance (optional)
            on_save: Callback when settings are saved
        """
        self.monitor = monitor
        self.stats = stats
        self.on_save_callback = on_save
        
        self.window = None
        self.is_open = False
        
        # Tkinter variables (created when window opens)
        self.vars = {}
    
    def show(self):
        """Show the settings window"""
        if self.is_open:
            if self.window:
                self.window.focus_force()
            return
        
        self.is_open = True
        self._create_window()
    
    def _create_window(self):
        """Create the settings window"""
        self.window = tk.Tk()
        self.window.title("Smart Battery Alert - Settings")
        self.window.geometry("550x700")
        self.window.resizable(True, True)
        
        # Set icon if available
        try:
            self.window.iconbitmap("battery.ico")
        except:
            pass
        
        # Create notebook for tabs
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        general_tab = ttk.Frame(notebook)
        alerts_tab = ttk.Frame(notebook)
        charge_tab = ttk.Frame(notebook)
        health_tab = ttk.Frame(notebook)
        stats_tab = ttk.Frame(notebook)
        about_tab = ttk.Frame(notebook)
        
        notebook.add(general_tab, text='General')
        notebook.add(alerts_tab, text='Low Battery')
        notebook.add(charge_tab, text='Charge Limit')
        notebook.add(health_tab, text='Health')
        notebook.add(stats_tab, text='Statistics')
        notebook.add(about_tab, text='About')
        
        # Build tabs
        self._build_general_tab(general_tab)
        self._build_alerts_tab(alerts_tab)
        self._build_charge_tab(charge_tab)
        self._build_health_tab(health_tab)
        self._build_stats_tab(stats_tab)
        self._build_about_tab(about_tab)
        
        # Buttons at bottom
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(button_frame, text="Save", command=self._save_settings).pack(side='right', padx=5)
        ttk.Button(button_frame, text="Cancel", command=self._close).pack(side='right', padx=5)
        ttk.Button(button_frame, text="Reset to Defaults", command=self._reset_defaults).pack(side='left', padx=5)
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self._close)
        
        # Start main loop
        self.window.mainloop()
    
    def _build_general_tab(self, parent):
        """Build the general settings tab"""
        # Display Settings
        display_frame = ttk.LabelFrame(parent, text="Display", padding=10)
        display_frame.pack(fill='x', padx=10, pady=5)
        
        # Show panel percentage
        self.vars['show_percentage'] = tk.BooleanVar(value=self.monitor.config.get('show_panel_percentage', True))
        ttk.Checkbutton(
            display_frame, 
            text="Show battery percentage in system tray tooltip",
            variable=self.vars['show_percentage']
        ).pack(anchor='w')
        
        # Run at Startup
        self.vars['run_at_startup'] = tk.BooleanVar(value=self._check_startup_status())
        ttk.Checkbutton(
            display_frame, 
            text="Run Smart Battery Alert at Windows startup",
            variable=self.vars['run_at_startup']
        ).pack(anchor='w', pady=(5, 0))
        
        # Update interval
        interval_frame = ttk.Frame(display_frame)
        interval_frame.pack(fill='x', pady=10)
        ttk.Label(interval_frame, text="Update interval (seconds):").pack(side='left')
        self.vars['update_interval'] = tk.IntVar(value=self.monitor.config.get('update_interval', 30))
        interval_spin = ttk.Spinbox(
            interval_frame, 
            from_=10, to=120,
            textvariable=self.vars['update_interval'],
            width=5
        )
        interval_spin.pack(side='left', padx=10)
        ttk.Label(interval_frame, text="(10-120)").pack(side='left')
        
        # Charge Prediction
        prediction_frame = ttk.LabelFrame(parent, text="Charge Prediction", padding=10)
        prediction_frame.pack(fill='x', padx=10, pady=5)
        
        self.vars['enable_prediction'] = tk.BooleanVar(value=self.monitor.config.get('enable_charge_prediction', True))
        ttk.Checkbutton(
            prediction_frame, 
            text="Enable charge time prediction",
            variable=self.vars['enable_prediction']
        ).pack(anchor='w')
        
        ttk.Label(
            prediction_frame,
            text="Shows estimated time when battery will be fully charged.\n"
                 "Tip: Set a phone alarm for that time, then shut down safely.",
            foreground='gray'
        ).pack(anchor='w', pady=(5, 0))
        
        # Sound Settings
        sound_frame = ttk.LabelFrame(parent, text="Sound Alerts", padding=10)
        sound_frame.pack(fill='x', padx=10, pady=5)
        
        self.vars['enable_sound'] = tk.BooleanVar(value=self.monitor.config.get('enable_sound_alerts', True))
        ttk.Checkbutton(
            sound_frame, 
            text="Enable sound alerts",
            variable=self.vars['enable_sound']
        ).pack(anchor='w')
        
        volume_frame = ttk.Frame(sound_frame)
        volume_frame.pack(fill='x', pady=5)
        ttk.Label(volume_frame, text="Volume:").pack(side='left')
        self.vars['sound_volume'] = tk.IntVar(value=self.monitor.config.get('sound_volume', 50))
        ttk.Scale(
            volume_frame, 
            from_=0, to=100, 
            variable=self.vars['sound_volume'],
            orient='horizontal',
            length=200
        ).pack(side='left', padx=10)
        self.volume_label = ttk.Label(volume_frame, text=f"{self.vars['sound_volume'].get()}%")
        self.volume_label.pack(side='left')
        self.vars['sound_volume'].trace('w', lambda *args: self.volume_label.config(text=f"{int(self.vars['sound_volume'].get())}%"))
        
        # Critical Dialog
        dialog_frame = ttk.LabelFrame(parent, text="Critical Battery Dialog", padding=10)
        dialog_frame.pack(fill='x', padx=10, pady=5)
        
        self.vars['enable_critical_dialog'] = tk.BooleanVar(value=self.monitor.config.get('enable_critical_dialog', True))
        ttk.Checkbutton(
            dialog_frame, 
            text="Show persistent dialog for critical battery",
            variable=self.vars['enable_critical_dialog']
        ).pack(anchor='w')
        
        ttk.Label(
            dialog_frame,
            text="When enabled, a dialog that cannot be easily closed\n"
                 "will appear when battery reaches critical level.",
            foreground='gray'
        ).pack(anchor='w', pady=(5, 0))
    
    def _build_alerts_tab(self, parent):
        """Build the low battery alerts settings tab"""
        # Enable Section
        enable_frame = ttk.LabelFrame(parent, text="Enable/Disable", padding=10)
        enable_frame.pack(fill='x', padx=10, pady=5)
        
        self.vars['enable_low_battery'] = tk.BooleanVar(value=self.monitor.config.get('enable_low_battery_alarm', True))
        ttk.Checkbutton(
            enable_frame, 
            text="Enable low battery alerts",
            variable=self.vars['enable_low_battery']
        ).pack(anchor='w')
        
        # Thresholds Section
        threshold_frame = ttk.LabelFrame(parent, text="Thresholds", padding=10)
        threshold_frame.pack(fill='x', padx=10, pady=5)
        
        # Low battery threshold
        low_frame = ttk.Frame(threshold_frame)
        low_frame.pack(fill='x', pady=5)
        ttk.Label(low_frame, text="Low battery threshold:").pack(side='left')
        self.vars['low_threshold'] = tk.IntVar(value=self.monitor.config.get('low_battery_threshold', 30))
        ttk.Scale(
            low_frame, 
            from_=15, to=50, 
            variable=self.vars['low_threshold'],
            orient='horizontal',
            length=200
        ).pack(side='left', padx=10)
        self.low_threshold_label = ttk.Label(low_frame, text=f"{self.vars['low_threshold'].get()}%")
        self.low_threshold_label.pack(side='left')
        self.vars['low_threshold'].trace('w', lambda *args: self.low_threshold_label.config(text=f"{int(self.vars['low_threshold'].get())}%"))
        
        ttk.Label(threshold_frame, text="Start alerting below this percentage", foreground='gray').pack(anchor='w')
        
        # Critical battery threshold
        critical_frame = ttk.Frame(threshold_frame)
        critical_frame.pack(fill='x', pady=(15, 5))
        ttk.Label(critical_frame, text="Critical battery threshold:").pack(side='left')
        self.vars['critical_threshold'] = tk.IntVar(value=self.monitor.config.get('critical_battery_threshold', 20))
        ttk.Scale(
            critical_frame, 
            from_=5, to=25, 
            variable=self.vars['critical_threshold'],
            orient='horizontal',
            length=200
        ).pack(side='left', padx=10)
        self.critical_threshold_label = ttk.Label(critical_frame, text=f"{self.vars['critical_threshold'].get()}%")
        self.critical_threshold_label.pack(side='left')
        self.vars['critical_threshold'].trace('w', lambda *args: self.critical_threshold_label.config(text=f"{int(self.vars['critical_threshold'].get())}%"))
        
        ttk.Label(threshold_frame, text="Show persistent alert that blocks screen at this level", foreground='gray').pack(anchor='w')
        
        # Alert interval
        interval_frame = ttk.LabelFrame(parent, text="Alert Frequency", padding=10)
        interval_frame.pack(fill='x', padx=10, pady=5)
        
        alert_int_frame = ttk.Frame(interval_frame)
        alert_int_frame.pack(fill='x', pady=5)
        ttk.Label(alert_int_frame, text="Alert every N% decrease:").pack(side='left')
        self.vars['alert_interval'] = tk.IntVar(value=self.monitor.config.get('alert_interval', 2))
        ttk.Spinbox(
            alert_int_frame, 
            from_=1, to=5,
            textvariable=self.vars['alert_interval'],
            width=5
        ).pack(side='left', padx=10)
        
        ttk.Label(interval_frame, text="Notify for every N% decrease below the low threshold", foreground='gray').pack(anchor='w')
    
    def _build_charge_tab(self, parent):
        """Build the charge limit settings tab"""
        # Enable Section
        enable_frame = ttk.LabelFrame(parent, text="Enable/Disable", padding=10)
        enable_frame.pack(fill='x', padx=10, pady=5)
        
        self.vars['enable_charge_limit'] = tk.BooleanVar(value=self.monitor.config.get('enable_charge_limit_alarm', True))
        ttk.Checkbutton(
            enable_frame, 
            text="Enable charge limit notification",
            variable=self.vars['enable_charge_limit']
        ).pack(anchor='w')
        
        ttk.Label(
            enable_frame,
            text="Protect your Li-ion battery by getting alerted at a set charge level",
            foreground='gray'
        ).pack(anchor='w', pady=(5, 0))
        
        # Charge Limit Section
        limit_frame = ttk.LabelFrame(parent, text="Charge Limit", padding=10)
        limit_frame.pack(fill='x', padx=10, pady=5)
        
        slider_frame = ttk.Frame(limit_frame)
        slider_frame.pack(fill='x', pady=5)
        ttk.Label(slider_frame, text="Charge limit:").pack(side='left')
        self.vars['charge_limit'] = tk.IntVar(value=self.monitor.config.get('charge_limit', 80))
        ttk.Scale(
            slider_frame, 
            from_=60, to=100, 
            variable=self.vars['charge_limit'],
            orient='horizontal',
            length=200
        ).pack(side='left', padx=10)
        self.charge_limit_label = ttk.Label(slider_frame, text=f"{self.vars['charge_limit'].get()}%")
        self.charge_limit_label.pack(side='left')
        self.vars['charge_limit'].trace('w', lambda *args: self.charge_limit_label.config(text=f"{int(self.vars['charge_limit'].get())}%"))
        
        # Quick Set Buttons
        quick_frame = ttk.LabelFrame(parent, text="Quick Set", padding=10)
        quick_frame.pack(fill='x', padx=10, pady=5)
        
        def set_limit(val):
            self.vars['charge_limit'].set(val)
        
        btn_frame = ttk.Frame(quick_frame)
        btn_frame.pack(fill='x')
        
        ttk.Button(btn_frame, text="70%", command=lambda: set_limit(70), width=10).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="80%", command=lambda: set_limit(80), width=10).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="90%", command=lambda: set_limit(90), width=10).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="100%", command=lambda: set_limit(100), width=10).pack(side='left', padx=5)
        
        # Descriptions
        desc_frame = ttk.Frame(quick_frame)
        desc_frame.pack(fill='x', pady=(10, 0))
        
        descriptions = [
            ("70%", "Conservative — maximum battery lifespan"),
            ("80%", "Recommended — best balance for daily use"),
            ("90%", "Balanced — more capacity per charge"),
            ("100%", "Full — no limit (not recommended for longevity)")
        ]
        
        for pct, desc in descriptions:
            ttk.Label(desc_frame, text=f"  {pct}: {desc}", foreground='gray').pack(anchor='w')
    
    def _build_health_tab(self, parent):
        """Build the battery health tab"""
        # Current Status
        status_frame = ttk.LabelFrame(parent, text="Current Status", padding=10)
        status_frame.pack(fill='x', padx=10, pady=5)
        
        info = self.monitor.get_battery_info()
        if info:
            percent = info['percent']
            status = "Charging" if info['power_plugged'] else "On battery"
            ttk.Label(status_frame, text=f"Battery: {percent}%", font=('TkDefaultFont', 12, 'bold')).pack(anchor='w')
            ttk.Label(status_frame, text=f"Status: {status}").pack(anchor='w')
            
            if info['power_plugged']:
                eta = self.monitor.get_charge_eta(percent, True)
                if eta:
                    ttk.Label(status_frame, text=f"Full charge by: {eta}").pack(anchor='w')
        else:
            ttk.Label(status_frame, text="No battery detected").pack(anchor='w')
        
        # Health Warning Threshold
        health_frame = ttk.LabelFrame(parent, text="Health Monitoring", padding=10)
        health_frame.pack(fill='x', padx=10, pady=5)
        
        threshold_frame = ttk.Frame(health_frame)
        threshold_frame.pack(fill='x', pady=5)
        ttk.Label(threshold_frame, text="Health warning threshold:").pack(side='left')
        self.vars['health_threshold'] = tk.IntVar(value=self.monitor.config.get('health_warning_threshold', 80))
        ttk.Scale(
            threshold_frame, 
            from_=50, to=95, 
            variable=self.vars['health_threshold'],
            orient='horizontal',
            length=200
        ).pack(side='left', padx=10)
        self.health_label = ttk.Label(threshold_frame, text=f"{self.vars['health_threshold'].get()}%")
        self.health_label.pack(side='left')
        self.vars['health_threshold'].trace('w', lambda *args: self.health_label.config(text=f"{int(self.vars['health_threshold'].get())}%"))
        
        ttk.Label(health_frame, text="Alert when battery capacity drops below this percentage", foreground='gray').pack(anchor='w')
        
        # Charge Cycles
        cycles_frame = ttk.LabelFrame(parent, text="Charge Cycles", padding=10)
        cycles_frame.pack(fill='x', padx=10, pady=5)
        
        cycles = self.monitor.config.get('charge_cycle_count', 0)
        ttk.Label(cycles_frame, text=f"Total cycles completed: {cycles}", font=('TkDefaultFont', 11, 'bold')).pack(anchor='w')
        ttk.Label(cycles_frame, text="(Based on cumulative discharge tracking)", foreground='gray').pack(anchor='w')
        
        # Reset cycles button
        def reset_cycles():
            if messagebox.askyesno("Reset Cycles", "Are you sure you want to reset the cycle count?"):
                self.monitor.config['charge_cycle_count'] = 0
                self.monitor.save_config()
                messagebox.showinfo("Reset", "Cycle count has been reset to 0.")
        
        ttk.Button(cycles_frame, text="Reset Cycle Count", command=reset_cycles).pack(anchor='w', pady=(10, 0))
    
    def _build_stats_tab(self, parent):
        """Build the statistics tab"""
        # Usage Statistics
        if self.stats:
            usage_frame = ttk.LabelFrame(parent, text="Usage Statistics", padding=10)
            usage_frame.pack(fill='both', expand=True, padx=10, pady=5)
            
            # Create scrollable text widget for stats
            text_frame = ttk.Frame(usage_frame)
            text_frame.pack(fill='both', expand=True)
            
            scrollbar = ttk.Scrollbar(text_frame)
            scrollbar.pack(side='right', fill='y')
            
            stats_text = tk.Text(text_frame, height=20, width=55, wrap='word', 
                                yscrollcommand=scrollbar.set)
            stats_text.pack(fill='both', expand=True)
            scrollbar.config(command=stats_text.yview)
            
            stats_text.insert('1.0', self.stats.format_summary_text())
            stats_text.config(state='disabled')  # Make read-only
            
            # Refresh and cleanup buttons
            btn_frame = ttk.Frame(usage_frame)
            btn_frame.pack(fill='x', pady=(10, 0))
            
            def refresh_stats():
                stats_text.config(state='normal')
                stats_text.delete('1.0', tk.END)
                stats_text.insert('1.0', self.stats.format_summary_text())
                stats_text.config(state='disabled')
            
            def cleanup_stats():
                removed = self.stats.cleanup_old_data(30)
                messagebox.showinfo("Cleanup", f"Removed {removed} days of old data.")
                refresh_stats()
            
            ttk.Button(btn_frame, text="Refresh", command=refresh_stats).pack(side='left', padx=5)
            ttk.Button(btn_frame, text="Cleanup Old Data (30+ days)", command=cleanup_stats).pack(side='left', padx=5)
        else:
            ttk.Label(parent, text="Statistics not available").pack(pady=20)
    
    def _build_about_tab(self, parent):
        """Build the about tab"""
        about_frame = ttk.Frame(parent, padding=20)
        about_frame.pack(fill='both', expand=True)
        
        ttk.Label(
            about_frame, 
            text="Smart Battery Alert",
            font=('TkDefaultFont', 18, 'bold')
        ).pack(pady=10)
        
        ttk.Label(
            about_frame, 
            text="Windows Battery Management Tool",
            font=('TkDefaultFont', 11)
        ).pack()
        
        ttk.Label(
            about_frame, 
            text="Feature parity with Linux GNOME Extension",
            font=('TkDefaultFont', 9),
            foreground='gray'
        ).pack()
        
        ttk.Label(about_frame, text="").pack(pady=5)
        
        features = [
            "Low battery alerts with customizable thresholds",
            "Critical battery dialog that blocks the screen",
            "Charge limit notifications for battery longevity",
            "Over-charge alerts every 1% beyond limit",
            "Charge time prediction with clock-time ETA",
            "Charger connected notification with ETA",
            "Battery health tracking and charge cycle counting",
            "Usage statistics and pattern analysis",
            "System tray with live battery icon",
            "Quick-set charge limit buttons (70%, 80%, 90%)"
        ]
        
        ttk.Label(about_frame, text="Features:", font=('TkDefaultFont', 10, 'bold')).pack(anchor='w', pady=(10, 5))
        for feature in features:
            ttk.Label(about_frame, text=f"  ✓ {feature}").pack(anchor='w')
        
        ttk.Label(about_frame, text="").pack(pady=10)
        ttk.Label(about_frame, text="Version 1.0.0").pack()
        ttk.Label(about_frame, text="Python + Tkinter + psutil").pack()
        ttk.Label(about_frame, text="").pack(pady=5)
        ttk.Label(about_frame, text="© 2026 Komesh Bathula", foreground='gray').pack()
    
    def _save_settings(self):
        """Save settings to config"""
        try:
            # Handle startup setting
            self._update_startup_status(self.vars['run_at_startup'].get())
            
            # General settings
            self.monitor.config['show_panel_percentage'] = self.vars['show_percentage'].get()
            self.monitor.config['update_interval'] = int(self.vars['update_interval'].get())
            self.monitor.config['enable_charge_prediction'] = self.vars['enable_prediction'].get()
            self.monitor.config['enable_sound_alerts'] = self.vars['enable_sound'].get()
            self.monitor.config['sound_volume'] = int(self.vars['sound_volume'].get())
            self.monitor.config['enable_critical_dialog'] = self.vars['enable_critical_dialog'].get()
            
            # Low battery settings
            self.monitor.config['enable_low_battery_alarm'] = self.vars['enable_low_battery'].get()
            self.monitor.config['low_battery_threshold'] = int(self.vars['low_threshold'].get())
            self.monitor.config['critical_battery_threshold'] = int(self.vars['critical_threshold'].get())
            self.monitor.config['alert_interval'] = int(self.vars['alert_interval'].get())
            
            # Charge limit settings
            self.monitor.config['enable_charge_limit_alarm'] = self.vars['enable_charge_limit'].get()
            self.monitor.config['charge_limit'] = int(self.vars['charge_limit'].get())
            
            # Health settings
            self.monitor.config['health_warning_threshold'] = int(self.vars['health_threshold'].get())
            
            # Validate thresholds
            if self.monitor.config['critical_battery_threshold'] >= self.monitor.config['low_battery_threshold']:
                messagebox.showwarning(
                    "Invalid Settings",
                    "Critical threshold must be lower than low battery threshold."
                )
                return
            
            # Save to file
            self.monitor.save_config()
            
            # Callback
            if self.on_save_callback:
                self.on_save_callback()
            
            messagebox.showinfo("Settings Saved", "Your settings have been saved.")
            self._close()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")
    
    def _reset_defaults(self):
        """Reset settings to defaults"""
        if messagebox.askyesno("Reset Settings", "Reset all settings to defaults?"):
            # General
            self.vars['show_percentage'].set(True)
            self.vars['update_interval'].set(30)
            self.vars['enable_prediction'].set(True)
            self.vars['enable_sound'].set(True)
            self.vars['sound_volume'].set(50)
            self.vars['enable_critical_dialog'].set(True)
            
            # Low battery
            self.vars['enable_low_battery'].set(True)
            self.vars['low_threshold'].set(30)
            self.vars['critical_threshold'].set(20)
            self.vars['alert_interval'].set(2)
            
            # Charge limit
            self.vars['enable_charge_limit'].set(True)
            self.vars['charge_limit'].set(80)
            
            # Health
            self.vars['health_threshold'].set(80)
    
    def _close(self):
        """Close the settings window"""
        self.is_open = False
        if self.window:
            self.window.destroy()
            self.window = None

    def _check_startup_status(self):
        """Check if application is set to run at startup (Windows Registry)"""
        import sys
        if sys.platform != 'win32':
            return False
            
        try:
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:
                try:
                    winreg.QueryValueEx(key, "SmartBatteryAlert")
                    return True
                except FileNotFoundError:
                    return False
        except Exception as e:
            print(f"Error checking startup status: {e}")
            return False

    def _update_startup_status(self, enable):
        """Enable/disable run at startup in Windows Registry"""
        import sys
        if sys.platform != 'win32':
            return
            
        try:
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                if enable:
                    # Get the absolute path to main.py
                    import os
                    app_path = os.path.abspath(sys.argv[0])
                    # If running as script, use python.exe
                    if app_path.endswith('.py'):
                        python_exe = sys.executable
                        command = f'"{python_exe}" "{app_path}"'
                    else:
                        command = f'"{app_path}"'
                    
                    winreg.SetValueEx(key, "SmartBatteryAlert", 0, winreg.REG_SZ, command)
                else:
                    try:
                        winreg.DeleteValue(key, "SmartBatteryAlert")
                    except FileNotFoundError:
                        pass
        except Exception as e:
            print(f"Error updating startup status: {e}")


# Test the settings GUI
if __name__ == "__main__":
    from battery_monitor import BatteryMonitor
    from usage_stats import UsageStats
    
    print("Settings GUI Test")
    print("=" * 50)
    print("Opening settings window...")
    
    monitor = BatteryMonitor()
    stats = UsageStats()
    
    def on_save():
        print("Settings saved!")
    
    gui = SettingsGUI(monitor, stats, on_save)
    gui.show()
    
    print("Settings window closed.")
