from __future__ import annotations

from tcia_cohort_forge.config import Settings


def test_settings_defaults():
    s = Settings()
    assert s.api_base_url == "https://nbia.cancerimagingarchive.net/nbia-api/services/v4"
    assert s.auth_token is None
    assert s.output_dir == "downloads"
    assert s.request_timeout == 60


def test_get_api_url():
    s = Settings(api_base_url="https://test.example.com/api")
    url = s.get_api_url("getCollectionValues")
    assert url == "https://test.example.com/api/getCollectionValues"


def test_get_api_url_trailing_slash():
    s = Settings(api_base_url="https://test.example.com/api/")
    url = s.get_api_url("getCollectionValues")
    assert url == "https://test.example.com/api/getCollectionValues"


def test_from_env(monkeypatch):
    monkeypatch.setenv("TCIA_API_BASE_URL", "https://custom.example.com/api")
    monkeypatch.setenv("TCIA_AUTH_TOKEN", "test-token-123")
    monkeypatch.setenv("TCIA_OUTPUT_DIR", "/custom/output")
    monkeypatch.setenv("TCIA_TIMEOUT", "120")

    s = Settings.from_env()
    assert s.api_base_url == "https://custom.example.com/api"
    assert s.auth_token == "test-token-123"
    assert s.output_dir == "/custom/output"
    assert s.request_timeout == 120
