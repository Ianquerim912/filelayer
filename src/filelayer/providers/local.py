from __future__ import annotations

import logging
from pathlib import Path, PurePosixPath

from ..config import StorageSettings
from ..exceptions import (
    StorageConfigurationError,
    StorageObjectNotFoundError,
    StorageReadError,
    StorageWriteError,
)
from ..logging_utils import StructuredLogger
from .base import FileProvider


class LocalFileProvider(FileProvider):
    def __init__(
        self,
        settings: StorageSettings,
        logger: logging.Logger | None = None,
    ) -> None:
        if settings.provider != "local":
            raise StorageConfigurationError(
                "LocalFileProvider requires STORAGE_PROVIDER=local."
            )

        self.settings = settings
        self.root_path = settings.local_base_path.resolve()
        self.root_path.mkdir(parents=True, exist_ok=True)
        self.log = StructuredLogger(logger or logging.getLogger(self.__class__.__name__))

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

    def _resolve_path(self, filepath: str) -> Path:
        normalized = self._normalize_filepath(filepath)
        candidate = (self.root_path / normalized).resolve()

        try:
            candidate.relative_to(self.root_path)
        except ValueError as exc:
            raise StorageConfigurationError(
                f"filepath escapes local storage root: {filepath}"
            ) from exc

        return candidate

    def read_file(self, filepath: str) -> str:
        resolved = self._resolve_path(filepath)

        self.log.info(
            "local_read_text_started",
            filepath=filepath,
            resolved_path=str(resolved),
            encoding=self.settings.encoding,
        )

        if not resolved.exists() or not resolved.is_file():
            raise StorageObjectNotFoundError(f"Local file not found: {filepath}")

        try:
            content = resolved.read_text(encoding=self.settings.encoding)
            self.log.info(
                "local_read_text_completed",
                filepath=filepath,
                resolved_path=str(resolved),
                size_chars=len(content),
            )
            return content
        except StorageObjectNotFoundError:
            raise
        except UnicodeDecodeError as exc:
            self.log.exception(
                "local_read_text_decode_failed",
                filepath=filepath,
                resolved_path=str(resolved),
                encoding=self.settings.encoding,
            )
            raise StorageReadError(
                f"Failed to decode local file '{filepath}' using '{self.settings.encoding}'."
            ) from exc
        except Exception as exc:
            self.log.exception(
                "local_read_text_failed",
                filepath=filepath,
                resolved_path=str(resolved),
            )
            raise StorageReadError(f"Failed to read local file: {filepath}") from exc

    def write_file(self, filepath: str, file_content: str) -> None:
        resolved = self._resolve_path(filepath)
        resolved.parent.mkdir(parents=True, exist_ok=True)

        self.log.info(
            "local_write_text_started",
            filepath=filepath,
            resolved_path=str(resolved),
            size_chars=len(file_content),
            encoding=self.settings.encoding,
        )

        try:
            resolved.write_text(file_content, encoding=self.settings.encoding)
            self.log.info(
                "local_write_text_completed",
                filepath=filepath,
                resolved_path=str(resolved),
                size_chars=len(file_content),
            )
        except UnicodeEncodeError as exc:
            self.log.exception(
                "local_write_text_encode_failed",
                filepath=filepath,
                resolved_path=str(resolved),
                encoding=self.settings.encoding,
            )
            raise StorageWriteError(
                f"Failed to encode local file '{filepath}' using '{self.settings.encoding}'."
            ) from exc
        except Exception as exc:
            self.log.exception(
                "local_write_text_failed",
                filepath=filepath,
                resolved_path=str(resolved),
            )
            raise StorageWriteError(f"Failed to write local file: {filepath}") from exc

    def read_file_bytes(self, filepath: str) -> bytes:
        resolved = self._resolve_path(filepath)

        self.log.info(
            "local_read_bytes_started",
            filepath=filepath,
            resolved_path=str(resolved),
        )

        if not resolved.exists() or not resolved.is_file():
            raise StorageObjectNotFoundError(f"Local file not found: {filepath}")

        try:
            data = resolved.read_bytes()
            self.log.info(
                "local_read_bytes_completed",
                filepath=filepath,
                resolved_path=str(resolved),
                size_bytes=len(data),
            )
            return data
        except StorageObjectNotFoundError:
            raise
        except Exception as exc:
            self.log.exception(
                "local_read_bytes_failed",
                filepath=filepath,
                resolved_path=str(resolved),
            )
            raise StorageReadError(f"Failed to read local file: {filepath}") from exc

    def write_file_bytes(self, filepath: str, file_bytes: bytes) -> None:
        resolved = self._resolve_path(filepath)
        resolved.parent.mkdir(parents=True, exist_ok=True)

        self.log.info(
            "local_write_bytes_started",
            filepath=filepath,
            resolved_path=str(resolved),
            size_bytes=len(file_bytes),
        )

        try:
            resolved.write_bytes(file_bytes)
            self.log.info(
                "local_write_bytes_completed",
                filepath=filepath,
                resolved_path=str(resolved),
                size_bytes=len(file_bytes),
            )
        except Exception as exc:
            self.log.exception(
                "local_write_bytes_failed",
                filepath=filepath,
                resolved_path=str(resolved),
            )
            raise StorageWriteError(f"Failed to write local file: {filepath}") from exc

    def exists(self, filepath: str) -> bool:
        resolved = self._resolve_path(filepath)
        return resolved.exists() and resolved.is_file()
