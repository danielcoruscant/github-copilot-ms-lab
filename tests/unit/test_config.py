from app.core.config import Settings


def test_settings_have_safe_development_defaults() -> None:
    settings = Settings(_env_file=None)

    assert settings.app_name == "ms-cadastro-funcionario"
    assert settings.app_port == 8000
    assert settings.mongo_database == "technova_funcionarios"
