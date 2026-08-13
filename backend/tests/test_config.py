from app.core.config import Settings


def test_image_ai_is_disabled_by_default() -> None:
    settings = Settings(_env_file=None)

    assert settings.image_ai_provider == "disabled"
    assert settings.openai_api_key is None
    assert settings.image_ai_model == "gpt-image-2"
    assert settings.image_ai_size == "1024x1536"
    assert settings.image_ai_quality == "medium"
    assert settings.image_ai_timeout_seconds == 120.0
    assert settings.image_ai_daily_limit_per_user == 2
    assert settings.image_ai_daily_limit_global == 5


def test_openai_key_is_separate_from_claude_key(monkeypatch) -> None:
    monkeypatch.setenv("AI_API_KEY", "claude-test-key")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-test-key")
    monkeypatch.setenv("IMAGE_AI_PROVIDER", "openai")

    settings = Settings(_env_file=None)

    assert settings.ai_api_key == "claude-test-key"
    assert settings.openai_api_key == "openai-test-key"
    assert settings.image_ai_provider == "openai"
