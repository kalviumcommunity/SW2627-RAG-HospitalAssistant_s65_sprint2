from app.config import EMBEDDING_MODEL, PROJECT_ROOT


def test_application_imports_with_default_settings() -> None:
    assert PROJECT_ROOT.is_dir()
    assert EMBEDDING_MODEL