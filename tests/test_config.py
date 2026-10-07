import pytest
from pydantic import ValidationError

from app.config import Settings


def test_env_file_loaded(tmp_path, monkeypatch):
    monkeypatch.delenv("TEACHEROS_LLM_PROVIDER", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("TEACHEROS_LLM_PROVIDER=openai\n", encoding="utf-8")
    settings = Settings(_env_file=env_file)
    assert settings.llm_provider == "openai"


def test_default_env_file_path():
    assert Settings.model_config["env_file"] == ".env"
    assert Settings.model_config["env_file_encoding"] == "utf-8"


def test_settings_rejects_unknown_llm_provider():
    with pytest.raises(ValidationError):
        Settings(llm_provider="anthropic", _env_file=None)


def test_get_provider_selection(monkeypatch):
    from app.config import settings
    from app.services.llm.provider import get_provider

    monkeypatch.setattr(settings, "llm_provider", "openai")
    monkeypatch.setattr(settings, "llm_api_key", "")
    assert get_provider().name == "mock"

    monkeypatch.setattr(settings, "llm_api_key", "sk-test")
    assert get_provider().name == "openai"

    monkeypatch.setattr(settings, "llm_provider", "mock")
    monkeypatch.setattr(settings, "llm_api_key", "")
    assert get_provider().name == "mock"
