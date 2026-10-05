from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "TeacherOS"
    database_url: str = "sqlite+aiosqlite:///./teacheros.db"
    llm_provider: str = "mock"
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"

    model_config = {
        "env_prefix": "TEACHEROS_",
        "extra": "ignore",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()
