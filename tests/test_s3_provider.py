from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from filelayer import (
    S3FileProvider,
    StorageObjectNotFoundError,
    StorageReadError,
    StorageSettings,
    StorageWriteError,
)
from filelayer.exceptions import StorageConfigurationError


@pytest.fixture
def s3_settings() -> StorageSettings:
    return StorageSettings(
        STORAGE_PROVIDER="s3",
        STORAGE_DEFAULT_PREFIX="test-prefix",
        STORAGE_ENCODING="utf-8",
        S3_ENDPOINT_URL="https://s3.example.com",
        S3_ACCESS_KEY_ID="fake-key",
        S3_SECRET_ACCESS_KEY="fake-secret",
        S3_BUCKET="test-bucket",
        S3_REGION_NAME="us-east-1",
    )


@pytest.fixture
def mock_client() -> MagicMock:
    return MagicMock()


@pytest.fixture
def provider(s3_settings: StorageSettings, mock_client: MagicMock) -> S3FileProvider:
    with patch("filelayer.providers.s3.boto3") as mock_boto3:
        mock_boto3.client.return_value = mock_client
        return S3FileProvider(s3_settings)


class TestS3ProviderInit:
    def test_wrong_provider_raises(self) -> None:
        settings = StorageSettings(
            STORAGE_PROVIDER="local",
            LOCAL_STORAGE_BASE_PATH="/tmp/test",
        )
        with (
            pytest.raises(StorageConfigurationError, match="STORAGE_PROVIDER=s3"),
            patch("filelayer.providers.s3.boto3"),
        ):
            S3FileProvider(settings)

    def test_missing_bucket_raises(self) -> None:
        with pytest.raises(StorageConfigurationError, match="Missing required S3 settings"):
            StorageSettings(
                STORAGE_PROVIDER="s3",
                S3_ACCESS_KEY_ID="key",
                S3_SECRET_ACCESS_KEY="secret",
                S3_BUCKET="",
            )


class TestNormalizeFilepath:
    def test_basic_path_with_prefix(self, provider: S3FileProvider) -> None:
        assert provider._normalize_filepath("docs/file.txt") == "test-prefix/docs/file.txt"

    def test_strips_leading_slash(self, provider: S3FileProvider) -> None:
        assert provider._normalize_filepath("/docs/file.txt") == "test-prefix/docs/file.txt"

    def test_rejects_path_traversal(self, provider: S3FileProvider) -> None:
        with pytest.raises(StorageConfigurationError, match="Invalid filepath"):
            provider._normalize_filepath("../escape.txt")

    def test_rejects_double_dot_in_middle(self, provider: S3FileProvider) -> None:
        with pytest.raises(StorageConfigurationError, match="Invalid filepath"):
            provider._normalize_filepath("foo/../../bar.txt")

    def test_empty_path_with_prefix(self, provider: S3FileProvider) -> None:
        assert provider._normalize_filepath("") == "test-prefix"

    def test_empty_path_without_prefix_raises(
        self, s3_settings: StorageSettings, mock_client: MagicMock
    ) -> None:
        s3_settings.default_prefix = ""
        with patch("filelayer.providers.s3.boto3") as mock_boto3:
            mock_boto3.client.return_value = mock_client
            provider = S3FileProvider(s3_settings)
        with pytest.raises(ValueError, match="filepath must not be empty"):
            provider._normalize_filepath("")


