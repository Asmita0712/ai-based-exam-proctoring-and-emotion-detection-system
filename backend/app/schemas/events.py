"""
Pydantic schemas for browser/window events (tab-switch, focus/blur).

Mirrors the event schema used by src/frontend tab tracking (Phase 1),
kept framework-independent per the architecture rules.
"""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel

EventType = Literal["tab_hidden", "tab_visible", "window_blur", "window_focus"]


class BrowserEvent(BaseModel):
    session_id: str
    type: EventType
    timestamp: datetime
