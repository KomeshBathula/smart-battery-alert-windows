"""
Smart Battery Alert for Windows
Usage Statistics - Tracks and analyzes battery usage patterns
"""

import json
import os
from datetime import datetime, timedelta
from collections import defaultdict


class UsageStats:
    """Tracks and analyzes battery usage patterns"""
    
    def __init__(self, stats_file="battery_stats.json"):
        self.stats_file = stats_file
        self.stats = self.load_stats()
        
        # Session tracking
        self.session_start = datetime.now()
        self.session_samples = []
        
    def load_stats(self):
        """Load statistics from file"""
        default_stats = {
            'daily_usage': {},  # Date -> usage data
            'weekly_summaries': {},  # Week -> summary
            'charge_sessions': [],  # List of charge sessions
            'discharge_sessions': [],  # List of discharge sessions
            'total_screen_on_time': 0,  # Total hours
            'average_daily_drain': 0,
            'average_charge_time': 0,
            'last_updated': None
        }
        
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r') as f:
                    loaded = json.load(f)
                    default_stats.update(loaded)
            except Exception as e:
                print(f"Error loading stats: {e}")
        
        return default_stats
    
    def save_stats(self):
        """Save statistics to file"""
        self.stats['last_updated'] = datetime.now().isoformat()
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            print(f"Error saving stats: {e}")
    
    def record_sample(self, percent, power_plugged, timestamp=None):
        """Record a battery sample"""
        if timestamp is None:
            timestamp = datetime.now()
        
        sample = {
            'percent': percent,
            'power_plugged': power_plugged,
            'timestamp': timestamp.isoformat()
        }
        
        self.session_samples.append(sample)
        
        # Update daily usage
        date_key = timestamp.strftime('%Y-%m-%d')
        if date_key not in self.stats['daily_usage']:
            self.stats['daily_usage'][date_key] = {
                'samples': [],
                'min_percent': 100,
                'max_percent': 0,
                'time_on_battery': 0,
                'time_charging': 0,
                'charge_cycles': 0
            }
        
        day_stats = self.stats['daily_usage'][date_key]
        day_stats['samples'].append(sample)
        day_stats['min_percent'] = min(day_stats['min_percent'], percent)
        day_stats['max_percent'] = max(day_stats['max_percent'], percent)
        
        # Periodically save
        if len(self.session_samples) % 10 == 0:
            self.save_stats()
    
    def record_charge_session(self, start_percent, end_percent, duration_minutes):
        """Record a charging session"""
        session = {
            'start_percent': start_percent,
            'end_percent': end_percent,
            'duration_minutes': duration_minutes,
            'timestamp': datetime.now().isoformat(),
            'percent_gained': end_percent - start_percent
        }
        
        self.stats['charge_sessions'].append(session)
        
        # Keep only last 100 sessions
        if len(self.stats['charge_sessions']) > 100:
            self.stats['charge_sessions'] = self.stats['charge_sessions'][-100:]
        
        # Update average charge time
        self._update_averages()
        self.save_stats()
    
    def record_discharge_session(self, start_percent, end_percent, duration_minutes):
        """Record a discharging session"""
        session = {
            'start_percent': start_percent,
            'end_percent': end_percent,
            'duration_minutes': duration_minutes,
            'timestamp': datetime.now().isoformat(),
            'percent_lost': start_percent - end_percent
        }
        
        self.stats['discharge_sessions'].append(session)
        
        # Keep only last 100 sessions
        if len(self.stats['discharge_sessions']) > 100:
            self.stats['discharge_sessions'] = self.stats['discharge_sessions'][-100:]
        
        self._update_averages()
        self.save_stats()
    
    def _update_averages(self):
        """Update average statistics"""
        # Average charge time
        if self.stats['charge_sessions']:
            total_charge_time = sum(s['duration_minutes'] for s in self.stats['charge_sessions'])
            self.stats['average_charge_time'] = total_charge_time / len(self.stats['charge_sessions'])
        
        # Average daily drain
        if self.stats['discharge_sessions']:
            total_drain = sum(s['percent_lost'] for s in self.stats['discharge_sessions'])
            self.stats['average_daily_drain'] = total_drain / len(self.stats['discharge_sessions'])
    
    def get_today_stats(self):
        """Get statistics for today"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        if today in self.stats['daily_usage']:
            return self.stats['daily_usage'][today]
        
        return {
            'min_percent': None,
            'max_percent': None,
            'time_on_battery': 0,
            'time_charging': 0,
            'samples': []
        }
    
    def get_weekly_stats(self):
        """Get statistics for the past 7 days"""
        weekly = {
            'days': [],
            'average_min': 0,
            'average_max': 0,
            'total_charge_sessions': 0,
            'total_discharge_sessions': 0
        }
        
        today = datetime.now()
        min_values = []
        max_values = []
        
        for i in range(7):
            date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
            if date in self.stats['daily_usage']:
                day_stats = self.stats['daily_usage'][date]
                weekly['days'].append({
                    'date': date,
                    'min_percent': day_stats['min_percent'],
                    'max_percent': day_stats['max_percent']
                })
                min_values.append(day_stats['min_percent'])
                max_values.append(day_stats['max_percent'])
        
        if min_values:
            weekly['average_min'] = sum(min_values) / len(min_values)
        if max_values:
            weekly['average_max'] = sum(max_values) / len(max_values)
        
        return weekly
    
    def get_battery_usage_summary(self):
        """Get a comprehensive battery usage summary"""
        today_stats = self.get_today_stats()
        weekly_stats = self.get_weekly_stats()
        
        # Calculate screen time estimate (rough based on samples)
        session_hours = (datetime.now() - self.session_start).total_seconds() / 3600
        
        summary = {
            'today': {
                'min_battery': today_stats.get('min_percent'),
                'max_battery': today_stats.get('max_percent'),
                'samples_recorded': len(today_stats.get('samples', []))
            },
            'weekly': {
                'average_low': round(weekly_stats['average_min'], 1),
                'average_high': round(weekly_stats['average_max'], 1),
                'days_tracked': len(weekly_stats['days'])
            },
            'session': {
                'duration_hours': round(session_hours, 2),
                'samples_recorded': len(self.session_samples)
            },
            'averages': {
                'charge_time_minutes': round(self.stats.get('average_charge_time', 0), 1),
                'daily_drain_percent': round(self.stats.get('average_daily_drain', 0), 1)
            },
            'totals': {
                'charge_sessions': len(self.stats['charge_sessions']),
                'discharge_sessions': len(self.stats['discharge_sessions'])
            }
        }
        
        return summary
    
    def get_usage_graph_data(self, days=7):
        """Get data suitable for graphing usage over time"""
        data = []
        today = datetime.now()
        
        for i in range(days - 1, -1, -1):  # Oldest to newest
            date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
            if date in self.stats['daily_usage']:
                day_stats = self.stats['daily_usage'][date]
                data.append({
                    'date': date,
                    'min': day_stats['min_percent'],
                    'max': day_stats['max_percent'],
                    'samples': len(day_stats.get('samples', []))
                })
            else:
                data.append({
                    'date': date,
                    'min': None,
                    'max': None,
                    'samples': 0
                })
        
        return data
    
    def cleanup_old_data(self, keep_days=30):
        """Remove data older than specified days"""
        cutoff = datetime.now() - timedelta(days=keep_days)
        cutoff_str = cutoff.strftime('%Y-%m-%d')
        
        # Clean daily usage
        keys_to_remove = [k for k in self.stats['daily_usage'].keys() if k < cutoff_str]
        for key in keys_to_remove:
            del self.stats['daily_usage'][key]
        
        # Clean sessions
        cutoff_iso = cutoff.isoformat()
        self.stats['charge_sessions'] = [
            s for s in self.stats['charge_sessions'] 
            if s.get('timestamp', '') >= cutoff_iso
        ]
        self.stats['discharge_sessions'] = [
            s for s in self.stats['discharge_sessions'] 
            if s.get('timestamp', '') >= cutoff_iso
        ]
        
        self.save_stats()
        return len(keys_to_remove)
    
    def format_summary_text(self):
        """Format a human-readable summary"""
        summary = self.get_battery_usage_summary()
        
        lines = [
            "Battery Usage Statistics",
            "=" * 40,
            "",
            "Today:",
        ]
        
        if summary['today']['min_battery'] is not None:
            lines.append(f"  Battery range: {summary['today']['min_battery']}% - {summary['today']['max_battery']}%")
        else:
            lines.append("  No data recorded yet")
        
        lines.extend([
            "",
            "This Week:",
            f"  Average low: {summary['weekly']['average_low']}%",
            f"  Average high: {summary['weekly']['average_high']}%",
            f"  Days tracked: {summary['weekly']['days_tracked']}",
            "",
            "Session:",
            f"  Duration: {summary['session']['duration_hours']} hours",
            f"  Samples: {summary['session']['samples_recorded']}",
            "",
            "Averages:",
            f"  Charge time: {summary['averages']['charge_time_minutes']} minutes",
            f"  Daily drain: {summary['averages']['daily_drain_percent']}%",
            "",
            "Totals:",
            f"  Charge sessions: {summary['totals']['charge_sessions']}",
            f"  Discharge sessions: {summary['totals']['discharge_sessions']}"
        ])
        
        return "\n".join(lines)


# Test the usage stats
if __name__ == "__main__":
    import time
    import random
    
    print("Usage Statistics Test")
    print("=" * 50)
    
    stats = UsageStats(stats_file="test_stats.json")
    
    # Simulate some battery samples
    print("\nSimulating battery usage...")
    percent = 80
    plugged = False
    
    for i in range(20):
        # Simulate battery drain/charge
        if plugged:
            percent = min(100, percent + random.randint(1, 3))
            if percent >= 95:
                plugged = False
        else:
            percent = max(10, percent - random.randint(1, 3))
            if percent <= 20:
                plugged = True
        
        stats.record_sample(percent, plugged)
        print(f"  Sample {i+1}: {percent}% {'[Charging]' if plugged else '[Discharging]'}")
    
    # Record some sessions
    stats.record_charge_session(20, 80, 90)
    stats.record_discharge_session(80, 30, 180)
    
    # Print summary
    print("\n" + stats.format_summary_text())
    
    # Cleanup test file
    if os.path.exists("test_stats.json"):
        os.remove("test_stats.json")
    
    print("\nTest complete!")
