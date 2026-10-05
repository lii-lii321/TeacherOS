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
