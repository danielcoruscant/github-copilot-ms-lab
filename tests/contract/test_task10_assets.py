from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[2]


def test_container_assets_are_present_and_use_expected_commands() -> None:
    dockerfile = (PROJECT_ROOT / "Dockerfile").read_text()
    dockerfile_dev = (PROJECT_ROOT / "Dockerfile.dev").read_text()
    compose = (PROJECT_ROOT / "compose.yaml").read_text()

    assert "FROM python:3.12-slim" in dockerfile
    assert "USER appuser" in dockerfile
    assert '"uvicorn", "app.main:app"' in dockerfile
    assert "--reload" in dockerfile_dev
    assert "mongodb:" in compose
    assert "healthcheck:" in compose
    assert "condition: service_healthy" in compose
    assert "mongodb_data:" in compose


def test_documentation_covers_local_docker_and_debug_setup() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text()
    technical = (PROJECT_ROOT / "docs" / "technical.md").read_text()

    for text in (readme, technical):
        assert "docker compose" in text
        assert "uvicorn" in text
        assert "debug" in text.lower()
        assert "pytest" in text
