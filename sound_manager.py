"""
Smart Battery Alert for Windows
Sound Manager - Plays alert sounds for notifications
"""

import os
import sys
import threading


class SoundManager:
    """Manages sound alerts for battery notifications"""
    
    def __init__(self, volume=50):
        self.volume = volume  # 0-100
        self._sound_thread = None
        
        # Sound types mapped to Windows system sounds
        self.sound_types = {
            'low_battery': 'SystemExclamation',
            'critical_battery': 'SystemHand',
            'charge_limit': 'SystemAsterisk',
            'over_charge': 'SystemExclamation',
            'charger_connected': 'SystemAsterisk',
            'fully_charged': 'SystemAsterisk',
            'health_warning': 'SystemExclamation',
            'default': 'SystemAsterisk'
        }
    
    def set_volume(self, volume):
        """Set volume level (0-100)"""
        self.volume = max(0, min(100, volume))
    
    def play_alert(self, alert_type='default', blocking=False):
        """
        Play an alert sound based on alert type
        
        Args:
            alert_type: Type of alert (low_battery, critical_battery, charge_limit, etc.)
            blocking: If True, wait for sound to complete
        """
        if blocking:
            self._play_sound(alert_type)
        else:
            # Play in background thread
            self._sound_thread = threading.Thread(
                target=self._play_sound, 
                args=(alert_type,),
                daemon=True
            )
            self._sound_thread.start()
    
    def _play_sound(self, alert_type):
        """Internal method to play the actual sound"""
        try:
            if sys.platform == 'win32':
                self._play_windows_sound(alert_type)
            else:
                # Fallback for testing on Linux
                self._play_fallback_sound(alert_type)
        except Exception as e:
            print(f"Error playing sound: {e}")
    
    def _play_windows_sound(self, alert_type):
        """Play Windows system sound"""
        try:
            import winsound
            
            # Map alert types to Windows sounds
            sound_map = {
                'low_battery': winsound.MB_ICONEXCLAMATION,
                'critical_battery': winsound.MB_ICONHAND,
                'charge_limit': winsound.MB_ICONASTERISK,
                'over_charge': winsound.MB_ICONEXCLAMATION,
                'charger_connected': winsound.MB_ICONASTERISK,
                'fully_charged': winsound.MB_ICONASTERISK,
                'health_warning': winsound.MB_ICONEXCLAMATION,
                'default': winsound.MB_OK
            }
            
            sound = sound_map.get(alert_type, winsound.MB_OK)
            winsound.MessageBeep(sound)
            
            # For critical alerts, play multiple beeps
            if alert_type == 'critical_battery':
                import time
                for _ in range(2):
                    time.sleep(0.3)
                    winsound.MessageBeep(winsound.MB_ICONHAND)
                    
        except ImportError:
            # winsound not available (not on Windows)
            self._play_fallback_sound(alert_type)
    
    def _play_fallback_sound(self, alert_type):
        """Fallback sound for non-Windows systems (for testing)"""
        try:
            # Try using plyer for cross-platform
            from plyer import notification
            # Plyer doesn't have sound, but we can print for testing
            print(f"[SOUND] Playing {alert_type} alert sound")
            
            # On Linux, try using system bell
            if sys.platform.startswith('linux'):
                # Print bell character
                print('\a', end='', flush=True)
                
                # Or try paplay if available
                try:
                    import subprocess
                    sound_file = '/usr/share/sounds/freedesktop/stereo/dialog-warning.oga'
                    if os.path.exists(sound_file):
                        subprocess.run(['paplay', sound_file], 
                                      capture_output=True, timeout=2)
                except:
                    pass
                    
        except Exception as e:
            print(f"Fallback sound error: {e}")
    
    def play_custom_sound(self, file_path):
        """Play a custom sound file"""
        if not os.path.exists(file_path):
            print(f"Sound file not found: {file_path}")
            return
        
        try:
            if sys.platform == 'win32':
                import winsound
                winsound.PlaySound(file_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                # Linux fallback
                import subprocess
                subprocess.Popen(['paplay', file_path], 
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"Error playing custom sound: {e}")
    
    def stop(self):
        """Stop any currently playing sound"""
        try:
            if sys.platform == 'win32':
                import winsound
                winsound.PlaySound(None, winsound.SND_PURGE)
        except:
            pass


# Test the sound manager
if __name__ == "__main__":
    print("Sound Manager Test")
    print("=" * 50)
    
    manager = SoundManager()
    
    print("\nTesting different alert sounds...")
    
    import time
    
    for alert_type in ['default', 'low_battery', 'critical_battery', 'charge_limit']:
        print(f"\nPlaying: {alert_type}")
        manager.play_alert(alert_type, blocking=True)
        time.sleep(1)
    
    print("\nSound test complete!")
