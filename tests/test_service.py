from pathlib import Path

from filelayer import LocalFileProvider, StorageService, StorageSettings


def test_storage_service_text_and_bytes(tmp_path: Path) -> None:
    settings = StorageSettings(
        STORAGE_PROVIDER="local",
        LOCAL_STORAGE_BASE_PATH=str(tmp_path),
        STORAGE_DEFAULT_PREFIX="svc",
    )
    provider = LocalFileProvider(settings)
    service = StorageService(provider)

    service.write_file("notes/test.txt", "service text")
    assert service.read_file("notes/test.txt") == "service text"

    service.write_file_bytes("notes/test.bin", b"abc")
    assert service.read_file_bytes("notes/test.bin") == b"abc"

    assert service.exists("notes/test.txt") is True
    assert service.exists("notes/test.bin") is True
    assert service.exists("notes/missing.txt") is False
