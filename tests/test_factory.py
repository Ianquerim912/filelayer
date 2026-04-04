from pathlib import Path

from filelayer import LocalFileProvider, StorageSettings, create_file_provider


def test_create_local_provider(tmp_path: Path) -> None:
    settings = StorageSettings(
        STORAGE_PROVIDER="local",
        LOCAL_STORAGE_BASE_PATH=str(tmp_path),
    )

    provider = create_file_provider(settings)

    assert isinstance(provider, LocalFileProvider)
