"""
Smart Battery Alert for Windows
System Tray Integration - Provides system tray icon with menu
Feature parity with Linux GNOME extension
"""

import threading
import sys
import os

# Handle imports for cross-platform compatibility
try:
    import pystray
    from pystray import MenuItem as item
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False
    print("Warning: pystray not available. System tray disabled.")

try:
    from PIL import Image, ImageDraw, ImageFont
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    print("Warning: Pillow not available. Using fallback icon.")


class SystemTray:
    """System tray icon and menu for battery monitor"""
    
    def __init__(self, monitor, sound_manager=None, on_settings=None, on_quit=None):
        """
        Initialize system tray
        
        Args:
            monitor: BatteryMonitor instance
            sound_manager: SoundManager instance (optional)
            on_settings: Callback for settings menu item
            on_quit: Callback for quit menu item
        """
        self.monitor = monitor
        self.sound_manager = sound_manager
        self.on_settings_callback = on_settings
        self.on_quit_callback = on_quit
        
        self.icon = None
        self._running = False
        self._thread = None
        
        # Cache for battery state
        self._last_percent = -1
        self._last_charging = None
    
    def create_battery_icon(self, percent, charging=False):
        """Create a battery icon with current percentage"""
        if not PILLOW_AVAILABLE:
            return None
        
        # Create 64x64 icon
        size = 64
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Battery outline
        battery_left = 8
        battery_right = 56
        battery_top = 16
        battery_bottom = 48
        cap_width = 4
        
        # Draw battery outline
        outline_color = (255, 255, 255, 255)
        draw.rectangle(
            [battery_left, battery_top, battery_right, battery_bottom],
            outline=outline_color, width=2
        )
        
        # Draw battery cap (positive terminal)
        cap_left = battery_right
        cap_top = battery_top + 10
        cap_bottom = battery_bottom - 10
        draw.rectangle(
            [cap_left, cap_top, cap_left + cap_width, cap_bottom],
            fill=outline_color
        )
        
        # Calculate fill based on percentage
        fill_width = int((battery_right - battery_left - 4) * (percent / 100))
        
        # Choose color based on percentage
        if percent <= 20:
            fill_color = (255, 60, 60, 255)  # Red
        elif percent <= 40:
            fill_color = (255, 165, 0, 255)  # Orange
        else:
            fill_color = (60, 255, 60, 255)  # Green
        
        # Draw fill
        if fill_width > 0:
            draw.rectangle(
                [battery_left + 3, battery_top + 3, 
                 battery_left + 3 + fill_width, battery_bottom - 3],
                fill=fill_color
            )
        
        # Draw charging indicator (lightning bolt)
        if charging:
            bolt_color = (255, 255, 0, 255)  # Yellow
            # Simple lightning bolt
            bolt_points = [
                (32, 10),   # Top
                (24, 32),   # Middle left
                (30, 32),   # Middle inner left
                (28, 54),   # Bottom
                (40, 30),   # Middle right
                (34, 30),   # Middle inner right
            ]
            draw.polygon(bolt_points, fill=bolt_color)
        
        # Draw percentage text
        try:
            # Try to use a font
            font = ImageFont.truetype("arial.ttf", 14)
        except:
            font = ImageFont.load_default()
        
        # Text position (bottom of icon)
        text = f"{percent}%"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_x = (size - text_width) // 2
        text_y = battery_bottom + 2
        
        # Draw text with outline for visibility
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx != 0 or dy != 0:
                    draw.text((text_x + dx, text_y + dy), text, 
                             fill=(0, 0, 0, 255), font=font)
        draw.text((text_x, text_y), text, fill=(255, 255, 255, 255), font=font)
        
        return img
    
    def create_simple_icon(self):
        """Create a simple fallback icon"""
        if not PILLOW_AVAILABLE:
            return None
        
        size = 64
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Simple green circle
        draw.ellipse([8, 8, 56, 56], fill=(60, 200, 60, 255))
        draw.text((20, 20), "B", fill=(255, 255, 255, 255))
        
        return img
    
    def _set_charge_limit(self, limit):
        """Set charge limit via quick-set button"""
        def action(icon, item):
            self.monitor.set_charge_limit(limit)
            self.update_icon()
            print(f"Charge limit set to {limit}%")
        return action
    
    def _is_limit_selected(self, limit):
        """Check if this limit is currently selected"""
        def check(item):
            return self.monitor.config.get('charge_limit') == limit
        return check
    
    def get_menu(self):
        """Create the system tray menu"""
        info = self.monitor.get_battery_info()
        
        if info:
            percent = info['percent']
            charging = info['power_plugged']
            
            if charging:
                status = "⚡ Charging"
            else:
                status = "🔋 On battery"
            
            # Get charge ETA if charging
            eta_text = ""
            if charging:
                eta = self.monitor.get_charge_eta(percent, charging)
                if eta:
                    eta_text = f" (Full by {eta})"
            
            battery_text = f"Battery: {percent}%"
            status_text = f"Status: {status}{eta_text}"
        else:
            battery_text = "Battery: Not detected"
            status_text = "Status: Unknown"
        
        # Get cycle count
        cycles = self.monitor.config.get('charge_cycle_count', 0)
        
        # Get current charge limit
        current_limit = self.monitor.config.get('charge_limit', 80)
        
        # Get shutdown tip
        shutdown_tip = None
        if info and info['power_plugged']:
            shutdown_tip = self.monitor.get_shutdown_tip(info['percent'], info['power_plugged'])
        
        # Build menu items
        menu_items = [
            # Header
            item('Smart Battery Alert', None, enabled=False),
            pystray.Menu.SEPARATOR,
            
            # Battery info
            item(battery_text, None, enabled=False),
            item(status_text, None, enabled=False),
            item(f"Charge Cycles: {cycles}", None, enabled=False),
            item(f"Charge Limit: {current_limit}%", None, enabled=False),
        ]
        
        # Add shutdown tip if charging
        if shutdown_tip:
            menu_items.append(pystray.Menu.SEPARATOR)
            menu_items.append(item(shutdown_tip, None, enabled=False))
        
        menu_items.append(pystray.Menu.SEPARATOR)
        
        # Quick-set charge limit submenu
        menu_items.append(
            item('Set Charge Limit', pystray.Menu(
                item('70% (Conservative)', self._set_charge_limit(70), 
                     checked=self._is_limit_selected(70)),
                item('80% (Recommended)', self._set_charge_limit(80),
                     checked=self._is_limit_selected(80)),
                item('90% (Balanced)', self._set_charge_limit(90),
                     checked=self._is_limit_selected(90)),
                item('100% (Full)', self._set_charge_limit(100),
                     checked=self._is_limit_selected(100)),
            ))
        )
        
        menu_items.extend([
            pystray.Menu.SEPARATOR,
            item('Settings', self._on_settings),
            item('Refresh', self._on_refresh),
            pystray.Menu.SEPARATOR,
            item('Quit', self._on_quit)
        ])
        
        return pystray.Menu(*menu_items)
    
    def _on_settings(self, icon, item):
        """Handle settings menu click"""
        if self.on_settings_callback:
            self.on_settings_callback()
    
    def _on_refresh(self, icon, item):
        """Handle refresh menu click"""
        self.update_icon()
    
    def _on_quit(self, icon, item):
        """Handle quit menu click"""
        self.stop()
        if self.on_quit_callback:
            self.on_quit_callback()
    
    def update_icon(self):
        """Update the tray icon based on current battery state"""
        if not self.icon:
            return
        
        info = self.monitor.get_battery_info()
        if info:
            percent = info['percent']
            charging = info['power_plugged']
            
            # Only update if state changed
            if percent != self._last_percent or charging != self._last_charging:
                self._last_percent = percent
                self._last_charging = charging
                
                new_icon = self.create_battery_icon(percent, charging)
                if new_icon:
                    self.icon.icon = new_icon
                
                # Update menu
                self.icon.menu = self.get_menu()
                
                # Update tooltip
                status = "Charging" if charging else "On battery"
                eta = ""
                if charging:
                    eta_time = self.monitor.get_charge_eta(percent, charging)
                    if eta_time:
                        eta = f" - Full by {eta_time}"
                
                # Show percentage in tooltip if enabled
                if self.monitor.config.get('show_panel_percentage', True):
                    self.icon.title = f"Smart Battery Alert - {percent}% ({status}){eta}"
                else:
                    self.icon.title = f"Smart Battery Alert - {status}{eta}"
    
    def start(self):
        """Start the system tray icon"""
        if not PYSTRAY_AVAILABLE:
            print("System tray not available")
            return False
        
        # Get initial battery state
        info = self.monitor.get_battery_info()
        if info:
            percent = info['percent']
            charging = info['power_plugged']
            icon_image = self.create_battery_icon(percent, charging)
        else:
            icon_image = self.create_simple_icon()
        
        if not icon_image:
            print("Could not create icon image")
            return False
        
        # Create the icon
        self.icon = pystray.Icon(
            "smart_battery_alert",
            icon_image,
            "Smart Battery Alert",
            menu=self.get_menu()
        )
        
        self._running = True
        
        # Run in background thread
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        
        return True
    
    def _run(self):
        """Run the system tray icon loop"""
        try:
            self.icon.run()
        except Exception as e:
            print(f"System tray error: {e}")
        finally:
            self._running = False
    
    def stop(self):
        """Stop the system tray icon"""
        self._running = False
        if self.icon:
            try:
                self.icon.stop()
            except:
                pass
            self.icon = None
    
    def is_running(self):
        """Check if system tray is running"""
        return self._running


# Test the system tray
if __name__ == "__main__":
    import time
    
    # Import the battery monitor for testing
    from battery_monitor import BatteryMonitor
    from sound_manager import SoundManager
    
    print("System Tray Test")
    print("=" * 50)
    print("The system tray icon should appear.")
    print("Right-click the icon to see the menu.")
    print("Press Ctrl+C to exit.\n")
    
    # Create instances
    monitor = BatteryMonitor()
    sound = SoundManager()
    
    def on_settings():
        print("Settings clicked!")
    
    def on_quit():
        print("Quit clicked!")
        sys.exit(0)
    
    # Create and start system tray
    tray = SystemTray(monitor, sound, on_settings, on_quit)
    
    if tray.start():
        print("System tray started successfully!")
        
        # Keep updating the icon
        try:
            while tray.is_running():
                tray.update_icon()
                time.sleep(5)
        except KeyboardInterrupt:
            print("\nStopping...")
            tray.stop()
    else:
        print("Failed to start system tray")
