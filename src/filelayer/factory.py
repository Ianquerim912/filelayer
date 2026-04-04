from __future__ import annotations

import logging

from .config import StorageSettings
from .exceptions import StorageConfigurationError
from .providers import FileProvider, LocalFileProvider, S3FileProvider


def create_file_provider(
    settings: StorageSettings | None = None,
    logger: logging.Logger | None = None,
) -> FileProvider:
    resolved_settings = settings or StorageSettings()

    if resolved_settings.provider == "local":
        return LocalFileProvider(resolved_settings, logger=logger)

    if resolved_settings.provider == "s3":
        return S3FileProvider(resolved_settings, logger=logger)

    raise StorageConfigurationError(
        f"Unsupported storage provider: {resolved_settings.provider}"
    )
