"""Unit test for settings loading (RULE 10/11: config must be centralized)."""
from backend.app.core.config import get_settings


def test_settings_load():
    settings = get_settings()
    assert settings.app_name
    assert 0.0 <= settings.suspicion_flag_threshold <= 1.0
