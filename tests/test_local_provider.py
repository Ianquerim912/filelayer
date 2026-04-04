from pathlib import Path

import pytest

from filelayer import LocalFileProvider, StorageObjectNotFoundError, StorageSettings


@pytest.fixture
def local_settings(tmp_path: Path) -> StorageSettings:
    return StorageSettings(
        STORAGE_PROVIDER="local",
        LOCAL_STORAGE_BASE_PATH=str(tmp_path),
        STORAGE_DEFAULT_PREFIX="test-prefix",
        STORAGE_ENCODING="utf-8",
    )


def test_write_and_read_text(local_settings: StorageSettings) -> None:
    provider = LocalFileProvider(local_settings)

    provider.write_file("docs/hello.txt", "hello world")

    assert provider.exists("docs/hello.txt") is True
    assert provider.read_file("docs/hello.txt") == "hello world"


def test_write_and_read_bytes(local_settings: StorageSettings) -> None:
    provider = LocalFileProvider(local_settings)

    provider.write_file_bytes("bin/data.bin", b"\x00\x01\x02")

    assert provider.exists("bin/data.bin") is True
    assert provider.read_file_bytes("bin/data.bin") == b"\x00\x01\x02"


def test_missing_file_raises(local_settings: StorageSettings) -> None:
    provider = LocalFileProvider(local_settings)

    with pytest.raises(StorageObjectNotFoundError):
        provider.read_file("missing/file.txt")


def test_path_traversal_is_blocked(local_settings: StorageSettings) -> None:
    provider = LocalFileProvider(local_settings)

    with pytest.raises(Exception):
        provider.write_file("../escape.txt", "nope")
