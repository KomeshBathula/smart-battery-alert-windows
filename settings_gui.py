"""
Smart Battery Alert for Windows
Settings GUI - Tkinter-based settings window
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
        self.window.geometry("500x600")
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
        alerts_tab = ttk.Frame(notebook)
        stats_tab = ttk.Frame(notebook)
        about_tab = ttk.Frame(notebook)
        
        notebook.add(alerts_tab, text='Alerts')
        notebook.add(stats_tab, text='Statistics')
        notebook.add(about_tab, text='About')
        
        # Build tabs
        self._build_alerts_tab(alerts_tab)
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
    
    def _build_alerts_tab(self, parent):
        """Build the alerts settings tab"""
        # Low Battery Section
        low_battery_frame = ttk.LabelFrame(parent, text="Low Battery Alerts", padding=10)
        low_battery_frame.pack(fill='x', padx=10, pady=5)
        
        # Enable low battery alerts
        self.vars['enable_low_battery'] = tk.BooleanVar(value=self.monitor.config.get('enable_low_battery_alarm', True))
        ttk.Checkbutton(
            low_battery_frame, 
            text="Enable low battery alerts",
            variable=self.vars['enable_low_battery']
        ).pack(anchor='w')
        
        # Low battery threshold
        threshold_frame = ttk.Frame(low_battery_frame)
        threshold_frame.pack(fill='x', pady=5)
        ttk.Label(threshold_frame, text="Low battery threshold:").pack(side='left')
        self.vars['low_threshold'] = tk.IntVar(value=self.monitor.config.get('low_battery_threshold', 30))
        ttk.Scale(
            threshold_frame, 
            from_=10, to=50, 
            variable=self.vars['low_threshold'],
            orient='horizontal',
            length=200
        ).pack(side='left', padx=10)
        self.low_threshold_label = ttk.Label(threshold_frame, text=f"{self.vars['low_threshold'].get()}%")
        self.low_threshold_label.pack(side='left')
        self.vars['low_threshold'].trace('w', lambda *args: self.low_threshold_label.config(text=f"{self.vars['low_threshold'].get()}%"))
        
        # Critical battery threshold
        critical_frame = ttk.Frame(low_battery_frame)
        critical_frame.pack(fill='x', pady=5)
        ttk.Label(critical_frame, text="Critical battery threshold:").pack(side='left')
        self.vars['critical_threshold'] = tk.IntVar(value=self.monitor.config.get('critical_battery_threshold', 20))
        ttk.Scale(
            critical_frame, 
            from_=5, to=30, 
            variable=self.vars['critical_threshold'],
            orient='horizontal',
            length=200
        ).pack(side='left', padx=10)
        self.critical_threshold_label = ttk.Label(critical_frame, text=f"{self.vars['critical_threshold'].get()}%")
        self.critical_threshold_label.pack(side='left')
        self.vars['critical_threshold'].trace('w', lambda *args: self.critical_threshold_label.config(text=f"{self.vars['critical_threshold'].get()}%"))
        
        # Alert interval
        interval_frame = ttk.Frame(low_battery_frame)
        interval_frame.pack(fill='x', pady=5)
        ttk.Label(interval_frame, text="Alert interval (%):").pack(side='left')
        self.vars['alert_interval'] = tk.IntVar(value=self.monitor.config.get('alert_interval', 2))
        ttk.Spinbox(
            interval_frame, 
            from_=1, to=10,
            textvariable=self.vars['alert_interval'],
            width=5
        ).pack(side='left', padx=10)
        
        # Charge Limit Section
        charge_limit_frame = ttk.LabelFrame(parent, text="Charge Limit", padding=10)
        charge_limit_frame.pack(fill='x', padx=10, pady=5)
        
        # Enable charge limit
        self.vars['enable_charge_limit'] = tk.BooleanVar(value=self.monitor.config.get('enable_charge_limit_alarm', True))
        ttk.Checkbutton(
            charge_limit_frame, 
            text="Enable charge limit notification",
            variable=self.vars['enable_charge_limit']
        ).pack(anchor='w')
        
        # Charge limit threshold
        limit_frame = ttk.Frame(charge_limit_frame)
        limit_frame.pack(fill='x', pady=5)
        ttk.Label(limit_frame, text="Charge limit:").pack(side='left')
        self.vars['charge_limit'] = tk.IntVar(value=self.monitor.config.get('charge_limit', 80))
        ttk.Scale(
            limit_frame, 
            from_=50, to=100, 
            variable=self.vars['charge_limit'],
            orient='horizontal',
            length=200
        ).pack(side='left', padx=10)
        self.charge_limit_label = ttk.Label(limit_frame, text=f"{self.vars['charge_limit'].get()}%")
        self.charge_limit_label.pack(side='left')
        self.vars['charge_limit'].trace('w', lambda *args: self.charge_limit_label.config(text=f"{self.vars['charge_limit'].get()}%"))
        
        # Sound Settings Section
        sound_frame = ttk.LabelFrame(parent, text="Sound", padding=10)
        sound_frame.pack(fill='x', padx=10, pady=5)
        
        self.vars['enable_sound'] = tk.BooleanVar(value=self.monitor.config.get('enable_sound_alerts', True))
        ttk.Checkbutton(
            sound_frame, 
            text="Enable sound alerts",
            variable=self.vars['enable_sound']
        ).pack(anchor='w')
        
        # Prediction Settings
        prediction_frame = ttk.LabelFrame(parent, text="Charge Prediction", padding=10)
        prediction_frame.pack(fill='x', padx=10, pady=5)
        
        self.vars['enable_prediction'] = tk.BooleanVar(value=self.monitor.config.get('enable_charge_prediction', True))
        ttk.Checkbutton(
            prediction_frame, 
            text="Enable charge time prediction",
            variable=self.vars['enable_prediction']
        ).pack(anchor='w')
    
    def _build_stats_tab(self, parent):
        """Build the statistics tab"""
        # Current Battery Status
        status_frame = ttk.LabelFrame(parent, text="Current Status", padding=10)
        status_frame.pack(fill='x', padx=10, pady=5)
        
        info = self.monitor.get_battery_info()
        if info:
            percent = info['percent']
            status = "Charging" if info['power_plugged'] else "Discharging"
            ttk.Label(status_frame, text=f"Battery: {percent}%", font=('TkDefaultFont', 12, 'bold')).pack(anchor='w')
            ttk.Label(status_frame, text=f"Status: {status}").pack(anchor='w')
            
            if info['power_plugged']:
                eta = self.monitor.get_charge_eta(percent, True)
                if eta:
                    ttk.Label(status_frame, text=f"Full charge by: {eta}").pack(anchor='w')
        else:
            ttk.Label(status_frame, text="No battery detected").pack(anchor='w')
        
        # Charge Cycles
        cycles_frame = ttk.LabelFrame(parent, text="Battery Health", padding=10)
        cycles_frame.pack(fill='x', padx=10, pady=5)
        
        cycles = self.monitor.config.get('charge_cycle_count', 0)
        ttk.Label(cycles_frame, text=f"Estimated charge cycles: {cycles}").pack(anchor='w')
        ttk.Label(cycles_frame, text="(Based on cumulative discharge tracking)").pack(anchor='w')
        
        # Usage Statistics
        if self.stats:
            usage_frame = ttk.LabelFrame(parent, text="Usage Statistics", padding=10)
            usage_frame.pack(fill='both', expand=True, padx=10, pady=5)
            
            # Create text widget for stats
            stats_text = tk.Text(usage_frame, height=15, width=50, wrap='word')
            stats_text.pack(fill='both', expand=True)
            
            stats_text.insert('1.0', self.stats.format_summary_text())
            stats_text.config(state='disabled')  # Make read-only
    
    def _build_about_tab(self, parent):
        """Build the about tab"""
        about_frame = ttk.Frame(parent, padding=20)
        about_frame.pack(fill='both', expand=True)
        
        ttk.Label(
            about_frame, 
            text="Smart Battery Alert",
            font=('TkDefaultFont', 16, 'bold')
        ).pack(pady=10)
        
        ttk.Label(
            about_frame, 
            text="Windows Battery Management Tool",
            font=('TkDefaultFont', 10)
        ).pack()
        
        ttk.Label(about_frame, text="").pack(pady=5)
        
        features = [
            "Low battery alerts with customizable thresholds",
            "Charge limit notifications for battery longevity",
            "Charge time prediction with clock-time ETA",
            "Battery health tracking and charge cycle counting",
            "Usage statistics and pattern analysis",
            "System tray integration with live battery icon"
        ]
        
        ttk.Label(about_frame, text="Features:", font=('TkDefaultFont', 10, 'bold')).pack(anchor='w', pady=(10, 5))
        for feature in features:
            ttk.Label(about_frame, text=f"  - {feature}").pack(anchor='w')
        
        ttk.Label(about_frame, text="").pack(pady=10)
        ttk.Label(about_frame, text="Version 1.0.0").pack()
        ttk.Label(about_frame, text="Python + Tkinter + psutil").pack()
    
    def _save_settings(self):
        """Save settings to config"""
        try:
            # Update monitor config
            self.monitor.config['enable_low_battery_alarm'] = self.vars['enable_low_battery'].get()
            self.monitor.config['low_battery_threshold'] = int(self.vars['low_threshold'].get())
            self.monitor.config['critical_battery_threshold'] = int(self.vars['critical_threshold'].get())
            self.monitor.config['alert_interval'] = int(self.vars['alert_interval'].get())
            self.monitor.config['enable_charge_limit_alarm'] = self.vars['enable_charge_limit'].get()
            self.monitor.config['charge_limit'] = int(self.vars['charge_limit'].get())
            self.monitor.config['enable_sound_alerts'] = self.vars['enable_sound'].get()
            self.monitor.config['enable_charge_prediction'] = self.vars['enable_prediction'].get()
            
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
            self.vars['enable_low_battery'].set(True)
            self.vars['low_threshold'].set(30)
            self.vars['critical_threshold'].set(20)
            self.vars['alert_interval'].set(2)
            self.vars['enable_charge_limit'].set(True)
            self.vars['charge_limit'].set(80)
            self.vars['enable_sound'].set(True)
            self.vars['enable_prediction'].set(True)
    
    def _close(self):
        """Close the settings window"""
        self.is_open = False
        if self.window:
            self.window.destroy()
            self.window = None


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
