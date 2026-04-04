"""Tests for S3FileProvider with ETag-based caching."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from filelayer import S3FileProvider, StorageObjectNotFoundError, StorageSettings


@pytest.fixture
def s3_settings(tmp_path: Path) -> StorageSettings:
    return StorageSettings(
        STORAGE_PROVIDER="s3",
        STORAGE_DEFAULT_PREFIX="pfx",
        S3_ENDPOINT_URL="https://s3.example.com",
        S3_ACCESS_KEY_ID="fake-key",
        S3_SECRET_ACCESS_KEY="fake-secret",
        S3_BUCKET="test-bucket",
        S3_CACHE_ENABLED=True,
        S3_CACHE_DIR=str(tmp_path / "cache"),
    )


@pytest.fixture
def s3_settings_no_cache(tmp_path: Path) -> StorageSettings:
    return StorageSettings(
        STORAGE_PROVIDER="s3",
        STORAGE_DEFAULT_PREFIX="pfx",
        S3_ENDPOINT_URL="https://s3.example.com",
        S3_ACCESS_KEY_ID="fake-key",
        S3_SECRET_ACCESS_KEY="fake-secret",
        S3_BUCKET="test-bucket",
        S3_CACHE_ENABLED=False,
    )


@pytest.fixture
def mock_client() -> MagicMock:
    return MagicMock()


@pytest.fixture
def provider(s3_settings: StorageSettings, mock_client: MagicMock) -> S3FileProvider:
    with patch("filelayer.providers.s3.boto3") as mock_boto3:
        mock_boto3.client.return_value = mock_client
        return S3FileProvider(s3_settings)


@pytest.fixture
def provider_no_cache(
    s3_settings_no_cache: StorageSettings, mock_client: MagicMock
) -> S3FileProvider:
    with patch("filelayer.providers.s3.boto3") as mock_boto3:
        mock_boto3.client.return_value = mock_client
        return S3FileProvider(s3_settings_no_cache)


def _make_get_response(data: bytes, etag: str) -> dict:
    body = MagicMock()
    body.read.return_value = data
    return {"Body": body, "ETag": etag}


class TestCacheOnRead:
    def test_first_read_populates_cache(
        self, provider: S3FileProvider, mock_client: MagicMock
    ) -> None:
        mock_client.get_object.return_value = _make_get_response(b"hello", '"abc123"')

        result = provider.read_file("doc.txt")

        assert result == "hello"
        assert provider.cache is not None
        cached = provider.cache.get("test-bucket", "pfx/doc.txt")
        assert cached is not None
        assert cached == (b"hello", '"abc123"')

    def test_second_read_uses_conditional_get(
        self, provider: S3FileProvider, mock_client: MagicMock
    ) -> None:
        # First read — populate cache
        mock_client.get_object.return_value = _make_get_response(b"hello", '"abc123"')
        provider.read_file("doc.txt")

        # Second read — S3 returns 304 Not Modified
        error_304 = {"Error": {"Code": "304", "Message": "Not Modified"}}
        mock_client.get_object.side_effect = ClientError(error_304, "GetObject")

        result = provider.read_file("doc.txt")

        assert result == "hello"
        # Verify IfNoneMatch was sent
        call_kwargs = mock_client.get_object.call_args_list[-1][1]
        assert call_kwargs.get("IfNoneMatch") == '"abc123"'

    def test_second_read_with_changed_content(
        self, provider: S3FileProvider, mock_client: MagicMock
    ) -> None:
        # First read
        mock_client.get_object.return_value = _make_get_response(b"v1", '"etag-v1"')
        provider.read_file("doc.txt")

        # Second read — content changed, S3 returns new content
        mock_client.get_object.return_value = _make_get_response(b"v2", '"etag-v2"')
        result = provider.read_file("doc.txt")

        assert result == "v2"
        assert provider.cache is not None
        cached = provider.cache.get("test-bucket", "pfx/doc.txt")
        assert cached is not None
        assert cached == (b"v2", '"etag-v2"')

    def test_read_bytes_uses_cache(self, provider: S3FileProvider, mock_client: MagicMock) -> None:
        mock_client.get_object.return_value = _make_get_response(b"\x00\x01", '"bin-etag"')
        provider.read_file_bytes("data.bin")

        error_304 = {"Error": {"Code": "304", "Message": "Not Modified"}}
        mock_client.get_object.side_effect = ClientError(error_304, "GetObject")

        result = provider.read_file_bytes("data.bin")
        assert result == b"\x00\x01"


class TestWriteThrough:
    def test_write_file_populates_cache(
        self, provider: S3FileProvider, mock_client: MagicMock
    ) -> None:
        mock_client.put_object.return_value = {"ETag": '"write-etag"'}

        provider.write_file("doc.txt", "written content")

        assert provider.cache is not None
        cached = provider.cache.get("test-bucket", "pfx/doc.txt")
        assert cached is not None
        assert cached[0] == b"written content"
        assert cached[1] == '"write-etag"'

    def test_write_bytes_populates_cache(
        self, provider: S3FileProvider, mock_client: MagicMock
    ) -> None:
        mock_client.put_object.return_value = {"ETag": '"bin-write-etag"'}

        provider.write_file_bytes("data.bin", b"\xde\xad")

        assert provider.cache is not None
        cached = provider.cache.get("test-bucket", "pfx/data.bin")
        assert cached is not None
        assert cached[0] == b"\xde\xad"

    def test_write_then_read_serves_from_cache(
        self, provider: S3FileProvider, mock_client: MagicMock
    ) -> None:
        mock_client.put_object.return_value = {"ETag": '"wt-etag"'}
        provider.write_file("doc.txt", "cached write")

        # S3 returns 304 on next read — cache serves it
        error_304 = {"Error": {"Code": "304", "Message": "Not Modified"}}
        mock_client.get_object.side_effect = ClientError(error_304, "GetObject")

        result = provider.read_file("doc.txt")
        assert result == "cached write"


class TestCacheDisabled:
    def test_no_cache_when_disabled(
        self, provider_no_cache: S3FileProvider, mock_client: MagicMock
    ) -> None:
        assert provider_no_cache.cache is None

        mock_client.get_object.return_value = _make_get_response(b"hello", '"etag"')
        result = provider_no_cache.read_file("doc.txt")
        assert result == "hello"

        # Second read should NOT send IfNoneMatch
        mock_client.get_object.return_value = _make_get_response(b"hello", '"etag"')
        provider_no_cache.read_file("doc.txt")
        call_kwargs = mock_client.get_object.call_args_list[-1][1]
        assert "IfNoneMatch" not in call_kwargs


class TestCacheEvictionOnNotFound:
    def test_404_evicts_cache(self, provider: S3FileProvider, mock_client: MagicMock) -> None:
        # Populate cache
        mock_client.get_object.return_value = _make_get_response(b"old", '"old-etag"')
        provider.read_file("doc.txt")

        # Object deleted from S3
        error_404 = {"Error": {"Code": "NoSuchKey", "Message": "Not found"}}
        mock_client.get_object.side_effect = ClientError(error_404, "GetObject")

        with pytest.raises(StorageObjectNotFoundError):
            provider.read_file("doc.txt")

        assert provider.cache is not None
        assert provider.cache.get("test-bucket", "pfx/doc.txt") is None
