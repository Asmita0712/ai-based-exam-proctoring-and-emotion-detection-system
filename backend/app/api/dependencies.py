"""
Shared FastAPI dependencies (e.g. settings injection).

Kept separate from routes so route files stay thin per RULE 3.
"""
from app.core.config import Settings, get_settings
from fastapi import Depends
from typing import Annotated

SettingsDep = Annotated[Settings, Depends(get_settings)]