class TestReadFile:
    def test_read_text(self, provider: S3FileProvider, mock_client: MagicMock) -> None:
        body_mock = MagicMock()
        body_mock.read.return_value = b"hello world"
        mock_client.get_object.return_value = {"Body": body_mock}

        result = provider.read_file("docs/test.txt")

        assert result == "hello world"
        mock_client.get_object.assert_called_once_with(
            Bucket="test-bucket", Key="test-prefix/docs/test.txt"
        )

    def test_read_missing_file_raises(
        self, provider: S3FileProvider, mock_client: MagicMock
    ) -> None:
        error_response = {"Error": {"Code": "NoSuchKey", "Message": "Not found"}}
        mock_client.get_object.side_effect = ClientError(error_response, "GetObject")

        with pytest.raises(StorageObjectNotFoundError, match="not found"):
            provider.read_file("missing.txt")

    def test_read_404_raises(self, provider: S3FileProvider, mock_client: MagicMock) -> None:
        error_response = {"Error": {"Code": "404", "Message": "Not found"}}
        mock_client.get_object.side_effect = ClientError(error_response, "GetObject")

        with pytest.raises(StorageObjectNotFoundError):
            provider.read_file("missing.txt")

    def test_read_client_error_raises_read_error(
        self, provider: S3FileProvider, mock_client: MagicMock
    ) -> None:
        error_response = {"Error": {"Code": "403", "Message": "Forbidden"}}
        mock_client.get_object.side_effect = ClientError(error_response, "GetObject")

        with pytest.raises(StorageReadError, match="Failed to read"):
            provider.read_file("forbidden.txt")

    def test_read_decode_error_raises(
        self, provider: S3FileProvider, mock_client: MagicMock
    ) -> None:
        body_mock = MagicMock()
        body_mock.read.return_value = b"\xff\xfe"
        mock_client.get_object.return_value = {"Body": body_mock}
        provider.settings.encoding = "ascii"

        with pytest.raises(StorageReadError, match="Failed to decode"):
            provider.read_file("binary.txt")


class TestWriteFile:
    def test_write_text(self, provider: S3FileProvider, mock_client: MagicMock) -> None:
        provider.write_file("docs/test.txt", "hello world")

        mock_client.put_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="test-prefix/docs/test.txt",
            Body=b"hello world",
            ContentType="text/plain; charset=utf-8",
        )

    def test_write_client_error_raises(
        self, provider: S3FileProvider, mock_client: MagicMock
    ) -> None:
        mock_client.put_object.side_effect = Exception("Connection failed")

        with pytest.raises(StorageWriteError, match="Failed to write"):
            provider.write_file("docs/test.txt", "content")


class TestReadFileBytes:
    def test_read_bytes(self, provider: S3FileProvider, mock_client: MagicMock) -> None:
        body_mock = MagicMock()
        body_mock.read.return_value = b"\x00\x01\x02"
        mock_client.get_object.return_value = {"Body": body_mock}

        result = provider.read_file_bytes("data.bin")

        assert result == b"\x00\x01\x02"

    def test_read_bytes_missing_raises(
        self, provider: S3FileProvider, mock_client: MagicMock
    ) -> None:
        error_response = {"Error": {"Code": "NoSuchKey", "Message": "Not found"}}
        mock_client.get_object.side_effect = ClientError(error_response, "GetObject")

        with pytest.raises(StorageObjectNotFoundError):
            provider.read_file_bytes("missing.bin")


class TestWriteFileBytes:
    def test_write_bytes(self, provider: S3FileProvider, mock_client: MagicMock) -> None:
        provider.write_file_bytes("data.bin", b"\x00\x01\x02")

        mock_client.put_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="test-prefix/data.bin",
            Body=b"\x00\x01\x02",
            ContentType="application/octet-stream",
        )

    def test_write_bytes_error_raises(
        self, provider: S3FileProvider, mock_client: MagicMock
    ) -> None:
        mock_client.put_object.side_effect = Exception("Network error")

        with pytest.raises(StorageWriteError):
            provider.write_file_bytes("data.bin", b"\x00")


class TestExists:
    def test_exists_true(self, provider: S3FileProvider, mock_client: MagicMock) -> None:
        mock_client.head_object.return_value = {}

        assert provider.exists("docs/test.txt") is True

    def test_exists_false(self, provider: S3FileProvider, mock_client: MagicMock) -> None:
        error_response = {"Error": {"Code": "404", "Message": "Not found"}}
        mock_client.head_object.side_effect = ClientError(error_response, "HeadObject")

        assert provider.exists("missing.txt") is False

    def test_exists_other_error_raises(
        self, provider: S3FileProvider, mock_client: MagicMock
    ) -> None:
        error_response = {"Error": {"Code": "403", "Message": "Forbidden"}}
        mock_client.head_object.side_effect = ClientError(error_response, "HeadObject")

        with pytest.raises(StorageReadError):
            provider.exists("forbidden.txt")
