from scripts.configure_vedastro_secret import update_env_text


def test_update_env_text_adds_and_replaces_vedastro_settings():
    text = "VEDASTRO_API_ENDPOINT=https://old.example/api\nOTHER=value\n"
    updated = update_env_text(
        text,
        {
            "VEDASTRO_API_KEY": "sample-secret",
            "VEDASTRO_API_ENDPOINT": "https://api.vedastro.org/api",
            "VEDASTRO_ENABLE_NETWORK": "1",
        },
    )
    assert "VEDASTRO_API_ENDPOINT=https://api.vedastro.org/api" in updated
    assert "VEDASTRO_API_KEY=sample-secret" in updated
    assert "VEDASTRO_ENABLE_NETWORK=1" in updated
    assert "OTHER=value" in updated
    assert "https://old.example/api" not in updated
