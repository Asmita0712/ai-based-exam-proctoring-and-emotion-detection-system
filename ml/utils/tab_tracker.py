"""
Browser Tab and Window focus tracking module.

Adheres to:
- RULE 4: Clean reusable interface
- RULE 6: Timestamped / window-level feature representation
- Tracks: visibilitychange, blur, focus, switch counts, and total time away
"""
from datetime import datetime
import time
from typing import Any, Dict, List, Optional


class TabTracker:
    """Tracks tab visibility and window focus state, switch counts, and time away."""

    def __init__(self) -> None:
        self.tab_hidden: bool = False
        self.window_blur: bool = False
        self.switch_count: int = 0
        self.total_time_away: float = 0.0
        self._away_start: Optional[float] = None
        self.events: List[Dict[str, Any]] = []

    def record_event(self, event_type: str, timestamp: Optional[float] = None) -> Dict[str, Any]:
        """
        Records a browser event ('tab_hidden', 'tab_visible', 'window_blur', 'window_focus').

        Args:
            event_type: One of the 4 supported browser event types.
            timestamp: Unix epoch timestamp in seconds (defaults to time.time()).

        Returns:
            Current tracker status dictionary.
        """
        now = timestamp if timestamp is not None else time.time()
        was_away = self.tab_hidden or self.window_blur

        if event_type == "tab_hidden":
            self.tab_hidden = True
        elif event_type == "tab_visible":
            self.tab_hidden = False
        elif event_type == "window_blur":
            self.window_blur = True
        elif event_type == "window_focus":
            self.window_blur = False

        is_now_away = self.tab_hidden or self.window_blur

        # Transition: active -> away
        if not was_away and is_now_away:
            self.switch_count += 1
            self._away_start = now

        # Transition: away -> active
        elif was_away and not is_now_away:
            if self._away_start is not None:
                self.total_time_away += max(0.0, now - self._away_start)
                self._away_start = None

        self.events.append({
            "type": event_type,
            "timestamp": now,
        })

        return self.get_status(now)

    def get_status(self, current_time: Optional[float] = None) -> Dict[str, Any]:
        """
        Returns the current aggregated browser state.
        """
        now = current_time if current_time is not None else time.time()
        active_away = 0.0
        if self._away_start is not None:
            active_away = max(0.0, now - self._away_start)

        total_away = self.total_time_away + active_away

        return {
            "tab_hidden": self.tab_hidden,
            "window_blur": self.window_blur,
            "switch_count": self.switch_count,
            "total_time_away_seconds": round(total_away, 2),
            "is_away": self.tab_hidden or self.window_blur,
        }

    def reset(self) -> None:
        """Resets all tracking states."""
        self.tab_hidden = False
        self.window_blur = False
        self.switch_count = 0
        self.total_time_away = 0.0
        self._away_start = None
        self.events.clear()
