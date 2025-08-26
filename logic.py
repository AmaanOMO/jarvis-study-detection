import time
from typing import Optional, Dict, Any

class FocusLogic:
    def __init__(self, away_hold_s: float = 0.6, cooldown_s: float = 2.0):
        """
        Initialize focus logic with timing parameters.
        
        Args:
            away_hold_s: Time in seconds user must be away before triggering roast
            cooldown_s: Cooldown between roasts in seconds
        """
        self.away_hold_s = away_hold_s
        self.cooldown_s = cooldown_s
        
        # State variables
        self.away_start_ts: Optional[float] = None
        self.last_roast_ts: Optional[float] = None
        self.active: bool = True
        self.current_status: str = 'LOOKING'
        
        # Event tracking
        self.events: list = []
    
    def update(self, is_away_now: bool) -> Optional[str]:
        """
        Update logic with current gaze status.
        
        Args:
            is_away_now: True if user is currently away, False if looking
            
        Returns:
            'ROAST' if roast should be triggered, None otherwise
        """
        current_time = time.time()
        
        # Update current status
        self.current_status = 'AWAY' if is_away_now else 'LOOKING'
        
        if is_away_now:
            # User is away
            if self.away_start_ts is None:
                # Just started being away
                self.away_start_ts = current_time
                self._log_event('away_start', 'User started looking away')
                print(f"🔴 Started looking away at {current_time:.1f}")
            
            # Check if away long enough to trigger roast
            if (self.away_start_ts is not None and 
                current_time - self.away_start_ts >= self.away_hold_s):
                
                # Check cooldown
                if (self.last_roast_ts is None or 
                    current_time - self.last_roast_ts >= self.cooldown_s):
                    
                    # Trigger roast
                    self.last_roast_ts = current_time
                    self._log_event('roast', 'Roast triggered after away hold')
                    print(f"🎤 ROAST TRIGGERED after {current_time - self.away_start_ts:.1f}s away!")
                    return 'ROAST'
                else:
                    cooldown_remaining = self.cooldown_s - (current_time - self.last_roast_ts)
                    print(f"⏳ Cooldown active, {cooldown_remaining:.1f}s remaining")
        else:
            # User is looking
            if self.away_start_ts is not None:
                # Just returned to looking
                away_duration = current_time - self.away_start_ts
                self.away_start_ts = None
                self._log_event('looking_return', f'User returned after {away_duration:.2f}s away')
                print(f"🟢 Returned to looking after {away_duration:.1f}s away")
        
        return None
    
    def toggle_active(self) -> bool:
        """Toggle active state and return new state."""
        self.active = not self.active
        status = 'active' if self.active else 'inactive'
        self._log_event('toggle', f'System toggled {status}')
        return self.active
    
    def reset_cooldown(self):
        """Reset cooldown timer."""
        self.last_roast_ts = None
        self._log_event('reset', 'Cooldown reset')
    
    def is_active(self) -> bool:
        """Check if system is currently active."""
        return self.active
    
    def get_status(self) -> str:
        """Get current gaze status."""
        return self.current_status
    
    def get_away_duration(self) -> float:
        """Get how long user has been away (0 if not away)."""
        if self.away_start_ts is None:
            return 0.0
        return time.time() - self.away_start_ts
    
    def get_time_since_last_roast(self) -> float:
        """Get time since last roast (0 if never roasted)."""
        if self.last_roast_ts is None:
            return 0.0
        return time.time() - self.last_roast_ts
    
    def _log_event(self, event_type: str, message: str):
        """Log an event for debugging."""
        self.events.append({
            'timestamp': time.time(),
            'event': event_type,
            'message': message,
            'status': self.current_status
        })
    
    def get_events(self) -> list:
        """Get list of recent events."""
        return self.events.copy()
    
    def clear_events(self):
        """Clear event history."""
        self.events.clear()
