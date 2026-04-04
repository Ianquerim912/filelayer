from __future__ import annotations

import logging
from pathlib import PurePosixPath
from typing import TYPE_CHECKING

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    ConnectTimeoutError,
    EndpointConnectionError,
)

from ..config import StorageSettings
from ..exceptions import (
    StorageConfigurationError,
    StorageObjectNotFoundError,
    StorageReadError,
    StorageWriteError,
)
from ..logging_utils import StructuredLogger
from .base import FileProvider

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client


class S3FileProvider(FileProvider):
    def __init__(
        self,
        settings: StorageSettings,
        logger: logging.Logger | None = None,
    ) -> None:
        if settings.provider != "s3":
            raise StorageConfigurationError("S3FileProvider requires STORAGE_PROVIDER=s3.")

        self.settings = settings
        if not settings.s3_bucket:
            raise StorageConfigurationError("S3 bucket is not configured.")
        self.bucket: str = settings.s3_bucket

        self.log = StructuredLogger(logger or logging.getLogger(self.__class__.__name__))
        self.client: S3Client = self._build_client()

    def _build_client(self) -> S3Client:
        try:
            boto_config = BotoConfig(
                region_name=self.settings.s3_region_name,
                signature_version="s3v4",
                connect_timeout=self.settings.s3_connect_timeout,
                read_timeout=self.settings.s3_read_timeout,
                retries={
                    "max_attempts": self.settings.s3_max_attempts,
                    "mode": "standard",
                },
                s3={"addressing_style": self.settings.s3_addressing_style},
            )

            return boto3.client(
                "s3",
                endpoint_url=self.settings.s3_endpoint_url,
                aws_access_key_id=self.settings.s3_access_key_id,
                aws_secret_access_key=self.settings.s3_secret_access_key_value,
                aws_session_token=self.settings.s3_session_token_value,
                region_name=self.settings.s3_region_name,
                use_ssl=self.settings.s3_use_ssl,
                verify=self.settings.s3_verify_ssl,
                config=boto_config,
            )
        except Exception as exc:
            raise StorageConfigurationError("Failed to initialize S3 client.") from exc

    def _normalize_filepath(self, filepath: str) -> str:
        clean_path = filepath.replace("\\", "/").strip().lstrip("/")
        path_parts = PurePosixPath(clean_path).parts if clean_path else ()

        if any(part in {".", ".."} for part in path_parts):
            raise StorageConfigurationError(f"Invalid filepath: {filepath}")

        prefix = self.settings.default_prefix

        if not clean_path and not prefix:
            raise ValueError("filepath must not be empty.")

        if prefix and clean_path:
            return f"{prefix}/{clean_path}"
        return clean_path or prefix

    def read_file(self, filepath: str) -> str:
        key = self._normalize_filepath(filepath)

        self.log.info(
            "s3_read_text_started",
            bucket=self.bucket,
            key=key,
            encoding=self.settings.encoding,
        )

        try:
            response = self.client.get_object(Bucket=self.bucket, Key=key)
            body = response["Body"].read()

            if not isinstance(body, bytes):
                raise StorageReadError(f"Unexpected response body for key: {filepath}")

            content = body.decode(self.settings.encoding)

            self.log.info(
                "s3_read_text_completed",
                bucket=self.bucket,
                key=key,
                size_chars=len(content),
            )
            return content

        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")
            if error_code in {"404", "NoSuchKey", "NotFound"}:
                raise StorageObjectNotFoundError(f"S3 object not found: {filepath}") from exc

            self.log.exception(
                "s3_read_text_failed",
                bucket=self.bucket,
                key=key,
                error_code=error_code,
            )
            raise StorageReadError(f"Failed to read S3 object: {filepath}") from exc

        except UnicodeDecodeError as exc:
            self.log.exception(
                "s3_read_text_decode_failed",
                bucket=self.bucket,
                key=key,
                encoding=self.settings.encoding,
            )
            raise StorageReadError(
                f"Failed to decode S3 object '{filepath}' using '{self.settings.encoding}'."
            ) from exc

        except (BotoCoreError, EndpointConnectionError, ConnectTimeoutError) as exc:
            self.log.exception(
                "s3_read_text_failed",
                bucket=self.bucket,
                key=key,
            )
            raise StorageReadError(f"Failed to read S3 object: {filepath}") from exc

    def write_file(self, filepath: str, file_content: str) -> None:
        key = self._normalize_filepath(filepath)

        self.log.info(
            "s3_write_text_started",
            bucket=self.bucket,
            key=key,
            size_chars=len(file_content),
            encoding=self.settings.encoding,
        )

        try:
            body = file_content.encode(self.settings.encoding)
            self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=body,
                ContentType=f"text/plain; charset={self.settings.encoding}",
            )
            self.log.info(
                "s3_write_text_completed",
                bucket=self.bucket,
                key=key,
                size_chars=len(file_content),
            )
        except UnicodeEncodeError as exc:
            self.log.exception(
                "s3_write_text_encode_failed",
                bucket=self.bucket,
                key=key,
                encoding=self.settings.encoding,
            )
            raise StorageWriteError(
                f"Failed to encode S3 object '{filepath}' using '{self.settings.encoding}'."
            ) from exc
        except Exception as exc:
            self.log.exception(
                "s3_write_text_failed",
                bucket=self.bucket,
                key=key,
            )
            raise StorageWriteError(f"Failed to write S3 object: {filepath}") from exc

    def read_file_bytes(self, filepath: str) -> bytes:
        key = self._normalize_filepath(filepath)

        self.log.info(
            "s3_read_bytes_started",
            bucket=self.bucket,
            key=key,
        )

        try:
            response = self.client.get_object(Bucket=self.bucket, Key=key)
            body = response["Body"].read()

            if not isinstance(body, bytes):
                raise StorageReadError(f"Unexpected response body for key: {filepath}")

            self.log.info(
                "s3_read_bytes_completed",
                bucket=self.bucket,
                key=key,
                size_bytes=len(body),
            )
            return body

        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")
            if error_code in {"404", "NoSuchKey", "NotFound"}:
                raise StorageObjectNotFoundError(f"S3 object not found: {filepath}") from exc

            self.log.exception(
                "s3_read_bytes_failed",
                bucket=self.bucket,
                key=key,
                error_code=error_code,
            )
            raise StorageReadError(f"Failed to read S3 object: {filepath}") from exc

        except (BotoCoreError, EndpointConnectionError, ConnectTimeoutError) as exc:
            self.log.exception(
                "s3_read_bytes_failed",
                bucket=self.bucket,
                key=key,
            )
            raise StorageReadError(f"Failed to read S3 object: {filepath}") from exc

    def write_file_bytes(self, filepath: str, file_bytes: bytes) -> None:
        key = self._normalize_filepath(filepath)

        self.log.info(
            "s3_write_bytes_started",
            bucket=self.bucket,
            key=key,
            size_bytes=len(file_bytes),
        )

        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=file_bytes,
                ContentType="application/octet-stream",
            )
            self.log.info(
                "s3_write_bytes_completed",
                bucket=self.bucket,
                key=key,
                size_bytes=len(file_bytes),
            )
        except Exception as exc:
            self.log.exception(
                "s3_write_bytes_failed",
                bucket=self.bucket,
                key=key,
            )
            raise StorageWriteError(f"Failed to write S3 object: {filepath}") from exc

    def exists(self, filepath: str) -> bool:
        key = self._normalize_filepath(filepath)

        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")
            if error_code in {"404", "NoSuchKey", "NotFound"}:
                return False
            raise StorageReadError(f"Failed to check existence for S3 object: {filepath}") from exc
        except Exception as exc:
            raise StorageReadError(f"Failed to check existence for S3 object: {filepath}") from exc
