"""
Smart Battery Alert for Windows
Critical Battery Dialog - A persistent, always-on-top modal dialog
that blocks the desktop until charger is connected (like Linux version)
"""

import tkinter as tk
from tkinter import ttk
import threading
import time


class CriticalBatteryDialog:
    """
    A modal dialog that blocks the desktop until charger is connected.
    - Always on top
    - Cannot be closed until charger is detected
    - Centered on screen
    - Shows battery icon and warning message
    """
    
    def __init__(self, get_state_callback, on_dismissed=None):
        """
        Initialize critical battery dialog
        
        Args:
            get_state_callback: Function that returns (percent, power_plugged)
            on_dismissed: Callback when dialog is properly dismissed
        """
        self._get_state = get_state_callback
        self._on_dismissed = on_dismissed
        self._dismissed = False
        self._window = None
        self._is_open = False
        self._check_timer = None
        
        # UI elements
        self._body_label = None
        self._percent_label = None
    
    def show(self):
        """Show the critical battery dialog"""
        if self._is_open:
            if self._window:
                self._window.focus_force()
            return
        
        self._is_open = True
        self._dismissed = False
        
        # Run in main thread
        self._create_window()
    
    def _create_window(self):
        """Create the critical battery dialog window"""
        self._window = tk.Tk()
        self._window.title("Critical Battery Warning")
        
        # Get screen dimensions
        screen_width = self._window.winfo_screenwidth()
        screen_height = self._window.winfo_screenheight()
        
        # Window size
        window_width = 450
        window_height = 350
        
        # Center the window
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self._window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Make it always on top and remove window decorations for "modal" feel
        self._window.attributes('-topmost', True)
        self._window.overrideredirect(False)  # Keep title bar for Windows
        self._window.resizable(False, False)
        
        # Prevent closing with X button
        self._window.protocol("WM_DELETE_WINDOW", self._on_close_attempt)
        
        # Red background for urgency
        self._window.configure(bg='#2d0000')
        
        # Main container
        main_frame = tk.Frame(self._window, bg='#2d0000', padx=30, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        # Warning icon (using text emoji)
        icon_label = tk.Label(
            main_frame,
            text="⚠️",
            font=('Segoe UI Emoji', 48),
            bg='#2d0000',
            fg='#ff5555'
        )
        icon_label.pack(pady=(10, 5))
        
        # Title
        title_label = tk.Label(
            main_frame,
            text="Critical Battery!",
            font=('Segoe UI', 24, 'bold'),
            bg='#2d0000',
            fg='#ff5555'
        )
        title_label.pack(pady=(0, 10))
        
        # Battery percentage
        percent, _ = self._get_state()
        self._percent_label = tk.Label(
            main_frame,
            text=f"Battery: {percent}%",
            font=('Segoe UI', 18),
            bg='#2d0000',
            fg='#ffffff'
        )
        self._percent_label.pack(pady=(0, 10))
        
        # Body message
        self._body_label = tk.Label(
            main_frame,
            text="Battery is critically low!\nConnect your charger immediately.",
            font=('Segoe UI', 12),
            bg='#2d0000',
            fg='#cccccc',
            justify='center'
        )
        self._body_label.pack(pady=(0, 20))
        
        # Button frame
        button_frame = tk.Frame(main_frame, bg='#2d0000')
        button_frame.pack(pady=(10, 0))
        
        # Check charger button
        check_button = tk.Button(
            button_frame,
            text="I've connected the charger",
            font=('Segoe UI', 11),
            bg='#444444',
            fg='#ffffff',
            activebackground='#555555',
            activeforeground='#ffffff',
            padx=20,
            pady=10,
            cursor='hand2',
            command=self._on_check_charger
        )
        check_button.pack()
        
        # Bind Enter key
        self._window.bind('<Return>', lambda e: self._on_check_charger())
        
        # Start periodic check for charger
        self._start_auto_check()
        
        # Keep window focused
        self._window.focus_force()
        self._window.grab_set()  # Modal grab
        
        # Start main loop
        self._window.mainloop()
    
    def _on_close_attempt(self):
        """Handle attempt to close the window"""
        # Check if charger is connected
        _, power_plugged = self._get_state()
        if power_plugged:
            self._dismiss()
        else:
            # Shake the window to indicate it can't be closed
            self._shake_window()
            self._body_label.config(
                text="You cannot close this window!\nPlease connect your charger first."
            )
    
    def _shake_window(self):
        """Shake the window to indicate action not allowed"""
        if not self._window:
            return
        
        x = self._window.winfo_x()
        y = self._window.winfo_y()
        
        for _ in range(3):
            self._window.geometry(f"+{x+10}+{y}")
            self._window.update()
            time.sleep(0.05)
            self._window.geometry(f"+{x-10}+{y}")
            self._window.update()
            time.sleep(0.05)
        
        self._window.geometry(f"+{x}+{y}")
    
    def _on_check_charger(self):
        """Handle 'I've connected the charger' button click"""
        percent, power_plugged = self._get_state()
        
        if power_plugged:
            self._dismiss()
        else:
            self._body_label.config(
                text="Charger NOT detected!\nPlease plug in your charger and try again.",
                fg='#ff8888'
            )
            self._shake_window()
    
    def _start_auto_check(self):
        """Start periodic check for charger connection"""
        def check():
            if not self._is_open or self._dismissed:
                return
            
            percent, power_plugged = self._get_state()
            
            # Update percentage display
            if self._percent_label and self._window:
                try:
                    self._percent_label.config(text=f"Battery: {percent}%")
                except:
                    pass
            
            # Auto-dismiss if charger is connected
            if power_plugged:
                self._dismiss()
                return
            
            # Schedule next check
            if self._window and self._is_open:
                self._check_timer = self._window.after(2000, check)
        
        # Start checking
        if self._window:
            self._check_timer = self._window.after(2000, check)
    
    def _dismiss(self):
        """Properly dismiss the dialog"""
        self._dismissed = True
        self._is_open = False
        
        if self._check_timer and self._window:
            try:
                self._window.after_cancel(self._check_timer)
            except:
                pass
        
        if self._window:
            try:
                self._window.grab_release()
                self._window.destroy()
            except:
                pass
            self._window = None
        
        if self._on_dismissed:
            self._on_dismissed()
    
    def close(self):
        """Force close the dialog (only for cleanup)"""
        self._dismiss()
    
    @property
    def was_dismissed(self):
        """Check if dialog was properly dismissed"""
        return self._dismissed
    
    @property
    def is_open(self):
        """Check if dialog is currently open"""
        return self._is_open


class ChargeLimitDialog:
    """
    A notification dialog for charge limit reached.
    - Always on top
    - Can be dismissed by clicking "OK" or unplugging
    - Shows charge limit warning
    """
    
    def __init__(self, percent, limit, on_dismissed=None):
        """
        Initialize charge limit dialog
        
        Args:
            percent: Current battery percentage
            limit: Configured charge limit
            on_dismissed: Callback when dialog is dismissed
        """
        self._percent = percent
        self._limit = limit
        self._on_dismissed = on_dismissed
        self._window = None
        self._is_open = False
    
    def show(self):
        """Show the charge limit dialog"""
        if self._is_open:
            return
        
        self._is_open = True
        self._create_window()
    
    def _create_window(self):
        """Create the charge limit dialog"""
        self._window = tk.Tk()
        self._window.title("Charge Limit Reached")
        
        # Get screen dimensions
        screen_width = self._window.winfo_screenwidth()
        screen_height = self._window.winfo_screenheight()
        
        # Window size
        window_width = 400
        window_height = 250
        
        # Center the window
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self._window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self._window.attributes('-topmost', True)
        self._window.resizable(False, False)
        
        # Handle close
        self._window.protocol("WM_DELETE_WINDOW", self._dismiss)
        
        # Green/yellow background for charge notification
        self._window.configure(bg='#1a2d1a')
        
        # Main container
        main_frame = tk.Frame(self._window, bg='#1a2d1a', padx=30, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        # Icon
        icon_label = tk.Label(
            main_frame,
            text="🔋",
            font=('Segoe UI Emoji', 36),
            bg='#1a2d1a'
        )
        icon_label.pack(pady=(10, 5))
        
        # Title
        title_label = tk.Label(
            main_frame,
            text="Charge Limit Reached",
            font=('Segoe UI', 18, 'bold'),
            bg='#1a2d1a',
            fg='#88ff88'
        )
        title_label.pack(pady=(0, 10))
        
        # Message
        message = f"Battery is at {self._percent}%.\n" \
                  f"You set a limit of {self._limit}%.\n\n" \
                  f"Please unplug the charger to protect battery health."
        
        body_label = tk.Label(
            main_frame,
            text=message,
            font=('Segoe UI', 11),
            bg='#1a2d1a',
            fg='#cccccc',
            justify='center'
        )
        body_label.pack(pady=(0, 15))
        
        # OK button
        ok_button = tk.Button(
            main_frame,
            text="OK, I'll unplug",
            font=('Segoe UI', 11),
            bg='#3d5c3d',
            fg='#ffffff',
            activebackground='#4d6c4d',
            activeforeground='#ffffff',
            padx=20,
            pady=8,
            cursor='hand2',
            command=self._dismiss
        )
        ok_button.pack()
        
        # Bind Enter key
        self._window.bind('<Return>', lambda e: self._dismiss())
        self._window.bind('<Escape>', lambda e: self._dismiss())
        
        # Focus
        self._window.focus_force()
        
        # Start main loop
        self._window.mainloop()
    
    def _dismiss(self):
        """Dismiss the dialog"""
        self._is_open = False
        
        if self._window:
            try:
                self._window.destroy()
            except:
                pass
            self._window = None
        
        if self._on_dismissed:
            self._on_dismissed()
    
    def close(self):
        """Close the dialog"""
        self._dismiss()


# Test the dialogs
if __name__ == "__main__":
    print("Critical Battery Dialog Test")
    print("=" * 50)
    
    # Mock state
    test_state = {'percent': 15, 'plugged': False}
    
    def get_state():
        return (test_state['percent'], test_state['plugged'])
    
    def on_dismissed():
        print("Dialog was dismissed!")
    
    print("\nShowing Critical Battery Dialog...")
    print("(Press 'c' in console to simulate charger connection)")
    
    # Simulate charger connection after 5 seconds
    def simulate_charger():
        time.sleep(5)
        print("\n[Simulating charger connection...]")
        test_state['plugged'] = True
    
    # Start simulation in background
    sim_thread = threading.Thread(target=simulate_charger, daemon=True)
    sim_thread.start()
    
    # Show dialog
    dialog = CriticalBatteryDialog(get_state, on_dismissed)
    dialog.show()
    
    print("\nTest complete!")
